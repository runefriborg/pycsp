"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp.greenlets.process import process as greenletsprocess, Process as GreenletsProcess,Parallel as greenletsParallel, Spawn as greenletsSpawn
from simulation import Simulation

# Decorators
def process(func):
    def _call(*args, **kwargs):
      return Process(func, *args, **kwargs)
    return _call

# Classes
class Process(GreenletsProcess):
    def __init__(self, fn, *args, **kwargs):
      GreenletsProcess.__init__(self,fn,*args,**kwargs)
      self.s = Simulation()

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

    s = Simulation()
    s.addBulk(processes)

    if block:
        s.join(processes)

# Run tests
process.__doc = greenletsprocess.__doc__
Parallel.__doc__ = greenletsParallel.__doc__
Spawn.__doc = greenletsSpawn.__doc__

if __name__ == '__main__':
  import doctest
  doctest.testmod()
