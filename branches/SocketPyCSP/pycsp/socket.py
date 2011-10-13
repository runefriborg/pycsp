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


def postREAD(req):
    
    
def removeREAD(req):



class LockThread(threading.Thread):
    """ Process(func, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances
    """
    def __init__(self, process, cond):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        
        # Create unique id
        self.id = str(random.random())+str(time.time())

    def run(self):

        

        try:
            # Store the returned value from the process
            self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException, e:
            # look for channels and channel ends
            self.__check_poison(self.args)
            self.__check_poison(self.kwargs.values())
        except ChannelRetireException, e:
            # look for channel ends
            self.__check_retire(self.args)
            self.__check_retire(self.kwargs.values())

