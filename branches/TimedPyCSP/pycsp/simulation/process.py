"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp.greenlets.process import Process 
from simulation import Simulation



# Classes
class Process(Process):
    """ Process(fn, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances
    See process.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
 			Process.__init__(self,fn,args,kwargs)       
			self.s = Simulation()

    
