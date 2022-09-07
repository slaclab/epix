#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : PyRogue AXI Version Module
#-----------------------------------------------------------------------------
# File       : from pyrogue/devices/axi_version.py
# Author     : originally from Ryan Herbst, rherbst@slac.stanford.edu
#            : adapted by Dionisio Doering
# Created    : 2016-09-29
# Last update: 2017-01-31
#-----------------------------------------------------------------------------
# Description:
# PyRogue AXI Version Module for ePix100a
# for genDAQ compatibility check software/deviceLib/Epix100aAsic.cpp
#-----------------------------------------------------------------------------
# This file is part of the rogue software platform. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue software platform, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import time as ti
import pyrogue as pr
import collections
import os
import numpy as np

usingPyQt5 = True

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
except ImportError:
    from PyQt4.QtCore    import *
    from PyQt4.QtGui     import *
    usingPyQt5 = False


class Epix100aAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create the axiVersion device for ePix100aAsic"""
        super().__init__(description='Epix100a Asic Configuration', **kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
        #it is defined the addrSize variable
        addrSize = 4	

        # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
        # contains this object. In most cases the parent and memBase are the same but they can be 
        # different in more complex bus structures. They will also be different for the top most node.
        # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
        # blocks will be updated.

        #############################################
        # Create block / variable combinations
        #############################################
    
        
        #Setup registers & variables
         
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True, overlapEn=True))
        
        # CMD = 1, Addr = 1  : Bits 2:0 - Pulser monostable bits
        #                      Bit  7   - Pulser sync bit
        self.add((pr.RemoteVariable(name='MonostPulser', description='MonoSt Pulser bits',   offset=0x00001001*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
                 pr.RemoteVariable( name='PulserSync',   description='Pulse on SYNC signal', offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode='RW', overlapEn=True)))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        #                    : Bit 0 = Test
        #                    : Bit 1 = Test
        self.add(pr.RemoteVariable(name='PixelDummy', description='Pixel dummy, write data', offset=0x00001002*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True))
        
        # TODO
        # check Variable("DummyMask") and Variable("DummyTest")
        # these variables don't seem to be needed in the rogue version of the software.

        # CMD = 1, Addr = 3  : Bits 9:0 = Pulser[9:0]
        #                    : Bit  10  = pbit
        #                    : Bit  11  = atest
        #                    : Bit  12  = test
        #                    : Bit  13  = sab_test
        #                    : Bit  14  = hrtest
        #                    : Bit  15  = PulserR
        self.add((
            pr.RemoteVariable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='sba_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 4  : Bits 3:0 = DM1[3:0]
        #                    : Bits 7:4 = DM2[3:0]
        
        self.add(
            pr.RemoteVariable(name='DigMon1', offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True))         

        self.add(
            pr.RemoteVariable(name='DigMon2', offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW', overlapEn=True))         
 
        # CMD = 1, Addr = 5  : Bits 2:0 = Pulser DAC[2:0]
        #                      Bits 7:4 = TPS_GR[3:0]
        self.add((
            pr.RemoteVariable(name='PulserDac', description='Pulser Dac', offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='TpsGr',     description='',           offset=0x00001005*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 6  : Bit  0   = DM1en
        #                    : Bit  1   = DM2en
        #                    : Bit  4   = SLVDSbit
        self.add((
            pr.RemoteVariable(name='Dm1En', description='Digital Monitor 1 Enable', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Dm2En', description='Digital Monitor 1 Enable', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='SLVDSbit', description='',                      offset=0x00001006*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW', overlapEn=True)))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.RemoteVariable(name='VRef',    description='Voltage Ref',                offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='VRefLow', description='Voltage Ref for Extra Rows', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.RemoteVariable(name='TPS_tcomp',  description='', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='TPS_MUX',    description='', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='TPS_Monost', description='', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base=pr.UInt,  mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 9  : Bit  3:0 = S2D0_GR[3:0]
        #                    : Bit  7:4 = S2D1_GR[3:0]
        self.add((
            pr.RemoteVariable(name='S2d0Gr', description='', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d1Gr', description='', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW', overlapEn=True)))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.RemoteVariable(name='PpOcbS2d',     description='', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Ocb',          description='', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Monost',       description='', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='FastppEnable', description='', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW', overlapEn=True)))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.RemoteVariable(name='Preamp',  description='', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='PixelCb', description='', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Vld1_b',  description='', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.RemoteVariable(name='S2dTComp',  description='', offset=0x0000100C*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='FilterDac', description='', offset=0x0000100C*addrSize, bitSize=6, bitOffset=1, base=pr.UInt,  mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.RemoteVariable(name='TC',         description='', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d',        description='', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2dDacBias', description='', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='TpsTcDac', description='', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='TpsDac',   description='', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='S2d0TcDac', description='', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d0Dac',   description='', offset=0x0000100F*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.RemoteVariable(name='TestBe',       description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='IsEn',         description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='DelExec',      description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='DelCckRef',    description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='ro_rst_exten', description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 17 : Row start  address[9:0]
        # CMD = 1, Addr = 18 : Row stop  address[9:0]
        # CMD = 1, Addr = 19 : Col start  address[9:0]
        # CMD = 1, Addr = 20 : Col stop  address[9:0]
        self.add((
            pr.RemoteVariable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=10, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=10, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=10, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=10, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True)))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.RemoteVariable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True))

        # CMD = 1, Addr = 22 : Bit  3:0 = S2D2GR[3:0]
        #                    : Bit  7:4 = S2D3GR[5:0] #TODO check it this is not 3:0??
        self.add((
            pr.RemoteVariable(name='S2d2Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d3Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 23 : Bit  1:0 = S2D1_tcDAC[1:0]
        #                    : Bit  7:2 = S2D1_DAC[5:0]
        # CMD = 1, Addr = 24 : Bit  1:0 = S2D2_tcDAC[1:0]
        #                    : Bit  7:2 = S2D2_DAC[5:0]  
        # CMD = 1, Addr = 25 : Bit  1:0 = S2D3_tcDAC[1:0]
        #                    : Bit  7:2 = S2D3_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='S2d1TcDac', description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d1Dac',   description='', offset=0x00001017*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d2TcDac', description='', offset=0x00001018*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d2Dac',   description='', offset=0x00001018*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d3TcDac', description='', offset=0x00001019*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d3Dac',   description='', offset=0x00001019*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))
        
        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))
 
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=2, bitOffset=0,  function=pr.Command.touch, hidden=False))

        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.RemoteVariable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'),
        #    pr.RemoteVariable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))



        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)
    
    
    
    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        if self._size == 0:
                self._size = 0xfffff

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if not isinstance(arg, str):
               arg = ''
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
               # in PyQt5 QFileDialog returns a tuple
               if usingPyQt5:
                  self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (354, 384):
                    self._rawWrite(0x00000000*addrSize,0)
                    self._rawWrite(0x00008000*addrSize,0)
                    for x in range (0, 354):
                        for y in range (0, 384):
                            bankToWrite = int(y/96);
                            if (bankToWrite == 0):
                               colToWrite = 0x700 + y%96;
                            elif (bankToWrite == 1):
                               colToWrite = 0x680 + y%96;
                            elif (bankToWrite == 2):
                               colToWrite = 0x580 + y%96;
                            elif (bankToWrite == 3):
                               colToWrite = 0x380 + y%96;
                            else:
                               print('unexpected bank number')
                            self._rawWrite(0x00006011*addrSize, x)
                            self._rawWrite(0x00006013*addrSize, colToWrite) 
                            self._rawWrite(0x00005000*addrSize, (int(matrixCfg[x][y])))
                    self._rawWrite(0x00000000*addrSize,0)
                else:
                    print('csv file must be 384x354 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")


    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if not isinstance(arg, str):
               arg = ''
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((354, 384),dtype='uint16')
                self._rawWrite(0x00000000*addrSize,0)
                self._rawWrite(0x00008000*addrSize,0)
                for x in range (0, 354):
                   for y in range (0, 384):
                      bankToWrite = int(y/96);
                      if (bankToWrite == 0):
                         colToWrite = 0x700 + y%96;
                      elif (bankToWrite == 1):
                         colToWrite = 0x680 + y%96;
                      elif (bankToWrite == 2):
                         colToWrite = 0x580 + y%96;
                      elif (bankToWrite == 3):
                         colToWrite = 0x380 + y%96;
                      else:
                         print('unexpected bank number')
                      self._rawWrite(0x00006011*addrSize, x)
                      self._rawWrite(0x00006013*addrSize, colToWrite)
                      readBack[x, y] = self._rawRead(0x00005000*addrSize)
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            for i in range (0, 96):
                self.PrepareMultiConfig()
                self.ColCounter.set(i)
                self.WriteColData.set(0)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")      

    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)

    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func



class EpixSAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create the axiVersion device for ePixSAsic"""
        super().__init__(description='EpixS Asic Configuration', **kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
        #it is defined the addrSize variable
        addrSize = 4	

        # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
        # contains this object. In most cases the parent and memBase are the same but they can be 
        # different in more complex bus structures. They will also be different for the top most node.
        # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
        # blocks will be updated.

        #############################################
        # Create block / variable combinations
        #############################################
    
        
        #Setup registers & variables
                
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True))
        
        # CMD = 1, Addr = 1  : Bit  7   - Pulser sync bit
        self.add((pr.RemoteVariable( name='PulserSync',   description='Pulse on SYNC signal', offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode='RW')))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        #                    : Bit 0 = Test
        #                    : Bit 1 = Test
        self.add(pr.RemoteVariable(name='PixelDummy', description='Pixel dummy, write data', offset=0x00001002*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
        
        # TODO
        # check Variable("DummyMask") and Variable("DummyTest")
        # these variables don't seem to be needed in the rogue version of the software.

        # CMD = 1, Addr = 3  : Bits 9:0 = Pulser[9:0]
        #                    : Bit  10  = pbit
        #                    : Bit  11  = atest
        #                    : Bit  12  = test
        #                    : Bit  13  = sab_test
        #                    : Bit  14  = hrtest
        #                    : Bit  15  = PulserR
        self.add((
            pr.RemoteVariable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='sba_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 4  : Bits 3:0 = DM1[3:0]
        #                    : Bits 7:4 = DM2[3:0]
        
        self.add(
            pr.RemoteVariable(name='DigMon1', offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'))         

        self.add(
            pr.RemoteVariable(name='DigMon2', offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW'))         
 
        # CMD = 1, Addr = 5  : Bits 2:0 = Pulser DAC[2:0]
        #                      Bits 7:4 = MonostPulser[2:0]
        self.add((
            pr.RemoteVariable(name='PulserDac',    description='Pulser Dac',   offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='MonostPulser', description='MonostPulser', offset=0x00001005*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 6  : Bit   0   = DM1en
        #                    : Bit   1   = DM2en
        #                    : Bit 3:2   = Vflg1_b
        #                    : Bit   4   = Vflg1_off
        self.add((
            pr.RemoteVariable(name='Dm1En',     description='Digital Monitor 1 Enable', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Dm2En',     description='Digital Monitor 1 Enable', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Vflg1_b',   description='Vflg1_b',                  offset=0x00001006*addrSize, bitSize=2, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Vflg1_off', description='Vflg1_off',                offset=0x00001006*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW')))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF_DAC[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.RemoteVariable(name='VRef_DAC',    description='Voltage Ref DAC',        offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='VRefLow', description='Voltage Ref for Extra Rows', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.RemoteVariable(name='TPS_tcomp',  description='', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='TPS_MUX',    description='', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='TPS_Monost', description='', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base=pr.UInt,  mode='RW')))

        # CMD = 1, Addr = 9  : Bit  3:0 = S2D0_GR[3:0]
        #                    : Bit  7:4 = S2D1_GR[3:0]
        self.add((
            pr.RemoteVariable(name='TPS_GR', description='', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2D_GR', description='', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.RemoteVariable(name='PpOcbS2d',     description='', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Ocb',          description='', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='Monost',       description='', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='FastppEnable', description='', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.RemoteVariable(name='Preamp',  description='', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='PixelCb', description='', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Vld1_b',  description='', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.RemoteVariable(name='S2dTComp',  description='', offset=0x0000100C*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='FilterDac', description='', offset=0x0000100C*addrSize, bitSize=6, bitOffset=1, base=pr.UInt,  mode='RW')))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.RemoteVariable(name='TC',         description='', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2d',        description='', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2dDacBias', description='', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='TpsTcDac', description='', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='TpsDac',   description='', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='S2d0TcDac', description='', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2d0Dac',   description='', offset=0x0000100F*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        #                    : Bit  5   = SLVDSbit
        self.add((
            pr.RemoteVariable(name='TestBe',       description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='IsEn',         description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelExec',      description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelCckRef',    description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='ro_rst_exten', description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='SLVDSbit',     description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=5, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 17 : Row start  address[9:0]
        # CMD = 1, Addr = 18 : Row stop  address[9:0]
        # CMD = 1, Addr = 19 : Col start  address[9:0]
        # CMD = 1, Addr = 20 : Col stop  address[9:0]
        self.add((
            pr.RemoteVariable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=9, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=9, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='RW')))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.RemoteVariable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))

        
        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))
 
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=2, bitOffset=0,  function=pr.Command.touch, hidden=False))

        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.RemoteVariable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'),
        #    pr.RemoteVariable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))



        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.ePix100aFPGA.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
                self.filename = arg
            else:
                self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (12, 10):
                    self._rawWrite(0x00000000*addrSize,0)
                    self._rawWrite(0x00008000*addrSize,0)
                    for x in range (0, 12):
                        for y in range (0, 10):
                            self._rawWrite(0x00006011*addrSize, x)
                            self._rawWrite(0x00006013*addrSize, y) 
                            self._rawWrite(0x00005000*addrSize, (int(matrixCfg[x][y])))
                    self._rawWrite(0x00000000*addrSize,0)
                else:
                    print('csv file must be 384x354 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")

    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.ePix100aFPGA.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):

            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
                self.filename = arg
            else:
                self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((12, 10),dtype='uint16')
                self._rawWrite(0x00000000*addrSize,0)
                self._rawWrite(0x00008000*addrSize,0)
                for x in range (0, 12):
                   for y in range (0, 10):
                      self._rawWrite(0x00006011*addrSize, x)
                      self._rawWrite(0x00006013*addrSize, y)
                      readBack[x, y] = self._rawRead(0x00005000*addrSize)
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.ePix100aFPGA.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            for i in range (0, 96):
                self.PrepareMultiConfig()
                self.ColCounter.set(i)
                self.WriteColData.set(0)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")      

    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)

    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func


class Epix10kaAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create the ePix10kaAsic device"""
        super().__init__(description='Epix10ka Asic Configuration', **kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
        #it is defined the addrSize variable
        addrSize = 4	

        # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
        # contains this object. In most cases the parent and memBase are the same but they can be 
        # different in more complex bus structures. They will also be different for the top most node.
        # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
        # blocks will be updated.

        #############################################
        # Create block / variable combinations
        #############################################
    
        
        #Setup registers & variables
                
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True, overlapEn=True))
        
        # CMD = 1, Addr = 1 
        # TODO: fix CompEn so it is one uint register
        self.add((
            pr.RemoteVariable(name='CompTH_DAC',   description='Config1',  offset=0x00001001*addrSize, bitSize=6, bitOffset=0, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='CompEn0',      description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='CompEn1',      description='Config5',  offset=0x00001005*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='CompEn2',      description='Config5',  offset=0x00001005*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='PulserSync',   description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW', overlapEn=True)))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        self.add(pr.RemoteVariable(name='PixelDummy', description='Pixel dummy, write data', offset=0x00001002*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True))
        

        # CMD = 1, Addr = 3  
        self.add((
            pr.RemoteVariable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='sab_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 4 
        self.add((
            pr.RemoteVariable(name='DigMon1', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='DigMon2', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW', overlapEn=True)))
 
        # CMD = 1, Addr = 5 
        self.add((
            pr.RemoteVariable(name='PulserDac',    description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='MonostPulser', description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 6 
        self.add((
            pr.RemoteVariable(name='Dm1En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Dm2En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='emph_bd',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='emph_bc',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW', overlapEn=True)))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.RemoteVariable(name='VRef',    description='Config7', offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='VRefLow', description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.RemoteVariable(name='TpsTComp',  description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='TpsMux',    description='Config8', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='RoMonost',  description='Config8', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base=pr.UInt,  mode='RW', overlapEn=True)))     

        # CMD = 1, Addr = 9 
        self.add((
            pr.RemoteVariable(name='TpsGr',  description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d0Gr', description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW', overlapEn=True)))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.RemoteVariable(name='PpOcbS2d',     description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Ocb',          description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Monost',       description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='FastppEnable', description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW', overlapEn=True)))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.RemoteVariable(name='Preamp',  description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='PixelCb', description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='Vld1_b',  description='Config11', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.RemoteVariable(name='S2dTComp',           description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='FilterDac',          description='Config12', offset=0x0000100C*addrSize, bitSize=6, bitOffset=1, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='TestLVDTransmitter', description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.RemoteVariable(name='TC',         description='Config13', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d',        description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2dDacBias', description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='TpsTcDac', description='Config14', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='TpsDac',   description='Config14', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='S2d0TcDac', description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d0Dac',   description='Config15', offset=0x0000100F*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.RemoteVariable(name='TestBe',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='IsEn',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='DelExec',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='DelCckRef',    description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='RO_rst_en',    description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='SlvdsBit',     description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=5, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='FELmode',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='CompEnOn',     description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW', overlapEn=True)))

        # CMD = 1, Addr = 17 : Row start  address[8:0]
        # CMD = 1, Addr = 18 : Row stop  address[8:0]
        # CMD = 1, Addr = 19 : Col start  address[6:0]
        # CMD = 1, Addr = 20 : Col stop  address[6:0]
        self.add((
            pr.RemoteVariable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=9, bitOffset=0, base=pr.UInt, mode='WO', overlapEn=True),
            pr.RemoteVariable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=9, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='WO', overlapEn=True),
            pr.RemoteVariable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True)))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.RemoteVariable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=16, bitOffset=0, base=pr.UInt, mode='RO', overlapEn=True))

        # CMD = 1, Addr = 22 
        self.add((
            pr.RemoteVariable(name='S2d1Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d2Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW', overlapEn=True)))
        
        # CMD = 1, Addr = 23
        self.add((
            pr.RemoteVariable(name='S2d3Gr', description='', offset=0x00001017*addrSize, bitSize=4, bitOffset=0, base=pr.UInt,  mode='RW', overlapEn=True),
            pr.RemoteVariable(name='trbit',  description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW', overlapEn=True)))
        
        # CMD = 1, Addr = 24
        self.add((
            pr.RemoteVariable(name='S2d1TcDac', description='', offset=0x00001018*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d1Dac',   description='', offset=0x00001018*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))
        
        # CMD = 1, Addr = 25
        self.add((
            pr.RemoteVariable(name='S2d2TcDac', description='', offset=0x00001019*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d2Dac',   description='', offset=0x00001019*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))
        
        # CMD = 1, Addr = 26
        self.add((
            pr.RemoteVariable(name='S2d3TcDac', description='', offset=0x0000101A*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True),
            pr.RemoteVariable(name='S2d3Dac',   description='', offset=0x0000101A*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW', overlapEn=True)))
        
        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))
   
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=4, bitOffset=0,  function=pr.Command.touch, hidden=False))
 
        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.RemoteVariable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'),
        #    pr.RemoteVariable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))




        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed
# 
        # self.add(
            # pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))
            # 
        # self.add(
            # pr.Command(name='SetMatrixHiMed',description='Set configuration bits of all pixels to 12', function=self.fnSetMatrixHiMed))
            # 
        # self.add(
            # pr.Command(name='SetMatrixLow',description='Set configuration bits of all pixels to 8', function=self.fnSetMatrixLow))
# 
        # self.add(
            # pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        # 
        # self.add(
            # pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)
        @self.command(description='SetPixelBitmap command function', value='', retValue='')
        def SetPixelBitmap(arg, dev, cmd):
            print('HEREEREREF')
            """SetPixelBitmap command function"""
            if self._size == 0:
                self._size = 0xfffff

            addrSize = 4

            if (self.enable.get()):
                self.reportCmd(dev, cmd, arg)
                if not isinstance(arg, str):
                    arg = ''
                if len(arg) > 0:
                    self.filename = arg
                if os.path.splitext(self.filename)[1] == '.csv':
                    matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                    if matrixCfg.shape == (178, 192):
                        self._rawWrite(0x00000000 * addrSize, 0)
                        self._rawWrite(0x00008000 * addrSize, 0)
                        for x in range(0, 177):
                            for y in range(0, 192):
                                bankToWrite = int(y / 48)
                                if (bankToWrite == 0):
                                    colToWrite = 0x700 + y % 48
                                elif (bankToWrite == 1):
                                    colToWrite = 0x680 + y % 48
                                elif (bankToWrite == 2):
                                    colToWrite = 0x580 + y % 48
                                elif (bankToWrite == 3):
                                    colToWrite = 0x380 + y % 48
                                else:
                                    print('unexpected bank number')
                                self._rawWrite(0x00006011 * addrSize, x)
                                self._rawWrite(0x00006013 * addrSize, colToWrite)
                                self._rawWrite(0x00005000 * addrSize, (int(matrixCfg[x][y])))
                        self._rawWrite(0x00000000 * addrSize, 0)
                    else:
                        print('csv file must be 192x178 pixels')
                else:
                    print("Not csv file : ", self.filename)
            else:
                print("Warning: ASIC enable is set to False!")

        @self.command(description='GetPixelBitmap command function', value='', retValue='')
        def GetPixelBitmap(dev, cmd, arg):
            """GetPixelBitmap command function"""
            if self._size == 0:
                self._size = 0xfffff

            addrSize = 4

            if (self.enable.get()):
                self.reportCmd(dev, cmd, arg)
                if not isinstance(arg, str):
                    arg = ''
                if len(arg) > 0:
                    self.filename = arg

                if os.path.splitext(self.filename)[1] == '.csv':
                    readBack = np.zeros((178, 192), dtype='uint16')
                    self._rawWrite(0x00000000 * addrSize, 0)
                    self._rawWrite(0x00008000 * addrSize, 0)
                    for x in range(0, 177):
                        for y in range(0, 192):
                            bankToWrite = int(y / 48)
                            if (bankToWrite == 0):
                                colToWrite = 0x700 + y % 48
                            elif (bankToWrite == 1):
                                colToWrite = 0x680 + y % 48
                            elif (bankToWrite == 2):
                                colToWrite = 0x580 + y % 48
                            elif (bankToWrite == 3):
                                colToWrite = 0x380 + y % 48
                            else:
                                print('unexpected bank number')
                            self._rawWrite(0x00006011 * addrSize, x)
                            self._rawWrite(0x00006013 * addrSize, colToWrite)
                            readBack[x, y] = self._rawRead(0x00005000 * addrSize)
                    np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
            else:
                print("Warning: ASIC enable is set to False!")

        @self.command(description='Clear selected matrix')
        def ClearMatrix(dev, cmd, arg):
            """ClearMatrix command function"""

            if (self.enable.get()):
                self.reportCmd(dev, cmd, arg)
                for i in range(0, 48):
                    self.PrepareMultiConfig()
                    self.ColCounter.set(i)
                    self.WriteColData.set(0)
                self.CmdPrepForRead()
            else:
                print("Warning: ASIC enable is set to False!")

        @self.command()
        def SetMatrixHiMed(dev, cmd, arg):
            """ClearMatrix command function"""

            if (self.enable.get()):
                self.reportCmd(dev, cmd, arg)
                for i in range(0, 48):
                    self.PrepareMultiConfig()
                    self.ColCounter.set(i)
                    self.WriteColData.set(12)
                self.CmdPrepForRead()
            else:
                print("Warning: ASIC enable is set to False!")

        @self.command()
        def SetMatrixLow(dev, cmd, arg):
            """ClearMatrix command function"""

            if (self.enable.get()):
                self.reportCmd(dev, cmd, arg)
                for i in range(0, 48):
                    self.PrepareMultiConfig()
                    self.ColCounter.set(i)
                    self.WriteColData.set(8)
                self.CmdPrepForRead()
            else:
                print("Warning: ASIC enable is set to False!")

    # standard way to report a command has been executed

    def reportCmd(self, dev, cmd, arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)

    @staticmethod
    def frequencyConverter(self):
        def func(dev, var):
            return '{:.3f} kHz'.format(1 / (self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func
    
class Epix10kaAsicRev2(Epix10kaAsic):
    def __init__(self, **kwargs):
        """Create the ePix10kaAsic rev2 device"""
        super().__init__(**kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
        #it is defined the addrSize variable
        addrSize = 4	
        
        # CMD = 1, Addr = 23
        self.add((
            pr.RemoteVariable(name='S2D_Rz', description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=5, base=pr.UInt,  mode='RW', overlapEn=True)))
        
        # CMD = 1, Addr = 27
        self.add((
            pr.RemoteVariable(name='S2D_LSB', description='', offset=0x0000101B*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW', overlapEn=True)))

class TixelAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create registers for Tixel ASIC"""
        super().__init__(description='Tixel ASIC Configuration', **kwargs)
        
        addrSize = 4	
        
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True))
        
        # CMD = 1, Addr = xxx - Register set
        
        self.add(pr.RemoteVariable(name='RowStart',      description='RowStart',       offset=0x00001001*addrSize, bitSize=8,  bitOffset=0,  base=pr.UInt,  mode='WO'))
        self.add(pr.RemoteVariable(name='RowStop',       description='RowStop',        offset=0x00001002*addrSize, bitSize=8,  bitOffset=0,  base=pr.UInt,  mode='RW'))
        self.add(pr.RemoteVariable(name='ColumnStart',   description='ColumnStart',    offset=0x00001003*addrSize, bitSize=8,  bitOffset=0,  base=pr.UInt,  mode='WO'))
        self.add(pr.RemoteVariable(name='StartPixel',    description='StartPixel',     offset=0x00001004*addrSize, bitSize=16, bitOffset=0,  base=pr.UInt,  mode='RW'))
        self.add((
            pr.RemoteVariable(name='TpsDacGain',   description='Config5', offset=0x00001005*addrSize, bitSize=2, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='TpsDac',       description='Config5', offset=0x00001005*addrSize, bitSize=6, bitOffset=2,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='TpsGr',        description='Config5', offset=0x00001005*addrSize, bitSize=4, bitOffset=8,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='TpsMux',       description='Config5', offset=0x00001005*addrSize, bitSize=4, bitOffset=12, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='BiasTpsBuffer', description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BiasTps',       description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=3,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BiasTpsDac',    description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=6,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DacComparator', description='Config6', offset=0x00001006*addrSize, bitSize=6, bitOffset=10, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='BiasComparator',     description='Config7', offset=0x00001007*addrSize, bitSize=3, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Preamp',             description='Config7', offset=0x00001007*addrSize, bitSize=3, bitOffset=3,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BiasDac',            description='Config7', offset=0x00001007*addrSize, bitSize=3, bitOffset=6,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BgrCtrlDacTps',      description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=9,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BgrCtrlDacComp',     description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=11, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DacComparatorGain',  description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=13, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='Ppbit',           description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='TestBe',          description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=1,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelExec',         description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=2,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelCCKreg',       description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=3,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='syncExten',       description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=4,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='syncRoleSel',     description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=5,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='hdrMode',         description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=6,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='acqRowlastEn',    description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=7,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DM1en',           description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=8,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DM2en',           description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=9,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DigROdisable',    description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=10, base=pr.Bool, mode='RW')))
        self.add((
            pr.RemoteVariable(name='pllReset',        description='Config9', offset=0x00001009*addrSize, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='pllItune',        description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=1,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllKvco',         description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=4,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllFilter1',      description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=7,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllFilter2',      description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=10, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllOutDivider',   description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=13, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='pllROReset',      description='Config10', offset=0x0000100a*addrSize, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='pllROItune',      description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=1,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllROKvco',       description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=4,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllROFilter1',    description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=7,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllROFilter2',    description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=10, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pllROOutDivider', description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=13, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='dllGlobalCalib',     description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='dllCalibrationRang', description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=3,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DllCpBias',          description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=6,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DllAlockRen',        description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=9,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DllReset',           description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=10, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DllDACvctrlEn',      description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=11, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DllBiasDisable',     description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=12, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='delayCellTestCalib', description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=13, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='BiasVthCalibStepSize',  description='Config12', offset=0x0000100c*addrSize, bitSize=2, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BiasVthCalibStepGlob',  description='Config12', offset=0x0000100c*addrSize, bitSize=3, bitOffset=2,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BiasVthCalibTail',      description='Config12', offset=0x0000100c*addrSize, bitSize=3, bitOffset=5,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='GlobalCounterStart',    description='Config12', offset=0x0000100c*addrSize, bitSize=8, bitOffset=8,  base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='ROslvdsBit',   description='Config13', offset=0x0000100d*addrSize, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='REFslvdsBit',  description='Config13', offset=0x0000100d*addrSize, bitSize=1, bitOffset=1,  base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='emphBc',       description='Config13', offset=0x0000100d*addrSize, bitSize=3, bitOffset=2,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='emphBd',       description='Config13', offset=0x0000100d*addrSize, bitSize=3, bitOffset=5,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DM1Sel',       description='Config13', offset=0x0000100d*addrSize, bitSize=4, bitOffset=8,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DM2Sel',       description='Config13', offset=0x0000100d*addrSize, bitSize=4, bitOffset=12, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='DacDllGain',      description='Config14', offset=0x0000100e*addrSize, bitSize=2, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DacDll',          description='Config14', offset=0x0000100e*addrSize, bitSize=6, bitOffset=2,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DacTestlineGain', description='Config14', offset=0x0000100e*addrSize, bitSize=2, bitOffset=8,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DacTestline',     description='Config14', offset=0x0000100e*addrSize, bitSize=6, bitOffset=10, base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='DacpfaCompGain',  description='Config15', offset=0x0000100f*addrSize, bitSize=2, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DacpfaComp',      description='Config15', offset=0x0000100f*addrSize, bitSize=6, bitOffset=2,  base=pr.UInt, mode='RW')))
        self.add((
            pr.RemoteVariable(name='LinearDecay',        description='Config16', offset=0x00001010*addrSize, bitSize=3, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BGRctrlDACdll',      description='Config16', offset=0x00001010*addrSize, bitSize=2, bitOffset=3,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BGRctrlDACtestine',  description='Config16', offset=0x00001010*addrSize, bitSize=2, bitOffset=5,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='BGRctrlDACpfaComp',  description='Config16', offset=0x00001010*addrSize, bitSize=2, bitOffset=7,  base=pr.UInt, mode='RW')))
         
        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006001*addrSize, bitSize=8, bitOffset=0, function=pr.Command.touch, hidden=False)))
        
        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006003*addrSize, bitSize=8, bitOffset=0, function=pr.Command.touch, hidden=False)))
            
        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data        
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))   
        

        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.RemoteVariable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'),
        #    pr.RemoteVariable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))



        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))
            
        self.add(
            pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Tixel.TixelFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (48, 48):
                    self._rawWrite(0x00000000*addrSize,0)
                    self._rawWrite(0x00008000*addrSize,0)
                    for x in range (0, 48):
                        for y in range (0, 48):
                            self._rawWrite(0x00006001*addrSize, x)
                            self._rawWrite(0x00006003*addrSize, y) 
                            self._rawWrite(0x00005000*addrSize, (int(matrixCfg[x][y])))
                    self._rawWrite(0x00000000*addrSize,0)
                else:
                    print('csv file must be 48x48 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      


    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Tixel.TixelFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((48,48),dtype='uint16')
                self._rawWrite(0x00000000*addrSize,0)
                self._rawWrite(0x00008000*addrSize,0)
                for x in range (0, 48):
                   for y in range (0, 48):
                      self._rawWrite(0x00006001*addrSize, x)
                      self._rawWrite(0x00006003*addrSize, y) 
                      readBack[x, y] = self._rawRead(0x00005000*addrSize)
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")      


    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Tixel.TixelFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            self.PrepareMultiConfig()
            self.WriteMatrixData.set(0)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")      


    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)
        
    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func

#################################################################################################################################################
##
## Cpix2 ASIC register definition
##
#################################################################################################################################################
class Cpix2Asic(pr.Device):
    def __init__(self, **kwargs):
        """Create registers for Cpix2 ASIC"""
        super().__init__(description='Cpix2 ASIC Configuration', **kwargs)
        
        addrSize = 4	
        
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True, overlapEn=True))
        
        # CMD = 1, Addr = xxx - Register set
        
        self.add(pr.RemoteVariable(name='CompTH1_DAC',   description='Config01', offset=0x00001001*addrSize, bitSize=6,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PulserSync',    description='Config01', offset=0x00001001*addrSize, bitSize=1,  bitOffset=7,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PLL_RO_Reset',  description='Config02', offset=0x00001002*addrSize, bitSize=1,  bitOffset=0,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PLL_RO_Itune',  description='Config02', offset=0x00001002*addrSize, bitSize=3,  bitOffset=1,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PLL_RO_KVCO',   description='Config02', offset=0x00001002*addrSize, bitSize=3,  bitOffset=4,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PLL_RO_filt1a', description='Config02', offset=0x00001002*addrSize, bitSize=1,  bitOffset=7,  base=pr.Bool,  mode='RW', hidden=False, overlapEn=True))
        self.add(pr.RemoteVariable(name='Pulser',        description='Config03', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Pbit',          description='Config03', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='atest',         description='Config03', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='test',          description='Config03', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Sba_test',      description='Config03', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Hrtest',        description='Config03', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PulserR',       description='Config03', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DM1',           description='Config04', offset=0x00001004*addrSize, bitSize=4,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DM2',           description='Config04', offset=0x00001004*addrSize, bitSize=4,  bitOffset=4,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Pulser_DAC',    description='Config05', offset=0x00001005*addrSize, bitSize=3,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Monost_Pulser', description='Config05', offset=0x00001005*addrSize, bitSize=3,  bitOffset=3,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DM1en',         description='Config06', offset=0x00001006*addrSize, bitSize=1,  bitOffset=0,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DM2en',         description='Config06', offset=0x00001006*addrSize, bitSize=1,  bitOffset=1,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='emph_bd',       description='Config06', offset=0x00001006*addrSize, bitSize=3,  bitOffset=2,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='emph_bc',       description='Config06', offset=0x00001006*addrSize, bitSize=3,  bitOffset=5,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='VREF_DAC',      description='Config07', offset=0x00001007*addrSize, bitSize=6,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='VrefLow',       description='Config07', offset=0x00001007*addrSize, bitSize=2,  bitOffset=6,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='TPS_MUX',       description='Config08', offset=0x00001008*addrSize, bitSize=4,  bitOffset=1,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='RO_Monost',     description='Config08', offset=0x00001008*addrSize, bitSize=3,  bitOffset=5,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='TPS_GR',        description='Config09', offset=0x00001009*addrSize, bitSize=4,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='cout',          description='Config09', offset=0x00001009*addrSize, bitSize=1,  bitOffset=5,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='ckc',           description='Config09', offset=0x00001009*addrSize, bitSize=1,  bitOffset=6,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='mod',           description='Config09', offset=0x00001009*addrSize, bitSize=1,  bitOffset=7,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PP_OCB_S2D',    description='Config0A', offset=0x0000100A*addrSize, bitSize=1,  bitOffset=0,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='OCB',           description='Config0A', offset=0x0000100A*addrSize, bitSize=3,  bitOffset=1,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Monost',        description='Config0A', offset=0x0000100A*addrSize, bitSize=3,  bitOffset=4,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='fastPP_enable', description='Config0A', offset=0x0000100A*addrSize, bitSize=1,  bitOffset=7,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Preamp',        description='Config0B', offset=0x0000100B*addrSize, bitSize=3,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Pixel_FB',      description='Config0B', offset=0x0000100B*addrSize, bitSize=3,  bitOffset=3,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Vld1_b',        description='Config0B', offset=0x0000100B*addrSize, bitSize=2,  bitOffset=6,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='CompTH2_DAC',   description='Config0C', offset=0x0000100C*addrSize, bitSize=6,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Vtrim_b',       description='Config0C', offset=0x0000100C*addrSize, bitSize=2,  bitOffset=6,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='tc',            description='Config0D', offset=0x0000100D*addrSize, bitSize=2,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))  
        self.add(pr.RemoteVariable(name='S2D',           description='Config0D', offset=0x0000100D*addrSize, bitSize=3,  bitOffset=2,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='S2D_DAC_Bias',  description='Config0D', offset=0x0000100D*addrSize, bitSize=3,  bitOffset=5,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='TPS_DAC',       description='Config0E', offset=0x0000100E*addrSize, bitSize=6,  bitOffset=2,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PLL_RO_filt1b', description='Config0F', offset=0x0000100F*addrSize, bitSize=2,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', hidden=False, overlapEn=True))
        #self.add(pr.RemoteRemoteVariable(name='PLL_RO_filt1', description='Config_020F', offset=[0x00001002*addrSize,0x0000100F*addrSize], bitSize=[1,2],  bitOffset=[7,0],  base=pr.UInt, disp = '{}',  mode='RW', disp='{#x}', hidden=True, overlapEn=True))
        self.add(pr.RemoteVariable(name='PLL_RO_filter2',description='Config0F', offset=0x0000100F*addrSize, bitSize=3,  bitOffset=2,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='PLL_RO_divider',description='Config0F', offset=0x0000100F*addrSize, bitSize=3,  bitOffset=5,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='test_BE',       description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=0,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DigRO_disable', description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=1,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DelEXEC',       description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=2,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DelCCKreg',     description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=3,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='RO_rst_en',     description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=4,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='SLVDSbit',      description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=5,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Pix_Count_T',   description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=6,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='Pix_Count_sel', description='Config10', offset=0x00001010*addrSize, bitSize=1,  bitOffset=7,  base=pr.Bool,  mode='RW', overlapEn=True))

        self.add(pr.RemoteVariable(name='RowStart',      description='RowStart',       offset=0x00001011*addrSize, bitSize=9,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='WO', overlapEn=True))
        self.add(pr.RemoteVariable(name='RowStop',       description='RowStop',        offset=0x00001012*addrSize, bitSize=9,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='ColumnStart',   description='ColumnStart',    offset=0x00001013*addrSize, bitSize=7,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='WO', overlapEn=True))
        self.add(pr.RemoteVariable(name='ColumnStop',    description='ColumnStop',     offset=0x00001014*addrSize, bitSize=7,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='CHIP ID',       description='CHIP ID',        offset=0x00001015*addrSize, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))

        self.add(pr.RemoteVariable(name='DCycle_DAC',    description='Config16',       offset=0x00001016*addrSize, bitSize=6,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DCycle_en',     description='Config16',       offset=0x00001016*addrSize, bitSize=1,  bitOffset=6,  base=pr.Bool,  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='DCycle_bypass', description='Config16',       offset=0x00001016*addrSize, bitSize=1,  bitOffset=7,  base=pr.Bool,  mode='RW', overlapEn=True))

        self.add(pr.RemoteVariable(name='MSBCompTH1_DAC',description='Config17',       offset=0x00001017*addrSize, bitSize=4,  bitOffset=0,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))
        self.add(pr.RemoteVariable(name='MSBCompTH2_DAC',description='Config17',       offset=0x00001017*addrSize, bitSize=4,  bitOffset=4,  base=pr.UInt, disp = '{}',  mode='RW', overlapEn=True))


        # linked variables
        #self.add(pr.LinkVariable(name='PLL_RO_filter1', description='Config02_0F', typeStr='Linked',  base=pr.UInt,  mode='RW', dependencies=[self.PLL_RO_filt1a, self.PLL_RO_filt1b], overlapEn=True))


        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=8, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))
        
        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=8, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))
            
        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True))

        # CMD = 4, Addr = X  : Write Matrix with data        
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=6, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))   
        

        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=6, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True))

        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.RemoteVariable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'),
        #    pr.RemoteVariable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False, overlapEn=True))

               
        # CMD = 6, Addr = 17 : Row counter[8:0]
