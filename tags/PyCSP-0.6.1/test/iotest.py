from common import *
import time

@io
def wait(seconds):
    time.sleep(seconds)
	
@process
def delay_output(msg, seconds):
    wait(seconds)
    print msg

Parallel(
    [ delay_output('%d second delay' % (i),i) for i in range(10)]
    )
