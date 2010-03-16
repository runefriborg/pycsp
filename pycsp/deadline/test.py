import unittest
from __init__ import *
from scheduling import *
from random import expovariate

class DeadlineTestCase(unittest.TestCase):
    def setUp(self):
        RT_Scheduler().decompose()

    def tearDown(self):
        Remove_deadline()
        RT_Scheduler().decompose()

#    def test_readDeadline(self):
#        deadline = 0.1
#        @process
#        def source(chan_out):
#            for i in range(1*10):
#                waittime = expovariate(1/deadline)
#                Wait(waittime)
#                chan_out(True)
#            retire(chan_out)
#            
#        @process
#        def sink(chan_in):
#            try:
#                while True:
#                    try:
#                        val = chan_in()
#                        Set_deadline(deadline)
#                        first = Now()
#                        val = chan_in()
#                        second = Now()
#                        print "\tReceived two messages with a delay of",second-first,"(deadline is",deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        continue
#            except ChannelRetireException:
#                pass
#        chan = Channel()
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )
#        
#        
#    def test_writeDeadline(self):
#        deadline = 0.1
#        @process
#        def sink(chan_in):
#            for i in range(1*10):
#                waittime = expovariate(1/deadline)
#                Wait(waittime)
#                val = chan_in()
#            retire(chan_in)
#            
#        @process
#        def source(chan_out):
#            try:
#                while True:
#                    try:
#                        chan_out("Hello world")
#                        Set_deadline(deadline)
#                        first = Now()
#                        chan_out("Hello world")
#                        second = Now()
#                        print "\tSent two messages with a delay of :",second-first,"(deadline is",deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        continue
#            except ChannelRetireException:
#                pass
#        chan = Channel()
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )
#        
#        
#        
#    def test_AlternationExecuteWriteDeadline(self):
#        deadline = 0.13
#        @process
#        def sink(chan_in):
#            try:
#                for i in range(2*10):
#                    waittime = expovariate(1/deadline)
#                    Wait(waittime)
#                    chan_in()
#                retire(chan_in)
#            except ChannelRetireException:
#                pass
#                
#        @process
#        def source(chan_out, chan_out2):
#            try:
#                while True:
#                    try:                                         
#                        Alternation([
#                            {(chan_out,True):"chan_out2(True)"},
#                            {(chan_out2,True):"chan_out(True)"}
#                        ]).execute()
#                        Set_deadline(deadline)
#                        first = Now()
#                        Alternation([
#                            {(chan_out,True):"chan_out2(True)"},
#                            {(chan_out2,True):"chan_out(True)"}
#                        ]).execute()
#                        second = Now()
#                        print "\tSent two messages with a delay of",second-first,"(deadline is",deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        Remove_deadline()
#                        continue
#            except ChannelRetireException:
#                retire(chan_out, chan_out2)
#                pass

#        chan = Channel()
#        chan2 = Channel()
#        print ""
#        Parallel(
#            1 * sink(+chan),
#            1 * sink(+chan2),
#            1 * source(-chan,-chan2)
#        )



#    def test_AlternationExecuteReadDeadline(self):
#        deadline = 0.13
#        @process
#        def source(chan_out):
#            try:
#                for i in range(2*10):
#                    waittime = expovariate(1/deadline-0.07)
#                    Wait(waittime)
#                    chan_out(True)
#                retire(chan_out)
#            except ChannelRetireException:
#                pass
#                
#        @process
#        def sink(chan_in, chan_in2):
#            try:
#                while True:
#                    try:                                         
#                        Alternation([
#                            {(chan_in):"chan_in2()"},
#                            {(chan_in2):"chan_in()"}
#                        ]).execute()
#                        Set_deadline(deadline)
#                        first = Now()
#                        Alternation([
#                            {(chan_in):"chan_in2()"},
#                            {(chan_in2):"chan_in()"}
#                        ]).execute()
#                        second = Now()
#                        print "\tReceived two messages with a delay of",second-first,"(deadline is",deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        Remove_deadline()
#                        continue
#            except ChannelRetireException:
#                retire(chan_in, chan_in2)
#                pass

#        chan = Channel()
#        chan2 = Channel()
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * source(-chan2),
#            1 * sink(+chan,+chan2)
#        )


    def test_AlternationExecuteTimeoutDeadline(self):
        deadline = 0.13
        @process
        def source(chan_out):
            try:
                for i in range(2*1):
                    waittime = 3*deadline #expovariate(1/deadline-0.07)
                    chan_out(True)
                    Wait(waittime)                    
                retire(chan_out)
            except ChannelRetireException:
                pass
                
        @process
        def sink(chan_in):
            try:
                while True:
                    try:                               
                        chan_in()          
                        Set_deadline(deadline)
                        first = Now()
                        g,_ = Alternation([
                            {chan_in:""},
                            {Timeout(seconds=2*deadline):None}
                        ]).select()
                        second = Now()
                        print g
                        print "\tReceived two messages with a delay of",second-first,"(deadline is",deadline,")"
                        Remove_deadline()
                        self.assertTrue(second-first<deadline)
                    except DeadlineException as e:
                        self.assertTrue(Now()-first>=deadline)
                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
                        Remove_deadline()
                        continue
            except ChannelRetireException:
                retire(chan_in)
                pass

        chan = Channel()
        chan2 = Channel()
        print ""
        Parallel(
            1 * source(-chan),
            1 * sink(+chan)
        )

