"""
Protocol module

Handles the protocol for the synchronisation model

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
from exceptions import *
from pycsp.common.const import *
from configuration import *


# Header CMDs:
LOCKTHREAD_ACQUIRE_LOCK, LOCKTHREAD_ACCEPT_LOCK, LOCKTHREAD_NOTIFY_SUCCESS, LOCKTHREAD_POISON, LOCKTHREAD_RETIRE, LOCKTHREAD_RELEASE_LOCK, LOCKTHREAD_SHUTDOWN = range(7)
CHANTHREAD_JOIN_READER, CHANTHREAD_JOIN_WRITER, CHANTHREAD_LEAVE_READER, CHANTHREAD_LEAVE_WRITER, CHANTHREAD_RETIRE_READER, CHANTHREAD_RETIRE_WRITER, CHANTHREAD_POISON = range(10,17)
CHANTHREAD_REGISTER, CHANTHREAD_DEREGISTER = range(17,19)
CHANTHREAD_POST_READ, CHANTHREAD_POST_WRITE = range(20,22)



# Header fields:
H_CMD, H_ID = range(2)
H_MSG_SIZE = 2
H_ARG = 2
H_SEQ = 3

# = : Native byte-order, standard size
# H : short, CMD
# 16s : string, uuid1 in bytes format
# L : long, payload size following this header
# L : long, sequence number used for ignoring channel requests, that was left behind.
header_fmt = "=H16sLL"
header_size = struct.calcsize(header_fmt)

conf = Configuration()

def data2bin(s):
    s = pickle.dumps(s, protocol = PICKLE_PROTOCOL)
    return s

def bin2data(s):
    s =  pickle.loads(s)
    return s

def register(channel):
    """
    Registers a channel reference at the channel home thread
    """
    try:
        send(channel.channelhome, CHANTHREAD_REGISTER, channel.name)
    except SocketException:
        # Unable to register at channel home thread
        raise ChannelSocketException(channel.channelhome, "PyCSP (register channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))

def deregister(channel):
    try:
        send(channel.channelhome, CHANTHREAD_DEREGISTER, channel.name)
    except SocketException:
        # Unable to deregister at channel home thread
        # The channel thread may have closed, thus this is an acceptable situation.
        pass
    
def join_reader(channel):
    try:
        send(channel.channelhome, CHANTHREAD_JOIN_READER, channel.name)
    except SocketException:
        # Unable to join channel
        raise ChannelSocketException(channel.channelhome, "PyCSP (join channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))

def join_writer(channel):
    try:
        send(channel.channelhome, CHANTHREAD_JOIN_WRITER, channel.name)
    except SocketException:
        # Unable to join channel
        raise ChannelSocketException(channel.channelhome, "PyCSP (join channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))

def leave_reader(channel):
    try:
        send(channel.channelhome, CHANTHREAD_LEAVE_READER, channel.name)
    except SocketException:
        # Unable to decrement reader count on channel
        if conf.get(SOCKETS_STRICT_MODE):
            raise ChannelSocketException(channel.channelhome, "PyCSP (leave channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
        else:
            sys.stderr.write("PyCSP (leave channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))

def leave_writer(channel):
    try:
        send(channel.channelhome, CHANTHREAD_LEAVE_WRITER, channel.name)
    except SocketException:
        # Unable to decrement writer count on channel
        if conf.get(SOCKETS_STRICT_MODE):
            raise ChannelSocketException(channel.channelhome, "PyCSP (leave channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
        else:
            sys.stderr.write("PyCSP (leave channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))

def retire_reader(channel):
    try:
        send(channel.channelhome, CHANTHREAD_RETIRE_READER, channel.name)
    except SocketException:
        # Unable to retire from channel
        if conf.get(SOCKETS_STRICT_MODE):
            raise ChannelSocketException(channel.channelhome, "PyCSP (retire from channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
        else:
            sys.stderr.write("PyCSP (retire from channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))

def retire_writer(channel):
    try:
        send(channel.channelhome, CHANTHREAD_RETIRE_WRITER, channel.name)
    except SocketException:
        # Unable to retire from channel
        if conf.get(SOCKETS_STRICT_MODE):
            raise ChannelSocketException(channel.channelhome, "PyCSP (retire from channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
        else:
            sys.stderr.write("PyCSP (retire from channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))

def poison(channel):
    try:
        send(channel.channelhome, CHANTHREAD_POISON, channel.name)
    except SocketException:
        # Unable to poison channel
        if conf.get(SOCKETS_STRICT_MODE):
            raise ChannelSocketException(channel.channelhome, "PyCSP (poison channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
        else:
            sys.stderr.write("PyCSP (poison channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))

def post_read(channel, process):
    try:
        send_payload(channel.channelhome, CHANTHREAD_POST_READ, channel.name, AddrID(process.lockThread.address, process.id), process.sequence_number)
    except SocketException:
        # Unable to post read request to channel home thread
        raise FatalException("PyCSP (post read request) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))

def post_write(channel, process, msg):
    try:
        send_payload(channel.channelhome, CHANTHREAD_POST_WRITE, channel.name, (AddrID(process.lockThread.address, process.id), msg), process.sequence_number)
    except SocketException:
        # Unable to post read request to channel home thread
        raise FatalException("PyCSP (post write request) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))



def send_payload(hostNport, cmd, id, payload, seq=0):
    pickle_payload = data2bin(payload)
    header = compile_header(cmd, id, len(pickle_payload), seq)

    sock = ossocket.connect(hostNport)
    
    sock = ossocket.sendall(sock, header)
    ossocket.sendallNOreconnect(sock, pickle_payload)
    
    ossocket.close(hostNport)

def sendNOcache(dest, cmd, arg=0, seq=0):
    header = compile_header(cmd, dest.id, arg)

    sock = ossocket.connectNOcache(dest.hostNport)
    sock.sendall(header)
    ossocket.closeNOcache(sock)

def send(hostNport, cmd, id, arg=0):
    """
    hostNport = (host, port)
    """
    header = compile_header(cmd, id, arg)

    sock = ossocket.connect(hostNport)
    sock = ossocket.sendall(sock, header)
    ossocket.close(hostNport)
        

def compile_header(cmd, id, arg, seq=0):
    """
    arg is often used as msg_size to indicate the size of the following pickle data section
    """
    return struct.pack(header_fmt, cmd, id, arg, seq)



def remote_acquire_and_get_state(dest):

    if not dest.active:
        return (None, FAIL, 0)
        
    try:
        sock = ossocket.connect(dest.hostNport, reconnect=False)
        if sock:
            ossocket.sendallNOreconnect(sock, compile_header(LOCKTHREAD_ACQUIRE_LOCK, dest.id, 0))
            compiled_header = ossocket.recvall(sock, header_size)
        else:
            compiled_header = ""
    except SocketException:
        ossocket.forceclose(dest.hostNport)
        compiled_header = ""

    if len(compiled_header) != header_size:
        # connection broken.
        # When a channel is unable to acquire the lock for process, the
        # posted request is disabled.

        dest.active = False
        return (None, FAIL, 0)
    
    header = struct.unpack(header_fmt, compiled_header)
    
    return (sock, header[H_ARG], header[H_SEQ])

def remote_notify(sock, dest, result_ch, result_msg):
    if dest.active:
        pickled_data = data2bin((result_ch,result_msg))
        try:
            ossocket.sendallNOreconnect(sock, compile_header(LOCKTHREAD_NOTIFY_SUCCESS, dest.id, len(pickled_data)))
            ossocket.sendallNOreconnect(sock, pickled_data)
        except SocketException:
            ossocket.forceclose(dest.hostNport)
            raise AddrUnavailableException(dest)

def remote_poison(sock, dest):
    if dest.active:
        try:
            ossocket.sendallNOreconnect(sock, compile_header(LOCKTHREAD_POISON, dest.id, 0))
        except SocketException:
            ossocket.forceclose(dest.hostNport)
            raise AddrUnavailableException(dest)

def remote_retire(sock, dest):
    if dest.active:
        try:
            ossocket.sendallNOreconnect(sock, compile_header(LOCKTHREAD_RETIRE, dest.id, 0))
        except SocketException:
            ossocket.forceclose(dest.hostNport)
            raise AddrUnavailableException(dest)

def remote_release(sock, dest):
    """
    Ignore socket exceptions on remote_release
    """
    if dest.active:
        try:
            ossocket.sendallNOreconnect(sock, compile_header(LOCKTHREAD_RELEASE_LOCK, dest.id, 0))
            ossocket.close(dest.hostNport)
        except SocketException:
            ossocket.forceclose(dest.hostNport)

    
class LockThread(threading.Thread):
    def __init__(self, process, cond):
        threading.Thread.__init__(self)

        self.process = process
        self.cond = cond

        # All pycsp processes calls shutdown, thus it will receive a shutdown message before it is terminated.
        self.daemon = False

        self.server_socket, self.address = ossocket.start_server()
        
        self.finished = False
        
    def run(self):
        active_socket_list = [self.server_socket]

        while(not self.finished):
            ready, _, exceptready = select.select(active_socket_list, [], [])
            for s in ready:
                if s == self.server_socket:
                    conn, _ = self.server_socket.accept()
                    active_socket_list.append(conn)
                else:
                    
                    recv_data = s.recv(header_size)
                    if len(recv_data) != header_size:
                    #if not recv_data:
                        # connection disconnected
                        active_socket_list.remove(s)
                        s.close()
                    else:

                        header = struct.unpack(header_fmt, recv_data)

                        if header[H_CMD] == LOCKTHREAD_SHUTDOWN:
                            self.cond.acquire()
                            self.finished = True
                            self.cond.notify()
                            self.cond.release()

                        elif header[H_CMD] == LOCKTHREAD_ACQUIRE_LOCK:
                            process_id = header[H_ID]
                            # The ID is not really necessary, since everything is kept in a local state.
                            # This will change when a lockthread handles multiple processes.

                            # Send reply
                            s.sendall(compile_header(LOCKTHREAD_ACCEPT_LOCK, process_id, self.process.state, seq=self.process.sequence_number))

                            lock_acquired = True


                            while (lock_acquired):
                                compiled_header = s.recv(header_size)
                                #if len(compiled_header) == 0:
                                if len(compiled_header) != header_size:
                                    # connection broken.
                                    raise Exception("connection broken")

                                header = struct.unpack(header_fmt, compiled_header)

                                if header[H_CMD] == LOCKTHREAD_NOTIFY_SUCCESS:
                                    self.cond.acquire()

                                    if self.process.state != READY:
                                        raise Exception("PyCSP Panic")
                                    
                                    result_ch, result_msg = bin2data(ossocket.recvall(s, header[H_MSG_SIZE]))
                                    self.process.result_ch = result_ch
                                    self.process.result_msg = result_msg
                                    self.process.state = SUCCESS
                                    self.cond.notifyAll()
                                    self.cond.release()

                                if header[H_CMD] == LOCKTHREAD_POISON:
                                    self.cond.acquire()
                                    
                                    if self.process.state == READY:
                                        self.process.state = POISON
                                        self.cond.notifyAll()
                                    self.cond.release()

                                if header[H_CMD] == LOCKTHREAD_RETIRE:
                                    self.cond.acquire()
                                    
                                    if self.process.state == READY:
                                        self.process.state = RETIRE
                                        self.cond.notifyAll()
                                    self.cond.release()

                                if header[H_CMD] == LOCKTHREAD_RELEASE_LOCK:
                                    lock_acquired = False
                  
        # Close server and spawned sockets
        for s in active_socket_list:
            s.close()
        self.server_socket.close()

    def shutdown(self):

        sendNOcache(AddrID(self.address), LOCKTHREAD_SHUTDOWN)
        
        # This method is called by another thread.
        # The LockThread of a process may shutdown before all posted requests have been
        # removed. A channel may therefore try to communicate to this lockthread. A failure
        # in connecting must be viewed as the posted requests is no longer active.

        # Another concern is if some other process willing to communicate starts a lockthread
        # on the same port. This must be avoided by using a key as identification. Though this
        # is probably not a problem when multiple processes will be handled by single lockthread
        # processes


class Buffer(object):
    def __init__(self, max):
        self.max = max
        self.items = []

        self.ispoisoned = False
        self.isretired = False
        
    def isfull(self):
        return len(self.items) == self.max

    def insertfrom(self, writer):
        success = False
        remove_write = False

        # Check for available buffer space
        if len(self.items) < self.max:

            try:
                w_conn, w_state, w_seq = remote_acquire_and_get_state(writer.process)

                if w_seq != writer.seq_check:
                    w_state = FAIL

                if (w_state == READY):
                    self.items.append(writer.msg)
                    remote_notify(w_conn, writer.process, writer.ch_id, None)
                    success = True

                    w_state = SUCCESS

                # Schedule removal of NOT READY requests from channel
                if (w_state != READY):
                    remove_write = True

                remote_release(writer.process)
            except AddrUnavailableException:
                remove_write = True

        return (remove_write, success)

    def putinto(self, reader):
        success = False
        remove_read = False

        # Check for available buffer items
        if self.items:

            try:
                r_conn, r_state, r_seq = remote_acquire_and_get_state(reader.process)
                
                if r_seq != reader.seq_check:
                    r_state = FAIL

                if (r_state == READY):
                    msg = self.items.pop(0)
                    remote_notify(r_conn, reader.process, reader.ch_id, msg)
                    success = True

                    r_state = SUCCESS

                # Schedule removal of NOT READY requests from channel
                if (r_state != READY):
                    remove_read = True

                remote_release(r_conn, reader.process)
            except AddrUnavailableException:
                remove_read = True

        return (remove_read, success)
    
        
class ChannelHome(object):
    def __init__(self, name, buffer):
        self.readqueue=[]
        self.writequeue=[]
        self.ispoisoned=False
        self.isretired=False
        self.retiring=False
        self.readers=0
        self.writers=0

        self.channelreferences = 0
        
        self.name = name

        if buffer > 0:
            self.buffer = Buffer(buffer)
        else:
            self.buffer = None

    def check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()

    def post_read(self, req):
        self.check_termination()

        success = True
        if self.isretired or self.ispoisoned:
            success = False
        else:
            self.readqueue.append(req)

        if success:
            self.match()
        else:
            self.check_termination()


    def post_write(self, req):
        self.check_termination()

        success = True
        if self.isretired or self.ispoisoned:
            success = False
        else:
            self.writequeue.append(req)

        if success:
            self.match()
        else:
            self.check_termination()

    def match(self):
        if self.buffer:
            # Buffering is enabled.
            
            if self.buffer.isfull():
                # Extract item
                for r in self.readqueue[:]:
                    remove_read, success = self.buffer.putinto(r)
                    if remove_read:
                        self.readqueue.remove(r)
                    if success:
                        break
                
                # Insert item
                for w in self.writequeue[:]:
                    remove_write, success = self.buffer.insertfrom(w)
                    if remove_write:
                        self.writequeue.remove(w)
                    if success:
                        break
            else:
                # Insert item
                for w in self.writequeue[:]:
                    remove_write, success = self.buffer.insertfrom(w)
                    if remove_write:
                        self.writequeue.remove(w)
                    if success:
                        break

                # Extract item
                for r in self.readqueue[:]:
                    remove_read, success = self.buffer.putinto(r)
                    if remove_read:
                        self.readqueue.remove(r)
                    if success:
                        break

        else:
            # Standard matching if no buffer
            for w in self.writequeue[:]:
                for r in self.readqueue[:]:
                    remove_write, remove_read, success = w.offer(r)
                    if remove_read:
                        self.readqueue.remove(r)
                    if remove_write:
                        self.writequeue.remove(w)
                        if success:
                            return # break match loop on first success
                        break
                    if success:
                        return # break match loop on first success

    def poison(self):
        self.ispoisoned=True
        
        for p in self.readqueue:
            p.poison()

        for p in self.writequeue:
            p.poison()

        # flush all requests
        self.readqueue = []
        self.writequeue = []

    def retire_reader(self):
        self.leave_reader()
        if not self.isretired:
            self.retiring = True
            if self.readers==0:
                self.isretired= True
                for p in self.writequeue:
                    p.retire()                    
                self.writequeue = []
                
    def retire_writer(self):
        self.leave_writer()
        if not self.isretired:
            self.retiring = True
            if self.writers==0:
                self.isretired= True
                for p in self.readqueue:
                    p.retire()                    
                self.readqueue = []
                
    def join_reader(self):
        self.readers+=1

    def join_writer(self):
        self.writers+=1

    def leave_reader(self):
        self.readers-=1

    def leave_writer(self):
        self.writers-=1

    def register(self):
        self.channelreferences += 1
        
    def deregister(self):
        self.channelreferences -= 1
        if self.channelreferences == 0:
            # Shutdown
            return True
        return False
    
class AddrID(object):
    def __init__(self, addr=('',0), id=""):
        self.hostNport = addr
        self.id = id
        self.active = True
        
    def __str__(self):
        return repr("%s %s" % (self.hostNport, self.id))


class ChannelReq(object):
    def __init__(self, process_src, process_seq, ch_id, msg = None):
        self.process = process_src
        self.ch_id = ch_id
        self.msg = msg

        # check_sequence contains a number which must be equivalent with the sequence
        # number returned by remote_acquire_and_get_state.
        self.seq_check = process_seq

    def cancel(self):
        try:
            conn, state, seq = remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                remote_cancel(conn, self.process)
            remote_release(conn, self.process)
        except AddrUnavailableException as e:
            # Unable to reach process to notify cancel
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP (cancel notification) unable to reach process (%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP (cancel notification) unable to reach process (%s)\n" % str(self.process))
 
    def poison(self):
        try:
            conn, state, seq = remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                remote_poison(conn, self.process)
            remote_release(conn, self.process)
        except AddrUnavailableException:
            # Unable to reach process to notify poison
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP (poison notification) unable to reach process (%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP (poison notification) unable to reach process (%s)\n" % str(self.process))
            
    def retire(self):
        try:
            conn, state, seq = remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                remote_retire(conn, self.process)
            remote_release(conn, self.process)
        except AddrUnavailableException:
            # Unable to reach process to notify retire
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP (retire notification) unable to reach process (%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP (retire notification) unable to reach process (%s)\n" % str(self.process))
            

    def offer(self, reader):
        success = False
        remove_write = False
        remove_read = False

        try:
            # Acquire double lock
            if (self.process.id < reader.process.id):
                w_conn, w_state, w_seq = remote_acquire_and_get_state(self.process)
                r_conn, r_state, r_seq = remote_acquire_and_get_state(reader.process)
            else:
                r_conn, r_state, r_seq = remote_acquire_and_get_state(reader.process)
                w_conn, w_state, w_seq = remote_acquire_and_get_state(self.process)
            
            # Check sequence numbers
            if r_seq != reader.seq_check:
                r_state = FAIL
            if w_seq != self.seq_check:
                w_state = FAIL
            
            # Success?
            if (r_state == READY and w_state == READY):
                remote_notify(r_conn, reader.process, reader.ch_id, self.msg)
                remote_notify(w_conn, self.process, self.ch_id, None)
                
                success = True

                r_state = SUCCESS 
                w_state = SUCCESS

            # Schedule removal of NOT READY requests from channel
            if (r_state != READY):
                remove_read = True
            if (w_state != READY):
                remove_write = True

            # Release double lock
            if (self.process.id < reader.process.id):
                remote_release(r_conn, reader.process)
                remote_release(w_conn, self.process)
            else:
                remote_release(w_conn, self.process)
                remote_release(r_conn, reader.process)
        except AddrUnavailableException as e:
            # Unable to reach process during offer
            # The primary reason is probably because a request were part of an alting and the process have exited.
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP unable to reach process during offer(%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP unable to reach process during offer(%s)\n" % str(self.process))

            success = False
            if e.addr == self.process.hostNport:
                remove_write = True
            if e.addr == reader.process.hostNport:
                remove_read = True

            
        return (remove_write, remove_read, success)

class ChannelHomeThread(threading.Thread):
    def __init__(self, name, buffer, addr = None):
        threading.Thread.__init__(self)

        # This may cause the thread to terminate unexpectedly and thus
        # leave processes in an inconsistent state.
        # To enforce a nice shutdown, the Shutdown function must be called
        # by the user
        self.daemon = False

        self.channel = ChannelHome(name, buffer)

        if not addr:
            if os.environ.has_key(ENVVAL_PORT):
                addr = ('', int(os.environ[ENVVAL_PORT]))
            else:
                addr = ('', 0)

        self.server_socket, self.address = ossocket.start_server(server_addr=addr)
        self.id = name

    def run(self):
        active_socket_list = [self.server_socket]

        while(True):
            ready, _, exceptready = select.select(active_socket_list, [], [])
            for s in ready:
                if s == self.server_socket:
                    conn, _ = self.server_socket.accept()
                    active_socket_list.append(conn)
                else:
                    recv_data = s.recv(header_size)                    
                    #if not recv_data:
                    if len(recv_data) != header_size:
                        # connection disconnected
                        active_socket_list.remove(s)
                        s.close()
                    else:
                        header = struct.unpack(header_fmt, recv_data)

                        if header[H_CMD] == CHANTHREAD_JOIN_READER:
                            self.channel.join_reader()
                        elif header[H_CMD] == CHANTHREAD_JOIN_WRITER:
                            self.channel.join_writer()
                        elif header[H_CMD] == CHANTHREAD_LEAVE_READER:
                            self.channel.leave_reader()
                        elif header[H_CMD] == CHANTHREAD_LEAVE_WRITER:
                            self.channel.leave_writer()
                        elif header[H_CMD] == CHANTHREAD_RETIRE_READER:
                            self.channel.retire_reader()
                        elif header[H_CMD] == CHANTHREAD_RETIRE_WRITER:
                            self.channel.retire_writer()
                        elif header[H_CMD] == CHANTHREAD_REGISTER:
                            self.channel.register()
                        elif header[H_CMD] == CHANTHREAD_DEREGISTER:
                            if self.channel.deregister():
                                # Force shutdown
                                # TODO: Ensure that the channel is unused
                                for s2 in active_socket_list:
                                    s2.close()
                                self.server_socket.close()

                                return
                                
                        elif header[H_CMD] == CHANTHREAD_POISON:
                            self.channel.poison()

                        elif header[H_CMD] == CHANTHREAD_POST_WRITE:
                            # Read messageparts until entire msg is received
                            data = ossocket.recvall(s, header[H_MSG_SIZE])
                            try:
                                (process, msg) = bin2data(data)
                            except Exception, e:
                                print "POST_WRITE"
                                print header[H_MSG_SIZE], len(data)
                                print data
                                print e
                                raise e
                            try:
                                self.channel.post_write(ChannelReq(process, header[H_SEQ], self.channel.name, msg))
                            except ChannelPoisonException:
                                try:                    
                                    lock_s, state, seq = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            remote_poison(lock_s, process)
                                    remote_release(lock_s, process)
                                except AddrUnavailableException:
                                    # Unable to reach process to notify poison
                                    if conf.get(SOCKETS_STRICT_MODE):
                                        raise FatalException("PyCSP (poison notification:2) unable to reach process (%s)" % str(process))
                                    else:
                                        sys.stderr.write("PyCSP (poison notification:2) unable to reach process (%s)\n" % str(process))

                            except ChannelRetireException:
                                try:                    
                                    lock_s, state, seq = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            remote_retire(lock_s, process)
                                    remote_release(lock_s, process)
                                except AddrUnavailableException:
                                    # Unable to reach process to notify retire
                                    if conf.get(SOCKETS_STRICT_MODE):
                                        raise FatalException("PyCSP (retire notification:2) unable to reach process (%s)" % str(process))
                                    else:
                                        sys.stderr.write("PyCSP (retire notification:2) unable to reach process (%s)\n" % str(process))
                                        
                        elif header[H_CMD] == CHANTHREAD_POST_READ:
                            data = ossocket.recvall(s, header[H_MSG_SIZE])
                            try:
                                process =  bin2data(data)
                            except Exception, e:
                                print "POST_READ"
                                print header[H_MSG_SIZE], len(data)
                                print data
                                print e
                                raise e
                            try:
                                self.channel.post_read(ChannelReq(process, header[H_SEQ], self.channel.name))
                            except ChannelPoisonException:
                                try:                    
                                    lock_s, state, seq = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            remote_poison(lock_s, process)
                                    remote_release(lock_s, process)
                                except AddrUnavailableException:
                                    # Unable to reach process to notify poison
                                    if conf.get(SOCKETS_STRICT_MODE):
                                        raise FatalException("PyCSP (poison notification:3) unable to reach process (%s)" % str(process))
                                    else:
                                        sys.stderr.write("PyCSP (poison notification:3) unable to reach process (%s)\n" % str(process))
                                        
                            except ChannelRetireException:
                                try:                    
                                    lock_s, state, seq = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            remote_retire(lock_s, process)
                                    remote_release(lock_s, process)
                                except AddrUnavailableException:
                                    # Unable to reach process to notify retire
                                    if conf.get(SOCKETS_STRICT_MODE):
                                        raise FatalException("PyCSP (retire notification:3) unable to reach process (%s)" % str(process))
                                    else:
                                        sys.stderr.write("PyCSP (retire notification:3) unable to reach process (%s)\n" % str(process))


def shutdown():
    pass
