"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp_import import *
import check
import time
import random

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
    retire(cout)

@process
def par_reader(cin1,cin2,cin3,cin4, cnt, sleeper, assertCheck=None):
    while True:
        if sleeper: sleeper()
        
        AltSelect(
            InputGuard(cin1, action(assertCheck, 0)),
            InputGuard(cin2, action(assertCheck, 1)),
            InputGuard(cin3, action(assertCheck, 2)),
            InputGuard(cin4, action(assertCheck, 3))
            )

@process
def par_fair_reader(cin1,cin2,cin3,cin4, cnt, sleeper, assertCheck=None):
    while True:
        if sleeper: sleeper()
        
        FairSelect(
            InputGuard(cin1, action(assertCheck, 0)),
            InputGuard(cin2, action(assertCheck, 1)),
            InputGuard(cin3, action(assertCheck, 2)),
            InputGuard(cin4, action(assertCheck, 3))
            )

@process
def par_pri_reader(cin1,cin2,cin3,cin4, cnt, sleeper, assertCheck=None):
    while True:
        if sleeper: sleeper()
        
        PriSelect(
            InputGuard(cin1, action(assertCheck, 0)),
            InputGuard(cin2, action(assertCheck, 1)),
            InputGuard(cin3, action(assertCheck, 2)),
            InputGuard(cin4, action(assertCheck, 3))
            )

@process
def return_msg(cin, sleeper):
    if sleeper: sleeper()
    return cin()

@io
def sleep_one():
    time.sleep(0.01)

@io
def sleep_random():
    time.sleep(random.random()/100)


def Parallel_Test(sleeper):
    
    c1=Channel()
    
    L= Parallel(writer(c1.writer(), 0, 10, sleeper), 10 * return_msg(c1.reader(), sleeper))
    
    if len(L) == 11 and L[0] == None and not None in L[1:]:
        print("OK - Parallel_Test"+str(sleeper))
    else:
        print("Error - Parallel_Test"+str(sleeper))
        print(str(L))

def Sequence_Test(sleeper):
    
    c1=Channel()
    
    Spawn(writer(c1.writer(), 0, 10, sleeper))
    L= Sequence(10 * return_msg(c1.reader(), sleeper))
    
    if len(L) == 10 and not None in L:
        print("OK - Sequence_Test"+str(sleeper))
    else:
        print("Error - Sequence_Test"+str(sleeper))
        print(str(L))

    
def One2One_Test(read_sleeper, write_sleeper):
    x = Channel()
    Spawn(check.Assert(x.reader(), "One2One_Test"+str(read_sleeper)+str(write_sleeper), count=10, vocabulary=[0]))

    c1=Channel()
    Parallel(reader(c1.reader(), 0 , read_sleeper, x.writer()), writer(c1.writer(),1,10, write_sleeper))

def Any2One_Alting_Test(read_sleeper, write_sleeper):
    x = Channel()
    Spawn(check.Assert(x.reader(), "Any2One_Alting_Test"+str(read_sleeper)+str(write_sleeper), count=40, minimum=10, vocabulary=[0,1,2,3], quit_on_count=True))

    c1=Channel()
    c2=Channel()
    c3=Channel()
    c4=Channel()

    cnt = 10

    Parallel(par_reader(c1.reader(), c2.reader(), c3.reader(), c4.reader(),cnt, read_sleeper, x.writer()),
             writer(c1.writer(),0,cnt, write_sleeper),
             writer(c2.writer(),1,cnt, write_sleeper),
             writer(c3.writer(),2,cnt, write_sleeper),
             writer(c4.writer(),3,cnt, write_sleeper))

def Any2One_FairAlting_Test(read_sleeper, write_sleeper):
    x = Channel()
    Spawn(check.Assert(x.reader(), "Any2One_FairAlting_Test"+str(read_sleeper)+str(write_sleeper), count=40, minimum=10, vocabulary=[0,1,2,3], quit_on_count=True))

    c1=Channel()
    c2=Channel()
    c3=Channel()
    c4=Channel()

    cnt = 10

    Parallel(par_fair_reader(c1.reader(), c2.reader(), c3.reader(), c4.reader(),cnt, read_sleeper, x.writer()),
             writer(c1.writer(),0,cnt, write_sleeper),
             writer(c2.writer(),1,cnt, write_sleeper),
             writer(c3.writer(),2,cnt, write_sleeper),
             writer(c4.writer(),3,cnt, write_sleeper))

def Any2One_PriAlting_Test(read_sleeper, write_sleeper):
    x = Channel()
    Spawn(check.Assert(x.reader(), "Any2One_PriAlting_Test"+str(read_sleeper)+str(write_sleeper), count=40, minimum=10, vocabulary=[0,1,2,3], quit_on_count=True))

    c1=Channel()
    c2=Channel()
    c3=Channel()
    c4=Channel()

    cnt = 10

    Parallel(par_pri_reader(c1.reader(), c2.reader(), c3.reader(), c4.reader(),cnt, read_sleeper, x.writer()),
             writer(c1.writer(),0,cnt, write_sleeper),
             writer(c2.writer(),1,cnt, write_sleeper),
             writer(c3.writer(),2,cnt, write_sleeper),
             writer(c4.writer(),3,cnt, write_sleeper))

def Any2Any_Test(read_sleeper, write_sleeper):
    x = Channel()
    Spawn(check.Assert(x.reader(), "Any2Any_Test"+str(read_sleeper)+str(write_sleeper), count=40, vocabulary=[0,1,2,3]))

    c1=Channel()    
    cnt = 10

    Parallel(reader(c1.reader(),0, read_sleeper, x.writer()), writer(c1.writer(),0,cnt, write_sleeper),
             reader(c1.reader(),1, read_sleeper, x.writer()), writer(c1.writer(),1,cnt, write_sleeper),
             reader(c1.reader(),2, read_sleeper, x.writer()), writer(c1.writer(),2,cnt, write_sleeper),
             reader(c1.reader(),3, read_sleeper, x.writer()), writer(c1.writer(),3,cnt, write_sleeper))
    

def autotest():
    for read_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:

        Sequence_Test(read_sleep[1])
        Parallel_Test(read_sleep[1])

        for write_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
            rname, rsleep = read_sleep
            wname, wsleep = write_sleep

            
            if not rsleep==wsleep==sleep_one:
                One2One_Test(rsleep, wsleep)
                Any2One_Alting_Test(rsleep, wsleep)
                Any2One_FairAlting_Test(rsleep, wsleep)
                Any2One_PriAlting_Test(rsleep, wsleep)
                Any2Any_Test(rsleep, wsleep)

if __name__ == '__main__':
    autotest()
    shutdown()
