"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports

from guard import Skip, SkipGuard, Timeout, TimeoutGuard
from alternation import choice, Alternation
from altselect import FairSelect, AltSelect, InputGuard, OutputGuard
from channel import Channel, retire, poison
from process import Process, process, Sequence, Parallel, Spawn, current_process_id, init, shutdown
from multiprocess import MultiProcess, multiprocess
from exceptions import ChannelRetireException, ChannelPoisonException, ChannelSocketException, FatalException
from configuration import *
from compat import *

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
pycsp.current.retire = retire
pycsp.current.poison = poison
pycsp.current.IN = IN
pycsp.current.OUT = OUT
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


def test_suite():
    import unittest
    import doctest
    import scheduling, guard, alternation, channel, channelend, process, buffer

    suite = unittest.TestSuite()
    for mod in scheduling, guard, alternation, channel, channelend, process, buffer:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest

    suite = test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
