##############################################################################
## This file is part of 'EPIX Development Firmware'.
## It is subject to the license terms in the LICENSE.txt file found in the 
## top-level directory of this distribution and at: 
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
## No part of 'EPIX Development Firmware', including this file, 
## may be copied, modified, propagated, or distributed except according to 
## the terms contained in the LICENSE.txt file.
##############################################################################
#######################################
## Timing Constraints                ##
#######################################

create_clock -name gtRefClk0P   -period  6.400 [get_ports gtRefClk0P]
create_clock -name pgpClk       -period  6.400 [get_pins {U_EpixCore/G_PGP2B.U_PgpFrontEnd/G_PGP.U_Pgp2bVarLatWrapper/Pgp2bGtp7VarLat_Inst/MuliLane_Inst/GTP7_CORE_GEN[0].Gtp7Core_Inst/gtpe2_i/TXOUTCLK}]
create_clock -name adc0DoClkP   -period  2.203 [get_ports {adcDoClkP[0]}]
create_clock -name adc1DoClkP   -period  2.203 [get_ports {adcDoClkP[1]}]
create_clock -name adcMonDoClkP -period  2.203 [get_ports {adcDoClkP[2]}]

create_generated_clock -name coreClk      [get_pins {U_EpixCore/U_CoreClockGen0/MmcmGen.U_Mmcm/CLKOUT0}]
create_generated_clock -name delayCtrlClk [get_pins {U_EpixCore/U_CoreClockGen1/MmcmGen.U_Mmcm/CLKOUT0}]
create_generated_clock -name progClk      [get_pins {U_EpixCore/U_Iprog7Series/DIVCLK_GEN.BUFR_ICPAPE2/O}]
create_generated_clock -name adc0BitClkR  [get_pins {U_EpixCore/U_AdcPhyTop/G_AdcReadout[0].U_AdcReadout/U_AdcBitClkR/O}]
create_generated_clock -name adc1BitClkR  [get_pins {U_EpixCore/U_AdcPhyTop/G_AdcReadout[1].U_AdcReadout/U_AdcBitClkR/O}]
create_generated_clock -name adcMonBitClkR [get_pins {U_EpixCore/U_AdcPhyTop/U_MonAdcReadout/U_AdcBitClkR/O}]


set_clock_groups -asynchronous \
   -group [get_clocks -include_generated_clocks pgpClk] \
   -group [get_clocks -include_generated_clocks coreClk] \
   -group [get_clocks -include_generated_clocks delayCtrlClk] \
   -group [get_clocks -include_generated_clocks gtRefClk0P] \
   -group [get_clocks -include_generated_clocks adc0DoClkP] \
   -group [get_clocks -include_generated_clocks adc1DoClkP] \
   -group [get_clocks -include_generated_clocks adcMonDoClkP] \
   -group [get_clocks -include_generated_clocks adc0BitClkR] \
   -group [get_clocks -include_generated_clocks adc1BitClkR] \
   -group [get_clocks -include_generated_clocks adcMonBitClkR] \
   -group [get_clocks -include_generated_clocks progClk]


#######################################
## Pin locations, IO standards, etc. ##
#######################################

# Boot Memory Port Mapping
set_property PACKAGE_PIN T19     [get_ports {bootCsL}]
set_property IOSTANDARD LVCMOS33 [get_ports {bootCsL}] 
set_property PACKAGE_PIN P22     [get_ports {bootMosi}]
set_property IOSTANDARD LVCMOS33 [get_ports {bootMosi}] 
set_property PACKAGE_PIN R22     [get_ports {bootMiso}]
set_property IOSTANDARD LVCMOS33 [get_ports {bootMiso}] 


set_property PACKAGE_PIN Y6  [get_ports {led[0]}]
set_property PACKAGE_PIN AA6 [get_ports {led[1]}]
set_property PACKAGE_PIN L5  [get_ports {led[2]}]
set_property PACKAGE_PIN L4  [get_ports {led[3]}]
set_property IOSTANDARD LVCMOS25 [get_ports {led[*]}]

