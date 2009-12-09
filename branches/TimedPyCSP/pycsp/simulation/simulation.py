# Imports
from greenlet import greenlet
import threading
import time
from pycsp.greenlets.scheduling import Scheduler as Scheduler
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
class Io(threading.Thread):
    """ Io(fn, *args, **kwargs)
    It is recommended to use the @io decorator, to create Io instances.
    See io.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.retval = None

        self.s = Simulation()
        self.p = self.s.current

    def run(self):
        self.retval = self.fn(*self.args, **self.kwargs)
        self.s.io_unblock(self.p)




class Simulation(Scheduler):
	def __init__(self, *args,**kwargs):
		Scheduler.__init__(self)
		#self.allTallies = []
		self._endtime = 0
		self._t = 0
		self._stop = False

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

