"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
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
		Spawn(element(this.reader(), next.writer()))
		this = next
	
	Parallel(root(cycles, this.reader(), head.writer()))

if __name__ == "__main__":
	ring(sys.argv[2:])

