"""
Protocol module

Handles the protocol for the synchronisation model

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

import sys
import threading
from exceptions import *

from header import *
from dispatch import *
from pycsp.common.const import *
from configuration import *


conf = Configuration()

class ChannelMessenger(object):
    def __init__(self):
        self.dispatch = SocketDispatcher().getThread()
        
    def register(self, channel):
        """
        Registers a channel reference at the channel home thread
        """
        try:
            self.dispatch.send(channel.channelhome, 
                                        Header(CHANTHREAD_REGISTER, channel.name))
        except SocketException:
            # Unable to register at channel home thread
            raise ChannelSocketException(channel.channelhome, "PyCSP (register channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))

    def deregister(self, channel):
        try:
            self.dispatch.send(channel.channelhome,
                                        Header(CHANTHREAD_DEREGISTER, channel.name))
        except SocketException:
            # Unable to deregister at channel home thread
            # The channel thread may have closed, thus this is an acceptable situation.
            pass
    
    def join(self, channel, direction):
        try:
            if direction == READ:
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_JOIN_READER, channel.name))
            elif direction == WRITE:
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_JOIN_WRITER, channel.name))
        except SocketException:
            # Unable to join channel
            raise ChannelSocketException(channel.channelhome, "PyCSP (join channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))

    def leave(self, channel, direction):
        try:
            if direction == READ:
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_LEAVE_READER, channel.name))
            elif direction == WRITE:
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_LEAVE_WRITER, channel.name))

        except SocketException:
            # Unable to decrement writer count on channel
            if conf.get(SOCKETS_STRICT_MODE):
                raise ChannelSocketException(channel.channelhome, "PyCSP (leave channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
            else:
                sys.stderr.write("PyCSP (leave channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))

    def retire(self, channel, direction):
        try:
            if direction == READ:
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_RETIRE_READER, channel.name))
            elif direction == WRITE:                
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_RETIRE_WRITER, channel.name))

        except SocketException:
            # Unable to retire from channel
            if conf.get(SOCKETS_STRICT_MODE):
                raise ChannelSocketException(channel.channelhome, "PyCSP (retire from channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
            else:
                sys.stderr.write("PyCSP (retire from channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))

    def poison(self, channel, direction):
        try:
            if direction == READ:
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_POISON_READER, channel.name))
            elif direction == WRITE:
                self.dispatch.send(channel.channelhome,
                                            Header(CHANTHREAD_POISON_WRITER, channel.name))

        except SocketException:
            # Unable to poison channel
            if conf.get(SOCKETS_STRICT_MODE):
                raise ChannelSocketException(channel.channelhome, "PyCSP (poison channel) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))
            else:
                sys.stderr.write("PyCSP (poison channel) unable to reach channel home thread (%s at %s)\n" % (channel.name, str(channel.channelhome)))


    def post_read(self, channel, process):
        try:
            self.dispatch.send(channel.channelhome,
                                        Header(CHANTHREAD_POST_READ, channel.name, process.sequence_number),
                                        AddrID(process.addr, process.id))
        except SocketException:
            # Unable to post read request to channel home thread
            raise FatalException("PyCSP (post read request) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))

    def post_write(self, channel, process, msg):
        try:
            self.dispatch.send(channel.channelhome,
                                        Header(CHANTHREAD_POST_WRITE, channel.name, process.sequence_number),
                                        (AddrID(process.addr, process.id), msg))
        except SocketException:
            # Unable to post read request to channel home thread
            raise FatalException("PyCSP (post write request) unable to reach channel home thread (%s at %s)" % (channel.name, str(channel.channelhome)))






class LockMessenger(object):
    def __init__(self, channel_id):
        self.dispatch = SocketDispatcher().getThread()
        self.channel_id = channel_id
        self.input = self.dispatch.getChannelQueue(channel_id)

    def remote_acquire_and_get_state(self, dest):
        if not dest.active:
            return (None, FAIL, 0)

        header = Header()
        try:
            h = Header(LOCKTHREAD_ACQUIRE_LOCK,  dest.id)
            h._source_id = self.channel_id
            self.dispatch.send(dest.hostNport, h)

            msg = self.input.reply.get()
            
            header = msg.header
        except SocketException:
            header.cmd = 401

        if header.cmd == 401:
            # connection broken.
            # When a channel is unable to acquire the lock for process, the
            # posted request is disabled.

            dest.active = False
            return (None, FAIL, 0)

        if header.cmd != LOCKTHREAD_ACCEPT_LOCK:
            raise Exception("Fatal error!")

        return (header, header.arg, header.seq_number)

    def remote_notify(self, source_header, dest, result_ch, result_msg):
        if dest.active:
            try:
                h = Header(LOCKTHREAD_NOTIFY_SUCCESS, dest.id)
                h._source_id = self.channel_id
                self.dispatch.reply(source_header, h, payload=(result_ch,result_msg))
            except SocketException:
                raise AddrUnavailableException(dest)

    def remote_poison(self, source_header, dest):
        if dest.active:
            try:
                h = Header(LOCKTHREAD_POISON, dest.id)
                h._source_id = self.channel_id
                self.dispatch.reply(source_header, h)
            except SocketException:
                raise AddrUnavailableException(dest)

    def remote_retire(self, source_header, dest):
        if dest.active:
            try:
                h = Header(LOCKTHREAD_RETIRE, dest.id)
                h._source_id = self.channel_id                
                self.dispatch.reply(source_header, h)
            except SocketException:
                raise AddrUnavailableException(dest)

    def remote_release(self, source_header, dest):
        """
        Ignore socket exceptions on remote_release
        """
        if dest.active:
            try:
                h = Header(LOCKTHREAD_RELEASE_LOCK, dest.id)
                h._source_id = self.channel_id
                self.dispatch.reply(source_header, h)
            except SocketException:
                pass
    


class RemoteLock:
    def __init__(self, process):
        self.process = process
        self.cond = process.cond

        self.dispatch = SocketDispatcher().getThread()

        self.waiting = []
        self.lock_acquired = None

    def handle(self, message):        
        header = message.header

        # Check id
        if not (self.process.id == header.id):
            raise Exception("Fatal error!, wrong process ID!")
                
        if header.cmd == LOCKTHREAD_ACQUIRE_LOCK:
            if not self.lock_acquired == None:
                self.waiting.append(message)
            else:
                self.lock_acquired = header._source_id
                
                # Send reply
                self.dispatch.reply(header, Header(LOCKTHREAD_ACCEPT_LOCK, header._source_id, self.process.sequence_number, self.process.state))
                

        elif header.cmd == LOCKTHREAD_NOTIFY_SUCCESS:
            if self.lock_acquired == header._source_id:
                self.cond.acquire()
                if self.process.state != READY:
                    raise Exception("PyCSP Panic")
                        
                self.process.result_ch, self.process.result_msg = message.payload
                self.process.state = SUCCESS
                self.cond.notifyAll()
                self.cond.release()        
            else:
                print "'%s','%s'" %(self.lock_acquired, ) 
                raise Exception("Fatal error!, Remote lock has not been acquired!")

        elif header.cmd == LOCKTHREAD_POISON:
            if self.lock_acquired == header._source_id:
                self.cond.acquire()
                
                if self.process.state == READY:
                    self.process.state = POISON
                    self.cond.notifyAll()
                self.cond.release()
            else:
                raise Exception("Fatal error!, Remote lock has not been acquired!")

        elif header.cmd == LOCKTHREAD_RETIRE:
            if self.lock_acquired == header._source_id:
                self.cond.acquire()
                
                if self.process.state == READY:
                    self.process.state = RETIRE
                    self.cond.notifyAll()
                self.cond.release()
            else:
                raise Exception("Fatal error!, Remote lock has not been acquired!")

        elif header.cmd == LOCKTHREAD_RELEASE_LOCK:
            if self.lock_acquired == header._source_id:
                self.lock_acquired = None
                if self.waiting:
                    self.handle(self.waiting.pop(0))
            else:
                raise Exception("Fatal error!, Remote lock has not been acquired!")


class Buffer(object):
    def __init__(self, LM, max):
        self.max = max
        self.items = []

        self.ispoisoned = False
        self.isretired = False
        self.LM = LM
        
    def isfull(self):
        return len(self.items) == self.max

    def isempty(self):
        return len(self.items) == 0

    def insertfrom(self, writer):
        success = False
        remove_write = False

        # Check for available buffer space
        if len(self.items) < self.max:

            try:
                w_conn, w_state, w_seq = self.LM.remote_acquire_and_get_state(writer.process)

                if w_seq != writer.seq_check:
                    w_state = FAIL

                if (w_state == READY):
                    self.items.append(writer.msg)
                    self.LM.remote_notify(w_conn, writer.process, writer.ch_id, None)
                    success = True

                    w_state = SUCCESS

                # Schedule removal of NOT READY requests from channel
                if (w_state != READY):
                    remove_write = True

                self.LM.remote_release(w_conn, writer.process)
            except AddrUnavailableException:
                remove_write = True

        return (remove_write, success)

    def putinto(self, reader):
        success = False
        remove_read = False

        # Check for available buffer items
        if self.items:

            try:
                r_conn, r_state, r_seq = self.LM.remote_acquire_and_get_state(reader.process)
                
                if r_seq != reader.seq_check:
                    r_state = FAIL

                if (r_state == READY):
                    msg = self.items.pop(0)
                    self.LM.remote_notify(r_conn, reader.process, reader.ch_id, msg)
                    success = True

                    r_state = SUCCESS

                # Schedule removal of NOT READY requests from channel
                if (r_state != READY):
                    remove_read = True

                self.LM.remote_release(r_conn, reader.process)
            except AddrUnavailableException:
                remove_read = True

        return (remove_read, success)
    
        
class ChannelHome(object):
    def __init__(self, name, buffer):
        self.readqueue=[]
        self.writequeue=[]
        self.ispoisoned=False
        self.isretired=False
        self.readers=0
        self.writers=0

        self.channelreferences = 0
        
        self.name = name

        self.LM = LockMessenger(name)

        if buffer > 0:
            self.buffer = Buffer(self.LM, buffer)
        else:
            self.buffer = None

    def check_termination(self):
        """
        This method is invoked on the initial posting of a request.

        It checks the buffer for any poison / retire pill, which has
        been prosponed because of buffered messages. If buffer is now
        empty, then the channel is poisoned / retired.
        """
        if self.buffer:
            # Buffer enabled
            if self.buffer.ispoisoned:
                if self.buffer.isempty():
                    self.poison_writer()

            if self.buffer.isretired:
                if self.buffer.isempty():
                    self.isretired= True
                    for p in self.readqueue:
                        p.retire()                    
                    self.readqueue = []
        
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

    # The method for poisoning non-buffered channels is identical
    # for both the reading and writing end, while the method differs
    # for buffered channels.
    # In buffered channels the poison pill must be propagated through
    # the buffer slots before the other end is poisoned.

    # An exception has been made for the reading end:
    # To allow poisoning to skip
    # buffer slots and instantly poison the writing end.

    def poison_reader(self):
        self.ispoisoned=True
        
        for p in self.readqueue:
            p.poison()

        for p in self.writequeue:
            p.poison()

        # flush all requests
        self.readqueue = []
        self.writequeue = []

    def poison_writer(self):
        if self.buffer and not self.buffer.isempty():
            # Buffer is enabled and has content
            self.buffer.ispoisoned = True

            for p in self.writequeue:
                p.poison()
    
            # flush all write requests
            self.writequeue = []

        else:
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
            if self.readers==0:
                self.isretired= True
                for p in self.writequeue:
                    p.retire()                    
                self.writequeue = []
                
    def retire_writer(self):
        self.leave_writer()
        if not self.isretired:
            if self.writers==0:

                if self.buffer and not self.buffer.isempty():
                    # Buffer is enabled and has content
                    self.buffer.isretired = True
                    
                else:
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
    def __init__(self, LM, process_src, process_seq, ch_id, msg = None):
        self.process = process_src
        self.ch_id = ch_id
        self.msg = msg

        # check_sequence contains a number which must be equivalent with the sequence
        # number returned by remote_acquire_and_get_state.
        self.seq_check = process_seq
        
        self.LM = LM

    def cancel(self):
        try:
            conn, state, seq = self.LM.remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                self.LM.remote_cancel(conn, self.process)
            self.LM.remote_release(conn, self.process)
        except AddrUnavailableException as e:
            # Unable to reach process to notify cancel
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP (cancel notification) unable to reach process (%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP (cancel notification) unable to reach process (%s)\n" % str(self.process))
 
    def poison(self):
        try:
            conn, state, seq = self.LM.remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                self.LM.remote_poison(conn, self.process)
            self.LM.remote_release(conn, self.process)
        except AddrUnavailableException:
            # Unable to reach process to notify poison
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP (poison notification) unable to reach process (%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP (poison notification) unable to reach process (%s)\n" % str(self.process))
            
    def retire(self):
        try:
            conn, state, seq = self.LM.remote_acquire_and_get_state(self.process)
            if seq == self.seq_check:
                self.LM.remote_retire(conn, self.process)
            self.LM.remote_release(conn, self.process)
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
                w_conn, w_state, w_seq = self.LM.remote_acquire_and_get_state(self.process)
                r_conn, r_state, r_seq = self.LM.remote_acquire_and_get_state(reader.process)
            else:
                r_conn, r_state, r_seq = self.LM.remote_acquire_and_get_state(reader.process)
                w_conn, w_state, w_seq = self.LM.remote_acquire_and_get_state(self.process)
            
            # Check sequence numbers
            if r_seq != reader.seq_check:
                r_state = FAIL
            if w_seq != self.seq_check:
                w_state = FAIL
            
            # Success?
            if (r_state == READY and w_state == READY):
                self.LM.remote_notify(r_conn, reader.process, reader.ch_id, self.msg)
                self.LM.remote_notify(w_conn, self.process, self.ch_id, None)
                
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
                self.LM.remote_release(r_conn, reader.process)
                self.LM.remote_release(w_conn, self.process)
            else:
                self.LM.remote_release(w_conn, self.process)
                self.LM.remote_release(r_conn, reader.process)
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

        self.id = name

        self.dispatch = SocketDispatcher().getThread()
        self.addr = self.dispatch.server_addr

        # Returns synchronized Queue object where messages are retrieved from.
        self.input = self.dispatch.registerChannel(self.id)

        self.channel = ChannelHome(name, buffer)

    def run(self):
        LM = self.channel.LM

        while(True):
            msg = self.input.normal.get()
            header = msg.header

            if header.cmd == CHANTHREAD_JOIN_READER:
                self.channel.join_reader()
            elif header.cmd == CHANTHREAD_JOIN_WRITER:
                self.channel.join_writer()
            elif header.cmd == CHANTHREAD_LEAVE_READER:
                self.channel.leave_reader()
            elif header.cmd == CHANTHREAD_LEAVE_WRITER:
                self.channel.leave_writer()
            elif header.cmd == CHANTHREAD_RETIRE_READER:
                self.channel.retire_reader()
            elif header.cmd == CHANTHREAD_RETIRE_WRITER:
                self.channel.retire_writer()
            elif header.cmd == CHANTHREAD_REGISTER:
                self.channel.register()
            elif header.cmd == CHANTHREAD_DEREGISTER:
                if self.channel.deregister():
                    # Force shutdown
                    # TODO: Ensure that the channel is unused
                    # TODO: Check if any unread messages is left in channel?
                    self.dispatch.deregisterChannel(self.id)
                    return

            elif header.cmd == CHANTHREAD_POISON_READER:
                self.channel.poison_reader()

            elif header.cmd == CHANTHREAD_POISON_WRITER:
                self.channel.poison_writer()

            elif header.cmd == CHANTHREAD_POST_WRITE:
                (process, msg) = msg.payload

                
                try:
                    self.channel.post_write(ChannelReq(LM, process, header.seq_number, self.channel.name, msg))
                except ChannelPoisonException:
                    try:                    
                        lock_s, state, seq = LM.remote_acquire_and_get_state(process)
                        if seq == header.seq_number:
                            if state == READY:
                                LM.remote_poison(lock_s, process)
                        LM.remote_release(lock_s, process)
                    except AddrUnavailableException:
                        # Unable to reach process to notify poison
                        if conf.get(SOCKETS_STRICT_MODE):
                            raise FatalException("PyCSP (poison notification:2) unable to reach process (%s)" % str(process))
                        else:
                            sys.stderr.write("PyCSP (poison notification:2) unable to reach process (%s)\n" % str(process))

                except ChannelRetireException:
                    try:                    
                        lock_s, state, seq = LM.remote_acquire_and_get_state(process)
                        if seq == header.seq_number:
                            if state == READY:
                                LM.remote_retire(lock_s, process)
                        LM.remote_release(lock_s, process)
                    except AddrUnavailableException:
                        # Unable to reach process to notify retire
                        if conf.get(SOCKETS_STRICT_MODE):
                            raise FatalException("PyCSP (retire notification:2) unable to reach process (%s)" % str(process))
                        else:
                            sys.stderr.write("PyCSP (retire notification:2) unable to reach process (%s)\n" % str(process))

            elif header.cmd == CHANTHREAD_POST_READ:
                process = msg.payload

                try:
                    self.channel.post_read(ChannelReq(LM, process, header.seq_number, self.channel.name))
                except ChannelPoisonException:
                    try:                    
                        lock_s, state, seq = LM.remote_acquire_and_get_state(process)
                        if seq == header.seq_number:
                            if state == READY:
                                LM.remote_poison(lock_s, process)
                        LM.remote_release(lock_s, process)
                    except AddrUnavailableException:
                        # Unable to reach process to notify poison
                        if conf.get(SOCKETS_STRICT_MODE):
                            raise FatalException("PyCSP (poison notification:3) unable to reach process (%s)" % str(process))
                        else:
                            sys.stderr.write("PyCSP (poison notification:3) unable to reach process (%s)\n" % str(process))

                except ChannelRetireException:
                    try:                    
                        lock_s, state, seq = LM.remote_acquire_and_get_state(process)
                        if seq == header.seq_number:
                            if state == READY:
                                LM.remote_retire(lock_s, process)
                        LM.remote_release(lock_s, process)
                    except AddrUnavailableException:
                        # Unable to reach process to notify retire
                        if conf.get(SOCKETS_STRICT_MODE):
                            raise FatalException("PyCSP (retire notification:3) unable to reach process (%s)" % str(process))
                        else:
                            sys.stderr.write("PyCSP (retire notification:3) unable to reach process (%s)\n" % str(process))


