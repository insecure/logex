#!/usr/bin/python
# coding=utf-8
import os.path

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='logex',
    version='1.0.0',
    description='Easily log uncaught exceptions in any kind of function.',
    url='https://github.com/',
    long_description=read('README.rst'),
    py_modules=['logex'],
    include_package_data=True,
    license='BSD',
    keywords='log unhandled exception thread dbus',
    # install_requires=[
    #     'six',
    # ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        # 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

