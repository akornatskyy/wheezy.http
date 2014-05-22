
User Guide
==========

:ref:`wheezy.http` is a lightweight `WSGI`_ library that aims to take most
benefits out of standard python library. It can be run from python 2.4 up
to most cutting age python 3.

Configuration Options
---------------------
Configuration options is a python dictionary passed to
:py:class:`~wheezy.http.application.WSGIApplication` during initialization.
These options are shared across various parts of application, including:
middleware factory, http request, cookies, etc.

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 26-30

There are no required options necessarily setup before use, since they
all fallback to some defaults defined in the :py:mod:`~wheezy.http.config` module.
Actually ``options`` are checked by the
:py:meth:`~wheezy.http.config.bootstrap_http_defaults` middleware factory
for missing values (the middleware factory is executed only once at
application start up).

See full list of available options in :py:mod:`~wheezy.http.config` module.

WSGI Application
----------------
`WSGI`_ is the Web Server Gateway Interface. It is a specification for
web/application servers to communicate with web applications. It is a
Python standard, described in detail in PEP 3333.

An instance of :py:class:`~wheezy.http.application.WSGIApplication` is
an entry point of your `WSGI`_ application. You instantiate it by supplying
a list of desired ``middleware factories`` and global configuration
``options``. Here is a snippet from :ref:`helloworld` example:

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 26-30

An instance of :py:class:`~wheezy.http.application.WSGIApplication` is
a callable that responds to the standard `WSGI`_ call. This callable is passed to
application/web server. Here is an integration example with the
web server from python standard ``wsgiref`` package:

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 35-42

The integration with other `WSGI`_ application servers varies. However the
principal of `WSGI`_ entry point is the same across those implementations.

Middleware
----------

The presence of middleware, in general, is transparent to the application
and requires no special support. Middleware is usually characterized by
playing the following roles within an application:

* It is singleton, there is only one instance per application.
* It is sort of interceptor of incoming request to handler.
* They can be chained so one pass request to following as well as capable
  to inspect response, override it, extend or modify as necessary.
* It capable to supply additional information in request context.

Middleware can be any callable of the following form::

    def middleware(request, following):
        if following is not None:
            response = following(request)
        else:
            response = ...
        return response

A middleware callable accepts as a first argument an instance of
:py:class:`~wheezy.http.request.HTTPRequest` and as second argument (``following``) the next middleware in the
chain. It is up to middleware to decide whether
to call the next middleware callable in the chain. It is expected that middleware
returns an instance of :py:class:`~wheezy.http.response.HTTPResponse` class or
``None``.

Middleware Factory
~~~~~~~~~~~~~~~~~~

Usually middleware requires some sort of initialization before being used.
This can be some configuration variables or sort of preparation, verification,
etc. ``Middleware Factory`` serves this purpose.

Middleware factory can be any callable of the following form::

    def middleware_factory(options):
        return middleware

Middleware factory is initialized with configuration ``options``, it is the
same dictionary used during
:py:class:`~wheezy.http.application.WSGIApplication`
initialization. Middleware factory returns particular middleware implementation
or ``None`` (this can be useful for some sort of initialization that needs
to be run during application bootstrap, e.g. some defaults, see
:py:meth:`~wheezy.http.config.bootstrap_http_defaults`).

In case the last middleware in the chain returns ``None`` it is equivalent
to returning HTTP response not found (HTTP status code 404).

Execution Order
~~~~~~~~~~~~~~~

Middleware is initialized and executed in certain order. Let's setup a simple
application with the following middleware chain::

    app = WSGIApplication(middleware=[
        a_factory,
        b_factory,
        c_factory
    ])

Initialization and execution order is the same - from first element in the
list to the last::

    a_factory => b_factory => c_factory

In case a factory returns ``None`` it is being skipped from middleware list.
Let assume ``b_factory`` returns ``None``, so the middleware chain become::

    a => c

It is up to middleware ``a`` to call ``c`` before or after its own
processing. :py:class:`~wheezy.http.application.WSGIApplication` in no way
prescribes it, instead it just chains them. This gives great power to the middleware
developer to take control over certain implementation use case.

