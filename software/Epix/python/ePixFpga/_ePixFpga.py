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
import pyrogue as pr
import collections
import os
import ePixAsics as epix
import surf.axi as axi
import surf.protocols.pgp as pgp
import surf.devices.analog_devices as ad
import surf.misc
from surf.devices.micron._AxiMicronN25Q import *
import surf
import numpy as np
import time

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
except ImportError:
    from PyQt4.QtCore    import *
    from PyQt4.QtGui     import *


################################################################################################
##
## epixM32Array Classes definition
##
################################################################################################
class EpixM32Array(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "EPIXM32ARRAY FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 5:'AsicR1', 7:'AsicR2', 8:'AsicR3', 6:'AsicClk', 9:'AsicStart', 10:'AsicSample'}
      #TODO: assign meaningful channel names
      inChaEnum={
            8: 'ASIC_OUT1', 3: 'ASIC_OUT2',  0: 'NONE00',   1: 'NONE01',    
            2: 'NONE02',    4: 'NONE04',     5: 'NONE05',   6: 'NONE06',
            7: 'NONE07',    9: 'NONE09',     10:'NONE10',   11:'NONE11', 
            12:'NONE12',    13:'NONE13',     14:'NONE14',   15:'NONE15'}
      inChbEnum={
            8: 'ASIC_OUT1', 3: 'ASIC_OUT2',  0: 'NONE00',   1: 'NONE01',    
            2: 'NONE02',    4: 'NONE04',     5: 'NONE05',   6: 'NONE06',
            7: 'NONE07',    9: 'NONE09',     10:'NONE10',   11:'NONE11', 
            12:'NONE12',    13:'NONE13',     14:'NONE14',   15:'NONE15'}
      #In order to easely compare GedDAQ address map with the eprix rogue address map 
      #it is defined the addrSize RemoteVariable
      addrSize = 4	
      
      super(self.__class__, self).__init__(**kwargs)
      self.add((
            axi.AxiVersion(offset=0x00000000, expand=False),
            EpixM32ArrayFpgaRegisters(name="EpixM32ArrayFpgaRegisters", offset=0x01000000, expand=True),
            TriggerRegisters(name="TriggerRegisters", offset=0x02000000, expand=False),
            SlowAdcRegisters(name="SlowAdcRegisters", offset=0x03000000, expand=False),
            OscilloscopeRegisters(name='Oscilloscope', offset=0x0B000000, enabled=False, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            pgp.Pgp2bAxi(name='Pgp2bAxi', offset=0x04000000, expand=False),
            ad.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[0]', offset=0x07000000, channels=8, enabled=False, expand=False),
            ad.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[1]', offset=0x08000000, channels=8, enabled=False, expand=False),
            ad.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x09000000, enabled=False, expand=False),
            ad.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x09000800, enabled=False, expand=False),
            AxiMicronN25Q(name='MicronN25Q',              offset=0x05000000, expand=False, hidden=False),
            #ad.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x09001000, enabled=False, expand=False),
            #axi.AxiStreamMonitoring(name='RdoutStreamMonitoring', offset=0x0C000000, enabled=True, expand=False, numberLanes=2),
            MicroblazeLog(name='MicroblazeLog', offset=0x0A000000, enabled=False, expand=False)))
      

