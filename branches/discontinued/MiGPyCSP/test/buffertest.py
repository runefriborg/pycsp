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
def reader(cin, id, cnt, sleeper):
    while True:
        if sleeper: sleeper()
        got= cin()
        print '.',
    
@process
def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))
    retire(cout)

@process
def par_reader(cin1,cin2,cin3,cin4, cnt, sleeper):
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
        
    retire(cout1, cout2, cout3, cout4)

@io
def sleep_random():
    time.sleep(random.random()/100)

@io
def sleep_one():
    time.sleep(0.01)

def One2One_Test(read_sleeper, write_sleeper):
    c1=Channel(buffer=1)
    c2=Channel(buffer=5)
    c3=Channel(buffer=10)
    c4=Channel(buffer=20)

    cnt = 10
    
    Parallel(reader(+c1,0,cnt, read_sleeper), writer(-c1,0,cnt, write_sleeper),
             reader(+c2,1,cnt, read_sleeper), writer(-c2,1,cnt, write_sleeper),
             reader(+c3,2,cnt, read_sleeper), writer(-c3,2,cnt, write_sleeper),
             reader(+c4,3,cnt, read_sleeper), writer(-c4,3,cnt, write_sleeper))

def Any2One_Test(read_sleeper, write_sleeper):
    c1=Channel(buffer=20)

    cnt = 10
    
    Parallel(reader(c1.reader(),0,cnt*4, read_sleeper),
             writer(c1.writer(),0,cnt, write_sleeper),
             writer(c1.writer(),1,cnt, write_sleeper),
             writer(c1.writer(),2,cnt, write_sleeper),
             writer(c1.writer(),3,cnt, write_sleeper))

def One2Any_Test(read_sleeper, write_sleeper):
    c1=Channel(buffer=20)

    cnt = 10
    
    Parallel(writer(c1.writer(),0,cnt*4, write_sleeper),
             reader(c1.reader(),0,cnt, read_sleeper),
             reader(c1.reader(),1,cnt, read_sleeper),
             reader(c1.reader(),2,cnt, read_sleeper),
             reader(c1.reader(),3,cnt, read_sleeper))


def One_Alting2Any_Test(read_sleeper, write_sleeper):
    c1=Channel(buffer=1)
    c2=Channel(buffer=5)
    c3=Channel(buffer=10)
    c4=Channel(buffer=20)

    cnt = 10
    
    Parallel(par_writer(c1.writer(),c2.writer(),c3.writer(),c4.writer(),cnt, write_sleeper),
             reader(c1.reader(),0,cnt, read_sleeper),
             reader(c2.reader(),1,cnt, read_sleeper),
             reader(c3.reader(),2,cnt, read_sleeper),
             reader(c4.reader(),3,cnt, read_sleeper))

def Any2Any_Test(read_sleeper, write_sleeper):
    c1=Channel(buffer=20)
    cnt = 10

    Parallel(reader(+c1,0,cnt, read_sleeper), writer(-c1,0,cnt, write_sleeper),
             reader(+c1,1,cnt, read_sleeper), writer(-c1,1,cnt, write_sleeper),
             reader(+c1,2,cnt, read_sleeper), writer(-c1,2,cnt, write_sleeper),
             reader(+c1,3,cnt, read_sleeper), writer(-c1,3,cnt, write_sleeper))

def Any_Alting2Any_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel(buffer=1)
    c2=Channel(buffer=5)
    c3=Channel(buffer=10)
    c4=Channel(buffer=20)

    cnt = 10
    
    Parallel(par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_writer(-c1, -c2, -c3, -c4,cnt, write_sleeper),
             par_reader(+c1, +c2, +c3, +c4,cnt, read_sleeper),
             par_reader(+c1, +c2, +c3, +c4,cnt, read_sleeper),
             par_reader(+c1, +c2, +c3, +c4,cnt, read_sleeper),
             par_reader(+c1, +c2, +c3, +c4,cnt, read_sleeper))



def commtest():
    for read_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
        for write_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
            rname, rsleep = read_sleep
            wname, wsleep = write_sleep
            if not rsleep==wsleep==sleep_one: #No reason to test with both sleep_one
                print '***',rname,wname,'***'
                print 'One2One_Test()'
                One2One_Test(rsleep, wsleep)
                print 'Any2One_Test()'
                Any2One_Test(rsleep, wsleep)
                print 'One2AnyTest()'
                One2Any_Test(rsleep, wsleep)
                print 'One_Alting2Any_Test()'
                One_Alting2Any_Test(rsleep, wsleep)
                print 'Any2Any_Test()'
                Any2Any_Test(rsleep,wsleep)
                print 'Any_Alting2Any_Alting_Test()'
                Any_Alting2Any_Alting_Test(rsleep, wsleep)

if __name__ == '__main__':
    commtest()
