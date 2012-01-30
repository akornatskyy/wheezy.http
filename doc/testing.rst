
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


.. _`WSGI`: http://www.python.org/dev/peps/pep-3333
