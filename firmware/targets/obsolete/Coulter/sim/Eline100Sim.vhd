-------------------------------------------------------------------------------
-- File       : ELine100Sim.vhd
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

use work.ELine100Pkg.all;

entity ELine100Sim is

   generic (
      TPD_G            : time := 1 ns;
      ANALOG_LATENCY_G : time := 2 ns);
   port (
      -- Analog readout interface
      rstN : in  sl;                    -- ELINE_RESET_L
      scP  : in  sl;
      scM  : in  sl;
      mckP : in  sl;
      mckM : in  sl;
      dOut : out slv(5 downto 0)       := (others => '0');
      aOut : out RealArray(5 downto 0) := (others => 0.0);
      -- ELINE100 configuration interface
      sclk : in  sl;                    -- SCLK
      sdi  : in  sl;                    -- SDI
      sdo  : out sl;                    -- SDO
      sen  : in  sl;                    -- SR_ENA
      rw   : in  sl);                   -- RD/WR

end entity ELine100Sim;

architecture rtl of ELine100Sim is

   -- Configuration registers
   signal shiftReg        : slv(ELINE_100_CFG_SHIFT_SIZE_C-1 downto 0) := (others => '0');
   signal shiftRegLatched : slv(ELINE_100_CFG_SHIFT_SIZE_C-1 downto 0) := (others => '0');

   -- Analog signals
   type Real6x16Array is array (5 downto 0) of RealArray(15 downto 0);
   signal pixels : Real6x16Array := (others => (others => 0.0));
   signal muxSel : integer       := 0;

begin

   -------------------------------------------------------------------------------------------------
   -- Configuration logic
   -------------------------------------------------------------------------------------------------
   sdo <= shiftReg(0) when sen = '1' else '0';

   SPI : process (sclk, rstN) is
   begin
      if (rstN = '0') then
         shiftReg <= (others => '0') after TPD_G;
      elsif (falling_edge(sclk)) then
         if (sen = '1' and rw = '1') then
            shiftReg <= sdi & shiftReg(ELINE_100_CFG_SHIFT_SIZE_C-1 downto 1) after TPD_G;
         elsif (sen = '1' and rw = '0') then
            shiftReg <= shiftRegLatched after TPD_G;
         end if;
      end if;
   end process SPI;

   LATCH : process (sen) is
   begin
      if (rstN = '0') then
         shiftRegLatched <= (others => '0') after TPD_G;
      elsif (falling_edge(sen)) then
         shiftRegLatched <= shiftReg after TPD_G;
      end if;
   end process LATCH;

   ANALOG_MUX : process (mckP, scP) is
   begin
      if (rstN = '0') then
         muxSel <= 0;
         aOut   <= (others => 0.0);
      elsif (rising_edge(scP)) then
         muxSel <= 0;
         aOut   <= (others => 0.0);
      elsif (rising_edge(mckP)) then
         for i in 5 downto 0 loop
            aOut(i) <= pixels(i)(muxSel) after ANALOG_LATENCY_G;
         end loop;
         if (muxSel = 15) then
            muxSel <= 0;
         else
            muxSel <= muxSel + 1;
         end if;
      end if;
   end process ANALOG_MUX;

   PIXEL_VALS_I : for i in 6 downto 1 generate
      PIXEL_VALS_J : for j in 16 downto 1 generate
         pixels(i-1)(j-1) <= (i * 0.1) + (j * 0.01);
      end generate PIXEL_VALS_J;
   end generate PIXEL_VALS_I;

end architecture rtl;
