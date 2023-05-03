#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# Title      : CPix2 array prototype board instance
#-----------------------------------------------------------------------------
# File       : Cpix2LoadFpga.py
# Author     : Maciej Kwiatkowski, mkwiatko@slac.stanford.edu
# Created    : 2016-09-29
# Last update: 2017-02-01
#-----------------------------------------------------------------------------
# Description:
# Rogue interface to ePix 10ka board
#-----------------------------------------------------------------------------
# This file is part of the rogue_example software. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the rogue_example software, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import setupLibPaths

import argparse
import atexit
import signal
import sys
import threading
import time

import ePixFpga as fpga
import ePixViewer as vi
import pyrogue.gui
import pyrogue.utilities.fileio
import pyrogue.utilities.prbs
import rogue.hardware.pgp
import surf
import surf.axi
import surf.protocols.ssi
from surf.devices.micron._AxiMicronN25Q import *
import yaml

import testBridge

try:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *

# Set the argument parser
parser = argparse.ArgumentParser()

# Convert str to bool
argBool = lambda s: s.lower() in ['true', 't', 'yes', '1']

# Add arguments
parser.add_argument(
    "--pollEn",
    type=argBool,
    required=False,
    default=False,
    help="Enable auto-polling",
)

parser.add_argument(
    "--initRead",
    type=argBool,
    required=False,
    default=False,
    help="Enable read all variables at start",
)

parser.add_argument(
    "--pgp",
    type=str,
    required=False,
    default='/dev/pgpcard_0',
    help="PGP devide (default /dev/pgpcard_0)",
)

parser.add_argument(
    "--verbose",
    type=argBool,
    required=False,
    default=False,
    help="Print debug info",
)

parser.add_argument(
    "--mcs",
    type=str,
    required=True,
    help="path to mcs file",
)

# Get the arguments
args = parser.parse_args()

#############################################
#print debug info
PRINT_VERBOSE = args.verbose
#############################################

# Create the PGP interfaces for ePix camera
pgpVc1 = rogue.hardware.pgp.PgpCard(args.pgp, 0, 0)  # Data & cmds
pgpVc0 = rogue.hardware.pgp.PgpCard(args.pgp, 0, 1)  # Registers for ePix board
pgpVc2 = rogue.hardware.pgp.PgpCard(args.pgp, 0, 2)  # PseudoScope
pgpVc3 = rogue.hardware.pgp.PgpCard(args.pgp, 0, 3)  # Monitoring (Slow ADC)

print("")
print("PGP Card Version: %x" % (pgpVc0.getInfo().version))

# Add data stream to file as channel 1
# File writer
dataWriter = pyrogue.utilities.fileio.StreamWriter(name='dataWriter')
pyrogue.streamConnect(pgpVc0, dataWriter.getChannel(0x1))
# Add pseudoscope to file writer
pyrogue.streamConnect(pgpVc2, dataWriter.getChannel(0x2))
pyrogue.streamConnect(pgpVc3, dataWriter.getChannel(0x3))

cmd = rogue.protocols.srp.Cmd()
pyrogue.streamConnect(cmd, pgpVc0)

# Create and Connect SRP to VC1 to send commands
srp = rogue.protocols.srp.SrpV0()
pyrogue.streamConnectBiDir(pgpVc1, srp)


#######################################
# Custom run control
#######################################
class MyRunControl(pyrogue.RunControl):

    def __init__(self, name):
        pyrogue.RunControl.__init__(self,
                                    name,
                                    description='Run Controller Cpix2',
                                    rates={
                                        1: '1 Hz',
                                        2: '2 Hz',
                                        4: '4 Hz',
                                        8: '8 Hz',
                                        10: '10 Hz',
                                        30: '30 Hz',
                                        60: '60 Hz',
                                        120: '120 Hz'
                                    })
        self._thread = None

    def _setRunState(self, dev, var, value, changed):
        if changed:
            if self.runState.get(read=False) == 'Running':
                self._thread = threading.Thread(target=self._run)
                self._thread.start()
            else:
                self._thread.join()
                self._thread = None

    def _run(self):
        self.runCount.set(0)
        self._last = int(time.time())

        while (self.runState.value() == 'Running'):
            delay = 1.0 / (
                {value: key
                 for key, value in self.runRate.enum.items()}[self._runRate])
            time.sleep(delay)
            self._root.ssiPrbsTx.oneShot()

            self._runCount += 1
            if self._last != int(time.time()):
                self._last = int(time.time())
                self.runCount._updated()


##############################
# Set base
##############################
class EpixBoard(pyrogue.Root):

    def __init__(self, cmd, dataWriter, srp, **kwargs):
        super().__init__(name='ePixBoard', description='ePix 100a Board', **kwargs)
        #self.add(MyRunControl('runControl'))
        self.add(dataWriter)

        @self.command()
        def Trigger():
            cmd.sendCmd(0, 0)

        # Add Devices
        self.add(
            fpga.Epix100a(name='ePix100aFPGA',
                          offset=0,
                          memBase=srp,
                          hidden=False,
                          enabled=True))
        self.add(
            pyrogue.RunControl(name='runControl',
                               description='Run Controller Cpix2',
                               cmd=self.Trigger,
                               rates={
                                   1: '1 Hz',
                                   2: '2 Hz',
                                   4: '4 Hz',
                                   8: '8 Hz',
                                   10: '10 Hz',
                                   30: '30 Hz',
                                   60: '60 Hz',
                                   120: '120 Hz'
                               }))


if (PRINT_VERBOSE): dbgData = rogue.interfaces.stream.Slave()
if (PRINT_VERBOSE): dbgData.setDebug(60, "DATA[{}]".format(0))
if (PRINT_VERBOSE): pyrogue.streamTap(pgpVc0, dbgData)

# Create GUI
appTop = QApplication(sys.argv)
ePixBoard = EpixBoard(cmd, dataWriter, srp)
ePixBoard.start(
    # pollEn=args.pollEn,
    # initRead=args.initRead,
    # timeout=5.0,
)

# Create useful pointers
AxiVersion = ePixBoard.ePix100aFPGA.AxiVersion
PROM = ePixBoard.ePix100aFPGA.MicronN25Q

print('###################################################')
print('#                 Old Firmware                    #')
print('###################################################')
AxiVersion.printStatus()

# Program the FPGA's PROM
PROM.LoadMcsFile(args.mcs)

# Check if PROM successfully programmed
if (PROM._progDone):
    print('\nReloading FPGA firmware from PROM ....')
    AxiVersion.FpgaReload()
    time.sleep(10)
    print('\nReloading FPGA done')

    print('###################################################')
    print('#                 New Firmware                    #')
    print('###################################################')
    AxiVersion.printStatus()
else:
    print('Failed to program FPGA')

ePixBoard.stop()
exit()
