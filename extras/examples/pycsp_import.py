"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""
import sys
sys.path.insert(0,"..")

if len(sys.argv) > 1:
    mod = sys.argv[1]
else:
    mod = ''

if (mod == 'parallel'):
    from pycsp.parallel import *
elif (mod == 'greenlets'):
    from pycsp.greenlets import *
else:
    print("python",sys.argv[0],"[ parallel | greenlets ]")
    from pycsp.parallel import *

print('Using version', version)

