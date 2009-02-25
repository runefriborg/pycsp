from common import *
from pycsp import *

@choice
def action(ChannelInput=None):
    print '.',
    
@process
def reader(c, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        got=c.read()
        print '.',
    
@process
def writer(c, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        c.write((id, i))
    
@process
def par_reader(c1,c2,c3,c4, cnt, sleeper):
    for i in range(cnt*4):
        if sleeper: sleeper()
        Alternation({c1:action(), c2:action(), c3:action(), c4:action()}).execute()

@process
def par_writer(c1,c2,c3,c4, cnt, sleeper):
    for i in range(cnt*4):
        if sleeper: sleeper()
        Alternation({(c1, i):None, (c2,i):None, (c3,i):None, (c4,i):None}).execute()

def sleep_random():
    time.sleep(random.random())

def sleep_one():
    time.sleep(0.5)

def One2One_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(reader(c1,0,cnt, read_sleeper), writer(c1,0,cnt, write_sleeper),
             reader(c2,1,cnt, read_sleeper), writer(c2,1,cnt, write_sleeper),
             reader(c3,2,cnt, read_sleeper), writer(c3,2,cnt, write_sleeper),
             reader(c4,3,cnt, read_sleeper), writer(c4,3,cnt, write_sleeper))

def Any2One_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')

    cnt = 10
    
    Parallel(reader(c1,0,cnt*4, read_sleeper),
             writer(c1,0,cnt, write_sleeper),
             writer(c1,1,cnt, write_sleeper),
             writer(c1,2,cnt, write_sleeper),
             writer(c1,3,cnt, write_sleeper))

def One2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')

    cnt = 10
    
    Parallel(writer(c1,0,cnt*4, write_sleeper),
             reader(c1,0,cnt, read_sleeper),
             reader(c1,1,cnt, read_sleeper),
             reader(c1,2,cnt, read_sleeper),
             reader(c1,3,cnt, read_sleeper))

def Any2One_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             writer(c1,0,cnt, write_sleeper),
             writer(c2,1,cnt, write_sleeper),
             writer(c3,2,cnt, write_sleeper),
             writer(c4,3,cnt, write_sleeper))

def One_Alting2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             reader(c1,0,cnt, read_sleeper),
             reader(c2,1,cnt, read_sleeper),
             reader(c3,2,cnt, read_sleeper),
             reader(c4,3,cnt, read_sleeper))

def Any2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    cnt = 10

    Parallel(reader(c1,0,cnt, read_sleeper), writer(c1,0,cnt, write_sleeper),
             reader(c1,1,cnt, read_sleeper), writer(c1,1,cnt, write_sleeper),
             reader(c1,2,cnt, read_sleeper), writer(c1,2,cnt, write_sleeper),
             reader(c1,3,cnt, read_sleeper), writer(c1,3,cnt, write_sleeper))

def Any_Alting2Any_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper))


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

commtest()
