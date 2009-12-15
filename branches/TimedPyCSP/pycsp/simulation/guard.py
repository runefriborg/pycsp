"""
Adds Skip and Timeout guards

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from simulation import Simulation
import pycsp.greenlets.guard 

class Timeout(pycsp.greenlets.Timeout):
  """
  Timeout spawns a timer thread, when posted. If removed
  before timeout, then the timer thread is cancelled.
  
  >>> from __init__ import *
  >>> import time

  >>> @process 
  ... def P():
  ...     C = Channel()
  ...     Cin = IN(C)
  ...     time_start = Now()
  ...     (g, msg) = Alternation([{Timeout(seconds=0.5):None}, {Cin:None}]).select()
  ...     time_passed = Now() - time_start
  ...     print time_passed >= 0.5
  ...     print time_passed < 0.6
  ...     print isinstance(g, Timeout) and msg == None
  
  >>> Parallel(P())
  True
  True
  True
  """   

  def __init__(self, seconds):
    pycsp.greenlets.Timeout.__init__(self, seconds)
    self.s = Simulation()
        
        
# Run tests
def testsuite():
  return
testsuite.__doc__ = pycsp.greenlets.Skip.__doc__
if __name__ == '__main__':
    import doctest
    doctest.testmod()
