"""
Adds Skip and Timeout guards

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from simulation import Simulation
from pycsp.greenlets.guard import Timeout as greenletsTimeout

class Timeout(greenletsTimeout):
    def __init__(self, seconds):
        greenletsTimeout.__init__(self, seconds)
        self.s = Simulation()
        
        
# Run tests
Timeout.__doc__ = greenletsTimeout.__doc__
if __name__ == '__main__':
    import doctest
    doctest.testmod()
