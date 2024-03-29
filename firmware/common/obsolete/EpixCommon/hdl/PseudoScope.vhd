-------------------------------------------------------------------------------
-- Title      : Pseudo Oscilloscope Interface
-- Project    : EPIX 
-------------------------------------------------------------------------------
-- File       : PseudoScope.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- Pseudo-oscilloscope interface for ADC channels, similar to chipscope.
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
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;

use work.ScopeTypes.all;
use work.EpixTypes.all;
use work.VcPkg.all;

entity PseudoScope is
   port ( 

      -- Master system clock
      sysClk          : in  sl;
      sysClkRst       : in  sl;

      -- ADC data
      adcData         : in  word16_array(19 downto 0);
      adcValid        : in  slv(19 downto 0);

      -- Signal for auto-rearm of trigger
      arm             : in  sl;

      -- Potential triggers in
      acqStart        : in  sl;
      asicAcq         : in  sl;
      asicR0          : in  sl;
      asicRoClk       : in  sl;
      asicPpmat       : in  sl;
      asicPpbe        : in  sl;
      asicSync        : in  sl;
      asicGr          : in  sl;
      asicSaciSel     : in  slv(3 downto 0);

      -- Configuration interface
      scopeConfig     : in  ScopeConfigType;

      -- Sequence count from normal readout block
      acqCount        : in  slv(31 downto 0);
      seqCount        : in  slv(31 downto 0);
      
      -- Data out interface
      frameTxIn       : out  VcUsBuff32InType;
      frameTxOut      :  in  VcUsBuff32OutType

   );
end PseudoScope;


-- Define architecture
architecture PseudoScope of PseudoScope is
   signal overThresholdA   : sl := '0';
   signal overThresholdB   : sl := '0';
   signal autoTrigger      : sl := '0';
   signal trigger          : sl := '0';
   signal triggerRising    : sl := '0';
   signal triggerFalling   : sl := '0';
   signal triggerToUse     : sl := '0';
   signal triggerChannel   : integer range 0 to 15 := 0;
   signal triggerMode      : integer range 0 to 3  := 0;
   signal adcChA           : slv(15 downto 0);
   signal adcChB           : slv(15 downto 0);
   signal adcChAValid      : sl;
   signal adcChBValid      : sl;
   signal bufferReadyA     : sl;
   signal bufferReadyB     : sl;
   signal bufferDataA      : slv(15 downto 0);
   signal bufferDataB      : slv(15 downto 0);
   signal bufferRdEnA      : sl;
   signal bufferRdEnB      : sl;
   signal bufferDoneA      : sl;
   signal bufferDoneB      : sl;
   signal wordCntRst       : sl;
   signal wordCntEn        : sl;
   signal wordCnt          : unsigned(3 downto 0);
   signal oddEven          : sl := '0';
   signal oddEvenToggle    : sl;
   signal oddEvenRst       : sl;
   signal armSelect        : sl;
   signal triggerAdcThresh : unsigned(15 downto 0);
   signal iFrameTxIn       : VcUsBuff32InType;
   signal adcWordPackedA   : slv(31 downto 0) := (others => '0');
   signal adcWordPackedB   : slv(31 downto 0) := (others => '0');

   type StateType is (
      IDLE_S,
      START_HDR_S,
      WAIT_SCOPE_S,
      FIRST_WORD_A_S,
      SCOPE_DATA_A_S,
      FIRST_WORD_B_S,
      SCOPE_DATA_B_S,
      STOP_S);
   signal curState : StateType := IDLE_S;
   signal nxtState : StateType := IDLE_S;

   -- Hard coded words in the data stream
   -- Some may be updated later.
   constant cLane     : slv( 1 downto 0) := "00";
   constant cVC       : slv( 1 downto 0) := "10";
   constant cQuad     : slv( 1 downto 0) := "00";
   constant cOpCode   : slv( 7 downto 0) := x"00";
   constant cZeroWord : slv(31 downto 0) := x"00000000";

