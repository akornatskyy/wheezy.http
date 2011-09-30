.SILENT: clean env doc release test
.PHONY: clean env doc release test

VERSION=2.6
PYTHON=env/bin/python$(VERSION)
EASY_INSTALL=env/bin/easy_install-$(VERSION)
PYTEST=env/bin/py.test-$(VERSION)
NOSE=env/bin/nosetests-$(VERSION)
SPHINX=env/bin/sphinx-build

all: clean test release

debian:
	apt-get -yq update
	apt-get -yq dist-upgrade
	# How to Compile Python from Source
	# http://mindref.blogspot.com/2011/09/compile-python-from-source.html
	apt-get -yq install libbz2-dev build-essential python \
		python-dev python-setuptools python-virtualenv \
		mercurial libgmp10

env:
	PYTHON_EXE=/usr/local/bin/python$(VERSION); \
	if [ ! -x $$PYTHON_EXE ]; then \
		PYTHON_EXE=/usr/bin/python$(VERSION); \
	fi;\
	virtualenv --python=$$PYTHON_EXE \
		--no-site-packages env
	$(EASY_INSTALL) coverage docutils nose \
		pytest pytest-pep8 pytest-cov wsgiref
	if [ ! -e env/pycrypto.tgz ]; then \
		wget https://github.com/dlitz/pycrypto/tarball/py3k \
			-O env/pycrypto.tgz; \
	fi
	$(EASY_INSTALL) env/pycrypto.tgz

clean:
	find src/ -type d -name __pycache__ | xargs rm -rf
	find src/ -name '*.py[co]' -delete
	rm -rf dist/ build/ MANIFEST src/*.egg-info

release:
	$(PYTHON) setup.py -q bdist_egg

test:
	$(PYTEST) -q -x --pep8 --doctest-modules \
		src/wheezy/http

doctest-cover:
	$(NOSE) --stop --with-doctest --detailed-errors \
		--with-coverage --cover-package=wheezy.http,wheezy.http.crypto

test-cover:
	$(PYTEST) -q --cov wheezy.http \
		--cov-report term-missing \
		src/wheezy/http/tests

doc:
	$(SPHINX) -a -b html doc/ doc/_build/
