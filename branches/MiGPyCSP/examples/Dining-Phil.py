"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Import pycsp.[sys.argv[1]]
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
            AltSelect(
                    OutputGuard(left, msg=True, action="right(True)"),
                    OutputGuard(right, msg=True, action="left(True)")
                    )
                    
            # eat
            eat += 1

            # put down the forks (left and right)
            AltSelect(
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
        AltSelect(
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

        AltSelect(*guards)

    retire(*down)
    retire(*up)
    
@process
def secure_college(steps):
    left, right, up, down = 4*[5*[None]]
    left = map(Channel, left)
    right = map(Channel, right)
    up = map(Channel, up)
    down = map(Channel, down)

    Parallel(
        security(steps, [d.reader() for d in down] , [u.reader() for u in up]),
        [philosopher(i, left[i].writer(), right[i].writer(), down[i].writer(), up[i].writer()) for i in range(5)],
        [fork(left[i].reader(), right[(i+1) % 5].reader()) for i in range(5)]
        )
    

Sequence(secure_college(1000))
