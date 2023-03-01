#export GIT_BYPASS = 0

# # Use the PGPv3 3G core
# export INCLUDE_PGP3_3G = 1

# Define target output
target: prom

# Define target part
export PRJ_PART = XC7A200TSBG484-3

# Define Firmware Version Number
export PRJ_VERSION = 0xCALDEBUG

# Define the Microblaze source path
export SDK_SRC_PATH = $(PROJ_DIR)/../../common/EpixCommonGen2/src/ePix100a

# Use top level makefile
include ../../submodules/ruckus/system_vivado.mk


#-- 02/02/2018 (0xE2030004): Added one more AXIL corssbar and extended registers module to fix the timing issues
#--                          The register map was changed but the region mapped by the LCLS DAQ was not touched
