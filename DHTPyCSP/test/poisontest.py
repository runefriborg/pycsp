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
import time
import random

@choice
def action(channel_input=None):
    print '.',

@process
def reader(cin, id,  sleeper):
    while True:
        if sleeper: sleeper()
        got=cin()
        print '.',
    
@process
def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))
    poison(cout)

@process
def par_reader(cin1,cin2,cin3,cin4, sleeper):
    while True:
        if sleeper: sleeper()
        AltSelect(
            InputGuard(cin1, action()),
            InputGuard(cin2, action()),
            InputGuard(cin3, action()),
            InputGuard(cin4, action())
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
    c1=Channel('C1')
    Parallel(reader(+c1,0, read_sleeper), writer(-c1,1,10, write_sleeper))
    print
    
def Any2One_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_reader(c1.reader(),c2.reader(),c3.reader(),c4.reader(), read_sleeper),
             writer(c1.writer(),0,cnt, write_sleeper),
             writer(c2.writer(),1,cnt, write_sleeper),
             writer(c3.writer(),2,cnt, write_sleeper),
             writer(c4.writer(),3,cnt, write_sleeper))
    print

def Any2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    cnt = 10

    Parallel(reader(+c1,0, read_sleeper), writer(-c1,0,cnt, write_sleeper),
             reader(+c1,1, read_sleeper), writer(-c1,1,cnt, write_sleeper),
             reader(+c1,2, read_sleeper), writer(-c1,2,cnt, write_sleeper),
             reader(+c1,3, read_sleeper), writer(-c1,3,cnt, write_sleeper))
    
def Any_Alting2Any_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    Parallel(par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_reader(+c1, +c2, +c3, +c4, read_sleeper),
             par_reader(+c1, +c2, +c3, +c4, read_sleeper))
    print

    
def poisontest():
    for read_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
        for write_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
            rname, rsleep = read_sleep
            wname, wsleep = write_sleep

            if not rsleep==wsleep==sleep_one:
                print '***',rname,wname,'***'
                print 'One2One_Test'
                One2One_Test(rsleep, wsleep)
                print 'Any2One_Alting_Test()'
                Any2One_Alting_Test(rsleep, wsleep)
                print 'Any2Any_Test()'
                Any2Any_Test(rsleep, wsleep)
                print 'Any_Alting2Any_Alting_Test()'
                Any_Alting2Any_Alting_Test(None,None)

if __name__ == '__main__':
    poisontest()
