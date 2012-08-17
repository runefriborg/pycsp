from pycsp_import import *
from random import randint

@process(fail_type=CHECKPOINT, fail_type_after_retires=FAILSTOP)
def P(cout):
  i = load(i = -10)
  for i in range(i, 10):
    x = i/randint(0, 1)
    cout(x)

@process(fail_type=CHECKPOINT, fail_type_after_retires=FAILSTOP)
def Q(cin):
  while True:
    print cin()

c = Channel()

Parallel(
  P(-c), 
  Q(+c)
)