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

import SocketServer
from SimpleXMLRPCServer import SimpleXMLRPCServer
 
# Threaded mix-in
class AsyncXMLRPCServer(SocketServer.ThreadingMixIn,SimpleXMLRPCServer): pass


from configuration import *
from alternation import *
from channel import *
from channelend import *
from guard import *
from pycsp.common.const import *

# Classes
class ServerProcess(threading.Thread):
    def __init__(self, host):
        threading.Thread.__init__(self)
        self.cond = threading.Condition()
        self.uri = None
        self.host = host

    def run(self):
        self.cond.acquire()

        # Init server
        if self.host == None:            
            self._daemon = AsyncXMLRPCServer(("localhost", 8000), logRequests=False, allow_none=True)
            self.uri = 'http://localhost:8000'
        else:
            self._daemon = AsyncXMLRPCServer((self.host, 8000), allow_none=True)
            self.uri = 'http://'+self.host+':8000'
        
            
        self._daemon.register_introspection_functions()

        self._daemon.register_instance(ServerManager())

        Configuration().set(NET_SERVER_URI, self.uri)

        self.cond.notify()
        self.cond.release()
        
        
        try:
            self._daemon.serve_forever()
        except Exception, e:
            self._daemon.shutdown()            
            raise Exception(e)
        
    def stop(self):
        self._daemon.shutdown()
        import time
        time.sleep(0.2)
        

class ServerManager:
    def __init__(self):
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

def start(host=None):
    server_process = ServerProcess(host)

    server_process.cond.acquire()
    server_process.daemon = True
    server_process.start()

    # Wait for server to init
    server_process.cond.wait()
    server_process.cond.release()

    return server_process

