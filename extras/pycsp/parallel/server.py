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
import types
import os

# Extract paramenters
cwd, ip, port, name, scriptPath, funcName = sys.argv[1:]

# Change to working dir
os.chdir(cwd)

# Load pycsp modules
from pycsp.parallel import serverresult
real_stdout = serverresult.save_stdout()
from pycsp.parallel.clusterprocess import NodePlacement
from pycsp.parallel.process import init
from pycsp.parallel import *

# Init main process
init()

# Connect to channel
chan = Channel(name, connect=(ip, int(port)))

# Retrive args, kwargs
val = chan.reader()()
if len(val) == 2:
    args, kwargs = val
else:
    # For clusterprocesses
    args, kwargs, available_nodes = val
    if available_nodes:
        nodefile, group_state = available_nodes
        NodePlacement().set_nodegroup(nodefile, group_state)


# Load script
sys.path.insert(0, os.path.dirname(scriptPath))
moduleName = os.path.basename(scriptPath)

if moduleName[-3:] == '.py':
    moduleName = moduleName[:-3]

m = __import__(moduleName)

# Run function
fn = getattr(m, funcName)

return_value = None
try:
    return_value = fn().fn(*args, **kwargs)
except ChannelPoisonException as e:
    # look for channels and channel ends
    def __check_poison(args):
        for arg in args:
            try:
                if types.ListType == type(arg) or types.TupleType == type(arg):
                    self.__check_poison(arg)
                elif types.DictType == type(arg):
                    self.__check_poison(arg.keys())
                    self.__check_poison(arg.values())
                elif type(arg.poison) == types.UnboundMethodType:
                    arg.poison()
            except AttributeError:
                pass


    __check_poison(args)
    __check_poison(kwargs.values())

except ChannelRetireException as e:
    # look for channel ends
    def __check_retire(args):
        for arg in args:
            try:
                if types.ListType == type(arg) or types.TupleType == type(arg):
                    self.__check_retire(arg)
                elif types.DictType == type(arg):
                    self.__check_retire(arg.keys())
                    self.__check_retire(arg.values())
                elif type(arg.retire) == types.UnboundMethodType:
                    # Ignore if try to retire an already retired channel end.
                    try:
                        arg.retire()
                    except ChannelRetireException:
                        pass
            except AttributeError:
                pass

    __check_retire(args)
    __check_retire(kwargs.values())
finally:

    # Output result to parallel
    serverresult.output_and_restore_stdout(return_value, real_stdout)

    # The rest of process clean up is done in shutdown
    shutdown()

