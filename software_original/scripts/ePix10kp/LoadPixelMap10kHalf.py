import pythonDaq
import time
import struct
import os
import sys
import getopt

def main(argv):
   inputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hi:")
   except getopt.GetoptError:
      print 'LoadPixelMap -i <input tab separated pixel map>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'LoadPixelMap -i <input tab separated pixel map>'
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfile = arg

   pythonDaq.daqOpen("epix",1)
   print 'Resetting all pixels.'
   pixelG  = "False"
   pixelGA = "False"
   pixelTest = "False"
   pixelMask = "False"
   pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelTest","False")
   pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelMask","False")
   pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelG",str(pixelG))
   pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelGA",str(pixelGA))
   pythonDaq.daqSendCommand("WriteMatrixData","0")

   pythonDaq.daqSendCommand("PrepForRead","");
   for row in range(0,48):
      if (row == 0):
         pixelG    = "False"
         pixelGA   = "False"
         pixelTest = "False"
         pixelMask = "True"
      elif (row < 24):
         pixelG    = "False"
         pixelGA   = "False"
         pixelTest = "False"
         pixelMask = "False"
      else:
         pixelG    = "True"
         pixelGA   = "False"
         pixelTest = "False"
         pixelMask = "False"

      pythonDaq.daqSetConfig("digFpga:epix10kpAsic:RowCounter",str(row))
      pythonDaq.daqSendCommand("WriteRowCounter","");
      pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelTest",pixelTest)
      pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelMask",pixelMask)
      pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelG",str(pixelG))
      pythonDaq.daqSetConfig("digFpga:epix10kpAsic:PixelGA",str(pixelGA))
      pythonDaq.daqSendCommand("WriteRowData","");

   print 'Sending prepare for readout'
   pythonDaq.daqSendCommand("PrepForRead","");
            

if __name__ == "__main__":
   main(sys.argv[1:])
          


