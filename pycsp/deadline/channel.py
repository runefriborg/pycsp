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

class Channel(greenletsChannel):
    def __init__(self, name=None):
        greenletsChannel.__init__(self,name)
        self.readerprocesses = []
        self.writerprocesses = []
        self.s = RT_Scheduler()
      
    def _read(self):
        self.check_termination()
        augment_inherience = False
        if self.s.current.has_priority and self.s.current.deadline>Now() and self.writerprocesses:
            logging.warning("no writers are ready - will try to inherience %d writer"%len(self.writerprocesses))
            augment_inherience = True
            for writer in self.writerprocesses:
                SetInherience(writer)

        msg  = greenletsChannel._read(self)

        if augment_inherience:
            logging.warning("will try to reset inherience")
            for writer in self.writerprocesses:
                ResetInherience(writer)
        if self.s.current.deadline and self.s.current.deadline<Now():
            raise DeadlineException(self.s.current)
        return msg

    def _write(self,msg):
        #if writer has a priority an no readers are ready to read we augments the readers priority to speed up writer
        self.check_termination()
        augment_inherience = False
        if self.s.current.has_priority and self.s.current.deadline>Now() and self.readerprocesses:
            logging.warning("no readers are ready - will try to inherience %d readers"%len(self.readerprocesses))
            augment_inherience = True
            for reader in self.readerprocesses:
                SetInherience(reader)
        returnvalue =  greenletsChannel._write(self,msg)
        if augment_inherience:
            logging.warning("will try to reset inherience")
            for reader in self.readerprocesses:
                ResetInherience(reader)
        
        if self.s.current.deadline and self.s.current.deadline<Now():
            logging.debug("Throwing Deadline exception")
            raise DeadlineException(self.s.current)
        return returnvalue

    def _addReaderProcess(self, process):
        logging.warning("_addReaderProcess. self: %s\nprocess:%s",self,process)
        self.readerprocesses.append(process)

    def _addWriterProcess(self, process):
        logging.warning("_addWriterProcess. self: %s\nprocess:%s",self,process)
        self.writerprocesses.append(process)

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
