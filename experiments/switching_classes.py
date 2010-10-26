
class Test1:
    def __init__(self, val):        
        self.val = val


class Test2:
    def __init__(self):
        pass

    def read(self):
        return self.val


t = Test1('Hello')

# Fails: print t.read()
t2 = Test2()
t2.__dict__ = t.__dict__


print t2.read()
