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


