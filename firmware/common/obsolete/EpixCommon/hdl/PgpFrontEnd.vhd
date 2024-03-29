-------------------------------------------------------------------------------
-- Title         : Pretty Good Protocol Applications, Front End Wrapper
-- Project       : General Purpose Core
-------------------------------------------------------------------------------
-- File          : PgpFrontEnd.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- Wrapper for front end logic connection to the PGP card.
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

use work.VcPkg.all;
use work.Pgp2CoreTypesPkg.all;

library UNISIM;
use UNISIM.vcomponents.all;

entity PgpFrontEnd is 
   generic (
      InterfaceType       : string := "PGP" -- PGP or ETH
   );
   port ( 
      
      -- Reference Clock, Power on Reset
      pgpRefClkP       : in  std_logic;
      pgpRefClkM       : in  std_logic;
      ethRefClkP       : in  std_logic;
      ethRefClkM       : in  std_logic;
      ponResetL        : in  std_logic;
      resetReq         : in  std_logic;

      -- Local clock and reset
      sysClk           : out std_logic;
      sysClkRst        : out std_logic;

      -- Local command signal
      pgpCmd           : out VcCmdSlaveOutType;

      -- Local register control signals
      pgpRegOut        : out VcRegSlaveOutType;
      pgpRegIn         : in  VcRegSlaveInType;

      -- Local data transfer signals
      frameTxIn        : in  VcUsBuff32InType;
      frameTxOut       : out VcUsBuff32OutType;

      -- Oscillscope channel data transfer signals
      scopeTxIn        : in  VcUsBuff32InType;
      scopeTxOut       : out VcUsBuff32OutType;

      -- Gtp Serial Pins
      pgpRxN           : in  std_logic;
      pgpRxP           : in  std_logic;
      pgpTxN           : out std_logic;
      pgpTxP           : out std_logic
   );
end PgpFrontEnd;


-- Define architecture
architecture PgpFrontEnd of PgpFrontEnd is

   -- Local Signals
   signal pgpTxVcIn          : VcTxQuadInType;
   signal pgpTxVcOut         : VcTxQuadOutType;
   signal pgpRxVcCommon      : VcRxCommonOutType;
   signal pgpRxVcOut         : VcRxQuadOutType;
   signal intRefClkOut       : std_logic;
   signal ipgpClk            : std_logic;
   signal ipgpClk2x          : std_logic;
   signal ipgpClkRst         : std_logic;
   signal isysClkRaw         : std_logic;
   signal isysClk            : std_logic;
   signal isysClkRst         : std_logic;
   signal isysClkRstRaw      : std_logic;
   signal iresetReq          : std_logic;
   signal pgpRefClk          : std_logic;
   signal ethRefClk          : std_logic;
   signal resetReqPgpSync    : std_logic;
   signal iUserClk           : std_logic;
   signal iUserClkRst        : std_logic;
   signal iPllFb             : std_logic;
   signal iPllLocked         : std_logic;

