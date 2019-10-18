##############################################################################
## This file is part of 'EPIX Development Firmware'.
## It is subject to the license terms in the LICENSE.txt file found in the 
## top-level directory of this distribution and at: 
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
## No part of 'EPIX Development Firmware', including this file, 
## may be copied, modified, propagated, or distributed except according to 
## the terms contained in the LICENSE.txt file.
##############################################################################
## User Debug Script

##############################
# Get variables and procedures
##############################
source -quiet $::env(RUCKUS_DIR)/vivado_env_var.tcl
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

############################
## Open the synthesis design
############################
open_run synth_1

###############################
## Set the name of the ILA core
###############################
set ilaName u_ila_1

##################
## Create the core
##################
CreateDebugCore ${ilaName}

#######################
## Set the record depth
#######################
set_property C_DATA_DEPTH 16384 [get_debug_cores ${ilaName}]

#################################
## Set the clock for the ILA core
#################################
#SetDebugCoreClk ${ilaName} {U_EpixHR/bitClk}
SetDebugCoreClk ${ilaName} {U_EpixHR/coreClk}

#######################
## Set the debug Probes
#######################

#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/dacDin}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/dacSclk}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/dacCsL}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/dacLdacL}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/dacClrL}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/dacData[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/dacCh[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/waveform_addr[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/waveform_dout[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/DAC8812_0/curState[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_HSDAC/DAC8812_0/dacStrobe}
ConfigProbe ${ilaName} {U_EpixHR/iasicTsSync}
ConfigProbe ${ilaName} {U_EpixHR/iasicTsData[*]}
ConfigProbe ${ilaName} {U_EpixHR/acqStart}
ConfigProbe ${ilaName} {U_EpixHR/byteClk}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/dFifoOut[*]}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/dFifoSof}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/dFifoEof}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/dFifoEofe}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/dFifoValid}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/rxDataCs[*]}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/rxValidCs}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[0].U_AXI_Framer/sAxisMaster[*]}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[1].U_AXI_Framer/dFifoSof}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[1].U_AXI_Framer/dFifoEof}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[1].U_AXI_Framer/dFifoEofe}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[1].U_AXI_Framer/dFifoValid}
#ConfigProbe ${ilaName} {U_EpixHR/G_ASIC[1].U_AXI_Framer/rxValidCs}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/DecTSMode_U/s[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/dFifoOut[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/dFifoSof}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/dFifoEof}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/dFifoEofe}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/dFifoValid}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/rxDataCs[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_Framer/rxValidCs}
ConfigProbe ${ilaName} {U_EpixHR/U_AXI_TS_ExtClk/r[*]}
#ConfigProbe ${ilaName} {U_EpixHR/iAdcPdwn[*]}
#ConfigProbe ${ilaName} {U_EpixHR/iAdcSpiCsb[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_MonAdcReadout/axilR[*]}
#ConfigProbe ${ilaName} {U_EpixHR/U_MonAdcReadout/curDelayData[*]}
#ConfigProbe ${ilaName} {U_EpixHR/adcSpiClk}

### Delete the last unused port
#delete_debug_port [get_debug_ports [GetCurrentProbe ${ilaName}]]

##########################
## Write the port map file
##########################
WriteDebugProbes ${ilaName} ${PROJ_DIR}/images/debug_probes.ltx



################################################################
# old debug content
################################################################

## Open the run
#open_run synth_1

### Configure the Core
#set ilaName u_ila_0
##set ilaName1 u_ila_1
#CreateDebugCore ${ilaName}
##CreateDebugCore ${ilaName1}
#
### Increase the record depth
#set_property C_DATA_DEPTH 16384 [get_debug_cores ${ilaName}]
##set_property C_DATA_DEPTH 2048 [get_debug_cores ${ilaName1}]
#
#############################################################################
#############################################################################
#############################################################################
#
### Core debug signals
##SetDebugCoreClk ${ilaName} {U_EpixCore/coreClk}
##SetDebugCoreClk ${ilaName} {U_TixelCore/coreClk}
#SetDebugCoreClk ${ilaName} {U_TixelCore/coreClk}
#
#ConfigProbe ${ilaName} {U_TixelCore/errInhibit}
#ConfigProbe ${ilaName} {U_TixelCore/iAsicSync}
#ConfigProbe ${ilaName} {U_TixelCore/iAsicR0}
#ConfigProbe ${ilaName} {U_TixelCore/iAsicAcq}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/rxDataCs[*]}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/rxValidCs}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/dFifoOut[*]}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/dFifoSof}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/dFifoEof}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/dFifoEofe}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/dFifoValid}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[0].U_AXI_Framer/s[state][*]}
#
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/rxDataCs[*]}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/rxValidCs}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/dFifoOut[*]}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/dFifoSof}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/dFifoEof}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/dFifoEofe}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/dFifoValid}
#ConfigProbe ${ilaName} {U_TixelCore/G_ASIC[1].U_AXI_Framer/s[state][*]}
#
##ConfigProbe ${ilaName} {U_TixelCore/iAsic01DM1}
##ConfigProbe ${ilaName} {U_TixelCore/iAsic01DM2}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicR0}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicStart}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicTpulse}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicAcq}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicGrst}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicSync}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicPpmat}
##ConfigProbe ${ilaName} {U_TixelCore/iAsicPPbe}
#
##ConfigProbe ${ilaName1} {U_TixelCore/dataOut[1][*]}
##ConfigProbe ${ilaName1} {U_TixelCore/dataKOut[1]}
##ConfigProbe ${ilaName1} {U_TixelCore/G_ASIC[1].U_AsicDeser/iserdese_out[*]}
#
#############################################################################
#
### Delete the last unused port
#delete_debug_port [get_debug_ports [GetCurrentProbe ${ilaName}]]
##delete_debug_port [get_debug_ports [GetCurrentProbe ${ilaName1}]]
#
### Write the port map file
###write_debug_probes -force ${PROJ_DIR}/debug/debug_probes.ltx
#
