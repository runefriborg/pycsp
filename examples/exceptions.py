from pycsp_import import *

@process(fail_type=FAILSTOP)
def producer(job_out, i, stop):
    for i in range(i, stop):
        job_out(i)

@process(fail_type=FAILSTOP)
def worker(job_in, job_out):
    while True:
        x = 1.0/job_in()
        job_out(x)

@process(fail_type=FAILSTOP)
def consumer(job_in):
    while True:
        x = job_in()
        print x

c = Channel('prod-worker')
d = Channel('worker-consumer')

Parallel(
    producer(-c, -10, 11),
    3 * worker(+c, -d),
    consumer(+d)
)