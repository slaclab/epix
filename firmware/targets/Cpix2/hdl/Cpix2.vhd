-------------------------------------------------------------------------------
-- File       : Cpix2.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: 
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.SaciMasterPkg.all;
use surf.Pgp2bPkg.all;

library unisim;
use unisim.vcomponents.all;

entity Cpix2 is
   generic (
      TPD_G : time := 1 ns;
      FPGA_BASE_CLOCK_G : slv(31 downto 0) := x"00" & x"100000"; 
      BUILD_INFO_G  : BuildInfoType
   );
   port (
      -- Debugging IOs
      led                 : out slv(3 downto 0);
      -- Power good
      powerGood           : in  sl;
      -- Power Control
      analogCardDigPwrEn  : out sl;
      analogCardAnaPwrEn  : out sl;
      analogCardIoPwrEn   : out sl;
      -- GT CLK Pins
      gtRefClk0P          : in  sl;
      gtRefClk0N          : in  sl;
      -- SFP TX/RX
      gtDataTxP           : out sl;
      gtDataTxN           : out sl;
      gtDataRxP           : in  sl;
      gtDataRxN           : in  sl;
      -- SFP control signals
      sfpDisable          : out sl;
      -- Guard ring DAC
      vGuardDacSclk       : out sl;
      vGuardDacDin        : out sl;
      vGuardDacCsb        : out sl;
      vGuardDacClrb       : out sl;
      -- External Signals
      runTg               : in  sl;
      daqTg               : in  sl;
      mps                 : out sl;
      tgOut               : out sl;
      -- Board IDs
      snIoAdcCard         : inout sl;
      snIoCarrier         : inout sl;
      -- Slow ADC
      slowAdcSclk         : out sl;
      slowAdcDin          : out sl;
      slowAdcCsb          : out sl;
      slowAdcRefClk       : out sl;
      slowAdcDout         : in  sl;
      slowAdcDrdy         : in  sl;
      slowAdcSync         : out sl; --unconnected by default
      -- Fast ADC Control
      adcSpiClk           : out sl;
      adcSpiData          : inout sl;
      adcSpiCsb           : out slv(2 downto 0);
      adcPdwn01           : out sl;
      adcPdwnMon          : out sl;
      -- ASIC SACI Interface
      asicSaciCmd         : out sl;
      asicSaciClk         : out sl;
      asicSaciSel         : out slv(1 downto 0);
      asicSaciRsp         : in  sl;
      -- ADC readout signals
      adcClkP             : out slv( 1 downto 0);
      adcClkM             : out slv( 1 downto 0);
      adcDoClkP           : in  slv( 2 downto 0);
      adcDoClkM           : in  slv( 2 downto 0);
      adcFrameClkP        : in  slv( 2 downto 0);
      adcFrameClkM        : in  slv( 2 downto 0);
      adcDoP              : in  slv(19 downto 0);
      adcDoM              : in  slv(19 downto 0);
      -- ASIC Control
      asic01DM1           : in sl;
      asic01DM2           : in sl;
      asicEnA             : out sl;
      asicEnB             : out sl;
      asicVid             : out sl;
      asicPPbe            : out slv(1 downto 0);
      asicPpmat           : out slv(1 downto 0);
      asicR0              : out sl;
      asicSR0             : out sl;
      asicGlblRst         : out sl;
      asicSync            : out sl;
      asicAcq             : out sl;
      asicDoutP           : in  slv(1 downto 0);
      asicDoutM           : in  slv(1 downto 0);
      asicRoClkP          : out slv(1 downto 0);
      asicRoClkM          : out slv(1 downto 0);
      -- Boot Memory Ports
      bootCsL             : out sl;
      bootMosi            : out sl;
      bootMiso            : in  sl
      -- TODO: Add DDR pins
      -- TODO: Add I2C pins for SFP
      -- TODO: Add sync pins for DC/DCs
   );
end Cpix2;

