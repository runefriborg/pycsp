#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP.net implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Handles all channel communications in a main server process. All network communication is handled by Pyro.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
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

# Test for Pyro
import sys
try: import Pyro.naming
except ImportError, e:
    sys.stderr.write("PyCSP.net requires Pyro, the latest version is\navailable from http://pyro.sourceforge.net/.\n\n")
    raise ImportError(e)

# Set current implementation
import os
os.environ['PYCSP'] = 'NET'

# Imports
from configuration import *
from net import Alternation, AltSelect, InputGuard, OutputGuard
from alternation import choice
from guard import Skip, Timeout, SkipGuard, TimeoutGuard
from channel import ChannelPoisonException, ChannelRetireException
from channelend import retire, poison, IN, OUT
from process import io, Process, process, Sequence, Parallel, Spawn, current_process_id

# Buffered channel will fallback to the default Channel, if not buffered.
from buffer import BufferedChannel as Channel

version = (0,7,0, 'net')

def test_suite():
    import unittest
    import doctest
    import configuration, net, alternation, channel, channelend, process, guard, buffer

    suite = unittest.TestSuite()
    for mod in configuration, net, alternation, channel, channelend, process, guard, buffer:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest

    suite = test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

