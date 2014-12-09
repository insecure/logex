#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2014, Tobias Hommel
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  * Neither the name of the author nor the names of its contributors may
#    be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import (division, absolute_import, print_function, unicode_literals)

import logging
import threading

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import logex

try:
	from gi.repository.GObject import MainLoop
except ImportError:
	MainLoop = None

logger = logging.getLogger()
formatter = logging.Formatter("%(asctime)s %(levelname).5s %(filename)s(%(lineno)s): %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logex.LOGFUNCTION = logging.critical

BUS_NAME = 'org.logex_test.DBusTest'
OBJECT_PATH = '/org/logex_test/DBusTest'

def raise_exception():
	raise Exception('raising exception')

class DBusService(dbus.service.Object):
	def __init__(self, bus, object_path=OBJECT_PATH):
		super(DBusService, self).__init__(bus, object_path)

	@logex.log(view_source=True)
	@dbus.service.method(dbus_interface=BUS_NAME,
					 in_signature='isb', out_signature='')
	def crash(self, arg1, noch_ein_arg, lazy=True):
		a = 1
		print("lazy?: %s" % lazy)
		raise_exception()

def do_something_and_crash(x):
	x += 2
	raise_exception()
	print(x)

@logex.log(view_source=True, reraise=False)
def argstest(a, b=1):
	print(" * argstest start")
	c = 2
	do_something_and_crash(c)
	x = c+2
	print("x: %s" % x)
	print(" * argstest done")
	print("")

class CrashingThread(threading.Thread):

	def __init__(self):
		super(CrashingThread, self).__init__(daemon=True)

	@logex.log(reraise=False, view_source=True)
	def run(self):
		print(' -> in thread function')
		print(' -> crashing now')
		do_something_and_crash(123)
		print(' -> done')

def main():
	argstest('blah', b=b'abc')
	print('='*80)

	t = CrashingThread()
	t.start()
	import time
	time.sleep(1)
	print('='*80)

	if MainLoop is None:
		print('pygobject not installed, skipping dbus demo')
	else:
		print('starting D-Bus service at %s' % BUS_NAME)
		DBusGMainLoop(set_as_default=True)
		bus = dbus.SessionBus()
		name = dbus.service.BusName(BUS_NAME, bus)
		service = DBusService(bus=bus)
		print('call with: "dbus-send --session --print-reply --dest=%(busname)s %(object_path)s '
			  '%(busname)s.crash int32:123 string:foo boolean:true"' %
			  {'busname': BUS_NAME, 'object_path': OBJECT_PATH})

		loop = MainLoop()
		loop.run()


if __name__ == '__main__':
	main()
