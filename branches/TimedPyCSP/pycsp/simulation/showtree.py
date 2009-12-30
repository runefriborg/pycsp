#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2008 Doug Hellmann All rights reserved.
#
"""
"""

__version__ = "$Id: heapq_showtree.py 1413 2008-05-11 17:04:47Z dhellmann $"

import math
from cStringIO import StringIO

def show_tree(tree, total_width=36, fill=' ',offset=0):
    """Pretty-print a tree."""
    output = StringIO()
    last_row = -1
    for i, n in enumerate(tree):
        if i:
            row = int(math.floor(math.log(i+1, 2)))
        else:
            row = 0
        if row != last_row:
            output.write('\n'+' '*offset)
        columns = 2**row
        col_width = int(math.floor((total_width * 1.0) / columns))
        output.write(str(n).center(col_width, fill))
        last_row = row
    print output.getvalue()
    print ' '*offset,'-' * total_width
    print
    return

if __name__ == '__main__':
    print 'With dot as fill character:'
    show_tree([ 0, 1, 2, 3, 4, 5, 6 ], fill='.')
    print 'Wider:'
    show_tree([ 0, 1, 2, 3, 4, 5, 6 ], total_width=60)
