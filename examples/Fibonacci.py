from common import *

@process
def Prefix(cin, cout, prefix):
    cout(prefix)
    while True:
        cout(cin())

@process
def Delta2(cin, cout1, cout2):
    while True:
        msg = cin()
        Alternation([{
            (cout1,msg):'cout2(msg)',
            (cout2,msg):'cout1(msg)'
            }]).execute()

@process
def Plus(cin1, cin2, cout):
    while True:
        cout(cin1() + cin2())

@process
def Tail(cin, cout):
    dispose = cin()
    while True:
        cout(cin())

@process
def Pairs(cin, cout):
    pA, pB, pC = Channel('pA'), Channel('pB'), Channel('pC')
    Parallel(
        Delta2(cin, -pA, -pB),
        Plus(+pA, +pC, cout),
        Tail(+pB, -pC)
    )
    
@process
def Printer(cin, limit):
    for i in xrange(limit):
        print cin(),
    poison(cin)

A = Channel('A')
B = Channel('B')
C = Channel('C')
D = Channel('D')
printC = Channel()

Parallel(
    Prefix(B.reader(), A.writer(), prefix=0),
    Prefix(C.reader(), B.writer(), prefix=1),
    Pairs(D.reader(), C.writer()),
    Delta2(A.reader(), D.writer(), printC.writer()),
    Printer(printC.reader(), limit=20)
)

