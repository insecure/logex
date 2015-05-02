#!/usr/bin/python
# coding=utf-8
import os.path

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='logex',
    version='2.1.1',
    description='Easily log uncaught exceptions in D-Bus, thread and other functions.',
	url='https://github.com/insecure/logex',
	author='Tobias Hommel',
	author_email='software@genoetigt.de',
    long_description=read('README.rst'),
    py_modules=['logex'],
    include_package_data=True,
    license='BSD',
    keywords='debug log unhandled exception thread dbus D-Bus',
    # install_requires=[
    #     'six',
    # ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

