from types import *
import common


all = dir(common)

classes, functions, rest = [],[],[]
constants = []

for val in all:
    t = type(eval('common.'+val))
    if t == ClassType or t == TypeType:
        classes.append(val)
    elif t == FunctionType:
        functions.append(val)
    elif t == IntType:
        constants.append(val)
    else:
        rest.append(val)

print 'Classes:'
print classes
print
print 'Functions:'
print functions
print
print 'Constants'
print constants
print
print 'Rest:', rest