HTTP Handler
------------

Handler is any callable that accepts an instance of
:py:class:`~wheezy.http.request.HTTPRequest` and returns
:py:class:`~wheezy.http.response.HTTPResponse`::

    def handler(request):
        return response

Here is an example:

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 11-14

:ref:`wheezy.http` does not provide HTTP handler implementations (see
`wheezy.web`_ for this purpose).

@accept_method
~~~~~~~~~~~~~~

Decorator :py:class:`~wheezy.http.method.accept_method` accepts only
particular HTTP request method if its argument (``constraint``) is a string::

    @accept_method('GET')
    def my_view(request):
        ...

or one of multiple HTTP request methods if the argument (``constraint``) is a list or tuple::

    @accept_method(('GET', 'POST'))
    def my_view(request):
        ...

Method argument constraint must be in uppercase.

Respond with an HTTP status code 405 (Method Not Allowed) in case incoming HTTP
request method does not match decorator constraint.

@secure
~~~~~~~

Decorator :py:class:`~wheezy.http.authorization.secure` accepts only secure
requests (those that are communication via SSL)::

    @secure
    def my_view(request):
        ...

Its behavior can be controlled via ``enabled`` (in case it is
``False`` no checks are performed, defaults to ``True``).


HTTP Request
------------
:py:class:`~wheezy.http.request.HTTPRequest` is a wrapper around WSGI environ
dictionary. It provides access to all variables stored within the environ as well
as provide several handy methods for daily use.

:py:class:`~wheezy.http.request.HTTPRequest` includes the following useful
attributes (they are evaluated only once during processing):

* ``method`` - request method (GET, POST, HEAD, etc)
* ``host`` - request host; depends on WSGI variable ``HTTP_HOST``.
* ``remote_addr`` - remote address; depends on WSGI variable ``REMOTE_ADDR``.
* ``root_path`` - application virtual path; environ ``SCRIPT_NAME``
  plus ``/``.
* ``path`` - request url path; environ ``SCRIPT_NAME`` plus ``PATH_INFO``.
* ``query`` - request url query; data are returned as a dictionary. The
  dictionary keys are the unique query variable names and the values are
  lists of values for each name.
* ``form`` - request form; data are returned as a dictionary. The dictionary
  keys are the unique form variable names and the values are lists of values
  for each name. Supports the following mime types:
  ``application/x-www-form-urlencoded``, ``application/json`` and
  ``multipart/form-data``.
* ``files`` - request form files; data are returned as a dictionary. The
  dictionary keys are the unique file variable names and the values are lists
  of files (``cgi.FieldStorage``) for each name.
* ``cookies`` - cookies passed by browser; an instance of ``dict``.
* ``ajax`` - returns ``True`` if current request is AJAX request.
* ``secure`` - determines whether the current request was made via SSL
  connection; depends on WSGI variable ``wsgi.url_scheme``.
* ``scheme`` - request url scheme (``http`` or ``https``); depends on
  WSGI variable ``wsgi.url_scheme``.
* ``urlparts`` - returns a tuple of 5, corresponding to request url: scheme,
  host, path, query and fragment (always ``None``).
* ``content_type`` - returns the MIME content type of the incoming request.
* ``content_length`` - returns the length, in bytes, of content sent by
  the client.
* ``stream`` - returns the contents of the incoming HTTP entity body.

Form and Query
~~~~~~~~~~~~~~

While working with request form/query you get a dictionary. The dictionary
keys are the unique form variable names and the values are lists of values
for each name. There usually exists just one value, so working with list is
not that convenient. You can use ``first_item_adapter`` or
``last_item_adapter`` (see `wheezy.core`_)::

    >>> from wheezy.core.collections import last_item_adapter
    ...
    >>> request.query['a']
    ['1', '2']
    >>> query = last_item_adapter(request.query)
    >>> query['a']
    '2'

While you are able initialize your application models by requesting
certain values from ``form`` or ``query``, there is a separate python
package `wheezy.validation`_ that is recommended way to add forms
facility to your application. It includes both model binding as well
as a number of validation rules.

