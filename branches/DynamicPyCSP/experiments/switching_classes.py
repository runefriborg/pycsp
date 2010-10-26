
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

# Fails: print t.read()

t.__class__ = Test2

print t.read()
foo()

print test_for_sideeffect.read() # should fail
