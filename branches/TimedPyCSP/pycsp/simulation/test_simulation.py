import unittest
from __init__ import *



class SimulationTestCase(unittest.TestCase):
  def setUp(self):
    Simulation().decompose()

  def tearDown(self):
    return

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
      from collections import deque
      buffer = deque() 
      max_len = 0
      Wait(1)
      while True:
        buffer.append(cREADER())
        while len(buffer)>0:
          t = buffer[0]
          Alternation([
            {cREADER:"buffer.append(__channel_input)"},
            {(cWRITER,t):"buffer.popleft()"}
          ]).execute()
          if max_len<len(buffer):
            max_len = len(buffer)
    @process
    def Printer(cREADER,number):
      #calls simulations Wait to sleep for one timeunit
      Wait(2)
      for n in range(number):
        self.assertEqual(n,cREADER())

    @process 
    def Generator(cWriter,number):
      import random
      for n in range(number):
        cWriter(n)


    buffer_channel1 = Channel()
    buffer_channel2 = Channel()
    number = 1000
    Parallel(Generator(-buffer_channel1,number),
             Printer(+buffer_channel2,number),
             Buffer(+buffer_channel1,-buffer_channel2))

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
          L.append(kwargs["__channel_input"])
     
        alt = Alternation([{cin1:append(), cin2:append()}])
        for i in range(n):
            alt.execute()
   
        assert(len(L) == 10)
        L.sort()
        assert(L == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4])

    C1, C2 = Channel(), Channel()
    Parallel(P1(OUT(C1)), P1(OUT(C2)), P2(IN(C1), IN(C2)))


  def test_buffered_channels2(self):
    @process
    def Printer(cREADER,number):
      #calls simulations Wait to sleep for one timeunit
      Wait(2)
      for n in range(number):
        self.assertEqual(n,cREADER())

    @process 
    def Generator(cWriter,number):
      import random
      for n in range(number):
        cWriter(n)


    buffer_channel1 = Channel()
    buffer_channel2 = Channel()
    number = 1000
    Parallel(Generator(-buffer_channel1,number),
             Printer(+buffer_channel2,number),
             Buffer(+buffer_channel1,-buffer_channel2))




