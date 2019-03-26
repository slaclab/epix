-------------------------------------------------------------------------------
-- Title         : Acquisition Control Block
-- Project       : EPIX Readout
-------------------------------------------------------------------------------
-- File          : ReadoutControl.vhd
-- Author        : Kurtis Nishimura, kurtisn@slac.stanford.edu
-- Created       : 12/08/2011
-------------------------------------------------------------------------------
-- Description:
-- Readout control block
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------
-- Modification history:
-- 12/08/2011: created.
-- 07/07/2014: Updated style of primary state machine
-------------------------------------------------------------------------------

LIBRARY ieee;
use work.all;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;
use work.StdRtlPkg.all;
use work.AxiStreamPkg.all;
use work.SsiPkg.all;
use work.EpixPkgGen2.all;
library UNISIM;
use UNISIM.vcomponents.all;

entity ReadoutControl is
   generic (
      TPD_G                      : time := 1 ns;
      ASIC_TYPE_G                : AsicType;
      MASTER_AXI_STREAM_CONFIG_G : AxiStreamConfigType := ssiAxiStreamConfig(4, TKEEP_COMP_C)
   );
   port (

      -- Clocks and reset
      sysClk              : in    sl;
      sysClkRst           : in    sl;

      -- Configuration
      epixConfig          : in    EpixConfigType;

      -- Data for headers
      acqCount            : in    slv(31 downto 0);

      -- Frame counter out to register control
      seqCount            : out   slv(31 downto 0);

      -- Opcode to insert into frame
      opCode              : in    slv(7 downto 0);
      
      -- Run control
      acqStart            : in    sl;
      readValidA0         : in    sl;
      readValidA1         : in    sl;
      readValidA2         : in    sl;
      readValidA3         : in    sl;
      readDone            : out   sl;
      acqBusy             : in    sl;
      dataSend            : in    sl;
      readTps             : in    sl;

      -- ADC Data
      adcPulse            : in    sl;
      adcValid            : in    slv(19 downto 0);
      adcData             : in    Slv16Array(19 downto 0);
      
      -- monitoring data (ADC board gen2)
      envData             : in    Slv32Array(8 downto 0);

      -- Data out interface
      mAxisMaster         : out AxiStreamMasterType;
      mAxisSlave          : in  AxiStreamSlaveType;

      -- MPS
      mpsOut              : out   sl;
      
      -- EPIX10KA bank-deserialized digital outputs
      doutOut             : in  Slv2Array(15 downto 0);
      doutRd              : out slv(15 downto 0);
      doutValid           : in  slv(15 downto 0);
      
      tagIn                : in sl
   );
end ReadoutControl;

