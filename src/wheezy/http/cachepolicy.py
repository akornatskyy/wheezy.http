
""" ``cachepolicy`` module.
"""

from wheezy.core.datetime import format_http_datetime
from wheezy.core.datetime import total_seconds


SUPPORTED = [
    'no-cache',
    'private',
    'public'
]


class HTTPCachePolicy(object):
    """ Controls cache specific http headers.

        >>> from datetime import datetime
        >>> from wheezy.core.datetime import UTC
        >>> when = datetime(2011, 9, 20, 15, 00, tzinfo=UTC)

        ``Expires`` HTTP header:
        >>> p = HTTPCachePolicy()
        >>> p.expires(when)
        >>> p.http_expires
        'Tue, 20 Sep 2011 15:00:00 GMT'
        >>> p = HTTPCachePolicy('no-cache')
        >>> p.http_expires
        '-1'

        ``Last-Modified`` HTTP header:
        >>> p = HTTPCachePolicy()
        >>> p.last_modified(when)
        >>> p.http_last_modified
        'Tue, 20 Sep 2011 15:00:00 GMT'

        ``Pragma`` HTTP header:

        >>> p = HTTPCachePolicy('no-cache')
        >>> p.http_pragma
        'no-cache'
        >>> p = HTTPCachePolicy()
        >>> p.http_pragma

        ``ETag`` HTTP header:

        >>> p = HTTPCachePolicy('public')
        >>> p.etag('ABC')
        >>> p.http_etag
        'ABC'
    """

    modified = None
    http_last_modified = None
    http_etag = None
    is_no_store = False
    is_must_revalidate = False
    is_proxy_revalidate = False
    is_no_transform = False
    max_age_delta = -1
    smax_age_delta = -1

    def __init__(self, cacheability='private'):
        """ Initialize cache policy with a given cacheability.

            If cacheability is not supported raise ValueError.

            >>> HTTPCachePolicy('x') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            AssertionError...
        """
        assert cacheability in SUPPORTED
        self.cacheability = cacheability
        self.is_no_cache = cacheability == 'no-cache'
        self.is_public = cacheability == 'public'
        self.http_pragma = self.is_no_cache and 'no-cache' or None
        self.http_expires = self.is_no_cache and '-1' or None
        self.vary_headers = []
        self.private_fields = []
        self.no_cache_fields = []
        self.extensions = []

    def extend(self, headers):
        """ Updates ``headers`` with this cache policy.

            No cache headers:

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

            If haders doesn't support ``__setitem__`` protocol
            raise TypeError.

            >>> p = HTTPCachePolicy()
            >>> p.extend('') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            AttributeError: ...
        """
        append = headers.append
        append(self.http_cache_control())
        if self.http_pragma:
            append(('Pragma', self.http_pragma))
        if self.http_expires:
            append(('Expires', self.http_expires))
        if self.http_last_modified:
            append(('Last-Modified', self.http_last_modified))
        if self.http_etag:
            append(('ETag', self.http_etag))
        if self.vary_headers:
            append(self.http_vary())

    def fail_no_cache(self, option):
        if self.is_no_cache:
            raise ValueError(option + ' is not valid '
                             'for no-cache cacheability')

    def assert_public(self, option):
        if not self.is_public:
            raise ValueError(option + ' is valid for '
                             'public cacheability only')

    def private(self, *fields):
        """ Indicates that part of the response message is
            intended for a single user and MUST NOT be
            cached by a shared cache.

            Only valid for ``public`` cacheability.

            >>> p = HTTPCachePolicy('public')
            >>> p.private('a', 'b')
            >>> p.private_fields
            ['a', 'b']

            Otherwise raise error.

            >>> p = HTTPCachePolicy('no-cache')
            >>> p.private('a') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        if fields:
            self.assert_public('private field(s)')
            self.private_fields += fields

    def no_cache(self, *fields):
        """ The specified field-name(s) MUST NOT be sent in the
            response to a subsequent request without successful
            revalidation with the origin server.

            >>> p = HTTPCachePolicy('public')
            >>> p.no_cache('a', 'b')
            >>> p.no_cache_fields
            ['a', 'b']

            Not valid for ``no-cache`` cacheability.

            >>> p = HTTPCachePolicy('no-cache')
            >>> p.no_cache('a') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
          """
        if fields:
            self.fail_no_cache('no-cache fields')
            self.no_cache_fields += fields

    def no_store(self):
        """ The purpose of the no-store directive is to
            prevent the inadvertent release or retention of
            sensitive information.

            >>> p = HTTPCachePolicy()
            >>> p.no_store()
            >>> assert p.is_no_store
        """
        self.is_no_store = True

    def must_revalidate(self):
        """ Because a cache MAY be configured to ignore a
            server's specified expiration time, and because a
            client request MAY include a max-stale directive
            (which has a similar effect), the protocol also
            includes a mechanism for the origin server to
            require revalidation of a cache entry on any
            subsequent use.

            >>> p = HTTPCachePolicy()
            >>> p.must_revalidate()
            >>> assert p.is_must_revalidate

            Raises ValueError if proxy-revalidave is set.

            >>> p = HTTPCachePolicy()
            >>> p.is_proxy_revalidate = True
            >>> p.must_revalidate() # doctest: +ELLIPSIS
            Traceback (most recent call last):
              ...
            ValueError: ...
        """
        if self.is_proxy_revalidate:
            raise ValueError('proxy-revalidate is already set')
        self.is_must_revalidate = True

    def proxy_revalidate(self):
        """ The proxy-revalidate directive has the same
            meaning as the must- revalidate directive,
            except that it does not apply to non-shared
            user agent caches.

            >>> p = HTTPCachePolicy()
            >>> p.proxy_revalidate()
            >>> assert p.is_proxy_revalidate

            Raises ValueError if must-revalidave is set.

            >>> p = HTTPCachePolicy()
            >>> p.is_must_revalidate = True
            >>> p.proxy_revalidate() # doctest: +ELLIPSIS
            Traceback (most recent call last):
              ...
            ValueError: ...
        """
        if self.is_must_revalidate:
            raise ValueError('must-revalidate is already set')
        self.is_proxy_revalidate = True

    def no_transform(self):
        """ The cache or proxy MUST NOT change any aspect
            of the entity-body that is specified by this header,
            including the value of the entity-body itself.

            >>> p = HTTPCachePolicy()
            >>> p.no_transform()
            >>> assert p.is_no_transform
        """
        self.is_no_transform = True

    def append_extension(self, extension):
        """ Appends the ``extension`` to the Cache-Control HTTP header.

            >>> p = HTTPCachePolicy()
            >>> p.append_extension('ext')
            >>> assert 'ext' in p.extensions
        """
        self.extensions.append(extension)

    def max_age(self, delta):
        """ Accept a response whose age is no greater than the
            specified time in seconds.

            ``delta`` can be ``int`` or ``datetime.timedelta``.

            >>> p = HTTPCachePolicy()
            >>> p.max_age(100)
            >>> p.max_age_delta
            100

            Not valid for ``no-cache`` cacheability, raise ValueError.

            >>> p = HTTPCachePolicy('no-cache')
            >>> p.max_age(100) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        self.fail_no_cache('max-age')
        self.max_age_delta = total_seconds(delta)

    def smax_age(self, delta):
        """ If a response includes an s-maxage directive, then
            for a shared cache (but not for a private cache),
            the maximum age specified by this directive overrides
            the maximum age specified by either the max-age
            directive or the Expires header. Accept a response whose
            age is no greater than the specified time in seconds.

            ``delta`` can be ``int`` or ``datetime.timedelta``.

            >>> p = HTTPCachePolicy()
            >>> p.smax_age(100)
            >>> p.smax_age_delta
            100

            Not valid for ``no-cache`` cacheability, raise ValueError.

            >>> p = HTTPCachePolicy('no-cache')
            >>> p.smax_age(100) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        self.fail_no_cache('smax-age')
        self.smax_age_delta = total_seconds(delta)

    def expires(self, when):
        """ The Expires entity-header field gives the date/time
            after which the response is considered stale.

            >>> from datetime import datetime
            >>> from wheezy.core.datetime import UTC
            >>> p = HTTPCachePolicy()
            >>> when = datetime(2011, 9, 20, 13, 30, tzinfo=UTC)
            >>> p.expires(when)
            >>> p.http_expires
            'Tue, 20 Sep 2011 13:30:00 GMT'

            Not valid for ``no-cache`` cacheability, raise ValueError.

            >>> p = HTTPCachePolicy('no-cache')
            >>> p.expires(when) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        self.fail_no_cache('expires')
        self.http_expires = format_http_datetime(when)

    def last_modified(self, when):
        """ The Last-Modified entity-header field indicates the
            date and time at which the origin server believes
            the variant was last modified.

            >>> from datetime import datetime
            >>> from wheezy.core.datetime import UTC
            >>> p = HTTPCachePolicy()
            >>> when = datetime(2011, 9, 20, 15, 1, tzinfo=UTC)
            >>> p.last_modified(when)
            >>> p.http_last_modified
            'Tue, 20 Sep 2011 15:01:00 GMT'

            Not valid for ``no-cache`` cacheability, raise ValueError.

            >>> p = HTTPCachePolicy('no-cache')
            >>> p.last_modified(when) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        self.fail_no_cache('last_modified')
        self.modified = when
        self.http_last_modified = format_http_datetime(when)

    def etag(self, tag):
        """ Provides the current value of the entity tag for the
            requested variant.

            >>> p = HTTPCachePolicy('public')
            >>> p.etag('ABC')
            >>> p.http_etag
            'ABC'

            Valid only for ``public`` cacheability, raise ValueError.

            >>> p = HTTPCachePolicy()
            >>> p.etag('ABC') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        self.assert_public('etag')
        self.http_etag = tag

    def vary(self, *headers):
        """ The Vary field value indicates the set of request-header
            fields that fully determines, while the response is fresh,
            whether a cache is permitted to use the response to reply
            to a subsequent request without revalidation.

            >>> p = HTTPCachePolicy('public')
            >>> p.vary('Accept-Encoding', 'Accept-Language')
            >>> p.vary_headers
            ['Accept-Encoding', 'Accept-Language']

            Vary by star (*):
            >>> p = HTTPCachePolicy('public')
            >>> p.vary()
            >>> p.vary_headers
            ('*',)

            Valid only for ``public`` cacheability, raise ValueError.

            >>> p = HTTPCachePolicy()
            >>> p.vary() # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        self.assert_public('vary')
        if headers:
            self.vary_headers.extend(headers)
        else:
            self.vary_headers = ('*',)

    def http_vary(self):
        """ Returns a value for Vary header.

            >>> p = HTTPCachePolicy('public')
            >>> p.vary()
            >>> p.http_vary()
            ('Vary', '*')
        """
        return ('Vary', ', '.join(self.vary_headers))

    def http_cache_control(self):
        """ Returns a value for Cache-Control header.

            >>> p = HTTPCachePolicy('public')
            >>> p.http_cache_control()
            ('Cache-Control', 'public')
            >>> p = HTTPCachePolicy('public')
            >>> p.private('a', 'b')
            >>> p.http_cache_control()
            ('Cache-Control', 'public, private="a, b"')
            >>> p = HTTPCachePolicy('public')
            >>> p.no_cache('c', 'd')
            >>> p.http_cache_control()
            ('Cache-Control', 'public, no-cache="c, d"')
            >>> p = HTTPCachePolicy('no-cache')
            >>> p.no_store()
            >>> p.no_transform()
            >>> p.http_cache_control()
            ('Cache-Control', 'no-cache, no-store, no-transform')
            >>> p = HTTPCachePolicy('no-cache')
            >>> p.must_revalidate()
            >>> p.http_cache_control()
            ('Cache-Control', 'no-cache, must-revalidate')
            >>> p = HTTPCachePolicy('no-cache')
            >>> p.proxy_revalidate()
            >>> p.http_cache_control()
            ('Cache-Control', 'no-cache, proxy-revalidate')
            >>> p = HTTPCachePolicy()
            >>> p.append_extension('ext1')
            >>> p.append_extension('ext2')
            >>> p.http_cache_control()
            ('Cache-Control', 'private, ext1, ext2')
            >>> p = HTTPCachePolicy()
            >>> p.max_age(60)
            >>> p.http_cache_control()
            ('Cache-Control', 'private, max-age=60')
            >>> p = HTTPCachePolicy()
            >>> p.smax_age(15)
            >>> p.http_cache_control()
            ('Cache-Control', 'private, smax-age=15')
        """
        directives = [self.cacheability]
        append = directives.append
        if self.private_fields:
            append('private="' + ', '.join(self.private_fields) + '"')
        if self.no_cache_fields:
            append('no-cache="' + ', '.join(self.no_cache_fields) + '"')
        if self.is_no_store:
            append('no-store')
        if self.is_must_revalidate:
            append('must-revalidate')
        elif self.is_proxy_revalidate:
            append('proxy-revalidate')
        if self.is_no_transform:
            append('no-transform')
        if self.extensions:
            append(', '.join(self.extensions))
        if self.max_age_delta >= 0:
            append('max-age=' + str(self.max_age_delta))
        if self.smax_age_delta >= 0:
            append('smax-age=' + str(self.smax_age_delta))
        return ('Cache-Control', ', '.join(directives))
