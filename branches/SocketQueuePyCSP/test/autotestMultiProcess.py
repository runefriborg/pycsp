"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
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

@multiprocess
def reader(cin, id,  sleeper, assertCheck=None):
    while True:
        if sleeper: sleeper()
        got = cin()
        if assertCheck:
            assertCheck(id)
    
@multiprocess
def writer(cout, id, cnt, sleeper):
    try:
        for i in range(cnt):
            if sleeper: sleeper()
            cout((id, i))
        print('writer1 %d' % id)
        poison(cout)
        print('writer2 %d' % id)
        
    except ChannelRetireException:
        print('retired! %d' % id)
        raise



@multiprocess
def par_reader(cin1,cin2,cin3,cin4, cnt, sleeper, assertCheck=None):
    while True:
        if sleeper: sleeper()

        print AltSelect(
            InputGuard(cin1, action(assertCheck, 0)),
            InputGuard(cin2, action(assertCheck, 1)),
            InputGuard(cin3, action(assertCheck, 2)),
            InputGuard(cin4, action(assertCheck, 3))
            )

def sleep_one():
    time.sleep(0.01)

def sleep_random():
    time.sleep(random.random()/100)


def One2One_Test(read_sleeper, write_sleeper):
    x = Channel()

    c1=Channel()
    Parallel(check.Assert(x.reader(), "One2One_Test"+str(read_sleeper)+str(write_sleeper), count=10, vocabulary=[0]),
             reader(c1.reader(), 0 , read_sleeper, x.writer()), writer(c1.writer(),1,10, write_sleeper))

    close(x, c1)
    
def Any2One_Alting_Test(read_sleeper, write_sleeper):

    print "before"
    x = Channel("x")

    c1=Channel("c1")
    c2=Channel("c2")
    c3=Channel("c3")
    c4=Channel("c4")

    cnt = 5

    #Parallel(check.Assert(x.reader(), "Any2One_Alting_Test"+str(read_sleeper)+str(write_sleeper), count=40, minimum=10, vocabulary=[0,1,2,3], quit_on_count=True),
    #         par_reader(c1.reader(), c2.reader(), c3.reader(), c4.reader(),cnt, read_sleeper, x.writer()),
    #         writer(c1.writer(),0,cnt, write_sleeper),
    #         writer(c2.writer(),1,cnt, write_sleeper),
    #         writer(c3.writer(),2,cnt, write_sleeper),
    #         writer(c4.writer(),3,cnt, write_sleeper))

    Parallel(par_reader(c1.reader(), c2.reader(), c3.reader(), c4.reader(),cnt, read_sleeper),
             writer(c1.writer(),0,cnt, write_sleeper),
             writer(c2.writer(),1,cnt, write_sleeper),
             writer(c3.writer(),2,cnt, write_sleeper),
             writer(c4.writer(),3,cnt, write_sleeper))

    close(x, c1, c2, c3, c4)
    
    print "after"

def Any2Any_Test(read_sleeper, write_sleeper):
    x = Channel()

    c1=Channel()    
    cnt = 10

    Parallel(check.Assert(x.reader(), "Any2Any_Test"+str(read_sleeper)+str(write_sleeper), count=40, vocabulary=[0,1,2,3]),
             reader(c1.reader(),0, read_sleeper, x.writer()), writer(c1.writer(),0,cnt, write_sleeper),
             reader(c1.reader(),1, read_sleeper, x.writer()), writer(c1.writer(),1,cnt, write_sleeper),
             reader(c1.reader(),2, read_sleeper, x.writer()), writer(c1.writer(),2,cnt, write_sleeper),
             reader(c1.reader(),3, read_sleeper, x.writer()), writer(c1.writer(),3,cnt, write_sleeper))
    close(x, c1)
    

def autotest():
    for read_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
        for write_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
            rname, rsleep = read_sleep
            wname, wsleep = write_sleep

            if not rsleep==wsleep==sleep_one:
                #One2One_Test(rsleep, wsleep)
                Any2One_Alting_Test(rsleep, wsleep)
                #Any2Any_Test(rsleep, wsleep)

if __name__ == '__main__':
    autotest()
    shutdown()
