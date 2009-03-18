from common import *
from pycsp import *

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
            # pick up the forks
            Parallel(
                Process(left, True),
                Process(right, True)
                )
            # eat
            eat += 1
            # put down the forks
            Parallel(
                Process(left, True),
                Process(right, True)
                )
            # notify security you have finished
            up(True)

    except ChannelPoisonException:
        print 'philospher '+str(id)+' has eaten '+str(eat)+' times'

@process
def fork(left, right):
    while True:
        Alternation({

                # philosopher left picks up fork
                # philosopher left puts down fork
                left:"left()",

                # philosopher right picks up fork
                # philosopher right puts down fork                
                right:"right()"

                }).execute()

@process
def security(steps, down, up):
    max = 4
    n_sat_down = 0
    for step in range(steps):
        guards = {}
        for i in range(5):
            # philosopher wanting to sit down
            if n_sat_down < max: # don't allow max at a time
                guards[down[i]] = "n_sat_down += 1"

            # philosopher wanting to stand up
            # always allow this
            guards[up[i]] = "n_sat_down -= 1" 

        Alternation(guards).execute()

    poison(*down)
    poison(*up)
    
@process
def secure_college(steps):
    left, right, up, down = 4*[5*[Channel()]]

    Parallel(
        security(steps, map(IN,down), map(IN,up)),
        [philosopher(i, OUT(left[i]), OUT(right[i]), OUT(down[i]), OUT(up[i])) for i in range(5)],
        [fork(IN(left[i]), IN(right[(i+1) % 5])) for i in range(5)]
        )
    

Sequence(secure_college(1000))
