import unittest
from __init__ import *
from scheduling import *
from random import expovariate

class DeadlineTestCase(unittest.TestCase):
    def setUp(self):
        RT_Scheduler().decompose()

    def tearDown(self):
        RT_Scheduler().decompose()

    def test_readDeadline(self):
        deadline = 0.2
        @process
        def source(chan_out):
            for i in range(1*10):
                waittime = expovariate(1/deadline)
                Wait(waittime)
                chan_out("Hello world (%s)\n" % (waittime))
            retire(chan_out)
            
        @process
        def sink(chan_in):
            try:
                while True:
                    try:
                        print "\n1. waiting for first channel"                        
                        val = chan_in()
                        Set_deadline(deadline)
                        first = Now()
                        print "2. waiting for second"                       
                        val = chan_in()
                        second = Now()
                        print "3. received with a delay of",second-first,"(deadline is",deadline,")\n"
                        Remove_deadline()
                        self.assertTrue(second-first<deadline)
                    except DeadlineException:
                        print "3. Deadline hoppede i havet\n"
                        continue
            except ChannelRetireException:
                pass
        chan = Channel()
        Parallel(
            1 * source(-chan),
            1 * sink(+chan)
        )
        
        
    def test_writeDeadline(self):
        deadline = 0.2
        @process
        def sink(chan_in):
            for i in range(1*10):
                waittime = expovariate(1/deadline)
                Wait(waittime)
                val = chan_in()
                #print "got ",val
            retire(chan_in)
            
        @process
        def source(chan_out):
            try:
                while True:
                    try:
                        print "\n1. waiting for first channel"
                        chan_out("Hello world")
                        deadline = 0.2
                        Set_deadline(deadline)
                        first = Now()
                        print "2. waiting for second channel"
                        chan_out("Hello world")
                        second = Now()
                        print "3. sent with a delay of :",second-first,"(deadline is",deadline,")\n"
                        Remove_deadline()
                        self.assertTrue(second-first<deadline)
                    except DeadlineException:
                        print "3. Deadline hoppede i havet\n"
                        continue
            except ChannelRetireException:
                pass
        chan = Channel()
        Parallel(
            1 * source(-chan),
            1 * sink(+chan)
        )
        
        
    def test_AlternationreadDeadline(self):
        deadline = 0.2
        @process
        def source(chan_out):
            try:
                for i in range(2*10):
                    waittime = expovariate(1/deadline)
                    Wait(waittime)
                    chan_out("Hello world (%s)\n" % (waittime))
                retire(chan_out)
            except ChannelRetireException:
                pass
                
        @process
        def sink(chan_in, chan_in2):
            try:
                while True:
                    try:                     
                        val = chan_in()
                        Set_deadline(deadline)
                        first = Now()
                        print "2. waiting for second"                       
                        Alternation([
                            {chan_in:"print '3. got msg from chan_in'"},
                            {chan_in2:"print '3. got msg from chan_in2'"}
                        ]).execute()
                        second = Now()
                        print "4. received with a delay of",second-first,"(deadline is",deadline,")\n"
                        Remove_deadline()
                        self.assertTrue(second-first<deadline)
                    except DeadlineException:
                        print "3. Deadline hoppede i havet\n"
                        continue
            except ChannelRetireException:
                retire(chan_in, chan_in2)
                pass

        chan = Channel()
        chan2 = Channel()
        Parallel(
            1 * source(-chan),
            1 * source(-chan2),
            1 * sink(+chan,+chan2)
        )
        

