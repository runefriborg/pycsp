#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Versions available: greenlets, threads, processes, net
Channels can not be used to communicate between versions.

Modules
> import pycsp.threads
> import pycsp.greenlets
> import pycsp.processes
> import pycsp.net

>>> @process
... def P():
...     pass

>>> @io
... def IO():
...     pass

>>> c = Channel('B')
>>> cin = IN(c)
>>> alt = Alternation([{cin:"print ChannelInput", Skip():"print 42", Timeout(1):None}])
>>> alt.select() # doctest:+ELLIPSIS
(<threads.guard.Skip instance at 0x...>, None)

>>> alt.execute()
42

>>> cout = OUT(c)
>>> alt = Alternation([{(cout, 'MSG_DATA'):"print 'sent'", Timeout(0.01):"print 'abort'"}])
>>> alt.execute()
abort

>>> retire(cout)

>>> cout('FAIL')
Traceback (most recent call last):
ChannelRetireException

>>> FAIL = cin()
Traceback (most recent call last):
ChannelRetireException


A reader process
>>> @process
... def reader(cin):
...     while True: cin()

A writer process
>>> @process
... def writer(cout, cnt):
...     for i in range(cnt): cout(i)
...     retire(cout)

1-to-1 channel example
>>> c = Channel('A')
>>> Parallel(reader(IN(c)), writer(OUT(c), 10))

any-to-any channel example
>>> c = Channel('A')
>>> Parallel(reader(IN(c)), writer(OUT(c), 10),reader(IN(c)), writer(OUT(c), 10))

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Import threads version
from threads import *

# Run tests
if __name__ == '__main__':
    import sys
    import unittest
    import doctest
    mods = []

    try:
        import greenlets
        mods.append(greenlets)
    except ImportError:
        print "Skipping doctest for greenlets"
        print

    try:
        if sys.platform == 'win32':
            print "Skipping doctest for processes"
            print
        else:
            import processes
            mods.append(processes)
    except ImportError:
        print "Skipping doctest for processes"
        print

    try:
        import net
        mods.append(net)
    except ImportError:
        print "Skipping doctest for net"
        print

    import threads
    mods.append(threads)

    suite = unittest.TestSuite()
    for mod in mods:
        suite.addTest(mod.test_suite())
    suite.addTest(doctest.DocTestSuite())
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)




