#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : local image viewer for the ePix camera images
#-----------------------------------------------------------------------------
# File       : ePixViewer.py
# Author     : Dionisio Doering
# Created    : 2017-02-08
# Last update: 2017-02-08
#-----------------------------------------------------------------------------
# Description:
# Simple image viewer that enble a local feedback from data collected using
# ePix cameras. The initial intent is to use it with stand alone systems
#
#-----------------------------------------------------------------------------
# This file is part of the ATLAS CHESS2 DEV. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ATLAS CHESS2 DEV, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import sys
import os
import rogue.utilities
import rogue.utilities.fileio
import rogue.interfaces.stream
import pyrogue    
import time
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import QObject, pyqtSignal



class Window(QtGui.QMainWindow, QObject):
    """Class that defines the main window for the viewer."""
    
    # Define a new signal called 'trigger' that has no arguments.
    trigger = pyqtSignal()

    def __init__(self):
        super(Window, self).__init__()
      
        # window init
        self.mainWdGeom = [50, 50, 1000, 600] # x, y, width, height
        self.setGeometry(self.mainWdGeom[0], self.mainWdGeom[1], self.mainWdGeom[2],self.mainWdGeom[3])
        self.setWindowTitle("ePix image viewer")

        # add actions for menu item
        extractAction = QtGui.QAction("&Quit", self)
        extractAction.setShortcut("Ctrl+Q")
        extractAction.setStatusTip('Leave The App')
        extractAction.triggered.connect(self.close_viewer)
 
        openFile = QtGui.QAction("&Open File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open a new set of images')
        openFile.setStatusTip('Open file')
        openFile.triggered.connect(self.file_open)

        # display status tips for all menu items (or actions)
        self.statusBar()

        # Creates the main menu, 
        mainMenu = self.menuBar()
        # adds items and subitems
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(extractAction)

        # Create widget
        #screen = QtGui.QDesktopWidget().screenGeometry(self)
        #self.label = QLabel(self)
        #self.label.setGeometry(self.mainWdGeom[0]+100, self.mainWdGeom[1]+100, self.mainWdGeom[2]-200,self.mainWdGeom[3]-200)
        #self.setCentralWidget(self.label)
        #pixmap = QPixmap(os.getcwd() + '~ddoering/Desktop/genDAQScrenshots/GenDAQ10.png')
        #self.label.setPixmap(pixmap)
        self.prepairWindow()

        
        # add all buttons to the screen
        self.def_bttns()

        # rogue interconection
 
        # Create the objects            
        self.fileReader  = rogue.utilities.fileio.StreamReader()
        self.eventReader = EventReader(self)

        # Connect the fileReader to our event processor
        pyrogue.streamConnect(self.fileReader,self.eventReader)

        # Connect the trigger signal to a slot.
        self.trigger.connect(self.displayImageFromReader)
 

        # display the window on the screen after all items have been added 
        self.show()

    def prepairWindow(self):
        # Centre UI
        screen = QtGui.QDesktopWidget().screenGeometry(self)
        size = self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
        #self.setStyleSheet("QWidget{background-color: #000000;}")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.buildUi()
#        self.showFullScreen()

    #creates the main display elemento of the user interface
    def buildUi(self):
        self.label = QtGui.QLabel()
        #self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.move(50,0)
        self.setCentralWidget(self.label)

    # if the image is png or other standard extensio it uses this function to display it.
    def displayImag(self, path):
        print('File name: ', path)
        if path:
            image = QtGui.QImage(path)
            pp = QtGui.QPixmap.fromImage(image)
            self.label.setPixmap(pp.scaled(
                    self.label.size(),
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation))

    # if the image is a rogue type, calls the file readr objetct to read all frames
    def displayImagDat(self, filename):
        print('File name: ', filename)
        self.eventReader.readDataDone = False
        self.eventReader.numAcceptedFrames = 0
        self.fileReader.open(filename)
        # waits until data is found
        timeoutCnt = 0
        while ((self.eventReader.readDataDone == False) and (timeoutCnt < 10)):
             timeoutCnt += 1
             print('Loading image...', self.eventReader.frameIndex, 'atempt',  timeoutCnt)
             time.sleep(0.1)

#        self.displayImageFromReader()

#        self.fileReader.close()

    def displayImageFromReader(self):
        # core code for displaying the image
        arrayLen = len(self.eventReader.frameData)
        print('Image size: ', arrayLen)

        imgWidth = 4*184
        imgHeight = 4*184
        self.image = QtGui.QImage(self.eventReader.frameData, imgWidth, imgHeight, QtGui.QImage.Format_RGB16)
#        for y in range(0,imgHeight):
#            for x in range(0,imgWidth):
#                arrayIndex = x+(y*imgWidth)
#                if (arrayIndex < arrayLen):
#                    data = self.eventReader.frameData[arrayIndex]
#                else:
#                    data = self.eventReader.frameData[0]
                #value = QtGui.qRgb(data, data, data)
                #image.setPixel(x,y,value)
#                self.image.setPixel(x,y,data<<16|data<<8|data)
        pp = QtGui.QPixmap.fromImage(self.image)
        self.label.setPixmap(pp.scaled(self.label.size(),QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))

    def file_open(self):
        self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', '', 'Rogue Images (*.dat);; GenDAQ Images (*.bin);;Any (*.*)')  
        if (os.path.splitext(self.filename)[1] == '.dat'): 
            self.displayImagDat(self.filename)
        else:
            self.displayImag(self.filename)

    def def_bttns(self):

        #button next
        btn = QtGui.QPushButton("Prev", self)
        btn.clicked.connect(self.prevFrame)
        btn.resize(btn.minimumSizeHint())
        btn.move(self.mainWdGeom[2]-100,self.mainWdGeom[3]-200)

        #button next
        btn = QtGui.QPushButton("Next", self)
        btn.clicked.connect(self.nextFrame)
        btn.resize(btn.minimumSizeHint())
        btn.move(self.mainWdGeom[2]-100,self.mainWdGeom[3]-150)

        #button quit
        btn = QtGui.QPushButton("Quit", self)
        btn.clicked.connect(self.close_viewer)
        btn.resize(btn.minimumSizeHint())
        btn.move(self.mainWdGeom[2]-100,self.mainWdGeom[3]-100)


    # display the previous frame from the current file
    def prevFrame(self):
        self.eventReader.frameIndex -= 1
        if (self.eventReader.frameIndex<1):
            self.eventReader.frameIndex = 1
        print('Selected frame ', self.eventReader.frameIndex)
        self.displayImagDat(self.filename)

    # display the next frame from the current file
    def nextFrame(self):
        self.eventReader.frameIndex += 1
        print('Selected frame ', self.eventReader.frameIndex)
        self.displayImagDat(self.filename)


    def close_viewer(self):
        choice = QtGui.QMessageBox.question(self, 'Quit!',
                                            "Do you want to quit viewer?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            print("Exiting now...")
            sys.exit()
        else:
            pass


class EventReader(rogue.interfaces.stream.Slave):
    def __init__(self, parent) :
        rogue.interfaces.stream.Slave.__init__(self)
        super(EventReader, self).__init__()
        self.enable = True
        self.numAcceptedFrames = 0
        self.lastFrame = rogue.interfaces.stream.Frame
        self.frameIndex = 1
        self.frameData = bytearray()
        self.readDataDone = False
        self.parent = parent


    def _acceptFrame(self,frame):
        self.lastFrame = frame
        if self.enable:
            self.numAcceptedFrames += 1
            # Get the channel number
            chNum = (frame.getFlags() >> 24)
            print('-------- Frame ',self.numAcceptedFrames,'Channel flags',frame.getFlags() , ' Accepeted --------' , chNum)
            # Check if channel number is 0x1 (streaming data channel)
            if (chNum == 0x0) :
#                print('-------- Event --------')
                # Collect the data
                p = bytearray(frame.getPayload())
                print('Num. data readout: ', len(p))
                frame.read(p,0)
                cnt = 0
                self.frameData = p
            if ((self.numAcceptedFrames == self.frameIndex) or (self.frameIndex == 0)):              
                self.readDataDone = True
                # Emit the signal.
                self.parent.trigger.emit()
                time.sleep(0.1)
#                    self.parent.displayImageFromReader()

