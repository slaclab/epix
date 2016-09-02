//-----------------------------------------------------------------------------
// File          : cpixPulserScan.cpp
// Author        : Maciej Kwiatkowski  <mkwiatko@slac.stanford.edu>
// Created       : 04/12/2011
// Project       : CSPAD
//-----------------------------------------------------------------------------
// Description :
//-----------------------------------------------------------------------------
// This file is part of 'EPIX Development Softare'.
// It is subject to the license terms in the LICENSE.txt file found in the 
// top-level directory of this distribution and at: 
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
// No part of 'EPIX Development Softare', including this file, 
// may be copied, modified, propagated, or distributed except according to 
// the terms contained in the LICENSE.txt file.
// Proprietary and confidential to SLAC.
//-----------------------------------------------------------------------------
// Modification history :
// 04/12/2011: created
//----------------------------------------------------------------------------
#include <PgpLink.h>
#include <MultDestPgp.h>
#include <MultLink.h>
#include <EpixControl.h>
#include <ControlServer.h>
#include <Device.h>
#include <iomanip>
#include <fstream>
#include <iostream>
#include <signal.h>
#include <string>
#include <pthread.h>
#include <Data.h>
#include <DataRead.h>

using namespace std;

#define HEADER_SIZE 14
#define FOOTER_SIZE 1

#define EVENTS_PER_FRAME 1
#define FRAMES_PER_FILE 1

#define PULSER_START 0
#define PULSER_STOP 1023
#define PULSER_STEP 1

#define MATRIX_TEST_BIT 0x1
#define MATRIX_TRIM 0x7
#define MATRIX_TEST_ROW 0
#define MATRIX_TEST_COL 0

// Run flag for sig catch
bool stop;

// Function to catch cntrl-c
void sigTerm (int) { 
   cout << "Got Signal!" << endl;
   stop = true; 
}


