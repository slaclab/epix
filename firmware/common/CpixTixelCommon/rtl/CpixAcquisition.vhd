-------------------------------------------------------------------------------
-- Title      : Cpix detector acquisition control
-------------------------------------------------------------------------------
-- File       : CpixAcquisition.vhd
-- Author     : Maciej Kwiatkowski <mkwiatko@slac.stanford.edu>
-- Company    : SLAC National Accelerator Laboratory
-- Created    : 01/19/2016
-- Last update: 01/19/2016
-- Platform   : Vivado 2014.4
-- Standard   : VHDL'93/02
-------------------------------------------------------------------------------
-- Description: 
-------------------------------------------------------------------------------
-- Copyright (c) 2015 SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
--


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.StdRtlPkg.all;
use work.EpixPkgGen2.all;
use work.CpixPkg.all;


library unisim;
use unisim.vcomponents.all;

entity CpixAcquisition is
   generic (
      TPD_G           : time := 1 ns;
      NUMBER_OF_ASICS : natural := 2
   );
   port (
   
      -- global signals
      sysClk          : in  std_logic;
      sysClkRst       : in  std_logic;

      -- control/status signals (byteClk)
      cntAcquisition  : out std_logic_vector(31 downto 0);
      cntSequence     : out std_logic_vector(31 downto 0);
      cntAReadout     : out std_logic;
      frameReq        : out std_logic;
      frameAck        : in  std_logic_vector(NUMBER_OF_ASICS-1 downto 0);
      headerAck       : in  std_logic_vector(NUMBER_OF_ASICS-1 downto 0);
      timeoutReq      : out std_logic;
      epixConfig      : in  EpixConfigType;
      cpixConfig      : in  CpixConfigType;
      saciReadoutReq  : out std_logic;
      saciReadoutAck  : in  std_logic;
      
      -- ASICs signals
      asicEnA         : out std_logic;
      asicEnB         : out std_logic;
      asicVid         : out std_logic;
      asicPPbe        : out std_logic;
      asicPpmat       : out std_logic;
      asicR0          : out std_logic;
      asicSRO         : out std_logic;
      asicGlblRst     : out std_logic;
      asicSync        : out std_logic;
      asicAcq         : out std_logic
      
   );
end CpixAcquisition;

architecture rtl of CpixAcquisition is
   
   TYPE STATE_TYPE IS (
      IDLE_S, 
      WAIT_R0_HIGH_S, 
      R0_HIGH_S, 
      ACQ_HIGH_S, 
      ACQ_LOW_S, 
      SRO_HIGH_S, 
      WAIT_READOUT_S, 
      SYNC_HIGH_S, 
      SACI_SYNC_S
   );
   signal state, next_state   : STATE_TYPE; 
   
   TYPE AB_STATE_TYPE IS (
      IDLE_S, 
      WAIT_ABEN_HIGH_S, 
      ABEN_HIGH_S
   );
   signal ab_state, ab_next_state   : AB_STATE_TYPE; 
   
   signal a2bCnt        : natural;
   signal a2bDlyCnt     : natural;
   signal a2bDlyRst     : std_logic;
   signal a2bRst        : std_logic;
   signal a2bCntEn      : std_logic;
   signal runsCnt       : natural;
   signal runsCntEn     : std_logic;
   signal runsCntRst    : std_logic;
   signal delayCnt      : natural;
   signal delayCntRst   : std_logic;
   constant sroDly      : natural := 1000;
   signal acqStartSys   : std_logic;
   signal startAbDly    : std_logic;
   
   signal iAsicR0       : std_logic;
   signal iAsicAcq      : std_logic;
   signal iAsicAcqD1    : std_logic;
   signal iAsicAcqD2    : std_logic;
   signal iAsicAcqD3    : std_logic;
   signal iAsicAcqD4    : std_logic;
   signal iAsicAcqD5    : std_logic;
   signal iAsicSync     : std_logic;
   signal syncMode      : std_logic_vector(1 downto 0);
   
   signal runToR0       : unsigned(31 downto 0);
   signal runToAcq      : unsigned(31 downto 0);
   signal r0ToAcq       : unsigned(31 downto 0);
   signal acqWidth      : unsigned(31 downto 0);
   signal syncWidth     : unsigned(31 downto 0);
   signal sROWidth      : unsigned(31 downto 0);
   signal nRuns         : unsigned(31 downto 0);
   
