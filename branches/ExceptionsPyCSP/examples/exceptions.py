from pycsp_import import *

@process
def producer(job_out):
    for i in range(-10, 11):
        job_out(i)

@process
def worker(job_in):
    while True:
        x = job_in()
        print 1.0/x

c = Channel()

Parallel(
    producer(-c),
    3 * worker(+c)
)