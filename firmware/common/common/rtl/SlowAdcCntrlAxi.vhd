-------------------------------------------------------------------------------
-- Title      : ADS1217 ADC Controller
-- Project    : EPIX Detector
-------------------------------------------------------------------------------
-- File       : SlowAdcCntrlAxi.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- This block is responsible for reading the voltages, currents and strongback  
-- temperatures from the ADS1217 on the generation 2 EPIX analog board.
-- The ADS1217 is an 8 channel ADC.
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
use ieee.math_real.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiPkg.all;

entity SlowAdcCntrlAxi is 
   generic (
      TPD_G           	: time := 1 ns;
      SYS_CLK_PERIOD_G  : real := 10.0E-9;   -- 100MHz
      ADC_CLK_PERIOD_G  : real := 200.0E-9;  -- 5MHz
      SPI_SCLK_PERIOD_G : real := 1.0E-6;    -- 1MHz
      AXIL_ERR_RESP_G   : slv(1 downto 0)  := AXI_RESP_DECERR_C
   );
   port ( 
      -- Master system clock
      sysClk            : in  sl;
      sysClkRst         : in  sl;

      -- Trigger Control
      adcStart          : in  sl;
      
      -- external enable strobe (optional)
      monEnAxisMaster   : in  AxiStreamMasterType := AXI_STREAM_MASTER_INIT_C;
      
      -- Raw env data outputs (optional)
      envData           : out Slv32Array(8 downto 0);
      
      -- AXI lite slave port for register access
      axilClk           : in  sl;
      axilRst           : in  sl;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType;
      
      -- AXI stream output
      axisClk           : in  sl;
      axisRst           : in  sl;
      mAxisMaster       : out AxiStreamMasterType;
      mAxisSlave        : in  AxiStreamSlaveType;

      -- ADC Control Signals
      adcRefClk         : out sl;
      adcDrdy           : in  sl;
      adcSclk           : out sl;
      adcDout           : in  sl;
      adcCsL            : out sl;
      adcDin            : out sl
   );
end SlowAdcCntrlAxi;