Supported content types: *application/x-www-form-urlencoded*,
*application/json* and *multipart/form-data*.

HTTP Response
-------------
:py:class:`~wheezy.http.response.HTTPResponse` correctly maps the following
HTTP response status codes (according to `rfc2616`_):

.. literalinclude:: ../src/wheezy/http/response.py
   :lines: 8-57

Content Type and Encoding
~~~~~~~~~~~~~~~~~~~~~~~~~

You instantiate :py:class:`~wheezy.http.response.HTTPResponse` and initialize
it with ``content_type`` and ``encoding``::

    >>> r = HTTPResponse()
    >>> r.headers
    [('Content-Type', 'text/html; charset=UTF-8')]
    >>> r = HTTPResponse(content_type='image/gif')
    >>> r.headers
    [('Content-Type', 'image/gif')]

    >>> r = HTTPResponse(content_type='text/plain; charset=iso-8859-4',
    ...             encoding='iso-8859-4')
    >>> r.headers
    [('Content-Type', 'text/plain; charset=iso-8859-4')]

Buffered Output
~~~~~~~~~~~~~~~

:py:class:`~wheezy.http.response.HTTPResponse` has two methods to buffer
output: ``write`` and ``write_bytes``.

Method ``write`` let you buffer response before it actually being
passed to application server. The ``write`` method does encoding of input
chunk to bytes accordingly to response encoding.

Method ``write_bytes`` buffers output bytes.

Other Members
~~~~~~~~~~~~~

Here are some attributes available in
:py:class:`~wheezy.http.response.HTTPResponse`:

* ``cache`` - setup :py:class:`~wheezy.http.cachepolicy.HTTPCachePolicy`.
  Defaults to ``private`` cache policy.
* ``cache_dependency`` - a list of keys; used to setup dependency for given
  request thus effectively invalidating cached response depending on some
  application logic. It is a hook for integration with `wheezy.caching`_.
* ``headers`` - list of headers to be returned to browser; the header must
  be a tuple of two: ``(name, value)``. No checks for duplicates.
* ``cookies`` - list of cookies to set in response. This list contains
  :py:class:`~wheezy.http.cookie.HTTPCookie` objects.

Redirect Responses
~~~~~~~~~~~~~~~~~~

There are a number of handy preset redirect responses:

* :py:meth:`~wheezy.http.response.permanent_redirect` - returns permanent
  redirect response. The HTTP response status ``301 Moved Permanently``
  is used for permanent redirection.
* :py:meth:`~wheezy.http.response.redirect`,
  :py:meth:`~wheezy.http.response.found` - returns redirect response.
  The HTTP response status ``302 Found`` is a common way of performing a
  redirection.
* :py:meth:`~wheezy.http.response.see_other` - returns see other redirect
  response. The HTTP response status ``303 See Other`` is the correct manner
  in which to redirect web applications to a new URI, particularly after
  an HTTP POST has been performed. This response indicates that the correct
  response can be found under a different URI and should be retrieved
  using a GET method. The specified URI is not a substitute reference for
  the original resource.
* :py:meth:`~wheezy.http.response.temporary_redirect` - returns temporary
  redirect response. In this occasion, the request should be repeated with
  another URI, but future requests can still use the original URI.
  In contrast to 303, the request method should not be changed when reissuing
  the original request. For instance, a POST request must be repeated using
  another POST request.

AJAX Redirect
~~~~~~~~~~~~~

Browsers incorrectly handle redirect response to AJAX requests, so there is
used status code 207 that javascript is capable to receive and process
browser redirect.

* :py:meth:`~wheezy.http.response.ajax_redirect` - returns ajax redirect
  response.

Here is an example for jQuery::

    $.ajax({
        // ...
        success: function(data, textStatus, jqXHR) {
            if (jqXHR.status == 207) {
                window.location.replace(
                    jqXHR.getResponseHeader('Location'));
            } else {
                // ...
            }
        }
    });

If AJAX response status code is 207, browser navigates to URL specified
in HTTP response header ``Location``.

