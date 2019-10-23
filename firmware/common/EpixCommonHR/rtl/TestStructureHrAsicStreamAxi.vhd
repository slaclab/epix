-------------------------------------------------------------------------------
-- Title         : AsicStreamAxi
-- Project       : Tixel Detector
-------------------------------------------------------------------------------
-- File          : TestStructureHrAsicStreamAxi.vhd
-- Created       : 8/27/2017
-------------------------------------------------------------------------------
-- Description:
-------------------------------------------------------------------------------
-- This file is part of 'Tixel Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------
-- Modification history:
-- 8/27/2017: created.
-------------------------------------------------------------------------------

LIBRARY ieee;
use work.all;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;
use work.StdRtlPkg.all;
use work.AxiLitePkg.all;
use work.AxiStreamPkg.all;
use work.SsiPkg.all;

entity TestStructureHrAsicStreamAxi is 
   generic (
      TPD_G           	: time := 1 ns;
      VC_NO_G           : slv(3 downto 0)  := "0000";
      LANE_NO_G         : slv(3 downto 0)  := "0000";
      ASIC_NO_G         : slv(2 downto 0)  := "000";
      ASIC_DATA_G       : natural := (32*32)-1; --workds
      AXIL_ERR_RESP_G   : slv(1 downto 0)  := AXI_RESP_DECERR_C
   );
   port ( 
      -- Deserialized data port
      rxClk             : in  sl;
      rxRst             : in  sl;
      rxData            : in  slv(15 downto 0);
      rxValid           : in  sl;
      
      -- AXI lite slave port for register access
      axilClk           : in  sl;
      axilRst           : in  sl;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType;
      
      -- AXI data stream output
      axisClk           : in  sl;
      axisRst           : in  sl;
      mAxisMaster       : out AxiStreamMasterType;
      mAxisSlave        : in  AxiStreamSlaveType;
      
      -- acquisition number input to the header
      acqNo             : in  slv(31 downto 0);
      
      -- optional readout trigger for test mode
      testTrig          : in  sl := '0';
      -- optional inhibit counting errors 
      -- workaround to tixel bug dropping link after R0
      -- affects only SOF error counter
      errInhibit        : in  sl := '0'
      
   );
end TestStructureHrAsicStreamAxi;


