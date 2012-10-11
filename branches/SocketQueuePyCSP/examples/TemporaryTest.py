from pycsp_import import *


@process
def fisk(cin):
    cin()
    poison(cin)

@process
def fisk2(cout):
    for i in range(4):
        cout(i)

A = Channel()  
print "Channel address: ", A.address

Parallel(fisk(A.reader()) * 4,
         fisk2(A.writer()))

print "The End"

shutdown()
