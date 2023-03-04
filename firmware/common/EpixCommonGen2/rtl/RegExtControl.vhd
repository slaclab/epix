-------------------------------------------------------------------------------
-- File       : RegExtControl.vhd
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

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;

use work.EpixPkgGen2.all;

library unisim;
use unisim.vcomponents.all;

entity RegExtControl is
   generic (
      TPD_G             : time            := 1 ns;
      AXI_ERROR_RESP_G  : slv(1 downto 0) := AXI_RESP_OK_C;
      FPGA_BASE_CLOCK_G : slv(31 downto 0)
   );
   port (
      -- Global Signals
      axiClk         : in  sl;
      axiRst         : in  sl;
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  : in  AxiLiteReadMasterType;
      axiReadSlave   : out AxiLiteReadSlaveType;
      axiWriteMaster : in  AxiLiteWriteMasterType;
      axiWriteSlave  : out AxiLiteWriteSlaveType;
      -- Register Inputs/Outputs (axiClk domain)
      epixConfigExt  : out EpixConfigExtType;
      epixConfig     : in  EpixConfigType
   );
end RegExtControl;

architecture rtl of RegExtControl is
   
   type RegType is record
      epixRegOut        : EpixConfigExtType;
      axiReadSlave      : AxiLiteReadSlaveType;
      axiWriteSlave     : AxiLiteWriteSlaveType;
      pipelineDelayA0   : slv(31 downto 0);
      pipelineDelayA1   : slv(31 downto 0);
      pipelineDelayA2   : slv(31 downto 0);
      pipelineDelayA3   : slv(31 downto 0);
   end record RegType;
   
   constant REG_INIT_C : RegType := (
      epixRegOut        => EPIX_CONFIG_EXT_INIT_C,
      axiReadSlave      => AXI_LITE_READ_SLAVE_INIT_C,
      axiWriteSlave     => AXI_LITE_WRITE_SLAVE_INIT_C,
      pipelineDelayA0   => (others=>'0'),
      pipelineDelayA1   => (others=>'0'),
      pipelineDelayA2   => (others=>'0'),
      pipelineDelayA3   => (others=>'0')
   );

   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
   