architecture RTL of Cpix2 is

   signal iFpgaOutputEn : sl;
   signal iFpgaOutputEnL : sl;
   
   -- Internal versions of signals so that we don't
   -- drive anything unpowered until the components
   -- are online.
   signal iVGuardDacClrb : sl;
   signal iVGuardDacSclk : sl;
   signal iVGuardDacDin  : sl;
   signal iVGuardDacCsb  : sl;
   
   signal iRunTg : sl;
   signal iDaqTg : sl;
   signal iMps   : sl;
   signal iTgOut : sl;
   
   signal iSerialIdIo : slv(1 downto 0);
   
   signal iSaciClk  : sl;
   signal iSaciSelL : slv(1 downto 0);
   signal iSaciCmd  : sl;
   signal iSaciRsp  : sl;
   
   signal iAdcPdwn       : slv(2 downto 0);
   signal iAdcSpiCsb     : slv(2 downto 0);
   signal iAdcSpiClk     : sl;   
   signal iAdcClkP       : slv( 2 downto 0);
   signal iAdcClkM       : slv( 2 downto 0);
   
   signal iBootCsL      : sl;
   signal iBootMosi     : sl;
   
   signal iAsicRoClk    : slv(1 downto 0);
   signal iAsicR0       : sl;
   signal iAsicAcq      : sl;
   signal iAsicPpmat    : slv(1 downto 0);
   signal iAsicPPbe     : slv(1 downto 0);
   signal iAsicGlblRst  : sl;
   signal iAsicSync     : sl;
   signal iAsicEnA      : sl;
   signal iAsicEnB      : sl;
   signal iAsicVid      : sl;
   signal iAsicSR0      : sl;


   
