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

__version__ = '2.1.1'

LOGFUNCTION = logging.error
TEMPLATE = ('Unhandled exception calling %(funcname)s(%(argsview)s):\n'
			'%(traceback)s\n'
			'%(sourceview)s')
ADVANCED = False
LAZY = False
RERAISE = True
CATCHALL = False
VIEW_SOURCE = False
DETECT_NESTED = True

_logger = logging.getLogger('logex')


def _get_next_code_name(tb, wrapper_code):
	while tb is not None:
		if tb.tb_frame.f_code is wrapper_code:
			tb = tb.tb_next
		else:
			return tb.tb_frame.f_code.co_name
	return '<unknown>'

def _generate_source_view(tb, wrapper_code):
	"""Generate a view showing the source code for all frames in a given traceback.
	The view contains the following information for every frame in the traceback:
	 * the name of the current function
	 * the file name containing the source code of the current function
	 * the source code of the current function (the source code is only shown up to the current line)
	 * line numbers
	 * an indicator "-->" for the current line of the frame
	 * a list of locals

	:param tb: a traceback object (e.g. from sys.exc_info()[2])
	:type tb: types.TracebackType
	:param wrapper_code: the code object of the wrapper function, used to detect nested logex calls if not None
	:param wrapper_code: types.CodeType or None
	:rtype: str
	"""
	source_view = ['========== sourcecode ==========']
	while tb is not None:
		crashed_frame = tb.tb_frame
		if wrapper_code is not None:
			if tb.tb_frame.f_code is wrapper_code:
				next_code_name = _get_next_code_name(tb, wrapper_code)
				source_view.extend(['-------------------------------------------------------',
									'-- detected nested logex calls, see previous message --',
									'-- for call to %-37.37s --' % (next_code_name+'()'),
									'-------------------------------------------------------'])
				break
		crashed_line = crashed_frame.f_lineno
		try:
			filename = inspect.getsourcefile(crashed_frame)
		except TypeError:
			filename = '<UNKNOWN>'
		file_header = '-- %s: %s --' % (filename, crashed_frame.f_code.co_name)
		frame_line = '-'*len(file_header)
		source_view.extend([frame_line,
							file_header,
							frame_line])
		try:
			sourcelines, lineno = inspect.getsourcelines(crashed_frame)
			del crashed_frame
		except IOError:
			sourcelines = []
			lineno = -1
		last = False
		for number, line in enumerate(sourcelines, lineno):
			if number == crashed_line:
				source_view.append('%5s-->%s' % (number, line[:-1]))
				last = True
			else:
				if last:
					source_view.append('...')
					break
				source_view.append('%5s   %s' % (number, line[:-1]))
		source_view.append('')
		locals_view = _generate_locals_view(tb.tb_frame)
		if locals_view != '':
			source_view.extend(['Locals when executing line %s:' % crashed_line, locals_view, ''])
		tb = tb.tb_next
	source_view.append('='*len(source_view[0]))
	return '\n'.join(source_view)

def _generate_locals_view(frame):
	arginfo = inspect.getargvalues(frame)
	frame_locals = []
	for item in sorted(arginfo.locals.items()):
		try:
			frame_locals.append('* %s: %r' % item)
		except Exception:
			frame_locals.append('* !!! could not get information for local at 0x%x !!!' % id(item))
	return '\n'.join(frame_locals)

def _generate_args_view(args, kwargs):
	"""Generate a string representing the arguments given.
	All arguments and keyword arguments are separated by ", ".
	All keyword arguments are in the form name=value.

	:param args: a tuple containing the arguments
	:type args: tuple
	:param kwargs: a dict containing key/value pairs for all keyword arguments
	:type kwargs: dict
	:rtype: str
	"""
	view = ', '.join([repr(arg) for arg in args])
	if kwargs != {}:
		view += ', ' + ', '.join(['%s=%r' % (k, v) for k, v in kwargs.items()])
	return view

def _is_method_of(func_name, class_object):
	"""Check if a given class object has a method of a given name.

	:param func_name: the name of the method to be checked for
	:param class_object: the instance of the class
	:rtype: bool
	"""
	attr = getattr(class_object, func_name, None)
	if attr is None:
		return False
	else:
		return inspect.ismethod(attr)

def generate_log_message(template, args, kwargs, exc, wrapper_code=None, view_source=None):
	"""Generate a message based on a given template.

	:param template: a template for the returned message, the following place holders will be replaced:
		- %(traceback)s: the traceback to the exception
		- %(funcname)s: the name of the function in which the exception occurred
		- %(args)s: the arguments to the function
		- %(kwargs)s: the keyword arguments to the function
		- %(argsview)s: args and kwargs in one line, separated by ', ' and kwargs in key=value form
		- %(sourceview)s: the source code of the function
	:type template: str
	:param args: the arguments to the top function of the traceback
	:type args: tuple
	:param kwargs: the keyword arguments to the top function of the traceback
	:type kwargs: dict
	:param exc: a (type, value, traceback) tuple as returned by sys.exc_info()
	:param wrapper_code: the code object of the wrapper function, used to detect nested logex calls if not None
	:param wrapper_code: types.CodeType or None
	:param view_source: if True, add a view for the source code of every relevant function in the exception traceback
	:type view_source: bool
	:rtype: str
	"""
	if view_source is None:
		view_source = VIEW_SOURCE
	type_, value_, tb_ = exc
	func_name = tb_.tb_frame.f_code.co_name
	if view_source:
		try:
			source = _generate_source_view(tb_, wrapper_code=wrapper_code)
		except Exception:
			source = 'Error generating source view:\n%s' % traceback.format_exc()
	else:
		source = ''
	if len(args) > 0 and _is_method_of(func_name, args[0]):
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

