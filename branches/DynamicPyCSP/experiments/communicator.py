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
#import cPickle as pickle
import struct

# = : Native byte-order, standard size
# h : short, Command.
# l : long, payload size following this header.
HEADER_CMD, HEADER_PAYLOAD_SIZE, = range(2)

header_fmt = "=hl"
header_size = struct.calcsize(header_fmt)

# Commands:
CMD_PAYLOAD, = range(1)

#import ChannelHomeManager
    
class RequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        """
        Here we handle the receiving end for a connection.
        """
        #chan_man = ChannelHomeManager()

        print 'Starting thread'
        # Start connection handling.
        while True:
            header = struct.unpack(header_fmt, self.request.recv(header_size))
            print header
            if header[HEADER_PAYLOAD_SIZE] > 0:
                payload = self.request.recv(header[HEADER_PAYLOAD_SIZE])
        
            print "Data:"+ payload

        

class ServerThread(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class Communicator(object):
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
            
            cls.__instance.server = ServerThread(("", int(os.environ['PYCSP_PORT'])), RequestHandler)
            #ip, port = server.server_address

            cls.__instance.server_thread = threading.Thread(target=cls.__instance.server.serve_forever)

            # Exit the server thread when the main thread terminates
            cls.__instance.server_thread.setDaemon(True)
            cls.__instance.server_thread.start()

            #server.shutdown()

            # key = addr, value = (
            cls.__instance.connections = {}
            
        return cls.__instance
    getInstance = classmethod(getInstance)

    def send_payload(self, addr, payload):
        header = struct.pack(header_fmt, CMD_PAYLOAD, len(payload))
        self.send(addr, header, payload)

    def send(self, addr, header, payload=0):
        """
        addr = (host, port)
        """
        if not self.connections.has_key(addr):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)            
            self.connections[addr] = sock

        self.connections[addr].send(header)
        if payload:
            self.connections[addr].send(payload)


comm = Communicator()

comm.send_payload(("",int(os.environ['PYCSP_PORT'])), "Hello1")
comm.send_payload(("",int(os.environ['PYCSP_PORT'])), "Hello35")
comm.send_payload(("192.168.16.83",int(os.environ['PYCSP_PORT'])), "Externa?")

comm.send_payload(("",int(os.environ['PYCSP_PORT'])), "and old one again")


import time
time.sleep(10)


comm.server_thread.shutdown()
