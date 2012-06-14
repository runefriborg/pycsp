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
import cPickle as pickle
import struct
from header import *
from exceptions import *
from pycsp.common.const import *
from configuration import *
        
conf = Configuration()

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

    def __repr__(self):
        return repr("<pycsp.dispatch.Message cmd:%s>" % (cmd2str(self.header.cmd)))

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

                # Init SocketThreadData                
                cls.__instance.socketthreaddata = SocketThreadData(cls.__instance.condObj)
        finally:
            #  Exit from critical section whatever happens
            cls.__condObj.release()
        # Critical section end

        return cls.__instance
    getInstance = classmethod(getInstance)


    def getThread(self):
        return self.socketthreaddata



class QueueBuffer:
    def __init__(self):
        self.normal = []
        self.reply = []

        self.lock = threading.Condition()
        self.waiting = False

    def __repr__(self):
        return repr("<pycsp.dispatch.QueueBuffer containing normal:%s reply:%s messages>" % (str(self.normal), str(self.reply)))

    def pop_normal(self):

        # Pre test
        if self.normal:
            return self.normal.pop(0)

        self.lock.acquire()
        while not self.normal:
            self.waiting = True
            self.lock.wait()
        obj = self.normal.pop(0)
        self.waiting = False
        self.lock.release()

        return obj        

    def pop_reply(self):

        # Pre test
        if self.reply:
            return self.reply.pop(0)

        self.lock.acquire()
        while not self.reply:
            self.waiting = True
            self.lock.wait()
        obj = self.reply.pop(0)
        self.waiting = False
        self.lock.release()

        return obj

    def put_normal(self, obj):
        self.lock.acquire()
        self.normal.append(obj)
        if self.waiting:
            self.lock.notify()
        self.lock.release()
    
    def put_reply(self, obj):
        self.lock.acquire()
        self.reply.append(obj)
        if self.waiting:
            self.lock.notify()
        self.lock.release()


class SocketThread(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)

        self.channels = data.channels
        self.processes = data.processes
        self.data = data
        self.cond = self.data.cond

        self.daemon = False

        self.finished = False

        
    def run(self):

        #print "Starting SocketThread"

        while(not self.finished):
            ready, _, exceptready = select.select(self.data.active_socket_list, [], [])
            for s in ready:
                if s == self.data.server_socket:
                    conn, _ = self.data.server_socket.accept()
                    self.data.active_socket_list.append(conn)
                else:
                    header = Header()
                    header.cmd = ERROR_CMD
                    s.recv_into(header)
                    if header.cmd == ERROR_CMD:
                        # connection disconnected
                        if s in self.data.active_socket_list:
                            self.data.active_socket_list.remove(s)
                        s.close()
                    else:
                        if (header.cmd & HAS_PAYLOAD):
                            payload =  pickle.loads(ossocket.recvall(s, header.arg))
                        else:
                            payload = None

                        m = Message(header, payload)

                        self.cond.acquire()
                        if (header.cmd == SOCKETTHREAD_SHUTDOWN):
                            if self.channels or self.processes:
                                # Socketthread is still busy. Thus ignore and expect a later call to deregister to invoke stopThread.
                                pass
                            else:
                                self.finished = True
                                
                                # Remove thread reference
                                self.data.thread = None
                        
                            # Do not close sockets as the socketthread may be restarted at a later time

                        elif (header.cmd & PROCESS_CMD):
                            if self.processes.has_key(header.id):
                                self.processes[header.id].handle(m)
                            elif (header.cmd & REQ_REPLY):
                                self.reply(header, Header(LOCKTHREAD_UNAVAILABLE, header._source_id))
                            elif (header.cmd & IGN_UNKNOWN):
                                pass
                            else:
                                if not self.data.processes_unknown.has_key(header.id):
                                    self.data.processes_unknown[header.id] = []
                                self.data.processes_unknown[header.id].append(m)
                                    
                        else:
                            if self.channels.has_key(header.id):                                
                                if (header.cmd & IS_REPLY):
                                    self.channels[header.id].put_reply(m)
                                else:
                                    self.channels[header.id].put_normal(m)
                            elif (header.cmd & IGN_UNKNOWN):
                                pass
                            else:                                
                                if not self.data.channels_unknown.has_key(header.id):
                                    self.data.channels_unknown[header.id] = QueueBuffer()

                                if (header.cmd & IS_REPLY):
                                    self.data.channels_unknown[header.id].put_reply(m)
                                else:
                                    self.data.channels_unknown[header.id].put_normal(m)
                        self.cond.release()

        
        
