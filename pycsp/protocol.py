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
import ossocket
import socket, select, threading
import cPickle as pickle
import struct
from pycsp.common.const import *



# Header CMDs:
LOCKTHREAD_ACQUIRE_LOCK, LOCKTHREAD_ACCEPT_LOCK, LOCKTHREAD_NOTIFY_SUCCESS, LOCKTHREAD_POISON, LOCKTHREAD_RETIRE, LOCKTHREAD_RELEASE_LOCK = range(6)
CHANTHREAD_JOIN_READER, CHANTHREAD_JOIN_WRITER, CHANTHREAD_LEAVE_READER, CHANTHREAD_LEAVE_WRITER, CHANTHREAD_POISON = range(10,15)
CHANTHREAD_POST_READ, CHANTHREAD_POST_WRITE = range(20,22)
SHUTDOWN = 30


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

def join_reader(channel):
    send(channel.channelhome, CHANTHREAD_JOIN_READER, channel.name)

def join_writer(channel):
    send(channel.channelhome, CHANTHREAD_JOIN_WRITER, channel.name)

def leave_reader(channel):
    send(channel.channelhome, CHANTHREAD_LEAVE_READER, channel.name)

def leave_writer(channel):
    send(channel.channelhome, CHANTHREAD_LEAVE_WRITER, channel.name)

def poison(channel):
    send(channel.channelhome, CHANTHREAD_POISON, channel.name)

def post_read(channel, process):
    send_payload(channel.channelhome, CHANTHREAD_POST_READ, channel.name, AddrID(process.lockThread.address, process.id), process.sequence_number)

def post_write(channel, process, msg):
    send_payload(channel.channelhome, CHANTHREAD_POST_WRITE, channel.name, (AddrID(process.lockThread.address, process.id), msg), process.sequence_number)


def send_payload(hostNport, cmd, id, payload, seq=0):
    pickle_payload = pickle.dumps(payload, protocol = pickle.HIGHEST_PROTOCOL)
    header = compile_header(cmd, id, len(pickle_payload), seq)

    sock = ossocket.connect(hostNport)
    
    sock.sendall(header)
    sock.sendall(pickle_payload)
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
    sock.sendall(header)
    ossocket.close(hostNport)

def compile_header(cmd, id, arg, seq=0):
    """
    arg is often used as msg_size to indicate the size of the following pickle data section
    """
    return struct.pack(header_fmt, cmd, id, arg, seq)



def remote_acquire_and_get_state(dest):

    sock = ossocket.connect(dest.hostNport)

    try:
        sock.sendall(compile_header(LOCKTHREAD_ACQUIRE_LOCK, dest.id, 0))
        compiled_header = sock.recv(header_size)
    except socket.error, (value,message): 
        if sock: 
            sock.close()             
        compiled_header = ""
    

    if len(compiled_header) == 0:
        # connection broken.
        # When a channel is unable to acquire the lock for process, the
        # posted request is disabled.
        raise SocketClosedException()

    header = struct.unpack(header_fmt, compiled_header)
    
    return (sock, header[H_ARG], header[H_SEQ])

def remote_notify(sock, dest, result_ch, result_msg):
    pickled_data = pickle.dumps((result_ch,result_msg), pickle.HIGHEST_PROTOCOL)
    sock.sendall(compile_header(LOCKTHREAD_NOTIFY_SUCCESS, dest.id, len(pickled_data)))
    sock.sendall(pickled_data)

def remote_poison(sock, dest):
    sock.sendall(compile_header(LOCKTHREAD_POISON, dest.id, 0))

def remote_retire(sock, dest):
    sock.sendall(compile_header(LOCKTHREAD_RETIRE, dest.id, 0))

def remote_release(dest):
    ossocket.sendall(dest.hostNport, compile_header(LOCKTHREAD_RELEASE_LOCK, dest.id, 0))
    ossocket.close(dest.hostNport)
    
