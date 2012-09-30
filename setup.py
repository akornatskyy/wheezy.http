#!/usr/bin/env python

import os

try:
    from setuptools import setup
except:
    from distutils.core import setup

README = open(os.path.join(os.path.dirname(__file__), 'README')).read()

setup(
    name='wheezy.http',
    version='0.1',
    description='A lightweight http request-response library',
    long_description=README,
    url='https://bitbucket.org/akorn/wheezy.http',

    author='Andriy Kornatskyy',
    author_email='andriy.kornatskyy at live.com',

    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing'
    ],
    keywords='wsgi http request response cache cachepolicy cookie '
               'functional middleware transforms',
    packages=['wheezy', 'wheezy.http'],
    package_dir={'': 'src'},
    namespace_packages=['wheezy'],

    zip_safe=False,
    install_requires=[
        'wheezy.core>=0.1.59'
    ],
    extras_require={
        'dev': [
            'wsgiref',
            'coverage',
            'nose',
            'pytest',
            'pytest-pep8',
            'pytest-cov',
            'mock'
        ]
    },

    platforms='any'
)
