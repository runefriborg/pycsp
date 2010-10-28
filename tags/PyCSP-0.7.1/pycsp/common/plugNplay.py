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
import pycsp.current

@pycsp.current.process
def Identity(cin, cout):
    """Copies its input stream to its output stream, adding a one-place buffer
    to the stream."""
    while True:
        t = cin()
        cout(t)

@pycsp.current.process
def Prefix(cin, cout, prefix=None):
    t = prefix
    while True:
        cout(t)
        t = cin()

@pycsp.current.process
def Successor(cin, cout):
    """Adds 1 to the value read on the input channel and outputs it on the output channel.
    Infinite loop.
    """
    while True:
        cout(cin()+1)

@pycsp.current.process
def Delta2(cin, cout1, cout2):
    while True:
        msg = cin()
        pycsp.current.Alternation([{
            (cout1,msg):'cout2(msg)',
            (cout2,msg):'cout1(msg)'
            }]).execute()

@pycsp.current.process
def Plus(cin1, cin2, cout):
    while True:
        cout(cin1() + cin2())

@pycsp.current.process
def Tail(cin, cout):
    dispose = cin()
    while True:
        cout(cin())

@pycsp.current.process
def Pairs(cin, cout):
    pA, pB, pC = pycsp.current.Channel('pA'), pycsp.current.Channel('pB'), pycsp.current.Channel('pC')
    pycsp.current.Parallel(
        Delta2(cin, -pA, -pB),
        Plus(+pA, +pC, cout),
        Tail(+pB, -pC)
    )

@pycsp.current.process
def SkipProcess():
    pass

@pycsp.current.process
def Mux2(cin1, cin2, cout):
    alt = pycsp.current.Alternation([{cin1:None, cin2:None}])
    while True:
        guard, msg = alt.select()
        cout(msg)