Error Responses
~~~~~~~~~~~~~~~

There are a number of handy preset client error responses:

* :py:meth:`~wheezy.http.response.bad_request`,
  :py:meth:`~wheezy.http.response.error400` - the request cannot be fulfilled
  due to bad syntax.
* :py:meth:`~wheezy.http.response.unauthorized`,
  :py:meth:`~wheezy.http.response.error401` - similar to ``403 Forbidden``,
  but specifically for use when authentication is possible but has failed
  or not yet been provided.
* :py:meth:`~wheezy.http.response.forbidden`,
  :py:meth:`~wheezy.http.response.error402` - The request was a legal request,
  but the server is refusing to respond to it.
* :py:meth:`~wheezy.http.response.not_found`,
  :py:meth:`~wheezy.http.response.error404` - The requested resource could not
  be found but may be available again in the future. Subsequent requests by
  the client are permissible.
* :py:meth:`~wheezy.http.response.method_not_allowed`,
  :py:meth:`~wheezy.http.response.error405` - a request was made of a resource
  using a request method not supported by that resource; for example, using
  GET on a form which requires data to be presented via POST, or using PUT on
  a read-only resource.
* :py:meth:`~wheezy.http.response.internal_error`,
  :py:meth:`~wheezy.http.response.error500` - returns internal error response.
* :py:meth:`~wheezy.http.response.http_error` - returns a response with
  given status code (between 400 and 505).

JSON
~~~~

There is integration with `wheezy.core`_ package in json object encoding.

* :py:meth:`~wheezy.http.response.json_response` - returns json response.
  Accepts two arguments ``obj`` and optional ``encoding`` that defaults
  to `UTF-8`.

Here is simple example::

    from wheezy.http import bad_request
    from wheezy.http import json_response

    def now_handler(request):
        if not request.ajax:
            return bad_request()
        return json_response({'now': datetime.now()})

Requests other than AJAX are rejected, return JSON response with
current time of server.

Cookies
-------
:py:class:`~wheezy.http.cookie.HTTPCookie` is implemented according to
`rfc2109`_. Here is a typical usage::

    response.cookies.append(HTTPCookie('a', value='123', options=options))

In case you would like delete a certain cookie::

    response.cookies.append(HTTPCookie.delete('a', options=options))

Security
~~~~~~~~
While the idea behind secure cookies is to protect value (via some sort
of encryption, hashing, etc), this task is out of scope of this package.
However you can use ``Ticket`` from `wheezy.security`_ package for this
purpose; it supports encryption, hashing, expiration and verification.

Transforms
----------
Transforms is a way to manipulate handler response accordingly to some
algorithm. Typical use case includes: runtime minification, hardening
readability, gzip, etc. While middleware is applied to whole application,
transform in contrast to particular handler only.

Transform is any callable of this form::

    def transform(request, response):
        return response

There is a general decorator capable of applying several transforms to a response.
You can use it in the following way::

    from wheezy.http.transforms import gzip_transform
    from wheezy.http.transforms import response_transforms

    @response_transforms(gzip_transform(compress_level=9))
    def handler(request):
        return response

If you need apply several transforms to handler here is how you can do that::

    @response_transforms(a_transform, b_transform)
    def handler(request):
        return response

Order in which transforms are applied are from first argument to last::

    a_transform => b_transform

GZip Transform
~~~~~~~~~~~~~~
It is not always effective to apply gzip encoding to whole applications.
While in most cases WSGI applications are deployed behind reverse proxy
web server, it is more effective to use its capabilities of response
compression (10-20% productivity gain with nginx). ON the other side, gzipped
responses stored in cache are even better, since compression is done once
before being added to cache. This is why there is a gzip transform.

Here is a definition::

    def gzip_transform(compress_level=6, min_length=1024, vary=False):

``compress_level`` - the compression level, between 1 and 9, where 1
is the least compression (fastest) and 9 is the most (slowest)

``min_length`` - sets the minimum length, in bytes, of the
first chunk in response that will be compressed. Responses
shorter than this byte-length will not be compressed.

