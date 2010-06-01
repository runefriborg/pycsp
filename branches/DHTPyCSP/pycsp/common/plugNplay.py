"""
PlugNPlay module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
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

import os
if os.environ.has_key('PYCSP'):
    if os.environ['PYCSP'] == 'PROCESSES':
        import pycsp.processes as pycsp
    elif os.environ['PYCSP'] == 'GREENLETS':
        import pycsp.greenlets as pycsp
    elif os.environ['PYCSP'] == 'NET':
        import pycsp.net as pycsp
    elif os.environ['PYCSP'] == 'THREADS':
        import pycsp.threads as pycsp
else:
    import pycsp.threads as pycsp

@pycsp.process
def Identity(cin, cout):
    """Copies its input stream to its output stream, adding a one-place buffer
    to the stream."""
    while True:
        t = cin()
        cout(t)

@pycsp.process
def Prefix(cin, cout, prefix=None):
    t = prefix
    while True:
        cout(t)
        t = cin()

@pycsp.process
def Successor(cin, cout):
    """Adds 1 to the value read on the input channel and outputs it on the output channel.
    Infinite loop.
    """
    while True:
        cout(cin()+1)

@pycsp.process
def Delta2(cin, cout1, cout2):
    while True:
        msg = cin()
        pycsp.Alternation([{
            (cout1,msg):'cout2(msg)',
            (cout2,msg):'cout1(msg)'
            }]).execute()

@pycsp.process
def Plus(cin1, cin2, cout):
    while True:
        cout(cin1() + cin2())

@pycsp.process
def Tail(cin, cout):
    dispose = cin()
    while True:
        cout(cin())

@pycsp.process
def Pairs(cin, cout):
    pA, pB, pC = pycsp.Channel('pA'), pycsp.Channel('pB'), pycsp.Channel('pC')
    pycsp.Parallel(
        Delta2(cin, -pA, -pB),
        Plus(+pA, +pC, cout),
        Tail(+pB, -pC)
    )

@pycsp.process
def SkipProcess():
    pass

@pycsp.process
def Mux2(cin1, cin2, cout):
    alt = pycsp.Alternation([{cin1:None, cin2:None}])
    while True:
        guard, msg = alt.select()
        cout(msg)