-- Define architecture
architecture ReadoutControl of ReadoutControl is
   
   constant NCOL_C       : integer          := getNumColumns(ASIC_TYPE_G);
   constant WORDS_PER_SUPER_ROW_C  : integer := getWordsPerSuperRow(ASIC_TYPE_G);

   -- Timeout in clock cycles between acqStart and sendData
   constant DAQ_TIMEOUT_C   : slv(31 downto 0) := conv_std_logic_vector(12500,32); --100 us at 125 MHz
   constant STUCK_TIMEOUT_C : slv(31 downto 0) := conv_std_logic_vector(1250000,32); --2 s at 125 MHz
   -- Depth of FIFO 
   constant CH_FIFO_ADDR_WIDTH_C : integer := 10;
   -- Hard coded words in the data stream for now
   constant LANE_C     : slv( 1 downto 0) := "00";
   constant VC_C       : slv( 1 downto 0) := "00";
   constant QUAD_C     : slv( 1 downto 0) := "00";
   constant ZEROWORD_C : slv(31 downto 0) := x"00000000";
   -- Register delay for simulation
   constant TPD_C : time := 0.5 ns;

   
   -- State definitions
   type StateType is (IDLE_S,ARMED_S,HEADER_S,READ_FIFO_S,
                      ENV_DATA_S,TPS_DATA_S,FOOTER_S);

   -- Local Signals
   type RegType is record
      readDone       : sl;
      testPattern    : sl;
      seqCountEn     : sl;
      fillCnt        : slv(CH_FIFO_ADDR_WIDTH_C-1 downto 0);
      chCnt          : slv(3 downto 0);
      timeoutCnt     : slv(31 downto 0);
      clearFifos     : sl;
      error          : sl;
      wordCnt        : slv(31 downto 0);
      adcData        : Slv16Array(19 downto 0);
      mAxisMaster    : AxiStreamMasterType;
      state          : StateType;
   end record;
   constant REG_INIT_C : RegType := (
      '0',
      '0',
      '0',
      (others => '0'),
      (others => '0'),
      (others => '0'),
      '0',
      '0',
      (others => '0'),
      (others => (others => '0')),      
      AXI_STREAM_MASTER_INIT_C,
      IDLE_S
   );
   
   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
   
   signal memRst         : sl := '0';
   signal dataSendEdge   : sl;
   signal acqStartEdge   : sl;
   signal adcMemWrEn     : slv(15 downto 0);
   signal adcMemRdOrder  : std_logic_vector(15 downto 0);
   signal adcMemRdRdy    : slv(15 downto 0);
   signal adcMemRdValid  : slv(15 downto 0);
   signal adcMemOflow    : slv(15 downto 0);
   signal adcMemOflowAny : std_logic;
   signal adcMemRdData   : Slv16Array(15 downto 0);

   signal adcCntEn       : sl;
   signal adcCntRst      : sl;
   signal adcCnt         : slv(11 downto 0);
   
   signal adcFifoWrEn    : slv(15 downto 0);
   signal adcFifoEmpty   : slv(15 downto 0);
   signal adcFifoOflow   : slv(15 downto 0);
   signal adcFifoRdValid : slv(15 downto 0);
   signal adcFifoRdEn    : slv(15 downto 0);
   signal adcFifoRdData  : Slv32Array(15 downto 0);
   signal adcFifoWrData  : Slv16Array(15 downto 0);
   signal fifoOflowAny   : sl := '0';
   signal fifoEmptyAll   : sl := '0';
   signal intSeqCount    : slv(31 downto 0) := (others => '0');

   signal adcDataToReorder : Slv16Array(19 downto 0);
   signal tpsData          : Slv16Array(3 downto 0);

   type chanMap is array(15 downto 0) of integer range 0 to 15;
   signal channelOrder   : chanMap;
   signal doutOrder      : chanMap;
   signal asicOrder      : chanMap;
   signal channelValid   : slv(15 downto 0);

   signal tpsAdcData     : Slv16Array(3 downto 0);

   attribute dont_touch : string;
   attribute dont_touch of r : signal is "true";
   
   attribute keep : string;
   attribute keep of fifoEmptyAll : signal is "true";
   attribute keep of r : signal is "true";
   attribute keep of adcFifoRdValid : signal is "true";
   attribute keep of adcFifoRdEn : signal is "true";
   
   
