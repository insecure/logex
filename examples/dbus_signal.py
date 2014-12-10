#!/usr/bin/python
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

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import logex

try:
	from gi.repository.GObject import MainLoop
except ImportError:
	print('pygobject not installed!')
	exit(1)

def print_exception(message):
	print('logex caught an unhandled exception somewhere:\n'
		  '++++++++++++++++++++++++++++++++++++++++++++++\n'
		  '%s\n'
		  '++++++++++++++++++++++++++++++++++++++++++++++\n' % message)

logex.LOGFUNCTION = print_exception

def raise_exception():
	raise Exception('raising exception')

@logex.log(view_source=True, reraise=False)
def catchall_signal_handler(*args, **kwargs):
	print('received D-Bus signal: "%s", "%s"' % (args, kwargs))
	raise_exception()

def main():
	DBusGMainLoop(set_as_default=True)
	bus = dbus.SystemBus()
	print("connecting to some signals")
	bus.add_signal_receiver(catchall_signal_handler)
	loop = MainLoop()
	loop.run()


if __name__ == '__main__':
	main()
