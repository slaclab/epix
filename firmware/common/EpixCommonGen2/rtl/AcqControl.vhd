-------------------------------------------------------------------------------
-- Title      : Acquisition Control Block
-- Project    : EPIX Readout
-------------------------------------------------------------------------------
-- File       : AcqControl.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- Acquisition control block
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

LIBRARY ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

library surf;
use surf.StdRtlPkg.all;

use work.EpixPkgGen2.all;

library UNISIM;
use UNISIM.vcomponents.all;

entity AcqControl is
   generic (
      ASIC_TYPE_G       : AsicType  := EPIX100A_C;
      TPD_G             : time      := 1 ns
   );
   port (

      -- Clocks and reset
      sysClk              : in    std_logic;
      sysClkRst           : in    std_logic;

      -- Run control
      acqStart            : in    std_logic;
      acqBusy             : out   std_logic;
      readDone            : in    std_logic;
      readValid           : out   slv(15 downto 0);
      adcPulse            : out   std_logic;
      roClkTail           : in    std_logic_vector(7 downto 0);
      injAcq              : out   std_logic;

      -- Configuration
      epixConfig          : in    EpixConfigType;
      epixConfigExt       : in    EpixConfigExtType;

      -- Fast ADC Readout
      adcClkP             : out   std_logic_vector(2 downto 0);
      adcClkM             : out   std_logic_vector(2 downto 0);

      -- ASIC Control
      asicR0              : out   std_logic;
      asicPpmat           : out   std_logic;
      asicPpbe            : out   std_logic;
      asicGlblRst         : out   std_logic;
      asicAcq             : out   std_logic;
      asicSync            : out   std_logic;
      asicRoClk           : out   std_logic

   );
end AcqControl;


-- Define architecture
architecture AcqControl of AcqControl is
   
   
   -- epix10ka dummy acquisition settings
   -- dummy acquisition to remove the ghost
   constant DUMMY_ASIC_ROCLK_HALFT_C   : natural := 2;
   constant DUMMY_ASIC_R0_TO_ACQ_C     : natural := 2500;
   constant DUMMY_ASIC_ACQ_WIDTH_C     : natural := 2500;
   
   -- arbitrary sync pulse width (1us)
   constant SYNC_WIDTH_C               : natural := 100;
   
   constant DUMMY_ACQ_EN_C : boolean := ite(ASIC_TYPE_G = EPIX10KA_C, true, false);
   
   signal dummyAcq : sl;
   signal dummyAcqSet : sl;
   signal dummyAcqClr : sl;

   -- Local Signals
   signal adcClk             : std_logic             := '0';
   signal adcClkEdge         : std_logic             := '0';
   signal asicClk            : std_logic             := '0';
   signal acqStartEdge       : std_logic             := '0';
   signal adcCnt             : unsigned(31 downto 0) := (others => '0');
   signal adcSampCnt         : slv(31 downto 0) := (others => '0');
   signal adcSampCntRst      : sl := '0';
   signal rstCnt             : unsigned(25 downto 0) := (others => '0');
   signal stateCnt           : unsigned(31 downto 0) := (others => '0');
   signal stateCntEn         : sl := '0';
   signal stateCntRst        : sl := '0';
   signal pixelCnt           : unsigned(31 downto 0) := (others => '0');
   signal pixelCntEn         : sl := '0';
   signal pixelCntRst        : sl := '0';
   signal iReadValid         : sl := '0';
   signal iReadValidWaiting  : slv(15 downto 0) := (others=>'0');
   signal readValidDelayed   : Slv128Array(15 downto 0);
   signal firstPixel         : sl := '0';
   signal firstPixelSet      : sl := '0';
   signal firstPixelRst      : sl := '0';
   signal iAcqBusy           : sl := '0';
   signal risingAcq          : sl := '0';
   signal risingAcqD1        : sl := '0';
   signal fallingAcq         : sl := '0';
   signal selEdgeAcq         : sl := '0';

   -- Multiplexed ASIC outputs.  These versions are the
   -- automatic ones controlled by state machine.
   -- You can override them with the manualPinControl config bits.
   signal iAsicR0          : std_logic := '0';
   signal iAsicPpmat       : std_logic := '0';
   signal iAsicPpbe        : std_logic := '0';
   signal iAsicGlblRst     : std_logic := '0';
   signal iAsicAcq         : std_logic := '0';
   signal iAsicClk         : std_logic := '0';
   signal iInjAcq          : std_logic;
   
   signal iAsicSync         : sl;

   -- State machine values
   type state is (IDLE_S,
                  WAIT_R0_S,
                  PULSE_R0_S,
                  WAIT_ACQ_S,
                  ACQ_S,
                  DROP_ACQ_S,
                  WAIT_PPMAT_S,
                  WAIT_POST_PPMAT_S,
                  SYNC_TO_ADC_S,
                  WAIT_ADC_S,
                  NEXT_CELL_S,
                  WAIT_DOUT_S,
                  NEXT_DOUT_S,
                  SYNC_RESET_S,
                  DONE_S);
   signal curState           : state := IDLE_S;
   signal nxtState           : state := IDLE_S;
   
   signal injTimeCnt    : slv(31 downto 0) := (others => '0');
   -- signal injStopCnt    : slv(31 downto 0);
   -- signal injSkipCnt    : slv(7 downto 0);
   -- signal injStartEn    : sl;
   -- signal injStopEn     : sl;
   

