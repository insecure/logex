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

import logging
import threading
import time

import logex

logger = logging.getLogger()
formatter = logging.Formatter("%(asctime)s %(levelname).5s %(filename)s(%(lineno)s): %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logex.LOGFUNCTION = logging.critical


def raise_exception():
	raise Exception('raising exception')

def do_something_and_crash(x):
	x += 2
	raise_exception()
	print(x)

class CrashingThread(threading.Thread):

	def __init__(self):
		super(CrashingThread, self).__init__()
		self.daemon = True

	@logex.log(reraise=False, view_source=True)
	def run(self):
		print(' -> in thread function')
		print(' -> crashing now')
		do_something_and_crash(123)
		print(' -> done')

def main():
	t = CrashingThread()
	print('===== starting thread...')
	t.start()
	time.sleep(1)
	print('===== main function done, exiting...')


if __name__ == '__main__':
	main()