begin

   -- Outputs
   sysClk     <= isysClk;
   sysClkRst  <= isysClkRst;

   -- Reference Clock
   U_PgpRefClk : IBUFDS port map ( I => pgpRefClkP, IB => pgpRefClkM, O => pgpRefClk );
   U_EthRefClk : IBUFDS port map ( I => ethRefClkP, IB => ethRefClkM, O => ethRefClk );

   -- Synchronize the register reset
   iresetReq <= resetReq or not(iPllLocked);
   U_SyncReset : entity surf.Synchronizer
      generic map (
         TPD_G          => 1 ns,
         RST_POLARITY_G => '1',
         OUT_POLARITY_G => '1',
         RST_ASYNC_G    => true,
         STAGES_G       => 2,
         BYPASS_SYNC_G  => false,
         INIT_G         => "0"
      )
      port map (
         clk     => ipgpClk,
         rst     => '0',
         dataIn  => iresetReq,
         dataOut => resetReqPgpSync
      );

   -- Clock generation
   U_PgpClk: Pgp2GtpPackage.Pgp2GtpClk
      generic map (
         UserFxDiv  => 5,  --5 for 125 MHz
         UserFxMult => 4   --4 for 125 MHz
      )
      port map (
         pgpRefClk     => intRefClkOut,
         ponResetL     => ponResetL,
         locReset      => resetReqPgpSync,
         pgpClk        => ipgpClk,
         pgpReset      => ipgpClkRst,
         pgpClk2x      => ipgpClk2x,
         userClk       => iUserClk,
         userReset     => isysClkRst,
         pgpClkIn      => ipgpClk,
         userClkIn     => isysClk
      );
   -- Secondary DCM to generate 100 and 200 MHz
   U_UserClkGen : PLL_BASE
      generic map( 
         BANDWIDTH          => "OPTIMIZED", -- "HIGH", "LOW" or "OPTIMIZED"
         CLKFBOUT_MULT      =>   4, -- Multiplication factor for all output clocks
         CLKFBOUT_PHASE     => 0.0, -- Phase shift (degrees) of all output clocks
         CLKIN_PERIOD       => 8.0, -- Clock period (ns) of input clock on CLKIN
         CLKOUT0_DIVIDE     =>   5, -- Division factor for CLKOUT0 (1 to 128)
         CLKOUT0_DUTY_CYCLE => 0.5, -- Duty cycle for CLKOUT0 (0.01 to 0.99)
         CLKOUT0_PHASE      => 0.0, -- Phase shift (degrees) for CLKOUT0 (0.0 to 360.0)
         CLKOUT1_DIVIDE     =>   1, -- Division factor for CLKOUT1 (1 to 128)
         CLKOUT1_DUTY_CYCLE => 0.5, -- Duty cycle for CLKOUT1 (0.01 to 0.99)
         CLKOUT1_PHASE      => 0.0, -- Phase shift (degrees) for CLKOUT1 (0.0 to 360.0)
         CLKOUT2_DIVIDE     =>   1, -- Division factor for CLKOUT2 (1 to 128)
         CLKOUT2_DUTY_CYCLE => 0.5, -- Duty cycle for CLKOUT2 (0.01 to 0.99)
         CLKOUT2_PHASE      => 0.0, -- Phase shift (degrees) for CLKOUT2 (0.0 to 360.0)
         CLKOUT3_DIVIDE     =>   1, -- Division factor for CLKOUT3 (1 to 128)
         CLKOUT3_DUTY_CYCLE => 0.5, -- Duty cycle for CLKOUT3 (0.01 to 0.99)
         CLKOUT3_PHASE      => 0.0, -- Phase shift (degrees) for CLKOUT3 (0.0 to 360.0)
         CLKOUT4_DIVIDE     =>   1, -- Division factor for CLKOUT4 (1 to 128)
         CLKOUT4_DUTY_CYCLE => 0.5, -- Duty cycle for CLKOUT4 (0.01 to 0.99)
         CLKOUT4_PHASE      => 0.0, -- Phase shift (degrees) for CLKOUT4 (0.0 to 360.0)
         CLKOUT5_DIVIDE     =>   1, -- Division factor for CLKOUT5 (1 to 128)
         CLKOUT5_DUTY_CYCLE => 0.5, -- Duty cycle for CLKOUT5 (0.01 to 0.99)
         CLKOUT5_PHASE      => 0.0, -- Phase shift (degrees) for CLKOUT5 (0.0 to 360.0)
         COMPENSATION       => "SYSTEM_SYNCHRONOUS", -- "SYSTEM_SYNCHRNOUS",
                                                     -- "SOURCE_SYNCHRNOUS", "INTERNAL",
                                                     -- "EXTERNAL", "DCM2PLL", "PLL2DCM"
         DIVCLK_DIVIDE      => 1,    -- Division factor for all clocks (1 to 52)
         REF_JITTER         => 0.100 -- Input reference jitter (0.000 to 0.999 UI%)
      ) 
      port map (
         CLKFBOUT => iPllFb,     -- General output feedback signal
         CLKOUT0  => isysClkRaw, -- One of six general clock output signals
         CLKOUT1  => open,       -- One of six general clock output signals
         CLKOUT2  => open,       -- One of six general clock output signals
         CLKOUT3  => open,       -- One of six general clock output signals
         CLKOUT4  => open,       -- One of six general clock output signals
         CLKOUT5  => open,       -- One of six general clock output signals
         LOCKED   => iPllLocked, -- Active high PLL lock signal
         CLKFBIN  => iPllFb,     -- Clock feedback input
         CLKIN    => iUserClk,   -- Clock input
         RST      => iUserClkRst -- Asynchronous PLL reset
      );
   U_SysClkBufG : BUFG port map ( I => isysClkRaw, O => isysClk );
   isysClkRstRaw <= not(iPllLocked) or iUserClkRst;
      
   -- PGP Core
   U_Pgp2Gtp16: Pgp2GtpPackage.Pgp2Gtp16
      generic map ( 
         EnShortCells => 1, 
         VcInterleave => 0
      )
      port map (
         pgpClk            => ipgpClk,
         pgpClk2x          => ipgpClk2x,
         pgpReset          => ipgpClkRst,
         pgpFlush          => '0',
         pllTxRst          => '0',
         pllRxRst          => '0',
         pllRxReady        => open,
         pllTxReady        => open,
         pgpRemData        => open,
         pgpLocData        => (others=>'0'),
         pgpTxOpCodeEn     => '0',
         pgpTxOpCode       => (others=>'0'),
         pgpRxOpCodeEn     => open,
         pgpRxOpCode       => open,
         pgpLocLinkReady   => open,
         pgpRemLinkReady   => open,
         pgpRxCellError    => open,
         pgpRxLinkDown     => open,
         pgpRxLinkError    => open,
         vc0FrameTxValid   => pgpTxVcIn(0).valid,
         vc0FrameTxReady   => pgpTxVcOut(0).ready,
         vc0FrameTxSOF     => pgpTxVcIn(0).sof,
         vc0FrameTxEOF     => pgpTxVcIn(0).eof,
         vc0FrameTxEOFE    => pgpTxVcIn(0).eofe,
         vc0FrameTxData    => pgpTxVcIn(0).data(0),
         vc0LocBuffAFull   => pgpTxVcIn(0).locBuffAFull,
         vc0LocBuffFull    => pgpTxVcIn(0).locBuffFull,
         vc1FrameTxValid   => pgpTxVcIn(1).valid,
         vc1FrameTxReady   => pgpTxVcOut(1).ready,
         vc1FrameTxSOF     => pgpTxVcIn(1).sof,
         vc1FrameTxEOF     => pgpTxVcIn(1).eof,
         vc1FrameTxEOFE    => pgpTxVcIn(1).eofe,
         vc1FrameTxData    => pgpTxVcIn(1).data(0),
         vc1LocBuffAFull   => pgpTxVcIn(1).locBuffAFull,
         vc1LocBuffFull    => pgpTxVcIn(1).locBuffFull,
         vc2FrameTxValid   => pgpTxVcIn(2).valid,
         vc2FrameTxReady   => pgpTxVcOut(2).ready,
         vc2FrameTxSOF     => pgpTxVcIn(2).sof,
         vc2FrameTxEOF     => pgpTxVcIn(2).eof,
         vc2FrameTxEOFE    => pgpTxVcIn(2).eofe,
         vc2FrameTxData    => pgpTxVcIn(2).data(0),
         vc2LocBuffAFull   => pgpTxVcIn(2).locBuffAFull,
         vc2LocBuffFull    => pgpTxVcIn(2).locBuffFull,
         vc3FrameTxValid   => pgpTxVcIn(3).valid,
         vc3FrameTxReady   => pgpTxVcOut(3).ready,
         vc3FrameTxSOF     => pgpTxVcIn(3).sof,
         vc3FrameTxEOF     => pgpTxVcIn(3).eof,
         vc3FrameTxEOFE    => pgpTxVcIn(3).eofe,
         vc3FrameTxData    => pgpTxVcIn(3).data(0),
         vc3LocBuffAFull   => pgpTxVcIn(3).locBuffAFull,
         vc3LocBuffFull    => pgpTxVcIn(3).locBuffFull,
         vcFrameRxSOF      => pgpRxVcCommon.sof,
         vcFrameRxEOF      => pgpRxVcCommon.eof,
         vcFrameRxEOFE     => pgpRxVcCommon.eofe,
         vcFrameRxData     => pgpRxVcCommon.data(0),
         vc0FrameRxValid   => pgpRxVcOut(0).valid,
         vc0RemBuffAFull   => pgpRxVcOut(0).remBuffAFull,
         vc0RemBuffFull    => pgpRxVcOut(0).remBuffFull,
         vc1FrameRxValid   => pgpRxVcOut(1).valid,
         vc1RemBuffAFull   => pgpRxVcOut(1).remBuffAFull,
         vc1RemBuffFull    => pgpRxVcOut(1).remBuffFull,
         vc2FrameRxValid   => pgpRxVcOut(2).valid,
         vc2RemBuffAFull   => pgpRxVcOut(2).remBuffAFull,
         vc2RemBuffFull    => pgpRxVcOut(2).remBuffFull,
         vc3FrameRxValid   => pgpRxVcOut(3).valid,
         vc3RemBuffAFull   => pgpRxVcOut(3).remBuffAFull,
         vc3RemBuffFull    => pgpRxVcOut(3).remBuffFull,
			gtpLoopback       => '0',
         gtpClkIn          => pgpRefClk,
         gtpRefClkOut      => intRefClkOut,
         gtpRxRecClk       => open,
         gtpRxN            => pgpRxN,
         gtpRxP            => pgpRxP,
         gtpTxN            => pgpTxN,
         gtpTxP            => pgpTxP,
         debug             => open
      );

   -- Lane 0, VC0, Command processor
   U_PgpCmd : entity work.VcCmdSlave 
      generic map (
         TPD_G           => 1 ns,
         RST_ASYNC_G     => false,
         RX_LANE_G       => 0,
         DEST_ID_G       => 0,
         DEST_MASK_G     => 0,
         GEN_SYNC_FIFO_G => false,
         SYNC_STAGES_G   => 3,
         ETH_MODE_G      => false
      )
      port map (
         -- RX VC Signals (vcRxClk domain)
         vcRxOut             => pgpRxVcOut(0),
         vcRxCommonOut       => pgpRxVcCommon,
         vcTxIn_locBuffAFull => pgpTxVcIn(0).locBuffAFull,
         vcTxIn_locBuffFull  => pgpTxVcIn(0).locBuffFull,
         -- Command Signals (locClk domain)
         cmdSlaveOut         => pgpCmd,
         -- Local clock and resets
         locClk              => isysClk,
         locRst              => isysClkRst,
         -- VC Rx Clock And Resets
         vcRxClk             => ipgpClk,
         vcRxRst             => ipgpClkRst
      );

   -- Return data, Lane 0, VC0
   U_DataBuff : entity work.VcUsBuff32
      generic map (
         TPD_G              => 1 ns,
         RST_ASYNC_G        => false,
         TX_LANES_G         => 1,
         GEN_SYNC_FIFO_G    => false,
         MEMORY_TYPE_G      => "block",
         FIFO_ADDR_WIDTH_G  => 9, 
         LITTLE_ENDIAN_G    => false,
         FIFO_SYNC_STAGES_G => 3,
         FIFO_INIT_G        => "0",
         FIFO_FULL_THRES_G  => 256,  -- Almost full at 1/2 capacity
         FIFO_EMPTY_THRES_G => 1
      )
      port map (
         -- TX VC Signals (vcTxClk domain)
         vcTxIn      => pgpTxVcIn(0),
         vcTxOut     => pgpTxVcOut(0),
         vcRxOut     => pgpRxVcOut(0),
         -- UP signals  (locClk domain)
         usBuff32In  => frameTxIn,
         usBuff32Out => frameTxOut,
         -- Local clock and resets
         locClk      => isysClk,
         locRst      => isysClkRst,
         -- VC Tx Clock And Resets
         vcTxClk     => ipgpClk,
         vcTxRst     => ipgpClkRst
     ); 

   -- Lane 0, VC1, Register access control
   U_PgpReg : entity work.VcRegSlave
      generic map (
         TPD_G           => 1 ns,
         LANE_G          => 0,
         RST_ASYNC_G     => false,
         GEN_SYNC_FIFO_G => false,
         MEMORY_TYPE_G   => "block",
         SYNC_STAGES_G   => 3,
         ETH_MODE_G      => false
      )
      port map (
         -- PGP Receive Signals
         vcRxOut       => pgpRxVcOut(1),
         vcRxCommonOut => pgpRxVcCommon,
         -- PGP Transmit Signals
         vcTxIn        => pgpTxVcIn(1),
         vcTxOut       => pgpTxVcOut(1),
         -- REG Signals (locClk domain)
         regSlaveIn    => pgpRegIn,
         regSlaveOut   => pgpRegOut,
         -- Local clock and reset
         locClk        => isysClk,
         locRst        => isysClkRst,
         -- PGP Rx Clock And Reset
         vcTxClk       => ipgpClk,
         vcTxRst       => ipgpClkRst,
         -- PGP Rx Clock And Reset
         vcRxClk       => ipgpClk,
         vcRxRst       => ipgpClkRst);

   -- Lane 0, VC2, Virtual oscilloscope channel
   U_ScopeBuff : entity work.VcUsBuff32
      generic map (
         TPD_G              => 1 ns,
         RST_ASYNC_G        => false,
         TX_LANES_G         => 1,
         GEN_SYNC_FIFO_G    => false,
         MEMORY_TYPE_G      => "block",
         FIFO_ADDR_WIDTH_G  => 9, 
         LITTLE_ENDIAN_G    => false,
         FIFO_SYNC_STAGES_G => 3,
         FIFO_INIT_G        => "0",
         FIFO_FULL_THRES_G  => 256,  -- Almost full at 1/2 capacity
         FIFO_EMPTY_THRES_G => 1
      )
      port map (
         -- TX VC Signals (vcTxClk domain)
         vcTxIn      => pgpTxVcIn(2),
         vcTxOut     => pgpTxVcOut(2),
         vcRxOut     => pgpRxVcOut(2),
         -- UP signals  (locClk domain)
         usBuff32In  => scopeTxIn,
         usBuff32Out => scopeTxOut,
         -- Local clock and resets
         locClk      => isysClk,
         locRst      => isysClkRst,
         -- VC Tx Clock And Resets
         vcTxClk     => ipgpClk,
         vcTxRst     => ipgpClkRst
     ); 
   -- No corresponding receiver for VC2
   pgpTxVcIn(2).locBuffAFull  <= '0';
   pgpTxVcIn(2).locBuffFull   <= '0';
   --pgpRxVcOut(2).valid,

   -- VC3 Unused
   pgpTxVcIn(3).valid  <= '0';
   pgpTxVcIn(3).sof    <= '0';
   pgpTxVcIn(3).eof    <= '0';
   pgpTxVcIn(3).eofe   <= '0';
   pgpTxVcIn(3).data   <= (others=>(others=>'0'));
   pgpTxVcIn(3).locBuffAFull  <= '0';
   pgpTxVcIn(3).locBuffFull   <= '0';
   --pgpTxVcOut(3).ready
   --pgpRxVcOut(3).remBuffAFull
   --pgpRxVcOut(3).remBuffFull
   --pgpRxVcOut(3).valid,

end PgpFrontEnd;

