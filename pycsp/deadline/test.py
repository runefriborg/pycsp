import unittest
from __init__ import *
from scheduling import *
from random import expovariate

class DeadlineTestCase(unittest.TestCase):

    def setUp(self):
        self.deadline = 0.2
        self.iteration = 2
        RT_Scheduler().decompose()


    def tearDown(self):
        RT_Scheduler().decompose()

#    def test_readDeadline(self):
#        @process
#        def source(chan_out):
#            for i in range(2*self.iteration):
#                waittime = expovariate(1/self.deadline)
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
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        val = chan_in()
#                        second = Now()
#                        print "\tReceived two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
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
#        @process
#        def sink(chan_in):
#            for i in range(2*self.iteration):
#                waittime = expovariate(1/self.deadline)
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
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        chan_out("Hello world")
#                        second = Now()
#                        print "\tSent two messages with a delay of :",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
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
#        @process
#        def sink(chan_in):
#            try:
#                for i in range(2*self.iteration):
#                    waittime = expovariate(1/self.deadline)
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
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        Alternation([
#                            {(chan_out,True):"chan_out2(True)"},
#                            {(chan_out2,True):"chan_out(True)"}
#                        ]).execute()
#                        second = Now()
#                        print "\tSent two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
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
#        @process
#        def source(chan_out):
#            try:
#                for i in range(2*self.iteration):
#                    waittime = expovariate(1/self.deadline-0.07)
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
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        Alternation([
#                            {(chan_in):"chan_in2()"},
#                            {(chan_in2):"chan_in()"}
#                        ]).execute()
#                        second = Now()
#                        print "\tReceived two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
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


#    def test_AlternationExecuteTimeoutDeadline(self):
#        @process
#        def source(chan_out):
#            try:
#                for i in range(2*self.iteration):
#                    waittime = expovariate(1/self.deadline)
#                    chan_out(True)
#                    Wait(waittime)                    
#                retire(chan_out)
#            except ChannelRetireException:
#                pass
#                
#        @process
#        def sink(chan_in):
#            try:
#                while True:
#                    try:                               
#                        chan_in()          
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        g,_ = Alternation([
#                            {chan_in:""},
#                            {Timeout(seconds=self.deadline):None}
#                        ]).select()
#                        second = Now()
#                        print "\tReceived two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        Remove_deadline()
#                        continue
#            except ChannelRetireException:
#                retire(chan_in)
#                pass

#        chan = Channel()
#        chan2 = Channel()
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )


#    def test_AlternationExecuteSkipDeadline(self):
#        @process
#        def source(chan_out):
#            try:
#                for i in range(self.iteration):
#                    waittime = expovariate(1/self.deadline-0.07)
#                    chan_out(True)
#                    Wait(waittime)                    
#                retire(chan_out)
#            except ChannelRetireException:
#                pass
#                
#        @process
#        def sink(chan_in):
#            try:
#                while True:
#                    try:                               
#                        chan_in()          
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        g,_ = Alternation([
#                            {chan_in:""},
#                            {Skip():"Wait(expovariate(1/self.deadline))"}
#                        ]).execute()
#                        second = Now()
#                        print "\tReceived two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        Remove_deadline()
#                        continue
#            except ChannelRetireException:
#                retire(chan_in)
#                pass

#        chan = Channel()
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )

#    def test_Alternationchoise1Deadline(self):
#        @choice
#        def action(channel_input=None):
#            Wait(expovariate(1/self.deadline))

#        @process
#        def source(): 
#            for x in range(self.iteration):
#                try:                               
#                    Set_deadline(self.deadline)
#                    first = Now()
#                    Alternation([{Skip():action()}]).execute()
#                    second = Now()
#                    Remove_deadline()
#                    print "\tReceived two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                    self.assertTrue(second-first<self.deadline)
#                except DeadlineException as e:
#                    self.assertTrue(Now()-first>=self.deadline)
#                    print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                    Remove_deadline()
#                    continue        
#        print ""                                
#        Parallel(source())

#    def test_Alternationchoise2Deadline(self):
#        @choice
#        def action(channel_input=None):
#           try:
#                Set_deadline(self.deadline)
#                first = Now()
#                Wait(expovariate(1/self.deadline))
#                second = Now()
#                Remove_deadline()
#                print "\tReceived two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                self.assertTrue(second-first<self.deadline)
#           except DeadlineException as e:
#                self.assertTrue(Now()-first>=self.deadline)
#                print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                Remove_deadline()
#                

#        @process
#        def source(): 
#            for x in range(self.iteration):
#                    Alternation([{Skip():action()}]).execute()
#        print ""                                
#        Parallel(source())


#    def test_PoisonAndDeadline1(self):
#        @process
#        def source(chan_out):
#            chan_out(True)
#            Wait(self.deadline)
#            poison(chan_out)    
#            
#        @process
#        def sink(chan_in):
#            Set_deadline(self.deadline)
#            chan_in()          
#            self.assertRaises(DeadlineException,chan_in)
#            self.assertRaises(ChannelPoisonException,chan_in)

#        chan = Channel()
#        Parallel(source(-chan),
#                 sink(+chan))
#                 
#    def test_PoisonAndDeadline2(self):
#        @process
#        def source(chan_out):
#            Set_deadline(self.deadline)
#            chan_out(True)
#            self.assertRaises(DeadlineException,chan_out,True)
#            self.assertRaises(ChannelPoisonException,chan_out,True)
#            
#        @process
#        def sink(chan_in):
#            chan_in()          
#            Wait(self.deadline)
#            poison(chan_in)    
#            
#        chan = Channel()
#        Parallel(source(-chan),
#                 sink(+chan))
#                 
#                 
#    def test_RetireAndDeadline(self):
#        @process
#        def source(chan_out):
#            chan_out(True)
#            Wait(self.deadline)
#            retire(chan_out)    
#            
#        @process
#        def sink(chan_in):
#            Set_deadline(self.deadline)
#            chan_in()          
#            self.assertRaises(DeadlineException,chan_in)
#            self.assertRaises(ChannelRetireException,chan_in)

#        chan = Channel()
#        Parallel(source(-chan),
#                 sink(+chan))
#                 
#                 
#                 
#    def test_Reader_Inheritance(self):
#        def pr(value):
#            print "\t-------------------------------------------------"
#            print "\t",value
#            print "\t-------------------------------------------------"

#        @process
#        def source(chan_out):
#            pr("source")
#            chan_out(True)
#            pr("source done")
#            Remove_deadline()
#        
#        @process
#        def sink(chan_in):
#            pr("sink")
#            chan_in()          
#            pr("sink done")
#            Remove_deadline()
#        
#        @process
#        def middlepriority():
#            pr("middle")
#            time.sleep(4*self.deadline)
#            pr("middle done")
#            Remove_deadline()   
#        print
#        chan = Channel()

#        p1 = source(-chan)
#        p2 = sink(+chan)
#        p3 = middlepriority()
#        
#        Set_deadline(1*self.deadline,p1)
#        Set_deadline(3*self.deadline,p2)

#        Set_deadline(2*self.deadline,p3)
#        Parallel(p1,
#                 p2,
#                 p3)
#                 
#    def test_Writer_Inheritance(self):
#        def pr(value):
#            print "\t-------------------------------------------------"
#            print "\t",value
#            print "\t-------------------------------------------------"

#        @process
#        def source(chan_out):
#            pr("source")
#            chan_out(True)
#            pr("source done")
#            Remove_deadline()
#        
#        @process
#        def sink(chan_in):
#            pr("sink")
#            chan_in()          
#            pr("sink done")
#            Remove_deadline()
#        
#        @process
#        def middlepriority():
#            pr("middle")
#            time.sleep(4*self.deadline)
#            pr("middle done")
#            Remove_deadline()   
#        print
#        chan = Channel()

#        p1 = source(-chan)
#        p2 = sink(+chan)
#        p3 = middlepriority()

#        Set_deadline(3*self.deadline,p1)
#        Set_deadline(1*self.deadline,p2)

#        Set_deadline(2*self.deadline,p3)
#        Parallel(p1,
#                 p2,
#                 p3)

#    def test_channelpriority_from_no_deadline(self):
#        @process
#        def sink(chan_in):
#            for i in range(2*self.iteration):
#                waittime = expovariate(1/self.deadline)
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
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        chan_out("Hello world")
#                        second = Now()
#                        print "\tSent two messages with a delay of :",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        continue
#            except ChannelRetireException:
#                pass
#        chan = Channel("channel")
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )


#    def test_channelpriority_from_low_deadline(self):
#        @process
#        def sink(chan_in):
#            for i in range(self.iteration):
#                Set_deadline(self.deadline*100)
#                val = chan_in()
#                waittime = expovariate(1/self.deadline)
#                Wait(waittime)
#                val = chan_in()
#                Wait(waittime)
#                Remove_deadline()                
#            retire(chan_in)
#            
#        @process
#        def source(chan_out):
#            try:
#                while True:
#                    try:
#                        chan_out("Hello world")
#                        first = Now()
#                        Set_deadline(self.deadline)
#                        chan_out("Hello world")
#                        second = Now()
#                        print "\tSent a message with a delay of :",second-first,"(deadline is",self.deadline,")"
#                        self.assertTrue(second-first<self.deadline)
#                        Remove_deadline()                        
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        Remove_deadline()
#                        continue
#            except ChannelRetireException:
#                pass
#                
#        chan = Channel("channel")
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )
#        
#    def test_channelpriority_from_no_deadline2(self):
#        @process
#        def source(chan_out):
#            for i in range(2*self.iteration):
#                waittime = expovariate(1/self.deadline)
#                Wait(waittime)
#                val = chan_out(True)
#            retire(chan_out)
#            
#        @process
#        def sink(chan_in):
#            try:
#                while True:
#                    try:
#                        chan_in()
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        chan_in()
#                        second = Now()
#                        print "\tReceived two messages with a delay of :",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        continue
#            except ChannelRetireException:
#                pass
#                
#        chan = Channel("channel")
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )


#    def test_channelpriority_from_low_deadline2(self):
#        @process
#        def source(chan_out):
#            for i in range(self.iteration):
#                Set_deadline(self.deadline*100)
#                val = chan_out(True)
#                waittime = expovariate(1/self.deadline)
#                Wait(waittime)
#                val = chan_out(True)
#                Wait(waittime)
#                Remove_deadline()                
#            retire(chan_out)
#            
#        @process
#        def sink(chan_in):
#            try:
#                while True:
#                    try:
#                        chan_in()
#                        first = Now()
#                        Set_deadline(self.deadline)
#                        chan_in()
#                        second = Now()
#                        print "\tReceived two message with a delay of :",second-first,"(deadline is",self.deadline,")"
#                        self.assertTrue(second-first<self.deadline)
#                        Remove_deadline()                        
#                    except DeadlineException as e:
#                        self.assertTrue(Now()-first>=self.deadline)
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        Remove_deadline()
#                        continue
#            except ChannelRetireException:
#                pass
#                
#        chan = Channel("channel")
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan)
#        )
#        
#        
#    def test_nestedDeadline(self):
#        @process
#        def sink(chan_in):
#            for i in range(3*self.iteration):
#                waittime = expovariate(1/self.deadline)-(0.3*self.deadline)
#                Wait(waittime)
#                val = chan_in()
#                #print "Received one messages"
#            retire(chan_in)
#            
#        @process 
#        def middle(chan_out):
#            
#            @process
#            def source(chan_out):
#                try:
#                    while True:                
#                        try:
#                            chan_out("Hello world")
#                            Set_deadline(self.deadline)
#                            first = Now()
#                            chan_out("Hello world")
#                            second = Now()
#                            print "\tSent two messages with a delay of :",second-first,"(deadline is",self.deadline,")"
#                            Remove_deadline()
#                            self.assertTrue(second-first<self.deadline)
#                        except DeadlineException as e:
#                            self.assertTrue(Now()-first>=self.deadline)
#                            print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                except ChannelRetireException:
#                    pass
#                    
#            Parallel(3*source(chan_out))
#        
#        chan = Channel()
#        print ""
#        Parallel(
#            1 * middle(-chan),
#            1 * sink(+chan)
#        )

#    def test_nestedDeadline2(self):
#        @process
#        def sink(chan_in):
#            for i in range(3*self.iteration):
#                waittime = expovariate(1/self.deadline)-(0.2*self.deadline)
#                Wait(waittime)
#                Alternation([
#                            {chan_in:None},
#                            {Timeout(seconds=2*self.deadline):None}
#                        ]).execute()
#            poison(chan_in)
#            print "poisend sink exiting\n"
#            
#            
#        @process 
#        def middle(chan_out):            
#            @process
#            def source(chan_out):
#                try:
#                    print "in source"
#                    while True:
#                        chan_out("Hello world")
#                        print "wrote"
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        print "writing"                    
#                        chan_out("Hello world")
#                        second = Now()
#                        print "\tSent two messages with a delay of :",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                except ChannelPoisonException:
#                    print "got PoisonException\n"
#                except  DeadlineException :
#                    print "got DeadlineException\n"


#            print "b4 parallel"                   
#            Parallel(1*source(chan_out))
#       

#        chan = Channel()
#        logging.warning("chan: %s"%chan)
#        print ""
#        Parallel(
#            1 * middle(-chan),
#            1 * sink(+chan)
#        )

    def test_AlternationChoiseWriter(self):
        @process
        def sink1(chan_in):
            try:
                for i in range(self.iteration):
                    Set_deadline(2*self.deadline)                    
                    chan_in()
                    Remove_deadline()
                    #Wait(self.deadline)
                retire(chan_in)
            except ChannelRetireException:
                pass

        @process
        def sink2(chan_in):
            try:
                for i in range(self.iteration):
                    Set_deadline(self.deadline)                    
                    chan_in()
                    Remove_deadline()
                retire(chan_in)
            except ChannelRetireException:
                pass
               
        @process
        def source(chan_out, chan_out2):
            try:
                while True:
                    Wait(0.1*self.deadline)     
                    Alternation([
                        {(chan_out,True):"print'chan_out(True)'"},
                        {(chan_out2,True):"print' chan_out2(True)'"}
                    ]).execute()                       
            except ChannelRetireException:
                retire(chan_out, chan_out2)
                pass

        chan = Channel()
        chan2 = Channel()
        print ""
        Parallel(
            1 * sink1(+chan),
            1 * sink2(+chan2),
            1 * source(-chan,-chan2)
        )

