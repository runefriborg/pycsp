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
import cPickle as pickle
import struct
from pycsp.common.const import *


# Header CMDs:
LOCKTHREAD_ACQUIRE_LOCK, LOCKTHREAD_ACCEPT_LOCK, LOCKTHREAD_NOTIFY_SUCCESS, LOCKTHREAD_POISON, LOCKTHREAD_RETIRE, LOCKTHREAD_RELEASE_LOCK = range(6)
CHANTHREAD_JOIN_READER, CHANTHREAD_JOIN_WRITER, CHANTHREAD_LEAVE_READER, CHANTHREAD_LEAVE_WRITER = range(10,14)
CHANTHREAD_POST_READ, CHANTHREAD_REMOVE_READ, CHANTHREAD_POST_WRITE, CHANTHREAD_REMOVE_WRITE = range(20,24)

# Header fields:
H_CMD, H_ID = range(2)
H_MSG_SIZE = 2
H_ARG = 2

# = : Native byte-order, standard size
# h : short, CMD
# l : long, ID
# l : long, payload size following this header
header_fmt = "=hll"
header_size = struct.calcsize(header_fmt)

def join_reader(channel):
    send(channel.channelhome, CHANTHREAD_JOIN_READER, 42)

def join_writer(channel):
    send(channel.channelhome, CHANTHREAD_JOIN_WRITER, 42)

def leave_reader(channel):
    send(channel.channelhome, CHANTHREAD_LEAVE_READER, 42)

def leave_writer(channel):
    send(channel.channelhome, CHANTHREAD_LEAVE_WRITER, 42)

def post_read(channel, process):
    # 42 must later be replaced by the number ID of the channel
    send_payload(channel.channelhome, CHANTHREAD_POST_READ, 42, process.lockThread.address)

def remove_read(channel, process):
    # 42 must later be replaced by the number ID of the channel
    send_payload(channel.channelhome, CHANTHREAD_REMOVE_READ, 42, process.lockThread.address)

def post_write(channel, process, msg):
    # 42 must later be replaced by the number ID of the channel
    send_payload(channel.channelhome, CHANTHREAD_POST_WRITE, 42, (process.lockThread.address, msg))

def remove_write(channel, process):
    # 42 must later be replaced by the number ID of the channel
    send_payload(channel.channelhome, CHANTHREAD_REMOVE_WRITE, 42, process.lockThread.address)


def send_payload(addr, cmd, id, payload):
    pickle_payload = pickle.dumps(payload, protocol = pickle.HIGHEST_PROTOCOL)
    header = compile_header(cmd, id, len(pickle_payload))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(addr)
    sock.sendall(header)
    sock.sendall(pickle_payload)
    sock.close()

def send(addr, cmd, id, arg=0):
    """
    addr = (host, port)
    """
    header = compile_header(cmd, id, arg)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(addr)
    sock.sendall(header)
    sock.close()

def compile_header(cmd, id, arg):
    """
    arg is often used as msg_size to indicate the size of the following pickle data section
    """
    return struct.pack(header_fmt, cmd, id, arg)



def remote_acquire_and_get_state(addr, process_id=42):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(addr)
    sock.sendall(compile_header(LOCKTHREAD_ACQUIRE_LOCK, process_id, 0))

    compiled_header = sock.recv(header_size)

    if len(compiled_header) == 0:
        # connection broken.
        raise Exception("connection broken")
    header = struct.unpack(header_fmt, compiled_header)
    
    return (sock, header[H_ARG])

def remote_notify(sock, result_ch, result_msg, process_id=42):
    data = {'channel':result_ch, 'msg':result_msg}
    pickled_data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
    sock.sendall(compile_header(LOCKTHREAD_NOTIFY_SUCCESS, process_id, len(pickled_data)))
    sock.sendall(pickled_data)

def remote_poison(sock, process_id=42):
    sock.sendall(compile_header(LOCKTHREAD_POISON, process_id, 0))

def remote_retire(sock, process_id=42):
    sock.sendall(compile_header(LOCKTHREAD_RETIRE, process_id, 0))

def remote_release(sock, process_id=42):
    # OPTIMIZE: remove sendall and signal release by closing the socket only
    sock.sendall(compile_header(LOCKTHREAD_RELEASE_LOCK, process_id, 0))
    sock.close()
    
class LockThread(threading.Thread):
    def __init__(self, process, cond):
        threading.Thread.__init__(self)

        self.process = process
        self.cond = cond

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.s.bind(('', 0))
        self.address = self.s.getsockname()
        self.s.listen(5)


    def run(self):
        while(True):            
            conn, addr = self.s.accept()

            compiled_header = conn.recv(header_size)
            if len(compiled_header) == 0:
                # connection broken.
                raise Exception("connection broken")

            header = struct.unpack(header_fmt, compiled_header)

            if header[H_CMD] == LOCKTHREAD_ACQUIRE_LOCK:
                ID = header[H_ID]
                # The ID is not really necessary, since everything is kept in a local state.
                # This will change when a lockthread handles multiple processes.

                # Send reply
                conn.sendall(compile_header(LOCKTHREAD_ACCEPT_LOCK, ID, self.process.state))

                lock_acquired = True


                while (lock_acquired):
                    compiled_header = conn.recv(header_size)
                    if len(compiled_header) == 0:
                        # connection broken.
                        raise Exception("connection broken")

                    header = struct.unpack(header_fmt, compiled_header)

                    if header[H_CMD] == LOCKTHREAD_NOTIFY_SUCCESS:
                        self.cond.acquire()
                        self.process.state = SUCCESS
                        data = pickle.loads(conn.recv(header[H_MSG_SIZE]))
                        self.process.result_ch = data['channel']
                        self.process.result_msg = data['msg']
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
            conn.close()

    def shutdown(self):
        pass
        #server.shutdown()