class LockThread(threading.Thread):
    def __init__(self, process, cond):
        threading.Thread.__init__(self)

        self.process = process
        self.cond = cond

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
                    if not recv_data:
                        # connection disconnected
                        active_socket_list.remove(s)
                        s.close()
                    else:

                        header = struct.unpack(header_fmt, recv_data)

                        if header[H_CMD] == SHUTDOWN:
                            self.finished = True

                        elif header[H_CMD] == LOCKTHREAD_ACQUIRE_LOCK:
                            process_id = header[H_ID]
                            # The ID is not really necessary, since everything is kept in a local state.
                            # This will change when a lockthread handles multiple processes.

                            # Send reply
                            s.sendall(compile_header(LOCKTHREAD_ACCEPT_LOCK, process_id, self.process.state, seq=self.process.sequence_number))

                            lock_acquired = True


                            while (lock_acquired):
                                compiled_header = s.recv(header_size)
                                if len(compiled_header) == 0:
                                    # connection broken.
                                    raise Exception("connection broken")

                                header = struct.unpack(header_fmt, compiled_header)

                                if header[H_CMD] == LOCKTHREAD_NOTIFY_SUCCESS:
                                    self.cond.acquire()
                                    result_ch, result_msg = pickle.loads(s.recv(header[H_MSG_SIZE]))
                                    self.process.result_ch = result_ch
                                    self.process.result_msg = result_msg
                                    self.process.state = SUCCESS
                                    self.cond.notifyAll()
                                    self.cond.release()

                                if header[H_CMD] == LOCKTHREAD_POISON:
                                    self.cond.acquire()
                                    self.process.state = POISON
                                    self.cond.notifyAll()
                                    self.cond.release()

                                if header[H_CMD] == LOCKTHREAD_RETIRE:
                                    self.cond.acquire()
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

        sendNOcache(AddrID(self.address), SHUTDOWN)
        
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

    def isfull(self):
        return len(self.items) == self.max

    def insertfrom(self, writer):
        success = False

        # Check for available buffer space
        if len(self.items) < self.max:

            # Check validity
            if writer.done == False:

                try:
                    w_conn, w_state, w_seq = remote_acquire_and_get_state(writer.addr)
                    

                    if (w_state == READY):
                        writer.done = True
                        self.items.append(writer.msg)
                        remote_notify(w_conn, 42, None)
                        success = True

                    remote_release(writer.addr)
                except SocketClosedException:
                    pass

        return success

    def putinto(self, reader):
        success = False

        # Check for available buffer items
        if self.items:

            # Check validity
            if reader.done == False:

                try:
                    r_conn, r_state = remote_acquire_and_get_state(reader.addr)

                    if (r_state == READY):
                        reader.done = True
                        msg = self.items.pop(0)
                        remote_notify(r_conn, 42, msg)
                        success = True

                    remote_release(reader.addr)
                except SocketClosedException:
                    pass

        return success
    
        
class ChannelHome(object):
    def __init__(self, name, buffer):
        self.readqueue=[]
        self.writequeue=[]
        self.ispoisoned=False
        self.isretired=False
        self.readers=0
        self.writers=0

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

    def check_shutdown(self):
        """
        Only call this method when the channel has been poisoned or retired
        """
        if self.ispoisoned or self.isretired:
            #import inspect
            
            #print self.readers,self.writers
            #import threading
            import inspect
            print "check_shutdown: %s" % (inspect.getouterframes(inspect.currentframe())[1][3])
            #print threading.current_thread().name
            if self.readers == 0 and self.writers == 0:
                print "shutdown"

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
            # If buffering is enabled.
            
            if self.buffer.isfull():
                # Extract item
                for r in self.readqueue:
                    if self.buffer.putinto(r):
                        break
                
                # Insert item
                for w in self.writequeue:
                    if self.buffer.insertfrom(w):
                        break
            else:
                # Insert item
                for w in self.writequeue:
                    if self.buffer.insertfrom(w):
                        break

                # Extract item
                for r in self.readqueue:
                    if self.buffer.putinto(r):
                        break

        else:
            # Standard matching if no buffer
            for w in self.writequeue[:]:
                for r in self.readqueue[:]:
                    remove_write, remove_read, success = w.offer(r)
                    if remove_write:                        
                        self.writequeue.remove(w)
                    if remove_read:
                        self.readqueue.remove(r)
                    if success:
                        return # break match loop on first success


    def poison(self):
        self.ispoisoned=True
        
        # counting to shutdown        
        self.readers -= len(self.readqueue) 
        self.writers -= len(self.writequeue)

        for p in self.readqueue:
            p.poison()

        for p in self.writequeue:
            p.poison()

        # flush all requests
        self.readqueue = []
        self.writequeue = []

        self.check_shutdown()

    def join_reader(self):
        self.readers+=1

    def join_writer(self):
        self.writers+=1

    def leave_reader(self):
        if not self.isretired:
            self.readers-=1
            if self.readers==0:
                # Set channel retired
                self.isretired = True

                self.writers-= len(self.writequeue) # counting to shutdown
                for p in self.writequeue:
                    p.retire()                    
                self.writequeue = []

        self.check_shutdown()

    def leave_writer(self):
        if not self.isretired:
            self.writers-=1
            if self.writers==0:
                # Set channel retired
                self.isretired = True
                
                self.readers-= len(self.readqueue) # counting to shutdown
                for p in self.readqueue:
                    p.retire()
                self.readqueue = []

        self.check_shutdown()

