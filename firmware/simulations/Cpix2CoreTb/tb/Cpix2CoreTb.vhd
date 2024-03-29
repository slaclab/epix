-------------------------------------------------------------------------------
-- File       : Cpix2CoreTb.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Simulation Testbed for EpixQuad top module
-------------------------------------------------------------------------------
-- This file is part of 'EPIX'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;
use ieee.math_real.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiPkg.all;
use surf.Code8b10bPkg.all;

use work.ad9249_pkg.all;
use work.EpixPkgGen2.all;
use work.Cpix2Pkg.all;

library unisim;
use unisim.vcomponents.all;

entity Cpix2CoreTb is end Cpix2CoreTb;

architecture testbed of Cpix2CoreTb is
   
   constant PGPCLK_PER_C      : time    := 6.4 ns;
   constant TPD_C             : time    := 1 ns;
   constant SIM_SPEEDUP_C     : boolean := true;
   
   constant BUILD_INFO_TB_C : BuildInfoRetType := (
      buildString =>  (others => (others => '0')),
      fwVersion => X"EA040000",
      gitHash => (others => '0'));
   
   
   signal adcSpiData : sl;
   signal runTrigger : sl;
   signal daqTrigger : sl;
   signal serialIdIo : slv(1 downto 0)    := "00";
   
   -- ASIC signals
   signal iAsicEnA      : sl;
   signal iAsicEnB      : sl;
   signal iAsicVid      : sl;
   signal iAsicPPbe     : slv(1 downto 0);
   signal iAsicPpmat    : slv(1 downto 0);
   signal iAsicR0       : sl;
   signal iAsicSR0      : sl;
   signal iAsicGlblRst  : sl;
   signal iAsicSync     : sl;
   signal iAsicAcq      : sl;
   signal iAsicRoClk    : slv(1 downto 0);
   
   signal pgpClkP    : sl;
   signal pgpClkN    : sl;
   signal adcClkP    : slv(2 downto 0);
   signal adcClkN    : slv(2 downto 0);
   signal adcFClkP   : slv(2 downto 0);
   signal adcFClkN   : slv(2 downto 0);
   signal adcDClkP   : slv(2 downto 0);
   signal adcDClkN   : slv(2 downto 0);
   signal adcChP     : Slv8Array(2 downto 0);
   signal adcChN     : Slv8Array(2 downto 0);
   
   signal iAdcChP    :  slv(23 downto 0);
   signal iAdcChN    :  slv(23 downto 0);
   
   signal adcDoutClk       : sl;
   
   signal asicDoutP           : slv(1 downto 0);
   signal asicDoutM           : slv(1 downto 0);
   
   signal sroAck     : slv(1 downto 0);
   signal sroReq     : slv(1 downto 0);
   
   constant ADC_BASELINE_C  : RealArray(79 downto 0)    := (
      0 =>0.5+0 *1.0/80, 1 =>0.5+1 *1.0/80, 2 =>0.5+2 *1.0/80, 3 =>0.5+3 *1.0/80, 4 =>0.5+4 *1.0/80, 5 =>0.5+5 *1.0/80, 6 =>0.5+6 *1.0/80, 7 =>0.5+7 *1.0/80,
      8 =>0.5+8 *1.0/80, 9 =>0.5+9 *1.0/80, 10=>0.5+10*1.0/80, 11=>0.5+11*1.0/80, 12=>0.5+12*1.0/80, 13=>0.5+13*1.0/80, 14=>0.5+14*1.0/80, 15=>0.5+15*1.0/80,
      16=>0.5+16*1.0/80, 17=>0.5+17*1.0/80, 18=>0.5+18*1.0/80, 19=>0.5+19*1.0/80, 20=>0.5+20*1.0/80, 21=>0.5+21*1.0/80, 22=>0.5+22*1.0/80, 23=>0.5+23*1.0/80,
      24=>0.5+24*1.0/80, 25=>0.5+25*1.0/80, 26=>0.5+26*1.0/80, 27=>0.5+27*1.0/80, 28=>0.5+28*1.0/80, 29=>0.5+29*1.0/80, 30=>0.5+30*1.0/80, 31=>0.5+31*1.0/80,
      32=>0.5+32*1.0/80, 33=>0.5+33*1.0/80, 34=>0.5+34*1.0/80, 35=>0.5+35*1.0/80, 36=>0.5+36*1.0/80, 37=>0.5+37*1.0/80, 38=>0.5+38*1.0/80, 39=>0.5+39*1.0/80,
      40=>0.5+40*1.0/80, 41=>0.5+41*1.0/80, 42=>0.5+42*1.0/80, 43=>0.5+43*1.0/80, 44=>0.5+44*1.0/80, 45=>0.5+45*1.0/80, 46=>0.5+46*1.0/80, 47=>0.5+47*1.0/80,
      48=>0.5+48*1.0/80, 49=>0.5+49*1.0/80, 50=>0.5+50*1.0/80, 51=>0.5+51*1.0/80, 52=>0.5+52*1.0/80, 53=>0.5+53*1.0/80, 54=>0.5+54*1.0/80, 55=>0.5+55*1.0/80,
      56=>0.5+56*1.0/80, 57=>0.5+57*1.0/80, 58=>0.5+58*1.0/80, 59=>0.5+59*1.0/80, 60=>0.5+60*1.0/80, 61=>0.5+61*1.0/80, 62=>0.5+62*1.0/80, 63=>0.5+63*1.0/80,
      64=>0.5+64*1.0/80, 65=>0.5+65*1.0/80, 66=>0.5+66*1.0/80, 67=>0.5+67*1.0/80, 68=>0.5+68*1.0/80, 69=>0.5+69*1.0/80, 70=>0.5+70*1.0/80, 71=>0.5+71*1.0/80,
      72=>0.5+72*1.0/80, 73=>0.5+73*1.0/80, 74=>0.5+74*1.0/80, 75=>0.5+75*1.0/80, 76=>0.5+76*1.0/80, 77=>0.5+77*1.0/80, 78=>0.5+78*1.0/80, 79=>0.5+79*1.0/80
   );
   
   constant COUNT_MASK_C  : Slv16Array(79 downto 0)    := (
      0 =>x"0000", 1 =>x"0100", 2 =>x"0200", 3 =>x"0300", 4 =>x"0400", 5 =>x"0500", 6 =>x"0600", 7 =>x"0700",
      8 =>x"0800", 9 =>x"0900", 10=>x"0a00", 11=>x"0b00", 12=>x"0c00", 13=>x"0d00", 14=>x"0e00", 15=>x"0f00",
      16=>x"1000", 17=>x"1100", 18=>x"1200", 19=>x"1300", 20=>x"1400", 21=>x"1500", 22=>x"1600", 23=>x"1700",
      24=>x"1800", 25=>x"1900", 26=>x"1a00", 27=>x"1b00", 28=>x"1c00", 29=>x"1d00", 30=>x"1e00", 31=>x"1f00",
      32=>x"2000", 33=>x"2100", 34=>x"2200", 35=>x"2300", 36=>x"2400", 37=>x"2500", 38=>x"2600", 39=>x"2700",
      40=>x"2800", 41=>x"2900", 42=>x"2a00", 43=>x"2b00", 44=>x"2c00", 45=>x"2d00", 46=>x"2e00", 47=>x"2f00",
      48=>x"3000", 49=>x"3100", 50=>x"3200", 51=>x"3300", 52=>x"3400", 53=>x"3500", 54=>x"3600", 55=>x"3700",
      56=>x"3800", 57=>x"3900", 58=>x"3a00", 59=>x"3b00", 60=>x"3c00", 61=>x"3d00", 62=>x"3e00", 63=>x"3f00",
      64=>x"0000", 65=>x"0100", 66=>x"0200", 67=>x"0300", 68=>x"0400", 69=>x"0500", 70=>x"0600", 71=>x"0700",
      72=>x"0800", 73=>x"0900", 74=>x"0a00", 75=>x"0b00", 76=>x"0c00", 77=>x"0d00", 78=>x"0e00", 79=>x"0f00"
   );
   
   procedure tixelSerialData ( 
         signal roClk         : in  std_logic;
         signal sroReq        : in  std_logic;
         signal sroAck        : out std_logic;
         signal dOutP         : out std_logic;
         signal dOutM         : out std_logic
      ) is
      variable t1             : time;
      variable dataClkPeriod  : time;
      constant idleK          : std_logic_vector(7 downto 0) := x"BC";
      constant idleD          : std_logic_vector(7 downto 0) := x"4A";
      constant sofK           : std_logic_vector(7 downto 0) := x"F7";
      constant sofD           : std_logic_vector(7 downto 0) := x"4A";
      constant eofK           : std_logic_vector(7 downto 0) := x"FD";
      constant eofD           : std_logic_vector(7 downto 0) := x"4A";
      variable dataIn         : std_logic_vector(15 downto 0) := x"0000";
      variable dataOut        : std_logic_vector(9 downto 0);
      variable disparity      : std_logic := '0';
      variable dispOut        : std_logic;
   begin
   
      dOutP <= '0';
      dOutM <= '1';
      sroAck <= '0';
      disparity := '0';
      
      -- wait for stable clock
      wait for 10 us;
   
      --wait until rising_edge(roClk);
      t1 := now;
      
      wait until rising_edge(roClk);
      dataClkPeriod := (now - t1)/40;
      
      -- the above does not work due to accumulating error
      -- fixed period
      dataClkPeriod := 2.0 ns;
      
      loop
         
         -- idle pattern
         
         encode8b10b (idleD, '0', disparity, dataOut, dispOut);
         disparity := dispOut;
         for i in 0 to 9 loop
            dOutP <= dataOut(9-i);
            dOutM <= not dataOut(9-i);
            wait for dataClkPeriod;
         end loop;
         
         encode8b10b (idleK, '1', disparity, dataOut, dispOut);
         disparity := dispOut;
         for i in 0 to 9 loop
            dOutP <= dataOut(i);
            dOutM <= not dataOut(i);
            wait for dataClkPeriod;
         end loop;
         
         
         -- data frame if requested
         if sroReq = '1' then
            sroAck <= '1';
            dataIn := x"0000";
            -- SOF
            encode8b10b (sofK, '1', disparity, dataOut, dispOut);
            disparity := dispOut;
            for i in 0 to 9 loop
               dOutP <= dataOut(i);
               dOutM <= not dataOut(i);
               wait for dataClkPeriod;
            end loop;
            encode8b10b (sofD, '0', disparity, dataOut, dispOut);
            disparity := dispOut;
            for i in 0 to 9 loop
               dOutP <= dataOut(i);
               dOutM <= not dataOut(i);
               wait for dataClkPeriod;
            end loop;
            -- DATA LOOP
            for i in 0 to 2303 loop
               encode8b10b (dataIn(7 downto 0), '0', disparity, dataOut, dispOut);
               disparity := dispOut;
               for i in 0 to 9 loop
                  dOutP <= dataOut(i);
                  dOutM <= not dataOut(i);
                  wait for dataClkPeriod;
               end loop;
               encode8b10b (dataIn(15 downto 8), '0', disparity, dataOut, dispOut);
               disparity := dispOut;
               for i in 0 to 9 loop
                  dOutP <= dataOut(i);
                  dOutM <= not dataOut(i);
                  wait for dataClkPeriod;
               end loop;
               dataIn := dataIn + 1;
            end loop;
            sroAck <= '0';
            -- EOF
            encode8b10b (eofK, '1', disparity, dataOut, dispOut);
            disparity := dispOut;
            for i in 0 to 9 loop
               dOutP <= dataOut(i);
               dOutM <= not dataOut(i);
               wait for dataClkPeriod;
            end loop;
            encode8b10b (eofD, '0', disparity, dataOut, dispOut);
            disparity := dispOut;
            for i in 0 to 9 loop
               dOutP <= dataOut(i);
               dOutM <= not dataOut(i);
               wait for dataClkPeriod;
            end loop;
         end if;
      
      end loop;
      
   end procedure tixelSerialData ;
   