set_property PACKAGE_PIN T18 [get_ports {powerGood}]
set_property IOSTANDARD LVCMOS33 [get_ports {powerGood}]

set_property PACKAGE_PIN  T16 [get_ports {analogCardDigPwrEn}]
set_property PACKAGE_PIN  U16 [get_ports {analogCardAnaPwrEn}]
set_property IOSTANDARD LVCMOS25 [get_ports {analogCard*PwrEn}]

set_property PACKAGE_PIN F6 [get_ports {gtRefClk0P}]
#set_property PACKAGE_PIN E6 [get_ports {gtRefClk0N}]

set_property PACKAGE_PIN B4 [get_ports {gtDataTxP}]
set_property PACKAGE_PIN A4 [get_ports {gtDataTxN}]
set_property PACKAGE_PIN B8 [get_ports {gtDataRxP}]
set_property PACKAGE_PIN A8 [get_ports {gtDataRxN}]

set_property PACKAGE_PIN R16 [get_ports {sfpDisable}]
set_property IOSTANDARD LVCMOS33 [get_ports {sfpDisable}]

set_property PACKAGE_PIN  R1  [get_ports {dacSclk}]
set_property PACKAGE_PIN  N2  [get_ports {dacDin}]
set_property PACKAGE_PIN AB17 [get_ports {dacCs[0]}]
set_property PACKAGE_PIN AB16 [get_ports {dacCs[1]}]
set_property IOSTANDARD LVCMOS25 [get_ports {dac*}] 

set_property PACKAGE_PIN AB21 [get_ports {runTg}]
set_property PACKAGE_PIN  U20 [get_ports {daqTg}]
set_property PACKAGE_PIN  V20 [get_ports {mps}]
set_property PACKAGE_PIN AB22 [get_ports {tgOut}]
set_property IOSTANDARD LVCMOS33 [get_ports {runTg}]
set_property IOSTANDARD LVCMOS33 [get_ports {daqTg}]
set_property IOSTANDARD LVCMOS33 [get_ports {mps}]
set_property IOSTANDARD LVCMOS33 [get_ports {tgOut}]

set_property PACKAGE_PIN  P14 [get_ports {snIoAdcCard}]
set_property IOSTANDARD LVCMOS33 [get_ports {snIoAdcCard}]
set_property PULLUP true [get_ports {snIoAdcCard}]

set_property PACKAGE_PIN  V18 [get_ports {slowAdcSclk}]
set_property IOSTANDARD LVCMOS33 [get_ports {slowAdcSclk}]
set_property PACKAGE_PIN  V19 [get_ports {slowAdcDin}]
set_property IOSTANDARD LVCMOS33 [get_ports {slowAdcDin}]
set_property PACKAGE_PIN  Y19 [get_ports {slowAdcCsb}]
set_property IOSTANDARD LVCMOS33 [get_ports {slowAdcCsb}]
set_property PACKAGE_PIN  Y18 [get_ports {slowAdcRefClk}]
set_property IOSTANDARD LVCMOS33 [get_ports {slowAdcRefClk}]
set_property PACKAGE_PIN  Y17 [get_ports {slowAdcSync}] 
set_property IOSTANDARD LVCMOS25 [get_ports {slowAdcSync}]
set_property PACKAGE_PIN  Y16 [get_ports {slowAdcDrdy}]
set_property IOSTANDARD LVCMOS25 [get_ports {slowAdcDrdy}]
set_property PACKAGE_PIN  Y9  [get_ports {slowAdcDout}]
set_property IOSTANDARD LVCMOS25 [get_ports {slowAdcDout}]


