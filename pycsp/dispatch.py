"""
Dispatch module

Handles all socket and inter-process communication by dispatching messages onto queues


Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

import os
import sys
import ossocket
import select, threading
import Queue
import cPickle as pickle
import struct
from header import *
from exceptions import *
from pycsp.common.const import *
from configuration import *


        
conf = Configuration()

def data2bin(s):

    return s

def bin2data(s):
    s =  pickle.loads(s)
    return s


class Message:
    """
    Message object which is used to exchange messages to both local and remote hosts
    header : Must be of Header class type
    payload : Any serializable type
    """
    def __init__(self, header, payload=None):
        self.header = header
        self.payload = payload 

    def transmit(self, addr):

        
        if not (self.header.cmd & HAS_PAYLOAD):
            sock = ossocket.connect(addr)
            sock = ossocket.sendall(sock, self.header)
            ossocket.close(addr)

        else:
            payload_bin_data = pickle.dumps(self.payload, protocol = PICKLE_PROTOCOL)
            self.header.arg = len(payload_bin_data)
            
            sock = ossocket.connect(addr)
            sock = ossocket.sendall(sock, self.header)
            ossocket.sendallNOreconnect(sock, payload_bin_data)
            ossocket.close(addr)

class SocketDispatcher(object):
    """
    SocketDispatcher singleton
   
    Requesting s = SocketDispatcher() will ensure that you
    are provided with one SocketDispatcher for each interpreter.
    
    """
    __condObj = threading.Condition() # lock object
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass

    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''

        #  Check that this is not a stale singleton from another interpreter. Using the multiprocessing
        #  module to create new subprocesses with individual interpreters, has such a side-effect.
        #  If the singleton is from another interpreter, then recreate a new singleton for this interpreter.

        # Critical section start
        cls.__condObj.acquire()
        try:
            try:
                import multiprocessing 
                if cls.__instance is not None:
                    subprocess = multiprocessing.current_process()
                    if cls.__instance.interpreter != subprocess:
                        cls.__instance = None
            except ImportError:
                pass

            if cls.__instance is not None:
                if cls.__instance.socketthread.finished:
                    # Socket thread has been terminated.
                    # Forcing reinitialisation
                    print "REINIT"
                    cls.__instance = None

            if cls.__instance is None:
                # Initialize **the unique** instance
                cls.__instance = object.__new__(cls)
                cls.__instance.condObj = cls.__condObj

                # Record interpreter subprocess if multiprocessing is available
                try:
                    import multiprocessing
                    cls.__instance.interpreter = multiprocessing.current_process()
                except ImportError:
                    pass

                # Start SocketThread
                cls.__instance.socketthread = SocketThread(cls.__instance.condObj)
                cls.__instance.socketthread.start()

        finally:
            #  Exit from critical section whatever happens
            cls.__condObj.release()
        # Critical section end

        return cls.__instance
    getInstance = classmethod(getInstance)


    def getThread(self):
        if self.socketthread == None:
            raise Exception("Fatal error: No socket thread running!")
        
        return self.socketthread




class SocketThread(threading.Thread):
    def __init__(self, cond):
        threading.Thread.__init__(self)

        self.channels = {}
        self.processes = {}

        self.cond = cond
        self.daemon = False


        if os.environ.has_key(ENVVAL_PORT):
            addr = ('', int(os.environ[ENVVAL_PORT]))
        else:
            addr = ('', 0)

        self.server_socket, self.server_addr = ossocket.start_server(addr)

        self.finished = False


    def run(self):
        active_socket_list = [self.server_socket]

        while(True):
            ready, _, exceptready = select.select(active_socket_list, [], [])
            for s in ready:
                if s == self.server_socket:
                    conn, _ = self.server_socket.accept()
                    active_socket_list.append(conn)
                else:
                    header = Header()
                    header.cmd = ERROR_CMD
                    s.recv_into(header)
                    if header.cmd == ERROR_CMD:
                        # connection disconnected
                        active_socket_list.remove(s)
                        s.close()
                    else:
                        if (header.cmd & HAS_PAYLOAD):
                            payload =  pickle.loads(ossocket.recvall(s, header.arg))
                        else:
                            payload = None

                        m = Message(header, payload)
                        if (header.cmd & PROCESS_CMD):
                            if (header.cmd & IS_REPLY):
                                self.processes[header.id][1].put(m)
                            else:
                                self.processes[header.id][0].put(m)
                        else:
                            if (header.cmd & IS_REPLY):
                                self.channels[header.id][1].put(m)
                            else:
                                self.channels[header.id][0].put(m)

    """
    q_primary is the queue containing messages for new actions
    q_replys is the queue containing replys for current actions and must be prioritised over q_primary

    TODO: q_primary / q_replys should be replaced by a priority_queue which uses the FIFO principle but priorities reply over the FIFO principle
    """
    def registerChannel(self, name_id):
        q_primary, q_replys = Queue.Queue(), Queue.Queue()
        self.channels[name_id] = (q_primary, q_replys)
        return (q_primary, q_replys)

    def registerProcess(self, name_id):
        q_primary, q_replys = Queue.Queue(), Queue.Queue()
        self.processes[name_id] = (q_primary, q_replys)
        return (q_primary, q_replys)

    def getChannelQueue(self, name_id):
        return self.channels[name_id]

    def getProcessQueue(self, name_id):
        return self.processes[name_id]

    def deregisterChannel(self, name_id):
        del self.channels[name_id]

    def deregisterProcess(self, name_id):
        del self.processes[name_id]


    """
    NOTICE! TODO These send methods might have to be synchronized for other interpreters than the standard CPYTHON interpreter.
    """
    def send(self, addr, header, payload=None):
        # Update message source
        header._source_host, header._source_port = self.server_addr
        
        m = Message(header, payload)
        
        # is address the same as my own address? 
        if addr == self.server_addr:

            if (header.cmd & PROCESS_CMD):
                if self.processes.has_key(header.id):
                    self.processes[header.id][0].put(m)
                else:
                    raise SocketDispatchException()
            else:
                if self.channels.has_key(header.id):
                    self.channels[header.id][0].put(m)
                else:
                    raise SocketDispatchException()
                
        else:            
            m.transmit(addr)


    def reply(self, source_header, header, payload=None):
        addr = (source_header._source_host, source_header._source_port)
        
        # Update message source
        header._source_host, header._source_port = self.server_addr        

        # Set REPLY flag
        header.cmd = header.cmd | IS_REPLY

        m = Message(header, payload)
    
        # is address the same as my own address? 
        if addr == self.server_addr:
            if (header.cmd & PROCESS_CMD):
                if self.processes.has_key(header.id):
                    self.processes[header.id][1].put(m)
                else:
                    raise SocketDispatchException()
            else:
                if self.channels.has_key(header.id):
                    self.channels[header.id][1].put(m)
                else:
                    raise SocketDispatchException()
                
        else:            
            m.transmit(addr)
        

        

