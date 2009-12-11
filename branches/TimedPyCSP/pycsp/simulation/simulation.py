# Imports
from greenlet import greenlet
import threading
import time
from pycsp.greenlets.scheduling import Scheduler as greenletsScheduler, Io as greenletsIo

# Decorators
def io(func):
    """
    @io decorator for blocking io operations.
    Execution is moved to seperate threads and the current greenlet is yielded.

    >>> from __init__ import *

    >>> @io
    ... def sleep(n):
    ...     import time
    ...     time.sleep(n)

    >>> @process
    ... def P1():
    ...     sleep(0.05)

    Sleeping for 10 times 0.05 seconds, which equals roughly half a second
    in the sequential case.
    >>> time_start = time.time()
    >>> Sequence([P1() for i in range(10)])
    >>> diff = time.time() - time_start
    >>> diff >= 0.5 and diff < 0.6
    True

    In parallel, it should be close to 0.05 seconds.
    >>> time_start = time.time()
    >>> Parallel([P1() for i in range(10)])
    >>> diff = time.time() - time_start
    >>> diff >= 0.05 and diff < 0.1
    True
    """
    def _call_io(*args, **kwargs):
        io_thread = Io(func, *args, **kwargs)

        if io_thread.p == None:
            # We are not executed from a greenlet
            # Run io code and quit
            return func(*args, **kwargs)
        
        io_thread.s.io_block_prepare(io_thread.p)
        io_thread.start()
        io_thread.s.io_block_wait(io_thread.p)

        # Return value from function, set by Io class.
        return io_thread.retval
    return _call_io

# Classes
class Io(greenletsIo):
    """ Io(fn, *args, **kwargs)
    It is recommended to use the @io decorator, to create Io instances.
    See io.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
      greenletsIo.__init__(self,fn,*args,**kwargs)
      self.s = Simulation()

class Simulation(greenletsScheduler):
  __instance = None  # the unique instance

  def getInstance(cls, *args, **kargs):
    '''Static method to have a reference to **THE UNIQUE** instance'''
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

  def __init__(self):
    pass

  def __new__(cls, *args, **kargs):
    return cls.getInstance(cls, *args, **kargs)

  def now(self):
    return self._t 

  # Main loop
  # When all queues are empty all greenlets have been executed.
  # Queues are new, next, timers and "blocking io counter"
  # Greenlets that are either executing, blocking on a channel or blocking on io is not in any lists.
  def main(self):
      while True:
          if self.timers and self.timers[0][0] < time.time():
              _,self.current = self.timers.pop(0)
              self.current.greenlet.switch()
          elif self.new:
              if len(self.new) > 1000:
                  # Pop from end, if the new list might be large.
                  self.current = self.new.pop(-1)
              else:
                  # Pop from beginning to be more fair
                  self.current = self.new.pop(0)
              self.current.greenlet.switch()
          elif self.next:
              # Pop from the beginning
              self.current = self.next.pop(0)
              self.current.greenlet.switch()

          # We enter a critical region, since timer threads or blocking io threads,
          # might try to update the internal queues.
          self.cond.acquire()
          if not (self.next or self.new):
              # Waiting on blocking processes or all processes have finished!
              if self.timers:
                  # Set timer to lowest activation time
                  seconds = self.timers[0][0] - time.time()
                  if seconds > 0:
                      t = threading.Timer(seconds, self.timer_notify)

                      # We don't worry about cancelling, since it makes no difference if timer_notify
                      # is called one more time.
                      t.start()

                      # Now go to sleep
                      self.cond.wait()

              elif self.blocking > 0:

                  # Now go to sleep
                  self.cond.wait()
              else:
                  # Execution finished!
                  self.cond.release()
                  return
          self.cond.release()

