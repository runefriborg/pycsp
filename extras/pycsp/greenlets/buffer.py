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

from .channel import Channel, ChannelPoisonException, ChannelRetireException
from .channelend import poison, retire
from .process import process, Spawn
from .alternation import Alternation

import pycsp.current
if pycsp.current.trace:
    from pycsp.common.trace import *

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
    >>> Spawn(P1(C.writer()))
    
    >>> cin = C.reader()
    >>> cin()
    'Hello World'

    >>> retire(cin)

    Buffered channels are semantically equivalent with a chain
    of forwarding processes.
    >>> B = Channel(buffer=5)
    >>> cout = B.writer()
    >>> for i in range(5):
    ...     cout(i)

    Poison and retire are attached to final element of the buffer.
    >>> poison(cout)

    >>> @process
    ... def sink(cin, L):
    ...     while True:
    ...         L.append(cin())

    >>> L = []
    >>> Parallel(sink(B.reader(), L))
    >>> L
    [0, 1, 2, 3, 4]
    """
    def __init__(self, name=None, buffer=1):
        if name == None:
            # Create unique name
            name = str(random.random())+str(time.time())

        self.name = name
        self.__inChan = Channel(name=name+'inChan')
        self.__outChan = Channel(name=name+'outChan')
        self.__bufferProcess = self.Buffer(self.__inChan.reader(),
                                       self.__outChan.writer(),
                                       N=buffer)

        # Retrieve channel ends
        self.reader = self.__outChan.reader
        self.writer = self.__inChan.writer

        # Set buffer process as deamon to allow kill if mother process
        # exists.
        self.__bufferProcess.daemon = True

        # Start buffer process        
        Spawn(self.__bufferProcess)

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def poison(self):
        self.__inChan.poison()
        self.__outChan.poison()

    @process
    def Buffer(self, cin, cout, N):
        queue = deque()
        poisoned = False
        retired = False
        while True:
            try:
                import pycsp.current
                if pycsp.current.trace:
                    TraceMsg(len(queue))

                # Handling poison / retire
                if (poisoned or retired):
                    if len(queue):
                        try:
                            cout(queue.popleft())
                        except:
                            if poisoned:
                                poison(cin, cout)
                            if retired:
                                retire(cin, cout)
                    else:
                        if poisoned:
                            poison(cin, cout)
                        if retired:
                            retire(cin, cout)
                        return # quit
                # Queue empty
                elif len(queue) == 0:
                    queue.append(cin())
                # Queue not full and not empty
                elif len(queue) < N:
                    g, msg = Alternation([
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
            except ChannelPoisonException, e:
                poisoned = True
            except ChannelRetireException, e:
                retired = True

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
