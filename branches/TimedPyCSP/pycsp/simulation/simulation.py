# Imports
import sys
try: from greenlet import greenlet
except ImportError, e:
    try: from py.magic import greenlet
    except ImportError, e: 
        sys.stderr.write("PyCSP.greenlets requires the greenlet module, recommended version is 0.2 and is\navailable from http://pypi.python.org/pypi/greenlet/.\n\n")
        raise ImportError(e)
import threading
import time
import heapq
from showtree import *
#from pycsp.greenlets.scheduling import Scheduler as greenletsScheduler, Io as greenletsIo, io as greenletsio
import pycsp.greenlets.scheduling
from pycsp.greenlets.const import *

def Now():
  return Simulation()._t 

def Wait(seconds):
    """Wrapper function for timer_wait. Will schedule the process for later activation and then switch active process. """
    logging.debug("calling wait")
    Simulation().timer_wait(Simulation().current, seconds)
    t = Now()+seconds
    while Now()<t:
        p = Simulation().getNext() 
        logging.debug("Wait swicthing from %s to %s"%(Simulation().current, p))
        p.greenlet.switch()

# Decorators
def io(func):
    def _call_io(*args, **kwargs):
        io_thread = Io(func, *args, **kwargs)
        logging.debug("")
        if io_thread.p == None:
            # We are not executed from a greenlet
            # Run io code and quiti
            logging.debug("warning run io and exit")
            return func(*args, **kwargs)
        io_thread.s.io_block_prepare(io_thread.p)
        io_thread.start()
        io_thread.s.io_block_wait(io_thread.p)
        logging.debug("returning from io thread")
        # Return value from function, set by Io class.
        return io_thread.retval
    return _call_io

# Classes
class Io(pycsp.greenlets.Io):
    def __init__(self, fn, *args, **kwargs):
      pycsp.greenlets.Io.__init__(self,fn,*args,**kwargs)
      self.s = Simulation()
      self.p = self.s.current
      logging.debug("init Io, current: %s,self: %s"%(self.s.current,self.s))

class Simulation(pycsp.greenlets.scheduling.Scheduler):
  """
  Scheduler is a singleton class.
  
  It is optimized for fast switching and is not fair.
  
  >>> A = Simulation()
  >>> B = Simulation()
  >>> A == B
  True
  """
   
  __instance = None  # the unique instance

  def __new__(cls, *args, **kargs):
    return cls.getInstance(cls, *args, **kargs)
  
  def __init__(self):
    pycsp.greenlets.scheduling.Scheduler.__init__(self)
    pass

  def decompose(self):
    pycsp.greenlets.scheduling.Scheduler.decompose(self)
    Simulation._Simulation__instance = None

  def getInstance(cls, *args, **kargs):
    '''Static method to have a reference to **THE UNIQUE** instance'''
    #logging.debug("getInstance, %s"%cls.__instance)
    if cls.__instance is None:
      # (Some exception may be thrown...)
      # # Initialize **the unique** instance
      cls.__instance = object.__new__(cls)

      # Initialize members for scheduler
      cls.__instance.new = []
      cls.__instance.next = []
      cls.__instance.current = None
      cls.__instance.greenlet = greenlet.getcurrent()
     
      # Timer specific  value = (activation time, process)
      # On update we do a sort based on the activation time
      cls.__instance.timers = []

      # Io specific
      cls.__instance.cond = threading.Condition()
      cls.__instance.blocking = 0

      cls.__instance.endtime = 0
      cls.__instance._t = 0
      cls.__instance.stop = False

    return cls.__instance
  getInstance = classmethod(getInstance)

  # Called by MainThread
  def timer_wait(self, p, seconds):
    """Using seconds as abitrary span of time. 
       Will cause the process to sleep for the amount of time before resuming operation
    """
    new_time = seconds + Now()
    heapq.heappush(self.timers,(new_time,p))
    logging.debug("timer_wait: timers:%s"%self.timers)
    #print "pushing:"
    #show_tree(self.timers)
  # Main loop
  # When all queues are empty all greenlets have been executed.
  # Queues are new, next, timers and "blocking io counter"
  # Greenlets that are either executing, blocking on a channel or blocking on io is not in any lists.
  def main(self):
      logging.debug("entering main, current:%s"%self.current)
      while True:
          #print "main, timers", self.timers,", self.new:",self.new,", self.next:",self.next
          # By definition of the heap, the first element is always the smallest. 
          if self.timers and self.timers[0][0] <= Now():
            # We should not be able to have processes in timers with a launchtime in the past.
            # Users can forces this to happen be defining a negative waittime. should we guard against it? 
            assert self.timers[0][0] >= Now()
            if self.timers[0][0] == Now():
              time = heapq.heappop(self.timers)
              #print "pop:"
              #show_tree(self.timers)
              self.current = time[1] 
              logging.debug("main:switching to process in timer queue %s"%self.current)
              self.current.greenlet.switch()
          elif self.new:
              if len(self.new) > 1000:
                  # Pop from end, if the new list might be large.
                  self.current = self.new.pop(-1)
              else:
                  # Pop from beginning to be more fair
                  self.current = self.new.pop(0)
              logging.debug("main:switching to new %s, self:%s"%(self.current.fn,self))
              self.current.greenlet.switch()
          elif self.next:
              # Pop from the beginning
              self.current = self.next.pop(0)
              logging.debug("main:switching to next %s"%self.current)
              self.current.greenlet.switch()

          # We enter a critical region, since timer threads or blocking io threads,
          # might try to update the internal queues.
          logging.debug("acquire cond")
          self.cond.acquire()
          logging.debug("main: acquired cond. len of blocking=%d, next=%d,new=%d"%(self.blocking,len(self.next),len(self.new)))
          if not (self.next or self.new):
            # Waiting on blocking processes
            if self.blocking > 0:
              # Now go to sleep
              logging.debug("waiting for blocking processes to call notify")
              self.cond.wait()

            #If there exist only processes in timers we can increment
            elif  not (self.next or self.new or self.blocking>0): 
                if self.timers:
                    # inc timer to lowest activation time
                    self._t = self.timers[0][0]
                    logging.debug("incrementing time to %f"%self._t)
                else:
                    # Execution finished!
                    self.cond.release()
                    logging.debug("exit")
                    return

          self.cond.release()
          logging.debug("releases cond")


io.__doc__ = pycsp.greenlets.io.__doc__
# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