-- Define architecture
architecture RTL of TestStructureHrAsicStreamAxi is

   constant AXI_STREAM_CONFIG_I_C : AxiStreamConfigType   := ssiAxiStreamConfig(2, TKEEP_COMP_C);
   constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
   constant TOA_C : natural := 1;
   
   type StateType is (IDLE_S, HDR_S, DATA_S);
   
   type StrType is record
      state          : StateType;
      stCnt          : natural;
      testColCnt     : natural;
      testRowCnt     : natural;
      testTrig       : slv(2 downto 0);
      testMode       : sl;
      testBitFlip    : sl;
      frmSize        : slv(15 downto 0);
      frmMax         : slv(15 downto 0);
      frmMin         : slv(15 downto 0);
      acqNo          : Slv32Array(1 downto 0);
      frmCnt         : slv(31 downto 0);
      sofError       : slv(15 downto 0);
      eofError       : slv(15 downto 0);
      ovError        : slv(15 downto 0);
      rstCnt         : sl;
      errInhibit     : sl;
      dFifoRd        : sl;
      tReady         : sl;
      axisMaster     : AxiStreamMasterType;
   end record;

   constant STR_INIT_C : StrType := (
      state          => IDLE_S,
      stCnt          => 0,
      testColCnt     => 0,
      testRowCnt     => 0,
      testTrig       => "000",
      testMode       => '0',
      testBitFlip    => '0',
      frmSize        => (others=>'0'),
      frmMax         => (others=>'0'),
      frmMin         => (others=>'1'),
      acqNo          => (others=>(others=>'0')),
      frmCnt         => (others=>'0'),
      sofError       => (others=>'0'),
      eofError       => (others=>'0'),
      ovError        => (others=>'0'),
      rstCnt         => '0',
      errInhibit     => '0',
      dFifoRd        => '0',
      tReady         => '0',
      axisMaster     => AXI_STREAM_MASTER_INIT_C
   );
   
   type RegType is record
      testMode          : sl;
      frmSize           : slv(15 downto 0);
      frmMax            : slv(15 downto 0);
      frmMin            : slv(15 downto 0);
      frmCnt            : slv(31 downto 0);
      sofError          : slv(15 downto 0);
      eofError          : slv(15 downto 0);
      ovError           : slv(15 downto 0);
      rstCnt            : slv(2 downto 0);
      frmExpSize        : slv(15 downto 0);
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
      tsMode            : slv(2 downto 0);
   end record RegType;

   constant REG_INIT_C : RegType := (
      testMode          => '0',
      frmSize           => (others=>'0'),
      frmMax            => (others=>'0'),
      frmMin            => (others=>'0'),
      frmCnt            => (others=>'0'),
      sofError          => (others=>'0'),
      eofError          => (others=>'0'),
      ovError           => (others=>'0'),
      rstCnt            => (others=>'0'),
      frmExpSize        => toSlv(ASIC_DATA_G, 16),
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C,
      tsMode            => (others=>'0')
   );
   
   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
   signal s   : StrType := STR_INIT_C;
   signal sin : StrType;
   
   signal decDataOut    : slv(15 downto 0);
   signal decValid      : sl;
   signal decSof        : sl;
   signal decEof        : sl;
   signal decEofe       : sl;
   
   signal dFifoRd       : sl;
   signal dFifoEofe     : sl;
   signal dFifoEof      : sl;
   signal dFifoSof      : sl;
   signal dFifoValid    : sl;
   signal dFifoOut      : slv(15 downto 0);
   
   signal sAxisMaster : AxiStreamMasterType;
   signal sAxisSlave  : AxiStreamSlaveType;
   
   signal testModeSync  : sl;
   signal iRxValid      : sl;
   
   signal rxDataCs   : slv(15 downto 0);                 -- for chipscope
   signal rxValidCs  : sl;                               -- for chipscope
   attribute keep : string;                              -- for chipscope
   attribute keep of s : signal is "true";               -- for chipscope
   attribute keep of dFifoOut : signal is "true";        -- for chipscope
   attribute keep of dFifoSof : signal is "true";        -- for chipscope
   attribute keep of dFifoEof : signal is "true";        -- for chipscope
   attribute keep of dFifoEofe : signal is "true";       -- for chipscope
   attribute keep of dFifoValid : signal is "true";      -- for chipscope
   attribute keep of rxDataCs : signal is "true";        -- for chipscope
   attribute keep of rxValidCs : signal is "true";       -- for chipscope

begin
   
   rxDataCs <= rxData;     -- for chipscope
   rxValidCs <= rxValid;   -- for chipscope
   
   -- synchronizers
   Sync1_U : entity work.Synchronizer
   port map (
      clk     => rxClk,
      rst     => rxRst,
      dataIn  => s.testMode,
      dataOut => testModeSync
   );   
   

    -- test structure data decoder
   DecTSMode_U : entity work.TSDecoderMode
   generic map (
      RST_POLARITY_G => '1'
   )
   port map (
      clk         => rxClk,
      rst         => rxRst,
      dataIn      => rxData,
      validIn     => iRxValid,
      modeIn      => r.tsMode,
      dataOut     => decDataOut,
      validOut    => decValid,
      sof         => decSof,
      eof         => decEof,
      eofe        => decEofe
   );
   
