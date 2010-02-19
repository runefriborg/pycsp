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
from pycsp_import import *

@process
def producer(cout, cnt):
    for i in range(2,cnt):
        cout(i)
    poison(cout)
    
@process
def worker(cin, cout):
    try:
        ccout=None
        my_prime=cin()
        cout(my_prime)
        child_channel=Channel()
        ccout=child_channel.writer()
        Spawn(worker(child_channel.reader(), cout))
        while True:
            new_prime=cin()
            if new_prime%my_prime:
                ccout(new_prime)
    except ChannelPoisonException:
        if ccout:
            poison(ccout)
        else:
            poison(cout)

@process
def printer(cin):
    while True:
        print cin()


first=Channel()
outc=Channel()

Parallel(producer(first.writer(),2000),
         worker(first.reader(), outc.writer()),
         printer(outc.reader()))