#        self.add((
#            pr.RemoteCommand(name='RowStartC', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))      
#        # CMD = 6, Addr = 18 : Bank select [3:0] & Col counter[6:0]
#        self.add((
#            pr.RemoteCommand(name='RowStopC', description='', offset=0x00006012*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))
#        # CMD = 6, Addr = 18 : Bank select [3:0] & Col counter[6:0]
#        self.add((
#            pr.RemoteCommand(name='ColumnStartC', description='', offset=0x00006013*addrSize, bitSize=7, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))
#        # CMD = 6, Addr = 18 : Bank select [3:0] & Col counter[6:0]
#        self.add((
#            pr.RemoteCommand(name='ColumnStopC', description='', offset=0x00006014*addrSize, bitSize=7, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))
#        # CMD = 6, Addr = 18 : Bank select [3:0] & Col counter[6:0]
#        self.add((
#            pr.RemoteCommand(name='ChipIDC', description='', offset=0x00006015*addrSize, bitSize=16, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))
#            
#        # CMD = 2, Addr = X  : Write Row with data
#        self.add((
#            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))#
#
#        # CMD = 3, Addr = X  : Write Column with data
#        self.add(
#            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True))
#
#        # CMD = 4, Addr = X  : Write Matrix with data        
#        self.add((    
#            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True)))   
#        
#
#        # CMD = 5, Addr = X  : Read/Write Pixel with data
#        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False, overlapEn=True))
#
#        # CMD = 7, Addr = X  : Prepare to write chip ID
#        self.add((
#            pr.RemoteVariable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'),
#            pr.RemoteVariable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
#        self.add(
#            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))



        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.LocalCommand(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))
            
        self.add(
            pr.LocalCommand(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.LocalCommand(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Cpix2.Cpix2FpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if not isinstance(arg, str):
               arg = ''
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
               # in PyQt5 QFileDialog returns a tuple
               if usingPyQt5:
                  self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (48, 48):
                    self._rawWrite(0x00000000*addrSize,0)
                    self._rawWrite(0x00008000*addrSize,0)
                    for x in range (0, 48):
                        for y in range (0, 48):
                            self._rawWrite(0x00006011*addrSize, x)
                            self._rawWrite(0x00006013*addrSize, y) 
                            self._rawWrite(0x00005000*addrSize, (int(matrixCfg[x][y])))
                    self._rawWrite(0x00000000*addrSize,0)
                else:
                    print('csv file must be 48x48 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      


    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Cpix2.Cpix2FpgaRegisters.AsicR0Mode.set(True)
        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if not isinstance(arg, str):
               arg = ''
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((48,48),dtype='uint16')
                self._rawWrite(0x00000000*addrSize,0)
                self._rawWrite(0x00008000*addrSize,0)
                for x in range (0, 48):
                   for y in range (0, 48):
                      self._rawWrite(0x00006011*addrSize, x)
                      self._rawWrite(0x00006013*addrSize, y) 
                      readBack[x, y] = self._rawRead(0x00005000*addrSize)
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")      


    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Cpix2.Cpix2FpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            self.PrepareMultiConfig()
            self.WriteMatrixData.set(0)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")      


    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)
        
    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func


#################################################################################################################
#
#  ASIC epix HR ADC prototype
#
#################################################################################################################
class EpixHrAdcAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create the ePix10kaAsic device"""
        super().__init__(description='EpixHrAdc Asic Configuration', **kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
        #it is defined the addrSize variable
        addrSize = 4	

        # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
        # contains this object. In most cases the parent and memBase are the same but they can be 
        # different in more complex bus structures. They will also be different for the top most node.
        # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
        # blocks will be updated.

        #############################################
        # Create block / variable combinations
        #############################################
    
        
        #Setup registers & variables
                
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout',offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True))
        
        # CMD = 1, Addr = 1 
        # TODO: fix CompEn so it is one uint register
        self.add((
            pr.RemoteVariable(name='shvc_DAC',     description='Config1',  offset=0x00001001*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='PulserSync',   description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        self.add((
            pr.RemoteVariable(name='Pll_RO_Reset',    description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Pll_Itune',       description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_KVCO',        description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_filter1LSB',  description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_filter1MSB',  description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW')))
        

        # CMD = 1, Addr = 3  
        self.add((
            pr.RemoteVariable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='sab_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 4 
        self.add((
            pr.RemoteVariable(name='DigMon1', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DigMon2', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
 
        # CMD = 1, Addr = 5 
        self.add((
            pr.RemoteVariable(name='PulserDac',    description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='MonostPulser', description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='RefGenB',      description='Config5',  offset=0x00001005*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 6 
        self.add((
            pr.RemoteVariable(name='Dm1En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Dm2En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='emph_bd',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='emph_bc',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.RemoteVariable(name='VRef_DAC',    description='Config7', offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='VRefLow',     description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.RemoteVariable(name='TpsMux',    description='Config8', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='RoMonost',  description='Config8', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base=pr.UInt,  mode='RW')))     

        # CMD = 1, Addr = 9 
        self.add((
            pr.RemoteVariable(name='TpsGr',       description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Balcony_clk', description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.RemoteVariable(name='PpOcbS2d',     description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Ocb',          description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Monost',       description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='mTest',        description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.RemoteVariable(name='Preamp',  description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2D_1_b', description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Vld1_b',  description='Config11', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.RemoteVariable(name='TS_mux',        description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=0, base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='TS_clk_sel',    description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='CompTH2_DAC',   description='Config12', offset=0x0000100C*addrSize, bitSize=3, bitOffset=3, base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='Vtrim_b',       description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=6, base=pr.UInt,  mode='RW')))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.RemoteVariable(name='TC',         description='Config13', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2d',        description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2dDacBias', description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='Tsd_Tser',   description='Config14', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Tps_DAC',    description='Config14', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='PLL_RO_filter2',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='PLL_RO_divider',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.RemoteVariable(name='TestBe',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DigRO_disable',  description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelExec',        description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelCCKReg',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='RO_rst_en',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='SlvdsBit',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=5, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Pix_Count_T',    description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Pix_Count_Sel',  description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 17 : Row start  address[8:0]
        # CMD = 1, Addr = 18 : Row stop  address[8:0]
        # CMD = 1, Addr = 19 : Col start  address[6:0]
        # CMD = 1, Addr = 20 : Col stop  address[6:0]
        self.add((
            pr.RemoteVariable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='RW')))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.RemoteVariable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=16, bitOffset=0, base=pr.UInt, mode='RO'))

        # CMD = 1, Addr = 22 
        self.add((
            pr.RemoteVariable(name='DCycle_DAC',    description='Config22', offset=0x00001016*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DCycle_en',     description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DCycle_bypass', description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        
        # CMD = 1, Addr = 23
        self.add((
            pr.RemoteVariable(name='Debug_bit',    description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='OSRsel',       description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='SecondOrder',  description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DHg',          description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='RefGenC',      description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=5, base=pr.UInt, mode='RW')))
        
        # CMD = 1, Addr = 24
        self.add((
            pr.RemoteVariable(name='SDclk_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='SDrst_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
        
        
        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))
   
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=4, bitOffset=0,  function=pr.Command.touch, hidden=False))
 
        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.RemoteVariable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'),
        #    pr.RemoteVariable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))




        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (178, 192):
                    self._rawWrite(0x00000000*addrSize,0)
                    self._rawWrite(0x00008000*addrSize,0)
                    for x in range (0, 177):
                        for y in range (0, 192):
                            bankToWrite = int(y/48);
                            if (bankToWrite == 0):
                               colToWrite = 0x700 + y%48;
                            elif (bankToWrite == 1):
                               colToWrite = 0x680 + y%48;
                            elif (bankToWrite == 2):
                               colToWrite = 0x580 + y%48;
                            elif (bankToWrite == 3):
                               colToWrite = 0x380 + y%48;
                            else:
                               print('unexpected bank number')
                            self._rawWrite(0x00006011*addrSize, x)
                            self._rawWrite(0x00006013*addrSize, colToWrite) 
                            self._rawWrite(0x00005000*addrSize, (int(matrixCfg[x][y])))
                    self._rawWrite(0x00000000*addrSize,0)
                else:
                    print('csv file must be 192x178 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((178, 192),dtype='uint16')
                self._rawWrite(0x00000000*addrSize,0)
                self._rawWrite(0x00008000*addrSize,0)
                for x in range (0, 177):
                   for y in range (0, 192):
                      bankToWrite = int(y/48);
                      if (bankToWrite == 0):
                         colToWrite = 0x700 + y%48;
                      elif (bankToWrite == 1):
                         colToWrite = 0x680 + y%48;
                      elif (bankToWrite == 2):
                         colToWrite = 0x580 + y%48;
                      elif (bankToWrite == 3):
                         colToWrite = 0x380 + y%48;
                      else:
                         print('unexpected bank number')
                      self._rawWrite(0x00006011*addrSize, x)
                      self._rawWrite(0x00006013*addrSize, colToWrite)
                      readBack[x, y] = self._rawRead(0x00005000*addrSize)
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")             

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            for i in range (0, 48):
                self.PrepareMultiConfig()
                self.ColCounter.set(i)
                self.WriteColData.set(0)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")          

    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)

    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func







