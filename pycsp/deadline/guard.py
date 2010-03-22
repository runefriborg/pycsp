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
        logging.debug("creating timeout process for %s"%self.s.current)
        self.parentprocess = self.s.current



    def post_read(self, reader):
        logging.debug("in post_read")
        self.posted = (READ, reader)

        # Start process
        self.p = Process(self.expire)
        
        self.p.inherit_priotity = self.parentprocess.inherit_priotity
        self.p.deadline = self.parentprocess.deadline
        self.p.internal_priority = self.parentprocess.internal_priority
        self.p.has_priority = self.parentprocess.has_priority
        
        self.p.start()
        self.p.setstate(ACTIVE)
        logging.debug("self.p: %s"%self.p)
        # Put process on the scheduler timer queue
        self.s.timer_wait(self.p, self.seconds)

    def post_write(self, writer):
        logging.debug("in post_write")
        self.posted = (WRITE, writer)

        # Start process
        self.p = Process(self.expire)

        self.p.optional_priotity = self.parentprocess.optional_priotity
        self.p.inherit_priotity = self.parentprocess.inherit_priotity
        self.p.deadline = self.parentprocess.deadline
        self.p.internal_priority = self.parentprocess.internal_priority
        self.p.has_priority = self.parentprocess.has_priority
        
        self.p.start()
        self.p.setstate(ACTIVE)
        logging.debug("self.p: %s"%self.p)
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
