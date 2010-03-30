import unittest
from __init__ import *
from scheduling import *
from random import expovariate

class DeadlineTestCase(unittest.TestCase):

    def setUp(self):
        self.deadline = 0.1
        self.iteration = 4
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
#            try:
#                pr("source")
#                chan_out(True)
#                pr("source done")
#                Remove_deadline()
#            except DeadlineException as e:
#                self.assertTrue(False)
#        
#        @process
#        def sink(chan_in):
#            try:
#                pr("sink")
#                chan_in()          
#                pr("sink done")
#                Remove_deadline()
#            except DeadlineException as e:
#                self.assertTrue(False)
#        
#        @process
#        def middlepriority():
#            try:
#                pr("middle")
#                time.sleep(4*self.deadline)
#                pr("middle done")
#                Remove_deadline()   
#            except DeadlineException as e:
#                self.assertTrue(False)
#        print
#        chan = Channel()

#        p1 = source(-chan)
#        p2 = sink(+chan)
#        p3 = middlepriority()
#        
#        Set_deadline(1*self.deadline,p1)
#        Set_deadline(3*self.deadline,p2)

#        Set_deadline(2*self.deadline,p3)
#        try:
#            Parallel(p1,
#                     p2,
#                     p3)
#        except DeadlineException as e:
#            self.assertTrue(False,e)
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

#    def test_AlternationChoiseWriter(self):
#        @process
#        def sink1(chan_in):
#            try:
#                for i in range(self.iteration):
#                    Set_deadline(2*self.deadline)                    
#                    chan_in()
#                    Remove_deadline()
#                    Wait(self.deadline)
#                retire(chan_in)
#            except ChannelRetireException:
#                pass

#        @process
#        def sink2(chan_in):
#            try:
#                for i in range(self.iteration):
#                    Set_deadline(self.deadline)                    
#                    chan_in()
#                    Remove_deadline()
#                retire(chan_in)
#            except ChannelRetireException:
#                pass
#               
#        @process
#        def source(chan_out, chan_out2):
#            try:
#                while True:
#                    Wait(0.1*self.deadline)     
#                    Alternation([
#                        {(chan_out,True):"print'\twarning'"},
#                        {(chan_out2,True):"print'\tgood'"}
#                    ]).execute()                       
#            except ChannelRetireException:
#                retire(chan_out, chan_out2)
#                pass

#        chan = Channel()
#        chan2 = Channel()
#        print ""
#        Parallel(
#            1 * sink1(+chan),
#            1 * sink2(+chan2),
#            1 * source(-chan,-chan2)
#        )


#    def test_AlternationChoiseReader(self):
#        @process
#        def source1(chan_out):
#            try:
#                for i in range(self.iteration):
#                    Set_deadline(2*self.deadline)                    
#                    chan_out("source1")
#                    Remove_deadline()
#                    Wait(self.deadline)
#                retire(chan_out)
#            except ChannelRetireException:
#                pass

#        @process
#        def source2(chan_out):
#            try:
#                for i in range(self.iteration):
#                    Set_deadline(self.deadline)                    
#                    chan_out("source2")
#                    Remove_deadline()
#                retire(chan_out)
#            except ChannelRetireException:
#                pass
#               
#        @process
#        def sink(chan_in, chan_in2):
#            try:
#                while True:
#                    Wait(0.1*self.deadline)     
#                    (g,msg) = Alternation([
#                        (chan_in,None),
#                        (chan_in2,None)
#                    ]).select()
#                    #print "\t g:",g          
#                    #print "\t msg:",msg                       
#             
#            except ChannelRetireException:
#                retire(chan_in, chan_in2)
#                pass

#        chan = Channel("chan")
#        chan2 = Channel("chan2")
#        print ""
#        Parallel(
#            1 * source1(-chan),
#            1 * source2(-chan2),
#            1 * sink(+chan,+chan2)
#        )


#    def test_ChoisemultipleWriter(self):
#        @process
#        def source1(chan_out):
#            try:
#                for i in range(self.iteration):
#                    Set_deadline(2*self.deadline)                    
#                    chan_out("\twarning")
#                    Remove_deadline()
#                    Wait(self.deadline)
#                retire(chan_out)
#            except ChannelRetireException:
#                pass

