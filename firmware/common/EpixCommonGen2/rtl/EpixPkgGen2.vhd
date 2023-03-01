-------------------------------------------------------------------------------
-- File       : EpixPkgGen2.vhd
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
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;

package EpixPkgGen2 is
   
   type AsicType is (EPIX100A_C, EPIX10KA_C, EPIX10KP_C, EPIXS_C);
   
   constant NUM_ASICS_C      : natural := 4;
   
   type EpixConfigType is record
      runTriggerEnable   : sl;
      runTriggerDelay    : slv(31 downto 0);
      daqTriggerEnable   : sl;
      daqTriggerDelay    : slv(31 downto 0);
      acqCountReset      : sl;
      vguardDacSetting   : slv(15 downto 0);
      powerEnable        : slv( 7 downto 0);
      seqCountReset      : sl;
      asicMask           : slv(NUM_ASICS_C-1 downto 0);
      autoRunEn          : sl;
      autoTrigPeriod     : slv(31 downto 0);
      autoDaqEn          : sl;
      acqToAsicR0Delay   : slv(31 downto 0);
      asicR0ToAsicAcq    : slv(31 downto 0);
      asicAcqWidth       : slv(31 downto 0);
      asicAcqLToPPmatL   : slv(31 downto 0);
      asicRoClkT         : slv(15 downto 0);
      asicRoClkHalfT     : slv(31 downto 0);
      asicPreAcqTime     : slv(31 downto 0);
      adcClkHalfT        : slv(31 downto 0);
      totalPixelsToRead  : slv(31 downto 0);
      asicPins           : slv( 5 downto 0);
      manualPinControl   : slv( 5 downto 0);
      testPattern        : sl;
      asicR0Width        : slv(31 downto 0);
      pipelineDelayA0    : slv(31 downto 0);
      pipelineDelayA1    : slv(31 downto 0);
      pipelineDelayA2    : slv(31 downto 0);
      pipelineDelayA3    : slv(31 downto 0);
      asicPpmatToReadout : slv(31 downto 0);
      requestStartupCal  : sl;
      startupAck         : sl;
      startupFail        : sl;
      pgpTrigEn          : sl;
   end record;
   type EpixConfigArray is array (natural range <>) of EpixConfigType;
   constant EPIX_CONFIG_INIT_C : EpixConfigType := (
      runTriggerEnable   => '0',
      runTriggerDelay    => (others => '0'),
      daqTriggerEnable   => '0',
      daqTriggerDelay    => (others => '0'),
      acqCountReset      => '0',
      vguardDacSetting   => (others => '0'),
      powerEnable        => (others => '0'),
      seqCountReset      => '0',
      asicMask           => (others => '0'),
      autoRunEn          => '0',
      autoTrigPeriod     => (others => '0'),
      autoDaqEn          => '0',
      acqToAsicR0Delay   => (others => '0'),
      asicR0ToAsicAcq    => (others => '0'),
      asicAcqWidth       => (others => '0'),
      asicAcqLToPPmatL   => (others => '0'),
      asicRoClkT         => x"0014",
      asicRoClkHalfT     => x"00000000",
      asicPreAcqTime     => (others => '0'),
      adcClkHalfT        => x"00000001",
      totalPixelsToRead  => x"000084C0",
      asicPins           => (others => '0'),
      manualPinControl   => (others => '0'),
      testPattern        => '0',
      asicR0Width        => (others => '0'),
      pipelineDelayA0    => (others => '0'),
      pipelineDelayA1    => (others => '0'),
      pipelineDelayA2    => (others => '0'),
      pipelineDelayA3    => (others => '0'),
      asicPpmatToReadout => (others => '0'),
      requestStartupCal  => '0',
      startupAck         => '0',
      startupFail        => '0',
      pgpTrigEn          => '0'
   );
   
   type EpixConfigExtType is record
      dbgReg             : slv(4 downto 0);
      injDelay           : slv(31 downto 0);
      injDlyWidth        : slv(31 downto 0);
      -- injSkip            : slv(7 downto 0);
      injSyncEn          : sl;
      ghostCorr          : sl;
      pipelineDelay      : Slv7Array(15 downto 0);
      oversampleSize     : slv(2 downto 0);
      oversampleEn       : sl;
   end record;
   type EpixConfigExtArray is array (natural range <>) of EpixConfigExtType;
   constant EPIX_CONFIG_EXT_INIT_C : EpixConfigExtType := (
      dbgReg             => (others => '0'),
      injDelay           => x"000037BB",
      injDlyWidth        => x"000032AA",
      -- injSkip            => (others => '0'),
      injSyncEn          => '0',
      ghostCorr          => '1',
      pipelineDelay      => (others => (others => '0')),
      oversampleSize     => (others => '0'),
      oversampleEn       => '0'
   );
   
   type EpixStatusType is record
      acqCount           : slv(31 downto 0);
      iDelayCtrlRdy      : sl;
      seqCount           : slv(31 downto 0);
      startupAck         : sl;
      startupFail        : sl;
   end record;
   type EpixStatusArray is array (natural range <>) of EpixStatusType;
   constant EPIX_STATUS_INIT_C : EpixStatusType := (
      acqCount           => (others => '0'),
      iDelayCtrlRdy      => '0',
      seqCount           => (others => '0'),
      startupAck         => '0',
      startupFail        => '0'
   );

   --Functions to allow use of EPIX100 or 10k
   function saciClkPeriod(version: AsicType) return real;
   function getNumColumns ( version : AsicType ) return integer;
   function getWordsPerSuperRow ( version : AsicType ) return integer;

   -- constant NCOL_C : integer := getNumColumns(FPGA_VERSION_C);
   -- --Number of columns in ePix "super row"
   -- -- (columns / ch) * (channels / asic) * (asics / row) / (adc values / word)
   -- -- constant WORDS_PER_SUPER_ROW_C : integer := NCOL_C * 4 * 2 / 2; 
   -- constant WORDS_PER_SUPER_ROW_C  : integer := getWordsPerSuperRow(FPGA_VERSION_C);
   
   constant EPIX100_COLS_PER_ROW   : integer := 96;
   constant EPIX10K_COLS_PER_ROW   : integer := 48;
   constant EPIX10KA_COLS_PER_ROW  : integer := 48;
   constant EPIXS_COLS_PER_ROW     : integer := 10;
   constant EPIX100A_ROWS_PER_ASIC : integer := 352;
   
   procedure globalToLocalPixel( signal   version    : in AsicType; 
                                 signal   globalRow  : in slv; 
                                 signal   globalCol  : in slv; 
                                 signal   calRowFlag : in sl; 
                                 signal   calBotFlag : in sl;
                                 signal   inputData  : in Slv16Array;
                                 variable localAsic  : inout slv; 
                                 variable localRow   : inout slv; 
                                 variable localCol   : inout slv;
                                 variable localData  : inout Slv16Array);
   procedure globalToLocalPixelEpix100A( signal   version    : in AsicType; 
                                         signal   globalRow  : in slv; 
                                         signal   globalCol  : in slv; 
                                         signal   calRowFlag : in sl; 
                                         signal   calBotFlag : in sl;
                                         signal   inputData  : in Slv16Array;
                                         variable localAsic  : inout slv; 
                                         variable localRow   : inout slv; 
                                         variable localCol   : inout slv;
                                         variable localData  : inout Slv16Array) ;   
   
