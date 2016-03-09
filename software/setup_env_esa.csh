# Template setup_env.csh script. You should make a copy of this and 
# rename it to setup_env.csh after checkout

# Base directory
setenv BASE ${PWD}

# Python search path, uncomment to compile python script support
setenv PYTHONPATH ${BASE}/python/lib64/python/

# Setup path
if ($?PATH) then
   setenv PATH ${BASE}/bin:${PATH}
else
   setenv PATH ${BASE}/bin
endif

