#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP.processes implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjørndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
See LICENSE.txt for licensing details (MIT License). 
"""

# Test for multiprocessing
import sys
try: import multiprocessing
except ImportError, e:
    sys.stderr.write("PyCSP.processes requires multiprocessing support, \nwhich is available from Python 2.6+.\n\n")
    raise ImportError(e)

# Imports
from configuration import *
from guard import Skip, Timeout
from alternation import choice, Alternation
from channel import Channel, ChannelPoisonException
from channelend import retire, poison, IN, OUT, ChannelEndException
from process import io, Process, process, Sequence, Parallel, Spawn

version = (0,6,1, 'processes')

def test_suite():
    import unittest
    import doctest
    import configuration, mem, guard, alternation, channel, channelend, process

    suite = unittest.TestSuite()
    for mod in configuration, mem, guard, alternation, channel, channelend, process:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest

    suite = test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