-- disable decoder in test mode (fake ASIC data)
   iRxValid <= rxValid and not testModeSync;
   
   -- async fifo for data
   -- for synchronization and small data pipeline
   -- not to store the whole frame
   DataFifo_U : entity work.FifoCascade
   generic map (
      GEN_SYNC_FIFO_G   => false,
      FWFT_EN_G         => true,
      ADDR_WIDTH_G      => 4,
      DATA_WIDTH_G      => 19
   )
   port map (
      -- Resets
      rst               => rxRst,
      wr_clk            => rxClk,
      wr_en             => decValid,
      din(15 downto 0)  => decDataOut,
      din(16)           => decEofe,
      din(17)           => decEof,
      din(18)           => decSof,
      --Read Ports (rd_clk domain)
      rd_clk            => axisClk,
      rd_en             => dFifoRd,
      dout(15 downto 0) => dFifoOut,
      dout(16)          => dFifoEofe,
      dout(17)          => dFifoEof,
      dout(18)          => dFifoSof,
      valid             => dFifoValid
   );
   
   -- axi stream fifo
   -- must be able to store whole frame if AXIS is muxed
   AxisFifo_U: entity work.AxiStreamFifo
   generic map(
      GEN_SYNC_FIFO_G      => false,
      FIFO_ADDR_WIDTH_G    => 13,
      SLAVE_AXI_CONFIG_G   => AXI_STREAM_CONFIG_I_C,
      MASTER_AXI_CONFIG_G  => AXI_STREAM_CONFIG_O_C
   )
   port map(
      sAxisClk    => axisClk,
      sAxisRst    => axisRst,
      sAxisMaster => sAxisMaster,
      sAxisSlave  => sAxisSlave,
      mAxisClk    => axisClk,
      mAxisRst    => axisRst,
      mAxisMaster => mAxisMaster,
      mAxisSlave  => mAxisSlave
   );


   comb : process (axilRst, axisRst, sAxilReadMaster, sAxilWriteMaster, sAxisSlave, r, s, 
      acqNo, dFifoOut, dFifoValid, dFifoSof, dFifoEof, dFifoEofe, testTrig, errInhibit) is
      variable sv       : StrType;
      variable rv       : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      rv := r;    -- r is in AXI lite clock domain
      sv := s;    -- s is in AXI stream clock domain
      sv.dFifoRd := '0';
      sv.axisMaster := AXI_STREAM_MASTER_INIT_C;
      sv.testTrig(0) := testTrig;
      sv.testTrig(1) := s.testTrig(0);
      sv.testTrig(2) := s.testTrig(1);
      sv.errInhibit := errInhibit;
      
      -- cross clock sync
      
      rv.frmSize := s.frmSize;
      rv.frmMax  := s.frmMax;
      rv.frmMin  := s.frmMin;
      rv.frmCnt   := s.frmCnt;
      rv.sofError := s.sofError;
      rv.eofError := s.eofError;
      rv.ovError  := s.ovError;
      sv.testMode := r.testMode;
      if r.rstCnt /= "000" then
         sv.rstCnt := '1';
      else
         sv.rstCnt := '0';
      end if;
      
      -- axi lite logic 
      rv.rstCnt := r.rstCnt(1 downto 0) & '0';
      rv.sAxilReadSlave.rdata := (others => '0');
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, rv.sAxilWriteSlave, rv.sAxilReadSlave);
      
      axiSlaveRegisterR(regCon, x"00", 0, r.frmCnt);
      axiSlaveRegisterR(regCon, x"04", 0, r.frmSize);
      axiSlaveRegisterR(regCon, x"08", 0, r.frmMax);
      axiSlaveRegisterR(regCon, x"0C", 0, r.frmMin);
      axiSlaveRegisterR(regCon, x"10", 0, r.sofError);
      axiSlaveRegisterR(regCon, x"14", 0, r.eofError);
      axiSlaveRegisterR(regCon, x"18", 0, r.ovError);
      axiSlaveRegister (regCon, x"1C", 0, rv.testMode);
      axiSlaveRegister (regCon, x"20", 0, rv.rstCnt);
      axiSlaveRegister (regCon, x"24", 0, rv.frmExpSize);
      axiSlaveRegister (regCon, x"28", 0, rv.tsMode);
      axiSlaveDefault(regCon, rv.sAxilWriteSlave, rv.sAxilReadSlave, AXIL_ERR_RESP_G);
      
      -- axi stream logic
      
      -- sync acquisition number
      sv.acqNo(0) := acqNo;
      
      -- report an error when sAxisSlave.tReady is dropped (overflow)
      sv.tReady := sAxisSlave.tReady;
      if sAxisSlave.tReady = '0' and s.tReady = '1' then
         sv.ovError := s.ovError + 1;
      end if;
      
      case s.state is
         when IDLE_S =>
            if (dFifoValid = '1' ) or (s.testMode = '1' and s.testTrig(1) = '1' and s.testTrig(2) = '0') then
               -- start sending the header
               -- do not read the fifo yet
               sv.acqNo(1) := s.acqNo(0);
               sv.state := HDR_S;
               sv.testBitFlip := '0';
               sv.testColCnt := 0;
               sv.testRowCnt := 0;
               sv.stCnt := 0;
            end if;
         
         -- header is 6 x 16 bit words
         when HDR_S =>
            sv.axisMaster.tValid := '1';
            if s.stCnt = 5 then
               sv.stCnt := 0;
               sv.state := DATA_S;
            else
               sv.stCnt := s.stCnt + 1;
            end if;
            if s.stCnt = 0 then
               sv.axisMaster.tData(15 downto 0) := x"00" & LANE_NO_G & VC_NO_G;
               ssiSetUserSof(AXI_STREAM_CONFIG_I_C, sv.axisMaster, '1');
            elsif s.stCnt = 1 then
               sv.axisMaster.tData(15 downto 0) := x"0000";
            elsif s.stCnt = 2 then
               sv.axisMaster.tData(15 downto 0) := s.acqNo(1)(15 downto 0);
            elsif s.stCnt = 3 then
               sv.axisMaster.tData(15 downto 0) := s.acqNo(1)(31 downto 16);
            elsif s.stCnt = 4 then
               if s.testMode = '0' then
                  sv.axisMaster.tData(15 downto 0) := x"000" & '0' & ASIC_NO_G;
               else
                  sv.axisMaster.tData(15 downto 0) := x"000" & '0' & ASIC_NO_G;
               end if;
            else
               sv.axisMaster.tData(15 downto 0) := x"0000";
            end if;
         
         when DATA_S =>
            if dFifoValid = '1' or s.testMode = '1' then
               
               -- test mode row and col counters
               if s.testColCnt < 31 then
                  sv.testColCnt := s.testColCnt + 1;
               else
                  sv.testColCnt := 0;
                  sv.testRowCnt := s.testRowCnt + 1;
               end if;
               
               -- test or real data readout
               sv.axisMaster.tValid := '1';
               if s.testMode = '0' then
                  sv.axisMaster.tData(15 downto 0) := dFifoOut;
               else
               -- there is no sof and eof on test structure so test mode is being used to send the real data. Normal mode will never produce data for this structure.
                  if s.testColCnt = 15 then
                     sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & s.acqNo(1)(4 downto 0) & "00" & toSlv(s.testRowCnt, 6);
                  elsif s.testRowCnt = 15 then
                     sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & s.acqNo(1)(4 downto 0) & "00" & toSlv(s.testColCnt, 6);
                  else
                     sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & "00000" & x"ff";
                  end if;
               end if;
               sv.dFifoRd := '1';
               sv.stCnt := s.stCnt + 1;
               if s.stCnt = r.frmExpSize then 
                  sv.frmSize := toSlv(s.stCnt, 16);
                  sv.stCnt := 0;
                  if s.frmMax <= sv.frmSize then
                     sv.frmMax := sv.frmSize;
                  end if;
                  if s.frmMin >= sv.frmSize then
                     sv.frmMin := sv.frmSize;
                  end if;
                  if dFifoEofe = '1' then
                     sv.eofError := s.eofError + 1;
                  end if;
                  sv.frmCnt := s.frmCnt + 1;
                  sv.axisMaster.tLast := '1';
                  sv.state := IDLE_S;
               end if;               
            end if;
         
         when others =>
      end case;
      
      -- reset counters
      if s.rstCnt = '1' then
         sv.frmCnt   := (others=>'0');
         sv.frmSize  := (others=>'0');
         sv.frmMax   := (others=>'0');
         sv.frmMin   := (others=>'1');
         sv.eofError := (others=>'0');
         sv.sofError := (others=>'0');
         sv.ovError  := (others=>'0');
         sv.state    := IDLE_S;         -- if SM is in odd state, puts it back
                                        -- to idle
      end if;
      
      -- reset logic
      
      if (axilRst = '1') then
         rv := REG_INIT_C;
      end if;
      if (axisRst = '1') then
         sv := STR_INIT_C;
      end if;

      -- outputs
      
      rin <= rv;
      sin <= sv;

      sAxilWriteSlave   <= r.sAxilWriteSlave;
      sAxilReadSlave    <= r.sAxilReadSlave;
      sAxisMaster       <= s.axisMaster;
      dFifoRd           <= sv.dFifoRd;

   end process comb;

   rseq : process (axilClk) is
   begin
      if (rising_edge(axilClk)) then
         r <= rin after TPD_G;
      end if;
   end process rseq;
   
   sseq : process (axisClk) is
   begin
      if (rising_edge(axisClk)) then
         s <= sin after TPD_G;
      end if;
   end process sseq;
   

end RTL;