end EpixPkgGen2;

package body EpixPkgGen2 is
   
   function saciClkPeriod(version: AsicType) return real is
   begin
      if (version = EPIX10KA_C) then
         return 1.00E-6;   -- 1MHz
      else
         return 0.25E-6;   -- 4MHz
      end if;
   end function; 
   
   function getNumColumns (version : AsicType ) return integer is
   begin
      --Epix100a
      if (version = EPIX100A_C) then
         return EPIX100_COLS_PER_ROW;
      --Epix 10kp
      elsif (version = EPIX10KP_C) then
         return EPIX10K_COLS_PER_ROW;
      --Epix 10ka
      elsif (version = EPIX10KA_C) then
         return EPIX10KA_COLS_PER_ROW;
      --Epix S
      elsif (version = EPIXS_C) then
         return EPIXS_COLS_PER_ROW;
      --Other (default to Epix 100)
      else
         return EPIX100_COLS_PER_ROW;
      end if; 
   end function;

   function getWordsPerSuperRow (version : AsicType ) return integer is
      variable NCOL_C   : integer;
   begin
      NCOL_C := getNumColumns(version);
      --EpixS reads only the active ASICs
      if (version = EPIXS_C) then
         return EPIXS_COLS_PER_ROW * 2 / 2;
      --Other
      else
         return NCOL_C * 4 * 2 / 2;
      end if; 
   end function;
   
   procedure globalToLocalPixel (
       signal   version    : in AsicType;
       signal   globalRow  : in slv;
       signal   globalCol  : in slv;
       signal   calRowFlag : in sl;
       signal   calBotFlag : in sl;
       signal   inputData  : in Slv16Array;
       variable localAsic  : inout slv;
       variable localRow   : inout slv;
       variable localCol   : inout slv;
       variable localData  : inout Slv16Array)
   is
   begin 
      assert (version = EPIX100A_C) report "Multi-pixel writes not supported for this ASIC!" severity warning;   
      if version = EPIX100A_C then
         globalToLocalPixelEpix100A(version,globalRow,globalCol,calRowFlag,calBotFlag,inputData,localAsic,localRow,localCol,localData);
      end if;
   end procedure globalToLocalPixel;
   
   procedure globalToLocalPixelEpix100A (
       signal   version    : in AsicType;
       signal   globalRow  : in slv;
       signal   globalCol  : in slv;
       signal   calRowFlag : in sl;
       signal   calBotFlag : in sl;
       signal   inputData  : in Slv16Array;
       variable localAsic  : inout slv;
       variable localRow   : inout slv;
       variable localCol   : inout slv;
       variable localData  : inout Slv16Array)
   is
      variable asicCol  : slv(9 downto 0);
      variable NCOL_C   : integer;
   begin 
      NCOL_C := getNumColumns(version);
      -- Top 2 ASICs
      if (globalRow < EPIX100A_ROWS_PER_ASIC and calRowFlag = '0') or (calRowFlag = '1' and calBotFlag = '0') then
         -- ASIC 2 (upper left)
         if globalCol < NCOL_C * 4 then
            localAsic := "10";
            asicCol   := NCOL_C * 4 - globalCol - 1;
         -- ASIC 1 (upper right)
         else
            localAsic := "01";
            asicCol   := NCOL_C * 4 * 2 - 1 - globalCol;
         end if;
         -- For both top ASICs, translate row to local space
         if calRowFlag = '1' then
            localRow := conv_std_logic_vector(EPIX100A_ROWS_PER_ASIC,localRow'length);
         else
            localRow := EPIX100A_ROWS_PER_ASIC - 1 - globalRow;
         end if;
         -- Readout order for top ASICs is 3->0
         for i in 0 to 3 loop
            localData(3-i) := inputData(i);
         end loop;
      -- Bottom two ASICs
      else
         -- ASIC 3 (lower left)
         if (globalCol < NCOL_C * 4) then
            localAsic := "11";
            asicCol   := globalCol;
         -- ASIC 0 (lower right)
         else
            localAsic := "00";
            asicCol   := globalCol - NCOL_C * 4;
         end if;
         -- For both bottom ASICs, translate row to local space
         if calRowFlag = '1' then
            localRow := conv_std_logic_vector(EPIX100A_ROWS_PER_ASIC,localRow'length);
         else
            localRow := globalRow - EPIX100A_ROWS_PER_ASIC;
         end if;
         -- Readout order for bottom ASICs is 0->3
         for i in 0 to 3 loop
            localData(i) := inputData(i);
         end loop;
      end if;
      -- Decode column to column within a bank   
      if asicCol  < NCOL_C then
         localCol := asicCol;
      elsif asicCol < NCOL_C * 2 then
         localCol := asicCol - NCOL_C;
      elsif asicCol < NCOL_C * 3 then
         localCol := asicCol - NCOL_C * 2;
      else
         localCol := asicCol - NCOL_C * 3;
      end if;
   end procedure globalToLocalPixelEpix100A;     
   
end package body EpixPkgGen2;