begin

   -- Counter output to register control
   seqCount <= intSeqCount;
   -- Channel Order for ASIC readout (last downto first)
   -- Readout order based on ePix100 ASIC numbering scheme (0 - forward, 1 - backward)
   -- Indexing for the memory readout order is linked to the raw ADC channel
   -- (i.e., if the channel reads out an ASIC from upper half of carrier,
   --  read it backward, otherwise, read it forward)
   G_EPIX100A_CARRIER_ADC_GEN2 : if (ASIC_TYPE_G = EPIX100A_C or ASIC_TYPE_G = EPIX10KA_C) generate
   
      -- EPIX100A and EPIX10KA Carrier Board View:
      --                             TOP
      --     B3    B2    B1    B0     |     B3    B2    B1    B0     
      --                              |
      --                              |
      --                              |
      --           ASIC2              |           ASIC1 
      --                              |
      --                              |
      --                              |
      --------------------------------------------------------------
      --                              |
      --                              |
      --                              |
      --           ASIC3              |           ASIC0 
      --                              |
      --                              |
      --                              |
      --     B0    B1    B2    B3     |     B0    B1    B2    B3     
      --
      -- ADC Channel Mappping for EPIX100A and EPIX10KA GEN2 ADC Board:
      -- 10:'ASIC0_B0',   2:'ASIC0_B1',   1:'ASIC0_B2',   0:'ASIC0_B3'
      --  8:'ASIC1_B0',   9:'ASIC1_B1',   3:'ASIC1_B2',   4:'ASIC1_B3'
      --  5:'ASIC2_B0',   6:'ASIC2_B1',   7:'ASIC2_B2',  15:'ASIC2_B3'
      -- 14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3'
      -- 17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'
      
      -- ADC channel mapping. See above.
      channelOrder <= (8,9,3,4,5,6,7,15,0,1,2,10,11,12,13,14);
      -- readout order per ADC channel (0 - forward, 1 - backward)
      adcMemRdOrder <= "1000001111111000";
      -- used for ADC Pipeline Delay per ASIC
      asicOrder <= (2,3,3,3,3,0,1,1,2,2,2,1,1,0,0,0);
      -- valid only for EPIX10KA_C
      -- see DoutDeserializer for dout mapping
      doutOrder <= (4,5,6,7,8,9,10,11,3,2,1,0,15,14,13,12);
      -- all 16 channels used
      channelValid  <= (others => '1');
      -- TPS ADC channnels mapping. See above.
      tpsData(0) <= r.adcData(17);
      tpsData(1) <= r.adcData(19);
      tpsData(2) <= r.adcData(18);
      tpsData(3) <= r.adcData(16);
   end generate;
   G_EPIX10KP_CARRIER_ADC_GEN2 : if (ASIC_TYPE_G = EPIX10KP_C) generate
      
      -- digital outputs are no longer supported for the EPIX10KP_C
      
      channelOrder <= (1,2,0,10,5,7,15, 6,9,4,3,8,10,11,13,12);
      channelValid  <= (others => '1');
      adcMemRdOrder <= "1100010010100111";
      tpsData(0) <= r.adcData(16);
      tpsData(1) <= r.adcData(17);
      tpsData(2) <= r.adcData(18);
      tpsData(3) <= r.adcData(19);
   end generate;
   G_EPIXS_CARRIER_ADC_GEN2 : if (ASIC_TYPE_G = EPIXS_C) generate
      channelOrder <= (4,5,6,7,8,9,10,11,3,2,1,0,15,14,13,12);
      channelValid  <= "1000100000010001";
      adcMemRdOrder <= x"0FF0";
      tpsData(0) <= r.adcData(16);
      tpsData(1) <= r.adcData(17);
      tpsData(2) <= r.adcData(18);
      tpsData(3) <= r.adcData(19);
   end generate;

   -- Edge detection for signals that interface with other blocks
   U_DataSendEdge : entity work.SynchronizerEdge
      port map (
         clk        => sysClk,
         rst        => sysClkRst,
         dataIn     => dataSend,
         risingEdge => dataSendEdge
      );
   U_ReadStartEdge : entity work.SynchronizerEdge
      port map (
         clk        => sysClk,
         rst        => sysClkRst,
         dataIn     => acqStart,
         risingEdge => acqStartEdge
      );

   --process(adcFifoRdValid,channelOrder, doutOrder,mAxisSlave,r, acqBusy) begin
   --   for i in 0 to 15 loop
   --      -- read ADC FIFOs
   --      if (r.state = READ_FIFO_S and i = channelOrder(conv_integer(r.chCnt)) and 
   --          adcFifoRdValid(i) = '1' and mAxisSlave.tReady = '1') then
   --         adcFifoRdEn(i) <= '1';
   --      else
   --         adcFifoRdEn(i) <= '0';
   --      end if;
   --      -- read dout FIFOs always with ADC FIFOs but in different order
   --      -- no validity check on dout FIFOs
   --      if (r.state = READ_FIFO_S and i = doutOrder(conv_integer(r.chCnt)) and 
   --          adcFifoRdValid(i) = '1' and mAxisSlave.tReady = '1') then
   --         doutRd(i) <= '1';
   --      else
   --         doutRd(i) <= '0';
   --      end if;
   --      
   --   end loop;
   --end process;
   
   
   
   
   --------------------------------------------------
   -- Simple state machine to just send ADC values --
   --------------------------------------------------
   comb : process (r,epixConfig,acqCount,intSeqCount,adcFifoRdData,adcFifoRdValid,doutValid,
                   channelOrder,doutOrder,fifoEmptyAll,acqBusy,adcMemOflowAny,fifoOflowAny,
                   envData,tpsAdcData,acqStartEdge,dataSendEdge,adcFifoEmpty,
                   sysClkRst,mAxisSlave, adcData, channelValid, opCode,
                   doutOut, tagIn) 
      variable v : RegType;
   begin
      v := r;

      -- Reset pulsed signals
      ssiResetFlags(v.mAxisMaster);
      v.mAxisMaster.tData := (others => '0');
      v.seqCountEn := '0';
      
      adcFifoRdEn <= (others=>'0');
      doutRd      <= (others=>'0');

      -- Always grab latest adc data
      for i in 0 to 19 loop
         v.adcData(i) := adcData(i);
      end loop;
      
      -- Latch overflows (this is reset in IDLE state)
      if (fifoOflowAny = '1' or adcMemOflowAny = '1') then
         v.error := '1';
      end if;
      
      -- State outputs
      if mAxisSlave.tReady = '1' then      
         case (r.state) is
            when IDLE_S =>
               v.wordCnt     := (others => '0');
               v.chCnt       := (others => '0');
               v.fillCnt     := (others => '0');
               v.timeoutCnt  := (others => '0');
               v.clearFifos  := '1';
               v.readDone    := '1';
               v.testPattern := epixConfig.testPattern;
               v.error       := '0';
               if acqStartEdge = '1' then
                  v.state := ARMED_S;
               end if;
            when ARMED_S =>
               v.readDone   := '0';
               v.clearFifos := '0';
               v.timeoutCnt := r.timeoutCnt + 1;
               if dataSendEdge = '1' then
                  v.seqCountEn := '1';
                  v.state      := HEADER_S;
               elsif (r.timeoutCnt >= DAQ_TIMEOUT_C) then
                  v.state := IDLE_S;
               end if;
            when HEADER_S =>
               v.wordCnt            := r.wordCnt + 1;
               v.mAxisMaster.tValid := '1';

               case conv_integer(r.wordCnt) is
                  when 0 => v.mAxisMaster.tData(31 downto 0) := x"000000" & "00" & LANE_C & "00" & VC_C;
                            ssiSetUserSof(MASTER_AXI_STREAM_CONFIG_G, v.mAxisMaster, '1');
                  when 1 => v.mAxisMaster.tData(31 downto 0) := x"0" & "00" & QUAD_C & opCode & acqCount(15 downto 0);
                  when 2 => v.mAxisMaster.tData(31 downto 0) := intSeqCount;
                  when 3 => v.mAxisMaster.tData(31 downto 0) := ZEROWORD_C;
                  when 4 => v.mAxisMaster.tData(31 downto 0) := ZEROWORD_C;
                  when 5 => v.mAxisMaster.tData(31 downto 0) := ZEROWORD_C;
                  when 6 => v.mAxisMaster.tData(31 downto 0) := ZEROWORD_C;
                  when 7 => v.mAxisMaster.tData(31 downto 0) := ZEROWORD_C;
                  when others => v.mAxisMaster.tData(31 downto 0) := ZEROWORD_C;
               end case;
               if (r.wordCnt = 7) then
                  v.wordCnt := (others => '0');
                  v.state := READ_FIFO_S;
               end if;
            when READ_FIFO_S => 
               -- read from ADC FIFOs and from Dout FIFOs (valid for EPIX10KA_C)
               v.mAxisMaster.tData(31 downto 0) := 
                  '0' & doutOut(doutOrder(conv_integer(r.chCnt)))(1) &
                  adcFifoRdData(channelOrder(conv_integer(r.chCnt)))(29 downto 16) & 
                  '0' & doutOut(doutOrder(conv_integer(r.chCnt)))(0) &
                  adcFifoRdData(channelOrder(conv_integer(r.chCnt)))(13 downto 0);
               
               --if adcFifoRdValid(channelOrder(conv_integer(r.chCnt))) = '1' then
               if adcFifoRdValid(channelOrder(conv_integer(r.chCnt))) = '1' and doutValid(doutOrder(conv_integer(r.chCnt))) = '1' then
                  
                  adcFifoRdEn(channelOrder(conv_integer(r.chCnt))) <= '1';
                  doutRd(doutOrder(conv_integer(r.chCnt))) <= '1';
                  
                  if (channelValid(conv_integer(r.chCnt)) = '1') then
                     v.mAxisMaster.tValid := '1';
                  end if;
                  v.fillCnt         := r.fillCnt + 1;
                  if (r.fillCnt = conv_std_logic_vector(NCOL_C/2-1,r.fillCnt'length)) then
                     v.chCnt   := r.chCnt + 1;
                     v.fillCnt := (others => '0');
                  end if;
               else
                  v.timeoutCnt := r.timeoutCnt + 1;
               end if;
               if acqBusy = '0' and fifoEmptyAll = '1' then
                  v.state := ENV_DATA_S;
               elsif r.error = '1' or r.timeoutCnt = STUCK_TIMEOUT_C then
                  v.state := FOOTER_S;
               end if;
            when ENV_DATA_S =>
               v.wordCnt         := r.wordCnt + 1;
               v.mAxisMaster.tValid := '1';
               if (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(0);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+1,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(1);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+2,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(2);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+3,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(3);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+4,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(4);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+5,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(5);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+6,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(6);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+7,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(7);
               elsif (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C+8,r.wordCnt'length)) then
                  v.mAxisMaster.tData(31 downto 0) := envData(8);
               else
                  v.mAxisMaster.tData(31 downto 0) := ZEROWORD_C;
               end if;
               if (r.wordCnt = conv_std_logic_vector(WORDS_PER_SUPER_ROW_C*2-1,r.wordCnt'length)) then
                  v.wordCnt := (others => '0');
                  v.state   := TPS_DATA_S;
               end if;
            when TPS_DATA_S =>
               v.wordCnt         := r.wordCnt + 1;
               v.mAxisMaster.tValid := '1';
               if (r.wordCnt = 0) then
                  v.mAxisMaster.tData(31 downto 0) := tpsAdcData(1) & tpsAdcData(0);
               elsif (r.wordCnt = 1) then
                  v.mAxisMaster.tData(31 downto 0) := tpsAdcData(3) & tpsAdcData(2);            
               end if;
               if (r.wordCnt = 1) then
                  v.state := FOOTER_S;
               end if;
            when FOOTER_S =>
               ssiSetUserEofe(MASTER_AXI_STREAM_CONFIG_G,v.mAxisMaster,r.error);
               v.readDone                       := '1';
               v.mAxisMaster.tData(31 downto 0) := x"0000000" & "000" & tagIn;
               v.mAxisMaster.tValid             := '1';
               v.mAxisMaster.tLast              := '1';
               v.state                          := IDLE_S;
         end case;
      end if;
 
      -- Synchronous Reset
      if sysClkRst = '1' then
         v := REG_INIT_C;
      end if;

      -- Register the variable for next clock cycle
      rin <= v;
      
      -- Outputs from block
      readDone    <= r.readDone;
      mAxisMaster <= r.mAxisMaster;
      mpsOut      <= '0';
      
   end process comb;
 
 
   seq : process (sysClk) is
   begin
      if rising_edge(sysClk) then
         r <= rin after TPD_G;
      end if;
   end process seq;
 

   --Count number of ADC writes
   adcCntEn  <= readValidA0 and adcPulse;
   adcCntRst <= memRst or sysClkRst;
   process(sysClk) begin
      if rising_edge(sysClk) then
         if (sysClkRst = '1' or adcCntRst = '1') then
            adcCnt <= (others => '0') after TPD_G;
         elsif adcCntEn = '1' then
            adcCnt <= adcCnt + 1 after TPD_G;
         end if;
      end if;
   end process;
   --Register the TPS ADC data when readTps is high
   process(sysClk) 
   begin
      if rising_edge(sysClk) then
         for i in 0 to 3 loop
            if readTps = '1' then
               tpsAdcData(i) <= tpsData(i);
            end if;
         end loop;
      end if;
   end process;
   --Sequence/frame counter
   process ( sysClk, sysClkRst ) begin
      if ( sysClkRst = '1' ) then
         intSeqCount <= (others => '0');
      elsif rising_edge(sysClk) then
         if epixConfig.seqCountReset = '1' then
            intSeqCount <= (others => '0') after TPD_G;
         elsif r.seqCountEn = '1' then
            intSeqCount <= intSeqCount + 1 after TPD_G;
          end if;
      end if;
   end process;

   --Simple logic to choose which memory to read from
   process(sysClk) begin
      if rising_edge(sysClk) then
         for i in 0 to 15 loop
            adcFifoWrEn(i)   <= adcMemRdValid(i);
            if r.testPattern = '0' then
               adcFifoWrData(i) <= adcMemRdData(i);
            else
               adcFifoWrData(i) <= "0000" & conv_std_logic_vector(i,4) & adcMemRdData(i)(7 downto 0);
            end if;
         end loop;
      end if;
   end process;

   --Blockrams to reorder data
   --Memory and fifos are reset on system reset or on IDLE state
   memRst <= r.clearFifos or sysClkRst;
   --Generate logic
   G_RowBuffers : for i in 0 to 15 generate
      process(sysClk) begin
         if rising_edge(sysClk) then
            if (adcValid(i) = '1') then
               adcDataToReorder(i) <= "00" & r.adcData(i)(13 downto 0);
            end if;
         end if;
      end process;
 
      --Write when the ADC block says data is good AND when AcqControl agrees
      process(sysClk) begin
         if rising_edge(sysClk) then
            if asicOrder(i) = 0  then
               adcMemWrEn(i) <= readValidA0 and adcPulse;
            elsif asicOrder(i) = 1 then
               adcMemWrEn(i) <= readValidA1 and adcPulse;
            elsif asicOrder(i) = 2 then
               adcMemWrEn(i) <= readValidA2 and adcPulse;
            else
               adcMemWrEn(i) <= readValidA3 and adcPulse;
            end if;                  
         end if;
      end process;

      --Instantiate memory
      U_RowBuffer : entity work.EpixRowBlockRam
      generic map (
         TPD_G        => TPD_G,
         ASIC_TYPE_G  => ASIC_TYPE_G)
      port map (
         sysClk      => sysClk,
         sysClkRst   => sysClkRst,
         wrReset     => r.clearFifos,
         wrData      => adcDataToReorder(i),
         wrEn        => adcMemWrEn(i),
         rdOrder     => adcMemRdOrder(i),
         rdReady     => adcMemRdRdy(i),
         rdStart     => adcMemRdRdy(i),
         overflow    => adcMemOflow(i),
         rdData      => adcMemRdData(i),
         dataValid   => adcMemRdValid(i),
         testPattern => r.testPattern
      );
      
   end generate;
   --Or of all memory overflow bits
   process(sysClk) 
      variable runningOr : std_logic := '0';
   begin
      if rising_edge(sysClk) then
         runningOr := '0';
         for i in 0 to 15 loop
            runningOr := runningOr or adcMemOflow(i);
         end loop;
         adcMemOflowAny <= runningOr;
      end if;
   end process;
   
   -- Instantiate FIFOs
   G_AdcFifos : for i in 0 to 15 generate
      --Instantiate the FIFOs
      U_AdcFifo : entity work.FifoMux
         generic map(
            WR_DATA_WIDTH_G => 16,
            RD_DATA_WIDTH_G => 32,
            GEN_SYNC_FIFO_G => true,
            ADDR_WIDTH_G    => CH_FIFO_ADDR_WIDTH_C,
            FWFT_EN_G       => true,
            USE_BUILT_IN_G  => false,
            EMPTY_THRES_G   => 1,
            LITTLE_ENDIAN_G => true
         )
         port map(
            rst           => memRst,
            --Write ports
            wr_clk        => sysClk,
            wr_en         => adcFifoWrEn(i),
            din           => adcFifoWrData(i),
            overflow      => adcFifoOflow(i),
            --Read ports
            rd_clk        => sysClk,
            rd_en         => adcFifoRdEn(i),
            dout          => adcFifoRdData(i),
            valid         => adcFifoRdValid(i),
            empty         => adcFifoEmpty(i)
         );
   end generate;
   --Or of all fifo overflow bits
   --And of all fifo empty bits
   PROC_FIFO_LOGIC : process(sysClk) 
      variable runningOr : std_logic := '0';
      variable runningAnd : std_logic := '0';
   begin
      if rising_edge(sysClk) then
         runningOr := '0';
         runningAnd := '1';
         for i in 0 to 15 loop
            runningOr := runningOr or adcFifoOflow(i);
            runningAnd := runningAnd and adcFifoEmpty(i);
         end loop;
         fifoOflowAny <= runningOr;
         fifoEmptyAll <= runningAnd;
      end if;
   end process;
   
   -- use as dout roClk skew setting for dout deserializer
   -- epixConfig.doutPipelineDelay(6 downto 0)
   
end ReadoutControl;

