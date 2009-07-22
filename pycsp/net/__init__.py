#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP.net implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Handles all channel communications in a main server process. All network communication is handled by Pyro.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Test for Pyro
import sys
try: import Pyro.naming
except ImportError, e:
    sys.stderr.write("PyCSP.net requires Pyro, the latest version is\navailable from http://pyro.sourceforge.net/.\n\n")
    raise ImportError(e)


# Imports
from configuration import *
from net import Channel, Alternation
from alternation import choice
from guard import Skip, Timeout
from channel import ChannelPoisonException, ChannelRetireException
from channelend import retire, poison, IN, OUT
from process import io, Process, process, Sequence, Parallel, Spawn

version = (0,6,1, 'net')

def test_suite():
    import unittest
    import doctest
    import configuration, net, alternation, channel, channelend, process, guard

    suite = unittest.TestSuite()
    for mod in configuration, net, alternation, channel, channelend, process, guard:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest

    suite = test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

