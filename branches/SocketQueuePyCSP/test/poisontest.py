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
import check
import time
import random


Configuration().set(SOCKETS_STRICT_MODE, True)

@choice
def action(assertCheck, id, channel_input=None):
    if assertCheck:
        assertCheck(id)

@process
def reader(cin, id,  sleeper, assertCheck=None):
    while True:
        if sleeper: sleeper()
        got = cin()
        if assertCheck:
            assertCheck(id)
    
@process
def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))
    poison(cout)

@process
def par_reader(cin1,cin2,cin3,cin4, sleeper, assertCheck=None):
    while True:
        if sleeper: sleeper()
        AltSelect(
            InputGuard(cin1, action(assertCheck, 0)),
            InputGuard(cin2, action(assertCheck, 1)),
            InputGuard(cin3, action(assertCheck, 2)),
            InputGuard(cin4, action(assertCheck, 3))
            )

@process
def par_writer(cout1,cout2,cout3,cout4, cnt, sleeper):
    for i in range(cnt*4):
        if sleeper: sleeper()
        AltSelect(
            OutputGuard(cout1, i),
            OutputGuard(cout2, i),
            OutputGuard(cout3, i),
            OutputGuard(cout4, i)
            )

    poison(cout1, cout2, cout3, cout4)

@io
def sleep_one():
    time.sleep(0.01)

@io
def sleep_random():
    time.sleep(random.random()/100)

def One2One_Test(read_sleeper, write_sleeper):
    x = Channel()

    c1=Channel()
    Parallel(check.Assert(x.reader(), "One2One_Test"+str(read_sleeper)+str(write_sleeper), count=10, vocabulary=[0]),
             reader(c1.reader(), 0 , read_sleeper, x.writer()), writer(c1.writer(),1,10, write_sleeper))
    
def Any2One_Alting_Test(read_sleeper, write_sleeper):
    x = Channel()

    c1=Channel()
    c2=Channel()
    c3=Channel()
    c4=Channel()

    cnt = 10

    Parallel(check.Assert(x.reader(), "Any2One_Alting_Test"+str(read_sleeper)+str(write_sleeper), count=40, minimum=10, vocabulary=[0,1,2,3], quit_on_count=True),
             par_reader(c1.reader(), c2.reader(), c3.reader(), c4.reader(), read_sleeper, x.writer()),
             writer(c1.writer(),0,cnt, write_sleeper),
             writer(c2.writer(),1,cnt, write_sleeper),
             writer(c3.writer(),2,cnt, write_sleeper),
             writer(c4.writer(),3,cnt, write_sleeper))

def Any2Any_Test(read_sleeper, write_sleeper):
    x = Channel()

    c1=Channel()    
    cnt = 10

    Parallel(check.Assert(x.reader(), "Any2Any_Test"+str(read_sleeper)+str(write_sleeper), count=40, minimum=10, vocabulary=[0,1,2,3]),
             reader(c1.reader(),0, read_sleeper, x.writer()), writer(c1.writer(),0,cnt, write_sleeper),
             reader(c1.reader(),1, read_sleeper, x.writer()), writer(c1.writer(),1,cnt, write_sleeper),
             reader(c1.reader(),2, read_sleeper, x.writer()), writer(c1.writer(),2,cnt, write_sleeper),
             reader(c1.reader(),3, read_sleeper, x.writer()), writer(c1.writer(),3,cnt, write_sleeper))
    
def Any_Alting2Any_Alting_Test(read_sleeper, write_sleeper):
    x = Channel()

    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    Parallel(check.Assert(x.reader(), "Any_Alting2Any_Alting_Test"+str(read_sleeper)+str(write_sleeper), count=80, minimum=40, vocabulary=[0,1,2,3]),
             par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_reader(+c1, +c2, +c3, +c4, read_sleeper, x.writer()),
             par_reader(+c1, +c2, +c3, +c4, read_sleeper, x.writer()))
    
def poisontest():
    for read_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
        for write_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
            rname, rsleep = read_sleep
            wname, wsleep = write_sleep

            if not rsleep==wsleep==sleep_one:
                One2One_Test(rsleep, wsleep)
                Any2One_Alting_Test(rsleep, wsleep)
                Any2Any_Test(rsleep, wsleep)
                Any_Alting2Any_Alting_Test(None,None)

if __name__ == '__main__':
    poisontest()