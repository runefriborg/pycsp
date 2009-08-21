from common import *
import time
import random

@choice
def action(id, __channel_input=None):
    print id,

@process
def reader(cin, id,  sleeper):
    while True:
        if sleeper: sleeper()
        got=cin()
        print id,
    
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
        Alternation([
            {
                cin1:action(0),
                cin2:action(1),
                cin3:action(2),
                cin4:action(3)
            }
        ]).execute()


@io
def sleep_one():
    time.sleep(0.01)

@io
def sleep_random():
    time.sleep(random.random()/100)


def One2One_Test(read_sleeper, write_sleeper):
    c1=Channel()
    Parallel(reader(IN(c1), 0 , read_sleeper), writer(OUT(c1),1,10, write_sleeper))
    print

def Any2One_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel()
    c2=Channel()
    c3=Channel()
    c4=Channel()

    cnt = 10

    Parallel(par_reader(IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             writer(OUT(c1),0,cnt, write_sleeper),
             writer(OUT(c2),1,cnt, write_sleeper),
             writer(OUT(c3),2,cnt, write_sleeper),
             writer(OUT(c4),3,cnt, write_sleeper))
    print

def Any2Any_Test(read_sleeper, write_sleeper):
    c1=Channel()
    cnt = 10

    Parallel(reader(IN(c1),0, read_sleeper), writer(OUT(c1),0,cnt, write_sleeper),
             reader(IN(c1),1, read_sleeper), writer(OUT(c1),1,cnt, write_sleeper),
             reader(IN(c1),2, read_sleeper), writer(OUT(c1),2,cnt, write_sleeper),
             reader(IN(c1),3, read_sleeper), writer(OUT(c1),3,cnt, write_sleeper))
    

def autotest():
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

if __name__ == '__main__':
    autotest()

