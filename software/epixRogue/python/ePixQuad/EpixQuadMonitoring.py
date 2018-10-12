#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : PyRogue AXI Version Module
#-----------------------------------------------------------------------------
# File       : 
# Author     : Maciej Kwiatkowski
# Created    : 2016-09-29
# Last update: 2017-01-31
#-----------------------------------------------------------------------------
# Description:
#-----------------------------------------------------------------------------
# This file is part of the rogue software platform. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue software platform, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import pyrogue as pr
import collections

class EpixQuadMonitor(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Monitoring Core data readout"""
      super().__init__(description='Temperature Sensors Registers', **kwargs)
      
      def getShtHum(var):
         x = var.dependencies[0].value()
         return x / 65535.0 * 100.0
      
      def getShtTemp(var):
         x = var.dependencies[0].value()
         return x / 65535.0 * 175.0 - 45.0
      
      def getNctTemp(var):
         x = var.dependencies[0].value()
         y = var.dependencies[1].value()
         return x * 1.0 + (y >> 6) * 0.25
      
      def getNctTempLoc(var):
         x = var.dependencies[0].value()
         return x * 1.0 
         
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      self.add((pr.RemoteVariable(name='MonitorEn',      description='Enable Monitor',              offset=0x00000000, bitSize=1,  bitOffset=0,  base=pr.Bool, mode='RW')))
      self.add((pr.RemoteVariable(name='MonitorStrEn',   description='Monitor Stream Enabled',      offset=0x00000004, bitSize=1,  bitOffset=0,  base=pr.Bool, mode='RO')))
      self.add((pr.RemoteVariable(name='TrigPrescaler',  description='Monitor Triggger Prescaler',  offset=0x00000008, bitSize=16, bitOffset=0,  base=pr.UInt, mode='RW')))
      self.add((pr.RemoteVariable(name='ShtError',       description='SHT31 Humidity Sensor Error', offset=0x0000000C, bitSize=16, bitOffset=0,  base=pr.UInt, mode='RO')))
      self.add((pr.RemoteVariable(name='ShtHumRaw',      description='SHT31 Humidity Value',        offset=0x00000010, bitSize=16, bitOffset=0,  base=pr.UInt, mode='RO')))
      self.add(pr.LinkVariable(
         name         = 'ShtHum', 
         mode         = 'RO', 
         units        = '%',
         linkedGet    = getShtHum,
         disp         = '{:1.2f}',
         dependencies = [self.ShtHumRaw],
      )) 
      self.add((pr.RemoteVariable(name='ShtTempRaw',     description='SHT31 Temperature Value',     offset=0x00000014, bitSize=16, bitOffset=0,  base=pr.UInt, mode='RO')))
      self.add(pr.LinkVariable(
         name         = 'ShtTemp', 
         mode         = 'RO', 
         units        = 'deg C',
         linkedGet    = getShtTemp,
         disp         = '{:1.2f}',
         dependencies = [self.ShtTempRaw],
      )) 
      self.add((pr.RemoteVariable(name='NctError',       description='NCT218 Temp. Sensor Error',   offset=0x00000018, bitSize=16, bitOffset=0,  base=pr.UInt, mode='RO')))
      self.add((pr.RemoteVariable(name='NctLocTempRaw',  description='NCT218 Local Temp.',          offset=0x0000001C, bitSize=8,  bitOffset=0,  base=pr.UInt, mode='RO')))
      self.add(pr.LinkVariable(
         name         = 'NctLocTemp', 
         mode         = 'RO', 
         units        = 'deg C',
         linkedGet    = getNctTempLoc,
         disp         = '{:1.2f}',
         dependencies = [self.NctLocTempRaw],
      )) 
      self.add((pr.RemoteVariable(name='NctRemTempLRaw', description='NCT218 Remote Temp. L Byte',  offset=0x00000020, bitSize=8,  bitOffset=0,  base=pr.UInt, mode='RO')))
      self.add((pr.RemoteVariable(name='NctRemTempHRaw', description='NCT218 Remote Temp. H Byte',  offset=0x00000024, bitSize=8,  bitOffset=0,  base=pr.UInt, mode='RO')))
      self.add(pr.LinkVariable(
         name         = 'NctRemTemp', 
         mode         = 'RO', 
         units        = 'deg C',
         linkedGet    = getNctTemp,
         disp         = '{:1.2f}',
         dependencies = [self.NctRemTempHRaw, self.NctRemTempLRaw],
      )) 
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func