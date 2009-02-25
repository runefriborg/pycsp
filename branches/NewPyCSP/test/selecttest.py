from common import *
from pycsp import *
import random

def sleep_random():
    time.sleep(random.random())

@process
def writer(c, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        c.write((id, i))
    
@process
def par_reader(c1,c2,c3,c4, cnt, sleeper):
    alt = Alternation({c1:'', c2:'', c3:'', c4:''})
    for i in range(cnt*4):
        if sleeper: sleeper()
        c,msg = alt.select()
        print 'From ',c.name,'got',msg


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

Any2One_Alting_Test(sleep_random, sleep_random)
        