def _handle_log_exception(args, kwargs, logfunction, lazy, advanced,
						  template, view_source, reraise,
						  wrapper_code=None, strip=1, exc=None):
	# noinspection PyBroadException
	try:
		logf = logfunction() if lazy else logfunction
		if exc is None:
			type_, value_, tb_ = sys.exc_info()
		else:
			type_, value_, tb_ = exc
		for i in range(strip):
			if tb_.tb_next is None:
				break
			tb_ = tb_.tb_next
		if advanced:
			logf(template, args, kwargs, (type_, value_, tb_), wrapper_code=wrapper_code,
				 view_source=view_source)
		else:
			message = generate_log_message(
				template, args, kwargs, (type_, value_, tb_), wrapper_code=wrapper_code,
				view_source=view_source)
			logf(message)
	except Exception:
		logging.basicConfig()
		_logger.exception('Error while generating log message for unhandled exception:')
	finally:
		try:
				# noinspection PyUnboundLocalVariable
				del tb_
		except NameError:
			pass
	if reraise:
		# noinspection PyCompatibility
		raise

def log(wrapped_f=None, logfunction=None, lazy=None, advanced=None, template=None,
		reraise=None, catchall=None, view_source=None, detect_nested=None):
	"""Decorator function that logs all unhandled exceptions in a function.
	This is especially useful for thread functions in a daemon or functions which are used as D-Bus signal handlers.

	:param wrapped_f: The decorated function(ignore when using @-syntax).
	:param logfunction: The logging function or a function returning a logging function (depending on `lazy` parameter).
	The parameters given to this function depend on the `advanced` parameter.
	If `advanced` is False, a string with a message string is passed.
	If `advanced` is True, the same parameters as for `generate_log_mesage` are passed.
	:type logfunction: function
	:param lazy: if True, `function` returns the actual logging function
	:type lazy: bool
	:param advanced: if True, pass the details to `function`, if False only pass the generated message to `function`
	:type advanced: bool
	:param template: If `advanced` is False, the message to be logged. See `generate_log_message` for a list of place
	holders that are replaced.
	:type template: str
	:param reraise: If set to False, do not re-raise the exception, but only log it. This does not resume the function!
	:type reraise: bool
	:param catchall: if True, also handle KeyboardInterrupt/SystemExit/GeneratorExit, i.e. log and only reraise if
	specified
	:type catchall: bool
	:param view_source: if True, include the source code of the failed function if possible
	:type view_source: bool
	:param detect_nested: if False, do not try to detect wrapped logex calls, i.e. if a method decorated by this
	function calls another method decorated by this function
	:type detect_nested: bool
	"""
	if logfunction is None: logfunction = LOGFUNCTION
	if lazy is None: lazy = LAZY
	if advanced is None: advanced = ADVANCED
	if template is None: template = TEMPLATE
	if reraise is None: reraise = RERAISE
	if catchall is None: catchall = CATCHALL
	if view_source is None: view_source = VIEW_SOURCE
	if detect_nested is None: detect_nested = DETECT_NESTED
	if wrapped_f is not None:
		if catchall:
			# noinspection PyBroadException,PyDocstring
			def wrapper_f(*args, **kwargs):
				try:
					return wrapped_f(*args, **kwargs)
				except:
					if detect_nested:
						try:
							# noinspection PyUnresolvedReferences
							wrapper_code = wrapper_f.func_code
						except AttributeError:
							# noinspection PyUnresolvedReferences
							wrapper_code = wrapper_f.__code__
					else:
						wrapper_code = None
					_handle_log_exception(args, kwargs, logfunction, lazy, advanced,
										  template, view_source, reraise, wrapper_code=wrapper_code)
		else:
			# noinspection PyBroadException,PyDocstring
			def wrapper_f(*args, **kwargs):
				try:
					return wrapped_f(*args, **kwargs)
				except Exception:
					if detect_nested:
						try:
							# noinspection PyUnresolvedReferences
							wrapper_code = wrapper_f.func_code
						except AttributeError:
							# noinspection PyUnresolvedReferences
							wrapper_code = wrapper_f.__code__
					else:
						wrapper_code = None
					_handle_log_exception(args, kwargs, logfunction, lazy, advanced,
										  template, view_source, reraise, wrapper_code=wrapper_code)
		return functools.update_wrapper(wrapper_f, wrapped_f)
	else:
		# noinspection PyDocstring
		def arg_wrapper(wrapped_fn):
			return log(wrapped_fn,
					   logfunction=logfunction, lazy=lazy, advanced=advanced,
					   template=template, reraise=reraise, catchall=catchall,
					   view_source=view_source, detect_nested=detect_nested)
		return arg_wrapper

def excepthook(type_, value_, traceback_):
	"""A wrapper that can be used as sys.excepthook."""
	_handle_log_exception((), {}, LOGFUNCTION, LAZY, ADVANCED,
							TEMPLATE, VIEW_SOURCE, False,
							exc=(type_, value_, traceback_))

def install_excepthook():
	"""Set the global excepthook which is called if an unhandled exception is raised in the main thread."""
	sys.excepthook = excepthook

def uninstall_excepthook():
	"""Restore the original excepthook."""
	sys.excepthook = sys.__excepthook__
