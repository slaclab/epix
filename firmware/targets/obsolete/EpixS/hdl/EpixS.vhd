-------------------------------------------------------------------------------
-- File       : EpixS.vhd
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

use work.EpixPkgGen2.all;

library unisim;
use unisim.vcomponents.all;

entity EpixS is
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
      asicSaciSel         : out slv(3 downto 0);
      asicSaciRsp         : in  slv(3 downto 0);
      -- ADC readout signals
      adcClkP             : out slv( 2 downto 0);
      adcClkM             : out slv( 2 downto 0);
      adcDoClkP           : in  slv( 2 downto 0);
      adcDoClkM           : in  slv( 2 downto 0);
      adcFrameClkP        : in  slv( 2 downto 0);
      adcFrameClkM        : in  slv( 2 downto 0);
      adcDoP              : in  slv(19 downto 0);
      adcDoM              : in  slv(19 downto 0);
      -- ASIC Control
      asicR0              : out sl;
      asicPpmat           : out sl;
      asicPpbe            : out sl;
      asicGlblRst         : out sl;
      asicSync            : out sl;
      asicAcq             : out sl;
--      asicDoutP           : in  slv(3 downto 0);
--      asicDoutM           : in  slv(3 downto 0);
      asicRoClkP          : out slv(3 downto 0);
      asicRoClkM          : out slv(3 downto 0);
      asicDm2             : in  sl;
      -- Boot Memory Ports
      bootCsL             : out sl;
      bootMosi            : out sl;
      bootMiso            : in  sl
      -- TODO: Add DDR pins
      -- TODO: Add I2C pins for SFP
      -- TODO: Add sync pins for DC/DCs
   );
end EpixS;

architecture top_level of EpixS is
   signal iLed          : slv(3 downto 0);
   signal iFpgaOutputEn : sl;
   signal iLedEn        : sl;
   
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
   signal iSaciSelL : slv(3 downto 0);
   signal iSaciCmd  : sl;
   signal iSaciRsp  : sl;
   
   signal iAdcSpiDataOut : sl;
   signal iAdcSpiDataIn   : sl;
   signal iAdcSpiDataEn  : sl;
   signal iAdcPdwn       : slv(2 downto 0);
   signal iAdcSpiCsb     : slv(2 downto 0);
   signal iAdcSpiClk     : sl;   
   
   signal iAsicRoClk    : sl;
   signal iAsicR0       : sl;
   signal iAsicAcq      : sl;
   signal iAsicPpmat    : sl;
   signal iAsicPpbe     : sl;
   signal iAsicGlblRst  : sl;
   signal iAsicSync     : sl;
   signal iAsicDm1      : sl;
   signal iAsicDm2      : sl;
   signal iAsicDout     : slv(3 downto 0);
   
   signal iBootCsL      : sl;
   signal iBootMosi     : sl;
   
   -- Keep douts from getting trimmed even if they're not used in this design
   attribute dont_touch : string;
   attribute dont_touch of iAsicDout : signal is "true";
   attribute dont_touch of iAsicDm1  : signal is "true";
   attribute dont_touch of iAsicDm2  : signal is "true";
   
