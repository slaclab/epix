-------------------------------------------------------------------------------
-- Title      : Test-bench of CpixCore
-- Project    : Cpix Detector
-------------------------------------------------------------------------------
-- File       : TB_CpixCore.vhd
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

LIBRARY ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;
use surf.Code8b10bPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.Pgp2bPkg.all;

use work.EpixPkgGen2.all;
use work.CpixPkg.all;

library unisim;
use unisim.vcomponents.all;

entity TB_CpixCore is 

end TB_CpixCore;


-- Define architecture
architecture beh of TB_CpixCore is
   
   constant TPD_G             : time := 1 ns;
   
   signal coreClk      : std_logic;
   signal axiRst       : std_logic;
   
   signal asicRdClk     : sl;
   signal asicRdClkRst  : sl;
   signal bitClk        : sl;
   signal bitClkRst     : sl;
   signal byteClk       : sl;
   signal byteClkRst    : sl;
   signal iAsicRoClk : sl;

   signal asicDoutP           : slv(1 downto 0);
   signal asicDoutM           : slv(1 downto 0);
   
   signal sroAck     : slv(1 downto 0);
   signal sroReq     : slv(1 downto 0);
   
   
   signal asicEnA      : std_logic;
   signal asicEnB      : std_logic;
   signal asicVid      : std_logic;
   signal iAsicPpbe    : std_logic;
   signal iAsicPpmat   : std_logic;
   signal iAsicR0      : std_logic;
   signal asicSRO      : std_logic;
   signal iAsicGrst    : std_logic;
   signal iAsicSync    : std_logic;   
   signal iAsicAcq     : std_logic;   
   signal saciPrepReadoutReq     : std_logic;   
   signal saciPrepReadoutAck     : std_logic;     
   signal acqStart     : std_logic;     
   
   signal epixStatus       : EpixStatusType;
   signal epixConfig       : EpixConfigType;
   signal cpixConfig       : CpixConfigType := CPIX_CONFIG_INIT_C;
   
   constant NUMBER_OF_ASICS   : natural := 2;
   
   signal forceFrameRead   : std_logic;
   signal cntAcquisition   : std_logic_vector(31 downto 0);
   signal cntSequence      : std_logic_vector(31 downto 0);
   signal cntAReadout      : std_logic;
   signal frameReq         : std_logic;
   signal frameAck         : std_logic_vector(NUMBER_OF_ASICS-1 downto 0);
   signal frameErr         : std_logic_vector(NUMBER_OF_ASICS-1 downto 0);
   signal headerAck        : std_logic_vector(NUMBER_OF_ASICS-1 downto 0);
   signal timeoutReq       : std_logic;
   
   signal deserAxisMaster  : AxiStreamMasterArray(NUMBER_OF_ASICS-1 downto 0);
   signal lutAxisMaster    : AxiStreamMasterArray(NUMBER_OF_ASICS-1 downto 0);
   signal inSync           : slv(NUMBER_OF_ASICS-1 downto 0);
   
   signal cntFrameDone     : Slv32Array(NUMBER_OF_ASICS-1 downto 0);
   signal cntFrameError    : Slv32Array(NUMBER_OF_ASICS-1 downto 0);
   signal cntCodeError     : Slv32Array(NUMBER_OF_ASICS-1 downto 0);
   signal cntToutError     : Slv32Array(NUMBER_OF_ASICS-1 downto 0);
   signal framerAxisMaster : AxiStreamMasterArray(NUMBER_OF_ASICS-1 downto 0);
   signal framerAxisSlave  : AxiStreamSlaveArray(NUMBER_OF_ASICS-1 downto 0);
   signal pgpAxisMaster    : AxiStreamMasterType;
   signal pgpAxisSlave     : AxiStreamSlaveType;
   

   procedure cpixSerialData ( 
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
      dataClkPeriod := 2.5 ns;
      
      loop
         
         -- idle pattern
         encode8b10b (idleK, '1', disparity, dataOut, dispOut);
         disparity := dispOut;
         for i in 0 to 9 loop
            dOutP <= dataOut(i);
            dOutM <= not dataOut(i);
            wait for dataClkPeriod;
         end loop;
         encode8b10b (idleD, '0', disparity, dataOut, dispOut);
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
               dataIn := std_logic_vector(unsigned(dataIn) + 1);
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
      
   end procedure cpixSerialData ;
   

begin
   
   -- clocks and resets
   
   process
   begin
      coreClk <= '0';
      wait for 5 ns;
      coreClk <= '1';
      wait for 5 ns;
   end process;
   
   process
   begin
      asicRdClk <= '0';
      wait for 100 ns;
      asicRdClk <= '1';
      wait for 100 ns;
   end process;
   
   process
   begin
      wait for 1.8 ns;
      loop
         bitClk <= '0';
         wait for 2.5 ns;
         bitClk <= '1';
         wait for 2.5 ns;
      end loop;
   end process;
   
   process
   begin
      axiRst <= '1';
      wait for 10 ns;
      axiRst <= '0';
      wait;
   end process;
   
   process
   begin
      bitClkRst <= '1';
      wait for 5 ns;
      bitClkRst <= '0';
      wait;
   end process;
   
   process
   begin
      asicRdClkRst <= '1';
      wait for 200 ns;
      asicRdClkRst <= '0';
      wait;
   end process;
   
   
   -- process emulating cPix data out
   
   process
   begin
   
      cpixSerialData ( 
         roClk       => iAsicRoClk,
         sroReq      => sroReq(0),
         sroAck      => sroAck(0),
         dOutP       => asicDoutM(0),     -- Cpix has swapped P and M pins
         dOutM       => asicDoutP(0)
      );
      
   end process;
   
   process
   begin
   
      cpixSerialData ( 
         roClk       => iAsicRoClk,
         sroReq      => sroReq(1),
         sroAck      => sroAck(1),
         dOutP       => asicDoutM(1),     -- Cpix has swapped P and M pins
         dOutM       => asicDoutP(1)
      );
      
   end process;

   -- triggers
   
   process
   begin

      acqStart <= '0';
   
      wait for 20 us;
      
      acqStart <= '1';
      
      wait for 10 ns;
      
   end process;
   
   epixConfig.asicMask <= "0011";
   epixConfig.daqTriggerEnable <= '1';
   epixConfig.manualPinControl <= (others=>'0');
   epixStatus.acqCount <= (others=>'0');
   
   cpixConfig.cpixRunToAcq         <= std_logic_vector(to_unsigned(100, 32));
   cpixConfig.cpixR0ToAcq          <= std_logic_vector(to_unsigned(50, 32));
   cpixConfig.cpixAcqWidth         <= std_logic_vector(to_unsigned(50, 32));
   cpixConfig.cpixAcqToCnt         <= std_logic_vector(to_unsigned(100, 32));
   cpixConfig.cpixSyncWidth        <= std_logic_vector(to_unsigned(5, 32));
   cpixConfig.cpixSROWidth         <= std_logic_vector(to_unsigned(5, 32));
   cpixConfig.cpixNRuns            <= std_logic_vector(to_unsigned(8, 32));
   cpixConfig.cpixCntAnotB         <= x"0F0F0F0F";
   cpixConfig.syncMode             <= "00";
   saciPrepReadoutAck              <= '1';
   --epixConfig.manualPinControl(1)  <= '1';
   --epixConfig.manualPinControl(2)  <= '1';
   --epixConfig.asicPins(1)          <= '1';
   --epixConfig.asicPins(2)          <= '1';
   
   --DUTs

   U_BUFR : BUFR
   generic map (
      SIM_DEVICE  => "7SERIES",
      BUFR_DIVIDE => "5"
   )
   port map (
      I   => bitClk,
      O   => byteClk,
      CE  => '1',
      CLR => '0'
   );
   
   U_RdPwrUpRst : entity surf.PwrUpRst
   generic map (
      DURATION_G => 20000000,
      SIM_SPEEDUP_G => true
   )
   port map (
      clk      => byteClk,
      rstOut   => byteClkRst
   );
   
   roClkDdr_i : ODDR 
   port map ( 
      Q  => iAsicRoClk,
      C  => asicRdClk,
      CE => '1',
      D1 => '1',
      D2 => '0',
      R  => '0',
      S  => '0'
   );
   
   ------------------------------------------
   -- Common ASIC acquisition control            --
   ------------------------------------------      
   U_ASIC_Acquisition : entity work.CpixAcquisition
   generic map(
      NUMBER_OF_ASICS   => NUMBER_OF_ASICS
   )
   port map(
   
      -- global signals
      sysClk            => coreClk,
      sysClkRst         => axiRst,
   
      -- trigger
      acqStart          => acqStart,
      
      -- control/status signals (byteClk)
      cntAcquisition    => cntAcquisition,
      cntSequence       => cntSequence,
      cntAReadout       => cntAReadout,
      frameReq          => frameReq,
      frameAck          => frameAck,
      frameErr          => frameErr,
      headerAck         => headerAck,
      timeoutReq        => timeoutReq,
      
      epixConfig        => epixConfig,
      cpixConfig        => cpixConfig,
      saciReadoutReq    => saciPrepReadoutReq,
      saciReadoutAck    => saciPrepReadoutAck,
      
      -- ASICs signals
      asicEnA           => asicEnA,
      asicEnB           => asicEnB,
      asicVid           => asicVid,
      asicPPbe          => iAsicPpbe,
      asicPpmat         => iAsicPpmat,
      asicR0            => iAsicR0,
      asicSRO           => asicSRO,
      asicGlblRst       => iAsicGrst,
      asicSync          => iAsicSync,
      asicAcq           => iAsicAcq
      
   );
   
   
   G_ASIC : for i in 0 to NUMBER_OF_ASICS-1 generate  
      
      -------------------------------------------------------
      -- ASIC deserializers
      -------------------------------------------------------
      U_AsicDeser : entity work.Deserializer
      generic map (
         INVERT_SDATA_G => true
      )
      port map ( 
         bitClk         => bitClk,
         byteClk        => byteClk,
         byteClkRst     => byteClkRst,
         
         -- serial data in
         asicDoutP      => asicDoutP(i),
         asicDoutM      => asicDoutM(i),
         
         -- status
         inSync         => inSync(i),
         
         -- control
         resync         => '0',
         delay          => "00000",
         
         -- decoded data Stream Master Port (byteClk)
         mAxisMaster    => deserAxisMaster(i)
      );
      
      -------------------------------------------------------
      -- CPIX LUT ranslators
      -------------------------------------------------------
      U_CpixLUT : entity work.CpixLUT
      port map (
         sysClk         => byteClk,
         sysRst         => byteClkRst,
         
         -- input stream
         sAxisMaster    => deserAxisMaster(i),
         
         -- output stream
         mAxisMaster    => lutAxisMaster(i)
         
      );
      
      -------------------------------------------------------
      -- ASIC AXI stream framers
      -------------------------------------------------------
      U_ASIC_Framer : entity work.Framer
      generic map(
         ASIC_NUMBER_G  => std_logic_vector(to_unsigned(i, 4))
      )
      port map(
         -- global signals
         sysClk         => coreClk,
         sysRst         => axiRst,
         byteClk        => byteClk,
         byteClkRst     => byteClkRst,
         
         -- control/status signals (byteClk)
         forceFrameRead => forceFrameRead,
         cntAcquisition => cntAcquisition,
         cntSequence    => cntSequence,
         cntAReadout    => cntAReadout,
         frameReq       => frameReq     ,
         frameAck       => frameAck(i)     ,
         frameErr       => frameErr(i)     ,
         headerAck      => headerAck(i)    ,
         timeoutReq     => timeoutReq   ,
         cntFrameDone   => cntFrameDone(i) ,
         cntFrameError  => cntFrameError(i),
         cntCodeError   => cntCodeError(i) ,
         cntToutError   => cntToutError(i) ,
         cntReset       => '0',
         epixConfig     => epixConfig,
         
         -- decoded data input stream (byteClk)
         sAxisMaster    => lutAxisMaster(i),
         
         -- AXI Stream Master Port (sysClk)
         mAxisMaster    => framerAxisMaster(i),
         mAxisSlave     => framerAxisSlave(i)
      );
      
      -- start of readout handshake
      -- only for simulation procedure
      process
      begin
      
         sroReq(i) <= '0';
      
         wait until rising_edge(asicSRO);
         
         sroReq(i) <= '1';
         
         wait until rising_edge(sroAck(i));
         
      end process;
   
   end generate;
   
   -------------------------------------------------------
   -- AXI stream mux
   -------------------------------------------------------
   U_AxiStreamMux : entity surf.AxiStreamMux
   generic map(
      NUM_SLAVES_G   => NUMBER_OF_ASICS
   )
   port map(
      -- Clock and reset
      axisClk        => coreClk,
      axisRst        => axiRst,
      -- Slaves
      sAxisMasters   => framerAxisMaster,
      sAxisSlaves    => framerAxisSlave,
      -- Master
      mAxisMaster    => pgpAxisMaster,
      mAxisSlave     => pgpAxisSlave
      
   );
   
   -- only for the simulation
   pgpAxisSlave.tReady <= '1';
   
   process
   begin
   
      forceFrameRead <= '1';
   
      wait for 461568 ns;
      
      forceFrameRead <= '0';
      
      wait;
      
   end process;
   

end beh;