begin

   -------------------------------
   -- Configuration Register
   -------------------------------  
   comb : process (axiReadMaster, axiRst, axiWriteMaster, r, epixConfig) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
      
   begin
      -- Latch the current value
      v := r;   
      
      -- set per bank delays when per asic delay is set
      -- this is for software backwards compatibility
      if epixConfig.pipelineDelayA0 /= r.pipelineDelayA0 then
         v.pipelineDelayA0 := epixConfig.pipelineDelayA0;
         v.epixRegOut.pipelineDelay( 0) := epixConfig.pipelineDelayA0(6 downto 0);
         v.epixRegOut.pipelineDelay( 1) := epixConfig.pipelineDelayA0(6 downto 0);
         v.epixRegOut.pipelineDelay( 2) := epixConfig.pipelineDelayA0(6 downto 0);
         v.epixRegOut.pipelineDelay(10) := epixConfig.pipelineDelayA0(6 downto 0);
      end if;
      if epixConfig.pipelineDelayA1 /= r.pipelineDelayA1 then
         v.pipelineDelayA1 := epixConfig.pipelineDelayA1;
         v.epixRegOut.pipelineDelay( 8) := epixConfig.pipelineDelayA1(6 downto 0);
         v.epixRegOut.pipelineDelay( 9) := epixConfig.pipelineDelayA1(6 downto 0);
         v.epixRegOut.pipelineDelay( 3) := epixConfig.pipelineDelayA1(6 downto 0);
         v.epixRegOut.pipelineDelay( 4) := epixConfig.pipelineDelayA1(6 downto 0);
      end if;
      if epixConfig.pipelineDelayA2 /= r.pipelineDelayA2 then
         v.pipelineDelayA2 := epixConfig.pipelineDelayA2;
         v.epixRegOut.pipelineDelay( 5) := epixConfig.pipelineDelayA2(6 downto 0);
         v.epixRegOut.pipelineDelay( 6) := epixConfig.pipelineDelayA2(6 downto 0);
         v.epixRegOut.pipelineDelay( 7) := epixConfig.pipelineDelayA2(6 downto 0);
         v.epixRegOut.pipelineDelay(15) := epixConfig.pipelineDelayA2(6 downto 0);
      end if;
      if epixConfig.pipelineDelayA3 /= r.pipelineDelayA3 then
         v.pipelineDelayA3 := epixConfig.pipelineDelayA3;
         v.epixRegOut.pipelineDelay(11) := epixConfig.pipelineDelayA3(6 downto 0);
         v.epixRegOut.pipelineDelay(12) := epixConfig.pipelineDelayA3(6 downto 0);
         v.epixRegOut.pipelineDelay(13) := epixConfig.pipelineDelayA3(6 downto 0);
         v.epixRegOut.pipelineDelay(14) := epixConfig.pipelineDelayA3(6 downto 0);
      end if;
      
      
      -- Determine the transaction type
      axiSlaveWaitTxn(regCon, axiWriteMaster, axiReadMaster, v.axiWriteSlave, v.axiReadSlave);

      -- Map out standard registers    
      axiSlaveRegister (regCon, x"000" & "00",  0, v.epixRegOut.ghostCorr);
      axiSlaveRegisterR(regCon, x"001" & "00",  0, FPGA_BASE_CLOCK_G);
      axiSlaveRegister (regCon, x"002" & "00",  0, v.epixRegOut.oversampleEn);
      axiSlaveRegister (regCon, x"003" & "00",  0, v.epixRegOut.oversampleSize);
      
      axiSlaveRegister (regCon, x"200" & "00",  0, v.epixRegOut.dbgReg);
      axiSlaveRegister (regCon, x"201" & "00",  0, v.epixRegOut.dbgReg2);
      axiSlaveRegister (regCon, x"202" & "00",  0, v.epixRegOut.injDelay);
      axiSlaveRegister (regCon, x"203" & "00",  0, v.epixRegOut.injDlyWidth);
      axiSlaveRegister (regCon, x"204" & "00",  0, v.epixRegOut.injSyncEn);
      
      axiSlaveRegister (regCon, x"C00",  0, v.epixRegOut.pipelineDelay( 0));
      axiSlaveRegister (regCon, x"C04",  0, v.epixRegOut.pipelineDelay( 1));
      axiSlaveRegister (regCon, x"C08",  0, v.epixRegOut.pipelineDelay( 2));
      axiSlaveRegister (regCon, x"C0C",  0, v.epixRegOut.pipelineDelay(10));
      axiSlaveRegister (regCon, x"C10",  0, v.epixRegOut.pipelineDelay( 4));
      axiSlaveRegister (regCon, x"C14",  0, v.epixRegOut.pipelineDelay( 3));
      axiSlaveRegister (regCon, x"C18",  0, v.epixRegOut.pipelineDelay( 9));
      axiSlaveRegister (regCon, x"C1C",  0, v.epixRegOut.pipelineDelay( 8));
      axiSlaveRegister (regCon, x"C20",  0, v.epixRegOut.pipelineDelay(15));
      axiSlaveRegister (regCon, x"C24",  0, v.epixRegOut.pipelineDelay( 7));
      axiSlaveRegister (regCon, x"C28",  0, v.epixRegOut.pipelineDelay( 6));
      axiSlaveRegister (regCon, x"C2C",  0, v.epixRegOut.pipelineDelay( 5));
      axiSlaveRegister (regCon, x"C30",  0, v.epixRegOut.pipelineDelay(11));
      axiSlaveRegister (regCon, x"C34",  0, v.epixRegOut.pipelineDelay(12));
      axiSlaveRegister (regCon, x"C38",  0, v.epixRegOut.pipelineDelay(13));
      axiSlaveRegister (regCon, x"C3C",  0, v.epixRegOut.pipelineDelay(14));
      
      
      axiSlaveDefault(regCon, v.axiWriteSlave, v.axiReadSlave, AXI_ERROR_RESP_G);
      
      -- Synchronous Reset
      if axiRst = '1' then
         v := REG_INIT_C;
      end if;

      -- Register the variable for next clock cycle
      rin <= v;

      --------------------------
      -- Outputs 
      --------------------------
      axiReadSlave   <= r.axiReadSlave;
      axiWriteSlave  <= r.axiWriteSlave;
      epixConfigExt  <= r.epixRegOut;
      
   end process comb;
   
   

   seq : process (axiClk) is
   begin
      if rising_edge(axiClk) then
         r <= rin after TPD_G;
      end if;
   end process seq;
   
end rtl;