begin

   ---------------------------
   -- Core block            --
   ---------------------------
   U_EpixCore : entity work.EpixCoreGen2
      generic map (
         TPD_G => TPD_G,
         ASIC_TYPE_G => EPIXS_C,
         FPGA_BASE_CLOCK_G => FPGA_BASE_CLOCK_G,
         BUILD_INFO_G => BUILD_INFO_G
      )
      port map (
         -- Debugging IOs
         led                 => iLed,
         -- Power enables
         digitalPowerEn      => analogCardDigPwrEn,
         analogPowerEn       => analogCardAnaPwrEn,
         fpgaOutputEn        => iFpgaOutputEn,
         ledEn               => iLedEn,
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
         adcSpiDataOut       => iAdcSpiDataOut,
         adcSpiDataIn        => iAdcSpiDataIn,
         adcSpiDataEn        => iAdcSpiDataEn,
         adcSpiCsb           => iAdcSpiCsb,
         adcPdwn             => iAdcPdwn,
         -- Fast ADC readout
         adcClkP             => adcClkP,
         adcClkN             => adcClkM,
         adcFClkP            => adcFrameClkP,
         adcFClkN            => adcFrameClkM,
         adcDClkP            => adcDoClkP,
         adcDClkN            => adcDoClkM,
         adcChP              => adcDoP,
         adcChN              => adcDoM,
         -- ASIC Control
         asicR0              => iAsicR0,
         asicPpmat           => iAsicPpmat,
         asicPpbe            => iAsicPpbe,
         asicGrst            => iAsicGlblRst,
         asicAcq             => iAsicAcq,
         asic0Dm2            => iAsicDm1,
         asic0Dm1            => iAsicDm2,
         asicRoClk           => iAsicRoClk,
         -- asicSync            => iAsicSync,
         -- ASIC digital data
         asicDout            => iAsicDout,
         -- Boot Memory Ports
         bootCsL             => iBootCsL,
         bootMosi            => iBootMosi,
         bootMiso            => bootMiso
      );

   ----------------------------
   -- Map ports/signals/etc. --
   ----------------------------
   led <= iLed when iLedEn = '1' else (others => '0');
   
   -- Boot Memory Ports
   bootCsL  <= iBootCsL    when iFpgaOutputEn = '1' else 'Z';
   bootMosi <= iBootMosi   when iFpgaOutputEn = '1' else 'Z';
   
   -- Guard ring DAC
   vGuardDacSclk <= iVGuardDacSclk when iFpgaOutputEn = '1' else 'Z';
   vGuardDacDin  <= iVGuardDacDin  when iFpgaOutputEn = '1' else 'Z';
   vGuardDacCsb  <= iVGuardDacCsb  when iFpgaOutputEn = '1' else 'Z';
   vGuardDacClrb <= ivGuardDacClrb when iFpgaOutputEn = '1' else 'Z';
   
   -- TTL interfaces (accounting for inverters on ADC card)
   mps   <= not(iMps)   when iFpgaOutputEn = '1' else 'Z';
   tgOut <= not(iTgOut) when iFpgaOutputEn = '1' else 'Z';
   iRunTg <= not(runTg);
   iDaqTg <= not(daqTg);

   -- ASIC SACI interfaces
   asicSaciCmd    <= iSaciCmd when iFpgaOutputEn = '1' else 'Z';
   asicSaciClk    <= iSaciClk when iFpgaOutputEn = '1' else 'Z';
   G_SACISEL : for i in 0 to 3 generate
      asicSaciSel(i) <= iSaciSelL(i) when iFpgaOutputEn = '1' else 'Z';
   end generate;
   iSaciRsp <= 
      asicSaciRsp(0) when iSaciSelL = "1110" else
      asicSaciRsp(1) when iSaciSelL = "1101" else
      asicSaciRsp(2) when iSaciSelL = "1011" else
      asicSaciRsp(3);

   -- Fast ADC Configuration
   adcSpiClk     <= iAdcSpiClk when iFpgaOutputEn = '1' else 'Z';
   --adcSpiData    <= '0' when iAdcSpiDataOut = '0' and iAdcSpiDataEn = '1' and iFpgaOutputEn = '1' else 'Z';
   adcSpiData    <= iAdcSpiDataOut when  iAdcSpiDataEn = '1' and iFpgaOutputEn = '1' else 'Z';
   iAdcSpiDataIn <= adcSpiData;
   adcSpiCsb(0)  <= iAdcSpiCsb(0) when iFpgaOutputEn = '1' else 'Z';
   adcSpiCsb(1)  <= iAdcSpiCsb(1) when iFpgaOutputEn = '1' else 'Z';
   adcSpiCsb(2)  <= iAdcSpiCsb(2) when iFpgaOutputEn = '1' else 'Z';
   adcPdwn01     <= iAdcPdwn(0) when iFpgaOutputEn = '1' else '0';
   --adcPdwn(1)    <= iAdcPdwn(1) when iFpgaOutputEn = '1' else '0';
   adcPdwnMon    <= iAdcPdwn(2) when iFpgaOutputEn = '1' else '0';
   
   
   -- ASIC Connections
   -- Digital bits, unused in this design but used to check pinout
--   G_ASIC_DOUT : for i in 0 to 3 generate
--      U_ASIC_DOUT_IBUFDS : IBUFDS port map (I => asicDoutP(i), IB => asicDoutM(i), O => iAsicDout(i));
--   end generate;
   -- ASIC control signals (differential)
   G_ROCLK : for i in 0 to 3 generate
      U_ASIC_ROCLK_OBUFTDS : OBUFTDS port map ( I => iAsicRoClk, T => not(iFpgaOutputEn), O => asicRoClkP(i), OB => asicRoClkM(i) );
   end generate;
   -- ASIC control signals (single ended)
   asicR0      <= iAsicR0      when iFpgaOutputEn = '1' else 'Z';
   asicAcq     <= iAsicAcq     when iFpgaOutputEn = '1' else 'Z';
   asicPpmat   <= iAsicPpmat   when iFpgaOutputEn = '1' else 'Z';
   asicPpbe    <= iAsicPpbe    when iFpgaOutputEn = '1' else 'Z';
   asicGlblRst <= iAsicGlblRst when iFpgaOutputEn = '1' else 'Z';
   asicSync    <= iAsicSync    when iFpgaOutputEn = '1' else 'Z';
   -- On this carrier ASIC digital monitors are shared with SN device
   --iAsicDm1    <= snIoCarrier;
   iAsicDm2    <= asicDm2;
   
end top_level;