class EpixM32ArrayFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Epix"""
      super().__init__(description='Epix Configuration Registers', **kwargs)	
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      self.add(pr.RemoteVariable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdDigitalLow',    description='IdDigitalLow',      offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdDigitalHigh',   description='IdDigitalHigh',     offset=0x00000008, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdAnalogLow',     description='IdAnalogLow',       offset=0x0000000C, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdAnalogHigh',    description='IdAnalogHigh',      offset=0x00000010, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdCarrierLow',    description='IdCarrierLow',      offset=0x00000014, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdCarrierHigh',   description='IdCarrierHigh',     offset=0x00000018, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      
      self.add(pr.RemoteVariable(name='AsicR1Tr1',       description='AsicR1Tr1',         offset=0x00000100, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR2Tr1',       description='AsicR2Tr1',         offset=0x00000104, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR3Tr1',       description='AsicR3Tr1',         offset=0x00000108, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR1Tr2',       description='AsicR1Tr2',         offset=0x0000010C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR2Tr2',       description='AsicR2Tr2',         offset=0x00000110, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR3Tr2',       description='AsicR3Tr2',         offset=0x00000114, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR1Test',      description='AsicR1Test',        offset=0x00000118, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicClkDly',      description='AsicClkDly',        offset=0x0000011C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicClkPerHalf',  description='AsicClkPerHalf',    offset=0x00000120, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicSampleDly',   description='AsicSampleDly',     offset=0x00000124, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='TrigOutDelay',    description='TrigOutDelay',      offset=0x00000128, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='TrigOutLength',   description='TrigOutLength',     offset=0x0000012C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicClkMaskEn',   description='AsicClkMaskEn',     offset=0x00000130, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicClkMaskCnt',  description='AsicClkMaskCnt',    offset=0x00000134, bitSize=11, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR3ForceLow',  description='AsicR3ForceLow',    offset=0x00000138, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR3ForceHigh', description='AsicR3ForceHigh',   offset=0x0000013C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR2ForceLow',  description='AsicR2ForceLow',    offset=0x00000140, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR2ForceHigh', description='AsicR2ForceHigh',   offset=0x00000144, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR1ForceLow',  description='AsicR1ForceLow',    offset=0x00000148, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR1ForceHigh', description='AsicR1ForceHigh',   offset=0x0000014C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      
      self.add((
         pr.RemoteVariable(name='AsicDigitalPwrEnable',  description='AsicPower', offset=0x00000200, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicAnalogPwrEnable',   description='AsicPower', offset=0x00000200, bitSize=1, bitOffset=1,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='FpgaOutputEnable',      description='AsicPower', offset=0x00000200, bitSize=1, bitOffset=2,  base=pr.Bool, mode='RW')))
      self.add(pr.RemoteVariable(name='DebugSel1',       description='DebugSel1', offset=0x00000204, bitSize=5, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='DebugSel2',       description='DebugSel2', offset=0x00000208, bitSize=5, bitOffset=0, base=pr.UInt,  mode='RW'))
      
      self.add(pr.RemoteVariable(name='AdcClkHalfT',     description='AdcClkHalfT',       offset=0x00000300, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add((
         pr.RemoteVariable(name='StartupReq',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='StartupAck',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=1, base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='StartupFail', description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=2, base=pr.Bool, mode='RO')))
      
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

################################################################################################
##
## epixMsh Classes definition
##
################################################################################################
class EpixMsh(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "EPIXMSH FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicCk', 5:'AsicRst', 6:'AsicCdsBline', 7:'AsicRstComp', 8:'AsicSampleN', 9:'AsicDinjEn', 10:'AsicCKinjEn'}
      inChaEnum={0: 'ASIC_BUFOUT', 1: 'ASIC_COMPOUT'}
      inChbEnum={0: 'ASIC_BUFOUT', 1: 'ASIC_COMPOUT'}
      
      
      
      super(self.__class__, self).__init__(**kwargs)
      self.add(axi.AxiVersion(offset=0x00000000, expand=False))
      self.add(EpixMshFpgaRegisters(name="EpixMshFpgaRegisters", offset=0x01000000, expand=True))
      self.add(EpixMshDACs(name="EpixMshDACs[0]", offset=0x01300000, expand=False, DACaName='ASIC_Vthr', DACbName='ASIC_V_precharge'))
      self.add(EpixMshDACs(name="EpixMshDACs[1]", offset=0x01300040, expand=False, DACaName='ASIC_V_Inj', DACbName='spare'))
      self.add(TriggerRegisters(name="TriggerRegisters", offset=0x01100000, expand=False, BaseClock=100000000))
      self.add(SlowAdcRegisters(name="SlowAdcRegisters", offset=0x03000000, expand=False))
      self.add(OscilloscopeRegisters(name='Oscilloscope', offset=0x01200000, enabled=False, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum))
      self.add(pgp.Pgp2bAxi(name='Pgp2bAxi', offset=0x02000000, expand=False, enabled=False))
      for i in range(3):
         if i == 2:
            channels = 4
         else:
            channels = 8
         self.add(ad.Ad9249ReadoutGroup      (name = ('Ad9249RdoutAdc[%d]'%i),   offset=(0x04100000+i*0x100000), channels=channels, enabled=False, expand=False))
      for i in range(3):
         self.add(ad.Ad9249ConfigGroup       (name = ('Ad9249ConfigAdc[%d]'%i),  offset=(0x04400000+i*0x000800), enabled=False, expand=False))
      self.add(AxiMicronN25Q(name='MicronN25Q',    offset=0x05000000, expand=False, hidden=False))
      self.add(MicroblazeLog(name='MicroblazeLog', offset=0x06000000, enabled=False, expand=False))
      
      self.add(pr.LocalCommand(name='InjDacRamp',  description='[start, stop, step, points, dly]', value=[0,0,0,0,0] ,function=self.injDacRamp))
   
   def injDacRamp(self, dev, cmd, arg):
      """InjDacRamp command function"""       
      print("InjDacRamp started")
      arguments = np.asarray(arg)
      dacStart = arguments[0]
      dacStop = arguments[1]
      dacStep = arguments[2]
      dacPoints = arguments[3]
      dacDly = arguments[4]
      for dacVal in range(dacStart, dacStop, dacStep):
         print('Set DAC to %d'%dacVal)
         self.EpixMshDACs[1].ASIC_V_Inj.set(int(dacVal))
         for pts in range(dacPoints):
            time.sleep(dacDly/1000) 
            #print('trigger %d'%pts)
            self.root.Trigger()
   
   

class EpixMshFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Epix"""
      super().__init__(description='Epix Configuration Registers', **kwargs)	
      
      def getFreqMHz(var):
         x = var.dependencies[0].value()
         return x / 1000000.0
      
      def getPerUs(var):
         x = var.dependencies[0].value()
         baseClk = self.BaseClock.get()
         if baseClk > 0:
            return x / (baseClk/1000000.0)
         else:
            return 0
               
      def setPerUs(deps):
         def setUsValue(var, value, write):
            rawVal = int(round(value*(self.BaseClock.get()/1000000.0)))
            deps[0].set(rawVal,write)            
         return setUsValue
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      self.add(pr.RemoteVariable(name='DigPowerEn',            description='DigPowerEn',              offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AnaPowerEn',            description='AnaPowerEn',              offset=0x00000000, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='FpgaOutEn',             description='FpgaOutEn',               offset=0x00000000, bitSize=1,  bitOffset=2, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='DbgMux0',               description='DbgMux0',                 offset=0x00000004, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='DbgMux1',               description='DbgMux1',                 offset=0x00000008, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AdcClkHalfPer',         description='AdcClkHalfPer',           offset=0x0000000C, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='StartupReq',            description='StartupReq',              offset=0x00000010, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StartupAck',            description='StartupAck',              offset=0x00000010, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StartupFail',           description='StartupFail',             offset=0x00000010, bitSize=1,  bitOffset=2, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='BaseClock',             description='FPGA base clk',           offset=0x00000014, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.LinkVariable(  name='BaseClockMHz',          dependencies=[self.BaseClock],         mode='RO', units='MHz', linkedGet=getFreqMHz, disp='{:1.6f}')) 
      self.add(pr.RemoteVariable(name='CompOutThreshold',      description='CompOutThreshold',        offset=0x00000018, bitSize=14, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AdcPipelineDly',        description='AdcPipelineDly',          offset=0x0000001C, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      
      self.add(pr.RemoteVariable(name='AsicRstPol',            description='AsicRstPol',              offset=0x00000100, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicRstDly',            description='AsicRstDly',              offset=0x00000104, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicRstDlyUs',          dependencies=[self.AsicRstDly],        mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicRstDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicRstWidth',          description='AsicRstWidth',            offset=0x00000108, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicRstWidthUs',        dependencies=[self.AsicRstWidth],      mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicRstWidth]), disp='{:1.5f}')) 
      
      self.add(pr.RemoteVariable(name='AsicCdsBlinePol',       description='AsicCdsBlinePol',         offset=0x0000010C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicCdsBlineDly',       description='AsicCdsBlineDly',         offset=0x00000110, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicCdsBlineDlyUs',     dependencies=[self.AsicCdsBlineDly],   mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicCdsBlineDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicCdsBlineWidth',     description='AsicCdsBlineWidth',       offset=0x00000114, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicCdsBlineWidthUs',   dependencies=[self.AsicCdsBlineWidth], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicCdsBlineWidth]), disp='{:1.5f}')) 
      
      self.add(pr.RemoteVariable(name='AsicRstCompPol',        description='AsicRstCompPol',          offset=0x00000118, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicRstCompDly',        description='AsicRstCompDly',          offset=0x0000011C, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicRstCompDlyUs',      dependencies=[self.AsicRstCompDly],    mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicRstCompDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicRstCompWidth',      description='AsicRstCompWidth',        offset=0x00000120, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicRstCompWidthUs',    dependencies=[self.AsicRstCompWidth],  mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicRstCompWidth]), disp='{:1.5f}')) 
      
      self.add(pr.RemoteVariable(name='AsicSampleNPol',        description='AsicSampleNPol',          offset=0x00000124, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicSampleNDly',        description='AsicSampleNDly',          offset=0x00000128, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicSampleNDlyUs',      dependencies=[self.AsicSampleNDly],    mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicSampleNDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicSampleNWidth',      description='AsicSampleNWidth',        offset=0x0000012C, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicSampleNWidthUs',    dependencies=[self.AsicSampleNWidth],  mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicSampleNWidth]), disp='{:1.5f}')) 
      
      self.add(pr.RemoteVariable(name='AsicGRPol',             description='AsicGRPol',               offset=0x00000130, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicGRDly',             description='AsicGRDly',               offset=0x00000134, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicGRDlyUs',           dependencies=[self.AsicGRDly],         mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicGRDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicGRWidth',           description='AsicGRWidth',             offset=0x00000138, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicGRWidthUs',         dependencies=[self.AsicGRWidth],       mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicGRWidth]), disp='{:1.5f}')) 
      
      self.add(pr.RemoteVariable(name='AsicRdDly',             description='AsicRdDly',               offset=0x00000200, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicRdDlyUs',           dependencies=[self.AsicRdDly],         mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicRdDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicRdHalfPer',         description='AsicRdHalfPer',           offset=0x00000204, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='AsicRdHalfPerUs',       dependencies=[self.AsicRdHalfPer],     mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicRdHalfPer]), disp='{:1.5f}')) 
      
      self.add(pr.RemoteVariable(name='IRegEn',                description='IRegEn',                  offset=0x00000210, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='IRegDly',               description='IRegDly',                 offset=0x00000214, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='IRegDlyUs',             dependencies=[self.IRegDly],           mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.IRegDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='IRegClkHalfPer',        description='IRegClkHalfPer',          offset=0x00000218, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='IRegClkHalfPerUs',      dependencies=[self.IRegClkHalfPer],    mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.IRegClkHalfPer]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='IRegDregLow',           description='IRegDregLow',             offset=0x0000021C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='IRegDregHigh',          description='IRegDregHigh',            offset=0x00000220, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      
      self.add(pr.RemoteVariable(name='OverSampleEn',          description='OverSampleEn',            offset=0x00000230, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='OverSampleSize',        description='OverSampleSize',          offset=0x00000234, bitSize=3,  bitOffset=0, base=pr.UInt, mode='RW'))
      
      self.add(pr.RemoteVariable(name='IDacEn',                description='IDacEn',                  offset=0x00000240, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='IDacStart',             description='IDacStart',               offset=0x00000244, bitSize=12, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='IDacStop',              description='IDacStop',                offset=0x00000248, bitSize=12, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='IDacStep',              description='IDacStep',                offset=0x0000024C, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='IDacPoints',            description='IDacPoints',              offset=0x00000250, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      
      for i in range(9):
         self.add(pr.RemoteVariable(name=('EnvData[%d]'%i),    description=('EnvData[%d]'%i),         offset=(0x00000300+i*4), bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'))
      
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

class EpixMshDACs(pr.Device):
   def __init__(self, DACaName = 'DAC_A', DACbName = 'DAC_B', **kwargs):
      """Create the configuration device for EpixMsh carrier DACs"""
      super().__init__(description='EpixMsh DACs Configuration Registers', **kwargs)	
      
      def setVolt(deps):
         def setUsValue(var, value, write):
            rawVal = int(round(value/1.8*(2**12-1)))
            deps[0].set(rawVal,write)            
         return setUsValue
      
      def getVolt(var):
         x = var.dependencies[0].value()
         return x/(2**12-1)*1.8
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      self.add(pr.RemoteVariable(name=DACaName,    description=DACaName, offset=0x00000009*4, bitSize=12,  bitOffset=0, base=pr.UInt, mode='WO'))
      self.add(pr.LinkVariable(name=DACaName+'_V', dependencies=[getattr(self, DACaName)],    mode='WO', linkedGet=getVolt, linkedSet=setVolt([getattr(self, DACaName)]), disp='{:1.2f}', units='V'))
      
      self.add(pr.RemoteVariable(name=DACbName,    description=DACbName, offset=0x0000000A*4, bitSize=12,  bitOffset=0, base=pr.UInt, mode='WO'))
      self.add(pr.LinkVariable(name=DACbName+'_V', dependencies=[getattr(self, DACbName)],    mode='WO', linkedGet=getVolt, linkedSet=setVolt([getattr(self, DACbName)]), disp='{:1.2f}', units='V'))


################################################################################################
##
## Cpix2 Class definition
##
################################################################################################
class Cpix2(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "Cpix2 FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
      inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
      inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
      
      super(self.__class__, self).__init__(**kwargs)
      self.add((
            axi.AxiVersion(                   name="AxiVersion", description="AXI-Lite Version Module", memBase=None, offset=0x00000000, hidden =  False, expand=False),
            Cpix2FpgaRegisters(               name="Cpix2FpgaRegisters",      offset=0x01000000, enabled=True),
            TriggerRegisters(                 name="TriggerRegisters",        offset=0x02000000, enabled=True, expand=False),
            SlowAdcRegisters(                 name="SlowAdcRegisters",        offset=0x03000000, enabled=False, expand=False),
            epix.Cpix2Asic(                   name='Cpix2Asic0',              offset=0x04000000, size=0x3fffff, enabled=False, expand=False),
            epix.Cpix2Asic(                   name='Cpix2Asic1',              offset=0x04400000, size=0x3fffff, enabled=False, expand=False),
            pgp.Pgp2bAxi(                     name='Pgp2bAxi',                offset=0x06000000, enabled=False, expand=False),
            AxiMicronN25Q(                    name='MicronN25Q',              offset=0x07000000, expand=False, hidden=False),
            ad.Ad9249ReadoutGroup(name='Ad9249Rdout[1].Adc[0]',   offset=0x09000000, channels=4, enabled=False, expand=False),
            #ad.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x0A000000),    # not used in tixel, disabled by microblaze
            #ad.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x0A000800),    # not used in tixel, disabled by microblaze
            ad.Ad9249ConfigGroup( name='Ad9249Config[1].Adc[0]',  offset=0x0A001000, enabled=False, expand=False),
            MicroblazeLog(                    name='MicroblazeLog',           offset=0x0B000000, enabled=False, expand=False),
            OscilloscopeRegisters(            name='Oscilloscope',            offset=0x0C000000, enabled=False, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            MMCM7Registers(                   name='MMCM7Registers',          offset=0x0D000000, enabled=False, expand=False),
            AsicDeserRegisters(               name='Asic0Deserializer',       offset=0x0E000000, enabled=False, expand=False),
            AsicDeserRegisters(               name='Asic1Deserializer',       offset=0x0F000000, enabled=False, expand=False),
            AsicPktRegisters(                 name='Asic0PktRegisters',       offset=0x10000000, enabled=False, expand=False),
            AsicPktRegisters(                 name='Asic1PktRegisters',       offset=0x11000000, enabled=False, expand=False),
            ))
      

class Cpix2FpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Cpix2"""
      super().__init__(description='Cpix2 Configuration Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      debugChEnum={0:'Asic01DM', 1:'AsicSync', 2:'AsicEnA', 3:'AsicAcq', 4:'AsicEnB', 5:'AsicR0', 6:'SaciClk', 7:'SaciCmd', 8:'saciRsp', 9:'SaciSelL(0)', 10:'SaciSelL(1)', 11:'asicRdClk', 12:'bitClk', 13:'byteClk', 14:'asicSR0', 15: 'acqStart'}

      #Setup registers & RemoteVariables
      
      #self.add(pr.RemoteVariable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  verify = False, mode='RW'))
      #self.add(pr.RemoteVariable(name='IdDigitalLow',    description='IdDigitalLow',      offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      #self.add(pr.RemoteVariable(name='IdDigitalHigh',   description='IdDigitalHigh',     offset=0x00000008, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      #self.add(pr.RemoteVariable(name='IdAnalogLow',     description='IdAnalogLow',       offset=0x0000000C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      #self.add(pr.RemoteVariable(name='IdAnalogHigh',    description='IdAnalogHigh',      offset=0x00000010, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      #self.add(pr.RemoteVariable(name='IdCarrierLow',    description='IdCarrierLow',      offset=0x00000014, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      #self.add(pr.RemoteVariable(name='IdCarrierHigh',   description='IdCarrierHigh',     offset=0x00000018, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='R0Polarity',      description='R0Polarity',        offset=0x00000410, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='R0Delay',         description='R0Delay',           offset=0x00000414, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',  mode='RW'))
      self.add(pr.RemoteVariable(name='R0Width',         description='R0Width',           offset=0x00000418, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',  mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base=pr.Bool, verify = False,  mode='RW'))
      #self.add(pr.RemoteVariable(name='GlblRstDelay',    description='GlblRstDelay',      offset=0x00000110, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      #self.add(pr.RemoteVariable(name='GlblRstWidth',    description='GlblRstWidth',      offset=0x00000114, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqPolarity',     description='AcqPolarity',         offset=0x00000118, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay1',       description='AcqDelay',            offset=0x0000011C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth1',       description='AcqWidth',            offset=0x00000120, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='EnAPattern',      description='EnAPattern',          offset=0x00000124, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RW'))
      self.add(pr.RemoteVariable(name='EnAShiftPattern', description='EnAShiftPattern',     offset=0x00000128, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='EnAPolarity',     description='EnAPolarity',         offset=0x0000012C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='EnADelay',        description='EnADelay',            offset=0x00000130, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='EnAWidth',        description='EnAWidth',            offset=0x00000134, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='EnBPattern',      description='EnBPattern',          offset=0x00000224, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RW'))
      self.add(pr.RemoteVariable(name='EnBShiftPattern', description='EnBShiftPattern',     offset=0x00000228, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='EnBPolarity',     description='EnBPolarity',         offset=0x0000022C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='EnBDelay',        description='EnBDelay',            offset=0x00000230, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='EnBWidth',        description='EnBWidth',            offset=0x00000234, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ReqTriggerCnt',     description='ReqTriggerCnt',     offset=0x00000138, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='triggerCntPerCycle',description='triggerCntPerCycle',offset=0x0000013C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnAllFrames',       description='EnAllFrames',       offset=0x00000140, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='EnSingleFrame',     description='EnSingleFrame',     offset=0x00000140, bitSize=1,  bitOffset=1, base=pr.Bool, verify = False, mode='RW'))

      self.add(pr.RemoteVariable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='FastSyncPolarity',description='FastSyncPolarity',  offset=0x0000015C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='FastSyncDelay',   description='FastSyncDelay',     offset=0x00000160, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='FastSyncWidth',   description='FastSyncWidth',     offset=0x00000164, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncPolarity',    description='SyncPolarity',      offset=0x00000168, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncDelay',       description='SyncDelay',         offset=0x0000016C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncWidth',       description='SyncWidth',         offset=0x00000170, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000174, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x00000178, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x0000017C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Polarity',     description='SR0Polarity',       offset=0x00000180, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Delay1',       description='SR0Delay1',         offset=0x00000184, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Width1',       description='SR0Width1',         offset=0x00000188, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Delay2',       description='SR0Delay2',         offset=0x0000018C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Width2',       description='SR0Width2',         offset=0x00000190, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SerialReSyncPolarity',description='Serial resync polarity',  offset=0x00000400, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SerialReSyncDelay',   description='Serial resync delay',     offset=0x00000404, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SerialReSyncWidth',   description='Serial resync width',     offset=0x00000408, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='Vid',             description='Vid',               offset=0x00000194, bitSize=1,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AsicWfEnOut',     description='Output enable',     offset=0x00000198, bitSize=13,  bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RW'))
      
      self.add(pr.RemoteVariable(name='AcqCnt',          description='AcqCnt',            offset=0x00000200, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SaciPrepRdoutCnt',description='SaciPrepRdoutCnt',  offset=0x00000204, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',     offset=0x00000208, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      #self.add(pr.RemoteVariable(name='AsicPowerEnable', description='AsicPowerEnable',   offset=0x0000020C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add((
         pr.RemoteVariable(name='AsicPwrEnable',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManual',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=16, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualDig',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=20, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualAna',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=21, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualIo',    description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=22, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualFpga',  description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=23, base=pr.Bool, mode='RW')))
      self.add(pr.RemoteVariable(name='AsicMask',        description='AsicMask',          offset=0x00000210, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='VguardDacSetting',description='VguardDacSetting',  offset=0x00000214, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
              #pr.RemoteVariable(name='TriggerChannel',  description='Setting1',          offset=0x00000008, bitSize=4,  bitOffset=2, base='enum', mode='RW', enum=trigChEnum),
      self.add(pr.RemoteVariable(name='Cpix2DebugSel1',  description='Cpix2DebugSel1',    offset=0x00000218, bitSize=5,  bitOffset=0, mode='RW', enum=debugChEnum))
      self.add(pr.RemoteVariable(name='Cpix2DebugSel2',  description='Cpix2DebugSel2',    offset=0x0000021C, bitSize=5,  bitOffset=0, mode='RW', enum=debugChEnum))
      self.add(pr.RemoteVariable(name='SyncCnt',         description='SyncCnt',           offset=0x00000220, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))      

      self.add(pr.RemoteVariable(name='AdcClkHalfT',     description='AdcClkHalfT',       offset=0x00000300, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add((
         pr.RemoteVariable(name='StartupReq',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='StartupAck',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=1, base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='StartupFail', description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=2, base=pr.Bool, mode='RO')))
      
      
      
      
      
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




##################################################################################################
#
# epix HR prototype class definition
#
##################################################################################################
class HrPrototype(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR prototype FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A', 2:'DAC B', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            axi.AxiVersion(                   name="AxiVersion",               description="AXI-Lite Version Module", enabled=False, memBase=None, offset=0x00000000, hidden =  False, expand=False),
            HrPrototypeFpgaRegisters(         name="HrPrototypeFpgaRegisters", offset=0x01000000, enabled=False, expand=False),
            TriggerRegisters(                 name="TriggerRegisters",         offset=0x02000000, enabled=False, expand=False),
            SlowAdcRegisters(                 name="SlowAdcRegisters",         offset=0x03000000, enabled=False, expand=False),
            epix.EpixHrAdcAsic(               name='HrAdcAsic0',               offset=0x04000000, enabled=False, expand=False),
            #epix.EpixHrAdcAsic(               name='HrAdcAsic1',               offset=0x04400000, enabled=False, expand=False),
            AsicDeserHrRegisters(             name='Asic0Deserializer',        offset=0x10000000, enabled=False, expand=False),
            AsicDeserHrRegisters(             name='Asic1Deserializer',        offset=0x11000000, enabled=False, expand=False),
            AsicPktRegistersHr(               name='Asic0PktRegisters',        offset=0x12000000, enabled=False, expand=False),
            AsicPktRegistersHr(               name='Asic1PktRegisters',        offset=0x13000000, enabled=False, expand=False),
            pgp.Pgp2bAxi(                     name='Pgp2bAxi',                 offset=0x06000000, enabled=False, expand=False),
            ad.Ad9249ReadoutGroup(name='Ad9249Rdout[1].Adc[0]',    offset=0x09000000, channels=4, enabled=False, expand=False),
            ad.Ad9249ConfigGroup( name='Ad9249Config[1].Adc[0]',   offset=0x0A000000, enabled=False, expand=False),
            OscilloscopeRegisters(            name='Oscilloscope',             offset=0x0C000000, enabled=False, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            HighSpeedDacRegisters(            name='HighSpeedDAC',             offset=0x0D000000, enabled=False, expand=False, HsDacEnum = HsDacEnum),
            #pr.MemoryDevice(                  name='WaveformMem',              offset=0x0E000000, wordBitSize=16, stride=4, size=1024*4),
            WaveformMemoryDevice(             name='WaveformMem',              offset=0x0E000000, enabled=False, wordBitSize=16, stride=4, size=1025*4),
            MicroblazeLog(                    name='MicroblazeLog',            offset=0x0B000000, enabled=False, expand=False),
            MMCM7Registers(                   name='MMCM7Registers',           offset=0x0F000000, enabled=False, expand=False),
            AsicTSPktRegisters(               name='AsicTSPktRegisters',       offset=0x14000000, enabled=False, expand=False),
            TSWaveCtrlEpixHR(                 name='TSExternalClkRegisters',   offset=0x15000000, enabled=False, expand=False)))


   
class HrPrototypeFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for HR prototype"""
      super().__init__(description='HR prototype Configuration Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      debugChEnum={0 :'Asic01DM',     1:'AsicSync',     2:'AsicEnA',      3:'AsicAcq',    4:'AsicEnB', 5:'AsicSR0',   6:'SaciClk',  7:'SaciCmd',  
                   8 :'saciRsp',      9:'SaciSelL(0)', 10:'SaciSelL(1)', 11:'asicRdClk', 12:'bitClk', 13:'byteClk', 14:'dacDin',  15: 'dacSclk',
                   16:'dacCsL',      17:'dacLdacL',    18: 'dacClrL'}      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='IdDigitalLow',    description='IdDigitalLow',      offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdDigitalHigh',   description='IdDigitalHigh',     offset=0x00000008, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdAnalogLow',     description='IdAnalogLow',       offset=0x0000000C, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdAnalogHigh',    description='IdAnalogHigh',      offset=0x00000010, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdCarrierLow',    description='IdCarrierLow',      offset=0x00000014, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdCarrierHigh',   description='IdCarrierHigh',     offset=0x00000018, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='WO', verify=False))
      self.add(pr.RemoteVariable(name='GlblRstDelay',    description='GlblRstDelay',      offset=0x00000110, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW', verify=False))
      self.add(pr.RemoteVariable(name='GlblRstWidth',    description='GlblRstWidth',      offset=0x00000114, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqPolarity',     description='AcqPolarity',       offset=0x00000118, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay1',       description='AcqDelay1',         offset=0x0000011C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth1',       description='AcqWidth1',         offset=0x00000120, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay2',       description='AcqDelay2',         offset=0x00000124, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth2',       description='AcqWidth2',         offset=0x00000128, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='TpulsePolarity',  description='TpulsePolarity',    offset=0x0000012C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='TpulseDelay',     description='TpulseDelay',       offset=0x00000130, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='TpulseWidth',     description='TpulseWidth',       offset=0x00000134, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='StartPolarity',   description='StartPolarity',     offset=0x00000138, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StartDelay',      description='StartDelay',        offset=0x0000013C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='StartWidth',      description='StartWidth',        offset=0x00000140, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncPolarity',    description='SyncPolarity',      offset=0x0000015C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncDelay',       description='SyncDelay',         offset=0x00000160, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncWidth',       description='SyncWidth',         offset=0x00000164, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000168, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x0000016C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x00000170, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Polarity',     description='SR0Polarity',       offset=0x00000174, bitSize=1,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Delay',        description='SR0Delay',          offset=0x00000178, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Width',        description='SR0Width',          offset=0x0000017C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      
      self.add(pr.RemoteVariable(name='AcqCnt',          description='AcqCnt',            offset=0x00000200, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='SaciPrepRdoutCnt',description='SaciPrepRdoutCnt',  offset=0x00000204, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',     offset=0x00000208, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add((
         pr.RemoteVariable(name='DigPwrEnable',          description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AnalogPwrManual',       description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=1,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='FPGAPwrManualDig',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=2,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='NegPwrEnable',          description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=3,  base=pr.Bool, mode='RW')))
#      self.add((
#         pr.RemoteVariable(name='AsicPwrEnable',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
#         pr.RemoteVariable(name='AsicPwrManual',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=16, base=pr.Bool, mode='RW'),
#         pr.RemoteVariable(name='AsicPwrManualDig',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=20, base=pr.Bool, mode='RW'),
#         pr.RemoteVariable(name='AsicPwrManualAna',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=21, base=pr.Bool, mode='RW'),
#         pr.RemoteVariable(name='AsicPwrManualIo',    description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=22, base=pr.Bool, mode='RW'),
#         pr.RemoteVariable(name='AsicPwrManualFpga',  description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=23, base=pr.Bool, mode='RW')))
      self.add(pr.RemoteVariable(name='AsicMask',        description='AsicMask',          offset=0x00000210, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='VguardDacSetting',description='VguardDacSetting',  offset=0x00000214, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='VBias1DacSetting',description='VBias1DacSetting',  offset=0x00000218, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='VBias2DacSetting',description='VBias2DacSetting',  offset=0x0000021C, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='VBias3DacSetting',description='VBias3DacSetting',  offset=0x00000220, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='VocmDacSetting',  description='VocsDacSetting',    offset=0x00000224, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='HRDebugSel1',     description='HRDebugSel1',       offset=0x00000228, bitSize=5,  bitOffset=0, base='enum',  mode='RW', enum=debugChEnum))
      self.add(pr.RemoteVariable(name='HRDebugSel2',     description='HRDebugSel2',       offset=0x0000022C, bitSize=5,  bitOffset=0, base='enum',  mode='RW', enum=debugChEnum))
      self.add(pr.RemoteVariable(name='AdcClkHalfT',     description='AdcClkHalfT',       offset=0x00000300, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add((
         pr.RemoteVariable(name='StartupReq',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='StartupAck',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=1, base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='StartupFail', description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=2, base=pr.Bool, mode='RO')))
     
      
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

################################################################################################
##
## epix100a Classes definition
##
################################################################################################
class Epix100a(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "EPIX100A FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicPpmat', 7:'AsicPpbe', 8:'AsicSync', 9:'AsicGr', 10: 'AsicRoClk'}
      #TODO: assign meaningful channel names
      inChaEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      inChbEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      #In order to easely compare GedDAQ address map with the eprix rogue address map 
      #it is defined the addrSize RemoteVariable
      addrSize = 4	
      
      super(self.__class__, self).__init__(**kwargs)
      
      self.add(axi.AxiVersion             (name="AxiVersion",           offset=0x00000000, expand=False))
      self.add(EpixFpgaRegisters          (name="EpixFpgaRegisters",    offset=0x01000000))
      self.add(EpixFpgaExtRegisters       (name="EpixFpgaExtRegisters", offset=0x01100000, enabled=False, expand=False))
      self.add(OscilloscopeRegisters      (name='Oscilloscope',         offset=0x01200000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum))
      for i in range(4):
         self.add(epix.Epix100aAsic       (name=('Epix100aAsic[%d]'%i), offset=(0x02000000+i*0x400000), enabled=False, expand=False))
      #self.add(pgp.Pgp2bAxi               (name='Pgp2bAxi',             offset=0x03000000, expand=False, enabled=False))
      self.add(pgp.Pgp3AxiL               (name='Pgp3Axi',              offset=0x03000000, expand=False, enabled=False))
      self.add(SlowAdcRegisters           (name="SlowAdcRegisters",     offset=0x04000000, enabled=False, expand=False))
      for i in range(3):
         if i == 2:
            channels = 4
         else:
            channels = 8
         self.add(ad.Ad9249ReadoutGroup   (name = ('Ad9249RdoutAdc[%d]'%i),   offset=(0x05100000+i*0x100000), channels=channels, enabled=False, expand=False))
      for i in range(3):
         self.add(ad.Ad9249ConfigGroup    (name = ('Ad9249ConfigAdc[%d]'%i),  offset=(0x05400000+i*0x000800), enabled=False, expand=False))
      self.add(AxiMicronN25Q              (name='MicronN25Q',           offset=0x06000000, expand=False, hidden=False))
      self.add(MicroblazeLog              (name='MicroblazeLog',        offset=0x07000000, enabled=False, expand=False))
      
   def writeBlocks(self, force=False, recurse=True, variable=None, checkEach=False):
      """
      Write all of the blocks held by this Device to memory
      """
      if not self.enable.get(): return
      
      # Process local blocks.
      if variable is not None:
         variable._block.startTransaction(rim.Write, check=checkEach)
      else:
         for block in self._blocks:
            if force or block.stale:
                  if block.bulkEn:
                     block.startTransaction(rim.Write, check=checkEach)
      
      # Retire any in-flight transactions before starting next sequence
      self._root.checkBlocks(recurse=True)
      
      self.asicMask = self.EpixFpgaRegisters.AsicMask.get()
      
      # Load all the registers
      self.AxiVersion.writeBlocks            ( force=force, recurse=recurse, variable=variable)   
      self.EpixFpgaRegisters.writeBlocks     ( force=force, recurse=recurse, variable=variable)   
      self.EpixFpgaExtRegisters.writeBlocks  ( force=force, recurse=recurse, variable=variable)   
      self.Oscilloscope.writeBlocks          ( force=force, recurse=recurse, variable=variable)   
      for i in range(4):
         if self.asicMask&(1<<i) != 0:
            self.Epix100aAsic[i].writeBlocks    ( force=force, recurse=recurse, variable=variable)   
         else:
            self.Epix100aAsic[i].enable.set(False)
      
      #self.Pgp2bAxi.writeBlocks              ( force=force, recurse=recurse, variable=variable)   
      self.SlowAdcRegisters.writeBlocks      ( force=force, recurse=recurse, variable=variable)   
      for i in range(3):
         self.Ad9249RdoutAdc[i].writeBlocks     ( force=force, recurse=recurse, variable=variable) 
         self.Ad9249ConfigAdc[i].writeBlocks    ( force=force, recurse=recurse, variable=variable) 
      self.MicronN25Q.writeBlocks            ( force=force, recurse=recurse, variable=variable) 
      self.MicroblazeLog.writeBlocks         ( force=force, recurse=recurse, variable=variable)    


################################################################################################
##
## epixS Classes definition
##
################################################################################################
class EpixS(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "EPIXS FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicPpmat', 7:'AsicPpbe', 8:'AsicSync', 9:'AsicGr', 10: 'AsicRoClk'}
      #TODO: assign meaningful channel names
      inChaEnum={
            0 :'NONE',
            8 :'U1_B0',  1: 'U2_B0',  5: 'U3_B0',  12:'U4_B0', 
            16:'U1_TPS', 17:'U2_TPS', 18:'U3_TPS', 19:'U4_TPS'}
      inChbEnum={
            0 :'NONE',
            8 :'U1_B0',  1: 'U2_B0',  5: 'U3_B0',  12:'U4_B0', 
            16:'U1_TPS', 17:'U2_TPS', 18:'U3_TPS', 19:'U4_TPS'}
      super(self.__class__, self).__init__(**kwargs)
      
      self.add(axi.AxiVersion                (name="AxiVersion",           offset=0x00000000, expand=False))
      self.add(EpixFpgaRegisters             (name="EpixFpgaRegisters",    offset=0x01000000))
      self.add(EpixFpgaExtRegisters          (name="EpixFpgaExtRegisters", offset=0x01100000, enabled=False, expand=False))
      self.add(OscilloscopeRegisters         (name='Oscilloscope',         offset=0x01200000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum))
      for i in range(4):
         self.add(epix.EpixSAsic          (name=('EpixSAsic[%d]'%i), offset=(0x02000000+i*0x400000), enabled=False, expand=False, size=0x3fffff))
      #self.add(pgp.Pgp2bAxi                  (name='Pgp2bAxi',             offset=0x03000000, expand=False, enabled=False))
      self.add(pgp.Pgp3AxiL                  (name='Pgp3Axi',              offset=0x03000000, expand=False, enabled=False))
      self.add(SlowAdcRegisters              (name="SlowAdcRegisters",     offset=0x04000000, enabled=False, expand=False))
      for i in range(3):
         if i == 2:
            channels = 4
         else:
            channels = 8
         self.add(ad.Ad9249ReadoutGroup      (name = ('Ad9249RdoutAdc[%d]'%i),   offset=(0x05100000+i*0x100000), channels=channels, enabled=False, expand=False))
      for i in range(3):
         self.add(ad.Ad9249ConfigGroup       (name = ('Ad9249ConfigAdc[%d]'%i),  offset=(0x05400000+i*0x000800), enabled=False, expand=False))
      self.add(AxiMicronN25Q                 (name='MicronN25Q',           offset=0x06000000, expand=False, hidden=False))
      self.add(MicroblazeLog                 (name='MicroblazeLog',        offset=0x07000000, enabled=False, expand=False))
            
            
   def writeBlocks(self, force=False, recurse=True, variable=None, checkEach=False):
      """
      Write all of the blocks held by this Device to memory
      """
      if not self.enable.get(): return
      
      # Process local blocks.
      if variable is not None:
         variable._block.startTransaction(rim.Write, check=checkEach)
      else:
         for block in self._blocks:
            if force or block.stale:
                  if block.bulkEn:
                     block.startTransaction(rim.Write, check=checkEach)
      
      # Retire any in-flight transactions before starting next sequence
      self._root.checkBlocks(recurse=True)
      
      self.asicMask = self.EpixFpgaRegisters.AsicMask.get()
      
      # Load all the registers
      self.AxiVersion.writeBlocks            ( force=force, recurse=recurse, variable=variable)   
      self.EpixFpgaRegisters.writeBlocks     ( force=force, recurse=recurse, variable=variable)   
      self.EpixFpgaExtRegisters.writeBlocks  ( force=force, recurse=recurse, variable=variable)   
      self.Oscilloscope.writeBlocks          ( force=force, recurse=recurse, variable=variable)   
      for i in range(4):
         if self.asicMask&(1<<i) != 0:
            self.EpixSAsic[i].writeBlocks    ( force=force, recurse=recurse, variable=variable)   
         else:
            self.EpixSAsic[i].enable.set(False)
      
      #self.Pgp2bAxi.writeBlocks              ( force=force, recurse=recurse, variable=variable)   
      self.SlowAdcRegisters.writeBlocks      ( force=force, recurse=recurse, variable=variable)   
      for i in range(3):
         self.Ad9249RdoutAdc[i].writeBlocks     ( force=force, recurse=recurse, variable=variable) 
         self.Ad9249ConfigAdc[i].writeBlocks    ( force=force, recurse=recurse, variable=variable) 
      self.MicronN25Q.writeBlocks            ( force=force, recurse=recurse, variable=variable) 
      self.MicroblazeLog.writeBlocks         ( force=force, recurse=recurse, variable=variable) 



################################################################################################
##
## epix10ka Classes definition
##
################################################################################################
class Epix10ka(pr.Device):
   def __init__(self, asic_rev=1, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "EPIX10KA FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicPpmat', 7:'AsicPpbe', 8:'AsicSync', 9:'AsicGr', 10: 'AsicRoClk'}
      #TODO: assign meaningful channel names
      inChaEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      inChbEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      super(self.__class__, self).__init__(**kwargs)
      
      self.add(axi.AxiVersion                (name="AxiVersion",           offset=0x00000000, expand=False))
      self.add(EpixFpgaRegisters             (name="EpixFpgaRegisters",    offset=0x01000000))
      self.add(EpixFpgaExtRegisters          (name="EpixFpgaExtRegisters", offset=0x01100000, enabled=False, expand=False))
      self.add(OscilloscopeRegisters         (name='Oscilloscope',         offset=0x01200000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum))
      self.add(Epix10kADouts                 (name="Epix10kADouts",        offset=0x01300000, expand=False))
      for i in range(4):
         if asic_rev == 1:
            self.add(epix.Epix10kaAsic          (name=('Epix10kaAsic[%d]'%i), offset=(0x02000000+i*0x400000), enabled=False, expand=False, size=0x0fffff))
         else:
            self.add(epix.Epix10kaAsicRev2      (name=('Epix10kaAsic[%d]'%i), offset=(0x02000000+i*0x400000), enabled=False, expand=False, size=0x0fffff))
      #self.add(pgp.Pgp2bAxi                  (name='Pgp2bAxi',             offset=0x03000000, expand=False, enabled=False))
      self.add(pgp.Pgp3AxiL                  (name='Pgp3Axi',              offset=0x03000000, expand=False, enabled=False))
      self.add(SlowAdcRegisters              (name="SlowAdcRegisters",     offset=0x04000000, enabled=False, expand=False))
      for i in range(3):
         if i == 2:
            channels = 4
         else:
            channels = 8
         self.add(ad.Ad9249ReadoutGroup      (name = ('Ad9249RdoutAdc[%d]'%i),   offset=(0x05100000+i*0x100000), channels=channels, enabled=False, expand=False))
      for i in range(3):
         self.add(ad.Ad9249ConfigGroup       (name = ('Ad9249ConfigAdc[%d]'%i),  offset=(0x05400000+i*0x000800), enabled=False, expand=False))
      self.add(AxiMicronN25Q                 (name='MicronN25Q',           offset=0x06000000, expand=False, hidden=False))
      self.add(MicroblazeLog                 (name='MicroblazeLog',        offset=0x07000000, enabled=False, expand=False))
            
            
   def writeBlocks(self, force=False, recurse=True, variable=None, checkEach=False):
      """
      Write all of the blocks held by this Device to memory
      """
      if not self.enable.get(): return
      
      # Process local blocks.
      if variable is not None:
         variable._block.startTransaction(rim.Write, check=checkEach)
      else:
         for block in self._blocks:
            if force or block.stale:
                  if block.bulkEn:
                     block.startTransaction(rim.Write, check=checkEach)
      
      # Retire any in-flight transactions before starting next sequence
      self._root.checkBlocks(recurse=True)
      
      self.asicMask = self.EpixFpgaRegisters.AsicMask.get()
      
      # Load all the registers
      self.AxiVersion.writeBlocks            ( force=force, recurse=recurse, variable=variable)   
      self.EpixFpgaRegisters.writeBlocks     ( force=force, recurse=recurse, variable=variable)   
      self.EpixFpgaExtRegisters.writeBlocks  ( force=force, recurse=recurse, variable=variable)   
      self.Oscilloscope.writeBlocks          ( force=force, recurse=recurse, variable=variable)   
      self.Epix10kADouts.writeBlocks         ( force=force, recurse=recurse, variable=variable)   
      for i in range(4):
         if self.asicMask&(1<<i) != 0:
            self.Epix10kaAsic[i].writeBlocks    ( force=force, recurse=recurse, variable=variable)   
         else:
            self.Epix10kaAsic[i].enable.set(False)
      
      #self.Pgp2bAxi.writeBlocks              ( force=force, recurse=recurse, variable=variable)   
      self.SlowAdcRegisters.writeBlocks      ( force=force, recurse=recurse, variable=variable)   
      for i in range(3):
         self.Ad9249RdoutAdc[i].writeBlocks     ( force=force, recurse=recurse, variable=variable) 
         self.Ad9249ConfigAdc[i].writeBlocks    ( force=force, recurse=recurse, variable=variable) 
      self.MicronN25Q.writeBlocks            ( force=force, recurse=recurse, variable=variable) 
      self.MicroblazeLog.writeBlocks         ( force=force, recurse=recurse, variable=variable) 

class EpixFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Epix"""
      super().__init__(description='Epix Configuration Registers', **kwargs)
      
      def getFreqMHz(var):
         x = var.dependencies[0].value()
         return x / 1000000.0
         
      def getPerUs(var):
         x = var.dependencies[0].value()
         baseClk = self.BaseClock.get()
         if baseClk > 0:
            return x / (baseClk/1000000.0)
         else:
            return 0
               
      def setPerUs(deps):
         def setUsValue(var, value, write):
            rawVal = int(round(value*(self.BaseClock.get()/1000000.0)))
            deps[0].set(rawVal,write)            
         return setUsValue
      
      def getPerMs(var):
         x = var.dependencies[0].value()
         baseClk = self.BaseClock.get()
         if baseClk > 0:
            return x / (baseClk/1000.0)
         else:
            return 0
               
      def setPerMs(deps):
         def setMsValue(var, value, write):
            rawVal = int(round(value*(self.BaseClock.get()/1000.0)))
            deps[0].set(rawVal,write)            
         return setMsValue
      
      #In order to easely compare GedDAQ address map with the eprix rogue address map 
      #it is defined the addrSize RemoteVariable
      addrSize = 4	
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      self.add(pr.RemoteVariable(name='Version',             description='FPGA firmware version number',                            offset=0x00000000*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='RunTriggerEnable',    description='Enable external run trigger',                             offset=0x00000001*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='RunTriggerDelay',     description='Run trigger delay',                                       offset=0x00000002*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='RunTriggerDelayUs',   dependencies=[self.RunTriggerDelay], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.RunTriggerDelay]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='DaqTriggerEnable',    description='Enable external run trigger',                             offset=0x00000003*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='DaqTriggerDelay',     description='Run trigger delay',                                       offset=0x00000004*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='DaqTriggerDelayUs',   dependencies=[self.DaqTriggerDelay], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.DaqTriggerDelay]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AcqCount',            description='Acquisition counter',                                     offset=0x00000005*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='AcqCountReset',       description='Reset acquisition counter',                               offset=0x00000006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='DacData',             description='Sets analog DAC (MAX5443)',                               offset=0x00000007*addrSize, bitSize=16, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='DigitalPowerEnable',  description='Digital power enable',                                    offset=0x00000008*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AnalogPowerEnable',   description='Analog power enable',                                     offset=0x00000008*addrSize, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='FpgaOutputEnable',    description='Fpga output enable',                                      offset=0x00000008*addrSize, bitSize=1,  bitOffset=2, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='IDelayCtrlRdy',       description='Ready flag for IDELAYCTRL block',                         offset=0x0000000A*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='SeqCount',            description='Sequence (frame) Counter',                                offset=0x0000000B*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='SeqCountReset',       description='Reset (frame) counter',                                   offset=0x0000000C*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicMask',            description='ASIC mask bits for the SACI access',                      offset=0x0000000D*addrSize, bitSize=4,  bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='BaseClock',           description='FPGA base clock frequency',                               offset=0x00000010*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.LinkVariable(  name='BaseClockMHz',        dependencies=[self.BaseClock], mode='RO', units='MHz', linkedGet=getFreqMHz, disp='{:1.6f}')) 
      self.add(pr.RemoteVariable(name='AutoRunEnable',       description='Enable auto run trigger',                                 offset=0x00000011*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AutoRunPeriod',       description='Auto run trigger period',                                 offset=0x00000012*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='AutoRunPeriodMs',     dependencies=[self.AutoRunPeriod], mode='RW', units='ms', linkedGet=getPerMs, linkedSet=setPerMs([self.AutoRunPeriod]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AutoDaqEnable',       description='Enable auto DAQ trigger',                                 offset=0x00000013*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqToAsicR0Delay',    description='Delay between system acq and ASIC reset pulse',           offset=0x00000020*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='AcqToAsicR0DelayUs',  dependencies=[self.AcqToAsicR0Delay], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AcqToAsicR0Delay]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicR0ToAsicAcq',     description='Delay between ASIC reset pulse and int. window',          offset=0x00000021*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='AsicR0ToAsicAcqUs',   dependencies=[self.AsicR0ToAsicAcq], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicR0ToAsicAcq]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicAcqWidth',        description='Width of ASIC acq signal',                                offset=0x00000022*addrSize, bitSize=31, bitOffset=0, base=pr.UInt, mode='RW')) 
      self.add(pr.LinkVariable(  name='AsicAcqWidthUs',      dependencies=[self.AsicAcqWidth], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicAcqWidth]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicAcqLToPPmatL',    description='Delay bet. ASIC acq drop and power pulse drop',           offset=0x00000023*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='AsicAcqLToPPmatLUs',  dependencies=[self.AsicAcqLToPPmatL], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicAcqLToPPmatL]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicRoClkT',          description='Width of readout clock ',                                 offset=0x00000024*addrSize, bitSize=16, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='AdcClkHalfT',         description='Width (in 8ns) of half clock period of ADC',              offset=0x00000026*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='TotalPixelsToRead',   description='Total numbers of pixels to be readout',                   offset=0x00000027*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='AsicGR',              description='ASIC Global Reset',                                       offset=0x00000029*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicAcq',             description='ASIC Acq Signal',                                         offset=0x00000029*addrSize, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicRO',              description='ASIC R0 Signal',                                          offset=0x00000029*addrSize, bitSize=1,  bitOffset=2, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPpmat',           description='ASIC Ppmat Signal',                                       offset=0x00000029*addrSize, bitSize=1,  bitOffset=3, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPpbe',            description='ASIC Ppbe Signal',                                        offset=0x00000029*addrSize, bitSize=1,  bitOffset=4, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicRoClk',           description='ASIC RO Clock Signal',                                    offset=0x00000029*addrSize, bitSize=1,  bitOffset=5, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPinGRControl',    description='Manual ASIC Global Reset Enabled',                        offset=0x0000002A*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPinAcqControl',   description='Manual ASIC Acq Enabled',                                 offset=0x0000002A*addrSize, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPinROControl',    description='Manual ASIC R0 Enabled',                                  offset=0x0000002A*addrSize, bitSize=1,  bitOffset=2, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPinPpmatControl', description='Manual ASIC Ppmat Enabled',                               offset=0x0000002A*addrSize, bitSize=1,  bitOffset=3, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPinPpbeControl',  description='Manual ASIC Ppbe Enabled',                                offset=0x0000002A*addrSize, bitSize=1,  bitOffset=4, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicPinROClkControl', description='Manual ASIC RO Clock Enabled',                            offset=0x0000002A*addrSize, bitSize=1,  bitOffset=5, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AdcPatternEnable',    description='Enables test pattern on data out',                        offset=0x0000002A*addrSize, bitSize=1,  bitOffset=8, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AsicR0Width',         description='Width of R0 low pulse',                                   offset=0x0000002B*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='AsicR0WidthUs',       dependencies=[self.AsicR0Width], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicR0Width]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='DigitalCardId0',      description='Digital Card Serial Number (low 32 bits)',                offset=0x00000030*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='DigitalCardId1',      description='Digital Card Serial Number (high 32 bits)',               offset=0x00000031*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='AnalogCardId0',       description='Analog Card Serial Number (low 32 bits)',                 offset=0x00000032*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='AnalogCardId1',       description='Analog Card Serial Number (high 32 bits)',                offset=0x00000033*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='AsicPreAcqTime',      description='Sum of time delays leading to the ASIC ACQ pulse',        offset=0x00000039*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.LinkVariable(  name='AsicPreAcqTimeUs',    dependencies=[self.AsicPreAcqTime], mode='RO', units='us', linkedGet=getPerUs, disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AsicPPmatToReadout',  description='Delay between Ppmat pulse and readout',                   offset=0x0000003A*addrSize, bitSize=31, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.LinkVariable(  name='AsicPPmatToReadoutUs',dependencies=[self.AsicPPmatToReadout], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.AsicPPmatToReadout]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='CarrierCardId0',      description='Carrier Card Serial Number (low 32 bits)',                offset=0x0000003B*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='CarrierCardId1',      description='Carrier Card Serial Number (high 32 bits)',               offset=0x0000003C*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='PgpTrigEn',           description='Set to enable triggering over PGP. Disables the TTL trigger input', offset=0x0000003D*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='RequestStartup',      description='Request startup sequence',                                offset=0x00000080*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StartupDone',         description='Startup sequence done',                                   offset=0x00000080*addrSize, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='StartupFail',         description='Startup sequence failed',                                 offset=0x00000080*addrSize, bitSize=1,  bitOffset=2, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='AdcPipelineDelayA0',  description='Number of samples to delay ADC reads of the ASIC0 chls',  offset=0x00000090*addrSize, bitSize=8,  bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='AdcPipelineDelayA1',  description='Number of samples to delay ADC reads of the ASIC1 chls',  offset=0x00000091*addrSize, bitSize=8,  bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='AdcPipelineDelayA2',  description='Number of samples to delay ADC reads of the ASIC2 chls',  offset=0x00000092*addrSize, bitSize=8,  bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='AdcPipelineDelayA3',  description='Number of samples to delay ADC reads of the ASIC3 chls',  offset=0x00000093*addrSize, bitSize=8,  bitOffset=0, base=pr.UInt,  mode='RW'))
  
      
      #####################################
      # Create commands
      #####################################
  
      self.add(pr.Command(name='masterReset',   description='Master Board Reset', function=pr.Command.postedTouch))
      self.add(pr.Command(name='fpgaReload',    description='Reload FPGA',        function=self.cmdFpgaReload))
      self.add(pr.Command(name='counterReset',  description='Counter Reset',      function='self.counter.post(0)'))
      self.add(pr.Command(name='testCpsw',      description='Test CPSW',          function=collections.OrderedDict({ 'masterResetVar': 1, 'usleep': 100, 'counter': 1 })))
      
      # Overwrite reset calls with local functions
      #self.setResetFunc(self.resetFunc)

   def cmdFpgaReload(dev,cmd,arg):
      """Example command function"""
      dev.Version.post(1)
   
   def resetFunc(dev,rstType):
      """Application specific reset function"""
      if rstType == 'soft':
         print('AxiVersion countReset')
      elif rstType == 'hard':
         dev.masterResetVar.post(1)
      elif rstType == 'count':
         print('AxiVersion countReset')

   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class EpixFpgaExtRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Epix"""
      super().__init__(description='Epix Extended Configuration Registers', **kwargs)
      
      def getFreqMHz(var):
         x = var.dependencies[0].value()
         return x / 1000000.0
      
      def getPerUs(var):
         x = var.dependencies[0].value()
         baseClk = self.BaseClock.get()
         if baseClk > 0:
            return x / (baseClk/1000000.0)
         else:
            return 0
               
      def setPerUs(deps):
         def setUsValue(var, value, write):
            rawVal = int(round(value*(self.BaseClock.get()/1000000.0)))
            deps[0].set(rawVal,write)            
         return setUsValue
      
      
      #In order to easely compare GedDAQ address map with the eprix rogue address map 
      #it is defined the addrSize RemoteVariable
      addrSize = 4	
      
      self.add(pr.RemoteVariable(name='GhostCorrEn',         description='GhostCorrEn',      offset=0x00000000*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='BaseClock',           description='FPGA base clock frequency', offset=0x00000001*addrSize, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.LinkVariable(  name='BaseClockMHz',        dependencies=[self.BaseClock], mode='RO', units='MHz', linkedGet=getFreqMHz, disp='{:1.6f}')) 
      self.add(pr.RemoteVariable(name='OversampleEn',        description='OversampleEn',     offset=0x00000002*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='OversampleSize',      description='OversampleSize',   offset=0x00000003*addrSize, bitSize=3,  bitOffset=0, base=pr.UInt, mode='RW'))
      
      self.add(pr.RemoteVariable(name='DebugOut',            description='DebugOut',         offset=0x00000200*addrSize, bitSize=5,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='InjStartDly',         description='InjStartDly',      offset=0x00000201*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='InjStartDlyUs',       dependencies=[self.InjStartDly], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.InjStartDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='InjStopDly',          description='InjStopDly',       offset=0x00000202*addrSize, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.LinkVariable(  name='InjStopDlyUs',        dependencies=[self.InjStopDly], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.InjStopDly]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='InjSkip',             description='InjSkip',          offset=0x00000203*addrSize, bitSize=8,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='InjSyncEn',           description='InjSyncEn',        offset=0x00000204*addrSize, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      
      self.add(pr.RemoteVariable(name='BankPipelineDly00',   description='BankDly00',        offset=0x00000300*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly01',   description='BankDly01',        offset=0x00000301*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly02',   description='BankDly02',        offset=0x00000302*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly03',   description='BankDly03',        offset=0x00000303*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly04',   description='BankDly04',        offset=0x00000304*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly05',   description='BankDly05',        offset=0x00000305*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly06',   description='BankDly06',        offset=0x00000306*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly07',   description='BankDly07',        offset=0x00000307*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly08',   description='BankDly08',        offset=0x00000308*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly09',   description='BankDly09',        offset=0x00000309*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly10',   description='BankDly10',        offset=0x0000030a*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly11',   description='BankDly11',        offset=0x0000030b*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly12',   description='BankDly12',        offset=0x0000030c*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly13',   description='BankDly13',        offset=0x0000030d*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly14',   description='BankDly14',        offset=0x0000030e*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='BankPipelineDly15',   description='BankDly15',        offset=0x0000030f*addrSize, bitSize=7,  bitOffset=0, base=pr.UInt, mode='RW'))
      
      # Overwrite reset calls with local functions
      #self.setResetFunc(self.resetFunc)

   def cmdFpgaReload(dev,cmd,arg):
      """Example command function"""
      dev.Version.post(1)
   
   def resetFunc(dev,rstType):
      """Application specific reset function"""
      if rstType == 'soft':
         print('AxiVersion countReset')
      elif rstType == 'hard':
         dev.masterResetVar.post(1)
      elif rstType == 'count':
         print('AxiVersion countReset')

   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


################################################################################################
##
## Tixel Class definition
##
################################################################################################
class Tixel(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "Tixel FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
      inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
      inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
      
      super(self.__class__, self).__init__(**kwargs)
      self.add((
            axi.AxiVersion(offset=0x00000000),
            TixelFpgaRegisters(name="TixelFpgaRegisters", offset=0x01000000),
            TriggerRegisters(name="TriggerRegisters", offset=0x02000000, expand=False),
            SlowAdcRegisters(name="SlowAdcRegisters", offset=0x03000000, expand=False),
            epix.TixelAsic(name='TixelAsic0', offset=0x04000000, enabled=False, expand=False),
            epix.TixelAsic(name='TixelAsic1', offset=0x04400000, enabled=False, expand=False),
            AsicDeserRegisters(name='Asic0Deserializer', offset=0x0E000000, expand=False),
            AsicDeserRegisters(name='Asic1Deserializer', offset=0x0F000000, expand=False),
            AsicPktRegisters(name='Asic0PktRegisters', offset=0x10000000, expand=False),
            AsicPktRegisters(name='Asic1PktRegisters', offset=0x11000000, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi', offset=0x06000000, expand=False),
            ad.Ad9249ReadoutGroup(name = 'Ad9249Rdout[1].Adc[0]', offset=0x09000000, channels=4, enabled=False, expand=False),
            #ad.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x0A000000),    # not used in tixel, disabled by microblaze
            #ad.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x0A000800),    # not used in tixel, disabled by microblaze
            ad.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x0A001000, enabled=False, expand=False),
            OscilloscopeRegisters(name='Oscilloscope', offset=0x0C000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            MicroblazeLog(name='MicroblazeLog', offset=0x0B000000, expand=False),
            MMCM7Registers(name='MMCM7Registers', offset=0x0D000000, enabled=False, expand=False)))
      

class TixelFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Tixel"""
      super().__init__(description='Tixel Configuration Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='IdDigitalLow',    description='IdDigitalLow',      offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdDigitalHigh',   description='IdDigitalHigh',     offset=0x00000008, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdAnalogLow',     description='IdAnalogLow',       offset=0x0000000C, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdAnalogHigh',    description='IdAnalogHigh',      offset=0x00000010, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdCarrierLow',    description='IdCarrierLow',      offset=0x00000014, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='IdCarrierHigh',   description='IdCarrierHigh',     offset=0x00000018, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='R0Polarity',      description='R0Polarity',        offset=0x00000100, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='R0Delay',         description='R0Delay',           offset=0x00000104, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='R0Width',         description='R0Width',           offset=0x00000108, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstDelay',    description='GlblRstDelay',      offset=0x00000110, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstWidth',    description='GlblRstWidth',      offset=0x00000114, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqPolarity',     description='AcqPolarity',       offset=0x00000118, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay1',       description='AcqDelay1',         offset=0x0000011C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth1',       description='AcqWidth1',         offset=0x00000120, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay2',       description='AcqDelay2',         offset=0x00000124, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth2',       description='AcqWidth2',         offset=0x00000128, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='TpulsePolarity',  description='TpulsePolarity',    offset=0x0000012C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='TpulseDelay',     description='TpulseDelay',       offset=0x00000130, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='TpulseWidth',     description='TpulseWidth',       offset=0x00000134, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='StartPolarity',   description='StartPolarity',     offset=0x00000138, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StartDelay',      description='StartDelay',        offset=0x0000013C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='StartWidth',      description='StartWidth',        offset=0x00000140, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncPolarity',    description='SyncPolarity',      offset=0x0000015C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncDelay',       description='SyncDelay',         offset=0x00000160, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncWidth',       description='SyncWidth',         offset=0x00000164, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000168, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x0000016C, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x00000170, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      
      self.add(pr.RemoteVariable(name='AcqCnt',          description='AcqCnt',            offset=0x00000200, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='SaciPrepRdoutCnt',description='SaciPrepRdoutCnt',  offset=0x00000204, bitSize=32, bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',     offset=0x00000208, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      #self.add(pr.RemoteVariable(name='AsicPowerEnable', description='AsicPowerEnable',   offset=0x0000020C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add((
         pr.RemoteVariable(name='AsicPwrEnable',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManual',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=16, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualDig',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=20, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualAna',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=21, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualIo',    description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=22, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualFpga',  description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=23, base=pr.Bool, mode='RW')))
      self.add(pr.RemoteVariable(name='AsicMask',        description='AsicMask',          offset=0x00000210, bitSize=32, bitOffset=0, base=pr.UInt,  mode='RO'))
      self.add(pr.RemoteVariable(name='VguardDacSetting',description='VguardDacSetting',  offset=0x00000214, bitSize=16, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='TixelDebugSel1',  description='TixelDebugSel1',    offset=0x00000218, bitSize=5,  bitOffset=0, base=pr.UInt,  mode='RW'))
      self.add(pr.RemoteVariable(name='TixelDebugSel2',  description='TixelDebugSel2',    offset=0x0000021C, bitSize=5,  bitOffset=0, base=pr.UInt,  mode='RW'))
      
      self.add(pr.RemoteVariable(name='AdcClkHalfT',     description='AdcClkHalfT',       offset=0x00000300, bitSize=32, bitOffset=0, base=pr.UInt, mode='RW'))
      self.add((
         pr.RemoteVariable(name='StartupReq',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='StartupAck',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=1, base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='StartupFail', description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=2, base=pr.Bool, mode='RO')))
      
      
      
      
      
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


class TriggerRegisters(pr.Device):
   def __init__(self, BaseClock=0, **kwargs):
      super().__init__(description='Trigger Registers', **kwargs)
      
      self.BaseClock = BaseClock
      
      def getPerUs(var):
         x = var.dependencies[0].value()
         baseClk = self.BaseClock
         if baseClk > 0:
            return x / (baseClk/1000000.0)
         else:
            return 0
               
      def setPerUs(deps):
         def setUsValue(var, value, write):
            rawVal = int(round(value*(self.BaseClock/1000000.0)))
            deps[0].set(rawVal,write)            
         return setUsValue
      
      def getPerMs(var):
         x = var.dependencies[0].value()
         baseClk = self.BaseClock
         if baseClk > 0:
            return x / (baseClk/1000.0)
         else:
            return 0
               
      def setPerMs(deps):
         def setMsValue(var, value, write):
            rawVal = int(round(value*(self.BaseClock/1000.0)))
            deps[0].set(rawVal,write)            
         return setMsValue
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      #Setup registers & RemoteVariables
 
      self.add(pr.RemoteVariable(name='RunTriggerEnable',description='RunTriggerEnable',  offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='RunTriggerDelay', description='RunTriggerDelay',   offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      if self.BaseClock != 0:
         self.add(pr.LinkVariable(  name='RunTriggerDelayUs',   dependencies=[self.RunTriggerDelay], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.RunTriggerDelay]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='DaqTriggerEnable',description='DaqTriggerEnable',  offset=0x00000008, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='DaqTriggerDelay', description='DaqTriggerDelay',   offset=0x0000000C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      if self.BaseClock != 0:
         self.add(pr.LinkVariable(  name='DaqTriggerDelayUs',   dependencies=[self.DaqTriggerDelay], mode='RW', units='us', linkedGet=getPerUs, linkedSet=setPerUs([self.DaqTriggerDelay]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='AutoRunEn',       description='AutoRunEn',         offset=0x00000010, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AutoDaqEn',       description='AutoDaqEn',         offset=0x00000014, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AutoTrigPeriod',  description='AutoTrigPeriod',    offset=0x00000018, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      if self.BaseClock != 0:
         self.add(pr.LinkVariable(  name='AutoTrigPeriodMs',dependencies=[self.AutoTrigPeriod], mode='RW', units='ms', linkedGet=getPerMs, linkedSet=setPerMs([self.AutoTrigPeriod]), disp='{:1.5f}')) 
      self.add(pr.RemoteVariable(name='PgpTrigEn',       description='PgpTrigEn',         offset=0x0000001C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqCountReset',   description='AcqCountReset',     offset=0x00000020, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqCount',        description='AcqCount',          offset=0x00000024, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      #self.add(pr.RemoteVariable(name='RunTrigPrescale', description='RunTrigPrescale',   offset=0x00000030, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      #self.add(pr.RemoteVariable(name='DaqTrigPrescale', description='DaqTrigPrescale',   offset=0x00000034, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      
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
      
class OscilloscopeRegisters(pr.Device):
   def __init__(self, trigChEnum, inChaEnum, inChbEnum, **kwargs):
      super().__init__(description='Virtual Oscilloscope Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='ArmReg',          description='Arm',               offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW', verify=False, pollInterval = 1))
      self.add(pr.RemoteVariable(name='TrigReg',         description='Trig',              offset=0x00000004, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW', verify=False, pollInterval = 1))
      self.add((
         pr.RemoteVariable(name='ScopeEnable',     description='Setting1', offset=0x00000008, bitSize=1,  bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='TriggerEdge',     description='Setting1', offset=0x00000008, bitSize=1,  bitOffset=1,  mode='RW', enum={0:'Falling', 1:'Rising'}),
         pr.RemoteVariable(name='TriggerChannel',  description='Setting1', offset=0x00000008, bitSize=4,  bitOffset=2,  mode='RW', enum=trigChEnum),
         pr.RemoteVariable(name='TriggerMode',     description='Setting1', offset=0x00000008, bitSize=2,  bitOffset=6,  mode='RW', enum={0:'Never', 1:'ArmReg', 2:'AcqStart', 3:'Always'}),
         pr.RemoteVariable(name='TriggerAdcThresh',description='Setting1', offset=0x00000008, bitSize=16, bitOffset=16, base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='TriggerHoldoff',  description='Setting2', offset=0x0000000C, bitSize=13, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='TriggerOffset',   description='Setting2', offset=0x0000000C, bitSize=13, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='TraceLength',     description='Setting3', offset=0x00000010, bitSize=13, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='SkipSamples',     description='Setting3', offset=0x00000010, bitSize=13, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='InputChannelA',   description='Setting4', offset=0x00000014, bitSize=5,  bitOffset=0,  mode='RW', enum=inChaEnum),       
         pr.RemoteVariable(name='InputChannelB',   description='Setting4', offset=0x00000014, bitSize=5,  bitOffset=5,  mode='RW', enum=inChbEnum)))
      self.add(pr.RemoteVariable(name='TriggerDelay',    description='TriggerDelay',      offset=0x00000018, bitSize=13, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      
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


class HighSpeedDacRegisters(pr.Device):
   def __init__(self, HsDacEnum, **kwargs):
      super().__init__(description='HS DAC Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add((
         pr.RemoteVariable(name='enabled',         description='Enable waveform generation',                        offset=0x00000000, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='run',             description='Generates waveform when true',                      offset=0x00000000, bitSize=1,   bitOffset=1,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='externalUpdateEn',description='Generates waveform when true',                      offset=0x00000000, bitSize=1,   bitOffset=2,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='samplingCounter', description='Sampling period (>269, times 1/clock ref. 156MHz)', offset=0x00000004, bitSize=12,  bitOffset=0,   base=pr.UInt, disp = '{:#x}',  mode='RW'),
         pr.RemoteVariable(name='DacValue',        description='Set a fixed value for the DAC',                     offset=0x00000008, bitSize=16,  bitOffset=0,   base=pr.UInt, disp = '{:#x}',  mode='RW'),
         pr.RemoteVariable(name='DacChannel',      description='Select the DAC channel to use',                     offset=0x00000008, bitSize=2,   bitOffset=16,  mode='RW', enum=HsDacEnum)))
      
      
      
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


class SlowAdcRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Monitoring Slow ADC Registers', **kwargs)
      
      def getTemp(var):
         x = np.int32(var.dependencies[0].value())/100.0
         return x 
      
      def getEnv(var):
         x = var.dependencies[0].value()
         return x 
      
      def getHum(var):
         x = var.dependencies[0].value() /100.0
         return x 
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables

      
      self.add(pr.RemoteVariable(name='StreamEn',        description='StreamEn',          offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StreamPeriod',    description='StreamPeriod',      offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RW'))
      
      self.add(pr.RemoteVariable(name='AdcData0',        description='RawAdcData',        offset=0x00000040, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData1',        description='RawAdcData',        offset=0x00000044, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData2',        description='RawAdcData',        offset=0x00000048, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData3',        description='RawAdcData',        offset=0x0000004C, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData4',        description='RawAdcData',        offset=0x00000050, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData5',        description='RawAdcData',        offset=0x00000054, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData6',        description='RawAdcData',        offset=0x00000058, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData7',        description='RawAdcData',        offset=0x0000005C, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData8',        description='RawAdcData',        offset=0x00000060, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      
      self.add(pr.RemoteVariable(name='EnvData0',        description='Temp1',             offset=0x00000080, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData1',        description='Temp2',             offset=0x00000084, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData2',        description='Humidity',          offset=0x00000088, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData3',        description='AsicAnalogCurr',    offset=0x0000008C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData4',        description='AsicDigitalCurr',   offset=0x00000090, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData5',        description='AsicVguardCurr',    offset=0x00000094, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData6',        description='Unused',            offset=0x00000098, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData7',        description='AnalogVin',         offset=0x0000009C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData8',        description='DigitalVin',        offset=0x000000A0, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',     mode='RO'))
      
      self.add(pr.LinkVariable(name='Temp1',             dependencies=[self.EnvData0], mode='RO', units='C', linkedGet=getTemp, disp='{:1.1f}')) 
      self.add(pr.LinkVariable(name='Temp2',             dependencies=[self.EnvData1], mode='RO', units='C', linkedGet=getTemp, disp='{:1.1f}')) 
      self.add(pr.LinkVariable(name='Humidity',          dependencies=[self.EnvData2], mode='RO', units='%', linkedGet=getHum, disp='{:1.2f}')) 
      self.add(pr.LinkVariable(name='AsicAnalogCurr',    dependencies=[self.EnvData3], mode='RO', units='mA', linkedGet=getEnv, disp='{:d}')) 
      self.add(pr.LinkVariable(name='AsicDigitalCurr',   dependencies=[self.EnvData4], mode='RO', units='mA', linkedGet=getEnv, disp='{:d}')) 
      self.add(pr.LinkVariable(name='AnalogVin',         dependencies=[self.EnvData7], mode='RO', units='mV', linkedGet=getEnv, disp='{:d}')) 
      self.add(pr.LinkVariable(name='DigitalVin',        dependencies=[self.EnvData8], mode='RO', units='mV', linkedGet=getEnv, disp='{:d}')) 
      
      
      
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


class MMCM7Registers(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='7 Series MMCM Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add((
         pr.RemoteVariable(name='CLKOUT0PhaseMux',  description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0HighTime',  description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0LowTime',   description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT0Frac',      description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=3, bitOffset=12, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0FracEn',    description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=11, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0Edge',      description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0NoCount',   description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0DelayTime', description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT1PhaseMux',  description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1HighTime',  description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1LowTime',   description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT1Edge',      description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1NoCount',   description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1DelayTime', description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT2PhaseMux',  description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2HighTime',  description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2LowTime',   description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT2Edge',      description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2NoCount',   description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2DelayTime', description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT3PhaseMux',  description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3HighTime',  description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3LowTime',   description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT3Edge',      description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3NoCount',   description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3DelayTime', description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT4PhaseMux',  description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4HighTime',  description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4LowTime',   description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT4Edge',      description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4NoCount',   description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4DelayTime', description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT5PhaseMux',  description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5HighTime',  description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5LowTime',   description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT5Edge',      description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5NoCount',   description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5DelayTime', description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT6PhaseMux',  description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6HighTime',  description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6LowTime',   description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT6Edge',      description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6NoCount',   description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6DelayTime', description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      
      
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

   #def enableChanged(self,value):
   #     if value is True:
   #         self.readBlocks(recurse=True, RemoteVariable=None)
   #         self.checkBlocks(recurse=True, RemoteVariable=None)

############################################################################
## Deserializers HR
############################################################################
class AsicDeserHrRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='7 Series 20 bit Deserializer Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='Delay',        description='Delay',          offset=0x00000000, bitSize=5,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Resync',       description='Resync',         offset=0x00000004, bitSize=1,  bitOffset=0, base=pr.Bool, verify = False, mode='RW'))
      self.add(pr.RemoteVariable(name='Locked',       description='Locked',         offset=0x00000008, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors',   description='LockErrors',     offset=0x0000000C, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SerDesDelay',  description='DelayValue',     offset=0x00000010, bitSize=5,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='DelayEn',      description='EnValueUpdate',  offset=0x00000014, bitSize=1,  bitOffset=0, base=pr.Bool, verify = False, mode='RW'))
      
      for i in range(0, 64):
         self.add(pr.RemoteVariable(name='IserdeseOut'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000100+i*4, bitSize=10, bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed

      self.add(
            pr.LocalCommand(name='TuneSerialDelay',description='Tune serial data delay', function=self.fnEvaluateSerDelay))

   def fnEvaluateSerDelay(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
                self.filename = arg
            else:
                self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
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

   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func

class TSWaveCtrlEpixHR(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='HS DAC Registers', **kwargs)
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add((
         pr.RemoteVariable(name='userReset',     description='Triggers user reset', offset=0x00000000, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='WO'),
         pr.RemoteVariable(name='enWaveforms',   description='Enable waveform',     offset=0x00000004, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='adcClkHalfT',   description='ADC clock period',    offset=0x00000010, bitSize=32,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='SDRstPolarity', description='SD polarity',         offset=0x00000020, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='SDRstDelay',    description='SD delay',            offset=0x00000024, bitSize=32,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='SDRstWidth',    description='SD width',            offset=0x00000028, bitSize=32,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='SHClkPolarity', description='SH polarity',         offset=0x00000030, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='SHClkDelay',    description='SD delay',            offset=0x00000034, bitSize=32,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='SHClkWidth',    description='SD width',            offset=0x00000038, bitSize=32,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW')))     

      
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


############################################################################
## Deserializers (cpix/Tixel)
############################################################################
class AsicDeserRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='7 Series 20 bit Deserializer Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='Delay',        description='Delay',          offset=0x00000000, bitSize=5,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Resync',       description='Resync',         offset=0x00000004, bitSize=1,  bitOffset=0, base=pr.Bool, verify = False, mode='RW'))
      self.add(pr.RemoteVariable(name='Locked',       description='Locked',         offset=0x00000008, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors',   description='LockErrors',     offset=0x0000000C, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SerDesDelay',  description='DelayValue',     offset=0x00000010, bitSize=5,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='DelayEn',      description='EnValueUpdate',  offset=0x00000014, bitSize=1,  bitOffset=0, base=pr.Bool, verify = False, mode='RW'))
      
      for i in range(0, 64):
         self.add(pr.RemoteVariable(name='IserdeseOut'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000100+i*4, bitSize=10, bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed

      self.add(
            pr.LocalCommand(name='TuneSerialDelay',description='Tune serial data delay', function=self.fnEvaluateSerDelay))

   def fnEvaluateSerDelay(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
                self.filename = arg
            else:
                self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
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

   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class AsicPktRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Asic data packet registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='FrameCount',      description='FrameCount',     offset=0x00000000, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameSize',       description='FrameSize',      offset=0x00000004, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMaxSize',    description='FrameMaxSize',   offset=0x00000008, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMinSize',    description='FrameMinSize',   offset=0x0000000C, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SofErrors',       description='SofErrors',      offset=0x00000010, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EofErrors',       description='EofErrors',      offset=0x00000014, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='OverflowErrors',  description='OverflowErrors', offset=0x00000018, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='TestMode',        description='TestMode',       offset=0x0000001C, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',  offset=0x00000020, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW', verify = False))
      
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


class AsicPktRegistersHr(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Asic data packet registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='FrameCount',      description='FrameCount',     offset=0x00000000, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameSize',       description='FrameSize',      offset=0x00000004, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMaxSize',    description='FrameMaxSize',   offset=0x00000008, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMinSize',    description='FrameMinSize',   offset=0x0000000C, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SofErrors',       description='SofErrors',      offset=0x00000010, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EofErrors',       description='EofErrors',      offset=0x00000014, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='OverflowErrors',  description='OverflowErrors', offset=0x00000018, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='TestMode',        description='TestMode',       offset=0x0000001C, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StopDataTx',      description='Disable data transmission',       offset=0x0000001C, bitSize=1,   bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',  offset=0x00000020, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW', verify = False))
      
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


class AsicTSPktRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Asic data packet registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add(pr.RemoteVariable(name='FrameCount',      description='FrameCount',       offset=0x00000000, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameSize',       description='FrameSize',        offset=0x00000004, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMaxSize',    description='FrameMaxSize',     offset=0x00000008, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMinSize',    description='FrameMinSize',     offset=0x0000000C, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SofErrors',       description='SofErrors',        offset=0x00000010, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EofErrors',       description='EofErrors',        offset=0x00000014, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='OverflowErrors',  description='OverflowErrors',   offset=0x00000018, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='TestMode',        description='TestMode',         offset=0x0000001C, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',    offset=0x00000020, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW', verify = False))
      self.add(pr.RemoteVariable(name='NumPixels',       description='Number of Pixels', offset=0x00000024, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='TSMode',          description='Matches TS ASIC mode', offset=0x00000028, bitSize=2,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))

      
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

class MicroblazeLog(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Microblaze log buffer', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      
      self.add((
         pr.RemoteVariable(name='MemPointer',   description='MemInfo', offset=0x00000000, bitSize=16,  bitOffset=0,  base=pr.UInt, disp = '{:#x}', mode='RO'),
         pr.RemoteVariable(name='MemLength',    description='MemInfo', offset=0x00000000, bitSize=16,  bitOffset=16, base=pr.UInt, disp = '{:#x}', mode='RO')))
      
      self.add(pr.RemoteVariable(name='MemLow',    description='MemLow',   offset=0x01*4,    bitSize=2048*8, bitOffset=0, base=pr.String, mode='RO'))
      self.add(pr.RemoteVariable(name='MemHigh',   description='MemHigh',  offset=0x201*4,   bitSize=2044*8, bitOffset=0, base=pr.String, mode='RO'))
      
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

class Epix10kADouts(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Epix10kADoutDeserializer', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / RemoteVariable combinations
      #############################################
      
      
      #Setup registers & RemoteVariables
      self.add(pr.RemoteVariable(name='RdoutClkDelay',   description='RdoutClkDelay',   offset=0x00000000,   bitSize=8,    bitOffset=0,   base=pr.UInt,   mode='RW'))
      self.add(pr.RemoteVariable(name='SystemClkDelay',  description='SystemClkDelay',  offset=0x00000004,   bitSize=8,    bitOffset=0,   base=pr.UInt,   mode='RW'))
      self.add(pr.RemoteVariable(name='RdoutOrder',      description='RdoutOrder',      offset=0x00000008,   bitSize=16,   bitOffset=0,   base=pr.UInt,    mode='RW'))
      
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


class WaveformMemoryDevice(pr.MemoryDevice):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "Waveform memory device"    
     
        super(self.__class__, self).__init__(**kwargs)

        self.add(pr.Command(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.Command(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))


    def fnSetWaveform(self, dev,cmd,arg):
        """SetTestBitmap command function"""
        self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            waveform = np.genfromtxt(self.filename, delimiter=',', dtype='uint16')
            if waveform.shape == (1024,):
                for x in range (0, 1024):
                    self._rawWrite(offset = (x * 4),data =  int(waveform[x]))
            else:
                print('wrong csv file format')

    def fnGetWaveform(self, dev,cmd,arg):
        """GetTestBitmap command function"""
        self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            readBack = np.zeros((1024),dtype='uint16')
            for x in range (0, 1024):
                readBack[x] = self._rawRead(offset = (x * 4))
            np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
