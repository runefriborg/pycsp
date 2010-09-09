"""
Channel server module

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
import threading
import Pyro.naming, Pyro.core

from configuration import *
from alternation import *
from channel import *
from channelend import *
from guard import *
from pycsp.common.const import *

# Classes
class PyroServerProcess(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.managerObj = None
        self.cond = threading.Condition()
        self.uri = None

    def run(self):
        self.cond.acquire()

        # Init server
        Pyro.core.initServer()
        self._daemon = Pyro.core.Daemon()

        self.managerObj = PyroServerManager()
        self.uri = self._daemon.connectPersistent(self.managerObj, 'SERVER')
        self.cond.notify()
        self.cond.release()
        
        #Starting requestLoop'
        
        try:
            self._daemon.requestLoop()
        except Exception, e:
            self._daemon.disconnect(self.managerObj)
            self._daemon.shutdown()
            raise Exception(e)
        
    def shutdown(self):
        self._daemon.disconnect(self.managerObj)
        self._daemon.shutdown()
        

class PyroServerManager(Pyro.core.ObjBase):
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self.ChannelIndex = {}
        self.AlternationIndex = {}
        self.lock = threading.RLock()

    def Alternation(self, reduced_guards):
        self.lock.acquire()
        id = str(random.random())+str(time.time())

        # Swap channel names for channels, preserve guards
        new_guards = []
        for prio_item in reduced_guards:
            c, op, msg = prio_item

            if not isinstance(c, Guard):
                # Swap channel name for channel
                if not self.ChannelIndex.has_key(c):
                    self.lock.release()
                    raise ChannelPoisonException()
                
                c = self.ChannelIndex[c]

            new_guards.append((c, op, msg))

        self.AlternationIndex[id] = RealAlternation(new_guards)
        self.lock.release()
        return id

    def Alternation_delete(self, id):
        del self.AlternationIndex[id]


    def Alternation_choose(self, id):
        idx, req, c, op = self.AlternationIndex[id].choose()
        if isinstance(c, RealChannel):
            c = c.name
        return idx, c, req.msg, op

    def Channel(self, name = None):
        self.lock.acquire()
        id = name
        if id == None:
            c = RealChannel()
            self.ChannelIndex[c.name] = c
            id = c.name
        elif not self.ChannelIndex.has_key(id):
            self.ChannelIndex[id] = RealChannel(id)
        self.lock.release()
        return id

    def Channel_delete(self, id):
        del self.ChannelIndex[id]
        
    def Channel_read(self, id):
        try:
            return self.ChannelIndex[id]._read()
        except KeyError:
            raise ChannelPoisonException()

    def Channel_write(self, id, msg):
        try:
            return self.ChannelIndex[id]._write(msg)
        except KeyError:
            raise ChannelPoisonException()

    def Channel_poison(self, id):
        try:
            self.ChannelIndex[id].poison()
            self.Channel_delete(id)
        except KeyError:
            pass
        
    def Channel_join_reader(self, id):
        try:
            self.ChannelIndex[id].join_reader()
        except KeyError:
            raise ChannelPoisonException()

    def Channel_leave_reader(self, id):
        try: 
            self.ChannelIndex[id].leave_reader()
        except KeyError:
            pass

    def Channel_join_writer(self, id):
        try:
            self.ChannelIndex[id].join_writer()
        except KeyError:
            raise ChannelPoisonException()

    def Channel_leave_writer(self, id):
        try:
            self.ChannelIndex[id].leave_writer()
        except KeyError:
            pass

    def test(self):
        return True

def run():
    server_process = PyroServerProcess()

    server_process.cond.acquire()
    server_process.start()

    # Wait for server to init
    server_process.cond.wait()
    server_process.cond.release()

    URI = server_process.uri
    print 'Server at '+str(URI)
    
    print 'Press enter to stop server and quit.', raw_input()
    server_process.shutdown()
    return
