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
"""This module provides ways to log unhandled exceptions in a function.
This can be extremely helpful for D-Bus signal handlers which crash, more or less, silently.
The same goes for thread functions or the main function in a daemon.

To add exception logging to a function simply decorate it with this modules log() function:
>>> import logex

>>> @logex.log
>>> def my_function():
>>> 	pass

The module can either be globally configured or via parameters to the decorator. Global parameters have the same
name as the decorator parameter, only in uppercase.
"""

from __future__ import (division, absolute_import, print_function, unicode_literals)

import inspect
import logging
import traceback
import functools

__version__ = '1.0.0'

LOGFUNCTION = logging.error
MESSAGE_TEMPLATE = ('Unhandled exception in %(module)s::%(funcname)s(%(args)s'
					', %(kwargs)s):\n%(traceback)s\n%(source)s')
ADVANCED = False
LAZY = False
RERAISE = True
CATCHALL = False
VIEW_SOURCE = False
LINE_NUMBERS = True

def _generate_source_view(filename, lineno, sourcelines, line_numbers=LINE_NUMBERS):
	source_view = ['----- sourcecode [%s(%s)] -----' % (filename, lineno)]
	if line_numbers:
		number_len = len(str(lineno+len(sourcelines)))
		source_view.append(''.join([
			'%*s %s' % (number_len, number, line) for number, line in enumerate(sourcelines, lineno)
		]))
	else:
		source_view.append(''.join(sourcelines))
	source_view.append('-'*len(source_view[0]))
	return '\n'.join(source_view)

def _generate_log_message(template, wrapped_f, args, kwargs, frame, view_source=VIEW_SOURCE, line_numbers=LINE_NUMBERS):
	try:
		sourcelines, lineno = inspect.getsourcelines(wrapped_f)
	except IOError:
		sourcelines = []
		lineno = -1
	try:
		filename = inspect.getsourcefile(wrapped_f)
	except TypeError:
		filename = '<builtin>'
	if view_source:
		source = _generate_source_view(filename, lineno, sourcelines, line_numbers=line_numbers)+'\n'
	else:
		source = ''
	return template % {
		'traceback': traceback.format_exc(),
		'funcname': wrapped_f.__name__,
		'module': wrapped_f.__module__,
		'args': args,
		'kwargs': kwargs,
		'source': source,
	}

def log(wrapped_f=None, logfunction=LOGFUNCTION, lazy=LAZY, advanced=ADVANCED,
		template=MESSAGE_TEMPLATE, reraise=RERAISE, catchall=CATCHALL,
		view_source=VIEW_SOURCE, line_numbers=LINE_NUMBERS):
	'''Decorator function that logs all unhandled exceptions in a function.
	This is especially useful for thread functions in a daemon or functions which are used as D-Bus signal handlers.

	:param wrapped_f: the decorated function(ignore when using @-syntax)
	:param logfunction: the logging function or a function returning a logging function (depending on `lazy` parameter)
	:type logfunction: function
	:param lazy: if True, `function` returns the actual logging function
	:type lazy: bool
	:param advanced: if True, pass the details to `function`, if False only pass the generated message to `function`
	:type advanced: bool
	:param template: The message to be logged. The following place holders will be replaced in the message:
		- %(traceback)s: the traceback to the exception
		- %(funcname)s: the name of the function in which the exception occurred
		- %(module)s: the name of the module containing the function
		- %(args)s: the arguments to the function
		- %(kwargs)s: the keyword arguments to the function
		- %(source)s: the source code of the function
	:type template: str
	:param reraise: If set to False, do not re-raise the exception, but only log it. default: True
	:type reraise: bool
	:param catchall: if True, also handle KeyboardInterrupt/SystemExit/GeneratorExit, i.e. log and only reraise if
	specified
	:type catchall: bool
	:param view_source: if True, include the source code of the failed function if possible
	:type view_source: bool
	:param line_numbers: if True, print line numbers in the source view
	:type line_numbers: bool
	'''
	if wrapped_f is not None:
		if catchall:
			# noinspection PyBroadException,PyDocstring
			def wrapper_f(*args, **kwargs):
				try:
					wrapped_f(*args, **kwargs)
				except:
					try:
						logf = logfunction() if lazy else logfunction
						frame = inspect.currentframe()
						if advanced:
							logf(template, wrapped_f, args, kwargs, frame,
								 view_source=view_source, line_numbers=line_numbers)
						else:
							logf(_generate_log_message(template, wrapped_f, args, kwargs, frame,
													   view_source=view_source, line_numbers=line_numbers))
						del frame
					except Exception:
						pass
					if reraise:
						raise
		else:
			# noinspection PyBroadException,PyDocstring
			def wrapper_f(*args, **kwargs):
				try:
					wrapped_f(*args, **kwargs)
				except Exception:
					try:
						logf = logfunction() if lazy else logfunction
						frame = inspect.currentframe()
						if advanced:
							logf(template, wrapped_f, args, kwargs, frame,
								 view_source=view_source, line_numbers=line_numbers)
						else:
							logf(_generate_log_message(template, wrapped_f, args, kwargs, frame,
													   view_source=view_source, line_numbers=line_numbers))
						del frame
					except Exception:
						pass
					if reraise:
						raise
		return functools.update_wrapper(wrapper_f, wrapped_f)
	else:
		# noinspection PyDocstring
		def arg_wrapper(wrapped_fn):
			return log(wrapped_fn,
					   logfunction=logfunction, lazy=lazy, advanced=advanced,
					   template=template, reraise=reraise, catchall=catchall, view_source=view_source)
		return arg_wrapper