class AddrID(object):
    def __init__(self, addr=('',0), id=""):
        self.hostNport = addr
        self.id = id

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
            remote_release(self.process)
        except SocketClosedException:
            pass

    def poison(self):
        try:
            conn, state, seq = remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                remote_poison(conn, self.process)
            remote_release(self.process)
        except SocketClosedException:
            pass

    def retire(self):
        try:
            conn, state, seq = remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                remote_retire(conn, self.process)
            remote_release(self.process)
        except SocketClosedException:
            pass
    
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
            
            if r_seq != reader.seq_check:
                r_state = FAIL
                print("FAIL %d %d" % (r_seq, reader.seq_check))

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
                remote_release(reader.process)
                remote_release(self.process)
            else:
                remote_release(self.process)
                remote_release(reader.process)
        except SocketClosedException:
            pass

        return (remove_write, remove_read, success)



class ChannelHomeThread(threading.Thread):
    def __init__(self, name, buffer):
        threading.Thread.__init__(self)

        self.channel = ChannelHome(name, buffer)
        self.server_socket, self.address = ossocket.start_server()

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
                    if not recv_data:
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
                            self.channel.join_writer()
                        elif header[H_CMD] == CHANTHREAD_POISON:
                            self.channel.poison()

                        elif header[H_CMD] == CHANTHREAD_POST_WRITE:
                            (process, msg) = pickle.loads(s.recv(header[H_MSG_SIZE]))
                            try:
                                self.channel.post_write(ChannelReq(process, header[H_SEQ], self.channel.name, msg))
                            except ChannelPoisonException:
                                try:                    
                                    lock_s, state, seq = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            remote_poison(lock_s, process)
                                            self.channel.writers-=1  # counting to shutdown
                                    remote_release(process)
                                except SocketClosedException:
                                    self.channel.writers-=1 # counting to shutdown

                            except ChannelRetireException:
                                try:                    
                                    lock_s, state, seq = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            remote_retire(lock_s, process)
                                            self.channel.writers-=1  # counting to shutdown
                                    remote_release(process)
                                except SocketClosedException:
                                    self.channel.writers-=1  # counting to shutdown
                            self.channel.check_shutdown()

                        elif header[H_CMD] == CHANTHREAD_POST_READ:
                            process = pickle.loads(s.recv(header[H_MSG_SIZE]))
                            try:
                                self.channel.post_read(ChannelReq(process, header[H_SEQ], self.channel.name))
                            except ChannelPoisonException:
                                try:                    
                                    lock_s, state, seq = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            remote_poison(lock_s, process)
                                            self.channel.readers-=1  # counting to shutdown
                                    remote_release(process)
                                except SocketClosedException:
                                    self.channel.readers-=1  # counting to shutdown
                            except ChannelRetireException:
                                try:                    
                                    lock_s, state = remote_acquire_and_get_state(process)
                                    if seq == header[H_SEQ]:
                                        if state == READY:
                                            self.channel.readers-=1  # counting to shutdown
                                            remote_retire(lock_s, process)
                                    remote_release(process)
                                except SocketClosedException:
                                    self.channel.readers-=1  # counting to shutdown
                            self.channel.check_shutdown()
                

    def shutdown(self):
        pass
        #server.shutdown()
