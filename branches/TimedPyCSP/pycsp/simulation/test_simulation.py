import unittest
from __init__ import *

class SimulationTestCase(unittest.TestCase):
    def setUp(self):
        Simulation().decompose()

    def tearDown(self):
        return

    def test_decompose(self):
        @process
        def P():
            self.assertEqual(0,Now())
            Wait(5)
            Simulation().decompose()
            self.assertEqual(0,Now())
        Parallel(P())

    def test_timers1(self):
        @process
        def P(wait_time):
            start_time = Now()
            Wait(wait_time)
            self.assertEqual(start_time+wait_time, Now())
        Parallel(P(5),P(4),P(2),P(0),P(5),P(5),P(0),P(0),P(5))  

    def test_timers2(self):
        @process
        def P(wait_time):
            start_time = Now()
            Wait(wait_time)
            self.assertEqual(start_time+wait_time, Now())  
        Parallel(P(0),P(0))

    def test_timers_time_in_past(self):
        @process
        def P(wait_time):
            start_time = Now()
            Wait(wait_time)
            self.assertEqual(start_time+wait_time, Now())
        self.assertRaises(AssertionError, Parallel,P(-1),P(2))

    def test_timers3(self):
        @process
        def P(wait_time):
            start_time = Now()
            Wait(wait_time)
            self.assertEqual(start_time+wait_time, Now())
        Parallel(P(9999999999999999999999999999999999999997))

    def test_buffered_channels(self):
        @process
        def Buffer(cREADER,cWRITER):
            try:
                from collections import deque
                buffer = deque() 
                max_len = 0
                Wait(1)
                while True:
                    buffer.append(cREADER())
                    while len(buffer)>0:
                          t = buffer[0]
                          Alternation([
                            {cREADER:"buffer.append(channel_input)"},
                            {(cWRITER,t):"buffer.popleft()"}
                          ]).execute()
                          if max_len<len(buffer):
                                max_len = len(buffer)
            except ChannelPoisonException:
                poison(cREADER,cWRITER)
                return

        @process
        def Printer(cREADER,number): 
            #calls simulations Wait to sleep for one timeunit
            try:
                Wait(2)
                for n in range(number):
                  self.assertEqual(n,cREADER())
                poison(cREADER)
            except ChannelPoisonException:
                poison(cREADER)
                return

        @process 
        def Generator(cWRITER,number):
            import random
            for n in range(number):
                cWRITER(n)
            poison(cWRITER)

        buffer_channel1 = Channel()
        buffer_channel2 = Channel()
        number = 1000
        Parallel(Generator(-buffer_channel1,number),
                 Printer(+buffer_channel2,number),
                 Buffer(+buffer_channel1,-buffer_channel2))


    def test_io(self):
        @io
        def sleep(n):
          import time
          time.sleep(n)

        @process
        def pr():
            self.assertEqual(Now(),0)
            for i in range(10):
                sleep(0.1)
                self.assertEqual(Now(), i)
                Wait(1)
                self.assertEqual(Now(), i+1)

        @process
        def pr2():
            return

        Parallel(pr(),pr2())


    def test_alternation(self):
        @process
        def P1(cout, n=5):
            for i in range(n):
                cout(i)

        @process
        def P2(cin1, cin2, n=10):
            L = []
       
            @choice
            #Using the normal __channel_input results in a Type error
            def append(*args,**kwargs):
              L.append(kwargs["channel_input"])
         
            alt = Alternation([{cin1:append(), cin2:append()}])
            for i in range(n):
                alt.execute()
       
            self.assertEqual(len(L),10)
            L.sort()
            self.assertEqual(L,[0, 0, 1, 1, 2, 2, 3, 3, 4, 4])

        C1, C2 = Channel(), Channel()
        Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))

    def test_buffer(self):
        import time
        import random
        @io
        def sleep_random():
            time.sleep(random.random()/10)

        @io
        def sleep_one():
            time.sleep(0.01)
        
        @process
        def reader(cin, id, cnt, sleeper):
            try:
                while True:
                    if sleeper: sleeper()
                    got= cin()
                    print '.',
            except ChannelRetireException:
                return

        @process
        def writer(cout, id, cnt, sleeper):
            for i in range(cnt):
                if sleeper: sleeper()
                cout((id, i))
            retire(cout)


        read_monitor = Monitor()
        ch2=Channel(buffer=5, mon=read_monitor)
        cnt = 10
        Parallel(reader(IN(ch2),0,cnt, sleep_random), 
                 writer(OUT(ch2),0,cnt, sleep_one))
