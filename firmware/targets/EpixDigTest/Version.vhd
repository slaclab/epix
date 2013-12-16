-------------------------------------------------------------------------------
-- Title         : Version Constant File
-- Project       : COB Zynq DTM
-------------------------------------------------------------------------------
-- File          : Version.vhd
-- Author        : Ryan Herbst, rherbst@slac.stanford.edu
-- Created       : 05/07/2013
-------------------------------------------------------------------------------
-- Description:
-- Version Constant Module
-------------------------------------------------------------------------------
-- Copyright (c) 2012 by SLAC. All rights reserved.
-------------------------------------------------------------------------------
LIBRARY ieee;
USE ieee.std_logic_1164.ALL;

package Version is

constant FpgaVersion : std_logic_vector(31 downto 0) := x"E0000008"; -- MAKE_VERSION
constant FpgaBaseClock : std_logic_vector(31 downto 0) := x"00" & x"125000";  
-- FPGA base clock (used for calculating various delay units)
-- Top two nybbles reserved
-- Bottom 6 nybbles are base clock rate in kHz (binary coded decimal)

end Version;

-------------------------------------------------------------------------------
-- Revision History:
--            (0xE0000004): Version used for original ASIC characterization.
-- 11/05/2013 (0xE0000005): First version that supports "final" readout format.
-- 11/15/2013 (0xE0000006): Added "BaseClock" register at 0x000010.  Turned off 
--                          DAC SPI clock when not in use to reduce ADC noise.
-- 12/03/2013 (0xE0000007): Modified trig_out behavior so something is still 
--                          sent out when in ADC stream mode.
-- 12/16/2013 (0xE0000008): Modified readout control for SSRL ePix test.
--                          Words 1 and 2 of the "TPS" data now come from
--                          the slow ADC thermistor channels rather than ASICs. 
-------------------------------------------------------------------------------

