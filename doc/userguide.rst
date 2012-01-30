
User Guide
==========

Configuration Options
---------------------
Configuration options is a python dictionary passed to
:py:class:`~wheezy.http.application.WSGIApplication` during initialization.
These options are shared across various parts of application, including:
middleware factory, http request/response, etc. There are no required
options necessary to be setup before use, since they all fallback to some
defaults defined in :py:mod:`~wheezy.http.config` module.

Here is a snippet from :ref:`helloworld` (setting up request/response
encoding):

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 11-13

Let take a look at another example. Consider our application is behind
some sort of reverse proxy (e.g. nginx). So remote address of client is
passed by reverse proxy in HTTP header ``X_FORWARDED_FOR``. You are able
to easily satisfy this::

    options = {
        #'ENVIRON_REMOTE_ADDR': 'REMOTE_ADDR',
        'ENVIRON_REMOTE_ADDR': 'HTTP_X_FORWARDED_FOR'
    }

See full list of available options in :py:mod:`~wheezy.http.config` module.

Application
-----------
`WSGI`_ is the Web Server Gateway Interface. It is a specification for
web/application servers to communicate with web applications. It is a
Python standard, described in detail in PEP 3333.

An instance of :py:class:`~wheezy.http.application.WSGIApplication` is
an entry point of your `WSGI`_ application. You instantiate it by supplying
a list of desied ``middleware factories`` and global configuration
``options``. Here is a snippet from :ref:`helloworld` example:

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 31-33

This callable is passed to web server. Here is an integration example with
application server from python standard wsgiref package:

.. literalinclude:: ../demos/hello/helloworld.py
   :lines: 36-43

The integration with various WSGI application servers vary, however the
principal of WSGI entry point is the same across those implementations.

Middleware
----------

The presence of middleware in general is transparent to application
and requires no special support. Middleware is usually characterized by
playing the following roles within application:

* It is singleton, the only one instance per application.
* It is sort of interceptor of incoming request to handler.
* They can be chained so one pass request to following as well as capable
  to inspect response, override it, extend or modify as necessary.
* It capable to supply additional information in request context.

Middleware can be any callable of the following form::

    def middleware(request, following):
        if following:
            response = following(request)
        else:
            response = ...
        return response

Middleware callable accepts as a first argument an instance of
:py:class:`~wheezy.http.request.HTTPRequest` and next middleware in the
chain (``following`` argument). It is up to middleware to decide whenever
to call next middleware callable in the chain. It is expected that middleware
return an instance of :py:class:`~wheezy.http.response.HTTPResponse` class or
``None``.

Middleware Factory
~~~~~~~~~~~~~~~~~~

Usually middleware requires sort of initialization before it is being used.
This can be some configuration variables or sort of preparation, verification,
etc. ``Middleware Factory`` serves this purpose.

Middleware factory can be any callable of the following form::

    def middleware_factory(options):
        return middleware

Middleware factory is initialized with ``options``, it is the same dictionary
used during :py:class:`~wheezy.http.application.WSGIApplication`
initialization. Middleware factory returns particular middleware implementation
or ``None`` (this can be useful for some sort of initialization that needs
to be run during application bootstrap, e.g. defaults).

In case the last middleware in the chain returns ``None`` it is equivalent
to returning HTTP response not found (HTTP status code 404).

Execution Order
~~~~~~~~~~~~~~~

Middleware is initialized and executed in certain order. Let setup a simple
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

Request
-------
:py:class:`~wheezy.http.request.HTTPRequest` is a wrapper around WSGI environ
dictionary. It provides access to all variables stored within environ as well
as provide several handy methods for daily use.

:py:class:`~wheezy.http.request.HTTPRequest` includes the following useful
attributes (they are evaluated only once during processing):

* ``method`` - request method (GET, POST, HEAD, etc)
* ``host`` - request host; depends on definition of configuration option
  ``ENVIRON_HOST`` and usually corresponds to WSGI variables: ``HTTP_HOST``
  (default), ``HTTP_X_FORWARDED_HOST``, or other related.
* ``remote_addr`` - remote address; depends on definition of configuration
  option ``ENVIRON_REMOTE_ADDR`` and usually corresponds to WSGI variables:
  ``REMOTE_ADDR`` (default), ``HTTP_X_FORWARDED_FOR``, or other related.
* ``root_path`` - application virtual path; environ ``SCRIPT_NAME``
  plus ``/``.
* ``path`` - request url path; environ ``SCRIPT_NAME`` plus ``PATH_INFO``.
* ``headers`` - HTTP headers; an instance of
  :py:class:`~wheezy.http.headers.HTTPRequestHeaders`.