``vary`` - enables response header "Vary: Accept-Encoding".

Cache Policy
------------
:py:class:`~wheezy.http.cachepolicy.HTTPCachePolicy` controls cache
specific http headers: Cache-Control, Pragma, Expires, Last-Modified,
ETag, Vary.

Cacheability Options
~~~~~~~~~~~~~~~~~~~~

While particular set of valid HTTP cache headers depends on certain
use case, there are distinguished three of them:

* ``no-cache`` - indicates cached information should not be used and
  instead requests should be forwarded to the origin server.
* ``private`` - response is cacheable only on the client and not by
  shared (proxy server) caches.
* ``public`` - response is cacheable by clients and shared (proxy)
  caches.

Useful Methods
~~~~~~~~~~~~~~

:py:class:`~wheezy.http.cachepolicy.HTTPCachePolicy` includes the
following useful methods:

* ``private(*fields)`` - indicates that part of the response message is
  intended for a single user and MUST NOT be cached by a shared cache.
  Only valid for ``public`` cacheability.
* ``no_cache(*fields)`` - the specified field-name(s) MUST NOT be sent
  in the response to a subsequent request without successful re-validation
  with the origin server. Not valid for ``no-cache`` cacheability.
* ``no_store()`` - the purpose of the no-store directive is to prevent
  the inadvertent release or retention of sensitive information.
* ``must_revalidate()`` - because a cache MAY be configured to ignore a
  server's specified expiration time, and because a client request MAY
  include a max-stale directive (which has a similar effect), the
  protocol also includes a mechanism for the origin server to require
  re-validation of a cache entry on any subsequent use.
* ``proxy_revalidate()`` - the proxy-revalidate directive has the same
  meaning as the must-revalidate directive, except that it does not
  apply to non-shared user agent caches.
* ``no_transform()`` - the cache or proxy MUST NOT change any aspect
  of the entity-body that is specified by this header, including the
  value of the entity-body itself.
* ``append_extension(extension)`` - appends the ``extension`` to the
  Cache-Control HTTP header.
* ``max_age(delta)`` - accept a response whose age is no greater than
  the specified time in seconds. Not valid for ``no-cache`` cacheability.
* ``smax_age(delta)`` - if a response includes an s-maxage directive, then
  for a shared cache (but not for a private cache). Not valid for
  ``no-cache`` cacheability.
* ``expires(when)`` - gives the date/time after which the response is
  considered stale. Not valid for ``no-cache`` cacheability.
* ``last_modified(when)`` - the Last-Modified entity-header field
  indicates the date and time at which the origin server believes
  the variant was last modified. Not valid for ``no-cache`` cacheability.
* ``etag(tag)`` - provides the current value of the entity tag for the
  requested variant. Not valid for ``no-cache`` cacheability.
* ``vary(*headers)`` - indicates the set of request-header fields that
  fully determines, while the response is fresh, whether a cache is
  permitted to use the response to reply to a subsequent request without
  re-validation. Not valid for ``no-cache`` cacheability.

Examples
~~~~~~~~

You can use ``extend(headers)`` method to update ``headers`` with this
cache policy (this is what :py:class:`~wheezy.http.response.HTTPResponse`
does when ``cache`` attribute is set)::

    >>> headers = []
    >>> p = HTTPCachePolicy('no-cache')
    >>> p.extend(headers)
    >>> headers # doctest: +NORMALIZE_WHITESPACE
    [('Cache-Control', 'no-cache'),
    ('Pragma', 'no-cache'),
    ('Expires', '-1')]

Public caching headers:

    >>> from datetime import datetime, timedelta
    >>> from wheezy.core.datetime import UTC
    >>> when = datetime(2011, 9, 20, 15, 00, tzinfo=UTC)
    >>> headers = []
    >>> p = HTTPCachePolicy('public')
    >>> p.last_modified(when)
    >>> p.expires(when + timedelta(hours=1))
    >>> p.etag('abc')
    >>> p.vary()
    >>> p.extend(headers)
    >>> headers # doctest: +NORMALIZE_WHITESPACE
    [('Cache-Control', 'public'),
    ('Expires', 'Tue, 20 Sep 2011 16:00:00 GMT'),
    ('Last-Modified', 'Tue, 20 Sep 2011 15:00:00 GMT'),
    ('ETag', 'abc'),
    ('Vary', '*')]

