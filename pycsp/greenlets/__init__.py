"""
PyCSP.greenlets implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Test for Greenlets
import sys
try: from greenlet import greenlet
except ImportError as e:
    try: from py.magic import greenlet
    except ImportError as e: 
        sys.stderr.write("PyCSP.greenlets requires the greenlet module, recommended version is 0.2 or above and is\navailable from http://pypi.python.org/pypi/greenlet/.\n\n")
        raise ImportError(e)

# Imports
from pycsp.greenlets.scheduling import Io, io
from pycsp.greenlets.guard import Skip, Timeout, SkipGuard, TimeoutGuard
from pycsp.greenlets.alternation import choice, Alternation
from pycsp.greenlets.altselect import FairSelect, AltSelect, PriSelect, InputGuard, OutputGuard
from pycsp.greenlets.channel import Channel
from pycsp.greenlets.channelend import retire, poison
from pycsp.greenlets.process import Process, process, Sequence, Parallel, Spawn, current_process_id
from pycsp.greenlets.exceptions import ChannelPoisonException, ChannelRetireException, FatalException, InfoException
from pycsp.greenlets.compat import *

__all__ = ['Skip', 'SkipGuard', 'Timeout', 'TimeoutGuard', 'InputGuard', 'OutputGuard', 'choice', 'Alternation', 'FairSelect', 'AltSelect', 'PriSelect', 'Channel', 'retire', 'poison', 'Process', 'process', 'MultiProcess', 'multiprocess', 'ClusterProcess', 'clusterprocess', 'SSHProcess', 'sshprocess', 'Sequence', 'Parallel', 'Spawn', 'current_process_id', 'shutdown', 'ChannelRetireException', 'ChannelPoisonException', 'ChannelSocketException', 'InfoException', 'FatalException', 'io', 'Io', 'Configuration', 'SOCKETS_CONNECT_TIMEOUT', 'SOCKETS_CONNECT_RETRY_DELAY', 'SOCKETS_BIND_TIMEOUT', 'SOCKETS_BIND_RETRY_DELAY', 'PYCSP_PORT', 'PYCSP_HOST', 'SOCKETS_STRICT_MODE', 'version']

version = (0,9,2, 'greenlets')

# Set current implementation
import pycsp.current
pycsp.current.version = version
pycsp.current.trace = False

pycsp.current.Skip = Skip
pycsp.current.Timeout = Timeout
pycsp.current.SkipGuard = SkipGuard
pycsp.current.TimeoutGuard = TimeoutGuard
pycsp.current.choice = choice
pycsp.current.Alternation = Alternation
pycsp.current.Channel = Channel
pycsp.current.ChannelPoisonException = ChannelPoisonException
pycsp.current.ChannelRetireException = ChannelRetireException
pycsp.current.ChannelSocketException = ChannelSocketException
pycsp.current.FatalException = FatalException
pycsp.current.InfoException = InfoException
pycsp.current.retire = retire
pycsp.current.poison = poison
pycsp.current.io = io
pycsp.current.Process = Process
pycsp.current.process = process
pycsp.current.Sequence = Sequence
pycsp.current.Parallel = Parallel
pycsp.current.Spawn = Spawn
pycsp.current.current_process_id = current_process_id
pycsp.current.FairSelect = FairSelect
pycsp.current.AltSelect = AltSelect
pycsp.current.PriSelect = PriSelect
pycsp.current.InputGuard = InputGuard
pycsp.current.OutputGuard = OutputGuard
pycsp.current.shutdown = shutdown