begin

   -- ADC Clock outputs
   U_AdcClk0 : OBUFDS port map ( I => adcClk, O => adcClkP(0), OB => adcClkM(0) );
   U_AdcClk1 : OBUFDS port map ( I => adcClk, O => adcClkP(1), OB => adcClkM(1) );
   U_AdcClk2 : OBUFDS port map ( I => adcClk, O => adcClkP(2), OB => adcClkM(2) );

   -- Single ended version out
   asicRoClk <= asicClk;

   --MUXes for manual control of ASIC signals
   asicGlblRst <= iAsicGlblRst           when ePixConfig.manualPinControl(0) = '0' else
                  ePixConfig.asicPins(0) when ePixConfig.manualPinControl(0) = '1' else
                  'X';
   asicAcq     <= iAsicAcq               when ePixConfig.manualPinControl(1) = '0' else
                  ePixConfig.asicPins(1) when ePixConfig.manualPinControl(1) = '1' else
                  'X';
   asicR0      <= iAsicR0                when ePixConfig.manualPinControl(2) = '0' else
                  ePixConfig.asicPins(2) when ePixConfig.manualPinControl(2) = '1' else
                  'X';
   asicPpmat   <= iAsicPpmat             when ePixConfig.manualPinControl(3) = '0' else
                  ePixConfig.asicPins(3) when ePixConfig.manualPinControl(3) = '1' else
                  'X';
   asicPpbe    <= iAsicPpbe              when ePixConfig.manualPinControl(4) = '0' else
                  ePixConfig.asicPins(4) when ePixConfig.manualPinControl(4) = '1' else
                  'X';
   asicClk     <= iAsicClk               when ePixConfig.manualPinControl(5) = '0' else
                  ePixConfig.asicPins(5) when ePixConfig.manualPinControl(5) = '1' else
                  'X';
   -- injAcq is used for the external trigger timed with the ACQ but can also be used as sync triggering the ASIC's pulser
   asicSync    <= iAsicSync              when epixConfigExt.injSyncEn = '0' else iInjAcq;
   injAcq      <= iInjAcq;
   
   --Outputs not incorporated into state machine at the moment
   iAsicPpbe    <= '1'; 

   --Busy is internal busy or data left in the pipeline
   acqBusy <= '1' when iAcqBusy = '1' or iReadValidWaiting /= 0 else '0';
   
   -- ADC pulse signal allows counting of adc cycles in other blocks
   adcPulse <= adcClkEdge;
   
   U_ReadStartEdge : entity surf.SynchronizerEdge
      port map (
         clk        => sysClk,
         rst        => sysClkRst,
         dataIn     => acqStart,
         risingEdge => acqStartEdge
      );
   

   --Next state logic
   process(curState,acqStartEdge,stateCnt,adcSampCnt,pixelCnt,ePixConfig,adcClkEdge,readDone,roClkTail,dummyAcq,epixConfigExt) begin
      
      --All signals default values
      iAsicClk           <= '0' after TPD_G;
      iAsicR0            <= '1' after TPD_G;
      iAsicPpmat         <= '0' after TPD_G;
      iAsicAcq           <= '0' after TPD_G;
      iAsicSync          <= '0' after TPD_G;
      stateCntEn         <= '0' after TPD_G;
      stateCntRst        <= '0' after TPD_G;
      adcSampCntRst      <= '0' after TPD_G;
      pixelCntEn         <= '0' after TPD_G;
      pixelCntRst        <= '1' after TPD_G;
      iAcqBusy           <= '1' after TPD_G;
      firstPixelRst      <= '0' after TPD_G;
      firstPixelSet      <= '0' after TPD_G;
      dummyAcqSet        <= '0' after TPD_G;
      dummyAcqClr        <= '0' after TPD_G;
      
      case curState is
         --Remain idle until we get the acqStart signal
         when IDLE_S =>
            iAcqBusy       <= '0' after TPD_G;
            stateCntRst    <= '1' after TPD_G;
            adcSampCntRst  <= '1' after TPD_G;
            firstPixelRst  <= '1' after TPD_G;
            iAsicR0        <= '0' after TPD_G;
            dummyAcqClr    <= '1' after TPD_G;
            if acqStartEdge = '1' then
               nxtState <= WAIT_R0_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Wait a specified number of clock cycles before bringing asicR0 up
         when WAIT_R0_S =>
            iAsicPpmat     <= '1' after TPD_G;
            iAsicR0        <= '0' after TPD_G;
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.acqToAsicR0Delay) or dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= PULSE_R0_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if; 
         
         --Pulse R0 low for a specified number of clock cycles
         when PULSE_R0_S =>
            iAsicPpmat     <= '1' after TPD_G;
            iAsicR0        <= '0' after TPD_G;
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicR0Width) or dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= WAIT_ACQ_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Wait a specified number of clock cycles before bringing asicAcq up
         when WAIT_ACQ_S => 
            iAsicPpmat     <= '1' after TPD_G;
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicR0ToAsicAcq) and dummyAcq = '0' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= ACQ_S after TPD_G;
            elsif stateCnt >= DUMMY_ASIC_R0_TO_ACQ_C-1 and dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= ACQ_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Hold acq high for a specified time
         when ACQ_S =>
            iAsicPpmat     <= '1' after TPD_G;
            iAsicAcq       <= '1' after TPD_G;
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicAcqWidth) and dummyAcq = '0' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= DROP_ACQ_S after TPD_G;
            elsif stateCnt >= DUMMY_ASIC_ACQ_WIDTH_C-1 and dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= DROP_ACQ_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Wait for the matrix counter to reset (via saci interface)
         when DROP_ACQ_S =>
            iAsicPpmat      <= '1' after TPD_G;
            stateCntEn      <= '1' after TPD_G;
            
            nxtState <= WAIT_PPMAT_S after TPD_G;
         
         --Ensure that the minimum hold off time has been enforced before dropping PPmat
         when WAIT_PPMAT_S =>
            iAsicPpmat     <= '1' after TPD_G;
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicAcqLToPPmatL) or dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= WAIT_POST_PPMAT_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         -- Programmable delay before starting the readout after dropping PPmat
         when WAIT_POST_PPMAT_S =>
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicPPmatToReadout) or dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= SYNC_TO_ADC_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Synchronize phases of ASIC RoClk and ADC clk
         when SYNC_TO_ADC_S =>
            if adcClkEdge = '1' then
               nxtState <= NEXT_CELL_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --ADC reads out while we wait a half period of RoClk.  If we're done with all pixels, finish.
         when WAIT_ADC_S => 
            pixelCntRst    <= '0' after TPD_G;
            firstPixelSet  <= '1' after TPD_G;
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicRoClkHalfT(31 downto 16))-1 and dummyAcq = '0' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               pixelCntEn  <= '1' after TPD_G;
               if pixelCnt < unsigned(ePixConfig.totalPixelsToRead)-1 then
                  nxtState <= NEXT_CELL_S after TPD_G;
               else
                  if unsigned(roClkTail) = 0 then
                     nxtState <= SYNC_RESET_S after TPD_G;
                  else
                     nxtState <= NEXT_DOUT_S after TPD_G;
                  end if;
               end if;
            -- do faster (dummy) readout 
            -- DUMMY_ASIC_ROCLK_HALFT_C = 2 -> 40ns -> 25MHz (this clock is divided by 4 inside epix10kA)
            elsif stateCnt >= DUMMY_ASIC_ROCLK_HALFT_C-1 and dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               pixelCntEn  <= '1' after TPD_G;
               if pixelCnt < unsigned(ePixConfig.totalPixelsToRead)-1 then
                  nxtState <= NEXT_CELL_S after TPD_G;
               else
                  if unsigned(roClkTail) = 0 then
                     nxtState <= SYNC_RESET_S after TPD_G;
                  else
                     nxtState <= NEXT_DOUT_S after TPD_G;
                  end if;
               end if;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Toggle the asicClk, then back to ADC readouts if there are more pixels to read.
         when NEXT_CELL_S => 
            pixelCntRst    <= '0' after TPD_G;
            iAsicClk       <= '1' after TPD_G;
            stateCntEn     <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicRoClkHalfT(15 downto 0))-1 and dummyAcq = '0' then
               stateCntEn     <= '0' after TPD_G;
               adcSampCntRst  <= '1' after TPD_G;
               stateCntRst    <= '1' after TPD_G;
               nxtState       <= WAIT_ADC_S after TPD_G;
            -- do faster (dummy) readout 
            -- DUMMY_ASIC_ROCLK_HALFT_C = 2 -> 40ns -> 25MHz (this clock is divided by 4 inside epix10kA)
            elsif stateCnt >= DUMMY_ASIC_ROCLK_HALFT_C-1 and dummyAcq = '1' then
               stateCntEn     <= '0' after TPD_G;
               adcSampCntRst  <= '1' after TPD_G;
               stateCntRst    <= '1' after TPD_G;
               nxtState       <= WAIT_ADC_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         -- continue asicClk untill all douts are captured (epix10ka only)
         when NEXT_DOUT_S => 
            pixelCntRst <= '0' after TPD_G;
            iAsicClk    <= '1' after TPD_G;
            stateCntEn  <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicRoClkHalfT(15 downto 0))-1 and dummyAcq = '0' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= WAIT_DOUT_S after TPD_G;
            -- do faster (dummy) readout 
            -- DUMMY_ASIC_ROCLK_HALFT_C = 2 -> 40ns -> 25MHz (this clock is divided by 4 inside epix10kA)
            elsif stateCnt >= DUMMY_ASIC_ROCLK_HALFT_C-1 and dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               nxtState    <= WAIT_DOUT_S after TPD_G;
            else 
               nxtState <= curState after TPD_G;
            end if;
         
         when WAIT_DOUT_S => 
            pixelCntRst <= '0' after TPD_G;
            stateCntEn  <= '1' after TPD_G;
            if stateCnt >= unsigned(ePixConfig.asicRoClkHalfT(31 downto 16))-1 and dummyAcq = '0' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               pixelCntEn  <= '1' after TPD_G;
               if pixelCnt < unsigned(ePixConfig.totalPixelsToRead)+unsigned(roClkTail)-1 then
                  nxtState <= NEXT_DOUT_S after TPD_G;
               else
                  nxtState <= SYNC_RESET_S after TPD_G;
               end if;
            -- do faster (dummy) readout 
            -- DUMMY_ASIC_ROCLK_HALFT_C = 2 -> 40ns -> 25MHz (this clock is divided by 4 inside epix10kA)
            elsif stateCnt >= DUMMY_ASIC_ROCLK_HALFT_C-1 and dummyAcq = '1' then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               pixelCntEn  <= '1' after TPD_G;
               if pixelCnt < unsigned(ePixConfig.totalPixelsToRead)+unsigned(roClkTail)-1 then
                  nxtState <= NEXT_DOUT_S after TPD_G;
               else
                  nxtState <= SYNC_RESET_S after TPD_G;
               end if;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --make SYNC pulse to reset ASIC readout counters
         when SYNC_RESET_S =>
            iAsicSync  <= '1' after TPD_G;
            iAcqBusy   <= '0' after TPD_G;
            iAsicR0    <= '0' after TPD_G;
            stateCntEn <= '1' after TPD_G;
            -- arbitrary sync pulse width (1us)
            if stateCnt >= SYNC_WIDTH_C then
               stateCntEn  <= '0' after TPD_G;
               stateCntRst <= '1' after TPD_G;
               -- this is implementing the gost effect correction in epix10ka
               -- until we have new ASICs with a proper fix
               -- run one more dummy ASIC acquisition cycle
               -- outputs won't be sampled and sent out
               -- the dummy cycle will be faster than normal acq cycle
               if dummyAcq = '0' and epixConfigExt.ghostCorr = '1' then
                  nxtState <= WAIT_R0_S after TPD_G;
                  dummyAcqSet <= '1' after TPD_G;
               else
                  nxtState <= DONE_S after TPD_G;
               end if;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Wait for readout to be done
         when DONE_S =>
            iAcqBusy    <= '0' after TPD_G;
            iAsicR0     <= '0' after TPD_G;
            if readDone = '1' then
               nxtState <= IDLE_S after TPD_G;
            else
               nxtState <= curState after TPD_G;
            end if;
         
         --Send back to IDLE if we end up in an undefined state
         when others =>
            nxtState <= IDLE_S after TPD_G;
      end case;
   end process;

   --Next state register update and synchronous reset to IDLE
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            curState <= IDLE_S after TPD_G;
         else 
            curState <= nxtState after TPD_G;
         end if;
      end if;
   end process;

   --Process to clock the ADC at selected frequency (50-50 duty cycle)
   process(sysClk) begin
      if rising_edge(sysClk) then
         if adcCnt >= unsigned(ePixConfig.adcClkHalfT)-1 then
            adcClk <= not(AdcClk)     after TPD_G;
            adcCnt <= (others => '0') after TPD_G;
         else
            adcCnt <= adcCnt + 1 after TPD_G;
         end if;
      end if;
   end process;

   -- Count the number of ADC samples within a single readout clock cycle 
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or adcSampCntRst = '1' then
            adcSampCnt <= (others => '0') after TPD_G;
         elsif adcClkEdge = '1' then
            adcSampCnt <= adcSampCnt + 1 after TPD_G;
         end if;
      end if;
   end process;
   --Give a flag saying whether the samples are valid to read
   process(adcSampCnt,epixConfig,firstPixel,sysClkRst, pixelCnt, dummyAcq) begin
      if sysClkRst = '1' or dummyAcq = '1' then
         iReadValid <= '0';
      else
         iReadValid <= '0';
         if ASIC_TYPE_G = EPIX10KA_C then
            -- in epix10ka analog output is valid after 4 readout clocks
            if adcSampCnt < 1 and firstPixel = '0' and pixelCnt(1 downto 0) = 3 then
               iReadValid <= '1' after TPD_G;
            end if;
         else
            if adcSampCnt < 1 and firstPixel = '0' then
               iReadValid <= '1' after TPD_G;
            end if;
         end if;
      end if;
   end process;

   --Count the current pixel position
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or pixelCntRst = '1' then
            pixelCnt <= (others => '0') after TPD_G;
         elsif pixelCntEn = '1' then
            pixelCnt <= pixelCnt + 1;
         end if;
      end if;
   end process;

   --Flag the first pixel
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or firstPixelRst = '1' then
            firstPixel <= '1' after TPD_G;
         elsif firstPixelSet = '1' then
            firstPixel <= '0';
         end if;
      end if;
   end process;
   
   --Set dummy ACQ flag
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or dummyAcqClr = '1' then
            dummyAcq <= '0' after TPD_G;
         elsif dummyAcqSet = '1' then
            dummyAcq <= '1';
         end if;
      end if;
   end process;

   --Or have an initial startup timer reset
   iAsicGlblRst <= rstCnt(rstCnt'left);
   process(sysClk) begin
      if rising_edge(sysClk) then
         if epixConfig.powerEnable(0) = '0' then
            rstCnt <= (others => '0') after TPD_G;
         elsif rstCnt(rstCnt'left) = '0' then
            rstCnt <= rstCnt + 1 after TPD_G;
         end if;
      end if;
   end process;

   --Generic counter for holding state machine states
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or stateCntRst = '1' then
            stateCnt <= (others => '0') after TPD_G;
         elsif stateCntEn = '1' then
            stateCnt <= stateCnt + 1 after TPD_G;
         end if;
      end if;
   end process;

   --Pipeline for the valid signal
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            readValidDelayed <= (others => (others => '0')) after TPD_G;     
         elsif (adcClkEdge = '1') then
            --Shift register to allow picking off delayed samples
            for i in 1 to 127 loop
               for j in 15 downto 0 loop
                  readValidDelayed(j)(i) <= readValidDelayed(j)(i-1) after TPD_G; 
               end loop;
            end loop;
            --Assignment of shifted-in bits
            --Test mode can only use the first oversampling shift register
            for j in 15 downto 0 loop
               readValidDelayed(j)(0) <= iReadValid after TPD_G;
            end loop;
         end if;
      end if;
   end process; 
   --Wire up the delayed output
   G_OUTS : for j in 15 downto 0 generate
      readValid(j) <= readValidDelayed(j)( conv_integer(epixConfigExt.pipelineDelay(j)) );
   end generate;
   --Single bit signal that indicates whether there is anything left in the pipeline
   process(sysClk)
      variable runningOr : slv(15 downto 0) := (others=>'0');
   begin
      if rising_edge(sysClk) then
         if (sysClkRst = '1') then
            iReadValidWaiting <= (others=>'0');
         else
            runningOr := (others=>'0');
            for i in 0 to 127 loop
               for j in 15 downto 0 loop
                  runningOr(j) := runningOr(j) or readValidDelayed(j)(i);
               end loop;
            end loop;
            iReadValidWaiting <= runningOr;
         end if;
      end if;
   end process;

   -- Edge detection for signals that interface with other blocks
   U_DataSendEdge : entity surf.SynchronizerEdge
      port map (
         clk        => sysClk,
         rst        => sysClkRst,
         dataIn     => adcClk,
         risingEdge => adcClkEdge
      );

   -- rising edge of Acq
   -- U_AcqEdge : entity surf.SynchronizerEdge
   --    port map (
   --       clk         => sysClk,
   --       rst         => sysClkRst,
   --       dataIn      => iAsicR0,
   --       risingEdge  => risingAcq,
   --       fallingEdge => open
   --    );
   
   -- falling edge strobe is used to misalign the sync pulse vs acq on demand
   -- selEdgeAcq <= risingAcqD1 when injSkipCnt = 0 else fallingAcq;
   
   -- generate external adjustable injection trigger wrt R0 pulse
   process(sysClk)
   begin
      if rising_edge(sysClk) then
         if iAsicR0 = '1' and  dummyAcq = '0' then
            if injTimeCnt /= x"FFFFFFFF" then
               injTimeCnt <= injTimeCnt + 1;
            end if;
            
            if epixConfigExt.injDelay <= injTimeCnt and epixConfigExt.injDelay /= 0 then 
               iInjAcq <= '1';
               
               if epixConfigExt.injDlyWidth  /= 0 and (epixConfigExt.injDlyWidth + epixConfigExt.injDelay) <= injTimeCnt then
                  iInjAcq <= '0';
               end if;
            end if;

         elsif iAsicR0 = '0' then
            iInjAcq <= '0';
            injTimeCnt <= (others => '0');
      
         end if;
      
      end if;
   end process;

end AcqControl;

