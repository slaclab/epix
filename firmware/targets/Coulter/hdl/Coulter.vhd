-------------------------------------------------------------------------------
-- Title      : 
-------------------------------------------------------------------------------
-- File       : Coulter.vhd
-- Author     : Maciej Kwiatkowski <mkwiatko@slac.stanford.edu>
-- Company    : SLAC National Accelerator Laboratory
-- Created    : 09/30/2015
-- Last update: 2016-05-25
-- Platform   : Vivado 2014.4
-- Standard   : VHDL'93/02
-------------------------------------------------------------------------------
-- Description: 
-------------------------------------------------------------------------------
-- Copyright (c) 2015 SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.StdRtlPkg.all;

use work.AxiLitePkg.all;
use work.AxiStreamPkg.all;
use work.SsiPkg.all;
use work.SsiCmdMasterPkg.all;
use work.EpixPkgGen2.all;

library unisim;
use unisim.vcomponents.all;

entity Coulter is
   generic (
      TPD_G : time := 1 ns
      );
   port (
      -- Debugging IOs
      led                : out   slv(3 downto 0);
      -- Power good
      powerGood          : in    sl;
      -- Power Control
      analogCardDigPwrEn : out   sl;
      analogCardAnaPwrEn : out   sl;
      -- GT CLK Pins
      gtRefClk0P         : in    sl;
      gtRefClk0N         : in    sl;
      -- SFP TX/RX
      gtDataTxP          : out   sl;
      gtDataTxN          : out   sl;
      gtDataRxP          : in    sl;
      gtDataRxN          : in    sl;
      -- SFP control signals
      sfpDisable         : out   sl;
      -- Guard ring DAC
--       vGuardDacSclk       : out sl;
--       vGuardDacDin        : out sl;
--       vGuardDacCsb        : out sl;
--       vGuardDacClrb       : out sl;
      -- External Signals
      runTg              : in    sl;
      daqTg              : in    sl;
      mps                : out   sl;
      tgOut              : out   sl;
      -- Board IDs
      snIoAdcCard        : inout sl;
      snIoCarrier        : inout sl;
      -- Slow ADC
      slowAdcSclk        : out   sl;
      slowAdcDin         : out   sl;
      slowAdcCsb         : out   sl;
      slowAdcRefClk      : out   sl;
      slowAdcDout        : in    sl;
      slowAdcDrdy        : in    sl;
      slowAdcSync        : out   sl;    --unconnected by default
      -- Fast ADC Control
      adcSpiClk          : out   sl;
      adcSpiData         : inout sl;
      adcSpiCsb          : out   slv(2 downto 0);
      adcPdwn01          : out   sl;
      adcPdwnMon         : out   sl;
      -- ADC readout signals
      adcClkP            : out   sl;
      adcClkM            : out   sl;
      adcDoClkP          : in    slv(1 downto 0);
      adcDoClkM          : in    slv(1 downto 0);
      adcFrameClkP       : in    slv(1 downto 0);
      adcFrameClkM       : in    slv(1 downto 0);
      adcDoP             : in    slv(15 downto 0);
      adcDoM             : in    slv(15 downto 0);
      adcOverflow        : in    slv(1 downto 0);
      -- ELine100 Config
      elineResetL        : out   sl;

      elineEnaAMon : out slv(1 downto 0);
      elineMck     : out slv(1 downto 0);
      elineSc      : out slv(1 downto 0);
      elineSclk    : out slv(1 downto 0);
      elineRnW     : out slv(1 downto 0);
      elineSdi     : out slv(1 downto 0);
      elineSdo     : in  slv(1 downto 0));
end Coulter;

architecture top_level of Coulter is
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
   signal iSaciRsp  : slv(3 downto 0);

   signal iAdcSpiDataOut : sl;
   signal iAdcSpiDataIn  : sl;
   signal iAdcSpiDataEn  : sl;
   signal iAdcPdwn       : slv(2 downto 0);
   signal iAdcSpiCsb     : slv(2 downto 0);
   signal iAdcSpiClk     : sl;
   signal iAdcClkP       : slv(2 downto 0);
   signal iAdcClkM       : slv(2 downto 0);


