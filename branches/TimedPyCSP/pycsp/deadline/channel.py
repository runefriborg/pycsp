"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from pycsp.greenlets.channel import Channel as greenletsChannel, ChannelReq as greenletsChannelReq

from process import  SetInheritance,ResetInheritance
from scheduling import RT_Scheduler,DeadlineException,Now
from pycsp.greenlets.const import *
import process

class ChannelReq(greenletsChannelReq):
    def __init__(self, process, msg=None):
        greenletsChannelReq.__init__(self, process, msg=None)
    def __str__(self):
            return "ChannelReq: msg: %s,\tresult: %s,\t%s"%(self.msg,self.result,"")
        


class Channel(greenletsChannel):
    def __init__(self, name=None):
        greenletsChannel.__init__(self,name)
        #List of possible processes we can raise priority on to speed up communication
        self.readerprocesses = []
        self.writerprocesses = []    
        self.s = RT_Scheduler()
    def __str__(self):
        return "%s, %d af %d read klar, %d af %d writer klar, poison = %s"%(self.name, len(self.readqueue), self.readers ,len(self.writequeue), self.writers, self.ispoisoned)
        
    def Readpriority(self):       
        minr = process.Process("dummy")
        if self.readqueue:
            minr = min(self.readqueue,key=lambda obj: obj.process.internal_priority).process
        #logging.warning("\nminReadQueue: %s"%minr)
        return minr.internal_priority
        
    def Writepriority(self):       
        minw = process.Process("dummy")
        if self.writequeue:
            minw = min(self.writequeue,key=lambda obj: obj.process.internal_priority).process
        #logging.warning("\nminwriteQueue: %s"%minw)
        return minw.internal_priority

    #Extend greenelt reader, but auguments channel priority, and will push augumentet priority to other processes
    def _read(self):
        logging.warning("starting _read: %s"%self)
        self.check_termination()
        augment_Inheritance = False
        #logging.warning("%s"%self.s.current)
        #logging.warning("%s and %s and %s and (%s or %s)"%
        #               (self.s.current.has_priority,bool(self.readerprocesses), not self.readqueue, not self.s.current.deadline,self.s.current.deadline>Now()))
        if PRIORITY_INHERITANCE and self.s.current.has_priority and self.writerprocesses and not self.writequeue and (not self.s.current.deadline or self.s.current.deadline>Now()) :
                logging.warning("no writers are ready - will try to Inheritance %d writer"%len(self.writerprocesses))
                #to increase performace dont increase to a lower priority as it has no effect 
                #if self.priority() > self.s.current.internal_priority:
                augment_Inheritance = True
                for writer in self.writerprocesses:
                    SetInheritance(writer)
                    logging.warning("writer agumentet to: \n%s"%writer)
                  
        
        returnvalue =  greenletsChannel._read(self)
       
        if augment_Inheritance :
            logging.warning("trying to reset Inheritance for %d writers"%len(self.writerprocesses))
            for writer in self.writerprocesses:
                ResetInheritance(writer)

        if self.s.current.deadline and self.s.current.deadline<Now():
            raise DeadlineException(self.s.current)
        logging.warning("ending _read: %s"%self)
        return  returnvalue

    def _write(self,msg):
        #if writer has a priority an no readers are ready to read we augments the readers priority to speed up writer
        logging.warning("_write: %s"%self)
        self.check_termination()
        augment_Inheritance = False
        #logging.warning("%s will inheritance %s =  %s and %s and %s and (%s or %s)"%
        #               (self.name, self.s.current.has_priority and self.readerprocesses and not self.readqueue and (not self.s.current.deadline or self.s.current.deadline>Now()),
        #               self.s.current.has_priority,bool(self.readerprocesses), not self.readqueue, not self.s.current.deadline,self.s.current.deadline>Now()))
        if PRIORITY_INHERITANCE and self.s.current.has_priority and self.readerprocesses and not self.readqueue and (not self.s.current.deadline or self.s.current.deadline>Now()):            
                logging.warning("no readers are ready - will try to Inheritance %d readers"%len(self.readerprocesses))
                #if self.priority() > self.s.current.internal_priority:
                augment_Inheritance = True
                for reader in self.readerprocesses:
                    SetInheritance(reader)

        returnvalue =  greenletsChannel._write(self,msg)

        if augment_Inheritance:
            logging.warning("will try to reset Inheritance")
            #print "\n\n\nResetting priority "
            #print self.priority
            #self.priority.pop()
            #print self.priority
            for reader in self.readerprocesses:
                ResetInheritance(reader)
            logging.warning("done resetting Inheritance")
        if self.s.current.deadline and self.s.current.deadline<Now():
            logging.warning("Throwing Deadline exception")
            raise DeadlineException(self.s.current)
        return returnvalue

    def _addReaderProcess(self, process):
        #logging.warning("_addReaderProcess. self: %s\nprocess:%s",self,process)
        self.readerprocesses.append(process)

    def _addWriterProcess(self, process):
        #logging.warning("_addWriterProcess. self: %s\nprocess:%s",self,process)
        self.writerprocesses.append(process)
        
    def match(self):        
        print "in match, \n\treadq:%s \n\t writeq:%s"%(self.readqueue, self.writequeue)
        if self.readqueue and self.writequeue:
            self.readqueue.sort(key=lambda channelReq:channelReq.process.internal_priority)
            self.writequeue.sort(key=lambda channelReq:channelReq.process.internal_priority)
            for w in self.writequeue:
                for r in self.readqueue:
                    if w.offer(r):
                        print "made succesful offer"
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