* ``query`` - request url query; an instance of ``defaultdict(list)``.
* ``form`` - request form; an instance of ``defaultdict(list)``.
* ``files`` - request form files; an instance of ``defaultdict(list)``.
* ``cookies`` - cookies passed by browser; an instance of ``dict``.
* ``ajax`` - returns ``True`` is current request is AJAX request.
* ``secure`` - determines whenever current request is made via SSL
  connection; depends on definition of configuration option ``ENVIRON_HTTPS``
  and usually corresponds to WSGI variables: ``wsgi.url_scheme`` (default),
  ``HTTP_X_FORWARDED_PROTO``, or other related.
* ``scheme`` - request url scheme (``http`` or ``https``); takes into
  account ``secure`` attribute.
* ``urlparts`` - returns a tuple of 5 corresponding to request url: scheme,
  host, path, query and fragment (always ``None``).

Form and Query
~~~~~~~~~~~~~~

While working with request form/query you get ``defaultdict(list)``. Each
key in dictionary maps to a list of values. There usually exists just one
value so working with list is not that convenient. You can use
``first_item_adapter`` or ``last_item_adapter``::

    >>> from wheezy.core.collections import last_item_adapter
    >>> r = HTTPRequest(environ)
    >>> r.query['a']
    ['1', '2']
    >>> query = last_item_adapter(r.query)
    >>> query['a']
    '2'

Response
--------
:py:class:`~wheezy.http.response.HTTPResponse` correctly maps the following
HTTP response status codes (according to `rfc2616`_):

.. literalinclude:: ../src/wheezy/http/response.py
   :lines: 12-37

You instantiate :py:class:`~wheezy.http.response.HTTPResponse` and initialize
it with ``content_type``, ``encoding`` and ``options``::

    >>> r = HTTPResponse()
    >>> r.headers
    [('Content-Type', 'text/html; charset=utf-8')]
    >>> r = HTTPResponse(content_type='image/gif')
    >>> r.headers
    [('Content-Type', 'image/gif')]

    >>> r = HTTPResponse(encoding='iso-8859-4')
    >>> r.headers
    [('Content-Type', 'text/html; charset=iso-8859-4')]

:py:class:`~wheezy.http.response.HTTPResponse` has method ``write`` that
let you buffer response before it actually being passed to application server.
The ``write`` method does encoding of input string accordingly to response
encoding options. You can also pass bytes so they buffered unchanged.

Here are some attributes:

* ``cache`` - setup :py:class:`~wheezy.http.response.HTTPCachePolicy`.
  Defaults to ``private`` cache policy.
* ``skip_body`` - doesn't pass response body; content length is set to zero.
* ``dependency`` - it is used to setup ``CacheDependency`` for given request
  thus effectively invalidating cached response depending on some application
  logic.
* ``headers`` - list of headers to be returned to browser; the header must
  be a tuple of two: ``(name, value)``.
* ``cookies`` - list of cookies to set in response. This list contains
  :py:class:`~wheezy.http.cookie.HTTPCookie` objects.

Preset Responses
~~~~~~~~~~~~~~~~

There are a number of handy preset responses defined as the following:

.. literalinclude:: ../src/wheezy/http/response.py
   :lines: 63-68

``http_error`` function is definded this way:

.. literalinclude:: ../src/wheezy/http/response.py
   :lines: 71

Response Redirect
~~~~~~~~~~~~~~~~~
Here is a definition of redirect function::

    def redirect(absolute_url, permanent=False, options=None):

Optional argument ``permanent`` determines whenever redirect should be
permanent or not.

Cookies
-------
:py:class:`~wheezy.http.cookie.HTTPCookie` is implemented according to
`rfc2109`_. Here is a typical use::

    response = HTTPResponse()
    response.cookies.append(HTTPCookie('a', value='123'))

In case you would like delete certain cookie::

    response = HTTPResponse()
    response.cookies.append(HTTPCookie.delete('a'))

