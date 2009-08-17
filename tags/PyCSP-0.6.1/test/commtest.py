from common import *
import time
import random

@choice
def action(ChannelInput=None):
    print '.',
    
@process
def reader(cin, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        got= cin()
        print '.',
    
@process
def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))
    
@process
def par_reader(cin1,cin2,cin3,cin4, cnt, sleeper):
    for i in range(cnt*4):
        if sleeper: sleeper()
        Alternation([{cin1:action(), cin2:action(), cin3:action(), cin4:action()}]).execute()

@process
def par_writer(cout1,cout2,cout3,cout4, cnt, sleeper):
    for i in range(cnt*4):
        if sleeper: sleeper()
        Alternation([{(cout1, i):None, (cout2,i):None, (cout3,i):None, (cout4,i):None}]).execute()

@io
def sleep_random():
    time.sleep(random.random()/100)

@io
def sleep_one():
    time.sleep(0.01)

def One2One_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(reader(IN(c1),0,cnt, read_sleeper), writer(OUT(c1),0,cnt, write_sleeper),
             reader(IN(c2),1,cnt, read_sleeper), writer(OUT(c2),1,cnt, write_sleeper),
             reader(IN(c3),2,cnt, read_sleeper), writer(OUT(c3),2,cnt, write_sleeper),
             reader(IN(c4),3,cnt, read_sleeper), writer(OUT(c4),3,cnt, write_sleeper))

def Any2One_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')

    cnt = 10
    
    Parallel(reader(IN(c1),0,cnt*4, read_sleeper),
             writer(OUT(c1),0,cnt, write_sleeper),
             writer(OUT(c1),1,cnt, write_sleeper),
             writer(OUT(c1),2,cnt, write_sleeper),
             writer(OUT(c1),3,cnt, write_sleeper))

def One2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')

    cnt = 10
    
    Parallel(writer(OUT(c1),0,cnt*4, write_sleeper),
             reader(IN(c1),0,cnt, read_sleeper),
             reader(IN(c1),1,cnt, read_sleeper),
             reader(IN(c1),2,cnt, read_sleeper),
             reader(IN(c1),3,cnt, read_sleeper))

def Any2One_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_reader(IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             writer(OUT(c1),0,cnt, write_sleeper),
             writer(OUT(c2),1,cnt, write_sleeper),
             writer(OUT(c3),2,cnt, write_sleeper),
             writer(OUT(c4),3,cnt, write_sleeper))


def One_Alting2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_writer(OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             reader(IN(c1),0,cnt, read_sleeper),
             reader(IN(c2),1,cnt, read_sleeper),
             reader(IN(c3),2,cnt, read_sleeper),
             reader(IN(c4),3,cnt, read_sleeper))

def Any2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    cnt = 10

    Parallel(reader(IN(c1),0,cnt, read_sleeper), writer(OUT(c1),0,cnt, write_sleeper),
             reader(IN(c1),1,cnt, read_sleeper), writer(OUT(c1),1,cnt, write_sleeper),
             reader(IN(c1),2,cnt, read_sleeper), writer(OUT(c1),2,cnt, write_sleeper),
             reader(IN(c1),3,cnt, read_sleeper), writer(OUT(c1),3,cnt, write_sleeper))

def Any_Alting2Any_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_writer(OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             par_writer(OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             par_writer(OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             par_writer(OUT(c1),OUT(c2),OUT(c3),OUT(c4),cnt, write_sleeper),
             par_reader(IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             par_reader(IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             par_reader(IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             par_reader(IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper))



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
