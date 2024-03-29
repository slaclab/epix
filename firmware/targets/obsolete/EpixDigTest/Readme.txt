
The Makefile in this directory may be used to build
this project with a simple 'gmake' command. 

The Version.vhd file in this directory is used to 
generate the software readable version constant 
in the build and is also used to set the name of 
the files added to the images directory.

The following sub directories exist in this project:

config:
   This directory contains Xilinx configuration files for
   various steps in the synthesis process. The files in this
   directory include:

      bitgen_options.txt:   Options for bitgen
      map_options.txt:      Options for map 
      ngdbuild_options.txt: Options for ngdbuild
      par_options.txt:      Options for par
      trce_options.txt:     Options for trce
      xst_options.txt:      Options for xst
      sources.txt           Source file list used by xst
      smart_options:        Options for smart explorer
      smart_hosts:          Host name list for smart explorer

coregen:
   This directory holds the coregen project and any modules
   generated by coregen that are specific to this project. 

hdl:
   This directory contains the source files (.vhd and .v) for
   the project and the constraints file (.ucf) for the project.
   The top level module name, its source file name and the ucf
   file name should match the name of the project.

images:

   This directory contains the result of the project compile. 
   The resulting .mcs and .bit files for the project are 
   added to this directory. The name of the copied file will
   be: project_version.mcs/.bit.

