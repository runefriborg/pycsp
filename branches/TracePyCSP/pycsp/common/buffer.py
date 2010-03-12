"""
BufferedChannel implementation.

Automatically instantiated if buffer argument is used.

A = Channel(buffer=10)

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


import os, sys

# Detect current PYCSP version and import
# Default import is pycsp.threads

PYCSP = 'THREADS'
if os.environ.has_key('PYCSP'):
    if os.environ['PYCSP'] == 'PROCESSES':
        PYCSP = 'PROCESSES'
        import pycsp.processes as pycsp
    elif os.environ['PYCSP'] == 'GREENLETS':
        PYCSP = 'GREENLETS'
        import pycsp.greenlets as pycsp
    elif os.environ['PYCSP'] == 'NET':
        PYCSP = 'NET'
        import pycsp.net as pycsp
    elif os.environ['PYCSP'] == 'THREADS':
        import pycsp.threads as pycsp
else:
    import pycsp.threads as pycsp

if os.environ.has_key('PYCSP_TRACE'):
    from pycsp.common import trace as pycsp

from collections import deque
import time, random


class BufferedChannel:
    """ Channel class.
    Blocking or buffered communication.
    
    >>> from pycsp import *

    >>> @process
    ... def P1(cout):
    ...     while True:
    ...         cout('Hello World')

    >>> C = Channel()
    >>> Spawn(P1(OUT(C)))
    
    >>> cin = IN(C)
    >>> cin()
    'Hello World'

    >>> retire(cin)

    Buffered channels are semantically equivalent with a chain
    of forwarding processes.
    >>> B = Channel(buffer=5)
    >>> cout = OUT(B)
    >>> for i in range(5):
    ...     cout(i)

    Poison and retire are attached to final element of the buffer.
    >>> poison(cout)

    >>> @process
    ... def sink(cin, L):
    ...     while True:
    ...         L.append(cin())

    >>> L = []
    >>> Parallel(sink(IN(B), L))
    >>> L
    [0, 1, 2, 3, 4]
    """
    def __init__(self, name=None, buffer=1):
        if name == None:
            # Create unique name
            name = str(random.random())+str(time.time())

        self.name = name
        self.__inChan = pycsp.Channel(name=name+'inChan')
        self.__outChan = pycsp.Channel(name=name+'outChan')
        self.__bufferProcess = self.Buffer(self.__inChan.reader(),
                                       self.__outChan.writer(),
                                       N=buffer)

        # Retrieve channel ends
        self.reader = self.__outChan.reader
        self.writer = self.__inChan.writer

        # Set buffer process as deamon to allow kill if mother process
        # exists.
        if PYCSP != 'GREENLETS':
            self.__bufferProcess.daemon = True

        # Start buffer process        
        pycsp.Spawn(self.__bufferProcess)

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def poison(self):
        self.__inChan.poison()
        self.__outChan.poison()

    @pycsp.process
    def Buffer(self, cin, cout, N):
        queue = deque()
        poisoned = False
        retired = False
        while True:
            try:
                if os.environ.has_key('PYCSP_TRACE'):
                    pycsp.TraceMsg(len(queue))

                # Handling poison / retire
                if (poisoned or retired):
                    if len(queue):
                        try:
                            cout(queue.popleft())
                        except:
                            if poisoned:
                                pycsp.poison(cin, cout)
                            if retired:
                                pycsp.retire(cin, cout)
                    else:
                        try:
                            if poisoned:
                                pycsp.poison(cin, cout)
                            if retired:
                                pycsp.retire(cin, cout)
                        except:
                            pass
                        return # quit
                # Queue empty
                elif not len(queue):
                    queue.append(cin())
                # Queue not full and not empty
                elif len(queue) < N:
                    g, msg = pycsp.Alternation([
                            (cout, queue[0], None),
                            (cin, None)
                            ]).select()
                    if g == cin:
                        queue.append(msg)
                    else:
                        queue.popleft()
                # Queue full
                else:
                    cout(queue.popleft())
            except pycsp.ChannelPoisonException, e:
                poisoned = True
            except pycsp.ChannelRetireException, e:
                retired = True

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