begin

   U_AcqStartSys : entity work.SynchronizerEdge
   port map (
      clk        => sysClk,
      rst        => sysClkRst,
      dataIn     => acqStart,
      risingEdge => acqStartSys
   );
   
   --MUXes for manual control of ASIC signals
   asicGlblRst <= 
      '1'                     when epixConfig.manualPinControl(0) = '0' else
      epixConfig.asicPins(0);
   asicAcq <= 
      iAsicAcq                when epixConfig.manualPinControl(1) = '0' else
      epixConfig.asicPins(1);
   asicR0 <=   
      iAsicR0                 when epixConfig.manualPinControl(2) = '0' else
      epixConfig.asicPins(2);
   asicPpmat <=
      '1'                     when epixConfig.manualPinControl(3) = '0' else
      epixConfig.asicPins(3);
   asicPPbe <= 
      '1'                     when epixConfig.manualPinControl(4) = '0' else
      epixConfig.asicPins(4);
   
   asicSync <= 
      iAsicSync               when cpixConfig.syncMode = "00" else      -- sync pin used as ASIC sync
      '0'                     when cpixConfig.syncMode = "01" else      -- saci command used as ASIC sync
      iAsicAcqD5              when cpixConfig.syncMode = "10" else      -- sync pin used to inject charge in test mode
      '0';
   
   --asicEnA <= cpixConfig.cpixCntAnotB(a2bCnt);
   --asicEnB <= not cpixConfig.cpixCntAnotB(a2bCnt);
   asicVid <= '0';
   
   asicEnA <= 
      cpixConfig.cpixCntAnotB(a2bCnt)     when cpixConfig.cpixAsicPinControl(5) = '0' else
      cpixConfig.cpixAsicPins(5);
   
   asicEnB <= 
      not cpixConfig.cpixCntAnotB(a2bCnt) when cpixConfig.cpixAsicPinControl(6) = '0' else
      cpixConfig.cpixAsicPins(6);
   
   
   fsm_seq_p: process ( sysClk ) 
   begin
      -- FSM state register
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            state <= IDLE_S               after TPD_G;
         else
            state <= next_state           after TPD_G;
         end if;
      end if;
      
      -- Generic delay counter
      if rising_edge(sysClk) then
         if delayCntRst = '1' then
            delayCnt <= 0                 after TPD_G;
         else
            delayCnt <= delayCnt + 1      after TPD_G;
         end if;
      end if;
      
      -- Generic iterations counter
      if rising_edge(sysClk) then
         if runsCntRst = '1' then
            runsCnt <= 0                  after TPD_G;
         elsif runsCntEn = '1' then
            runsCnt <= runsCnt + 1        after TPD_G;
         end if;
      end if;
      
      -- CPIX cntA/cntB swich delay counter
      if rising_edge(sysClk) then
         if a2bDlyRst = '1' then
            a2bDlyCnt <= to_integer(unsigned(cpixConfig.cpixAcqToCnt) - 1) after TPD_G;
         elsif a2bDlyCnt /= 0 then
            a2bDlyCnt <= a2bDlyCnt - 1    after TPD_G;
         end if;
      end if;
      
      -- CPIX cntA/cntB sequence select counter
      if rising_edge(sysClk) then
         if a2bRst = '1' then
            a2bCnt <= 0                   after TPD_G;
         elsif a2bCntEn = '1' then
            a2bCnt <= a2bCnt + 1          after TPD_G;
         end if;
      end if;
      
      -- 2nd FSM state register
      if rising_edge(sysClk) then
         if sysClkRst = '1' or a2bRst = '1' then
            ab_state <= IDLE_S            after TPD_G;
         else
            ab_state <= ab_next_state     after TPD_G;
         end if;
      end if;
      
      -- delayed asicAcq to be used as the pulser injection
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            iAsicAcqD1 <= '0'             after TPD_G;
            iAsicAcqD2 <= '0'             after TPD_G;
            iAsicAcqD3 <= '0'             after TPD_G;
            iAsicAcqD4 <= '0'             after TPD_G;
            iAsicAcqD5 <= '0'             after TPD_G;
         else
            iAsicAcqD1 <= iAsicAcq        after TPD_G;
            iAsicAcqD2 <= iAsicAcqD1      after TPD_G;
            iAsicAcqD3 <= iAsicAcqD2      after TPD_G;
            iAsicAcqD4 <= iAsicAcqD3      after TPD_G;
            iAsicAcqD5 <= iAsicAcqD4      after TPD_G;
         end if;
      end if;
      
   end process;
   
   runToR0 <= runToAcq - r0ToAcq when runToAcq >= r0ToAcq else (others=>'0');
   runToAcq <= unsigned(cpixConfig.cpixRunToAcq);
   r0ToAcq <= unsigned(cpixConfig.cpixR0ToAcq);
   acqWidth <= unsigned(cpixConfig.cpixAcqWidth);
   syncWidth <= unsigned(cpixConfig.cpixSyncWidth);
   sROWidth <= unsigned(cpixConfig.cpixSROWidth);
   nRuns <= unsigned(cpixConfig.cpixNRuns);
   syncMode <= cpixConfig.syncMode;

   fsm_cmb_p: process (
      state, acqStartSys, readPend, delayCnt, runsCnt,
      runToR0, r0ToAcq, acqWidth, syncMode,
      syncWidth, sROWidth, nRuns, saciReadoutAck
   ) 
   begin
      next_state <= state;
      delayCntRst <= '0';
      runsCntEn <= '0';
      runsCntRst <= '0';
      acqDone <= '0';
      asicSRO <= '0';
      iAsicR0 <= '0';
      iAsicAcq <= '0';
      iAsicSync <= '0';
      saciReadoutReq <= '0';
      startAbDly <= '0';
      a2bRst <= '0';
      readCntA <= '0';
      
      case state is
      
         when IDLE_S =>
            if acqStartSys = '1' then
               -- keep counting when not all acquisition runs are completed
               if runsCnt < nRuns then
                  runsCntEn <= '1';
                  delayCntRst <= '1';
                  next_state <= WAIT_R0_HIGH_S;
               -- start the readout if enabled
               elsif epixConfig.daqTriggerEnable = '1' then
                  runsCntRst <= '1';
                  delayCntRst <= '1';
                  a2bRst <= '1';
                  next_state <= SRO_HIGH_S;
               -- start runs otherwise
               else
                  runsCntRst <= '1';
                  delayCntRst <= '1';
                  next_state <= WAIT_R0_HIGH_S;
               end if;
            end if;
         
          when WAIT_R0_HIGH_S =>
            if delayCnt >= to_integer(runToR0) - 1 then
               delayCntRst <= '1';
               next_state <= R0_HIGH_S;
            end if;
         
         when R0_HIGH_S =>
            iAsicR0 <= '1';
            if delayCnt >= to_integer(r0ToAcq) - 1 then
               delayCntRst <= '1';
               startAbDly <= '1';
               next_state <= ACQ_HIGH_S;
            end if;
         
         when ACQ_HIGH_S =>
            iAsicR0 <= '1';
            iAsicAcq <= '1';
            if delayCnt >= to_integer(acqWidth) - 1 then
               next_state <= ACQ_LOW_S;
            end if;
         
         when ACQ_LOW_S =>
            iAsicR0 <= '1';
            next_state <= IDLE_S;
            
         when SRO_HIGH_S =>
            acqDone <= '1';
            asicSRO <= '1';
            if delayCnt >= to_integer(sROWidth) - 1 then
               next_state <= WAIT_READOUT_S;
            end if;
            
         when WAIT_READOUT_S =>
            -- wait for the readout state machine to complete
            -- the timeout is implemented there
            -- readPend is always '0' when the readout is disabled in the configuration
            if readPend = '0' then
               -- read twice
               -- 1st cntA
               -- 2nd cntB
               if runsCnt < 1 then
                  delayCntRst <= '1';
                  runsCntEn <= '1';
                  next_state <= SRO_HIGH_S;
               else
                  runsCntRst <= '1';
                  -- sync the ASICs via sync pin or SACI command
                  if syncMode = "00" then
                     delayCntRst <= '1';
                     next_state <= SYNC_HIGH_S;
                  else
                     next_state <= SACI_SYNC_S;
                  end if;   
               end if;   
            end if;  
            
            if runsCnt = 0 then
               readCntA <= '1';
            end if;
         
         when SYNC_HIGH_S =>
            iAsicSync <= '1';
            if delayCnt >= to_integer(syncWidth) - 1 then
               next_state <= IDLE_S;
            end if;
         
         when SACI_SYNC_S =>
            saciReadoutReq <= '1';
            if saciReadoutAck = '1' then
               saciReadoutReq <= '0';
               next_state <= IDLE_S;
            end if;
            
         when others =>
            next_state <= IDLE_S;
      
      end case;
      
   end process;
   
   
   
   abfsm_cmb_p: process (
      ab_state, startAbDly, a2bDlyCnt
   ) 
   begin
      ab_next_state <= ab_state;
      a2bDlyRst <= '1';
      a2bCntEn <= '0';
      
      case ab_state is
      
         when IDLE_S =>
            if startAbDly = '1' then
               ab_next_state <= WAIT_ABEN_HIGH_S;
            end if;
         
          when WAIT_ABEN_HIGH_S =>
            a2bDlyRst <= '0';
            if a2bDlyCnt = 0 then
               ab_next_state <= ABEN_HIGH_S;
            end if;
         
         when ABEN_HIGH_S =>
            a2bCntEn <= '1';
            ab_next_state <= IDLE_S;
            
         when others =>
            ab_next_state <= IDLE_S;
      
      end case;
      
   end process;
   
   
   
   
end rtl;