begin

   -- Output
   frameTxIn.valid <= iFrameTxIn.valid;   
   frameTxIn.sof   <= iFrameTxIn.sof;
   frameTxIn.eof   <= iFrameTxIn.eof;
   frameTxIn.eofe  <= iFrameTxIn.eofe;
   frameTxIn.data  <= iFrameTxIn.data(15 downto 0) & iFrameTxIn.data(31 downto 16);
   
   -- Type conversions
   triggerChannel   <= to_integer(unsigned(scopeConfig.triggerChannel));
   triggerAdcThresh <= unsigned(scopeConfig.triggerAdcThresh);
   triggerMode      <= to_integer(unsigned(scopeConfig.triggerMode));

   -- Arming mode
   armSelect <= '0'             when triggerMode = 0 else
                scopeConfig.arm when triggerMode = 1 else
                arm             when triggerMode = 2 else
                '1';

   -- Trigger multiplexing
   trigger <= scopeConfig.trig when triggerChannel =  0 else
              overThresholdA   when triggerChannel =  1 else
              overThresholdB   when triggerChannel =  2 else
              acqStart         when triggerChannel =  3 else
              asicAcq          when triggerChannel =  4 else
              asicR0           when triggerChannel =  5 else
              asicRoClk        when triggerChannel =  6 else
              asicPpmat        when triggerChannel =  7 else
              asicPpbe         when triggerChannel =  8 else
              asicSync         when triggerChannel =  9 else
              asicGr           when triggerChannel = 10 else
              asicSaciSel(0)   when triggerChannel = 11 else
              asicSaciSel(1)   when triggerChannel = 12 else
              asicSaciSel(2)   when triggerChannel = 13 else
              asicSaciSel(3)   when triggerChannel = 14 else
              '0'              when triggerChannel = 15 else
              'X';

   -- Generate edges of the possible trigger signals
   U_RunEdge : entity surf.SynchronizerEdge 
      port map (
         clk         => sysClk,
         rst         => sysClkRst,
         dataIn      => trigger,
         risingEdge  => triggerRising,
         fallingEdge => triggerFalling
      ); 

   -- And make the final trigger output
   triggerToUse <= triggerRising  when scopeConfig.triggerEdge = '1' else
                   triggerFalling when scopeConfig.triggerEdge = '0' else
                   'X';

   -- Logic for the levels on the ADCs
   process(sysClk) begin
      if rising_edge(sysClk) then
         if (unsigned(adcChA) > triggerAdcThresh) then
            overThresholdA  <= '1';
         else
            overThresholdA  <= '0';
         end if;
         if (unsigned(adcChB) > triggerAdcThresh) then
            overThresholdB  <= '1';
         else
            overThresholdB  <= '0';
         end if;
      end if;
   end process;

   -- Input channel multiplexing
   adcChA <= adcData(to_integer(unsigned(scopeConfig.inputChannelA)));
   adcChB <= adcData(to_integer(unsigned(scopeConfig.inputChannelB)));
   adcChAValid <= adcValid(to_integer(unsigned(scopeConfig.inputChannelA)));
   adcChBValid <= adcValid(to_integer(unsigned(scopeConfig.inputChannelA)));

   -- Instantiate ring buffers for storing the ADC data
   RingBufferA : entity work.RingBuffer
      generic map(
         MEMORY_TYPE_G=> "block",
         DATA_WIDTH_G => 16,
         ADDR_WIDTH_G => 13)
      port map (
         sysClk      => sysClk,
         sysClkRst   => sysClkRst,
         wrData      => adcChA,
         wrValid     => adcChAValid,
         arm         => armSelect,
         rdEn        => bufferRdEnA,
         rdData      => bufferDataA,
         rdReady     => bufferReadyA, 
         rdDone      => bufferDoneA,
         trigger     => triggerToUse,
         holdoff     => scopeConfig.triggerHoldoff,
         offset      => scopeConfig.triggerOffset,
         skipSamples => scopeConfig.skipSamples,
         depth       => scopeConfig.traceLength
      );
   RingBufferB : entity work.RingBuffer
      generic map(
         MEMORY_TYPE_G=> "block",
         DATA_WIDTH_G => 16,
         ADDR_WIDTH_G => 13)
      port map (
         sysClk      => sysClk,
         sysClkRst   => sysClkRst,
         wrData      => adcChB,
         wrValid     => adcChBValid,
         arm         => armSelect,
         rdEn        => bufferRdEnB,
         rdData      => bufferDataB,
         rdReady     => bufferReadyB, 
         rdDone      => bufferDoneB,
         trigger     => triggerToUse,
         holdoff     => scopeConfig.triggerHoldoff,
         offset      => scopeConfig.triggerOffset,
         skipSamples => scopeConfig.skipSamples,
         depth       => scopeConfig.traceLength
      );

   --State machine to send out the data

   --Synchronous part
   process(sysClk) begin
      if rising_edge(sysClk) then
         if (sysClkRst = '1' or scopeConfig.scopeEnable = '0') then
            curState <= IDLE_S;
         else
            curState <= nxtState;
         end if;
      end if;
   end process;

   process(curState,wordCnt,bufferReadyA,bufferReadyB,bufferDataA,bufferDataB,
           oddEven,frameTxOut,trigger,iFrameTxIn,bufferDoneA,bufferDoneB,
           adcWordPackedA,adcWordPackedB,bufferRdEnA,bufferRdEnB) begin
      --Defaults
      iFrameTxIn.data  <= (others => '0');
      iFrameTxIn.valid <= '0';
      iFrameTxIn.sof   <= '0';
      iFrameTxIn.eof   <= '0';
      iFrameTxIn.eofe  <= '0';
      bufferRdEnA      <= '0';
      bufferRdEnB      <= '0';
      wordCntRst       <= '0';
      wordCntEn        <= '0';
      oddEvenRst       <= '0';
      oddEvenToggle    <= '0';
      nxtState         <= curState;
      if (frameTxOut.almostFull = '0') then
         case curState is
            when IDLE_S =>
               if trigger = '1' then
                  wordCntRst <= '1';
                  nxtState   <= WAIT_SCOPE_S;
               end if;
            when WAIT_SCOPE_S =>
               if bufferReadyA = '1' and bufferReadyB = '1' then
                  oddEvenRst  <= '1';
                  nxtState    <= START_HDR_S;
               end if;
            when START_HDR_S =>
               wordCntEn                <= '1';
               iFrameTxIn.valid <= '1';
               case to_integer(wordCnt) is
                  when 0 => iFrameTxIn.data <= x"000000" & "00" & cLane & "00" & cVC;
                            iFrameTxIn.sof  <= '1';
                  when 1 => iFrameTxIn.data <= x"0" & "00" & cQuad & cOpCode & acqCount(15 downto 0);
                  when 2 => iFrameTxIn.data <= seqCount;
                  when 3 => iFrameTxIn.data <= cZeroWord;
                  when 4 => iFrameTxIn.data <= cZeroWord;
                  when 5 => iFrameTxIn.data <= cZeroWord;
                  when 6 => iFrameTxIn.data <= cZeroWord;
                  when 7 => iFrameTxIn.data <= cZeroWord;
                            nxtState <= FIRST_WORD_A_S;
                  when others  => iFrameTxIn.data <= cZeroWord;
               end case;
            when FIRST_WORD_A_S =>
               bufferRdEnA            <= '1';
               oddEvenToggle          <= '1';
               if oddEven = '1' then
                  nxtState               <= SCOPE_DATA_A_S;
               end if;
            when SCOPE_DATA_A_S =>
               bufferRdEnA            <= '1';
               oddEvenToggle          <= '1';
               iFrameTxIn.data <= adcWordPackedA;
               if (bufferRdEnA = '1' and oddEven = '1') then
                  iFrameTxin.valid <= '1';
               end if;
               if bufferDoneA = '1' then
                  --iFrameTxIn.valid <= '1';  --force write if odd size
                  oddEvenRst               <= '1';
                  nxtState                 <= FIRST_WORD_B_S;
               end if;
            when FIRST_WORD_B_S =>
               bufferRdEnB            <= '1';
               oddEvenToggle          <= '1';
               if oddEven = '1' then
                  nxtState               <= SCOPE_DATA_B_S;
               end if;
            when SCOPE_DATA_B_S =>
               bufferRdEnB            <= '1';
               oddEvenToggle          <= '1';
               iFrameTxIn.data <= adcWordPackedB;
               if (bufferRdEnB = '1' and oddEven = '1') then
                  iFrameTxin.valid <= '1';
               end if;
               if bufferDoneB = '1' then
                  --iFrameTxIn.valid <= '1';  --force write if odd size
                  oddEvenRst               <= '1';
                  wordCntRst               <= '1';
                  nxtState                 <= STOP_S;
               end if; 
            when STOP_S =>
               iFrameTxIn.data  <= cZeroWord;
               iFrameTxIn.valid <= '1';
               wordCntEn                <= '1';
               if wordCnt = 4 then
                  iFrameTxIn.eof    <= '1';
                  nxtState <= IDLE_S;
               end if;
            when others =>
         end case;
      end if;
   end process;

   --Odd even counter used for packing words
   process(sysClk) begin
      if rising_edge(sysClk) then
         if oddEvenRst = '1' then
            oddEven <= '0';
         elsif oddEvenToggle = '1' then
            oddEven <= not(oddEven);
         end if;
      end if;
   end process;
   --Pack 16-bit ADC values into 32 bit words
   process(sysClk) begin
      if rising_edge(sysClk) then
         if oddEven = '1' then
            --adcWordPackedA <= x"0000" & x"A" & bufferDataA(11 downto 0);
            --adcWordPackedB <= x"0000" & x"B" & bufferDataB(11 downto 0);
            adcWordPackedA <= x"0000" & bufferDataA;
            adcWordPackedB <= x"0000" & bufferDataB;
         else
            adcWordPackedA(31 downto 16) <= bufferDataA;
            adcWordPackedB(31 downto 16) <= bufferDataB;
         end if;
      end if;
   end process;

   --Counts the number of words to choose what data to send next
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or wordCntRst = '1' then
            wordCnt <= (others => '0');
         elsif wordCntEn = '1' then
            wordCnt <= wordCnt + 1;
         end if; 
      end if; 
   end process;


end PseudoScope;