#        @process
#        def source2(chan_out):
#            try:
#                for i in range(self.iteration):
#                    Set_deadline(self.deadline)                    
#                    chan_out("\tgood")
#                    Remove_deadline()
#                retire(chan_out)
#            except ChannelRetireException:
#                pass
#               
#        @process
#        def sink(chan_in):
#            try:
#                while True:
#                    Wait(0.1*self.deadline)     
#                    print chan_in()
#            except ChannelRetireException:
#                retire(chan_in)
#                pass

#        chan = Channel("chan")
#        print ""
#        Parallel(
#            1 * source1(-chan),
#            1 * source2(-chan),
#            1 * sink(+chan)
#        )


    def test_ChoisemultipleReader(self):
        @process
        def sink(chan_in, deadline):
            try:
                while True:
                    Set_deadline(deadline)                    
                    chan_in()
                    print "\n-------------------------------------------------------------------------------------------\n\t",deadline
                    Remove_deadline()
                    #Wait(0.5*self.deadline)
            except ChannelPoisonException:
                pass
        @process
        def source(chan_out):

            for i in range(self.iteration):
                Wait(self.deadline)     
                chan_out(True)
            poison(chan_out)
            

        chan = Channel("chan")
        print ""
        Parallel(
            1 * source(-chan),
            1 * sink(+chan,self.deadline*5),
            1 * sink(+chan,self.deadline*30)            
        )
#        
#    def test_ChoisemultipleReader2(self):
#        @process
#        def sink(chan_in, deadline):
#            try:
#                while True:
#                    Set_deadline(deadline)                    
#                    chan_in()
#                    print "\t",deadline
#                    Remove_deadline()
#                    Wait(0.5*self.deadline)
#            except ChannelPoisonException:
#                pass

#        @process
#        def source(chan_out):
#            Wait(0.1*self.deadline)     
#            for i in range(self.iteration):
#                chan_out(True)
#            poison(chan_out)
#            

#        chan = Channel("chan")
#        print ""
#        Parallel(
#            1 * source(-chan),
#            1 * sink(+chan,self.deadline),
#            2 * sink(+chan,self.deadline*2)
#            )

#    def test_Alternation(self):
#        @process
#        def sink(chan_in,timer):
#            for i in range(1):
#                try:
#                    Set_deadline(timer)                    
#                    chan_in()
#                    Remove_deadline()
#                #except DeadlineException as e:
#                #    print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                except ChannelRetireException as e:
#                    print "\t got RetireException"
#                retire(chan_in)
#                
#        @process
#        def source(chan_out, chan_out2):
#            try:    
#                got_chan2 = False            
#                while True:
#                    Wait(self.deadline)
#                    (g,msg) = Alternation([
#                        {(chan_out,True):None},
#                        {(chan_out2,True):None}
#                    ]).select()                   
#                    if not got_chan2:
#                        self.assertTrue(g==chan_out2)
#                        got_chan2 = True
#                    else : self.assertTrue(g==chan_out)                                
#            except ChannelRetireException:
#                retire(chan_out, chan_out2)
#                pass

#        chan = Channel("chan")
#        chan2 = Channel("chan2")
#        print ""
#        Parallel(
#            1 * sink(+chan, 10*self.deadline),
#            1 * sink(+chan2, 5*self.deadline),
#            1 * source(-chan,-chan2)
#        )

#    def test_AlternationExecuteTimeoutDeadline(self):
#        @process
#        def source(chan_out):
#            try:
#                for i in range(self.iteration):
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
#                        Wait(0.01)          
#                        Set_deadline(self.deadline)
#                        first = Now()
#                        g,_ = Alternation([
#                            {chan_in:None},
#                            {Timeout(seconds=self.deadline):None}
#                        ]).select()
#                        
#                        second = Now()
#                        print "\tReceived two messages with a delay of",second-first,"(deadline is",self.deadline,")"
#                        Remove_deadline()
#                        self.assertTrue(second-first<self.deadline)
#                    except DeadlineException as e:
#                        dead = Now()
#                        print "\tDeadlineException deadline_passed_by", e.deadline_passed_by
#                        self.assertTrue(dead-first>=self.deadline)
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


#        
