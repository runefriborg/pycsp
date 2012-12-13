#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP.greenlets implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjørndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Test for Greenlets
import sys
try: from greenlet import greenlet
except ImportError, e:
    try: from py.magic import greenlet
    except ImportError, e: 
        sys.stderr.write("PyCSP.greenlets requires the greenlet module, recommended version is 0.2 and is\navailable from http://pypi.python.org/pypi/greenlet/.\n\n")
        raise ImportError(e)

# Imports
from scheduling import Io, io
from guard import Skip, Timeout, SkipGuard, TimeoutGuard
from alternation import choice, Alternation
from altselect import FairSelect, AltSelect, InputGuard, OutputGuard
from channel import Channel
from channelend import retire, poison
from process import Process, process, Sequence, Parallel, Spawn, current_process_id
from exceptions import ChannelPoisonException, ChannelRetireException, FatalException, InfoException
from compat import *

__all__ = ['Skip', 'SkipGuard', 'Timeout', 'TimeoutGuard', 'InputGuard', 'OutputGuard', 'choice', 'Alternation', 'FairSelect', 'AltSelect', 'Channel', 'retire', 'poison', 'Process', 'process', 'MultiProcess', 'multiprocess', 'Sequence', 'Parallel', 'Spawn', 'current_process_id', 'shutdown', 'ChannelRetireException', 'ChannelPoisonException', 'ChannelSocketException', 'InfoException', 'FatalException', 'io', 'Io', 'Configuration', 'SOCKETS_CONNECT_TIMEOUT', 'SOCKETS_CONNECT_RETRY_DELAY', 'SOCKETS_BIND_TIMEOUT', 'SOCKETS_BIND_RETRY_DELAY', 'PYCSP_PORT', 'PYCSP_HOST', 'SOCKETS_STRICT_MODE', 'version']

version = (0,9,0, 'greenlets')

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
pycsp.current.InputGuard = InputGuard
pycsp.current.OutputGuard = OutputGuard
pycsp.current.shutdown = shutdown

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