-- Define architecture
architecture RTL of SlowAdcCntrlAxi is

   constant r0_speed :     std_logic_vector(0 downto 0) := "0";      -- "0" - fosc/128, "1" - fosc/256
   constant r0_refhi :     std_logic_vector(0 downto 0) := "0";      -- "0" - Vref 1.25, "1" - Vref 2.5
   constant r0_bufen :     std_logic_vector(0 downto 0) := "0";      -- "0" - buffer disabled, "1" - buffer enabled
   constant r2_idac1r :    std_logic_vector(1 downto 0) := "01";     -- "00" - off, "01" - range 1 (0.25mA@1.25Vref) ... "11" - range 3 (1mA@1.25Vref)
   constant r2_idac2r :    std_logic_vector(1 downto 0) := "01";     -- "00" - off, "01" - range 1 (0.25mA@1.25Vref) ... "11" - range 3 (1mA@1.25Vref)
   constant r2_pga :       std_logic_vector(2 downto 0) := "000";    -- PGA 1 to 128
   constant r3_idac1 :     std_logic_vector(7 downto 0) := CONV_STD_LOGIC_VECTOR(26, 8);    -- I DAC1 0 to max range
   constant r4_idac2 :     std_logic_vector(7 downto 0) := CONV_STD_LOGIC_VECTOR(26, 8);    -- I DAC2 0 to max range
   constant r5_r6_dec0 :   std_logic_vector(10 downto 0) := CONV_STD_LOGIC_VECTOR(195, 11); -- Decimation value
   constant r6_ub :        std_logic_vector(0 downto 0) := "1";      -- "0" - bipolar, "1" - unipolar
   constant r6_mode :      std_logic_vector(1 downto 0) := "00";     -- "00" - auto, "01" - fast ...
   
   constant adc_setup_regs : Slv8Array(9 downto 0) := (
      0 => "000" & r0_speed & "1" & r0_refhi & r0_bufen & "0",
      1 => "00001000",  -- start with MUX set to Ain0 and Comm
      2 => "0" & r2_idac1r & r2_idac2r & r2_pga,
      3 => r3_idac1,
      4 => r4_idac2,
      5 => "00000000",  -- offset DAC leave default
      6 => "00000000",  -- DIO leave default
      7 => "11111110",  -- change bit 0 DIR to output
      8 => r5_r6_dec0(7 downto 0),
      9 => "0" & r6_ub & r6_mode & "0" & r5_r6_dec0(10 downto 8)
   );
   
   constant cmd_wr_reg :   std_logic_vector(3 downto 0) := "0101";
   constant cmd_reset :    std_logic_vector(7 downto 0) := "11111110";
   constant cmd_dsync :    std_logic_vector(7 downto 0) := "11111100";
   constant cmd_rdata :    std_logic_vector(7 downto 0) := "00000001";
   
   constant adc_refclk_t: integer := integer(ceil((ADC_CLK_PERIOD_G/SYS_CLK_PERIOD_G)/2.0))-1;
   constant dout_wait_t: integer := 60;
   constant wreg_wait_t: integer := 6;
   constant reset_wait_t: integer := 20;
   
   TYPE STATE_TYPE IS (RESET, IDLE, CMD_SEND, CMD_WAIT, CMD_DLY, WAIT_DRDY, READ_DATA, STORE_DATA);
   SIGNAL state, next_state   : STATE_TYPE;   
   
   signal adcDrdyEn :      std_logic;
   signal adcDrdyD1 :      std_logic;
   signal adcDrdyD2 :      std_logic;
   signal adcStartEn :     std_logic;
   signal adcStartD1 :     std_logic;
   signal adcStartD2 :     std_logic;
   signal spi_wr_en :      std_logic;
   signal spi_wr_data :    std_logic_vector(7 downto 0);
   signal spi_rd_en :      std_logic;
   signal spi_rd_en_d1 :   std_logic;
   signal spi_rd_data :    std_logic_vector(7 downto 0);
   signal cmd_counter :    integer range 0 to 22;
   signal cmd_data :       integer range 0 to 22;
   signal cmd_load :       std_logic;
   signal cmd_en :         std_logic;
   signal ch_sel  :        std_logic_vector(3 downto 0);
   signal byte_counter :   integer range 0 to 3;
   signal byte_rst :       std_logic;
   signal byte_en :        std_logic;
   signal ch_counter :     integer range 0 to 9;
   signal channel_en :     std_logic;
   
   signal wait_counter :   integer range 0 to dout_wait_t;
   signal wait_data :      integer range 0 to dout_wait_t;
   signal wait_load :      std_logic;
   signal wait_done :      std_logic;
   
   signal data_23_16 :     std_logic_vector(7 downto 0);
   signal data_15_08 :     std_logic_vector(7 downto 0);
   
   signal ref_counter :    integer range 0 to adc_refclk_t;
   signal ref_clk :        std_logic;
   signal ref_clk_en :     std_logic;
   
   signal csl_master :     std_logic;
   signal csl_cmd :        std_logic;
   
   signal adcData :        Slv24Array(8 downto 0);
   signal adcDataSync :    Slv24Array(8 downto 0);
   signal iEnvData :       Slv32Array(8 downto 0);
   signal envDataSync :    Slv32Array(8 downto 0);
   
   signal streamPeriodSync : slv(31 downto 0);
   
   signal monitorTrig   : sl;
   signal monTrigCnt    : integer;
   
   signal mAxisMasterFifo : AxiStreamMasterType;
   signal mAxisSlaveFifo :  AxiStreamSlaveType;
   
   signal streamEnSync     : sl;
   
   type RegType is record
      streamEn          : sl;
      streamPeriod      : slv(31 downto 0);
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
   end record RegType;

   constant REG_INIT_C : RegType := (
      streamEn          => '0',
      streamPeriod      => toSlv(getTimeRatio(1.0, SYS_CLK_PERIOD_G),32),
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
   );
   
   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;

