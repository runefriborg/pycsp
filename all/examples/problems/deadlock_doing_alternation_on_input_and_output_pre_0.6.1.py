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
# Diamond setup, with 4 channels and 4 processes.

# In versions of pycsp from 0.5.0 to 0.6.0 the locking mechanism will produce a deadlock,
# when multiple processes are doing an alternation on an input and output guard.
#
# The locks is acquired in write-read order and produces a deadlock eventually.
#
# PyCSP 0.6.1 fixes this issue by introducing ordering of locks by memory address, before actual locking.

from common import *

@process
def P(id, c1, c2):
    while True:
        Alternation([{(c1,True):None, c2:None}]).select()

if __name__=='__main__':
    c1 = Channel('c1')
    c2 = Channel('c2')
    c3 = Channel('c3')
    c4 = Channel('c4')

    Parallel(P(1,OUT(c1), IN(c2)),
             P(2,OUT(c2), IN(c3)),
             P(3,OUT(c3), IN(c4)),
             P(4,OUT(c4), IN(c1)))
