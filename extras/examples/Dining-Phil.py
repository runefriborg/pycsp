"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *

# Based on the exercise q7.occ from the source distribution of kroc-1.4
# 
# This is an example, showing how to do the equivalent in python using PyCSP
#

@process
def philosopher(id, left, right, down, up):
    try:
        eat = 0
        while True:
            # think
            # Skip

            # get permission to sit down
            down(True)

            # pick up the forks (left and right)
            FairSelect(
                    OutputGuard(left, msg=True, action="right(True)"),
                    OutputGuard(right, msg=True, action="left(True)")
                    )
                    
            # eat
            eat += 1

            # put down the forks (left and right)
            FairSelect(
                    OutputGuard(left, msg=True, action="right(True)"),
                    OutputGuard(right, msg=True, action="left(True)")
                    )

            # notify security you have finished
            up(True)

    except ChannelRetireException:
        print 'philosopher '+str(id)+' has eaten '+str(eat)+' times'
        retire(left, right)

@process
def fork(left, right):
    while True:
        FairSelect(
            # philosopher left picks up fork
            # philosopher left puts down fork
            InputGuard(left, "left()"),
            
            # philosopher right picks up fork
            # philosopher right puts down fork                
            InputGuard(right, "right()")
            )

@process
def security(steps, down, up):
    max = 4
    n_sat_down = [0] # use call by reference
    for step in xrange(steps):
        guards = []

        if n_sat_down[0] < max: # don't allow max at a time
                        
            for i in range(5):
                # philosopher wanting to sit down
                guards.append(InputGuard(down[i], action="n_sat_down[0] += 1"))

        for i in range(5):
            # philosopher wanting to stand up
            # always allow this
            guards.append(InputGuard(up[i], action="n_sat_down[0] -= 1"))

        FairSelect(*guards)

    retire(*down)
    retire(*up)
    
@process
def secure_college(steps):
    left  = Channel() * 5
    right = Channel() * 5
    up    = Channel() * 5
    down  = Channel() * 5

    Parallel(
        security(steps, [d.reader() for d in down] , [u.reader() for u in up]),
        [philosopher(i, left[i].writer(), right[i].writer(), down[i].writer(), up[i].writer()) for i in range(5)],
        [fork(left[i].reader(), right[(i+1) % 5].reader()) for i in range(5)]
        )
    

Sequence(secure_college(1000))

shutdown()