int main (int argc, char **argv) {
   
   stop = false;
   
   // Catch signals
   signal (SIGINT,&sigTerm);

   try {
      
      MultLink     *pgpLink;
      MultDest     *dest;  
      string        defFile = "xml/cpix_1_async_mode_pulser_scan.xml";
      uint          baseAddress;
      uint          addrSize;
      unsigned int  value;
      int           cntAevent;
      int           cntBevent;
      int           cntAframe;
      int           cntBframe;
      int           pulser;
      
      
      baseAddress = 0x00000000;
      addrSize = 4;
      dest = new MultDestPgp("/dev/pgpcard0");
      dest->addDataSource(0x00000000); // VC0 - acq data
      dest->addDataSource(0x02000000); // VC2 - oscilloscope
      pgpLink = new MultLink();
      pgpLink->setDebug(false);
      pgpLink->setMaxRxTx(0x800000);
      pgpLink->open(1,dest);
      pgpLink->enableSharedMemory("epix",1);   
      usleep(100);

      cout << "Created PGP Link" << endl;

      EpixControl   epix(pgpLink,defFile,CPIXP, baseAddress, addrSize);
      epix.setDebug(false);
      epix.command("SetDefaults", "");

      DataRead  *dread_;
      Data      *event_;
      uint       dsize_;
      uint       seqNum;
      bool       first;
      //unsigned long int bytes = 0;

      dread_ = new DataRead;
      event_ = new Data;

      dread_->openShared("epix",1);
      
      pulser = PULSER_START;
      
      //stop auto run to config the matrix
      epix.device("digFpga",0)->writeSingle("AutoRunEnable", 0);
      
      //set the initial matrix config
      printf("Setting matrich config bits to 0x%X\n", MATRIX_TEST_BIT | (7<<2));
      epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("PrepareMultiConfig", 0);
      epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("WriteMatrixData", MATRIX_TEST_BIT | (MATRIX_TRIM<<2) );
      epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("CmdPrepForRead", 0);
      
      //set selected column and row if requested
      if (MATRIX_TEST_ROW > 0 && MATRIX_TEST_ROW <= 47) {
         epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("PrepareMultiConfig", 0);
         epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("RowCounter", MATRIX_TEST_ROW);
         epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("WriteRowData", 0x1 | (MATRIX_TRIM<<2));
      }
      if (MATRIX_TEST_COL > 0 && MATRIX_TEST_COL <= 47) {
         epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("PrepareMultiConfig", 0);
         epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("ColCounter", MATRIX_TEST_COL);
         epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("WriteColData", 0x1 | (MATRIX_TRIM<<2));
      }
      
      //set pulser here
      printf("Pulser changed to %d\n", pulser);
      value = epix.device("digFpga",0)->device("CpixPAsic",0)->readSingle("Config3");
      epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("Config3", (value&0xfffffC00)|(pulser&0x3FF));    //test only ASIC 0 (CpixPAsic, 0)
      
      //start auto run when done
      epix.device("digFpga",0)->writeSingle("AutoRunEnable", 1);
      
      
      time_t current_time;
      struct tm * time_info;
      char timeString[128];

      time(&current_time);
      time_info = localtime(&current_time);

      strftime(timeString, 128, "%m%d%y", time_info);
      
      ofstream frameFile;
      
      printf("Waiting for data\n");
      
      cntAevent = 0;
      cntBevent = 0;
      
      cntAframe = 0;
      cntBframe = 0;
      
      first = true;
      
      while (!stop) {
         
         if ( dread_->next(event_) ) {
            
            dsize_ = event_->size(); // 32 bit values
            
            if (dsize_ >= 1168) {
               
               
               //drop frames following failed acquisitions
               //it is related to (possibly ASIC bug) the counter not being reset properly after a SACI command
               if(first) {
                  seqNum = event_->data()[2];
                  if ((event_->data()[HEADER_SIZE]&0xf0)==0) // cntB
                     first = false; //make sure to start with good cntA
                  continue;
               }
               if (event_->data()[2] != seqNum+1) {
                  printf("Dropping frame seqNo %d that arrived after frame seqNo %d\n", event_->data()[2], seqNum);
                  if ((event_->data()[HEADER_SIZE]&0xf0)!=0) // cntA
                     first = true; // drop also cntB
                  seqNum = event_->data()[2];
                  continue;
               }
               else {
                  seqNum = event_->data()[2];
               }
               
               
               //print packet size
               printf("Payload size %d 32-bit words. Packet size %d 32-bit words. Acq %d, seq %d, ASIC %d, cnt%c\n", dsize_-(HEADER_SIZE+FOOTER_SIZE+1), dsize_, event_->data()[1], event_->data()[2], (event_->data()[HEADER_SIZE]&0xf), (event_->data()[HEADER_SIZE]&0xf0)!=0?'A':'B');
               //print a couple of pixels
               for (int x = HEADER_SIZE+1, i=0; x < event_->size() - FOOTER_SIZE; x++, i++) {
                  if (i < 4) {
                     cout << "0x" << hex << setw(4) << setfill('0') << (event_->data()[x]&0x0000ffff) << "    ";
                     cout << "0x" << hex << setw(4) << setfill('0') << ((event_->data()[x]&0xffff0000)>>16) << "    ";
                  }
               }
               cout << endl;
               
               //Frame with cntA was received
               if ((event_->data()[HEADER_SIZE]&0xf0)!=0) {
                  //skip every EVENTS_PER_FRAME frame and save selected number of frames to the file
                  //when all saved stop and wait until new settings are applied or the test is done
                  if (cntAevent >= EVENTS_PER_FRAME-1 && cntAframe <= FRAMES_PER_FILE-1) {
                     cntAevent = 0;
                     cntAframe++;
                     // save the file
                     ostringstream cnvMPul;
                     cnvMPul << pulser;
                     string fileName = "/u1/mkwiatko/CPIX_" + string(timeString) + "_cntA_Pulser_" + cnvMPul.str() + ".bin";
                     frameFile.open (fileName.c_str(), ios::out | ios::binary | ios::app);
                     frameFile.write ((char*)event_->data(), dsize_*4);
                     frameFile.close();
                  }
                  else if (cntAevent < EVENTS_PER_FRAME-1) {
                     cntAevent++;
                  }
                  
               }
               //Frame with cntB was received
               else {
                  //skip every EVENTS_PER_FRAME frame and save selected number of frames to the file
                  //when all saved stop and wait until new settings are applied or the test is done
                  if (cntBevent >= EVENTS_PER_FRAME-1 && cntBframe <= FRAMES_PER_FILE-1) {
                     cntBevent = 0;
                     cntBframe++;
                     // save the file
                     ostringstream cnvMPul;
                     cnvMPul << pulser;
                     string fileName = "/u1/mkwiatko/CPIX_" + string(timeString) + "_cntB_Pulser_" + cnvMPul.str() + ".bin";
                     frameFile.open (fileName.c_str(), ios::out | ios::binary | ios::app);
                     frameFile.write ((char*)event_->data(), dsize_*4);
                     frameFile.close();
                  }
                  else if (cntBevent < EVENTS_PER_FRAME-1) {
                     cntBevent++;
                  }
               }
               
               // if all frames are saved
               // move settings as requested
               if (cntAframe > FRAMES_PER_FILE-1 && cntBframe > FRAMES_PER_FILE-1) {
                  
                  //stop auto run to config the ASIC
                  epix.device("digFpga",0)->writeSingle("AutoRunEnable", 0);
                  
                  cntAframe=0;
                  cntBframe=0;
                  cntAevent=0;
                  cntBevent=0;
                  
                  //move the pulser if not last
                  if (pulser < PULSER_STOP && pulser+PULSER_STEP <= 1023) {
                     pulser+=PULSER_STEP;
                     
                     //set pulser here
                     printf("Pulser changed to %d\n", pulser);
                     value = epix.device("digFpga",0)->device("CpixPAsic",0)->readSingle("Config3");
                     epix.device("digFpga",0)->device("CpixPAsic",0)->writeSingle("Config3", (value&0xfffffC00)|(pulser&0x3FF));    //test only ASIC 0 (CpixPAsic, 0)
                     
                  }
                  else {
                     // all pulser steps are done
                     printf("Testing finished!\n");
                     break;
                  }
                  
                  epix.device("digFpga",0)->writeSingle("AutoRunEnable", 1);
                  
               }
               
            }
            else if (dsize_ >= HEADER_SIZE) {
               printf("Wrong size packet %d 32-bit words. Acq %d, seq %d, ASIC %d, cnt%c\n", dsize_, event_->data()[1], event_->data()[2], (event_->data()[HEADER_SIZE]&0xf), (event_->data()[HEADER_SIZE]&0xf0)!=0?'A':'B');
            }
            else {
               printf("Wrong size packet %d 32-bit words.\n", dsize_);
            }
            
            timespec tv;
            tv.tv_sec = 0;
            tv.tv_nsec = 1000000;
            nanosleep(&tv,0);

         }
         
         
      }
      
      exit(0);
      

   } catch ( string error ) {
      cout << "Caught Error: " << endl;
      cout << error << endl;
   }
}

