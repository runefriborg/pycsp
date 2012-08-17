from pycsp_import import *
from random import randint

@process(fail_type=CHECKPOINT, retries=-1)
def producer(job_out, start, end):
  i = load(i = start)
  for i in range(i, end):
    job_out("x: " + str(i))
    1 / randint(0, 1)
    job_out("y: " + str(i))

@process(fail_type=CHECKPOINT, retries=-1)
def consumer(job_in):
  while True:
    x = job_in()
    y = job_in()
    print x, y

c = Channel()

Parallel(
  producer(-c, -5, 6),
  consumer(+c)
)