Security
~~~~~~~~
While idea behind secure cookies is to protect value (via some sort
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

There is general decorator capable to apply several transforms to response.
You can use it this way::

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
compression (10-20% productivity gain with nginx). From other side gzipped
response stored in cache is even better since compression is done once
before being added to cache. This is why you have gzip transform.

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
  requested variant. Valid only for ``public`` cacheability.
* ``vary(*headers)`` - indicates the set of request-header fields that
  fully determines, while the response is fresh, whether a cache is
  permitted to use the response to reply to a subsequent request without
  re-validation. Valid only for ``public`` cacheability.

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
    
While you not directly make a call to extend headers from cache policy
it is still useful to experiment in python console.

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
   :lines: 13-19

Cache profile method ``cache_policy`` is adapted according to map from above.

Typical Use
~~~~~~~~~~~

You create cache profile by instantiating 
:py:class:`~wheezy.http.cacheprofile.CacheProfile` and passing the following
arguments:

* ``location`` - must fall into one of acceptable values as defined 
  by ``SUPPORTED``.
* ``duration`` - time for the cache item to be cached.
* ``no_store`` - instructs state of ``No-Cache`` http response header.
* ``vary_headers`` - a list of headers that should be included into cache 
  key.
* ``vary_query`` - a list of query items that should be included into cache 
  key.
* ``vary_form`` - a list of form items that should be included into cache 
  key.
* ``vary_environ`` - a list of environ items that should be included into 
  cache key.
* ``middleware_vary`` - an instance of 
  :py:class:`~wheezy.http.cacheprofile.RequestVary` describing how to vary
  cache key in cache middleware.
* ``enabled`` - determines whenever this cache profile is enabled.

Here is an example::

    cache_profile = CacheProfile('client', duration=timedelta(minutes=15))
    
    cache_profile = CacheProfile('both', duration=15)

It is recommended define cache profiles in a separate module and import them
as needed into a various parts of application. This way you can achieve
better control and a single place of change.

Content Cache
-------------
Content caching is the most effective type of cache. This way your application
code doesn't provide processing to determine valid response to user, instead
one returned from cache. Since there is no heavy processing and just simple
operation to get item from cache it should be supper fast. However not 
every request can be cached and it completely depends on your application.

If you show a list of goods and its not changed in any way (price is the same,
etc.) why would you make several calls per second every time it requested
and regenerate page again? You can apply cache profile to response and it
will be cached according to it rules.

What happens if the price has been changed but list of goods cacheability
is set to 15 mins, how to invalidate it? This is where ``CacheDependency``
is to rescue. The core feature of cache dependency is implemented in
package `wheezy.caching`_, however http module supports integration.
       
Cache Contract
~~~~~~~~~~~~~~
        
Cache contract requires just two methods: ``get(key)`` and 
``set_multi(mapping)``. Cache dependency requires ``next_key()`` only. Look
at `wheezy.caching`_ package for more details.

@response_cache
~~~~~~~~~~~~~~~

:py:meth:`~wheezy.http.cache.response_cache` decorator is used to apply
cache feature to handler. Here is an example::

    from wheezy.caching import MemoryCache
    from wheezy.http import CacheProfile
    from wheezy.http import response_cache
    
    cache = MemoryCache()
    cache_profile = CacheProfile('server', duration=15)
    
    @response_cache(cache_profile, cache=cache)
    def list_of_goods(request):
        ...
        response.dependency = CacheDependency('list_of_goods')
        return response
        
    def change_price(request):
        CacheDependency('list_of_goods').delete()
        ...        
        return response

While ``list_of_goods`` is being cached, ``change_price`` handler 
effectively invalidates ``list_of_goods`` cache result, so next call
will fetch updated list.

Cache Middleware
~~~~~~~~~~~~~~~~
:py:meth:`~wheezy.http.cache.response_cache` decorator is applied to
handler. It is pretty far from the WSGI entry point, there are number
of middlewares as well as routing in between (all these are relatively
time consuming, especially routing). What if we were able determine
cache profile for the given request earlier, being the first middleware
in the chain. This is where 
:py:class:`~wheezy.http.middleware.HTTPCacheMiddleware` comes to scene.

:py:class:`~wheezy.http.middleware.HTTPCacheMiddleware` serves exactly
this purpose. It is initialized with two arguments:

* ``cache`` - instance of cache used
* ``middleware_vary`` - strategy to be used to determine cache key 
  for the incoming request.
  
Here is an example::

    options = {
        'http_cache': http_cache
    }
    
    main = WSGIApplication([
        http_cache_middleware_factory()
    ], options)

``middleware_vary`` is an instance of 
:py:class:`~wheezy.http.cacheprofile.RequestVary`. By default it varies
cache key by HTTP method and path. Let assume we would like vary key by
http header Accept-Encoding::

    options = {
        ...
        'http_cache_middleware_vary': RequestVary(
            headers=['ACCEPT_ENCODING'])
    }

Request Vary
~~~~~~~~~~~~
:py:class:`~wheezy.http.cacheprofile.RequestVary` is designed to compose 
a key depending on number of values, including: headers, query, form and 
environ. It always vary by request method and path.

Here is a list of arguments that can be passed during initialization:

* ``headers`` - a list of headers.
* ``query`` - a list of request url query items.
* ``form`` - a list of form items submitted via http POST method.
* ``environ`` - a list of items from environ.

The following example will vary incoming request by request url query
parameter `q`::

    request_vary = RequestVary(query=['q'])

:py:class:`~wheezy.http.cacheprofile.RequestVary` is used by ``CacheProfile``
and ``HTTPCacheMiddleware`` internally.


.. _`WSGI`: http://www.python.org/dev/peps/pep-3333
.. _`rfc2616`: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
.. _`rfc2109`:  http://www.ietf.org/rfc/rfc2109.txt
.. _`wheezy.security`: http://pypi.python.org/pypi/wheezy.security
.. _`wheezy.caching`: http://pypi.python.org/pypi/wheezy.caching
