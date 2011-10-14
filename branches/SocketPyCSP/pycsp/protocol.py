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


# = : Native byte-order, standard size
# 36s : string, process uuid4
# 64s : string, ip/hostname
# h : short, port
# h : short, Command.
# l : long, payload size following this header.
HEADER_PROCESS_ID, HEADER_REPLY_HOST, HEADER_REPLY_PORT, HEADER_CMD, HEADER_PAYLOAD_SIZE = range(5)

header_fmt = "=36s64shhl"
header_size = struct.calcsize(header_fmt)

# Commands:
CMD_GET_CHANNEL_HOME, CMD_EVENT, CMD_EVENT_FAIL, CMD_CHANNEL_JOIN, CMD_CHANNEL_LEAVE = range(5)



cmd_to_str = {
    CMD_GET_CHANNEL_HOME:"GET_CHANNEL_HOME",
    CMD_EVENT:"EVENT",
    CMD_EVENT_FAIL:"EVENT_FAIL",
    CMD_CHANNEL_JOIN:"CHANNEL_JOIN",
    CMD_CHANNEL_LEAVE:"CHANNEL_LEAVE"
    }         


def join_reader(channel):
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

class LockThread(threading.Thread):
    def __init__(self, process, cond):
        threading.Thread.__init__(self)

        class LockThreadHandler(SocketServer.BaseRequestHandler):
            def setup(self):
                self.lock = (None, 0)

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
                        self.request.send(compile_header(LOCKTHREAD_ACCEPT_LOCK, header[H_ID], process.state)

                if self.lock[0] == header[H_ID] and self.lock[1] > 0:
                    if header[H_CMD] == LOCKTHREAD_RELEASE_LOCK:
                        self.lock[1] -= 1

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

                



                    
                    
                print "Welcome"
                # self.request is the TCP socket connected to the client
                self.data = self.request.recv(1024).strip()
                print "%s wrote:" % self.client_address[0]
                print self.data
                # just send back the same data, but upper-cased
                self.request.send(self.data.upper())

        self.server = SocketServer.TCPServer(("localhost", 0), LockThreadHandler)
        self.address = self.server.server_address

    def run(self):
        server.serve_forever()

    def shutdown(self):
        server.shutdown()
