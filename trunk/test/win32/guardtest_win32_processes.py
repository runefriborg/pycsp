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

def sleep_long():
    time.sleep(2)

def sleep_random():
    time.sleep(random.random()/2)

def sleep_long_random():
    time.sleep(random.random()*2)


def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))

def par_reader_skip_sel(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:'', cin2:''},{Skip():''},{cin3:'', cin4:''}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        c,msg = alt.select()
        print 'From ',c ,'got',msg
    retire(cin1, cin2, cin3, cin4)

def par_reader_timeout_sel(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:'', cin2:''},{cin3:'', cin4:''},{Timeout(0.1):''}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        c,msg = alt.select()
        print 'From ',c ,'got',msg
    retire(cin1, cin2, cin3, cin4)

def par_reader_skip_exec(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:"print 'From cin1 got', channel_input",
                        cin2:"print 'From cin2 got', channel_input"},
                       {Skip():"print 'Skip'"},
                       {cin3:"print 'From cin3 got', channel_input",
                        cin4:"print 'From cin4 got', channel_input"}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        alt.execute()
    retire(cin1, cin2, cin3, cin4)

def par_reader_timeout_exec(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:"print 'From cin1 got', channel_input",
                        cin2:"print 'From cin2 got', channel_input"},
                       {cin3:"print 'From cin3 got', channel_input",
                        cin4:"print 'From cin4 got', channel_input"},
                       {Timeout(seconds=0.1):"print 'Timeout(seconds=0.1)'"}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        alt.execute()
    retire(cin1, cin2, cin3, cin4)


def Any2One_Alting_Test(par_reader, read_sleeper, write_sleeper):
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


def Any2Any_Alting_Test(par_reader, read_sleeper, write_sleeper):
    c1=Channel()
    c2=Channel()
    c3=Channel()
    c4=Channel()

    cnt = 40
    
    Parallel(Process(par_reader,IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             Process(writer,OUT(c1),0,cnt, write_sleeper),
             Process(writer,OUT(c1),1,cnt, write_sleeper),
             Process(writer,OUT(c1),2,cnt, write_sleeper),
             Process(writer,OUT(c1),3,cnt, write_sleeper),
             Process(writer,OUT(c2),4,cnt, write_sleeper),
             Process(writer,OUT(c2),5,cnt, write_sleeper),
             Process(writer,OUT(c2),6,cnt, write_sleeper),
             Process(writer,OUT(c2),7,cnt, write_sleeper),
             Process(writer,OUT(c3),8,cnt, write_sleeper),
             Process(writer,OUT(c3),9,cnt, write_sleeper),
             Process(writer,OUT(c3),10,cnt, write_sleeper),
             Process(writer,OUT(c3),11,cnt, write_sleeper),
             Process(writer,OUT(c4),12,cnt, write_sleeper),
             Process(writer,OUT(c4),13,cnt, write_sleeper),
             Process(writer,OUT(c4),14,cnt, write_sleeper),
             Process(writer,OUT(c4),15,cnt, write_sleeper))


if __name__ == '__main__':
    print "Any2One_Alting_Test(par_reader_skip_sel, sleep_random, sleep_random)"
    Any2One_Alting_Test(par_reader_skip_sel, sleep_random, sleep_random)
    print

    print "Any2One_Alting_Test(par_reader_timeout_sel, sleep_random, sleep_long_random)"
    Any2One_Alting_Test(par_reader_timeout_sel, sleep_random, sleep_long_random)
    print

    print "Any2One_Alting_Test(par_reader_skip_exec, sleep_random, sleep_random)"
    Any2One_Alting_Test(par_reader_skip_exec, sleep_random, sleep_random)
    print

    print "Any2One_Alting_Test(par_reader_timeout_exec, sleep_random, sleep_long_random)"
    Any2One_Alting_Test(par_reader_timeout_exec, sleep_random, sleep_long_random)
    print

    print "Any2Any_Alting_Test(par_reader_skip_sel, None, sleep_long)"
    Any2Any_Alting_Test(par_reader_skip_sel, None, sleep_long)
    print

    print "Any2Any_Alting_Test(par_reader_timeout_sel, None, sleep_long)"
    Any2Any_Alting_Test(par_reader_timeout_sel, None, sleep_long)
    print

        
