"""
Adds Skip and Timeout guards

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from scheduling import RT_Scheduler
import pycsp.greenlets.guard 
from process import Process
from pycsp.greenlets.const import *

class Skip(pycsp.greenlets.Skip):
    # Start process
    def process(self):
        p = Process(self.empty)
        p.start()
        p.setstate(ACTIVE)
        return p
 
class Timeout(pycsp.greenlets.Timeout):
    def __init__(self, seconds):
        pycsp.greenlets.Timeout.__init__(self, seconds)
        self.s = RT_Scheduler()

    def post_read(self, reader):
        self.posted = (READ, reader)

        # Start process
        self.p = Process(self.expire)
        self.p.start()
        self.p.setstate(ACTIVE)

        # Put process on the scheduler timer queue
        self.s.timer_wait(self.p, self.seconds)

    def post_write(self, writer):
        self.posted = (WRITE, writer)

        # Start process
        self.p = Process(self.expire)
        self.p.start()
        self.p.setstate(ACTIVE)

        # Put process on the scheduler timer queue
        self.s.timer_wait(self.p, self.seconds)
     
        
# Run tests
def testsuite():
  return
testsuite.__doc__ = pycsp.greenlets.Skip.__doc__
Timeout.__doc__ = pycsp.greenlets.Timeout.__doc__
if __name__ == '__main__':
    import doctest
    doctest.testmod()
