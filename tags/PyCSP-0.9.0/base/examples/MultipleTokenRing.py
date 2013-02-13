"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import sys
from pycsp_import import *

elements = 64

@process
def element(this_read, next_write):
    while True:
        token = this_read()
        next_write(token + 1)

@process
def root(cycles, tokens, this_read, next_write):
	next_write(1)
	token = this_read()

	sys.stdout.write("start\n")
	sys.stdout.flush()
	
	for i in range(tokens):
		next_write(i + 1)

	while cycles:
		for i in range(tokens):
			token = this_read()
			next_write(token + 1)
		cycles = cycles - 1
	
	sum = 0
	for i in range(tokens):
		sum += this_read()

	sys.stdout.write("end\n")
	sys.stdout.flush()

	sys.stdout.write(str(sum) + "\n")

	retire(next_write, this_read)

def ring(args):
	global elements
	cycles = 0
	tokens = 1
	if len(args) > 0:
		cycles = int(args[0])
	if len(args) > 1:
		tokens = int(args[1])

	head = Channel()
	this = head

	#chanlist to avoid Channel() datastructures to be gb_collected, when used in element processes
	chanlist = [head]
	for i in range(elements - 1):
		next = Channel()
		chanlist.append(next)
		Spawn(element(this.reader(), next.writer()))
		this = next
	
	Parallel(root(cycles, tokens, this.reader(), head.writer()))

if __name__ == "__main__":
	ring(sys.argv[2:])

shutdown()
