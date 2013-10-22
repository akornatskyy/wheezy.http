
Examples
========

We start with a simple helloworld example. Before we proceed with examples
let's setup a `virtualenv`_ environment::

    $ virtualenv env
    $ env/bin/easy_install wheezy.http


.. _helloworld:

Hello World
-----------

`helloworld.py`_ shows you how to use :ref:`wheezy.http` in a pretty
simple `WSGI`_ application:

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 5-

Let have a look through each line in this application.

Request Handler
~~~~~~~~~~~~~~~

First of all let's take a look what is request handler:

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 11-14

It is a simple callable of form::

    def handler(request):
        return response

In :ref:`wheezy.http` there are no dependencies between
:py:class:`~wheezy.http.request.HTTPRequest` and
:py:class:`~wheezy.http.response.HTTPResponse`.

While :ref:`wheezy.http` doesn't prescribe what is a router, we add
here a simple router middleware. This way you can use one of available
alternatives to provide route matching for your application.

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 17-23

There is a  separate python package `wheezy.routing`_ that is recommended
way to add routing facility to your application.

Finally we create the entry point that is an instance of
:py:class:`~wheezy.http.application.WSGIApplication`.

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 26-30

The rest in the ``helloworld`` application launches a simple wsgi server.
Try it by running::

    $ python helloworld.py

Visit http://localhost:8080/.

.. _guestbook:

Guest Book
-----------
TODO

.. _`virtualenv`: http://pypi.python.org/pypi/virtualenv
.. _`helloworld.py`: https://bitbucket.org/akorn/wheezy.http/src/tip/demos/hello/helloworld.py
.. _`WSGI`: http://www.python.org/dev/peps/pep-3333
.. _`wheezy.routing`: http://pypi.python.org/pypi/wheezy.routing
