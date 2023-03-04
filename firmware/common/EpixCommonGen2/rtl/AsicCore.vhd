-------------------------------------------------------------------------------
-- File       : AsicCore.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: EPIX Quad Target's Top Level
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
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;

use work.EpixPkgGen2.all;

library unisim;
use unisim.vcomponents.all;

entity AsicCore is
   generic (
      TPD_G                : time             := 1 ns;
      FPGA_BASE_CLOCK_G    : slv(31 downto 0);
      BUILD_INFO_G         : BuildInfoType;
      AXI_CLK_FREQ_G       : real             := 100.00E+6;
      ASIC_TYPE_G          : AsicType;
      AXI_BASE_ADDR_G      : slv(31 downto 0) := (others => '0')
   );
   port (
      -- Clock and Reset
      sysClk               : in    sl;
      sysRst               : in    sl;
      axiRst               : out   sl;
      -- ADC signals
      adcStreams           : in    AxiStreamMasterArray(19 downto 0);
      -- AXI-Lite Register Interface (sysClk domain)
      mAxilReadMaster      : in    AxiLiteReadMasterType;
      mAxilReadSlave       : out   AxiLiteReadSlaveType;
      mAxilWriteMaster     : in    AxiLiteWriteMasterType;
      mAxilWriteSlave      : out   AxiLiteWriteSlaveType;
      -- ASIC Control
      asicR0               : out sl;
      asicPpmat            : out sl;
      asicPpbe             : out sl;
      asicGrst             : out sl;
      asicAcq              : out sl;
      asic0Dm2             : in  sl;
      asic0Dm1             : in  sl;
      asicRoClk            : out sl;
      asicSync             : out sl;
      -- ASIC digital data
      asicDout             : in  slv(3 downto 0) := "0000";
      -- ADC clock
      adcClkP              : out slv( 2 downto 0);
      adcClkN              : out slv( 2 downto 0);
      -- Guard ring DAC
      vGuardDacSclk        : out sl;
      vGuardDacDin         : out sl;
      vGuardDacCsb         : out sl;
      vGuardDacClrb        : out sl;
      -- Board IDs
      serialIdIo           : inout slv(1 downto 0) := "00";
      -- External Signals
      runTrigger           : in  sl;
      daqTrigger           : in  sl;
      mpsOut               : out sl;
      triggerOut           : out sl;
      -- SW and fiber trigger
      swRun                : in  sl;
      pgpOpCode            : in  slv(7 downto 0);
      pgpOpCodeEn          : in  sl;
      -- Power enables
      digitalPowerEn       : out sl;
      analogPowerEn        : out sl;
      fpgaOutputEn         : out sl;
      ledEn                : out sl;
      adcCardPowerUp       : out sl;
      delayCtrlRdy         : in  sl;
      requestStartupCal    : out sl;
      acqStartOut          : out sl;
      -- env data
      envData              : in    Slv32Array(8 downto 0);
      -- Image Data Stream
      dataAxisMaster       : out   AxiStreamMasterType;
      dataAxisSlave        : in    AxiStreamSlaveType;
      -- Scope Data Stream
      scopeAxisMaster      : out   AxiStreamMasterType;
      scopeAxisSlave       : in    AxiStreamSlaveType
   );
end AsicCore;

architecture rtl of AsicCore is
   
   constant NUM_AXI_MASTERS_C    : natural := 4;

   constant REGS_INDEX_C         : natural := 0;
   constant EXT_REGS_INDEX_C     : natural := 1;
   constant SCOPE_INDEX_C        : natural := 2;
   constant DOUT_INDEX_C         : natural := 3;

   constant AXI_CONFIG_C   : AxiLiteCrossbarMasterConfigArray(NUM_AXI_MASTERS_C-1 downto 0) := genAxiLiteConfig(NUM_AXI_MASTERS_C, AXI_BASE_ADDR_G, 24, 20);

   signal mAxiWriteMasters : AxiLiteWriteMasterArray(NUM_AXI_MASTERS_C-1 downto 0);
   signal mAxiWriteSlaves  : AxiLiteWriteSlaveArray(NUM_AXI_MASTERS_C-1 downto 0);
   signal mAxiReadMasters  : AxiLiteReadMasterArray(NUM_AXI_MASTERS_C-1 downto 0);
   signal mAxiReadSlaves   : AxiLiteReadSlaveArray(NUM_AXI_MASTERS_C-1 downto 0);
   
   
   
   -- ASIC signals
   signal iAsicAcq   : sl;
   signal iAsicR0    : sl;
   signal iAsicPpmat : sl;
   signal iAsicPpbe  : sl;
   signal iAsicGrst  : sl;
   signal iAsicRoClk : sl;
   signal iAsicSync  : sl;
   signal iInjAcq    : sl;
   
   signal doutOut    : Slv2Array(15 downto 0);
   signal doutRd     : slv(15 downto 0);
   signal doutValid  : slv(15 downto 0);
   signal roClkTail  : slv(7 downto 0);
   
   -- Triggers and associated signals
   signal iDaqTrigger      : sl;
   signal iRunTrigger      : sl;
   signal opCode           : slv(7 downto 0);
   
   -- Interfaces between blocks
   signal acqStart           : sl;
   signal acqBusy            : sl;
   signal dataSend           : sl;
   signal readDone           : sl;
   signal readValid          : slv(15 downto 0);
   signal adcPulse           : sl;
   
   -- Configuration and status
   signal epixStatus       : EpixStatusType;
   signal epixConfig       : EpixConfigType;
   signal epixConfigExt    : EpixConfigExtType;
   
   signal iAxiRst      : sl;
   
   -- ADC signals
   signal adcValid         : slv(19 downto 0);
   signal adcData          : Slv16Array(19 downto 0);
   
