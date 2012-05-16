
Functional Testing
------------------
Functional testing is a type of black box testing. Functions are tested by
feeding them input and examining the output. Internal program structure
is rarely considered.

Let take a look at functional tests for :ref:`helloworld` application:

.. literalinclude:: ../demos/hello/test_helloworld.py
   :lines: 5-

:ref:`wheezy.http` comes with :py:class:`~wheezy.http.functional.WSGIClient`
that simulates calls to `WSGI`_ application.

While developing functional tests it is recommended distinguish three
primary actors:

* Page
* Functional Mixin
* Test Case

Let demo this idea in a scenario where we would like to test a signin process.

Page
~~~~
Page provides a number of asserts to prove the current content is related to
given page. Since this page will be used to submit signin information we need
find a form as well. Here is our signin page::

    class SignInPage(object):

        def __init__(self, client):
            assert '- Sign In</title>' in client.content
            assert AUTH_COOKIE not in client.cookies
            assert XSRF_NAME in client.cookies
            self.client = client
            self.form = client.form

        def signin(self, username, password):
            form = self.form
            form.username = username
            form.password = password
            self.client.submit(form)
            return self.client.form.errors()

We add as much asserts as necessary to prove this is signin page. We look at
title, check cookies and select form. ``signin`` method implements a simple
use case to initialize form with parameters passed, submit form and return
any errors found back.

Functional Mixin
~~~~~~~~~~~~~~~~
Functional mixin is more high level actor. While considered to be developed as
mixin, your actual test case can combine them as much as necessary to fulfill
its goal. Here is a singin mixin::

    class SignInMixin(object):

        def signin(self, username, password):
            client = self.client
            assert 200 == client.get('/en/signin')
            page = SignInPage(client)
            return page.signin(username, password)

It is up to functional mixin to implement particular use case. However it is recommended that its method represent operation particular to given domain,
abstracting details like url, form, etc.

Test Case
~~~~~~~~~
While page and functional mixin plays distinct simple role, test case tries
to get as much as possible to accomplish a number of use cases. Here is a
test case::

    class SignInTestCase(unittest.TestCase, SignInMixin):

        def setUp(self):
            self.client = WSGIClient(main)

        def tearDown(self):
            del self.client
            self.client = None

        def test_validation_error(self):
            """ Ensure sigin page displays field validation errors.
            """
            errors = self.signin('', '')
            assert 2 == len(errors)
            assert AUTH_COOKIE not in self.client.cookies

        def test_valid_user(self):
            """ Ensure sigin is successful.
            """
            self.signin('demo', 'P@ssw0rd')
            assert 200 == self.client.follow()
            assert AUTH_COOKIE in self.client.cookies
            assert XSRF_NAME not in self.client.cookies
            assert 'Welcome <b>demo' in self.client.content

Test case can use many functional mixins to accomplish its goal. Test case in
general is a set of conditions under which we can determine whether an
application is working correctly or not. The mechanism for determining
whether a software program has passed or failed such a test is known as a
test oracle. In some settings, an oracle could be a requirement or use case,
while in others it could be a heuristic. It may take many test cases to
determine that a software program or system is considered sufficiently
scrutinized to be released. Being able combine and reuse test case building
blocks is crucial.

Benchmark
~~~~~~~~~

You can benchmark your test cases with ``wheezy.core.benchmark.Benchmark``.
Here is an example::

    """ ``benchmark_views`` module.
    """

    from wheezy.core.benchmark import Benchmark

    from public.web.tests.test_views import PublicTestCase


    class BenchmarkTestCase(PublicTestCase):

        def runTest(self):
            """ Perform bachmark and print results.
            """
            p = Benchmark((
                self.test_home,
                self.test_about,
                self.test_static_files,
                self.test_static_file_not_found,
                self.test_static_file_forbidden,
                self.test_static_file_gzip,
                self.test_head_static_file
                ), 1000)
            p.report('public', baselines={
                    'test_home': 1.0,
                    'test_about': 0.926,
                    'test_static_files': 1.655,
                    'test_static_file_not_found': 0.64,
                    'test_static_file_forbidden': 0.62,
                    'test_static_file_gzip': 8.91,
                    'test_head_static_file': 9.08
            })

Report
^^^^^^

Sample output::

    public: 7 x 1000
    baseline throughput change target
      100.0%     839rps  +0.0% test_home
       96.2%     807rps  +3.9% test_about
      235.7%    1979rps +42.4% test_static_files
       72.4%     608rps +13.1% test_static_file_not_found
       72.3%     607rps +16.6% test_static_file_forbidden
     1141.4%    9585rps +28.1% test_static_file_gzip
     1193.6%   10023rps +31.5% test_head_static_file

Each of seven test cases has been run 1000 times. It shows productivity gain
from first test case (it serves baseline purpose for others), throughput
in requests per second, change from ``baselines`` argument passed to
``report`` method and targeted being benchmarked.

Report is being printed as results available.

Organizing Benchmarks
^^^^^^^^^^^^^^^^^^^^^

It is recommended keep benchmark test separately from others tests in
files with prefix ``benchmark``, e.g. ``benchmark_views.py``. This way
can be run separately. Here is an example how to run only benchmark
tests with ``nose``::

    $ nosetests-2.7 -qs -m benchmark src/

This method of benchmarking does not involve web server layer, nor http
traffic, instead it gives you idea how performance of your handlers
evolve over time.

Profiling
^^^^^^^^^

Since benchmark does certain workload on your application that workload
is a good start point for profiling your code as well as analyzing
productivity bottlenecks.

Here we are running profiling::

    $ nosetests-2.7 -qs -m benchmark --with-profile \
                --profile-stats-file=profile.pstats src/

Profiling results can be further analyzed with::

    gprof2dot.py -f pstats profile.pstats | dot -Tpng -o profile.png

Profiling your application let determine performance critical places that
might require further optimization.

Performance
^^^^^^^^^^^
You can boost :py:class:`~wheezy.http.functional.WSGIClient` form
parsing performance by installing `lxml`_ package. It tries to use
``HTMLParser`` from ``lxml.etree`` package and if it is not available
fallback to the standard library default one.

.. _`WSGI`: http://www.python.org/dev/peps/pep-3333
.. _`lxml`: http://lxml.de/parsing.html