class SocketThreadData:
    def __init__(self, cond):

        self.channels = {}
        self.processes = {}

        # Unknown messages, which is moved to known messages, if a channel or processes with a matching name registers.
        # TODO: This must be capped.
        self.channels_unknown = {}
        self.processes_unknown = {}

        self.cond = cond

        if os.environ.has_key(ENVVAL_PORT):
            addr = ('', int(os.environ[ENVVAL_PORT]))
        else:
            addr = ('', 0)

        self.server_socket, self.server_addr = ossocket.start_server(addr)
        self.active_socket_list = [self.server_socket]

        self.thread = None



    def startThread(self):
        self.cond.acquire()
        if self.thread == None:
            self.thread = SocketThread(self)
            self.thread.start()
        self.cond.release()

            
    def stopThread(self):
        self.cond.acquire()
        if not self.thread == None:
            h = Header(SOCKETTHREAD_SHUTDOWN)
            sock = ossocket.connectNOcache(self.server_addr)
            sock.sendall(h)
            ossocket.closeNOcache(sock)

        self.cond.release()
                
    
    """
    QueueBuffer contains two queues.
    normal is the queue containing messages for new actions
    reply is the queue containing replys for current actions and must be prioritised over normal

    """
    def registerChannel(self, name_id):

        self.cond.acquire()

        if self.channels_unknown.has_key(name_id):
            print "GOT UNKNOWN MESSAGE"
            q = self.channels_unknown.pop(name_id)
        else:
            q = QueueBuffer()


        self.channels[name_id] = q
        if self.thread == None:
            self.startThread()

        self.cond.release()
        return q

    def getChannelQueue(self, name_id):
        self.cond.acquire()
        q = self.channels[name_id]
        self.cond.release()
        return q

    def deregisterChannel(self, name_id):
        self.cond.acquire()
        del self.channels[name_id]
        if len(self.channels) == 0 and len(self.processes) == 0:
            self.stopThread()            
        self.cond.release()

    def registerProcess(self, name_id, remotelock):
        self.cond.acquire()
        if self.processes_unknown.has_key(name_id):
            for m in self.processes_unknown[name_id]:
                remotelock.handle(m)
            del self.processes_unknown[name_id]


        self.processes[name_id] = remotelock

        if self.thread == None:
            self.startThread()

        self.cond.release()

    def deregisterProcess(self, name_id):
        ok = False
        rl = self.processes[name_id]

        while (not ok):
            self.cond.acquire()
            if rl.lock_acquired or rl.waiting:
                self.cond.release()
                rl.close()
                self.cond.acquire()
            else:
                ok = True
                del self.processes[name_id]
                if len(self.channels) == 0 and len(self.processes) == 0:
                    self.stopThread()

            self.cond.release()

    def send(self, addr, header, payload=None):
        # Update message source
        header._source_host, header._source_port = self.server_addr
        
        m = Message(header, payload)
        
        # is address the same as my own address? 
        if addr == self.server_addr:
            self.cond.acquire()
            if (header.cmd & PROCESS_CMD):
                if self.processes.has_key(header.id):
                    self.processes[header.id].handle(m)
                elif (header.cmd & REQ_REPLY):
                    #print("%s UNAVAILABLE for channel %s!" % (str(header.id), str(header._source_id)))
                    self.reply(header, Header(LOCKTHREAD_UNAVAILABLE, header._source_id))
                elif (header.cmd & IGN_UNKNOWN):
                    pass
                else:
                    if not self.processes_unknown.has_key(header.id):
                        self.processes_unknown[header.id] = []
                    self.processes_unknown[header.id].append(m)
            else:
                if self.channels.has_key(header.id):
                    self.channels[header.id].put_normal(m)
                elif (header.cmd & IGN_UNKNOWN):
                    pass
                else:
                    if not self.channels_unknown.has_key(header.id):
                        self.channels_unknown[header.id] = QueueBuffer()
                    self.channels_unknown[header.id].put_normal(m)
            self.cond.release()
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
            self.cond.acquire()
            if (header.cmd & PROCESS_CMD):
                if self.processes.has_key(header.id):
                    self.processes[header.id].handle(m)
                elif (header.cmd & IGN_UNKNOWN):
                    pass
                else:
                    if not self.processes_unknown.has_key(header.id):
                        self.processes_unknown[header.id] = []
                    self.processes_unknown[header.id].append(m)
            else:
                if self.channels.has_key(header.id):
                    self.channels[header.id].put_reply(m)
                elif (header.cmd & IGN_UNKNOWN):
                    pass
                else:
                    if not self.channels_unknown.has_key(header.id):
                        self.channels_unknown[header.id] = QueueBuffer()
                    self.channels_unknown[header.id].put_reply(m)                
            self.cond.release()
        else:            
            m.transmit(addr)
        

        

