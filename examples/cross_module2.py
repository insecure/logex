from __future__ import (division, absolute_import, print_function, unicode_literals)

import logex

def raise_exception():
	raise Exception('raising exception')

def do_something_and_crash(x):
	x += 2
	raise_exception()
	print(x)

@logex.log(view_source=True, reraise=False)
def argstest(a, b=1):
	print(" * argstest module2 start")
	c = 2
	do_something_and_crash(c)
	x = c+2
	print("x: %s" % x)
	print(" * argstest module2 done")
	print("")