set_property PACKAGE_PIN  Y12 [get_ports {adcSpiData}]
# set_property PULLUP TRUE [get_ports {adcSpiData}]
set_property PACKAGE_PIN  W16 [get_ports {adcSpiClk}]
# set_property PULLUP TRUE [get_ports {adcSpiClk}]
set_property PACKAGE_PIN  U15 [get_ports {adcSpiCsb[0]}]
set_property PACKAGE_PIN  V15 [get_ports {adcSpiCsb[1]}]
set_property PACKAGE_PIN  W15 [get_ports {adcSpiCsb[2]}]
# vset_property PULLUP TRUE [get_ports {adcSpiCsb[*]}]



set_property PACKAGE_PIN   U7 [get_ports {adcPdwn01}]
set_property PACKAGE_PIN   W9 [get_ports {adcPdwnMon}]
set_property IOSTANDARD LVCMOS25 [get_ports {adcSpi*}]
set_property IOSTANDARD LVCMOS25 [get_ports {adcPdwn*}]


set_property PACKAGE_PIN T1 [get_ports {bufEn}]
set_property IOSTANDARD LVCMOS25 [get_ports {bufEn}]

set_property PACKAGE_PIN AB8 [get_ports {asicGR}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicGR}]
set_property PACKAGE_PIN AB6 [get_ports {asicCk}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicCk}]
set_property PACKAGE_PIN AA8 [get_ports {asicRst}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicRst}]
set_property PACKAGE_PIN AA13 [get_ports {asicCdsBline}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicCdsBline}]
set_property PACKAGE_PIN U6 [get_ports {asicRstComp}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicRstComp}]
set_property PACKAGE_PIN AA16 [get_ports {asicSampleN}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicSampleN}]
set_property PACKAGE_PIN V5 [get_ports {asicDinjEn}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicDinjEn}]
set_property PACKAGE_PIN AB13 [get_ports {asicCKinjEn}]
set_property IOSTANDARD LVCMOS25 [get_ports {asicCKinjEn}]


set_property PACKAGE_PIN   V9 [get_ports {adcClkP[0]}]
set_property PACKAGE_PIN   V8 [get_ports {adcClkM[0]}]
set_property PACKAGE_PIN  T14 [get_ports {adcClkP[1]}]
set_property PACKAGE_PIN  T15 [get_ports {adcClkM[1]}]   
set_property IOSTANDARD LVDS_25 [get_ports {adcClkP[*]}]

set_property PACKAGE_PIN   R4 [get_ports {adcDoClkP[0]}]
set_property PACKAGE_PIN   T4 [get_ports {adcDoClkM[0]}]
set_property PACKAGE_PIN   K4 [get_ports {adcDoClkP[1]}]
set_property PACKAGE_PIN   J4 [get_ports {adcDoClkM[1]}]
set_property PACKAGE_PIN  V13 [get_ports {adcDoClkP[2]}]   
set_property PACKAGE_PIN  V14 [get_ports {adcDoClkM[2]}] 
set_property IOSTANDARD LVDS_25 [get_ports {adcDoClkP[*]}]
set_property DIFF_TERM true [get_ports {adcDoClkP[*]}]

set_property PACKAGE_PIN   V4 [get_ports {adcFrameClkP[0]}]
set_property PACKAGE_PIN   W4 [get_ports {adcFrameClkM[0]}]
set_property PACKAGE_PIN   H4 [get_ports {adcFrameClkP[1]}]
set_property PACKAGE_PIN   G4 [get_ports {adcFrameClkM[1]}]
set_property PACKAGE_PIN  W11 [get_ports {adcFrameClkP[2]}]
set_property PACKAGE_PIN  W12 [get_ports {adcFrameClkM[2]}]
set_property IOSTANDARD LVDS_25 [get_ports {adcFrameClkP[*]}]
set_property DIFF_TERM true [get_ports {adcFrameClkP[*]}]

