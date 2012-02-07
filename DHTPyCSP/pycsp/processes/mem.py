"""
This contains classes for managing shared memory usage.

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
import multiprocessing as mp
import ctypes

# Constants
FREE, OCCUPIED = range(2)

# Structures
class FreeStruct(ctypes.Structure):
    _fields_ = [('offset', ctypes.c_int),
                  ('blocks', ctypes.c_int)]
                  
class AllocatedStruct(ctypes.Structure):
    _fields_ = [('size', ctypes.c_int)]
                  
# Classes
class Memory:
    """ 
    Uses next-fit allocation strategy to allocate and free char buffers.

    >>> MSG_MEMORY_SIZE = 1000000
    >>> MSG_MEMORY_BLOCKSIZE = 256
    
    >>> mem = Memory(mp.RLock(), MSG_MEMORY_SIZE, MSG_MEMORY_BLOCKSIZE)
    
    >>> [mem.alloc(100) for i in range(10)]
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    >>> s = 'Hello World'
    >>> hello = mem.alloc(len(s))
    >>> mem.write(hello, s)

    >>> [mem.free(i) for i in range(10)]
    [None, None, None, None, None, None, None, None, None, None]
    
    >>> mem.read(hello)
    'Hello World'

    
    """
    def __init__(self, lock, mem_size, block_size):
        self.data = mp.RawArray(ctypes.c_char, mem_size)

        self.block_count = int(mem_size/block_size)

        self.free_blocks = mp.RawArray(FreeStruct, int(self.block_count))
        self.free_len = mp.RawValue(ctypes.c_int, 0)

        self.allocated_blocks = mp.RawArray(AllocatedStruct, self.block_count)
        self.allocated_len = mp.RawValue(ctypes.c_int, 0)
        
        self.lock = lock
        self.mem_size = mem_size
        self.block_size = block_size

        # Add free memory entry
        self.free_len.value += 1
        self.free_blocks[0].blocks = self.block_count
        self.free_blocks[0].offset = 0
        

    def status(self):
        print 'Allocated entries:', self.allocated_len.value, 'Free entries:', self.free_len.value
        
    def alloc(self, size, defragment=True):

        blocks = int(size / self.block_size) + 1

        self.lock.acquire()
        for i in xrange(self.free_len.value):
            if blocks < self.free_blocks[i].blocks:
                #id = self.allocated_len.value
                #self.allocated_len.value += 1
                #self.allocated_blocks[id].offset = self.free_blocks[i].offset
                offset = self.free_blocks[i].offset
                self.allocated_blocks[offset].size = size

                # Reduce free entry
                self.free_blocks[i].offset += blocks
                self.free_blocks[i].blocks -= blocks
                
                self.lock.release()
                return offset

            elif blocks == self.free_blocks[i].blocks:
                #id = self.allocated_len.value
                #self.allocated_len.value += 1
                #self.allocated_blocks[id].offset = self.free_blocks[i].offset
                offset = self.free_blocks[i].offset
                self.allocated_blocks[offset].size = size
                
                # Delete free entry
                self.free_len.value -= 1
                self.free_blocks[i].offset = self.free_blocks[self.free_len.value].offset
                self.free_blocks[i].blocks = self.free_blocks[self.free_len.value].blocks
                
                self.lock.release()
                return offset


        # Try to defragmentize the free blocks, by merging neighbour fragments
        if defragment:
            print "mem.py: Defragmentation", self.free_len.value # Debugging
            assembled = 0
            i = 0
            while i < self.free_len.value:
                j = 0
                while j < self.free_len.value:
                    if self.free_blocks[i].offset == self.free_blocks[j].offset + self.free_blocks[j].blocks:
                        self.free_blocks[j].blocks += self.free_blocks[i].blocks
                        
                        # Delete free entry
                        self.free_len.value -= 1
                        self.free_blocks[i].offset = self.free_blocks[self.free_len.value].offset
                        self.free_blocks[i].blocks = self.free_blocks[self.free_len.value].blocks
                        
                        # Try this index again, using the new block.
                        i -= 2
                        assembled += 1
                    j += 1          
                i += 1

            print 'mem.py: Assembled', assembled # Debugging
            self.lock.release()
            return self.alloc(size, defragment = False)

        self.lock.release()

        raise Exception("No more blocks!")
    
    def free(self, offset):
        
        blocks = int(self.allocated_blocks[offset].size / self.block_size) + 1

        self.lock.acquire()
        # Add free entry
        self.free_blocks[self.free_len.value].offset = offset
        self.free_blocks[self.free_len.value].blocks = blocks
        self.free_len.value += 1

        self.lock.release()


    def write(self, offset, string_data):
        if offset < 0:
            return None
        start = offset * self.block_size
        end = start + len(string_data)
        self.data[start:end] = string_data

    def read(self, offset):
        if offset < 0:
            return None
        start = offset * self.block_size
        end = start + self.allocated_blocks[offset].size
        return self.data[start:end]
        
    def alloc_and_write(self, string_data):
        offset = self.alloc(len(string_data))
        self.write(offset, string_data)
        return offset

    def read_and_free(self, offset):
        string_data = self.read(offset)
        self.free(offset)
        return string_data
    
        
    


class ReusableDataPool:
    """
    Data segments are newed and retired. Can be used over and over again.

    >>> class TestStruct(ctypes.Structure):
    ...     _fields_ = [('val', ctypes.c_double)]

    >>> pool = ReusableDataPool(mp.RLock(), TestStruct, 10)

    >>> [pool.new() for i in range(10)]
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    >>> pool.get(1).val = 99.0
    >>> pool.get(2).val = 10.3
    >>> pool.get(1).val
    99.0

    >>> pool.retire(7)

    >>> pool.new()
    7
    """

    def __init__(self, lock, struct, size):
        
        self.shared_data = mp.RawArray(struct, size)
        self.syncActive = mp.RawArray(ctypes.c_int, [FREE for i in xrange(size)])

        self.size = size
        self.lock = lock

    def new(self):
        self.lock.acquire()
        new_id = None
        for i in xrange(self.size):
            if self.syncActive[i] == FREE:
                new_id = i
                break

        if new_id == None:
            self.lock.release()
            raise Exception('Internal Error: Pool size exceeded for '+str(self.shared_data))

        self.syncActive[new_id] = OCCUPIED
        self.lock.release()
        return new_id

    def get(self, id):
        return self.shared_data[id]

    def retire(self, id):
        self.lock.acquire()
        self.syncActive[id] = FREE
        self.lock.release()


class SharedLockPool:
    """
    Shared means that calling new, might return used locks.
    The locks are handed out in a round-robin manor.

    >>> pool = SharedLockPool(mp.RLock(), mp.Condition, 5)

    >>> [pool.new() for i in range(10)]
    [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]

    >>> type(pool.get(1)) == type(mp.Condition())
    True

    >>> pool.get(1) != pool.get(2)
    True
    """

    def __init__(self, _lock, lockClass, size):
        self.shared_locks = []

        self.next = mp.RawValue(ctypes.c_int, 0)
        self.size = size
        
        # Instantiate locks
        for i in xrange(size):
            self.shared_locks.append(lockClass())
            
        self.lock = _lock

    def new(self):
        self.lock.acquire()
        id = self.next.value
        if id >= self.size:
            self.lock.release()
            raise Exception('Internal Error: Pool size exceeded for '+str(self.shared_locks[0]))
        self.next.value = (self.next.value + 1)%len(self.shared_locks)
        self.lock.release()
        return id

    def get(self, id):
        return self.shared_locks[id]


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
