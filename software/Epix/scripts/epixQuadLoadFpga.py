#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# Title      : ePix 100a board instance
#-----------------------------------------------------------------------------
# File       : epix100aDAQ.py evolved from evalBoard.py
# Author     : Ryan Herbst, rherbst@slac.stanford.edu
# Modified by: Dionisio Doering
# Created    : 2016-09-29
# Last update: 2017-02-01
#-----------------------------------------------------------------------------
# Description:
# Rogue interface to ePix 100a board
#-----------------------------------------------------------------------------
# This file is part of the rogue_example software. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue_example software, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import sys
import pyrogue as pr
import pyrogue.gui
import PyQt4.QtGui
import argparse
import time
import rogue.hardware
import ePixQuad as quad

#################################################################

# Set the argument parser
parser = argparse.ArgumentParser()

# Add arguments
parser.add_argument(
    "--type", 
    type     = str,
    required = False,
    default  = 'pgp3_cardG3',
    help     = "define the PCIe card type (either pgp-gen3 or datadev)",
)  

parser.add_argument(
    "--dev", 
    type     = str,
    required = False,
    default  = '/dev/pgpcard_0',
    help     = "path to device",
)  

parser.add_argument(
    "--l", 
    type     = int,
    required = True,
    help     = "PGP lane number [0 ~ 3]",
)

parser.add_argument(
    "--mcs", 
    type     = str,
    required = True,
    help     = "path to mcs file",
)

# Get the arguments
args = parser.parse_args()

#################################################################

# Set base
base = quad.Top(
    hwType = args.type, 
    dev    = args.dev, 
    lane   = args.l,
)    

# Start the system
base.start(
    pollEn   = False,
    initRead = False,
)
    
# Create useful pointers
AxiVersion = base.AxiVersion
PROM       = base.CypressS25Fl

print ( '###################################################')
print ( '#                 Old Firmware                    #')
print ( '###################################################')
AxiVersion.printStatus()

# Program the FPGA's PROM
PROM.LoadMcsFile(args.mcs)

# Check if PROM successfully programmed
if(PROM._progDone):
    print('\nReloading FPGA firmware from PROM ....')
    AxiVersion.FpgaReload()
    time.sleep(10)
    print('\nReloading FPGA done')

    print ( '###################################################')
    print ( '#                 New Firmware                    #')
    print ( '###################################################')
    AxiVersion.printStatus()
else:
    print('Failed to program FPGA')

base.stop()
exit()