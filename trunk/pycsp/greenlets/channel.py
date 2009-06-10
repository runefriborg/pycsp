"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from scheduling import Scheduler

# Constants
ACTIVE, DONE, POISON = range(3)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

# Classes
class ChannelReq:
    def __init__(self, process, msg=None):
        self.msg = msg
        self.result = FAIL
        self.process = process

    def poison(self):
        self.result = POISON
        self.process.notify(POISON)

    def offer(self, recipient):
        if self.process.state == recipient.process.state == ACTIVE:
            recipient.msg= self.msg
            self.result=SUCCESS
            recipient.result=SUCCESS
            self.process.notify(DONE)
            recipient.process.notify(DONE)
            return True
        return False


class Channel:
    """ Channel class. Blocking communication
    
    >>> from __init__ import *

    >>> @process
    ... def WrapP():
    ...     @process
    ...     def P1(cout):
    ...         while True:
    ...             cout('Hello World')
    ...
    ...     C = Channel()
    ...     Spawn(P1(OUT(C)))
    ...
    ...     cin = IN(C)
    ...     print cin()
    ...
    ...     retire(cin)

    >>> Parallel(WrapP())
    Hello World
    """

    def __init__(self, name=None):

        if name == None:
            # Create name based on host ID and current time
            import uuid
            name = str(uuid.uuid1())

        self.name=name

        self.readqueue = []
        self.writequeue = []
        
        # Count, makes sure that all processes knows how many channel ends have retired
        self.readers = 0
        self.writers = 0

        self.ispoisoned = False

        self.s = Scheduler()
        
    def check_poison(self):        
        if self.ispoisoned:
            raise ChannelPoisonException()

    def _read(self):
        self.check_poison()

        p = self.s.current
        
        # If anyone is on the writequeue and ACTIVE, then we can do the match right away
        # This hack provides a 150% performance improvement and can be removed
        # without breaking anything.
        for w in self.writequeue:
            if w.process.state == ACTIVE:
                msg = w.msg
                w.result = SUCCESS
                w.process.state = DONE
                if p != w.process:
                    self.s.next.append(w.process)
                return msg        

        p.setstate(ACTIVE)
        req = ChannelReq(p)
        self.post_read(req)
        req.process.wait()
        self.remove_read(req)

        if req.result==SUCCESS:
            return req.msg
        
        self.check_poison()
            
        print 'We should not get here in read!!!', req.status.state
        return None #Here we should handle that a read was cancled...

    
    def _write(self, msg):
        self.check_poison()

        p = self.s.current
        
        # If anyone is on the readqueue and ACTIVE, then we can do the match right away
        # This hack provides a 150% performance improvement and can be removed
        # without breaking anything.
        for r in self.readqueue:
            if r.process.state == ACTIVE:
                r.msg = msg
                r.result = SUCCESS
                r.process.state = DONE
                if p != r.process:
                    self.s.next.append(r.process)
                return True

        p.setstate(ACTIVE)
        req = ChannelReq(p,msg=msg)
        self.post_write(req)
        req.process.wait()
        self.remove_write(req)

        if req.result==SUCCESS:
            return True
    
        self.check_poison()

        print 'We should not get here in write!!!', req.status
        return None #Here we should handle that a read was cancled...

    def post_read(self, req):
        self.readqueue.append(req)
        self.match()

    def remove_read(self, req):
        self.readqueue.remove(req)
        
    def post_write(self, req):
        self.writequeue.append(req)
        self.match()

    def remove_write(self, req):
        self.writequeue.remove(req)

    def match(self):
        if self.readqueue and self.writequeue:
            for w in self.writequeue:
                for r in self.readqueue:
                    if w.offer(r):
                        # Did an offer
                        # We can guarantee, that there will always be someone to call offer,
                        # since everything is run in a single thread. Thus we break the loop.
                        return

    def poison(self):
        if not self.ispoisoned:
            self.ispoisoned = True
            map(ChannelReq.poison, self.readqueue)
            map(ChannelReq.poison, self.writequeue)


    def join_reader(self):
        self.readers+=1

    def join_writer(self):
        self.writers+=1

    def leave_reader(self):
        self.readers-=1
        if self.readers==0:
            self.poison()
            return

    def leave_writer(self):
        self.writers-=1
        if self.writers==0:
            self.poison()
            return
            
    def status(self):
        print 'Reads:',len(self.readqueue), 'Writes:',len(self.writequeue)


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
