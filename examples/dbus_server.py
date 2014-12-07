#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Tobias Hommel <software@genoetigt.de>
#
# Distributed under terms of the BSD license.

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
logex.MESSAGE_TEMPLATE = 'Unhandled exception in %(module)s::%(funcname)s(%(args)s' \
								 ' -- %(kwargs)s -- %(dict)s):\n%(traceback)s\n%(source)s\n'

def raise_exception():
	raise Exception('raising exception')

class DBusService(dbus.service.Object):
	def __init__(self, bus, object_path='/org/insecutor/DBusTest'):
		super(DBusService, self).__init__(bus, object_path)

	@dbus.service.method(dbus_interface='org.insecutor.DBusTest',
					 in_signature='', out_signature='')
	def do_something(self):
		print("doing something")

	@dbus.service.method(dbus_interface='org.insecutor.DBusTest',
					 in_signature='', out_signature='')
	def crash(self):
		raise Exception('now crashing')

	@dbus.service.method(dbus_interface='org.insecutor.DBusTest',
					 in_signature='', out_signature='')
	def catch_exception(self):
		try:
			raise Exception('now crashing')
		except Exception as exc:
			print('caught exception %s' % exc)

	@dbus.service.method(dbus_interface='org.insecutor.DBusTest',
					 in_signature='', out_signature='')
	def dbus_in_dbus(self):
		bus = dbus.SystemBus()
		try:
			nm = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
			nm.GetDeviceByIpIface("nathoesunth")
		except Exception as exc:
			print('Caught exception "%s".' % exc)

	@logex.log(logfunction=logging.info, lazy=False, view_source=True)
	@dbus.service.method(dbus_interface='org.insecutor.DBusTest',
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
	name = dbus.service.BusName('org.insecutor.DBusTest', bus)
	service = DBusService(bus=bus)

	loop = MainLoop()
	loop.run()


if __name__ == '__main__':
	print('call with: "dbus-send --session --print-reply --dest=org.insecutor.BaseExceptionDBusTest /org/insecutor/DBusTest org.insecutor.DBusTest.catch_exception"')
	main()
