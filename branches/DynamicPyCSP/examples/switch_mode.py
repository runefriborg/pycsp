from pycsp_import import *

A = Channel()

@process
def Fun(cin):
    while True:
        print cin()

Spawn(Fun(A.reader()))

cout = A.writer()

cout('Test')



cout2 = A.writer()

cout2('Test2')



