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
import sys

__version__ = '2.0.0'

LOGFUNCTION = logging.error
TEMPLATE = ('Unhandled exception calling %(funcname)s(%(argsview)s):\n'
			'%(traceback)s\n'
			'%(sourceview)s')
ADVANCED = False
LAZY = False
RERAISE = True
CATCHALL = False
VIEW_SOURCE = False

def _generate_source_view(tb):
	source_view = ['========== sourcecode ==========']
	while tb is not None:
		crashed_frame = tb.tb_frame
		crashed_line = crashed_frame.f_lineno
		try:
			filename = inspect.getsourcefile(crashed_frame)
		except TypeError:
			filename = '<UNKNOWN>'
		crashed_name = crashed_frame.f_code.co_name
		file_header = '-- %s: %s --' % (filename, crashed_name)
		frame_line = '-'*len(file_header)
		source_view.append(frame_line)
		source_view.append(file_header)
		source_view.append(frame_line)
		try:
			sourcelines, lineno = inspect.getsourcelines(crashed_frame)
			del crashed_frame
		except IOError:
			sourcelines = []
			lineno = -1
		number_len = len(str(lineno+len(sourcelines)))
		last = False
		for number, line in enumerate(sourcelines, lineno):
			if number == crashed_line:
				source_view.append('%*s-->%s' % (number_len, number, line[:-1]))
				last = True
			else:
				if last:
					source_view.append('...')
					break
				source_view.append('%*s   %s' % (number_len, number, line[:-1]))
		source_view.append('')
		locals_view = _generate_locals_view(tb.tb_frame)
		if locals_view != '':
			source_view.extend(['Locals when executing line %s:' % crashed_line, locals_view, ''])
		tb = tb.tb_next
	source_view.append('='*len(source_view[0]))
	return '\n'.join(source_view)

def _generate_locals_view(frame):
	arginfo = inspect.getargvalues(frame)
	frame_locals = ['* %s: %r' % item for item in sorted(arginfo.locals.items())]
	return '\n'.join(frame_locals)

def _generate_args_view(args, kwargs):
	view = ', '.join([repr(arg) for arg in args])
	if kwargs != {}:
		view += ', ' + ', '.join(['%s=%r' % (k, v) for k, v in kwargs.items()])
	return view


def is_method_of(func_code, some_object):
	attr = getattr(some_object, func_code.co_name, None)
	if attr is None:
		return False
	else:
		return inspect.ismethod(attr)

def _generate_log_message(template, args, kwargs, exc, view_source=VIEW_SOURCE):
	type_, value_, tb_ = exc
	func_code = tb_.tb_frame.f_code
	func_name = func_code.co_name
	if view_source:
		try:
			source = _generate_source_view(tb_)
		except Exception:
			source = 'Error generating source view:\n%s' % traceback.format_exc()
	else:
		source = ''
	if is_method_of(func_code, args[0]):
		func_name = '%s.%s' % (args[0].__class__.__name__, func_name)
		argsview = _generate_args_view(args[1:], kwargs)
	else:
		argsview = _generate_args_view(args, kwargs)
	return template % {
		'traceback': ''.join(traceback.format_exception(type_, value_, tb_)),
		'funcname': func_name,
		'args': args,
		'kwargs': kwargs,
		'argsview': argsview,
		'sourceview': source
	}

def _handle_log_exception(args, kwargs, logfunction, lazy, advanced, template, view_source, reraise, strip=1):
	# noinspection PyBroadException
	try:
		logf = logfunction() if lazy else logfunction
		type_, value_, tb_ = sys.exc_info()
		for i in range(strip):
			if tb_.tb_next is None:
				break
			tb_ = tb_.tb_next
		if advanced:
			logf(template, args, kwargs, (type_, value_, tb_),
				 view_source=view_source)
		else:
			logf(_generate_log_message(
				template, args, kwargs, (type_, value_, tb_),
				view_source=view_source))
	except Exception:
		traceback.print_exc()
		pass #TODO: any sane way to report this? logging/print is not generic enough
	if reraise:
		# noinspection PyCompatibility
		raise

#TODO: document parameters to logfunction
def log(wrapped_f=None, logfunction=LOGFUNCTION, lazy=LAZY, advanced=ADVANCED,
		template=TEMPLATE, reraise=RERAISE, catchall=CATCHALL,
		view_source=VIEW_SOURCE):
	'''Decorator function that logs all unhandled exceptions in a function.
	This is especially useful for thread functions in a daemon or functions which are used as D-Bus signal handlers.

	:param wrapped_f: the decorated function(ignore when using @-syntax)
	:param logfunction: the logging function or a function returning a logging function (depending on `lazy` parameter)
	:type logfunction: function
	:param lazy: if True, `function` returns the actual logging function
	:type lazy: bool
	:param advanced: if True, pass the details to `function`, if False only pass the generated message to `function`
	:type advanced: bool
	:param template: If `advanced` is False, the message to be logged. The following place holders will be replaced:
		- %(traceback)s: the traceback to the exception
		- %(funcname)s: the name of the function in which the exception occurred
		- %(args)s: the arguments to the function
		- %(kwargs)s: the keyword arguments to the function
		- %(argsview)s: args and kwargs in one line, separated by ', ' and kwargs in key=value form
		- %(sourceview)s: the source code of the function
	:type template: str
	:param reraise: If set to False, do not re-raise the exception, but only log it. default: True
	:type reraise: bool
	:param catchall: if True, also handle KeyboardInterrupt/SystemExit/GeneratorExit, i.e. log and only reraise if
	specified
	:type catchall: bool
	:param view_source: if True, include the source code of the failed function if possible
	:type view_source: bool
	'''
	if wrapped_f is not None:
		if catchall:
			# noinspection PyBroadException,PyDocstring
			def wrapper_f(*args, **kwargs):
				try:
					wrapped_f(*args, **kwargs)
				except:
					_handle_log_exception(args, kwargs, logfunction, lazy, advanced, template, view_source, reraise)
		else:
			# noinspection PyBroadException,PyDocstring
			def wrapper_f(*args, **kwargs):
				try:
					wrapped_f(*args, **kwargs)
				except Exception:
					_handle_log_exception(args, kwargs, logfunction, lazy, advanced, template, view_source, reraise)
		return functools.update_wrapper(wrapper_f, wrapped_f)
	else:
		# noinspection PyDocstring
		def arg_wrapper(wrapped_fn):
			return log(wrapped_fn,
					   logfunction=logfunction, lazy=lazy, advanced=advanced,
					   template=template, reraise=reraise, catchall=catchall,
					   view_source=view_source)
		return arg_wrapper
