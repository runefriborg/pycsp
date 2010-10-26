import inspect

def func():
    print x
    x = 45

try:
    func()
except:
    pass

s = inspect.getsource(func)
s = 'if True:\n' + s[s.index('\n'):]

print s
lokal = {'x':[4,5]}

exec(s, lokal)
print lokal['x']
