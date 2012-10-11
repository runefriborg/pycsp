from pycsp_import import *

A = Channel("A")

@multiprocess
def redirect(cout):
    B = Channel("B")
    cout(B.writer())
    cin = B.reader()
    while True:
        print cin()


getChan = A.reader()

@multiprocess
def producer(dispatch):
    
    # receive channel end
    write = dispatch()

    for i in range(4):
        write(i)
    poison(write)

Parallel(redirect(A.writer()),
         producer(getChan))

shutdown()