While you do not directly make a call to extend headers from cache policy,
it is still useful to experiment within a python console.

Cache Profile
-------------
:py:class:`~wheezy.http.cacheprofile.CacheProfile` combines a number of
settings applicable to http cache policy as well as server side cache.

Cache Location
~~~~~~~~~~~~~~
:py:class:`~wheezy.http.cacheprofile.CacheProfile` supports the following
list of valid cache locations:

* ``none`` - no server or client cache.
* ``server`` - only server side caching, no client cache.
* ``client`` - only client side caching, no server cache.
* ``both`` - server and client caching.
* ``public`` - server and client caching including intermediate proxies.

Here is a map between cache profile cacheability and http cache policy:

.. literalinclude:: ../src/wheezy/http/cacheprofile.py
   :lines: 13-17

Cache profile method ``cache_policy`` is adapted according the above map.

Typical Use
~~~~~~~~~~~

You create a cache profile by instantiating
:py:class:`~wheezy.http.cacheprofile.CacheProfile` and passing in the following
arguments:

* ``location`` - must fall into one of acceptable values as defined
  by ``SUPPORTED``.
* ``duration`` - time for the cache item to be cached.
* ``no_store`` - instructs state of ``no-store`` http response header.
* ``vary_query`` - a list of query items that should be included into cache
  key.
* ``vary_form`` - a list of form items that should be included into cache
  key.
* ``vary_environ`` - a list of environ items that should be included into
  cache key (particularly useful to vary by HTTP headers, request scheme, etc).
* ``vary_cookies`` - a list of cookies that should be included
  into cache key.
* ``http_vary`` - manages HTTP cache policy `Very` header.
* ``etag_func`` - a function used to setup HTTP cache policy
  ETag header. See :py:meth:`~wheezy.http.cache.make_etag` and
  :py:meth:`~wheezy.http.cache.make_etag_crc32`.
* ``namespace`` - a namespace to be used in server cache operations.
* ``enabled`` - determines whenever this cache profile is enabled.

Here is an example::

    cache_profile = CacheProfile('client', duration=timedelta(minutes=15))

    cache_profile = CacheProfile('both', duration=15)

It is recommended to define cache profiles in a separate module and import them
as needed into a various parts of application. This way you can achieve
better control with a single place of change.

Content Cache
-------------
Content caching is the most effective type of cache. This way your application
code doesn't have to process to determine a valid response to user. Instead
a response is returned from cache. Since there is no heavy processing and just simple
operation to get an item from cache, it should be super fast. However not
every request can be cached and whether it can completely depends on your application.

If you show a list of goods and it has not changed in any way (price is the same,
etc.) why would you make several calls per second every time it requested
and regenerate the page again? You can apply cache profile to response and it
will be cached according to it rules.

What happens if the price has been changed, but the list of goods cacheability
was set to 15 mins? How to invalidate the cache? This is where ``CacheDependency``
comes to the rescue. The core feature of cache dependency is implemented in
package `wheezy.caching`_, however http module supports its integration.

Cache Contract
~~~~~~~~~~~~~~

Cache contract requires: ``get(key, namespace)``,
``set(key, value, time, namespace)``,
``set_multi(mapping, time, namespace)`` and
``incr(self, key, delta=1, namespace=None, initial_value=None)``.
Look at `wheezy.caching`_ package for more details.

@response_cache
~~~~~~~~~~~~~~~

