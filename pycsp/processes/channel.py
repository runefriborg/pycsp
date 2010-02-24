"""
Channel module

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

# Imports
import ctypes
import cPickle as pickle
import sys
import multiprocessing as mp
import mem
from configuration import *
from channelend import ChannelEndRead, ChannelEndWrite, ChannelRetireException
from const import *

# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

# Classes
class ReqStatusSyncData(ctypes.Structure):
    _fields_ = [("state", ctypes.c_int),
                ("condition_id", ctypes.c_int)]

class ChannelReqSyncData(ctypes.Structure):
    _fields_ = [("result",ctypes.c_int),
                ("status_id",ctypes.c_int),
                ("mem_id",ctypes.c_int)]

class ChannelSyncData(ctypes.Structure):
    _fields_ = [("readers",ctypes.c_int),
                ("writers",ctypes.c_int),
                ("ispoisoned",ctypes.c_int),
                ("isretired",ctypes.c_int),
                ("copies",ctypes.c_int),
                ("readqueue",ctypes.c_int*Configuration().get(PROCESSES_ALLOC_QUEUE_PER_CHANNEL)),
                ("readqueue_len", ctypes.c_int),
                ("writequeue",ctypes.c_int*Configuration().get(PROCESSES_ALLOC_QUEUE_PER_CHANNEL)),
                ("writequeue_len", ctypes.c_int)]


class ShmManager(object):
    """
    ShmManager is a singleton class.
    
    This manager ensures that we have access to shared lock and data
    references from other processes.

    >>> A = ShmManager(allocate = True)
    >>> B = ShmManager()
    >>> A == B
    True
    
    >>> new_lock_id = ShmManager().SharedRLockPool.new()
    """

    __lockObj = mp.RLock()  # lock object
    __instance = None  # the unique instance

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self, allocate=False):
        pass
    
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        # Critical section start
        cls.__lockObj.acquire()
        try:
            if cls.__instance is None:
                # Initialize **the unique** instance
                cls.__instance = object.__new__(cls)

                # We will only get here, if __instance has not been set by an earlier instantiation
                # of this class.
                # Unless this object is pickled. In this case __instance is None, until __dict__ is set.
                # For this reason we have added the allocate variable, which is false by default.
                #
                if kwargs.has_key('allocate') and kwargs['allocate'] == True:

                    # Initialize members
                    cls.__instance.lock = cls.__lockObj

                    # Ensures atomic access for __del__ methods
                    cls.__instance.global_lock = mp.Lock()

                    # Fetch configuration
                    conf = Configuration()

                    # Allocating lock and data pools
                    cls.__instance.SharedRLockPool     = mem.SharedLockPool(cls.__lockObj, mp.RLock, conf.get(PROCESSES_SHARED_LOCKS))
                    cls.__instance.SharedConditionPool = mem.SharedLockPool(cls.__lockObj, mp.Condition, conf.get(PROCESSES_SHARED_CONDITIONS))

                    cls.__instance.ReqStatusDataPool   = mem.ReusableDataPool(cls.__lockObj, ReqStatusSyncData, conf.get(PROCESSES_ALLOC_CHANNELENDS))
                    cls.__instance.ChannelReqDataPool  = mem.ReusableDataPool(cls.__lockObj, ChannelReqSyncData, conf.get(PROCESSES_ALLOC_CHANNELENDS))
                    cls.__instance.ChannelDataPool     = mem.ReusableDataPool(cls.__lockObj, ChannelSyncData, conf.get(PROCESSES_ALLOC_CHANNELS))
                
                    # Msg buffer memory
                    cls.__instance.MemoryHandler = mem.Memory(cls.__lockObj, conf.get(PROCESSES_ALLOC_MSG_BUFFER), conf.get(PROCESSES_MSG_BUFFER_BLOCKSIZE))

        finally:
            #  Exit from critical section whatever happens
            cls.__lockObj.release()
        # Critical section end

        return cls.__instance
    getInstance = classmethod(getInstance)


    def ReqStatus_reset(self, req_status_id, state=ACTIVE):
        req_status = self.ReqStatusDataPool.get(req_status_id)
        req_status.condition_id = self.SharedConditionPool.new()
        req_status.state = state

    def ReqStatus_wait(self, req_status_id):
        req_status = self.ReqStatusDataPool.get(req_status_id)
        cond = self.SharedConditionPool.get(req_status.condition_id)

        # (optimization) First check. If this fails we can be positive that we do not need to call cond.wait()
        if req_status.state == ACTIVE:
            cond.acquire()
            while req_status.state == ACTIVE:
                cond.wait()
            cond.release()

    def ChannelReq_reset(self, req_id, req_status_id, msg=None, write=False):
        req = self.ChannelReqDataPool.get(req_id)
        if not write:
            req.mem_id = -1
        else:
            s = pickle.dumps(msg, pickle.HIGHEST_PROTOCOL)
            req.mem_id = self.MemoryHandler.alloc_and_write(s)
        
        req.result = FAIL
        req.status_id = req_status_id

    def ChannelReq_poison(self, req_id):
        req = self.ChannelReqDataPool.get(req_id)
        req_status = self.ReqStatusDataPool.get(req.status_id)
        cond = self.SharedConditionPool.get(req_status.condition_id)

        cond.acquire()
        if req.result == FAIL and req_status.state == ACTIVE:
            req_status.state = POISON
            req.result = POISON
            cond.notify_all()
        cond.release()

    def ChannelReq_retire(self, req_id):
        req = self.ChannelReqDataPool.get(req_id)
        req_status = self.ReqStatusDataPool.get(req.status_id)
        cond = self.SharedConditionPool.get(req_status.condition_id)

        cond.acquire()
        if req.result == FAIL and req_status.state == ACTIVE:
            req_status.state = RETIRE
            req.result = RETIRE
            cond.notify_all()
        cond.release()

    def ChannelReq_wait(self, req_id):
        req = self.ChannelReqDataPool.get(req_id)
        req_status = self.ReqStatusDataPool.get(req.status_id)
        cond = self.SharedConditionPool.get(req_status.condition_id)

        # (optimization) First check. If this fails we can be positive that it is ok to skip the locking.
        if req_status.state == ACTIVE:
            cond.acquire()
            while req_status.state == ACTIVE:
                cond.wait()
            cond.release()


    def ChannelReq_offer(self, sender_req_id, recipient_req_id):
        s_req = self.ChannelReqDataPool.get(sender_req_id)
        s_req_status = self.ReqStatusDataPool.get(s_req.status_id)
        r_req = self.ChannelReqDataPool.get(recipient_req_id)
        r_req_status = self.ReqStatusDataPool.get(r_req.status_id)

        # (optimization) First check. If this fails we can be positive that it is ok, to skip the locking.
        if s_req_status.state == r_req_status.state == ACTIVE:

            s_cond = self.SharedConditionPool.get(s_req_status.condition_id)
            r_cond = self.SharedConditionPool.get(r_req_status.condition_id)

            # Ensuring to lock in the correct order.
            # To avoid a deadlock in the case two communicating processes, which
            # are sharing the same Conditions in reversed order, are trying to offer
            # at the same time.
            if s_cond < r_cond:
                s_cond.acquire()
                r_cond.acquire()
            else:
                r_cond.acquire()
                s_cond.acquire()

            if s_req_status.state == r_req_status.state == ACTIVE:
                r_req.mem_id= s_req.mem_id
                s_req_status.state=DONE
                s_req.result=SUCCESS
                r_req_status.state=DONE
                r_req.result=SUCCESS
                s_cond.notify_all()
                r_cond.notify_all()

            # Ensuring that we also release in the correct order. ( done in the opposite order of locking )
            if s_cond < r_cond:
                r_cond.release()
                s_cond.release()
            else:
                s_cond.release()
                r_cond.release()

class Channel:
    """ Channel class. Blocking communication
    """

    def __init__(self, name=None):

        if name == None:
            # Create name based on host ID and current time
            import uuid
            name = str(uuid.uuid1())

        self.name=name

        self.conf = Configuration()
        self.manager = ShmManager(allocate=True)

        # Get lock from pool
        self.lock_id = self.manager.SharedRLockPool.new()
        self.lock = self.manager.SharedRLockPool.get(self.lock_id)
        
        # Get datasegment from pool
        self.syncData_id = self.manager.ChannelDataPool.new()
        self.syncData = self.manager.ChannelDataPool.get(self.syncData_id)

        # readqueue and writequeue contains an id for every active reading or writing channel ends
        self.syncData.readqueue_len = 0
        self.syncData.writequeue_len = 0
        
        # Count, makes sure that all processes knows how many channel ends, have retired
        self.syncData.readers = 0
        self.syncData.writers = 0

        self.syncData.ispoisoned = 0
        self.syncData.isretired = 0
        self.syncData.copies = 0
            
    # Destructor
    def __del__(self):
        self.restore()

        # Retire the syncData structure, for later reuse
        self.manager.global_lock.acquire()
        if self.syncData.copies == 0:
            self.manager.ChannelDataPool.retire(self.syncData_id)
        else:
            self.syncData.copies -= 1
        self.manager.global_lock.release()

        # The self.lock is shared and doesn't need to be retired.
        

    def restore(self):
        if self.manager == None:
            self.manager = ShmManager(allocate=True)

        if self.lock == None:
            self.lock = self.manager.SharedRLockPool.get(self.lock_id)

        if self.syncData == None:
            self.syncData = self.manager.ChannelDataPool.get(self.syncData_id)

    def check_termination(self, cleanup_req_id = None):        
        self.restore()

        self.lock.acquire()
        if self.syncData.ispoisoned == 1:
            if cleanup_req_id != None:
                # Clean up
                req = self.manager.ChannelReqDataPool.get(cleanup_req_id)
                self.manager.ReqStatusDataPool.retire(req.status_id)
                self.manager.ChannelReqDataPool.retire(cleanup_req_id)

            self.lock.release()
            raise ChannelPoisonException()
        if self.syncData.isretired == 1:
            if cleanup_req_id != None:
                # Clean up
                req = self.manager.ChannelReqDataPool.get(cleanup_req_id)
                self.manager.ReqStatusDataPool.retire(req.status_id)
                self.manager.ChannelReqDataPool.retire(cleanup_req_id)

            self.lock.release()
            raise ChannelRetireException()
        self.lock.release()

    def _read(self):
        self.restore()

        done=False
        while not done:
            req_id = self.manager.ChannelReqDataPool.new()
            req_status_id = self.manager.ReqStatusDataPool.new()
            self.manager.ReqStatus_reset(req_status_id)
            self.manager.ChannelReq_reset(req_id, req_status_id)

            self.post_read(req_id)
            self.check_termination(cleanup_req_id = req_id)
            self.manager.ChannelReq_wait(req_id)
            self.remove_read(req_id)

            req = self.manager.ChannelReqDataPool.get(req_id)
            if req.result==SUCCESS:
                done=True
                msg = pickle.loads(self.manager.MemoryHandler.read_and_free(req.mem_id))
                
                # Clean up
                self.manager.ReqStatusDataPool.retire(req.status_id)
                self.manager.ChannelReqDataPool.retire(req_id)

                return msg

            self.check_termination(cleanup_req_id = req_id)
            
        print 'We should not get here in read!!!', req.status.state
        return None #Here we should handle that a read was cancled...

    
    def _write(self, msg):
        self.restore()

        self.check_termination()
        done=False
        while not done:
            req_id = self.manager.ChannelReqDataPool.new()
            req_status_id = self.manager.ReqStatusDataPool.new()
            self.manager.ReqStatus_reset(req_status_id)
            self.manager.ChannelReq_reset(req_id, req_status_id, msg, write=True)

            self.post_write(req_id)
            self.manager.ChannelReq_wait(req_id)
            self.remove_write(req_id)

            req = self.manager.ChannelReqDataPool.get(req_id)
            if req.result==SUCCESS:
                done=True

                # Clean up
                self.manager.ReqStatusDataPool.retire(req.status_id)
                self.manager.ChannelReqDataPool.retire(req_id)

                return done
            self.check_termination(cleanup_req_id = req_id)

        print 'We should not get here in write!!!', req.status
        return None #Here we should handle that a read was cancled...

    def post_read(self, req_id):
        self.restore()
        self.check_termination()

        self.lock.acquire()
        if self.conf.get(PROCESSES_ALLOC_QUEUE_PER_CHANNEL) == self.syncData.readqueue_len:
            # queue full
            self.lock.release()
            raise Exception('Internal error: PROCESSES_ALLOC_QUEUE_PER_CHANNEL exceeded in post_read()')

        self.syncData.readqueue[self.syncData.readqueue_len] = req_id
        self.syncData.readqueue_len += 1

        self.lock.release()
        self.match()

    def remove_read(self, req_id):
        self.restore()

        self.lock.acquire()

        for i in xrange(self.syncData.readqueue_len):
            if self.syncData.readqueue[i] == req_id:
                # Replace with last item in queue
                self.syncData.readqueue_len -= 1
                self.syncData.readqueue[i] = self.syncData.readqueue[self.syncData.readqueue_len]
                break
        self.lock.release()

        
    def post_write(self, req_id):
        self.restore()
        self.check_termination()

        self.lock.acquire()
        if self.conf.get(PROCESSES_ALLOC_QUEUE_PER_CHANNEL) == self.syncData.writequeue_len:
            # queue full
            self.lock.release()
            raise Exception('Internal error: PROCESSES_ALLOC_QUEUE_PER_CHANNEL exceeded in post_read()')

        self.syncData.writequeue[self.syncData.writequeue_len] = req_id
        self.syncData.writequeue_len += 1

        self.lock.release()
        self.match()

    def remove_write(self, req_id):
        self.restore()
        self.lock.acquire()

        for i in xrange(self.syncData.writequeue_len):
            if self.syncData.writequeue[i] == req_id:
                # Replace with last item in queue
                self.syncData.writequeue_len -= 1
                self.syncData.writequeue[i] = self.syncData.writequeue[self.syncData.writequeue_len]
                break
        self.lock.release()

    def match(self):
        self.restore()

        self.lock.acquire()
        if self.syncData.readqueue_len > 0 and self.syncData.writequeue_len > 0:
            for w in self.syncData.writequeue[0:self.syncData.writequeue_len]:
                for r in self.syncData.readqueue[0:self.syncData.readqueue_len]:
                    self.manager.ChannelReq_offer(w,r)
        self.lock.release()


    def poison(self):
        self.restore()

        self.lock.acquire()
        self.syncData.ispoisoned = 1
        for req_id in self.syncData.readqueue[0:self.syncData.readqueue_len]:
            self.manager.ChannelReq_poison(req_id)
        for req_id in self.syncData.writequeue[0:self.syncData.writequeue_len]:
            self.manager.ChannelReq_poison(req_id)
        self.lock.release()


    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def reader(self):
        self.join_reader()
        return ChannelEndRead(self)

    def writer(self):
        self.join_writer()
        return ChannelEndWrite(self)

    def join_reader(self):
        self.restore()

        self.lock.acquire()
        self.syncData.readers+=1
        self.lock.release()

    def join_writer(self):
        self.restore()

        self.lock.acquire()
        self.syncData.writers+=1
        self.lock.release()

    def leave_reader(self):
        self.restore()

        self.lock.acquire()
        if self.syncData.isretired != 1:
            self.syncData.readers-=1
            if self.syncData.readers==0:
                # Set channel retired
                self.syncData.isretired = 1
                for req_id in self.syncData.writequeue[0:self.syncData.writequeue_len]:
                    self.manager.ChannelReq_retire(req_id)
        self.lock.release()

    def leave_writer(self):
        self.restore()

        self.lock.acquire()
        if self.syncData.isretired != 1:
            self.syncData.writers-=1
            if self.syncData.writers==0:
                # Set channel retired
                self.syncData.isretired = 1
                for req_id in self.syncData.readqueue[0:self.syncData.readqueue_len]:
                    self.manager.ChannelReq_retire(req_id)
        self.lock.release()        
            

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
