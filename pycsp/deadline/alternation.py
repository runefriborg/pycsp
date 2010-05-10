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
from channel import ChannelReq
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
        t_guards = []
        tmp_idx = 0        
        idx = None
        act = None
        c = None
        op  = None
        def a(x,y): 
            if x == True : return y.process.state == ACTIVE
            else : return x.process.state and y.process.state

        if True and PRIORITY_INHERITANCE:
            for prio_item in self.guards:
                if len(prio_item) == 3:
                    c, msg, action = prio_item
                    if isinstance(c,pycsp.greenlets.channelend.ChannelEndWrite) and c.channel.Readpriority()<float("inf") and c.channel.readqueue>0 and bool(reduce(a,c.channel.readqueue,True)):
                        heapq.heappush(t_guards,(c.channel.Readpriority(),(prio_item,tmp_idx)))
                else:
                    c, action = prio_item                  
                    if isinstance(c,pycsp.greenlets.channelend.ChannelEndRead) and c.channel.Writepriority()<float("inf") and c.channel.writequeue > 0 and bool(reduce(a,c.channel.writequeue,True)):
                        logging.debug("%s = %s and %s and %s and %s"%(isinstance(c,pycsp.greenlets.channelend.ChannelEndRead) and c.channel.Writepriority()<float("inf") and c.channel.writequeue > 0 and bool(reduce(a,c.channel.writequeue,True)),isinstance(c,pycsp.greenlets.channelend.ChannelEndRead),c.channel.Writepriority()<float("inf"),c.channel.writequeue > 0,bool(reduce(a,c.channel.writequeue,True))))
                        heapq.heappush(t_guards,(c.channel.Writepriority(),(prio_item,tmp_idx)))
                tmp_idx+=1
        if True and PRIORITY_INHERITANCE and t_guards :
            logging.warning("found guards already ready: %s"%t_guards)
            _,(prio_item,idx) = heapq.heappop(t_guards)
            if len(prio_item) == 3:
                c, msg, action = prio_item
                logging.warning("\n\nWRITER:\n\tc: %s,\n\tmsg: %s \n\t action:%s"%(c,msg,action))
                act = ChannelReq(self.s.current)
                c(msg)
                op = WRITE
            else:
                #print "in d choose"
                c, action = prio_item
                logging.warning("\n\nREADER:\n\tc: %s\n\t action:%s"%(c,action))
                act = ChannelReq(self.s.current)
                act.msg = c()
                op = READ
                
        else :
            #print "in g choose"
            (idx, act, c, op) = pycsp.greenlets.Alternation.choose(self)


        if self.s.current.deadline and self.s.current.deadline<Now():
            logging.critical("alternation calling deadlineexception")
            raise DeadlineException(self.s.current)
        #logging.warning("\n%s,%s,%s,%s"%(idx, act, c, op))
        logging.warning("\n\tidx:%s,\n\tc: %s,\n\top: %s"%(idx,c,op))
        logging.warning("\n\tact:%s",act)

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
    
