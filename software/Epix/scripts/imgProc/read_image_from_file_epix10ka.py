#-----------------------------------------------------------------------------
# Title      : read images from file script
#-----------------------------------------------------------------------------
# File       : read_image_from_file.py
# Created    : 2017-06-19
# Last update: 2017-06-21
#-----------------------------------------------------------------------------
# Description:
# Simple image viewer that enble a local feedback from data collected using
# ePix cameras. The initial intent is to use it with stand alone systems
#
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ePix rogue, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import setupLibPaths
import os, sys, time
import numpy as np
import ePixViewer.Cameras as cameras
import ePixViewer.imgProcessing as imgPr
# 
import matplotlib   
#matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import h5py
#matplotlib.pyplot.ion()
MAX_NUMBER_OF_FRAMES_PER_BATCH  = 8000


##################################################
# Global variables
##################################################
cameraType = 'ePix10ka'
bitMask = 0x7fff
PLOT_IMAGE = False
PLOT_IMAGE_DARKSUB = False
SAVEHDF5              = True
##################################################
# Dark images
##################################################
if (len(sys.argv[1])>0):
    filename = sys.argv[1]
else:
    filename = ''

f = open(filename, mode = 'rb')
h5_filename = os.path.splitext(filename)[0]+".hdf5"
f_h5 = h5py.File(h5_filename, "w")

file_header = [0]
numberOfFrames = 0
while ((len(file_header)>0) and (numberOfFrames<MAX_NUMBER_OF_FRAMES_PER_BATCH)):
    try:
        # reads file header [the number of bytes to read, EVIO]
        file_header = np.fromfile(f, dtype='uint32', count=2)
        payloadSize = int(file_header[0]/4)-1 #-1 is need because size info includes the second word from the header
        #print ('size',  file_header)
        newPayload = np.fromfile(f, dtype='uint32', count=payloadSize) #(frame size splited by four to read 32 bit 
        if (numberOfFrames == 0):
            allFrames = [newPayload.copy()]
        else:
            newFrame  = [newPayload.copy()]
            allFrames = np.append(allFrames, newFrame, axis = 0)
        numberOfFrames = numberOfFrames + 1 
        #print ("Payload" , numberOfFrames, ":",  (newPayload[0:5]))
        previousSize = file_header
    except Exception: 
        #e = sys.exc_info()[0]
        #print ("Message\n", e)
        print ('size', file_header, 'previous size', previousSize)
        print("numberOfFrames read: " ,numberOfFrames)


##################################################
# image descrambling
##################################################
currentCam = cameras.Camera(cameraType = cameraType)
currentCam.bitMask = bitMask
#numberOfFrames = allFrames.shape[0]
print("numberOfFrames in the 3D array: " ,numberOfFrames)

if(numberOfFrames==1):
    [frameComplete, readyForDisplay, rawImgFrame] = currentCam.buildImageFrame(currentRawData = [], newRawData = allFrames[0])
    imgDesc = np.array([currentCam.descrambleImage(bytearray(rawImgFrame.tobytes()))])
    imgTrig = np.array([0xffff&rawImgFrame[1]])
else:
    for i in range(0, numberOfFrames):
        #get an specific frame
        [frameComplete, readyForDisplay, rawImgFrame] = currentCam.buildImageFrame(currentRawData = [], newRawData = allFrames[i,:])
    
        #get descrambled image from camera
        if (i==0):
            imgDesc = np.array([currentCam.descrambleImage(bytearray(rawImgFrame.tobytes()))])
            imgTrig = np.array([0xffff&rawImgFrame[1]])
        else:
            imgDesc = np.concatenate((imgDesc, np.array([currentCam.descrambleImage(bytearray(rawImgFrame.tobytes()))])),0)
            imgTrig = np.concatenate((imgTrig, np.array([0xffff&rawImgFrame[1]])),0)
        #print(0xffff&rawImgFrame[1])


##################################################
#from here on we have a set of images to work with
##################################################
#show first image
if PLOT_IMAGE :
    for i in range(0, 10):
        plt.imshow(imgDesc[i,:,:], interpolation='nearest')
        plt.gray()
        plt.colorbar()
        plt.title('First image of :'+filename)
        plt.show()

darkImg = np.mean(imgDesc, axis=0)
print(darkImg.shape)

darkSub = imgDesc - darkImg

if PLOT_IMAGE_DARKSUB :
    for i in range(0, 1):
        plt.imshow(darkSub[i,:,0:31], interpolation='nearest')
        plt.gray()
        plt.colorbar()
        plt.title('First image of :'+filename)
        plt.show()


if(SAVEHDF5):
    print("Saving Hdf5")
    index_h5 ='data'
    f_h5[index_h5] = imgDesc.astype('uint16')
    f_h5['acqCnt'] = imgTrig.astype('uint16')
f_h5.close()

# the histogram of the data
#nbins = 1024
#EnergyTh = -50
#n = np.zeros(nbins)
#for i in range(0, imgDesc.shape[0]):
#    n, bins, patches = plt.hist(darkSub[5,:,:], bins=256, range=(0.0, 256.0), fc='k', ec='k')
#    [x,y] = np.where(darkSub[i,:,32:63]>EnergyTh)
#    h, b = np.histogram(darkSub[i,x,y], np.arange(-nbins/2,nbins/2+1))
#    n = n + h

#plt.bar(b[1:nbins+1],n, width = 0.55)
#plt.show()