begin

   -------------------------------------------------------------------------------------------------
   -- PGP
   -------------------------------------------------------------------------------------------------

   -------------------------------------------------------------------------------------------------
   -- Crossbar
   -------------------------------------------------------------------------------------------------

   -------------------------------------------------------------------------------------------------
   -- Version
   -------------------------------------------------------------------------------------------------

   

   ---------------------------
   -- Core block            --
   ---------------------------
   U_EpixCore : entity work.EpixCoreGen2
      generic map (
         TPD_G          => TPD_G,
         -- Polarity of selected LVDS data lanes is swapped on gen2 ADC board
         ADC1_INVERT_CH => "10000000",
         ADC2_INVERT_CH => "00000010"
         )
      port map (
         -- Debugging IOs
         led            => iLed,
         -- Power enables
         digitalPowerEn => analogCardDigPwrEn,
         analogPowerEn  => analogCardAnaPwrEn,
         fpgaOutputEn   => iFpgaOutputEn,
         ledEn          => iLedEn,
         -- Clocks and reset
         powerGood      => powerGood,
         gtRefClk0P     => gtRefClk0P,
         gtRefClk0N     => gtRefClk0N,
         -- SFP interfaces
         sfpDisable     => sfpDisable,
         -- SFP TX/RX
         gtDataRxP      => gtDataRxP,
         gtDataRxN      => gtDataRxN,
         gtDataTxP      => gtDataTxP,
         gtDataTxN      => gtDataTxN,
         -- Guard ring DAC
         vGuardDacSclk  => iVGuardDacSclk,
         vGuardDacDin   => iVGuardDacDin,
         vGuardDacCsb   => iVGuardDacCsb,
         vGuardDacClrb  => iVGuardDacClrb,
         -- External Signals
         runTrigger     => iRunTg,
         daqTrigger     => iDaqTg,
         mpsOut         => iMps,
         triggerOut     => iTgOut,
         -- Board IDs
         serialIdIo(1)  => snIoCarrier,
         serialIdIo(0)  => snIoAdcCard,
         -- Slow ADC
         slowAdcRefClk  => slowAdcRefClk,
         slowAdcSclk    => slowAdcSclk,
         slowAdcDin     => slowAdcDin,
         slowAdcCsb     => slowAdcCsb,
         slowAdcDout    => slowAdcDout,
         slowAdcDrdy    => slowAdcDrdy,
         -- SACI
         saciClk        => iSaciClk,
         saciSelL       => iSaciSelL,
         saciCmd        => iSaciCmd,
         saciRsp        => iSaciRsp,
         -- Fast ADC Control
         adcSpiClk      => iAdcSpiClk,
         adcSpiDataOut  => iAdcSpiDataOut,
         adcSpiDataIn   => iAdcSpiDataIn,
         adcSpiDataEn   => iAdcSpiDataEn,
         adcSpiCsb      => iAdcSpiCsb,
         adcPdwn        => iAdcPdwn,
         -- Fast ADC readout
         adcClkP        => iAdcClkP,
         adcClkN        => iAdcClkM,
         adcFClkP       => adcFrameClkP,
         adcFClkN       => adcFrameClkM,
         adcDClkP       => adcDoClkP,
         adcDClkN       => adcDoClkM,
         adcChP         => adcDoP,
         adcChN         => adcDoM,
         -- ASIC Control
         asicR0         => iAsicR0,
         asicPpmat      => iAsicPpmat,
         asicPpbe       => open,
         asicGrst       => iAsicGlblRst,
         asicAcq        => iAsicAcq,
         asic0Dm2       => iAsicDm1,
         asic0Dm1       => iAsicDm2,
         asicRoClk      => iAsicRoClk,
         asicSync       => iAsicSync,
         -- ASIC digital data
         asicDout       => iAsicDout
         );

   adcClkP(0) <= iAdcClkP(0);
   adcClkM(0) <= iAdcClkM(0);

   adcClkP(1) <= iAdcClkP(2);
   adcClkM(1) <= iAdcClkM(2);

   ----------------------------
   -- Map ports/signals/etc. --
   ----------------------------
   led <= iLed when iLedEn = '1' else (others => '0');

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
   asicSaciCmd <= iSaciCmd when iFpgaOutputEn = '1' else 'Z';
   asicSaciClk <= iSaciClk when iFpgaOutputEn = '1' else 'Z';
   G_SACISEL : for i in 0 to 3 generate
      asicSaciSel(i) <= iSaciSelL(i) when iFpgaOutputEn = '1' else 'Z';
      iSaciRsp(i)    <= asicSaciRsp;
   end generate;

   -- Fast ADC Configuration
   adcSpiClk     <= iAdcSpiClk     when iFpgaOutputEn = '1'                         else 'Z';
   --adcSpiData    <= '0' when iAdcSpiDataOut = '0' and iAdcSpiDataEn = '1' and iFpgaOutputEn = '1' else 'Z';
   adcSpiData    <= iAdcSpiDataOut when iAdcSpiDataEn = '1' and iFpgaOutputEn = '1' else 'Z';
   iAdcSpiDataIn <= adcSpiData;
   adcSpiCsb(0)  <= iAdcSpiCsb(0)  when iFpgaOutputEn = '1'                         else 'Z';
   adcSpiCsb(1)  <= iAdcSpiCsb(1)  when iFpgaOutputEn = '1'                         else 'Z';
   adcSpiCsb(2)  <= iAdcSpiCsb(2)  when iFpgaOutputEn = '1'                         else 'Z';
   adcPdwn01     <= iAdcPdwn(0)    when iFpgaOutputEn = '1'                         else '0';
   --adcPdwn(1)    <= iAdcPdwn(1) when iFpgaOutputEn = '1' else '0';
   adcPdwnMon    <= iAdcPdwn(2)    when iFpgaOutputEn = '1'                         else '0';

   -- ASIC Connections
   -- Digital bits, unused in this design but used to check pinout
--   G_ASIC_DOUT : for i in 0 to 3 generate
--      U_ASIC_DOUT_IBUFDS : IBUFDS port map (I => asicDoutP(i), IB => asicDoutM(i), O => iAsicDout(i));
--   end generate;
   -- ASIC control signals (differential)
   G_ROCLK : for i in 0 to 3 generate
      U_ASIC_ROCLK_OBUFTDS : OBUFTDS port map (I => iAsicRoClk, T => not(iFpgaOutputEn), O => asicRoClkP(i), OB => asicRoClkM(i));
   end generate;
   -- ASIC control signals (single ended)
   asicR0      <= iAsicR0      when iFpgaOutputEn = '1' else 'Z';
   asicAcq     <= iAsicAcq     when iFpgaOutputEn = '1' else 'Z';
   asicPpmat   <= iAsicPpmat   when iFpgaOutputEn = '1' else 'Z';
   asicGlblRst <= iAsicGlblRst when iFpgaOutputEn = '1' else 'Z';
   asicSync    <= iAsicSync    when iFpgaOutputEn = '1' else 'Z';
   -- On this carrier ASIC digital monitors are shared with SN device
   --iAsicDm1    <= snIoCarrier;
   --iAsicDm2    <= snIoCarrier;

end top_level;
