"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

import pycsp.greenlets.process
from scheduling import RT_Scheduler,Now
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
        self.optional_priotity = 0
        self.inherit_priotity = 0      
        self.deadline = None
        self.internal_priority = 0
        self.has_priority = False

    def __repr__(self):
        return "%s%s\n\tstate:\t\t\t%s\n\texecuted:\t\t%s\n\toptional_priotity:\t%s\n\thas_priority:\t\t%s"%(
        self.fn, self.args, state[self.state], self.executed,self.optional_priotity,self.has_priority)
    
    
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
    s.addBulk(processes)

    if block:
        s.join(processes)

def current_process_id():
    s = RT_Scheduler()
    g = s.current
    return g.id


def Set_deadline(value):
    now = Now()
    RT_Scheduler().current.deadline = value+now
    RT_Scheduler().current.priority = value+now
    RT_Scheduler().current.has_priority = True

def Remove_deadline():
    RT_Scheduler().current.deadline = None
    RT_Scheduler().current.priority = None
    RT_Scheduler().current.has_priority = False
        
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
