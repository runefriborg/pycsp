"""
Add buffering to Channel module

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

# Imports
from configuration import *
from alternation import Alternation
from channel import Channel, ChannelPoisonException, ChannelRetireException
from channelend import retire, poison
from process import Process, Spawn
from collections import deque
import uuid

class BufferedChannel(object):
    def __new__(cls, *args, **kargs):
        if kargs.has_key('buffer') and kargs['buffer'] > 0:
            return object.__new__(cls)
        else:
            if kargs.has_key('buffer'):
                del kargs['buffer']
            return Channel(*args, **kargs)

    def __init__(self, name=None, buffer=0):
        if name == None:
            # Create name based on host ID and current time
            import uuid
            name = str(uuid.uuid1())

        self.__inChan = Channel(name=name+'inChan')
        self.__outChan = Channel(name=name+'outChan')
        self.__bufferProcess = Process(self.__proc,
                                       self.__inChan.reader(),
                                       self.__outChan.writer(),
                                       N=buffer)

        # Retrieve channel ends
        self.reader = self.__outChan.reader
        self.writer = self.__inChan.writer

        # Start buffer process
        Spawn(self.__bufferProcess)

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()
    
    def __proc(self, cin, cout, N):
        queue = deque()
        poisoned = False
        retired = False
        while True:
            try:
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
                        try:
                            if poisoned:
                                poison(cin, cout)
                            if retired:
                                retire(cin, cout)
                        except:
                            pass
                        return # quit
                # Queue empty
                elif not len(queue):
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
