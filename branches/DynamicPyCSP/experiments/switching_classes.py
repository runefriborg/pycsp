
class Test1:
    def __init__(self, val):        
        self.val = val

class Test2:
    def __init__(self):
        pass

    def read(self):
        return self.val


t = Test1('Hello')
print t

def foo():
    print t
    _t = t
    print _t.read()

test_for_sideeffect = Test1('Fisk')


try:
    print t.read() # must fail
    print 'Fail!'    
except:
    print 'Success'


t.__class__ = Test2

print t.read()
foo()

try:
    print test_for_sideeffect.read() # must fail
    print 'Fail!'    
except:
    print 'Success'

