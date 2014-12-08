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

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import logex

from gi.repository.GObject import MainLoop

logger = logging.getLogger()
formatter = logging.Formatter("%(asctime)s %(levelname).5s %(filename)s(%(lineno)s): %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logex.LOGFUNCTION = logging.debug

def raise_exception():
	raise Exception('raising exception')

class DBusService(dbus.service.Object):
	def __init__(self, bus, object_path='/com/logex_test/DBusTest'):
		super(DBusService, self).__init__(bus, object_path)

	@dbus.service.method(dbus_interface='com.logex_test.DBusTest',
					 in_signature='', out_signature='')
	def do_something(self):
		print("doing something")

	@dbus.service.method(dbus_interface='com.logex_test.DBusTest',
					 in_signature='', out_signature='')
	def crash(self):
		raise Exception('now crashing')

	@dbus.service.method(dbus_interface='com.logex_test.DBusTest',
					 in_signature='', out_signature='')
	def catch_exception(self):
		try:
			raise Exception('now crashing')
		except Exception as exc:
			print('caught exception %s' % exc)

	@dbus.service.method(dbus_interface='com.logex_test.DBusTest',
					 in_signature='', out_signature='')
	def dbus_in_dbus(self):
		bus = dbus.SystemBus()
		try:
			nm = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
			nm.GetDeviceByIpIface("nathoesunth")
		except Exception as exc:
			print('Caught exception "%s".' % exc)

	@logex.log(logfunction=logging.info, lazy=False, view_source=True)
	@dbus.service.method(dbus_interface='com.logex_test.DBusTest',
					 in_signature='isb', out_signature='')
	def logexc(self, arg1, noch_ein_arg, lazy=True):
		a = 1
		print("lazy?: %s" % lazy)
		raise_exception()

def do_something(x):
	x += 2
	raise_exception()
	print(x)

@logex.log(logfunction=logging.info, lazy=False, view_source=True, reraise=False)
def argstest(a, b=1):
	print(" * argstest start")
	c = 2
	do_something(c)
	x = c+2
	print("x: %s" % x)
	print(" * argstest done")
	print("")

def main():
	argstest('blah', b=b'abc')

	DBusGMainLoop(set_as_default=True)
	bus = dbus.SessionBus()
	name = dbus.service.BusName('com.logex_test.DBusTest', bus)
	service = DBusService(bus=bus)

	loop = MainLoop()
	loop.run()


if __name__ == '__main__':
	print('call with: "dbus-send --session --print-reply --dest=com.logex_test.BaseExceptionDBusTest /com/logex_test/DBusTest com.logex_test.DBusTest.catch_exception"')
	main()
