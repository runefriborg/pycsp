import sys
sys.path.append("..")

if len(sys.argv) > 1:
    mod = sys.argv[1]
else:
    mod = ''

if (mod == 'threads'):
    from pycsp.threads import *
elif (mod == 'processes'):
    from pycsp.processes import *
elif (mod == 'greenlets'):
    from pycsp.greenlets import *
elif (mod == 'net'):
    from pycsp.net import *    
else:
    print "python",sys.argv[0],"[ threads | processes | greenlets | net ]"
    from pycsp import *

print 'Using version', version

if sys.platform == 'win32' and (version[3] == 'processes'):
    print 'These tests are not compatible with PyCSP.processes and win32.'
    sys.exit(0)

