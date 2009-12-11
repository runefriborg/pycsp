"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp.greenlets.process import Process as GreenletsProcess
from simulation import Simulation

# Decorators
def process(func):
    """
    @process decorator for creating process functions

    >>> @process
    ... def P():
    ...     pass

    >>> isinstance(P(), Process)
    True
    """
    def _call(*args, **kwargs):
      return Process(func, *args, **kwargs)
    return _call

# Classes
class Process(GreenletsProcess):
    """ Process(fn, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances
    See process.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
      GreenletsProcess.__init__(self,fn,*args,**kwargs)
      self.s = Simulation()

def Parallel(*plist):
    """ Parallel(P1, [P2, .. ,PN])
    >>> from __init__ import *
    
    >>> @process
    ... def P1(cout, id):
    ...     for i in range(10):
    ...         cout(id)

    >>> @process
    ... def P2(cin):
    ...     for i in range(10):
    ...         cin()
    
    >>> C = [Channel(str(i)) for i in range(10)]
    >>> Cin = map(IN, C)
    >>> Cout = map(OUT, C)
    
    >>> Parallel([P1(Cout[i], i) for i in range(10)],[P2(Cin[i]) for i in range(10)])
    """
    _parallel(plist, True)

def Spawn(*plist):
    """ Spawn(P1, [P2, .. ,PN])
    >>> from __init__ import *
    
    >>> @process
    ... def WrapP():
    ...     @process
    ...     def P1(cout, id):
    ...         for i in range(10):
    ...             cout(id)
    ...     
    ...     C = Channel()
    ...     Spawn([P1(OUT(C), i) for i in range(10)])
    ...     
    ...     L = []
    ...     cin = IN(C)
    ...     for i in range(100):
    ...        L.append(cin())
    ...     
    ...     print len(L)

    >>> Parallel(WrapP())
    100
    """
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
   
