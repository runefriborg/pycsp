"""
Communicator module

Handles the sharing of TCP connections from host to host. Even though
these connections support two-way communication, we only use them as
one-way to avoid possible deadlocks from synchronization conflicts.

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

import os
import sys
import socket
import threading
import SocketServer
import cPickle as pickle
import struct


# Header CMDs:
LOCKTHREAD_ACQUIRE_LOCK, LOCKTHREAD_ACCEPT_LOCK, LOCKTHREAD_NOTIFY_SUCCESS, LOCKTHREAD_POISON, LOCKTHREAD_RETIRE = range(5)

# Header fields:
H_CMD, H_ID, H_MSG_SIZE = range(3)

# = : Native byte-order, standard size
# h : short, CMD
# l : long, ID
# l : long, payload size following this header
header_fmt = "=hll"
header_size = struct.calcsize(header_fmt)

def join_reader(channel):
    channel.channelhome
    pass
    #channel.connect

def join_writer(channel):
    pass

def leave_reader(channel):
    return True

def leave_writer(channel):
    return False

def post_read(channel):
    pass

def remove_read(channel):
    pass

def post_write(channel):
    pass

def remote_write(channel):
    pass


def compile_header(cmd, id, arg):
    pass

class LockVal(object):
    def __init__(self):
        self.id = None
        self.counter = 0

    def acquire(self, id):
        if self.counter == 0:
            self.id = id

        if self.id == id:
            self.counter += 1

            return True
        else:
            return False

    def release(self, id):
        if self.id != id or self.counter == 0:
            raise Exception("Should never release a lock, which is not acquired!")
        
        self.counter -= 1

        if self.counter == 0:
            return True
        else:
            return False
    

class LockThread(threading.Thread):
    def __init__(self, process, cond):
        threading.Thread.__init__(self)

        class Handler(SocketServer.BaseRequestHandler):
            def setup(self):
                self.lock = LockVal()
                self.lock_acquire_queue = []

            def handle(self):
                compiled_header = self.request.recv(header_size)
                if len(compiled_header) == 0:
                    # connection broken.
                    raise Exception("connection broken")

                header = struct.unpack(header_fmt, compiled_header)

                if header[H_CMD] == LOCKTHREAD_ACQUIRE_LOCK:
                    if self.lock.acquire(header[H_ID]):
                        # Send reply
                        self.request.sendall(compile_header(LOCKTHREAD_ACCEPT_LOCK, header[H_ID], process.state))
                    else:
                        self.lock_acquire_queue.append(header)
                        

                if self.lock[0] == header[H_ID] and self.lock[1] > 0:
                    if header[H_CMD] == LOCKTHREAD_RELEASE_LOCK:
                        
                        if self.lock.release(header[H_ID]):
                            # The lock is no longer acquired by anyone
                            if self.lock_acquire_queue:
                                header = self.lock_acquire_queue.pop(0)
                                self.lock.acquire(header[H_ID]):
                                # Send reply
                                s = open(

                        

                    if header[H_CMD] == LOCKTHREAD_NOTIFY_SUCCESS:
                        cond.acquire()
                        process.state = SUCCESS
                        data = pickle.loads(self.request.recv(header[H_MSG_SIZE]))
                        process.result_ch = data['channel']
                        process.result_msg = data['msg']
                        cond.notifyAll()
                        cond.release()

                    if header[H_CMD] == LOCKTHREAD_POISON:
                        cond.acquire()
                        process.state = POISON
                        cond.notifyAll()
                        cond.release()

                    if header[H_CMD] == LOCKTHREAD_RETIRE:
                        cond.acquire()
                        process.state = RETIRE
                        cond.notifyAll()
                        cond.release()
           
        self.server = SocketServer.TCPServer(("localhost", 0), Handler)
        self.address = self.server.server_address

    def run(self):
        server.serve_forever()

    def shutdown(self):
        server.shutdown()



class ChannelHomeThread(threading.Thread):
    def __init__(self, process, cond):
        threading.Thread.__init__(self)

        class Handler(SocketServer.BaseRequestHandler):
            def setup(self):
                self.lock = (None, 0)
                self.lock_acquire_queue = []

            def handle(self):
                                
                compiled_header = self.request.recv(header_size)
                if len(compiled_header) == 0:
                    # connection broken.
                    raise Exception("connection broken")

                header = struct.unpack(header_fmt, compiled_header)

                if header[H_CMD] == LOCKTHREAD_ACQUIRE_LOCK:
                    if self.lock[1] == 0:
                        self.lock[0] = header[H_ID]

                    if self.lock[0] == header[H_ID]:
                        self.lock[1] += 1
                        
                        # Send reply
                        self.request.sendall(compile_header(LOCKTHREAD_ACCEPT_LOCK, header[H_ID], process.state)

                if self.lock[0] == header[H_ID] and self.lock[1] > 0:
                    if header[H_CMD] == LOCKTHREAD_RELEASE_LOCK:
                        self.lock[1] -= 1
                        if self.lock[1] == 0:
                                                 
                                                 

                    if header[H_CMD] == LOCKTHREAD_NOTIFY_SUCCESS:
                        cond.acquire()
                        process.state = SUCCESS
                        data = pickle.loads(self.request.recv(header[H_MSG_SIZE]))
                        process.result_ch = data['channel']
                        process.result_msg = data['msg']
                        cond.notifyAll()
                        cond.release()

                    if header[H_CMD] == LOCKTHREAD_POISON:
                        cond.acquire()
                        process.state = POISON
                        cond.notifyAll()
                        cond.release()

                    if header[H_CMD] == LOCKTHREAD_RETIRE:
                        cond.acquire()
                        process.state = RETIRE
                        cond.notifyAll()
                        cond.release()

                

        self.server = SocketServer.TCPServer(("localhost", 0), Handler)
        self.address = self.server.server_address

    def run(self):
        server.serve_forever()

    def shutdown(self):
        server.shutdown()



class InitChannelHome(object):
    """
    Singleton
    """
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
    
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)
            
            cls.__instance.chan_home_db = {}
            
        return cls.__instance
    getInstance = classmethod(getInstance)

    def request(self, chan_id):
        if self.chan_home_db.has_key(chan_id):
            return self.chan_home_db[chan_id]
        else:
            return None

    def add(self, chan_id, chan_home):
        self.chan_home_db['chan_id'] = chan_home
