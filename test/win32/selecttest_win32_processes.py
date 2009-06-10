from common import *
import time
import random

def sleep_random():
    time.sleep(random.random()/10)

def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))
    
def par_reader(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:'', cin2:'', cin3:'', cin4:''}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        c,msg = alt.select()
        print 'From ',c ,'got',msg


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

if __name__ == '__main__':
    Any2One_Alting_Test(sleep_random, sleep_random)
        
