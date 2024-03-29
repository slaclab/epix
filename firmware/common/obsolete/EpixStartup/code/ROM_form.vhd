ROM_form.vhd

Ken Chapman (Xilinx Ltd) 2nd January 2007

This is the VHDL template file for the KCPSM3 assembler.
It is used to configure a Spartan-3 generation, Virtex-II or Virtex-IIPRO block RAM to act as 
a single port program ROM.

This VHDL file is not valid as input directly into a synthesis or simulation tool.
The assembler will read this template and insert the data required to complete the 
definition of program ROM and write it out to a new '.vhd' file associated with the 
name of the original '.psm' file being assembled.

This template can be modified to define alternative memory definitions such as dual port.
However, you are responsible for ensuring the template is correct as the assembler does 
not perform any checking of the VHDL.

The assembler identifies all text enclosed by {} characters, and replaces these
character strings. All templates should include these {} character strings for 
the assembler to work correctly. 

****************************************************************************************
	
This template defines a block RAM configured in 1024 x 18-bit single port mode and 
connected to act as a single port ROM.

****************************************************************************************

The next line is used to determine where the template actually starts and must exist.
{begin template}
--
-- Definition of a single port ROM for KCPSM3 program defined by {name}.psm
--
-- Generated by KCPSM3 Assembler {timestamp}. 
--
-- Standard IEEE libraries
--
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
--
-- The Unisim Library is used to define Xilinx primitives. It is also used during
-- simulation. The source can be viewed at %XILINX%\vhdl\src\unisims\unisim_VCOMP.vhd
--  
library unisim;
use unisim.vcomponents.all;
--
--
entity {name} is
    Port (      address : in std_logic_vector(9 downto 0);
            instruction : out std_logic_vector(17 downto 0);
                    clk : in std_logic);
    end {name};
--
architecture low_level_definition of {name} is
--
begin
--
  --Instantiate the Xilinx primitive for a block RAM
  ram_1024_x_18: RAMB16_S18
  generic map ( INIT_00 => X"{INIT_00}",
                INIT_01 => X"{INIT_01}",
                INIT_02 => X"{INIT_02}",
                INIT_03 => X"{INIT_03}",
                INIT_04 => X"{INIT_04}",
                INIT_05 => X"{INIT_05}",
                INIT_06 => X"{INIT_06}",
                INIT_07 => X"{INIT_07}",
                INIT_08 => X"{INIT_08}",
                INIT_09 => X"{INIT_09}",
                INIT_0A => X"{INIT_0A}",
                INIT_0B => X"{INIT_0B}",
                INIT_0C => X"{INIT_0C}",
                INIT_0D => X"{INIT_0D}",
                INIT_0E => X"{INIT_0E}",
                INIT_0F => X"{INIT_0F}",
                INIT_10 => X"{INIT_10}",
                INIT_11 => X"{INIT_11}",
                INIT_12 => X"{INIT_12}",
                INIT_13 => X"{INIT_13}",
                INIT_14 => X"{INIT_14}",
                INIT_15 => X"{INIT_15}",
                INIT_16 => X"{INIT_16}",
                INIT_17 => X"{INIT_17}",
                INIT_18 => X"{INIT_18}",
                INIT_19 => X"{INIT_19}",
                INIT_1A => X"{INIT_1A}",
                INIT_1B => X"{INIT_1B}",
                INIT_1C => X"{INIT_1C}",
                INIT_1D => X"{INIT_1D}",
                INIT_1E => X"{INIT_1E}",
                INIT_1F => X"{INIT_1F}",
                INIT_20 => X"{INIT_20}",
                INIT_21 => X"{INIT_21}",
                INIT_22 => X"{INIT_22}",
                INIT_23 => X"{INIT_23}",
                INIT_24 => X"{INIT_24}",
                INIT_25 => X"{INIT_25}",
                INIT_26 => X"{INIT_26}",
                INIT_27 => X"{INIT_27}",
                INIT_28 => X"{INIT_28}",
                INIT_29 => X"{INIT_29}",
                INIT_2A => X"{INIT_2A}",
                INIT_2B => X"{INIT_2B}",
                INIT_2C => X"{INIT_2C}",
                INIT_2D => X"{INIT_2D}",
                INIT_2E => X"{INIT_2E}",
                INIT_2F => X"{INIT_2F}",
                INIT_30 => X"{INIT_30}",
                INIT_31 => X"{INIT_31}",
                INIT_32 => X"{INIT_32}",
                INIT_33 => X"{INIT_33}",
                INIT_34 => X"{INIT_34}",
                INIT_35 => X"{INIT_35}",
                INIT_36 => X"{INIT_36}",
                INIT_37 => X"{INIT_37}",
                INIT_38 => X"{INIT_38}",
                INIT_39 => X"{INIT_39}",
                INIT_3A => X"{INIT_3A}",
                INIT_3B => X"{INIT_3B}",
                INIT_3C => X"{INIT_3C}",
                INIT_3D => X"{INIT_3D}",
                INIT_3E => X"{INIT_3E}",
                INIT_3F => X"{INIT_3F}",    
               INITP_00 => X"{INITP_00}",
               INITP_01 => X"{INITP_01}",
               INITP_02 => X"{INITP_02}",
               INITP_03 => X"{INITP_03}",
               INITP_04 => X"{INITP_04}",
               INITP_05 => X"{INITP_05}",
               INITP_06 => X"{INITP_06}",
               INITP_07 => X"{INITP_07}")
  port map(    DI => "0000000000000000",
              DIP => "00",
               EN => '1',
               WE => '0',
              SSR => '0',
              CLK => clk,
             ADDR => address,
               DO => instruction(15 downto 0),
              DOP => instruction(17 downto 16)); 
--
end low_level_definition;
--
------------------------------------------------------------------------------------
--
-- END OF FILE {name}.vhd
--
------------------------------------------------------------------------------------

