
import sys
from common import *

elements = 64

@process
def element(this_read, next_write):
    while True:
        token = this_read()
        next_write(token + 1)

@process
def root(cycles, this_read, next_write):
	next_write(1)
	token = this_read()

	sys.stdout.write("start\n")
	sys.stdout.flush()
	while cycles:
		next_write(token + 1)
		token = this_read()
		cycles = cycles - 1
	sys.stdout.write("end\n")
	sys.stdout.flush()

	sys.stdout.write(str(token) + "\n")

	retire(next_write, this_read)

def ring(args):
	global elements
	cycles = 0
	if len(args) > 0:
		cycles = int(args[0])

	head = Channel()
	this = head

	#chanlist to avoid Channel() datastructures to be gb_collected, when used in element processes
	chanlist = [head]

	for i in range(elements - 1):
		next = Channel()
		chanlist.append(next)
		Spawn(element(IN(this), OUT(next)))
		this = next
	
	Parallel(root(cycles, IN(this), OUT(head)))

if __name__ == "__main__":
	ring(sys.argv[2:])

