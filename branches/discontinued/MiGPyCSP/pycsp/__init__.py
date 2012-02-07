#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).


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
>>> cin = c.reader()
>>> selected, msg = AltSelect( InputGuard(cin, action="print ChannelInput"), SkipGuard(action="print 42"), TimeoutGuard(seconds=1) )
42

>>> print selected # doctest:+ELLIPSIS
<threads.guard.SkipGuard instance at 0x...>

>>> cout = c.writer()
>>> _,_ = AltSelect( OutputGuard(cout, 'MSG_DATA', "print 'sent'"), TimeoutGuard(0.01, "print 'abort'") )
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
>>> Parallel(reader(c.reader()), writer(c.writer(), 10))

any-to-any channel example
>>> c = Channel('A')
>>> Parallel(reader(c.reader()), writer(c.writer(), 10),reader(c.reader()), writer(c.writer(), 10))
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




