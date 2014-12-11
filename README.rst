logex
=====

A python module to easily add logging for unhandled exceptions in D-Bus, thread
and other functions.
Although unhandled exceptions get written to STDERR by default and most modules
provide some mechanism to log these, this is not always sufficient, e.g. when
inside a daemon which discards all default output.
Sometimes it may also be desirable to automatically send an email if some
exception occurs or at least write some kind of audit log.

It comes with a decorator function which can be applied on demand. It provides
advanced debugging information which gives you the most relevant information
for each frame in the exception's traceback.

Well, the most simple usage would be:

.. code:: python
 #!/usr/bin/python
 import logex

 @logex.log
 def my_function():
     raise Exception("something bad happens here")

 my_function()

Running this code will result in something like the following output::

 ERROR:root:Unhandled exception calling my_function():
 Traceback (most recent call last):
   File "./x.py", line 7, in my_function
     raise Exception("something bad happens here")
 Exception: something bad happens here
 
 
 Traceback (most recent call last):
   File "./x.py", line 9, in <module>
     my_function()
   File "/home/tobi/repos/logex/logex.py", line 308, in wrapper_f
     template, view_source, reraise, wrapper_code=wrapper_code)
   File "/home/tobi/repos/logex/logex.py", line 301, in wrapper_f
     wrapped_f(*args, **kwargs)
   File "./x.py", line 7, in my_function
     raise Exception("something bad happens here")
 Exception: something bad happens here

...
TODO: write some more important information...
