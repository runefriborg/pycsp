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

from home import ChannelHomeManager

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


class RequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        """
        Here we handle the receiving end for a connection.
        """

        # Get necessary classes
        chanman = ChannelHomeManager() 
        comm = Communicator()
        sched = comm.scheduler

        #print 'Starting thread'
        # Start connection handling.
        while True:
            req = self.request.recv(header_size)
            if len(req) == 0:
                # connection broken.                
                break
            header = struct.unpack(header_fmt, req)
            #print header
            if header[HEADER_PAYLOAD_SIZE] > 0:
                payload = pickle.loads(self.request.recv(header[HEADER_PAYLOAD_SIZE]))

            reply_addr = (header[HEADER_REPLY_HOST].strip('\x00'), header[HEADER_REPLY_PORT])
            p_id = header[HEADER_PROCESS_ID].strip('\x00')
            cmd = header[HEADER_CMD]

            print "IN:"
            print "  C:"+ cmd_to_str[cmd]
            print "  H:"+ str(header)
            print "  P:"+ str(payload)

            if cmd == CMD_GET_CHANNEL_HOME:
                chan = chanman.lookup(payload)
                if chan:
                    print "REPLY:"
                    print "  comm.send_payload(reply_addr, CMD_EVENT, p_id, comm.addr)"
                    comm.send_payload(reply_addr, CMD_EVENT, p_id, comm.addr)
                else:
                    comm.send_event_fail(reply_addr, p_id)

            elif cmd == CMD_EVENT:
                sched.new_process_event(p_id, payload)

            elif cmd == CMD_EVENT_FAIL:
                sched.new_process_event(p_id, None)
            else:
                # The event is passed on to the scheduler.
                sched.new_scheduler_event(reply_addr, p_id, cmd, payload[0], payload[1], payload[2])



class ServerThread(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class Communicator(object):
    """
    Singleton
    """
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self, scheduler=None):
        if scheduler:
            self.scheduler= scheduler

    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)
            
            if not os.environ.has_key('PYCSP_PORT'):
                raise Exception('Error! Can not use distributed channels without the PYCSP_PORT environment variable.')
            
            if os.environ['PYCSP_PORT'] == 'AUTO':                
                pycsp_port = 0
            else:
                pycsp_port = int(os.environ['PYCSP_PORT'])

            cls.__instance.server = ServerThread(("", pycsp_port), RequestHandler)
            cls.__instance.addr = cls.__instance.server.server_address

            cls.__instance.server_thread = threading.Thread(target=cls.__instance.server.serve_forever)

            # Exit the server thread when the main thread terminates
            cls.__instance.server_thread.setDaemon(True)
            cls.__instance.server_thread.start()

            #server.shutdown()

            # key = addr, value = (
            cls.__instance.connections = {}

            cls.__instance.wait_list = []

        return cls.__instance
    getInstance = classmethod(getInstance)

    def send_payload(self, addr, cmd, p_id, payload):
        pickle_payload = pickle.dumps(payload, protocol = pickle.HIGHEST_PROTOCOL)
        header = struct.pack(header_fmt, p_id, self.addr[0], self.addr[1], cmd, len(pickle_payload))
        self.send(addr, header, pickle_payload)

        
    def send(self, addr, header, data=0):
        """
        addr = (host, port)
        """
        if not self.connections.has_key(addr):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)            
            self.connections[addr] = sock

        self.connections[addr].sendall(header)
        if data:
            self.connections[addr].sendall(data)


    #def send_event_fail(self, addr, p_id):
    #    header = struct.pack(header_fmt, p_id, self.addr[0], self.addr[1], CMD_EVENT_FAIL, 0, 0, 0)

    def request_channel_home(self, addr, name):
        p = self.scheduler.current
        self.send_payload(addr, CMD_GET_CHANNEL_HOME, p.id, name)
        self.scheduler.event_wait()
        return p.event

    def channel_join(self, home_addr, name, mode, end_id):
        p = self.scheduler.current
        self.send_payload(home_addr, CMD_CHANNEL_JOIN, p.id, (mode, end_id, name))
        #self.scheduler.event_wait()
        return

    def channel_leave(self, home_addr, name, mode, end_id):
        p = self.scheduler.current
        self.send_payload(home_addr, CMD_CHANNEL_LEAVE, p.id, (mode, end_id, name))
        #self.scheduler.event_wait()
        return


#comm = Communicator()
#comm = Communicator()

#comm.send_payload(("",int(os.environ['PYCSP_PORT'])), "Hello1")
#comm.send_payload(("",int(os.environ['PYCSP_PORT'])), "Hello35")
#comm.send_payload(("192.168.16.83",int(os.environ['PYCSP_PORT'])), "Externa?")

#comm.send_payload(("",int(os.environ['PYCSP_PORT'])), "and old one again")


#import time
#time.sleep(10)


#comm.server_thread.shutdown()
