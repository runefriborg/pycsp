"""
process delegator service

Must be executable by
python -m pycsp.parallel.server

Used to handle the creation of external processes (sshprocess / clusterprocess)

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""


import sys
import os

# Extract paramenters
cwd, ip, port, input_name  = sys.argv[1:]

# Change to working dir
os.chdir(cwd)

# Load pycsp modules
from pycsp.parallel.clusterprocess import NodePlacement
from pycsp.parallel.process import init
from pycsp.parallel import *

# Init main process
init()


# Connect to channel
input_chan = Channel(input_name, connect=(ip, int(port)))

# Get channel ends
input_chan_end = input_chan.reader()


# PyCSP MultiProcess (Spawn)
def RunFunc(output_chan_name, fn, args, kwargs):
    output_chan = Channel(output_chan_name, connect=(ip, int(port)))
    send_return_value = output_chan.writer()

    val = Parallel(Process(fn, *args, **kwargs))

    send_return_value(val[0])
                   
try:
    while True:
        
        # Retrive args, kwargs
        val = input_chan_end()
        if len(val) == 7:
            h, p, output_chan_name, scriptPath, funcName, args, kwargs = val
        else:
            # For clusterprocesses
            h, p, output_chan_name, scriptPath, funcName, args, kwargs, available_nodes = val
            if available_nodes:
                nodefile, group_state = available_nodes
                NodePlacement().set_nodegroup(nodefile, group_state)
        
        # Load script
        sys.path.insert(0, os.path.dirname(scriptPath))
        moduleName = os.path.basename(scriptPath)

        if moduleName[-3:] == '.py':
            moduleName = moduleName[:-3]

        m = __import__(moduleName)

        # Get function by
        #  1. retrieve process factory function. 
        #  2. generate process from process factory
        #  3. Fetch function from generated process
        fn = getattr(m, funcName)().fn

        # Spawn a runner
        Spawn(MultiProcess(RunFunc, output_chan_name, fn, args, kwargs), pycsp_host=h, pycsp_port=p)

except ChannelPoisonException:
    pass

# The rest of process clean up is done in shutdown
shutdown()

