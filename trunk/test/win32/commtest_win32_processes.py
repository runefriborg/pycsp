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
from common import *
import time
import random

@choice
def action(channel_input=None):
    print '.',
    
def reader(cin, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        got= cin()
        print '.',
    
def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))

    
def par_reader(cin1,cin2,cin3,cin4, cnt, sleeper):
    for i in range(cnt*4):
        if sleeper: sleeper()
        Alternation([{cin1:action(), cin2:action(), cin3:action(), cin4:action()}]).execute()

def par_writer(cout1,cout2,cout3,cout4, cnt, sleeper):
    for i in range(cnt*4):
        if sleeper: sleeper()
        Alternation([{(cout1, i):None, (cout2,i):None, (cout3,i):None, (cout4,i):None}]).execute()

def sleep_random():
    time.sleep(random.random()/100)

def sleep_one():
    time.sleep(0.01)

def One2One_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(Process(reader,IN(c1),0,cnt, read_sleeper), Process(writer,OUT(c1),0,cnt, write_sleeper),
             Process(reader,IN(c2),1,cnt, read_sleeper), Process(writer,OUT(c2),1,cnt, write_sleeper),
             Process(reader,IN(c3),2,cnt, read_sleeper), Process(writer,OUT(c3),2,cnt, write_sleeper),
             Process(reader,IN(c4),3,cnt, read_sleeper), Process(writer,OUT(c4),3,cnt, write_sleeper))

def Any2One_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')

    cnt = 10
    
    Parallel(Process(reader,IN(c1),0,cnt*4, read_sleeper),
             Process(writer,OUT(c1),0,cnt, write_sleeper),
             Process(writer,OUT(c1),1,cnt, write_sleeper),
             Process(writer,OUT(c1),2,cnt, write_sleeper),
             Process(writer,OUT(c1),3,cnt, write_sleeper))

def One2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')

    cnt = 10
    
    Parallel(Process(writer,OUT(c1),0,cnt*4, write_sleeper),
             Process(reader,IN(c1),0,cnt, read_sleeper),
             Process(reader,IN(c1),1,cnt, read_sleeper),
             Process(reader,IN(c1),2,cnt, read_sleeper),
             Process(reader,IN(c1),3,cnt, read_sleeper))

def Any2One_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(Process(par_reader,IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             Process(writer,OUT(c1),0,cnt, write_sleeper),
             Process(writer,OUT(c2),1,cnt, write_sleeper),
             Process(writer,OUT(c3),2,cnt, write_sleeper),
             Process(writer,OUT(c4),3,cnt, write_sleeper))


def One_Alting2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(Process(par_writer,OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             Process(reader,IN(c1),0,cnt, read_sleeper),
             Process(reader,IN(c2),1,cnt, read_sleeper),
             Process(reader,IN(c3),2,cnt, read_sleeper),
             Process(reader,IN(c4),3,cnt, read_sleeper))

def Any2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    cnt = 10

    Parallel(Process(reader,IN(c1),0,cnt, read_sleeper), Process(writer,OUT(c1),0,cnt, write_sleeper),
             Process(reader,IN(c1),1,cnt, read_sleeper), Process(writer,OUT(c1),1,cnt, write_sleeper),
             Process(reader,IN(c1),2,cnt, read_sleeper), Process(writer,OUT(c1),2,cnt, write_sleeper),
             Process(reader,IN(c1),3,cnt, read_sleeper), Process(writer,OUT(c1),3,cnt, write_sleeper))

def Any_Alting2Any_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(Process(par_writer,OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             Process(par_writer,OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             Process(par_writer,OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             Process(par_writer,OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             Process(par_reader,IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             Process(par_reader,IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             Process(par_reader,IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             Process(par_reader,IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper))



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
                print 'Any2One_Alting_Test()'
                Any2One_Alting_Test(rsleep, wsleep)
                print 'One_Alting2Any_Test()'
                One_Alting2Any_Test(rsleep, wsleep)
                print 'Any2Any_Test()'
                Any2Any_Test(rsleep,wsleep)
                print 'Any_Alting2Any_Alting_Test()'
                Any_Alting2Any_Alting_Test(rsleep, wsleep)

if __name__ == '__main__':
    commtest()
