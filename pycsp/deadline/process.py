"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

import pycsp.greenlets.process
import pycsp.greenlets.channelend
from scheduling import RT_Scheduler, Now, DeadlineException
from pycsp.greenlets.const import *

# Decorators
def process(func):
    def _call(*args, **kwargs):
      return Process(func, *args, **kwargs)
    return _call

# Classes
class Process(pycsp.greenlets.Process):
    def __init__(self, fn, *args, **kwargs):
        pycsp.greenlets.Process.__init__(self,fn,*args,**kwargs)
        self.s = RT_Scheduler()
        #self.optional_priotity = float("inf")
        self.inherit_priotity = []     
        self.deadline = None
        self.internal_priority = float("inf")
        self.has_priority = False
        for arg in args:
            if isinstance(arg, pycsp.greenlets.channelend.ChannelEndRead):
                arg.channel._addReaderProcess(self)
            if isinstance(arg, pycsp.greenlets.channelend.ChannelEndWrite):
                arg.channel._addWriterProcess(self)

    def run(self):
        try:
            logging.debug("RT run")
            pycsp.greenlets.Process.run(self)
        except DeadlineException, e:
            logging.debug("process got deadline, but ignore it")
            pass
    
    def __repr__(self):
        return "%s\n\tstate:\t\t\t%s\tdeadline:\t%s\n\texecuted:\t\t%s\tint. deadline:\t%s\n\thas_priority:\t\t%s,"%(
        self.fn, state[self.state],self.deadline, self.executed,self.internal_priority, self.has_priority)
        #, self.args
        #return "%s"%self.fn

    # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]
    def __mul__(self, multiplier):
        return [self] + [Process(self.fn, *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

    # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]
    def __rmul__(self, multiplier):
        return [self] + [Process(self.fn, *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

def Parallel(*plist):
    _parallel(plist, True)

def Spawn(*plist):
    _parallel(plist, False)

def _parallel(plist, block = True):
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    for p in processes:
        p.start()

    s = RT_Scheduler()
    logging.debug("deadline - adding processes")
    s.addBulk(processes)

    if block:
        s.join(processes)

def Sequence(*plist):
    """ Sequence(P1, [P2, .. ,PN])
    """
    logging.debug("deadline, running i sequence")
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    # Wrap processes to be able to schedule greenlets.
    def WrapP():
        for p in processes:
            # Call Run directly instead of start() and join() 
            logging.debug("Running proces: %s",p)
            p.run()
    Parallel(Process(WrapP))



def current_process_id():
    s = RT_Scheduler()
    g = s.current
    return g.id


def _set_absolute_priority(value,process):    
    process.internal_priority = value
    process.inherit_priotity.append(value)
    process.has_priority = True

def Set_deadline(value,process=None):
    if  process == None:
        process = RT_Scheduler().current
    process.deadline = value+Now()
    _set_absolute_priority(process.deadline,process)

def SetInherience(process):
    current_process = RT_Scheduler().current
    new_value = min(process.internal_priority,current_process.internal_priority)
    logging.debug("process %s\n raises priority for %s"%(current_process, process))
    _set_absolute_priority(new_value,process)
    logging.debug("reschedules process")
    RT_Scheduler().reschedule(process)
    
def ResetInherience(process):
    if process.state != 1:
        logging.debug("Resetting inherience for %s"%process)
        assert(len(process.inherit_priotity)>0)
        process.inherit_priotity.pop(-1)
        if len(process.inherit_priotity):
            new_value = process.inherit_priotity[-1]    
            logging.debug("reset priorty from %f to %f"%(process.internal_priority,new_value))
            logging.debug("Setting absolute deadline")
            _set_absolute_priority(new_value,process)
        else:
            Remove_deadline(process)
        logging.debug("reschedules process")
        RT_Scheduler().reschedule(process)
    
    
def Remove_deadline(process=None):
    if  process == None:
        process = RT_Scheduler().current
    if process.state != 1:
        process.deadline = None
        process.internal_priority = float("inf")
        process.inherit_priotity = []     
        process.has_priority = False
        logging.debug("Removing deadline for\n%s"%process)
    
        
def Get_deadline():
    return RT_Scheduler().current.deadline

# Run tests
process.__doc = pycsp.greenlets.process.__doc__
Parallel.__doc__ = pycsp.greenlets.Parallel.__doc__
Spawn.__doc__ = pycsp.greenlets.Spawn.__doc__
def test_suite():
  return
test_suite.__doc__ = pycsp.greenlets.Sequence.__doc__

if __name__ == '__main__':
  import doctest
  doctest.testmod()