class ChannelHome(object):
    def __init__(self, buffer=0):
        self.readqueue=[]
        self.writequeue=[]
        self.ispoisoned=False
        self.isretired=False
        self.readers=0
        self.writers=0
    
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
        

    def remove_read(self, addr):
        #Optimize!
        for r in self.readqueue:
            if r.addr == addr:
                self.readqueue.remove(r)
                break

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

    def remove_write(self, addr):
        for w in self.writequeue:
            if w.addr == addr:
                self.writequeue.remove(w)
                break

    def match(self):
        for w in self.writequeue:
            for r in self.readqueue:
                if w.offer(r):
                    return # break match loop on first success

    def poison(self):
        self.ispoisoned=True
        for p in self.readqueue:
            p.poison()
        for p in self.writequeue:
            p.poison()


    def join_reader(self):
        self.readers+=1

    def join_writer(self):
        self.writers+=1

    def leave_reader(self):
        self.lock.acquire()
        if not self.isretired:
            self.readers-=1
            if self.readers==0:
                # Set channel retired
                self.isretired = True
                for p in self.writequeue:
                    p.retire()
        self.lock.release()

    def leave_writer(self):
        self.lock.acquire()
        if not self.isretired:
            self.writers-=1
            if self.writers==0:
                # Set channel retired
                self.isretired = True
                for p in self.readqueue:
                    p.retire()
        self.lock.release()

class ChannelReq(object):
    def __init__(self, process_addr, msg = None):
        self.addr = process_addr
        self.msg = msg
        self.done = False

    def cancel(self):
        conn, state = remote_acquire_and_get_state(self.addr)
        self.done = True
        remote_cancel(conn)
        remote_release(conn)

    def poison(self):
        conn, state = remote_acquire_and_get_state(self.addr)
        if state == READY:
            self.done = True
            remote_poison(conn)
        remote_release(conn)

    def retire(self):
        conn, state = remote_acquire_and_get_state(self.addr)
        if state == READY:
            self.done = True
            remote_retire(conn)
        remote_release(conn)
    
    def offer(self, reader):
        success = False

        # Check validity
        if self.done == False and reader.done == False:

            if (self.addr < reader.addr):
                w_conn, w_state = remote_acquire_and_get_state(self.addr)
                r_conn, r_state = remote_acquire_and_get_state(reader.addr)
            else:
                r_conn, r_state = remote_acquire_and_get_state(reader.addr)
                w_conn, w_state = remote_acquire_and_get_state(self.addr)

            if (r_state == READY and w_state == READY):
                self.done = True
                reader.done = True
                remote_notify(r_conn, 42, self.msg)
                remote_notify(w_conn, 42, None)
                success = True

            if (self.addr < reader.addr):
                remote_release(r_conn)
                remote_release(w_conn)
            else:
                remote_release(w_conn)
                remote_release(r_conn)

        return success


class ChannelHomeThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.channel = ChannelHome()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.s.bind(('', 0))
        self.address = self.s.getsockname()
        self.s.listen(5)

    def run(self):
        while(True):            
            conn, addr = self.s.accept()
            
            compiled_header = conn.recv(header_size)
            if len(compiled_header) == 0:
                # connection broken.
                raise Exception("connection broken")

            header = struct.unpack(header_fmt, compiled_header)

            
            if header[H_CMD] == CHANTHREAD_JOIN_READER:
                self.channel.join_reader()
            elif header[H_CMD] == CHANTHREAD_JOIN_WRITER:
                self.channel.join_writer()
            elif header[H_CMD] == CHANTHREAD_LEAVE_READER:
                self.channel.leave_reader()
            elif header[H_CMD] == CHANTHREAD_LEAVE_WRITER:
                self.channel.join_writer()

            elif header[H_CMD] == CHANTHREAD_POST_WRITE:
                (address, msg) = pickle.loads(conn.recv(header[H_MSG_SIZE]))
                try:
                    self.channel.post_write(ChannelReq(address, msg))
                except ChannelPoisonException:
                    s, state = remote_acquire_and_get_state(addr)
                    if state == READY:
                        remote_poison(s)
                    remote_release(s)
                except ChannelRetireException:
                    s, state = remote_acquire_and_get_state(addr)
                    if state == READY:
                        remote_retire(s)
                    remote_release(s)

            elif header[H_CMD] == CHANTHREAD_REMOVE_WRITE:
                address = pickle.loads(conn.recv(header[H_MSG_SIZE]))
                self.channel.remove_write(address)

            elif header[H_CMD] == CHANTHREAD_POST_READ:
                address = pickle.loads(conn.recv(header[H_MSG_SIZE]))
                try:
                    self.channel.post_read(ChannelReq(address))
                except ChannelPoisonException:
                    s, state = remote_acquire_and_get_state(addr)
                    if state == READY:
                        remote_poison(s)
                    remote_release(s)
                except ChannelRetireException:
                    s, state = remote_acquire_and_get_state(addr)
                    if state == READY:
                        remote_retire(s)
                    remote_release(s)

            elif header[H_CMD] == CHANTHREAD_REMOVE_READ:
                address = pickle.loads(conn.recv(header[H_MSG_SIZE]))
                self.channel.remove_read(address)

            conn.close()
                

    def shutdown(self):
        pass
        #server.shutdown()
