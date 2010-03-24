"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from pycsp.greenlets.channel import Channel as greenletsChannel, ChannelReq as greenletsChannelReq

from process import  SetInherience,ResetInherience
from scheduling import RT_Scheduler,DeadlineException,Now
from pycsp.greenlets.const import *

class ChannelReq(greenletsChannelReq):
    def __init__(self, process, msg=None):
        greenletsChannelReq.__init__(self, process, msg=None)


class Channel(greenletsChannel):
    def __init__(self, name=None):
        greenletsChannel.__init__(self,name)
        #List of possible processes we can raise priority on to speed up communication
        self.readerprocesses = []
        self.writerprocesses = []
        self.priority = []
        self.priority.append(float("inf"))
        self.s = RT_Scheduler()
    
    #Extend greenelt reader, but auguments channel priority, and will push augumentet priority to other processes
    def _read(self):
        logging.debug("_read: %s"%self)
        self.check_termination()
        logging.debug("done check_termination")
        augment_inherience = channel_inheritance = False
        logging.warning(self.s.current.has_priority,self.writerprocesses, not self.s.current.deadline,self.s.current.deadline>Now())
        if self.s.current.has_priority and self.writerprocesses and (not self.s.current.deadline or self.s.current.deadline>Now()) :
            logging.warning("no writers are ready - will try to inherience %d writer"%len(self.writerprocesses))
            channel_inheritance = True
            #to increase performace dont increase to a lower priority as it has no effect 
            if self.priority[-1]>self.s.current.internal_priority:
                augment_inherience = True
                for writer in self.writerprocesses:
                    SetInherience(writer)
            self.priority.append(min(self.priority[-1],self.s.current.internal_priority))

        returnvalue =  greenletsChannel._read(self)
       
        if channel_inheritance:
            logging.debug("will try to reset inherience")
            self.priority.pop()
            if augment_inherience :
                for writer in self.writerprocesses:
                    ResetInherience(writer)

        if self.s.current.deadline and self.s.current.deadline<Now():
            raise DeadlineException(self.s.current)
        return  returnvalue

    def _write(self,msg):
        #if writer has a priority an no readers are ready to read we augments the readers priority to speed up writer
        logging.debug("_write: %s"%self)
        self.check_termination()
        augment_inherience = False
        logging.warning("%s and %s and (%s or %s)"%(self.s.current.has_priority,bool(self.readerprocesses), not self.s.current.deadline,self.s.current.deadline>Now()))
        if self.s.current.has_priority and self.readerprocesses and (not self.s.current.deadline or self.s.current.deadline>Now()):            
            logging.warning("no readers are ready - will try to inherience %d readers"%len(self.readerprocesses))
            augment_inherience = True
            if self.priority[-1]>self.s.current.internal_priority:
                for reader in self.readerprocesses:
                    SetInherience(reader)
            self.priority.append(min(self.priority[-1],self.s.current.internal_priority))

        returnvalue =  greenletsChannel._write(self,msg)

        if augment_inherience:
            logging.debug("will try to reset inherience")
            #print "\n\n\nResetting priority "
            #print self.priority
            self.priority.pop()
            #print self.priority
            for reader in self.readerprocesses:
                ResetInherience(reader)
        
        if self.s.current.deadline and self.s.current.deadline<Now():
            logging.debug("Throwing Deadline exception")
            raise DeadlineException(self.s.current)
        return returnvalue

    def _addReaderProcess(self, process):
        logging.debug("_addReaderProcess. self: %s\nprocess:%s",self,process)
        self.readerprocesses.append(process)

    def _addWriterProcess(self, process):
        logging.debug("_addWriterProcess. self: %s\nprocess:%s",self,process)
        self.writerprocesses.append(process)
        
    def match(self):
        def reqcmp(x,y):
            #if y == float("inf"):return -1
            #if x == float("inf"):return 1
            return cmp(x.process.internal_priority,y.process.internal_priority)
        print "in match read: %d, write: %d"%(len(self.readqueue),len(self.writequeue))
        if self.readqueue and self.writequeue:
            self.readqueue.sort(reqcmp)
            self.writequeue.sort(reqcmp)
            for w in self.writequeue:
                for r in self.readqueue:
                    #logging.debug("in loop")
                    if w.offer(r):
                        #logging.debug("Did an offer")
                        # Did an offer
                        # We can guarantee, that there will always be someone to call offer,
                        # since everything is run in a single thread. Thus we break the loop.
                        return


        


# Run tests
Channel.__doc__ = greenletsChannel.__doc__
def testsuite():
  return
from pycsp.greenlets.channelend import *
testsuite.__doc__ = IN.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += OUT.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += retire.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += poison.__doc__

if __name__ == '__main__':
    import doctest
    doctest.testmod()
