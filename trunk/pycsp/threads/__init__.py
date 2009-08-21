#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 

"""

# Imports
from guard import Skip, Timeout
from alternation import choice, Alternation
from channel import Channel, ChannelPoisonException, ChannelRetireException
from channelend import retire, poison, IN, OUT
from process import io, Process, process, Sequence, Parallel, Spawn

version = (0,6,2, 'threads')

def test_suite():
    import unittest
    import doctest
    import alternation, channel, channelend, process, guard

    suite = unittest.TestSuite()
    for mod in alternation, channel, channelend, process, guard:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest

    suite = test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

