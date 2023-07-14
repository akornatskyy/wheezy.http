#!/usr/bin/env python

import multiprocessing
import os
import re

from setuptools import setup

extra = {}
try:
    from Cython.Build import cythonize

    p = os.path.join("src", "wheezy", "http")
    extra["ext_modules"] = cythonize(
        [os.path.join(p, "*.py")],
        exclude=os.path.join(p, "__init__.py"),
        # https://github.com/cython/cython/issues/3262
        nthreads=0 if multiprocessing.get_start_method() == "spawn" else 2,
        compiler_directives={"language_level": 3},
        quiet=True,
    )
except ImportError:
    pass

README = open(os.path.join(os.path.dirname(__file__), "README.md")).read()
VERSION = (
    re.search(
        r'__version__ = "(.+)"',
        open("src/wheezy/http/__init__.py").read(),
    )
    .group(1)
    .strip()
)

setup(
    name="wheezy.http",
    version=VERSION,
    python_requires=">=3.8",
    description="A lightweight http request-response library",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/akornatskyy/wheezy.http",
    author="Andriy Kornatskyy",
    author_email="andriy.kornatskyy@live.com",
    license="MIT",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    keywords="wsgi http request response cache cachepolicy cookie "
    "functional middleware transforms",
    packages=["wheezy", "wheezy.http"],
    package_dir={"": "src"},
    namespace_packages=["wheezy"],
    zip_safe=False,
    install_requires=["wheezy.core>=0.1.104"],
    platforms="any",
    **extra
)