begin
   
   -----------------------------------------------------------------------------------------------------------------------
   -----------   AXI LIte register readout logic  ----------------------------
   -----------------------------------------------------------------------------------------------------------------------
   
   DSync_G : for i in 0 to 8 generate 
      DaSync_U: entity surf.SynchronizerVector
      generic map (         
         WIDTH_G  => 24
      )
      port map (
         clk     => axilClk,
         rst     => axilRst,
         dataIn  => adcData(i),
         dataOut => adcDataSync(i)
      );
      DeSync_U: entity surf.SynchronizerVector
      generic map (         
         WIDTH_G  => 32
      )
      port map (
         clk     => axilClk,
         rst     => axilRst,
         dataIn  => iEnvData(i),
         dataOut => envDataSync(i)
      );
   end generate;
   
   EnSync_U: entity surf.Synchronizer
   port map (
      clk     => sysClk,
      rst     => sysClkRst,
      dataIn  => r.streamEn,
      dataOut => streamEnSync
   );
   
   SpSync_U: entity surf.SynchronizerVector
   generic map (         
      WIDTH_G  => 32
   )
   port map (
      clk     => sysClk,
      rst     => sysClkRst,
      dataIn  => r.streamPeriod,
      dataOut => streamPeriodSync
   );
      
   
   comb : process (axilRst, sAxilReadMaster, sAxilWriteMaster, r, adcDataSync, envDataSync, monEnAxisMaster) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      v := r;
      
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, v.sAxilWriteSlave, v.sAxilReadSlave);
      
      -- dedicated axi stream channel to set or clear monitorEnable register
      if monEnAxisMaster.tValid = '1' and monEnAxisMaster.tLast = '1' then
         v.streamEn := monEnAxisMaster.tData(0);
      end if;
      
      axiSlaveRegister(regCon, x"00", 0, v.streamEn);
      axiSlaveRegister(regCon, x"04", 0, v.streamPeriod);
      
      -- raw ADC data registers
      axiSlaveRegisterR(regCon, x"40", 0, adcDataSync(0));
      axiSlaveRegisterR(regCon, x"44", 0, adcDataSync(1));
      axiSlaveRegisterR(regCon, x"48", 0, adcDataSync(2));
      axiSlaveRegisterR(regCon, x"4C", 0, adcDataSync(3));
      axiSlaveRegisterR(regCon, x"50", 0, adcDataSync(4));
      axiSlaveRegisterR(regCon, x"54", 0, adcDataSync(5));
      axiSlaveRegisterR(regCon, x"58", 0, adcDataSync(6));
      axiSlaveRegisterR(regCon, x"5C", 0, adcDataSync(7));
      axiSlaveRegisterR(regCon, x"60", 0, adcDataSync(8));
      
      -- converted environmental data registers
      axiSlaveRegisterR(regCon, x"80", 0, envDataSync(0));
      axiSlaveRegisterR(regCon, x"84", 0, envDataSync(1));
      axiSlaveRegisterR(regCon, x"88", 0, envDataSync(2));
      axiSlaveRegisterR(regCon, x"8C", 0, envDataSync(3));
      axiSlaveRegisterR(regCon, x"90", 0, envDataSync(4));
      axiSlaveRegisterR(regCon, x"94", 0, envDataSync(5));
      axiSlaveRegisterR(regCon, x"98", 0, envDataSync(6));
      axiSlaveRegisterR(regCon, x"9C", 0, envDataSync(7));
      axiSlaveRegisterR(regCon, x"A0", 0, envDataSync(8));
      
      axiSlaveDefault(regCon, v.sAxilWriteSlave, v.sAxilReadSlave, AXIL_ERR_RESP_G);
      
      if (axilRst = '1') then
         v := REG_INIT_C;
      end if;

      rin <= v;

      sAxilWriteSlave   <= r.sAxilWriteSlave;
      sAxilReadSlave    <= r.sAxilReadSlave;

   end process comb;

   seq : process (axilClk) is
   begin
      if (rising_edge(axilClk)) then
         r <= rin after TPD_G;
      end if;
   end process seq;
   
   
   
   -----------------------------------------------------------------------------------------------------------------------
   -----------   ADC data readout logic - all channnels + epix board switch ----------------------------
   -----------------------------------------------------------------------------------------------------------------------
   
   -- ADC reference clock counter
   ref_cnt_p: process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            ref_counter <= 0 after TPD_G;
            ref_clk <= '0' after TPD_G;
         elsif ref_counter >= adc_refclk_t then
            ref_counter <= 0 after TPD_G;
            ref_clk <= not ref_clk after TPD_G;
         else
            ref_counter <= ref_counter + 1 after TPD_G;
         end if;
      end if;
   end process;
   adcRefClk <= ref_clk;
   ref_clk_en <= '1' when ref_clk = '1' and ref_counter >= adc_refclk_t else '0';

   -- Drdy sync and falling edge detector
   process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            adcDrdyD1 <= '0' after TPD_G;
            adcDrdyD2 <= '0' after TPD_G;
            adcStartD1 <= '0' after TPD_G;
            adcStartD2 <= '0' after TPD_G;
            spi_rd_en_d1 <= '0' after TPD_G;
         else
            adcDrdyD1 <= adcDrdy after TPD_G;
            adcDrdyD2 <= adcDrdyD1 after TPD_G;
            adcStartD1 <= adcStart after TPD_G;
            adcStartD2 <= adcStartD1 after TPD_G;
            spi_rd_en_d1 <= spi_rd_en after TPD_G;
         end if;
      end if;
   end process;
   
   adcDrdyEn <= adcDrdyD2 and not adcDrdyD1;
   adcStartEn <= adcStartD1 and not adcStartD2;

   -- Instance of the SPI Master controller
   SPI_Master_i: entity surf.SpiMaster
      generic map (
         TPD_G             => TPD_G,
         NUM_CHIPS_G       => 1,
         DATA_SIZE_G       => 8,
         CPHA_G            => '1',
         CPOL_G            => '1',
         CLK_PERIOD_G      => SYS_CLK_PERIOD_G,
         SPI_SCLK_PERIOD_G => SPI_SCLK_PERIOD_G
      )
      port map (
         --Global Signals
         clk      => sysClk,
         sRst     => sysClkRst,
         -- Parallel interface
         chipSel  => "0",
         wrEn     => spi_wr_en,
         wrData   => spi_wr_data,
         rdEn     => spi_rd_en,
         rdData   => spi_rd_data,
         --SPI interface
         --spiCsL(0)=> adcCsL,
         spiCsL(0)=> csl_master,
         spiSclk  => adcSclk,
         spiSdi   => adcDin,
         spiSdo   => adcDout
      );
      
      adcCsL <= csl_master and csl_cmd;
   
   -- keep CS low when within one command
   csl_cmd <= 
      '1'   when cmd_counter = 0 else    -- write reset command 
      '1'   when cmd_counter = 1 else    -- write register command starting from reg 0
      '0'   when cmd_counter = 2 else    -- write register command write 10 registers
      '0'   when cmd_counter = 3 else    -- write registers 0 to 9
      '0'   when cmd_counter = 4 else 
      '0'   when cmd_counter = 5 else 
      '0'   when cmd_counter = 6 else 
      '0'   when cmd_counter = 7 else 
      '0'   when cmd_counter = 8 else 
      '0'   when cmd_counter = 9 else 
      '0'   when cmd_counter = 10 else 
      '0'   when cmd_counter = 11 else 
      '0'   when cmd_counter = 12 else 
      '1'   when cmd_counter = 13 else
      '1'   when cmd_counter = 14 else
      '1'   when cmd_counter = 15 else
      '0';
   
   -- selsct command to be transimitted to the ADC
   spi_wr_data <=   
      cmd_reset               when cmd_counter = 0 else    -- write reset command 
      cmd_wr_reg & "0000"     when cmd_counter = 1 else    -- write register command starting from reg 0
      "00001001"              when cmd_counter = 2 else    -- write register command write 10 registers
      adc_setup_regs(0)       when cmd_counter = 3 else    -- write registers 0 to 9
      ch_sel & "1000"         when cmd_counter = 4 and ch_counter < 8 else    -- write register data with selected ain
      "0111"  & "1000"        when cmd_counter = 4 and ch_counter = 8 else    -- write register data with ain no 7
      adc_setup_regs(2)       when cmd_counter = 5 else 
      adc_setup_regs(3)       when cmd_counter = 6 else 
      adc_setup_regs(4)       when cmd_counter = 7 else 
      adc_setup_regs(5)       when cmd_counter = 8 else 
      "00000001"              when cmd_counter = 9 and ch_counter = 8 else    -- write register data, switch external MUX
      "00000000"              when cmd_counter = 9 and ch_counter /= 8 else   -- write register data, do not switch external MUX
      adc_setup_regs(7)       when cmd_counter = 10 else 
      adc_setup_regs(8)       when cmd_counter = 11 else 
      adc_setup_regs(9)       when cmd_counter = 12 else 
      cmd_dsync               when cmd_counter = 13 else    -- write dsync command
      "00000000"              when cmd_counter = 14 else    -- write zeros to release reset (see ADC doc.)
      cmd_rdata               when cmd_counter = 15 else    -- write RDATA command
      "00000000";
      

   -- comand select counter
   cmd_cnt_p: process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            cmd_counter <= 0 after TPD_G;
         elsif cmd_load = '1'  then
            cmd_counter <= cmd_data after TPD_G;
         elsif cmd_en = '1' then
            cmd_counter <= cmd_counter + 1 after TPD_G;         
         end if;
      end if;
   end process;
   
   
   -- after command delay counter
   wait_cnt_p: process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            wait_counter <= 0 after TPD_G;
         elsif wait_load = '1' then
            wait_counter <= wait_data after TPD_G;       
         elsif wait_done = '0' and ref_clk_en = '1' then
            wait_counter <= wait_counter - 1 after TPD_G;
         end if;
      end if;
   end process;
   wait_done <= '1' when wait_counter = 0 else '0';
   wait_data <= 
      reset_wait_t      when cmd_counter = 1 else     -- tosc delay after reset cmd
      wreg_wait_t       when cmd_counter = 13 else    -- tosc delay after wreg cmd
      wreg_wait_t       when cmd_counter = 14 else    -- tosc delay after dsync
      dout_wait_t       when cmd_counter = 16 else    -- tosc delay after rdata cmd
      0;
   
   -- read byte counter
   byte_cnt_p: process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or byte_rst = '1' then
            byte_counter <= 0 after TPD_G;
         elsif byte_en = '1' then
            byte_counter <= byte_counter + 1 after TPD_G;         
         end if;
      end if;
   end process;
   
   -- acquisition chanel counter
   ch_cnt_p: process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            ch_counter <= 0 after TPD_G;
         elsif channel_en = '1' then
            if ch_counter = 5 then     -- skip removed channel 6
               ch_counter <= ch_counter + 2 after TPD_G;
            elsif ch_counter < 8 then
               ch_counter <= ch_counter + 1 after TPD_G;
            else
               ch_counter <= 0 after TPD_G;
            end if;
         end if;
      end if;
   end process;
   ch_sel <= CONV_STD_LOGIC_VECTOR(ch_counter, 4);
   
   -- acquisition data storage
   data_reg_p: process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            data_23_16 <= (others=>'0') after TPD_G;
            data_15_08 <= (others=>'0') after TPD_G;
         elsif byte_counter = 0 and spi_rd_en = '1' and spi_rd_en_d1 = '0' then
            data_23_16 <= spi_rd_data after TPD_G;
         elsif byte_counter = 1 and spi_rd_en = '1' and spi_rd_en_d1 = '0' then
            data_15_08 <= spi_rd_data after TPD_G;
         elsif byte_counter = 2 and spi_rd_en = '1' and spi_rd_en_d1 = '0' then
            adcData(ch_counter) <= data_23_16 & data_15_08 & spi_rd_data after TPD_G;
         end if;
      end if;
   end process;
   
   -- Readout loop FSM
   fsm_cnt_p: process ( sysClk ) 
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            state <= RESET after TPD_G;
         else
            state <= next_state after TPD_G;         
         end if;
      end if;
   end process;

   fsm_cmb_p: process ( state, adcDrdyEn, spi_rd_en, cmd_counter, byte_counter, adcStartEn, wait_done) 
   begin
      next_state <= state;
      cmd_en <= '0';
      cmd_load <= '0';
      cmd_data <= 0;
      byte_en <= '0';
      byte_rst <= '0';
      spi_wr_en <= '0';
      channel_en <= '0';
      wait_load <= '0';
      
      case state is
      
         when RESET =>           -- command 0 (reset) only after power up
            cmd_load <= '1'; 
            if adcStartEn = '1' then
               next_state <= CMD_SEND;
            end if;
      
         when IDLE =>            -- start from command 1
            cmd_data <= 1;
            cmd_load <= '1';
            if adcStartEn = '1' then
               next_state <= CMD_SEND;
            end if;
         
         when CMD_SEND =>        -- trigger the SPI master
            spi_wr_en <= '1';
            cmd_en <= '1';
            next_state <= CMD_WAIT;
            
         when CMD_WAIT =>        -- wait for the SPI master to finish
            wait_load <= '1';
            if spi_rd_en = '1' then
               next_state <= CMD_DLY;
            end if;
         
         when CMD_DLY =>                     -- wait required Tosc periods (see ADC doc.)
            if wait_done = '1' then
               if cmd_counter < 15 then      -- repeat send command up to DSYNC
                  next_state <= CMD_SEND;    
               elsif cmd_counter = 15 then   -- after DSYNC must wait for DRDY
                  next_state <= WAIT_DRDY;
               else                          -- after RDATA go to data readout
                  byte_rst <= '1';
                  next_state <= READ_DATA;
               end if;
            end if;
         
         when WAIT_DRDY =>          -- wait for DRDY and go to send RDATA command
            if adcDrdyEn = '1' then
               next_state <= CMD_SEND;
            end if;
         
         when READ_DATA =>          -- trigger the SPI master for readout
            spi_wr_en <= '1';
            next_state <= STORE_DATA;
         
         when STORE_DATA =>         -- wait for the readout to complete and repeat 3 times
            if spi_rd_en = '1' then
               if byte_counter < 2 then
                  next_state <= READ_DATA;
                  byte_en <= '1';
               else
                  next_state <= IDLE;
                  channel_en <= '1';
                  byte_en <= '1';
               end if;
            end if;
         
         when others =>
            next_state <= RESET;
      
      end case;
      
   end process;
   
   
   -- conversion LUT
   SlowAdcLUT_U: entity work.SlowAdcLUT
   port map (
      sysClk          => sysClk,
      sysClkRst       => sysClkRst,
      adcData         => adcData,
      outEnvData      => iEnvData
   );
   envData <= iEnvData;
   
   -- ADC data stream
   SlowAdcStream_U: entity work.SlowAdcStream
   port map (
      sysClk               => sysClk,
      sysRst               => sysClkRst,
      acqCount             => (others=>'0'),
      seqCount             => (others=>'0'),
      trig                 => monitorTrig,
      dataIn               => iEnvData,
      mAxisMaster          => mAxisMasterFifo,
      mAxisSlave           => mAxisSlaveFifo
   );
   
   -- trigger monitor data stream at settable rate
   P_MonStrTrig: process (sysClk)
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or monitorTrig = '1' then
            monTrigCnt <= 0;
         elsif streamEnSync = '1' then
            monTrigCnt <= monTrigCnt + 1;
         end if;
      end if;   
   end process;
   monitorTrig <= '1' when monTrigCnt >= streamPeriodSync and streamEnSync = '1' and streamPeriodSync /= 0 else '0';
   
   -- Stream sync FIFO
   AxiStreamFifo_U: entity surf.AxiStreamFifoV2
   generic map (
      SLAVE_AXI_CONFIG_G   => ssiAxiStreamConfig(4),
      MASTER_AXI_CONFIG_G  => ssiAxiStreamConfig(4)
   )
   port map (
      sAxisClk    => sysClk,
      sAxisRst    => sysClkRst,
      sAxisMaster => mAxisMasterFifo,
      sAxisSlave  => mAxisSlaveFifo,
      mAxisClk    => axisClk,
      mAxisRst    => axisRst,
      mAxisMaster => mAxisMaster,
      mAxisSlave  => mAxisSlave
   );

end RTL;