:py:meth:`~wheezy.http.cache.response_cache` decorator is used to apply
cache feature to handler. Here is an example that includes also
``CacheDependency``::

    from wheezy.caching.patterns import Cached
    from wheezy.http import CacheProfile
    from wheezy.http import none_cache_profile
    from wheezy.http import response_cache
    from myapp import cache

    cached = Cached(cache, time=15)
    cache_profile = CacheProfile('server', duration=15)

    @response_cache(cache_profile)
    def list_of_goods(request):
        ...
        response.cache_dependency.append('list_of_goods:%s:' % catalog_id)
        return response

    @response_cache(none_cache_profile)
    def change_price(request):
        ...
        cached.dependency.delete('list_of_goods:%s:' % catalog_id)
        return response

While ``list_of_goods`` is being cached, ``change_price`` handler
effectively invalidates ``list_of_goods`` cache result, so next call
will fetch an updated list.

Note, cache dependency keys must not end with a number.

Cache Middleware
~~~~~~~~~~~~~~~~
The :py:meth:`~wheezy.http.cache.response_cache` decorator is applied to
handler. It is pretty far from the WSGI entry point, there are number
of middlewares as well as routing in between (all these are relatively
time consuming, especially routing). What if we were able determine
cache profile for the given request earlier, being the first middleware
in the chain. This is where
:py:class:`~wheezy.http.middleware.HTTPCacheMiddleware` comes to the scene.

:py:class:`~wheezy.http.middleware.HTTPCacheMiddleware` serves exactly
this purpose. It is initialized with two arguments:

* ``cache`` - a cache to be used (must be thread safe, see
  `wheezy.caching`_ for various implementations).
* ``middleware_vary`` - a strategy to be used to determine cache profile key
  for the incoming request.

Here is an example::

    cache = ...
    options = {
        'http_cache': cache
    }

    main = WSGIApplication([
        http_cache_middleware_factory()
    ], options)

``middleware_vary`` is an instance of
:py:class:`~wheezy.http.cacheprofile.RequestVary`. By default it varies
cache key by HTTP method and path. Let assume we would like vary middleware
key by HTTP scheme::

    options = {
        ...
        'http_cache_middleware_vary': RequestVary(
            environ=['wsgi.url_scheme'])
    }

Request Vary
~~~~~~~~~~~~
:py:class:`~wheezy.http.cacheprofile.RequestVary` is designed to compose
a key depending on number of values, including: headers, query, form and
environ. It always varies by request method and path.

Here is a list of arguments that can be passed during initialization:

* ``query`` - a list of request url query items.
* ``form`` - a list of form items submitted via http POST method.
* ``environ`` - a list of items from environ.

The following example will vary incoming request by request url query
parameter `q`::

    request_vary = RequestVary(query=['q'])

Note that you can vary by HTTP headers via environ names. A missing value is
distinguished from an empty one.

:py:class:`~wheezy.http.cacheprofile.RequestVary` is used by ``CacheProfile``
and ``HTTPCacheMiddleware`` internally.


WSGI Adapters
-------------

:ref:`wheezy.http` providers middleware adapters to be used for
integration with other WSGI applications:

* :py:class:`~wheezy.http.middleware.WSGIAdapterMiddleware` - adapts WSGI
  application response (initialization requires ``wsgi_app`` argument to
  be passed).
* :py:class:`~wheezy.http.middleware.EnvironCacheAdapterMiddleware` - adapts
  WSGI environ variables: ``wheezy.http.cache_policy``,
  ``wheezy.http.cache_profile``,
  ``wheezy.http.cache_dependency`` for http content caching
  middleware.

See the demo example in the `wsgi_adapter`_ application.


.. _`WSGI`: http://www.python.org/dev/peps/pep-3333
.. _`rfc2616`: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
.. _`rfc2109`:  http://www.ietf.org/rfc/rfc2109.txt
.. _`wheezy.core`: http://pypi.python.org/pypi/wheezy.core
.. _`wheezy.security`: http://pypi.python.org/pypi/wheezy.security
.. _`wheezy.caching`: http://pypi.python.org/pypi/wheezy.caching
.. _`wheezy.validation`: http://pypi.python.org/pypi/wheezy.validation
.. _`wheezy.web`: http://pypi.python.org/pypi/wheezy.web
.. _`wsgi_adapter`: https://bitbucket.org/akorn/wheezy.http/src/tip/demos/wsgi_adapter
