"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import pycsp.greenlets.alternation
from scheduling import RT_Scheduler

class Alternation(pycsp.greenlets.Alternation):
  def __init__(self,guards):
    pycsp.greenlets.Alternation.__init__(self,guards)
    self.s = RT_Scheduler()

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
    
