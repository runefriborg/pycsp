"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports

from pycsp.parallel.guard import Skip, SkipGuard, Timeout, TimeoutGuard
from pycsp.parallel.alternation import choice, Alternation
from pycsp.parallel.altselect import FairSelect, AltSelect, InputGuard, OutputGuard
from pycsp.parallel.channel import Channel, retire, poison
from pycsp.parallel.process import Process, process, Sequence, Parallel, Spawn, current_process_id, shutdown
from pycsp.parallel.multiprocess import MultiProcess, multiprocess
from pycsp.parallel.exceptions import ChannelRetireException, ChannelPoisonException, ChannelSocketException, FatalException, InfoException
from pycsp.parallel.configuration import *
from pycsp.parallel.compat import *

__all__ = ['Skip', 'SkipGuard', 'Timeout', 'TimeoutGuard', 'InputGuard', 'OutputGuard', 'choice', 'Alternation', 'FairSelect', 'AltSelect', 'Channel', 'retire', 'poison', 'Process', 'process', 'MultiProcess', 'multiprocess', 'Sequence', 'Parallel', 'Spawn', 'current_process_id', 'shutdown', 'ChannelRetireException', 'ChannelPoisonException', 'ChannelSocketException', 'InfoException', 'FatalException', 'io', 'Io', 'Configuration', 'SOCKETS_CONNECT_TIMEOUT', 'SOCKETS_CONNECT_RETRY_DELAY', 'SOCKETS_BIND_TIMEOUT', 'SOCKETS_BIND_RETRY_DELAY', 'PYCSP_PORT', 'PYCSP_HOST', 'SOCKETS_STRICT_MODE', 'version']

version = (0,9,0, 'parallel')

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
pycsp.current.InputGuard = InputGuard
pycsp.current.OutputGuard = OutputGuard
pycsp.current.shutdown = shutdown


def test_suite():
    import unittest
    import doctest
    import guard, alternation, channel, process

    suite = unittest.TestSuite()
    for mod in guard, alternation, channel, process:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest

    suite = test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
