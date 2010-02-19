"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
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
sys.path.append("..")

if len(sys.argv) > 1:
    mod = sys.argv[1]
else:
    mod = ''

if (mod == 'threads'):
    from pycsp.threads import *
elif (mod == 'processes'):
    from pycsp.processes import *
elif (mod == 'greenlets'):
    from pycsp.greenlets import *
elif (mod == 'net'):
    from pycsp.net import *
else:
    print "python",sys.argv[0],"[ threads | processes | greenlets | net ]"
    from pycsp.threads import *

print 'Using version', version

if sys.platform == 'win32' and (version[3] == 'processes'):
    print 'The examples are not compatible with PyCSP.processes and win32.'
    sys.exit(0)