begin
   
   PgpClk_Inst : entity surf.ClkRst
      generic map (
         CLK_PERIOD_G      => PGPCLK_PER_C,
         RST_START_DELAY_G => 0 ns,  -- Wait this long into simulation before asserting reset
         RST_HOLD_TIME_G   => 1 us)     -- Hold reset for this long)
      port map (
         clkP => pgpClkP,
         clkN => pgpClkN,
         rst  => open,
         rstL => open);
   
   ---------------------------
   -- Core block            --
   ---------------------------
   UUT_Cpix2Core : entity work.Cpix2Core 
      generic map (
         TPD_G             => TPD_C,
         BUILD_INFO_G      => toSlv (BUILD_INFO_TB_C),
         FPGA_BASE_CLOCK_G => x"00" & x"100000",
         -- Polarity of selected LVDS data lanes is swapped on gen2 ADC board
         ADC1_INVERT_CH    => "10000000",
         ADC2_INVERT_CH    => "00000010",
         SIMULATION_G      => true
      )
      port map (
         -- Debugging IOs
         led                 => open,
         -- Power enables
         digitalPowerEn      => open,
         analogPowerEn       => open,
         ioPowerEn           => open,
         fpgaOutputEn        => open,
         -- Clocks and reset
         powerGood           => '1',
         gtRefClk0P          => pgpClkP,
         gtRefClk0N          => pgpClkN,
         -- SFP interfaces
         sfpDisable          => open,
         -- SFP TX/RX
         gtDataRxP           => '0',
         gtDataRxN           => '1',
         gtDataTxP           => open,
         gtDataTxN           => open,
         -- Guard ring DAC
         vGuardDacSclk       => open,
         vGuardDacDin        => open,
         vGuardDacCsb        => open,
         vGuardDacClrb       => open,
         -- External Signals
         runTrigger          => runTrigger,
         daqTrigger          => daqTrigger,
         mpsOut              => open,
         triggerOut          => open,
         -- Board IDs
         serialIdIo          => serialIdIo,
         -- Slow ADC
         slowAdcRefClk       => open,
         slowAdcSclk         => open,
         slowAdcDin          => open,
         slowAdcCsb          => open,
         slowAdcDout         => '0',
         slowAdcDrdy         => '0',
         -- SACI
         saciClk             => open,
         saciSelL            => open,
         saciCmd             => open,
         saciRsp             => '0',
         -- Fast ADC Control
         adcSpiClk           => open,
         adcSpiData          => adcSpiData,
         adcSpiCsb           => open,
         adcPdwn             => open,
         -- Fast ADC readoutCh
         adcClkP             => adcClkP,
         adcClkN             => adcClkN,
         adcFClkP            => adcFClkP,
         adcFClkN            => adcFClkN,
         adcDClkP            => adcDClkP,
         adcDClkN            => adcDClkN,
         adcChP              => iAdcChP(19 downto 0),
         adcChN              => iAdcChN(19 downto 0),
         -- ASIC Control
         asic01DM1           => '0',
         asic01DM2           => '0',
         asicEnA             => iAsicEnA    ,
         asicEnB             => iAsicEnB    ,
         asicVid             => iAsicVid    ,
         asicPPbe            => iAsicPPbe   ,
         asicPpmat           => iAsicPpmat  ,
         asicR0              => iAsicR0     ,
         asicSR0             => iAsicSR0    ,
         asicGlblRst         => iAsicGlblRst,
         asicSync            => iAsicSync   ,
         asicAcq             => iAsicAcq    ,
         asicDoutP           => asicDoutP,
         asicDoutM           => asicDoutM,
         asicRoClk           => iAsicRoClk,
         -- Boot Memory Ports
         bootCsL             => open,
         bootMosi            => open,
         bootMiso            => '0'
      );
   
   G_ADC : for i in 0 to 2 generate 
      U_ADC : entity work.ad9249_group
      generic map (
         OUTPUT_TYPE_G     => (others=>COUNT_OUT),
         NOISE_BASELINE_G  => ADC_BASELINE_C(7+i*8 downto 0+i*8),
         NOISE_VPP_G       => (others=> 5.0e-3),
         PATTERN_G         => (others=>x"2F7C"),
         COUNT_MIN_G       => (others=>x"0000"),
         COUNT_MAX_G       => (others=>x"000F"),
         COUNT_MASK_G      => COUNT_MASK_C(7+i*8 downto 0+i*8),
         INDEX_G           => i
      )
      port map (
         aInP     => (others=>0.0),
         aInN     => (others=>0.0),
         sClk     => adcClkP(0),
         dClk     => adcDoutClk,
         fcoP     => adcFClkP(i),
         fcoN     => adcFClkN(i),
         dcoP     => adcDClkP(i),
         dcoN     => adcDClkN(i),
         dP       => adcChP(i),
         dN       => adcChN(i)
      );
      
      iAdcChP(0+i*8) <= adcChP(i)(0);
      iAdcChP(1+i*8) <= adcChP(i)(1);
      iAdcChP(2+i*8) <= adcChP(i)(2);
      iAdcChP(3+i*8) <= adcChP(i)(3);
      iAdcChP(4+i*8) <= adcChP(i)(4);
      iAdcChP(5+i*8) <= adcChP(i)(5);
      iAdcChP(6+i*8) <= adcChP(i)(6);
      iAdcChP(7+i*8) <= adcChP(i)(7);
      
      iAdcChN(0+i*8) <= adcChN(i)(0);
      iAdcChN(1+i*8) <= adcChN(i)(1);
      iAdcChN(2+i*8) <= adcChN(i)(2);
      iAdcChN(3+i*8) <= adcChN(i)(3);
      iAdcChN(4+i*8) <= adcChN(i)(4);
      iAdcChN(5+i*8) <= adcChN(i)(5);
      iAdcChN(6+i*8) <= adcChN(i)(6);
      iAdcChN(7+i*8) <= adcChN(i)(7);
      
   end generate;
   
   -- need Pll to create ADC readout clock (350 MHz)
   -- must be in phase with adcClk (50 MHz)
   U_PLLAdc : entity surf.ClockManager7
   generic map(
      INPUT_BUFG_G       => true,
      FB_BUFG_G          => true,
      NUM_CLOCKS_G       => 1,
      -- MMCM attributes
      CLKIN_PERIOD_G     => 20.0,
      DIVCLK_DIVIDE_G    => 1,
      CLKFBOUT_MULT_F_G  => 14.0,
      CLKOUT0_DIVIDE_F_G => 2.0
   )
   port map(
      -- Clock Input
      clkIn     => adcClkP(0),
      -- Clock Outputs
      clkOut(0) => adcDoutClk
   );
   
   -----------------------------------------------------------------------
   -- Sim process
   -----------------------------------------------------------------------
   process
   begin
      
      --tempAlertL <= '1';
      --
      --wait for 100 us;
      --
      --tempAlertL <= '0';
      --
      --wait for 100 us;
      --
      --tempAlertL <= '1';
      
      --wait;
      
      --acqStart <= not acqStart;
      
      wait for 100 us;
         
      
   end process;
   
   -- process emulating tixel data out
   
   process
   begin
   
      tixelSerialData ( 
         roClk       => iAsicRoClk(0),
         sroReq      => sroReq(0),
         sroAck      => sroAck(0),
         dOutP       => asicDoutP(0),
         dOutM       => asicDoutM(0)
      );
      
   end process;
   
   process
   begin
   
      tixelSerialData ( 
         roClk       => iAsicRoClk(1),
         sroReq      => sroReq(1),
         sroAck      => sroAck(1),
         dOutP       => asicDoutP(1),
         dOutM       => asicDoutM(1)
      );
      
   end process;
   
   -- start of readout handshake
   -- only for simulation procedure
   G_ASIC : for i in 0 to 1 generate
      
      process
      begin
      
         sroReq(i) <= '0';
      
         wait until rising_edge(iAsicSR0);
         
         sroReq(i) <= '1';
         
         wait until rising_edge(sroAck(i));
         
      end process;
   
   end generate;
   
   
   
end testbed;
