#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP.greenlets implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjørndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
See LICENSE.txt for licensing details (MIT License). 
"""

# Test for Greenlets
import sys
try: from greenlet import greenlet
except ImportError, e:
    sys.stderr.write("PyCSP.greenlets requires the greenlet module, recommended version is 0.2 and is\navailable from http://pypi.python.org/pypi/greenlet/.\n\n")
    raise ImportError(e)

# Imports
from scheduling import Io, io
from guard import Skip, Timeout
from alternation import choice, Alternation
from channel import Channel, ChannelPoisonException
from channelend import retire, poison, IN, OUT, ChannelEndException
from process import Process, process, Sequence, Parallel, Spawn

version = (0,6,1, 'greenlets')

def test_suite():
    import unittest
    import doctest
    import scheduling, guard, alternation, channel, channelend, process

    suite = unittest.TestSuite()
    for mod in scheduling, guard, alternation, channel, channelend, process:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest

    suite = test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
