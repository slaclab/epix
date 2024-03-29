# Load RUCKUS environment and library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Check for version 2017.2 of Vivado (or later)
if { [VersionCheck 2017.2] < 0 } {exit -1}

# Check if required variables exist
if { [info exists ::env(BUILD_MIG_CORE)] != 1 } {
   puts "\n\nERROR: BUILD_MIG_CORE is not defined in $::env(PROJ_DIR)/Makefile\n\n"; exit -1
}

if { [info exists ::env(BUILD_MB_CORE)] != 1 } {
   puts "\n\nERROR: BUILD_MB_CORE is not defined in $::env(PROJ_DIR)/Makefile\n\n"; exit -1
}

if { [info exists ::env(PROM_FSBL)] != 1 } {
   puts "\n\nERROR: PROM_FSBL is not defined in $::env(PROJ_DIR)/Makefile\n\n"; exit -1
}

# Load Source Code
loadSource -dir "$::DIR_PATH/rtl"
# loadSource -sim_only -dir "$::DIR_PATH/tb/"

loadSource -path "$::DIR_PATH/ip/SysMonCore/SysMonCore.dcp"
# loadIpCore -path "$::DIR_PATH/ip/SysMonCore/SysMonCore.xci"

#loadSource -path "$::DIR_PATH/ip/AxisFifo32k64b/axis_32k_64b_fifo.dcp"
#loadIpCore -path "$::DIR_PATH/ip/AxisFifo32k64b/axis_32k_64b_fifo.xci"
#loadSource -path "$::DIR_PATH/ip/AxisFifo32k64b/AxisFifo32k64b.vhd"

# Load Constraints
loadConstraints -path "$::DIR_PATH/ip/MigCore/MigCorePinout.xdc" 
loadSource      -path "$::DIR_PATH/ip/AxiInterconnnect/AxiIcWrapper.vhd"

# Check if building MIG Core
if { $::env(BUILD_MIG_CORE)  != 0 } {
   # Load Source Code and Constraints
   ##loadSource -path "$::DIR_PATH/ip/AxiInterconnnect/AxiInterconnect.dcp"
   loadIpCore      -path "$::DIR_PATH/ip/AxiInterconnnect/AxiInterconnect.xci"
   loadSource      -path "$::DIR_PATH/ip/MigCore/MigCoreWrapper.vhd"
   loadConstraints -path "$::DIR_PATH/ip/MigCore/MigCoreWrapper.xdc" 
   # Check for no Application Microblaze build (MIG core only)
   if { $::env(BUILD_MB_CORE)  == 0 } {

      # Add the pre-built .DCP file 
      # loadSource -path "$::DIR_PATH/ip/MigCore/MigCore.dcp"
      loadIpCore -path "$::DIR_PATH/ip/MigCore/MigCore.xci"
      
      ## Add the Microblaze Calibration Code
      add_files -norecurse $::DIR_PATH/ip/MigCore/MigCoreMicroblazeCalibration.elf
      set_property SCOPED_TO_REF   {MigCore}                                                  [get_files -all -of_objects [get_fileset sources_1] {MigCoreMicroblazeCalibration.elf}]
      set_property SCOPED_TO_CELLS {inst/u_ddr4_mem_intfc/u_ddr_cal_riu/mcs0/U0/microblaze_I} [get_files -all -of_objects [get_fileset sources_1] {MigCoreMicroblazeCalibration.elf}]

      ## Add the Microblaze block memory mapping
      add_files -norecurse $::DIR_PATH/ip/MigCore/MigCoreMicroblazeCalibration.bmm
      set_property SCOPED_TO_REF   {MigCore}                                     [get_files -all -of_objects [get_fileset sources_1] {MigCoreMicroblazeCalibration.bmm}]
      set_property SCOPED_TO_CELLS {inst/u_ddr4_mem_intfc/u_ddr_cal_riu/mcs0/U0} [get_files -all -of_objects [get_fileset sources_1] {MigCoreMicroblazeCalibration.bmm}]
      
   } else {
      # Add the IP core
      loadIpCore -path "$::DIR_PATH/ip/MigCore/MigCore.xci"
   }
} else {
   # Load Source Code and Constraints
   loadSource      -path "$::DIR_PATH/ip/MigCore/MigCoreBypass.vhd"
   loadConstraints -path "$::DIR_PATH/ip/MigCore/MigCoreBypass.xdc" 
}

# Check if building not building Microblaze Core
if { $::env(BUILD_MB_CORE)  == 0 } {
   # Remove the surf MB core
   remove_files  [get_files {MicroblazeBasicCore.bd}]
   remove_files  [get_files {MicroblazeBasicCoreWrapper.vhd}]
   # Add dummy source code
   loadSource -path "$::DIR_PATH/ip/MicroblazeBasicCoreBypass.vhd"
}

## Place and Route strategies 
set_property strategy Performance_Explore [get_runs impl_1]
set_property STEPS.OPT_DESIGN.ARGS.DIRECTIVE Explore [get_runs impl_1]

## Skip the utilization check during placement
set_param place.skipUtilizationCheck 1