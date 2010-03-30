"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import pycsp.greenlets.alternation
import pycsp.greenlets.channelend
from scheduling import RT_Scheduler, Now,DeadlineException
from pycsp.greenlets.const import *
import heapq

class Alternation(pycsp.greenlets.Alternation):
    def __init__(self,guards):
        pycsp.greenlets.Alternation.__init__(self,guards)
        self.s = RT_Scheduler()
        # Default is to go one up in stackframe. 
        # But we need one more because of inherince
        #self.execute_frame = -1


    def choose(self):        
        guards = tmp_guards = []        
        tmp_idx = 0
        for prio_item in self.guards:
            if len(prio_item) == 3:
                c, msg, action = prio_item
                if isinstance(c,pycsp.greenlets.channelend.ChannelEndWrite) and c.channel.Readpriority()<float("inf") and c.channel.readqueue>0:
                    heapq.heappush(guards,(c.channel.Readpriority(),(prio_item,tmp_idx)))
            else:
                c, action = prio_item                  
                if isinstance(c,pycsp.greenlets.channelend.ChannelEndRead) and c.channel.Writepriority()<float("inf") and c.channel.writequeue > 0:
                    heapq.heappush(guards,(c.channel.Writepriority() ,(prio_item,tmp_idx)))
            tmp_idx+=1
        if guards :
            logging.warning("found guards already ready: %s"%guards)
            tmp_guards = self.guards
            _,(prio_item,tmp_idx) = heapq.heappop(guards)
            logging.warning("\n\n\tprio_item: %s,\n\tidx: %s"%(prio_item,tmp_idx))
            self.guards = [prio_item]
        #try :
        logging.warning("self1: %s"%self.s.current)
        tmp = self.s.current
        try:
            (idx, act, c, op) = pycsp.greenlets.Alternation.choose(self)
        except DeadlineException as e:
            logging.critical("\n\ncaught deadlineexception\n\n")
            self.s.current = tmp
            raise e    
        self.s.current = tmp

        if guards :    
            self.guards = tmp_guards
            idx = tmp_idx
            
        if self.s.current.deadline and self.s.current.deadline<Now():
            logging.critical("alternation calling deadlineexception")
            raise DeadlineException(self.s.current)
        #logging.warning("\n%s,%s,%s,%s"%(idx, act, c, op))
        logging.warning("self2: %s"%self.s.current)
        return (idx, act, c, op)
        
    def select(self):
        logging.debug("deadline select")
        msg = pycsp.greenlets.Alternation.select(self)
        if self.s.current.deadline and self.s.current.deadline<Now():
            raise DeadlineException(self.s.current)
        return msg

# Run tests
def testsuite():
  return
testsuite.__doc__ = pycsp.greenlets.choice.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += pycsp.greenlets.Alternation.execute.__doc__
testsuite.__doc__ += '\n'
testsuite.__doc__ += pycsp.greenlets.Alternation.select.__doc__
Alternation.__doc__ = pycsp.greenlets.Alternation.__doc__


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