set_property PACKAGE_PIN   U2 [get_ports {adcDoP[0]}] 
set_property PACKAGE_PIN   V2 [get_ports {adcDoM[0]}] 
set_property PACKAGE_PIN   W2 [get_ports {adcDoP[1]}] 
set_property PACKAGE_PIN   Y2 [get_ports {adcDoM[1]}] 
set_property PACKAGE_PIN   U3 [get_ports {adcDoP[2]}] 
set_property PACKAGE_PIN   V3 [get_ports {adcDoM[2]}] 
set_property PACKAGE_PIN  AB3 [get_ports {adcDoP[3]}] 
set_property PACKAGE_PIN  AB2 [get_ports {adcDoM[3]}] 
set_property PACKAGE_PIN  AA5 [get_ports {adcDoP[4]}] 
set_property PACKAGE_PIN  AB5 [get_ports {adcDoM[4]}] 
set_property PACKAGE_PIN   W6 [get_ports {adcDoP[5]}] 
set_property PACKAGE_PIN   W5 [get_ports {adcDoM[5]}] 
set_property PACKAGE_PIN   R6 [get_ports {adcDoP[6]}] 
set_property PACKAGE_PIN   T6 [get_ports {adcDoM[6]}] 
set_property PACKAGE_PIN   V7 [get_ports {adcDoP[7]}] 
set_property PACKAGE_PIN   W7 [get_ports {adcDoM[7]}] 
set_property PACKAGE_PIN   C2 [get_ports {adcDoP[8]}] 
set_property PACKAGE_PIN   B2 [get_ports {adcDoM[8]}] 
set_property PACKAGE_PIN   E2 [get_ports {adcDoP[9]}] 
set_property PACKAGE_PIN   D2 [get_ports {adcDoM[9]}] 
set_property PACKAGE_PIN   F3 [get_ports {adcDoP[10]}] 
set_property PACKAGE_PIN   E3 [get_ports {adcDoM[10]}] 
set_property PACKAGE_PIN   H2 [get_ports {adcDoP[11]}] 
set_property PACKAGE_PIN   G2 [get_ports {adcDoM[11]}] 
set_property PACKAGE_PIN   J5 [get_ports {adcDoP[12]}] 
set_property PACKAGE_PIN   H5 [get_ports {adcDoM[12]}] 
set_property PACKAGE_PIN   M1 [get_ports {adcDoP[13]}] 
set_property PACKAGE_PIN   L1 [get_ports {adcDoM[13]}] 
set_property PACKAGE_PIN   K6 [get_ports {adcDoP[14]}] 
set_property PACKAGE_PIN   J6 [get_ports {adcDoM[14]}] 
set_property PACKAGE_PIN   N4 [get_ports {adcDoP[15]}] 
set_property PACKAGE_PIN   N3 [get_ports {adcDoM[15]}] 
set_property PACKAGE_PIN  V10 [get_ports {adcDoP[16]}] 
set_property PACKAGE_PIN  W10 [get_ports {adcDoM[16]}] 
set_property PACKAGE_PIN  AA9 [get_ports {adcDoP[17]}] 
set_property PACKAGE_PIN AB10 [get_ports {adcDoM[17]}] 
set_property PACKAGE_PIN  W14 [get_ports {adcDoP[18]}] 
set_property PACKAGE_PIN  Y14 [get_ports {adcDoM[18]}] 
set_property PACKAGE_PIN AA15 [get_ports {adcDoP[19]}] 
set_property PACKAGE_PIN AB15 [get_ports {adcDoM[19]}] 
set_property IOSTANDARD LVDS_25 [get_ports {adcDoP[*]}]
set_property DIFF_TERM true [get_ports {adcDoP[*]}]



#######################################
## Configuration properties          ##
#######################################
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]

set_property BITSTREAM.CONFIG.CONFIGRATE 33 [current_design]
set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]
set_property BITSTREAM.CONFIG.SPI_32BIT_ADDR Yes [current_design]
set_property BITSTREAM.CONFIG.SPI_FALL_EDGE No [current_design]
set_property BITSTREAM.STARTUP.STARTUPCLK Cclk [current_design]
