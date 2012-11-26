import sys
sys.path.append("..")

import pycsp.greenlets as pycsp

@pycsp.process
def readP(cin):
  cin()

A = pycsp.Channel("A")

pycsp.Spawn(1000000 * readP(A.reader()))

cout = A.writer()
for i in xrange(1000000):
  cout(i)
  if (i%20000 == 0):
      sys.stdout.write(".")
      sys.stdout.flush()

sys.stdout.write("done\n")

pycsp.shutdown()