begin

   ---------------------------------------------------------------------------------
   -- Cpix2 Core
   ---------------------------------------------------------------------------------
   U_Cpix2Core : entity work.Cpix2Core
      generic map (
         TPD_G => TPD_G,
         FPGA_BASE_CLOCK_G => FPGA_BASE_CLOCK_G,
         BUILD_INFO_G => BUILD_INFO_G,
         -- Polarity of selected LVDS data lanes is swapped on gen2 ADC board
         ADC1_INVERT_CH    => "10000000",
         ADC2_INVERT_CH    => "00000010"
      )
      port map (
         -- Debugging IOs
         led                 => led,
         -- Power enables
         digitalPowerEn      => analogCardDigPwrEn,
         analogPowerEn       => analogCardAnaPwrEn,
         ioPowerEn           => analogCardIoPwrEn,
         fpgaOutputEn        => iFpgaOutputEn,
         -- Clocks and reset
         powerGood           => powerGood,
         gtRefClk0P          => gtRefClk0P,
         gtRefClk0N          => gtRefClk0N,
         -- SFP interfaces
         sfpDisable          => sfpDisable,
         -- SFP TX/RX
         gtDataRxP           => gtDataRxP,
         gtDataRxN           => gtDataRxN,
         gtDataTxP           => gtDataTxP,
         gtDataTxN           => gtDataTxN,
         -- Guard ring DAC
         vGuardDacSclk       => iVGuardDacSclk,
         vGuardDacDin        => iVGuardDacDin,
         vGuardDacCsb        => iVGuardDacCsb,
         vGuardDacClrb       => iVGuardDacClrb,
         -- External Signals
         runTrigger          => iRunTg,
         daqTrigger          => iDaqTg,
         mpsOut              => iMps,
         triggerOut          => iTgOut,
         -- Board IDs
         serialIdIo(1)       => snIoCarrier,
         serialIdIo(0)       => snIoAdcCard,
         -- Slow ADC
         slowAdcRefClk       => slowAdcRefClk,
         slowAdcSclk         => slowAdcSclk,
         slowAdcDin          => slowAdcDin,
         slowAdcCsb          => slowAdcCsb,
         slowAdcDout         => slowAdcDout,
         slowAdcDrdy         => slowAdcDrdy,
         -- SACI
         saciClk             => iSaciClk,
         saciSelL            => iSaciSelL,
         saciCmd             => iSaciCmd,
         saciRsp             => iSaciRsp,
         -- Fast ADC Control
         adcSpiClk           => iAdcSpiClk,
         adcSpiData          => adcSpiData,
         adcSpiCsb           => iAdcSpiCsb,
         adcPdwn             => iAdcPdwn,
         -- Fast ADC readout
         adcClkP             => iAdcClkP,
         adcClkN             => iAdcClkM,
         adcFClkP            => adcFrameClkP,
         adcFClkN            => adcFrameClkM,
         adcDClkP            => adcDoClkP,
         adcDClkN            => adcDoClkM,
         adcChP              => adcDoP,
         adcChN              => adcDoM,
         -- ASIC Control
         asic01DM1           => asic01DM1,
         asic01DM2           => asic01DM2,
         asicEnA             => iAsicEnA,
         asicEnB             => iAsicEnB,
         asicVid             => iAsicVid,
         asicPPbe            => iAsicPPbe,
         asicPpmat           => iAsicPpmat,
         asicR0              => iAsicR0,
         asicSR0             => iAsicSR0,
         asicGlblRst         => iAsicGlblRst,
         asicSync            => iAsicSync,
         asicAcq             => iAsicAcq,
         asicDoutP           => asicDoutP,
         asicDoutM           => asicDoutM,
         asicRoClk           => iAsicRoClk,
         -- Boot Memory Ports
         bootCsL             => iBootCsL,
         bootMosi            => iBootMosi,
         bootMiso            => bootMiso
      );
      
      adcClkP(1) <= iAdcClkP(2);
      adcClkM(1) <= iAdcClkM(2);

   ----------------------------
   -- Map ports/signals/etc. --
   ----------------------------
   
   -- Boot Memory Ports
   bootCsL  <= iBootCsL    when iFpgaOutputEn = '1' else 'Z';
   bootMosi <= iBootMosi   when iFpgaOutputEn = '1' else 'Z';
   
   -- Guard ring DAC
   vGuardDacSclk <= iVGuardDacSclk when iFpgaOutputEn = '1' else 'Z';
   vGuardDacDin  <= iVGuardDacDin  when iFpgaOutputEn = '1' else 'Z';
   vGuardDacCsb  <= iVGuardDacCsb  when iFpgaOutputEn = '1' else 'Z';
   vGuardDacClrb <= ivGuardDacClrb when iFpgaOutputEn = '1' else 'Z';
   
   -- TTL interfaces (accounting for inverters on ADC card)
   mps    <= not(iMps)   when iFpgaOutputEn = '1' else 'Z';
   tgOut  <= not(iTgOut) when iFpgaOutputEn = '1' else 'Z';
   iRunTg <= not(runTg);
   iDaqTg <= not(daqTg);

   -- ASIC SACI interfaces
   asicSaciCmd    <= iSaciCmd when iFpgaOutputEn = '1' else 'Z';
   asicSaciClk    <= iSaciClk when iFpgaOutputEn = '1' else 'Z';
   G_SACISEL : for i in 0 to 1 generate
      asicSaciSel(i) <= iSaciSelL(i) when iFpgaOutputEn = '1' else 'Z';
   end generate;
   iSaciRsp <= asicSaciRsp;

   -- Fast ADC Configuration
   adcSpiClk     <= iAdcSpiClk when iFpgaOutputEn = '1' else 'Z';
   adcSpiCsb(0)  <= iAdcSpiCsb(0) when iFpgaOutputEn = '1' else 'Z';
   adcSpiCsb(1)  <= iAdcSpiCsb(1) when iFpgaOutputEn = '1' else 'Z';
   adcSpiCsb(2)  <= iAdcSpiCsb(2) when iFpgaOutputEn = '1' else 'Z';
   adcPdwn01     <= iAdcPdwn(0)   when iFpgaOutputEn = '1' else '0';
   adcPdwnMon    <= iAdcPdwn(2)   when iFpgaOutputEn = '1' else '0';
   
   -- ASIC control signals (differential)
   iFpgaOutputEnL <= not(iFpgaOutputEn);
   G_ROCLK : for i in 0 to 1 generate
      U_ASIC_ROCLK_OBUFTDS : OBUFTDS port map ( I => iAsicRoClk(i), T => iFpgaOutputEnL, O => asicRoClkP(i), OB => asicRoClkM(i) );
   end generate;
   -- ASIC control signals (single ended)
   asicR0         <= iAsicR0      when iFpgaOutputEn = '1' else 'Z';
   asicAcq        <= iAsicAcq     when iFpgaOutputEn = '1' else 'Z';
   asicPpmat      <= iAsicPpmat   when iFpgaOutputEn = '1' else "ZZ";
   asicPPbe       <= iAsicPPbe    when iFpgaOutputEn = '1' else "ZZ";
   asicGlblRst    <= iAsicGlblRst when iFpgaOutputEn = '1' else 'Z';
   asicSync       <= iAsicSync    when iFpgaOutputEn = '1' else 'Z';  
   asicEnA        <= iAsicEnA     when iFpgaOutputEn = '1' else 'Z';  
   asicEnB        <= iAsicEnB     when iFpgaOutputEn = '1' else 'Z';  
   asicVid        <= iAsicVid     when iFpgaOutputEn = '1' else 'Z';  
   asicSR0        <= iAsicSR0     when iFpgaOutputEn = '1' else 'Z';  
   
end RTL;
