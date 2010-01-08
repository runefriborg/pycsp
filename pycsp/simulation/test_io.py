import unittest
from __init__ import *

class TestCase(unittest.TestCase):
    def setUp(self):
        Simulation().decompose()

    def tearDown(self):
        return

    def test_wait(self):
        @io
        def sleep(n):
            import time
            time.sleep(n)

        def sleep_wrapper():
            sleep(3)
            print "indtast et tegn"
            t = raw_input()
        @process
        def p1():
            self.assertEqual(Now(),0)
            Wait(1)
            self.assertEqual(Now(),1)
            sleep_wrapper()
            self.assertEqual(Now(),1)
            Wait(1)
            self.assertEqual(Now(),2)

        @process
        def p2():
            self.assertEqual(Now(),0)
            Wait(1)
            self.assertEqual(Now(),1)
            Wait(3)
            self.assertEqual(Now(),4)

        Parallel(p1(),p2())

