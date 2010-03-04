"""
Generate wiki documentation for google code project.

"""
import sys
sys.path.append("..")
from pycsp.threads import *

print "#summary Documentation for all components in PyCSP ver. "+str(version[0])+"."+str(version[1])+"."+str(version[2])
print """

= Overview =

<wiki:toc max_depth="3" />

"""

def item(title, doc):
    print title

    if not doc:
        doc = ''

    in_code = False
    for line in doc.splitlines():
        if line.find('__init__') > -1:
            pass
        elif line.strip() == '':
            if in_code:
                in_code = False
                print '}}}'
            print ''
        else:
            if (line.find('>>>') > -1 or line.find('...') > -1):
                if not in_code:
                    in_code = True
                    print '{{{'
                    print line
                else:
                    print line
            else:
                if in_code:
                    in_code = False
                    print line
                    print '}}}'
                else:
                    print line

    if in_code:
        print '}}}'

def l1(title):
    return '== '+title+' =='

def l2(title):
    return '=== '+title+' ==='


item(l1('Creating Processes'), '')
item(l2('@process'), process.__doc__)

item(l1('Starting Processes'), '')
item(l2('Parallel'), Parallel.__doc__)
item(l2('Sequence'), Sequence.__doc__)
item(l2('Spawn'), Spawn.__doc__)

item(l1('Termination and Exceptions'), '')
item(l2('poison'), poison.__doc__)
#item(l2('ChannelPoisonException'), ChannelPoisonException.__doc__)
item(l2('retire'), retire.__doc__)
#item(l2('ChannelRetireException'), ChannelRetireException.__doc__)

item(l1('Channels'), Channel.__doc__)
C = Channel()
item(l2('Joining to Read'), C.reader.__doc__)
item(l2('Joining to Write'), C.writer.__doc__)

item(l1('External Choice / Choosing a Channel'), AltSelect.__doc__)
item(l2('@choice'), choice.__doc__)

item(l1('Guards'), '')
item(l2('InputGuard'), InputGuard.__doc__)
item(l2('OutputGuard'), OutputGuard.__doc__)
item(l2('SkipGuard'), SkipGuard.__doc__)
item(l2('TimeoutGuard'), TimeoutGuard.__doc__)

from pycsp.greenlets import *
item(l1('Specific for pycsp.greenlets: @io'), io.__doc__)

