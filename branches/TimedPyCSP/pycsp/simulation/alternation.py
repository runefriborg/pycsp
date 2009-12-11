"""
Alternation module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from pycsp.greenlets import Alternation as greenletsAlternation
from simulation import Simulation

class Alternation(greenletsAlternation):

  def __init__(self,guards):
    greenletsAlternation.__init__(self,guards)
    self.s = Simulation()