begin
   
   axiRst <= iAxiRst;
   acqStartOut <= acqStart;
   
   GenAdcStr : for i in 0 to 19 generate 
      adcData(i)  <= adcStreams(i).tData(15 downto 0);
      adcValid(i) <= adcStreams(i).tValid;
   end generate;
   
   -- Map out power enables
   digitalPowerEn <= epixConfig.powerEnable(0);
   analogPowerEn  <= epixConfig.powerEnable(1);
   fpgaOutputEn   <= epixConfig.powerEnable(2);
   ledEn          <= epixConfig.powerEnable(3);
   
   -- Triggers out
   triggerOut  <= 
         iAsicAcq     when epixConfigExt.dbgReg2 = "00000" else
         acqStart    when epixConfigExt.dbgReg2 = "00001" else
         dataSend    when epixConfigExt.dbgReg2 = "00010" else
         acqBusy     when epixConfigExt.dbgReg2 = "00011" else
         readDone    when epixConfigExt.dbgReg2 = "00100" else
         iAsicSync   when epixConfigExt.dbgReg2 = "00101" else
         iAsicR0     when epixConfigExt.dbgReg2 = "00110" else
         iAsicRoClk  when epixConfigExt.dbgReg2 = "00111" else
         iInjAcq     when epixConfigExt.dbgReg2 = "01000" else
         '0';
   
   mpsOut      <= 
         iAsicAcq     when epixConfigExt.dbgReg = "00000" else
         acqStart    when epixConfigExt.dbgReg = "00001" else
         dataSend    when epixConfigExt.dbgReg = "00010" else
         acqBusy     when epixConfigExt.dbgReg = "00011" else
         readDone    when epixConfigExt.dbgReg = "00100" else
         iAsicSync   when epixConfigExt.dbgReg = "00101" else
         iAsicR0     when epixConfigExt.dbgReg = "00110" else
         iAsicRoClk  when epixConfigExt.dbgReg = "00111" else
         iInjAcq     when epixConfigExt.dbgReg = "01000" else     -- this is debug pulse to trigger exernal source within ACQ pulse
         '0';
   
   -- Triggers in
   iRunTrigger    <= runTrigger;
   iDaqTrigger    <= daqTrigger;
   
   -- ASIC signals
   asicR0         <= iAsicR0;
   asicPpmat      <= iAsicPpmat;
   asicPpbe       <= iAsicPpbe;
   asicGrst       <= iAsicGrst;
   asicAcq        <= iAsicAcq;
   asicRoClk      <= iAsicRoClk;
   asicSync       <= iAsicSync;
   
   requestStartupCal <= epixConfig.requestStartupCal;
   
   ---------------------
   -- AXI-Lite: Crossbar
   ---------------------
   U_XBAR0 : entity surf.AxiLiteCrossbar
      generic map (
         TPD_G              => TPD_G,
         NUM_SLAVE_SLOTS_G  => 1,
         NUM_MASTER_SLOTS_G => NUM_AXI_MASTERS_C,
         MASTERS_CONFIG_G   => AXI_CONFIG_C
      )
      port map (
         axiClk              => sysClk,
         axiClkRst           => sysRst,
         sAxiWriteMasters(0) => mAxilWriteMaster,
         sAxiWriteSlaves(0)  => mAxilWriteSlave,
         sAxiReadMasters(0)  => mAxilReadMaster,
         sAxiReadSlaves(0)   => mAxilReadSlave,

         mAxiWriteMasters => mAxiWriteMasters,
         mAxiWriteSlaves  => mAxiWriteSlaves,
         mAxiReadMasters  => mAxiReadMasters,
         mAxiReadSlaves   => mAxiReadSlaves
      );
   
   
   --------------------------------------------
   --     Master Register Controller         --
   --------------------------------------------   
   U_RegControl : entity work.RegControl
   generic map (
      TPD_G                => TPD_G,
      FPGA_BASE_CLOCK_G    => FPGA_BASE_CLOCK_G,
      BUILD_INFO_G         => BUILD_INFO_G,
      CLK_PERIOD_G         => 10.0e-9
   )
   port map (
      axiClk         => sysClk,
      axiRst         => iAxiRst, -- out 
      sysRst         => sysRst, -- in
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  => mAxiReadMasters(REGS_INDEX_C),
      axiReadSlave   => mAxiReadSlaves(REGS_INDEX_C),
      axiWriteMaster => mAxiWriteMasters(REGS_INDEX_C),
      axiWriteSlave  => mAxiWriteSlaves(REGS_INDEX_C),
      -- Register Inputs/Outputs (axiClk domain)
      epixStatus     => epixStatus,
      epixConfig     => epixConfig,
      -- Guard ring DAC interfaces
      dacSclk        => vGuardDacSclk,
      dacDin         => vGuardDacDin,
      dacCsb         => vGuardDacCsb,
      dacClrb        => vGuardDacClrb,
      -- 1-wire board ID interfaces
      serialIdIo     => serialIdIo
   );
   
   --------------------------------------------
   --     Extended Register Controller         --
   --------------------------------------------   
   U_RegExtControl : entity work.RegExtControl
   generic map (
      TPD_G             => TPD_G,
      FPGA_BASE_CLOCK_G => FPGA_BASE_CLOCK_G
   )
   port map (
      -- Global Signals
      axiClk          => sysClk,
      axiRst          => iAxiRst,
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  => mAxiReadMasters(EXT_REGS_INDEX_C),
      axiReadSlave   => mAxiReadSlaves(EXT_REGS_INDEX_C),
      axiWriteMaster => mAxiWriteMasters(EXT_REGS_INDEX_C),
      axiWriteSlave  => mAxiWriteSlaves(EXT_REGS_INDEX_C),
      -- Register Inputs/Outputs (axiClk domain)
      epixConfigExt  => epixConfigExt,
      epixConfig     => epixConfig
   );
   
   ---------------------
   -- Trig control    --
   ---------------------
   U_TrigControl : entity work.TrigControl 
   port map ( 
      -- Core clock, reset
      sysClk         => sysClk,
      sysClkRst      => iAxiRst,
      -- TTL triggers in 
      runTrigger     => iRunTrigger,
      daqTrigger     => iDaqTrigger,
      -- SW trigger in (from VC)
      swRun          => swRun,
      pgpOpCode      => pgpOpCode,
      pgpOpCodeEn    => pgpOpCodeEn,
      -- Opcode associated with this trigger
      opCodeOut      => opCode,
      -- Configuration
      epixConfig     => epixConfig,
      -- Status output
      acqCount       => epixStatus.acqCount,
      -- Interface to other blocks
      acqStart       => acqStart,
      dataSend       => dataSend
   );   
   
   ---------------------------------------------------------------
   -- Acquisition core
   --------------------- ------------------------------------------     
   U_AcqControl : entity work.AcqControl
   generic map (
      ASIC_TYPE_G     => ASIC_TYPE_G
   )
   port map (
      sysClk          => sysClk,
      sysClkRst       => iAxiRst,
      acqStart        => acqStart,
      acqBusy         => acqBusy,
      readDone        => readDone,
      readValid       => readValid,
      adcClkP         => adcClkP,
      adcClkM         => adcClkN,
      adcPulse        => adcPulse,
      roClkTail       => roClkTail,
      injAcq          => iInjAcq,
      epixConfig      => epixConfig,
      epixConfigExt   => epixConfigExt,
      asicR0          => iAsicR0,
      asicPpmat       => iAsicPpmat,
      asicPpbe        => iAsicPpbe,
      asicGlblRst     => iAsicGrst,
      asicAcq         => iAsicAcq,
      asicSync        => iAsicSync,
      asicRoClk       => iAsicRoClk
   );
   
   
   ---------------------------------------------------------------
   -- Readout core 
   --------------------- ------------------------------------------    
   U_ReadoutControl : entity work.ReadoutControl
   generic map (
     TPD_G                      => TPD_G,
     ASIC_TYPE_G                => ASIC_TYPE_G,
     MASTER_AXI_STREAM_CONFIG_G => ssiAxiStreamConfig(4, TKEEP_COMP_C)
   )
   port map (
      sysClk         => sysClk,
      sysClkRst      => iAxiRst,
      epixConfig     => epixConfig,
      epixConfigExt  => epixConfigExt,
      acqCount       => epixStatus.acqCount,
      seqCount       => epixStatus.seqCount,
      opCode         => opCode,
      acqStart       => acqStart,
      readValid      => readValid,
      readDone       => readDone,
      acqBusy        => acqBusy,
      dataSend       => dataSend,
      adcPulse       => adcPulse,
      adcValid       => adcValid,
      adcData        => adcData,
      envData        => envData,
      mAxisMaster    => dataAxisMaster,
      mAxisSlave     => dataAxisSlave,
      mpsOut         => open,
      doutOut        => doutOut,
      doutRd         => doutRd,
      doutValid      => doutValid
   );
   
   ---------------------------------------------------------------
   -- PseudoScope Core
   --------------------- ------------------------------------------
   U_PseudoScopeCore : entity work.PseudoScope2Axi
   generic map (
      TPD_G                      => TPD_G,
      INPUTS_G                   => 20,
      MASTER_AXI_STREAM_CONFIG_G => ssiAxiStreamConfig(4, TKEEP_COMP_C)
   )
   port map ( 
      -- system clock
      clk               => sysClk,
      rst               => iAxiRst,
      -- input data
      dataIn            => adcData,
      dataValid         => adcValid,
      -- arm signal
      arm               => acqStart,
      -- input triggers
      triggerIn(0)      => acqStart,
      triggerIn(1)      => iAsicAcq,
      triggerIn(2)      => iAsicR0,
      triggerIn(3)      => iAsicPpmat,
      triggerIn(4)      => iAsicPpbe,
      triggerIn(5)      => iAsicSync,
      triggerIn(6)      => iAsicGrst,
      triggerIn(7)      => iAsicRoClk,
      triggerIn(12 downto 8) => "00000",
      -- AXI stream output
      axisClk           => sysClk,
      axisRst           => iAxiRst,
      axisMaster        => scopeAxisMaster,
      axisSlave         => scopeAxisSlave,
      -- AXI lite for register access
      axilClk           => sysClk,
      axilRst           => iAxiRst,
      sAxilWriteMaster  => mAxiWriteMasters(SCOPE_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(SCOPE_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(SCOPE_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(SCOPE_INDEX_C)
   );
   
   
   ---------------------------------------------------------------
   -- Digital output deserializer only for EPIX10KA
   --------------------- ------------------------------------------
   G_DOUT_EPIX10KA : if ASIC_TYPE_G = EPIX10KA_C generate
   begin
      
      U_DoutAsic : entity work.DoutDeserializer
      port map ( 
         clk               => sysClk,
         rst               => iAxiRst,
         acqBusy           => acqBusy,
         roClkTail         => roClkTail,
         asicDout          => asicDout,
         asicRoClk         => iAsicRoClk,
         doutOut           => doutOut,
         doutRd            => doutRd,
         doutValid         => doutValid,
         sAxilWriteMaster  => mAxiWriteMasters(DOUT_INDEX_C),
         sAxilWriteSlave   => mAxiWriteSlaves(DOUT_INDEX_C),
         sAxilReadMaster   => mAxiReadMasters(DOUT_INDEX_C),
         sAxilReadSlave    => mAxiReadSlaves(DOUT_INDEX_C)
      );
   
   end generate;
   G_DOUT_NONE : if ASIC_TYPE_G /= EPIX10KA_C generate
      mAxiWriteSlaves(DOUT_INDEX_C) <= AXI_LITE_WRITE_SLAVE_INIT_C;
      mAxiReadSlaves(DOUT_INDEX_C)  <= AXI_LITE_READ_SLAVE_INIT_C;
      doutOut <= (others=>(others=>'0'));
      doutValid <= (others=>'1');
      roClkTail <= (others=>'0');      
   end generate;
   
   -- Give a special reset to the SERDES blocks when power
   -- is turned on to ADC card.
   adcCardPowerUp <= epixConfig.powerEnable(0) and epixConfig.powerEnable(1) and epixConfig.powerEnable(2);
   epixStatus.iDelayCtrlRdy <= delayCtrlRdy;
   
end rtl;
