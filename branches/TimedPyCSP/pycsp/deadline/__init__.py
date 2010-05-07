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
    try: from py.magic import greenlet
    except ImportError, e: 
        sys.stderr.write("PyCSP.greenlets requires the greenlet module, recommended version is 0.2 and is\navailable from http://pypi.python.org/pypi/greenlet/.\n\n")
        raise ImportError(e)

# Set current implementation
import os
os.environ['PYCSP'] = 'DEADLINE'

# Imports
#from pycsp.greenlets.scheduling import Io, io
from scheduling import Io, io, Now, Wait, DeadlineException, Release
from guard import Timeout, Skip
from pycsp.greenlets.alternation import choice
from alternation import Alternation
from pycsp.greenlets.channel import ChannelPoisonException, ChannelRetireException
#from channel import Channel
from pycsp.greenlets.channelend import retire, poison, IN, OUT
from process import process, Process, Parallel, Spawn, Sequence, current_process_id, Set_deadline, Get_deadline, Remove_deadline


# Buffered channel will fallback to the default Channel, if not buffered.
from buffer import BufferedChannel as Channel

#from collection import Buffer
from showtree import *
version = (0,6,2, 'deadline')

def test_suite():
    import unittest
    import doctest
    import scheduling, guard, alternation, channel, process

    suite = unittest.TestSuite()
    for mod in scheduling,channel,process, guard, alternation:
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocTestSuite())
    return suite

# Run tests
if __name__ == '__main__':
    import unittest
    import test
    import test2
    suite = test_suite()
    deadlinesuite =  unittest.TestLoader().loadTestsFromTestCase(test.DeadlineTestCase)
    deadlinesuite2 = unittest.TestLoader().loadTestsFromTestCase(test2.DeadlineTestCase)
    allsuites = unittest.TestSuite([suite,deadlinesuite])

    runner = unittest.TextTestRunner(verbosity=2)
    #runner.run(suite)
    #runner.run(allsuites)
    runner.run(deadlinesuite)
    #runner.run(deadlinesuite2)
