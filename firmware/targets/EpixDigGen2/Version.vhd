-------------------------------------------------------------------------------
-- Title         : Version File
-- Project       : PGP To PCI-E Bridge Card, 8x
-------------------------------------------------------------------------------
-- File          : PgpCard8xG2Version.vhd
-- Author        : Ryan Herbst, rherbst@slac.stanford.edu
-- Created       : 04/27/2010
-------------------------------------------------------------------------------
-- Description:
-- Version Constant Module.
-------------------------------------------------------------------------------
-- Copyright (c) 2010 by SLAC National Accelerator Laboratory. All rights reserved.
-------------------------------------------------------------------------------
-- Modification history:
-- 04/27/2010: created.
-------------------------------------------------------------------------------
LIBRARY ieee;
USE ieee.std_logic_1164.ALL;

package Version is

constant FPGA_VERSION_C : std_logic_vector(31 downto 0) := x"00010000"; -- MAKE_VERSION

constant BUILD_STAMP_C : string := "EpixDigGen2: Built Fri Dec 12 13:49:34 PST 2014 by kurtisn";

end Version;

-------------------------------------------------------------------------------
-- Revision History:
-- 07/26/2013 (0xCEC83000): Initial Build
-------------------------------------------------------------------------------

