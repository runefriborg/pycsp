"""
Dispatch module

Handles all socket and inter-process communication by dispatching messages onto queues

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import os
import select, threading
import errno

try:    
    import multiprocessing
    MULTIPROCESSING_ENABLED=1
except ImportError:
    MULTIPROCESSING_ENABLED=0

import pickle


from pycsp.parallel import ossocket
from pycsp.parallel.header import *
from pycsp.parallel.exceptions import *
from pycsp.parallel.const import *
from pycsp.parallel.configuration import *
        
conf = Configuration()

class Message(object):
    """
    Message object which is used to exchange messages to both local and remote hosts
    header : Must be of Header class type
    payload : Any serializable type
    """
    def __init__(self, header, payload=b""):
        self.header = header
        self.payload = payload

        # transport for natfix
        self.natfix = None

    def transmit(self, handler, addr):

        if not (self.header.cmd & HAS_PAYLOAD):

            sock = handler.connect(addr)
            sock = handler.sendall(sock, self.header)
            handler.close(addr)

            # NATFIX Update SocketThread with new sock
            if (self.header.cmd == CHANTHREAD_ENTER):
                SocketDispatcher().getThread().add_to_active_socket_list(sock)

        else:
            # list is used as a marker, to detect whether
            # the payload has already been pickled. 
            if type(self.payload) == list:
                payload_bin_data = pickle.dumps(self.payload, protocol = PICKLE_PROTOCOL)
            else:
                # payload is already pickled
                payload_bin_data = self.payload

            self.header.arg = len(payload_bin_data)
            
            # Connect or fetch connected socket
            sock = handler.connect(addr)            

            # Send header and payload
            sock = handler.sendall(sock, self.header)
            handler.sendallNOreconnect(sock, payload_bin_data)
            handler.close(addr)            

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

    def __init__(self, reset=False):
        pass

    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''

        #  Check that this is not a stale singleton from another interpreter. Using the multiprocessing
        #  module to create new subprocesses with individual interpreters, has such a side-effect.
        #  If the singleton is from another interpreter, then recreate a new singleton for this interpreter.

        # Critical section start

        if "reset" in kwargs and kwargs["reset"]:
            del cls.__condObj
            cls.__condObj = threading.Condition()
            del cls.__instance
            cls.__instance = None

        cls.__condObj.acquire()

        try:
            if MULTIPROCESSING_ENABLED:                        
                if cls.__instance is not None:
                    subprocess = multiprocessing.current_process()
                    if cls.__instance.interpreter != subprocess:
                        del cls.__condObj
                        cls.__condObj = threading.Condition()
                        del cls.__instance
                        cls.__instance = None

            if cls.__instance is None:
                # Initialize **the unique** instance
                cls.__instance = object.__new__(cls)
                cls.__instance.condObj = cls.__condObj

                # Record interpreter subprocess if multiprocessing is available
                if MULTIPROCESSING_ENABLED:
                    cls.__instance.interpreter = multiprocessing.current_process()

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

class QueueBuffer(object):
    def __init__(self):
        self.normal = []
        self.reply = []

        self.lock = threading.Condition()

        self.waitingR = 0
        self.timeout = False

        self.waitingN = 0

    def __repr__(self):
        return repr("<pycsp.dispatch.QueueBuffer containing normal:%s reply:%s messages>" % (str(self.normal), str(self.reply)))

    def timeout_tick(self):
        # Check timeout values for waiting
        # Current setting is two ticks, to timeout
        # It is the input threads, which invokes the ticks
        if self.waitingR:
            #print("tick")
            self.lock.acquire()
            if self.waitingR:
                ticks = 2
                if self.waitingR < ticks:
                    self.waitingR += 1
                else:
                    self.timeout = True
                    self.lock.notify()
            self.lock.release()

    def pop_normal(self):

        # Pre test
        if self.normal:
            obj = self.normal.pop(0)
            #print("POP:%s id:%s" % (str(obj), str(self.x)))
            return obj

        self.lock.acquire()
        while not self.normal:
            self.waitingN = 1
            self.lock.wait()
            
        obj = self.normal.pop(0)
        self.waitingN = 0
        self.lock.release()

        #print("POP:%s id:%s" % (str(obj), str(self.x)))
        return obj        

    def pop_reply(self):

        # Pre test
        if self.reply:
            return self.reply.pop(0)

        self.lock.acquire()
        while not self.reply and not self.timeout:
            self.timeout = False
            self.waitingR = 1
            self.lock.wait()                
             
        if self.timeout:
            obj = None
        else:
            obj = self.reply.pop(0)        
        self.waitingR = 0
        self.lock.release()

        return obj

    def put_normal(self, obj):
        self.lock.acquire()
        #print("PUT:%s waiting:%s id:%s" % (str(obj), str(self.waiting), str(self.x)))
        self.normal.append(obj)
        if self.waitingN:
            self.lock.notify()
        self.lock.release()
    
    def put_reply(self, obj):
        self.lock.acquire()
        self.reply.append(obj)
        if self.waitingR:
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
        handler = ossocket.ConnHandler()

        while(not self.finished):

            # Performing select.select on possibly EBADF. A lingering socket may be left in the active_socket_list.
            # The following select.select is robust against Bad File Descriptors, and will remove them from the active_socket_list
            # The only way to test for a bad file descriptor, is to cause a socket.error exception.
            
            OK = False
            while (not OK):
                import socket
                try:
                    ready, _, exceptready = select.select(self.data.active_socket_list, [], [], 10.0)
                    OK = True
                except:
                    new_socket_list = []
                    for s in self.data.active_socket_list:
                        try:
                            if s.fileno() > 0:
                                new_socket_list.append(s)
                        except socket.error:
                            # Ignoring EBADF file descriptor errors
                            pass
                        except ValueError:
                            # Ignoring file descriptors with a value of -1
                            pass
                    self.data.active_socket_list = new_socket_list
            # Select finished OK
                    
            if not ready and not exceptready:
                # Timeout. Invoke ticks
                self.cond.acquire()
                for c in list(self.channels.values()):
                    c.timeout_tick()
                self.cond.release()

            else:
                for s in ready:
                    if s == self.data.server_socket:
                        conn, _ = self.data.server_socket.accept()
                        self.data.active_socket_list.append(conn)
                    else:
                        header = Header()
                        header.cmd = ERROR_CMD
                        self.cond.acquire()
                        try:
                            s.recv_into(header)
                        except ossocket.socket.error as e:
                            if e.errno == errno.ECONNRESET:
                                # Connection has been reset
                                header.cmd = ERROR_CMD
                            else:
                                raise
                        self.cond.release()

                        if header.cmd == ERROR_CMD:
                            # connection disconnected
                            if s in self.data.active_socket_list:
                                self.data.active_socket_list.remove(s)
                            s.close()
                        else:
                            if (header.cmd & HAS_PAYLOAD):
                                self.cond.acquire()
                                payload = ossocket.recvall(s, header.arg)
                                self.cond.release()
                            else:
                                payload = ""


                            m = Message(header, payload)

                            if (header.cmd & NATFIX):
                                # save reverse socket as payload
                                m.natfix = s

                            self.cond.acquire()
                            if (header.cmd == SOCKETTHREAD_PING):
                                if self.data.active_socket_list_add:
                                    self.data.active_socket_list.extend(self.data.active_socket_list_add)
                                    self.data.active_socket_list_add = []

                            elif (header.cmd == SOCKETTHREAD_SHUTDOWN):
                                if self.channels or self.processes:
                                    # Socketthread is still busy. Thus ignore and expect a later call to deregister to invoke stopThread.
                                    pass
                                else:
                                    self.finished = True

                                    # Remove thread reference
                                    self.data.thread = None

                                # Do not close sockets as the socketthread may be restarted at a later time

                            elif (header.cmd & PROCESS_CMD):
                                if header.id in self.processes:
                                    p = self.processes[header.id]
                                    p.handle(m)                                
                                elif (header.cmd & REQ_REPLY):
                                    raise FatalException("A REQ_REPLY message should always be valid!")
                                elif (header.cmd & IGN_UNKNOWN):
                                    raise FatalException("IGN_UNKNOWN should never occur!")
                                else:
                                    if not header.id in self.data.processes_unknown:
                                        self.data.processes_unknown[header.id] = []
                                    self.data.processes_unknown[header.id].append(m)

                            else:
                                if header.id in self.channels:
                                    c = self.channels[header.id]
                                    if (header.cmd & IS_REPLY):
                                        c.put_reply(m)
                                    else:
                                        c.put_normal(m)
                                elif (header.cmd & IGN_UNKNOWN):
                                    pass
                                else:                                
                                    if not header.id in self.data.channels_unknown:
                                        self.data.channels_unknown[header.id] = QueueBuffer()

                                    c = self.data.channels_unknown[header.id]

                                    if (header.cmd & IS_REPLY):
                                        c.put_reply(m)
                                    else:
                                        c.put_normal(m)
                            self.cond.release()

class SocketThreadData(object):
    def __init__(self, cond):

        self.channels = {}
        self.processes = {}
        self.guards = {}

        # Unknown messages, which is moved to known messages, if a channel or processes with a matching name registers.
        # TODO: This must be capped.
        self.channels_unknown = {}
        self.processes_unknown = {}

        self.cond = cond        

        host = conf.get(PYCSP_HOST)
        port = conf.get(PYCSP_PORT)
        if port == 0 and ENVVAL_PORT in os.environ:
            port = int(os.environ[ENVVAL_PORT])
        if host == '' and ENVVAL_HOST in os.environ:
            host = os.environ[ENVVAL_HOST]

        host = host.encode()

        addr = (host, port)

        self.server_socket, self.server_addr = ossocket.start_server(addr)
        self.server_addr = (self.server_addr[0].encode(), self.server_addr[1])

        self.active_socket_list = [self.server_socket]
        self.active_socket_list_add = []

        self.thread = None

        self.handler = ossocket.ConnHandler()

    def is_alive(self):
        """
        If the thread is stale (which may happen when channel ends are communicated between OS processes), a new thread must be started.
        """
        if self.thread and self.thread.is_alive():
            return True
        else:
            return False

    def add_reverse_socket(self, addr, sock):
        #print "added", addr, sock
        self.handler.updateCache(addr, sock)
        
    def add_to_active_socket_list(self, sock):
        if not (sock in self.active_socket_list or sock in self.active_socket_list_add):
            
            self.cond.acquire()
            try:
                if not (sock in self.active_socket_list or sock in self.active_socket_list_add):
                    self.active_socket_list_add.append(sock)
                    h = Header(SOCKETTHREAD_PING)
                    # This connection is made only to the local server
                    sock = self.handler.connect(self.server_addr)
                    self.handler.sendall(sock, h)
                    self.handler.close(sock)
            finally:
                self.cond.release()

    def startThread(self):
        #print("startThread dummy")
        """
        self.cond.acquire()
        try:
            if self.thread == None:
                self.thread = SocketThread(self)
                self.thread.start()
        finally:
            self.cond.release()
        """
        pass

            
    def stopThread(self):
        self.cond.acquire()
        try:
            if not self.thread == None:
                h = Header(SOCKETTHREAD_SHUTDOWN)
                # This connection is made only to the local server
                sock = ossocket.connectNOcache(self.server_addr)
                ossocket.sendallNOcache(sock, h)
                ossocket.closeNOcache(sock)
        finally:
            self.cond.release()
                
    
    """
    QueueBuffer contains two queues.
    normal is the queue containing messages for new actions
    reply is the queue containing replys for current actions and must be prioritised over normal

    """
    def registerChannel(self, name_id):
        self.cond.acquire()
        try:
            if name_id in self.channels_unknown:
                #print "GOT UNKNOWN MESSAGE"
                q = self.channels_unknown.pop(name_id)
            else:
                q = QueueBuffer()

            self.channels[name_id] = q
            if self.thread == None:
                self.startThread()
        finally:
            self.cond.release()
        return q

    def getChannelQueue(self, name_id):
        self.cond.acquire()
        if name_id in self.channels:
            q = self.channels[name_id]
        else:
            q = self.guards[name_id]
        self.cond.release()
        return q

    def deregisterChannel(self, name_id):
        self.cond.acquire()
        try:
            if name_id in self.channels:
                del self.channels[name_id]
            if len(self.channels) == 0 and len(self.processes) == 0:
                self.stopThread()           
        finally:
            self.cond.release()

    def registerGuard(self, name_id):
        self.cond.acquire()
        try:
            self.guards[name_id] = QueueBuffer()
            if self.thread == None:
                self.startThread()
        finally:
            self.cond.release()

    def deregisterGuard(self, name_id):
        self.cond.acquire()
        try:
            if name_id in self.guards:
                del self.guards[name_id]
            if len(self.channels) == 0 and len(self.processes) == 0:
                self.stopThread()            
        finally:
            self.cond.release()

    def registerProcess(self, name_id, remotelock):
        self.cond.acquire()
        try:
            if name_id in self.processes_unknown:
                for m in self.processes_unknown[name_id]:
                    remotelock.handle(m)
                del self.processes_unknown[name_id]


            self.processes[name_id] = remotelock

            if self.thread == None:
                self.startThread()
        finally:
            self.cond.release()

    def deregisterProcess(self, name_id):

        self.cond.acquire()
        del self.processes[name_id]
        self.cond.release()

        if len(self.channels) == 0 and len(self.processes) == 0:
            self.stopThread()

        #print("\n### DeregisterProcess\n%s: channels: %s,processes: %s,guards: %s" % (name_id, str(self.channels), str(self.processes), str(self.guards)))


    def send(self, addr, header, payload=b"", otherhandler=None):
        # Update message source
        #print("dispatch.send " + str(self.server_addr))
        header._source_host, header._source_port = self.server_addr
        
        m = Message(header, payload)
        
        # is destination address the same as my own address? 
        self.cond.acquire()
        try:
            if addr == self.server_addr:
                if (header.cmd & PROCESS_CMD):
                    # Process message
                    if header.id in self.processes:
                        self.processes[header.id].handle(m)
                    elif (header.cmd & REQ_REPLY):
                        self.reply(header, Header(LOCKTHREAD_UNAVAILABLE, header._source_id), payload="", otherhandler=otherhandler)
                    elif (header.cmd & IGN_UNKNOWN):
                        pass
                    else:
                        if not header.id in self.processes_unknown:
                            self.processes_unknown[header.id] = []
                        self.processes_unknown[header.id].append(m)
                elif (header.cmd & GUARD_CMD and header.id in self.guards):
                    # Guard message
                    raise FatalException("Guard should never receive a normal message")
                else:
                    # Channel message
                    if header.id in self.channels:
                        self.channels[header.id].put_normal(m)
                    elif (header.cmd & IGN_UNKNOWN):
                        pass
                    else:
                        if not header.id in self.channels_unknown:
                            self.channels_unknown[header.id] = QueueBuffer()
                        self.channels_unknown[header.id].put_normal(m)
            else:
                if otherhandler:
                    m.transmit(otherhandler, addr)
                else:
                    m.transmit(self.handler, addr)
        finally:
            self.cond.release()


    def reply(self, source_header, header, payload=b"", otherhandler=None):
        addr = (source_header._source_host, source_header._source_port)

        # Update message source
        header._source_host, header._source_port = self.server_addr        

        # Set REPLY flag
        header.cmd = header.cmd | IS_REPLY

        m = Message(header, payload)
    
        # is destination address the same as my own address? 
        self.cond.acquire()
        try:
            if addr == self.server_addr:
                if (header.cmd & PROCESS_CMD):
                    # Process message
                    if header.id in self.processes:
                        self.processes[header.id].handle(m)
                    elif (header.cmd & IGN_UNKNOWN):
                        pass
                    else:
                        if not header.id in self.processes_unknown:
                            self.processes_unknown[header.id] = []
                        self.processes_unknown[header.id].append(m)
                elif (header.cmd & GUARD_CMD and header.id in self.guards):
                    # Guard message
                    self.guards[header.id].put_reply(m)
                else:
                    # Channel message
                    if header.id in self.channels:
                        self.channels[header.id].put_reply(m)
                    elif (header.cmd & IGN_UNKNOWN):
                        pass
                    else:
                        if not header.id in self.channels_unknown:
                            self.channels_unknown[header.id] = QueueBuffer()
                        self.channels_unknown[header.id].put_reply(m)                
            else:
                if otherhandler:
                    m.transmit(otherhandler, addr)
                else:
                    m.transmit(self.handler, addr)
        finally:
            self.cond.release()
        

        

