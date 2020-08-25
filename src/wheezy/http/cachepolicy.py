""" ``cachepolicy`` module.
"""

from wheezy.core.datetime import format_http_datetime, total_seconds

SUPPORTED = ["no-cache", "private", "public"]


class HTTPCachePolicy(object):
    """Controls cache specific http headers."""

    modified = None
    http_last_modified = None
    http_etag = None
    is_no_store = False
    is_must_revalidate = False
    is_proxy_revalidate = False
    is_no_transform = False
    max_age_delta = -1
    smax_age_delta = -1

    def __init__(self, cacheability="private"):
        """Initialize cache policy with a given cacheability."""
        assert cacheability in SUPPORTED
        self.cacheability = cacheability
        self.is_no_cache = cacheability == "no-cache"
        self.is_public = cacheability == "public"
        self.http_pragma = self.is_no_cache and "no-cache" or None
        self.http_expires = self.is_no_cache and "-1" or None
        self.vary_headers = []
        self.private_fields = []
        self.no_cache_fields = []
        self.extensions = []

    def extend(self, headers):
        """Updates ``headers`` with this cache policy."""
        append = headers.append
        append(self.http_cache_control())
        if self.http_pragma:
            append(("Pragma", self.http_pragma))
        if self.http_expires:
            append(("Expires", self.http_expires))
        if self.http_last_modified:
            append(("Last-Modified", self.http_last_modified))
        if self.http_etag:
            append(("ETag", self.http_etag))
        if self.vary_headers:
            append(self.http_vary())

    def fail_no_cache(self, option):
        if self.is_no_cache:
            raise AssertionError(
                option + " is not valid " "for no-cache cacheability"
            )
        return True

    def assert_public(self, option):
        if not self.is_public:
            raise AssertionError(
                option + " is valid for " "public cacheability only"
            )
        return True

    def private(self, *fields):
        """Indicates that part of the response message is
        intended for a single user and MUST NOT be
        cached by a shared cache.

        Only valid for ``public`` cacheability.
        """
        if fields:
            assert self.assert_public("private field(s)")
            self.private_fields += fields

    def no_cache(self, *fields):
        """The specified field-name(s) MUST NOT be sent in the
        response to a subsequent request without successful
        revalidation with the origin server.

        Not valid for ``no-cache`` cacheability.
        """
        if fields:
            assert self.fail_no_cache("no-cache fields")
            self.no_cache_fields += fields

    def no_store(self):
        """The purpose of the no-store directive is to
        prevent the inadvertent release or retention of
        sensitive information.
        """
        self.is_no_store = True

    def must_revalidate(self):
        """Because a cache MAY be configured to ignore a
        server's specified expiration time, and because a
        client request MAY include a max-stale directive
        (which has a similar effect), the protocol also
        includes a mechanism for the origin server to
        require revalidation of a cache entry on any
        subsequent use.

        Raises AssertionError if proxy-revalidave is set.
        """
        assert not self.is_proxy_revalidate, "proxy-revalidate is already set"
        self.is_must_revalidate = True

    def proxy_revalidate(self):
        """The proxy-revalidate directive has the same
        meaning as the must- revalidate directive,
        except that it does not apply to non-shared
        user agent caches.

        Raises AssertionError if must-revalidave is set.
        """
        assert not self.is_must_revalidate, "must-revalidate is already set"
        self.is_proxy_revalidate = True

    def no_transform(self):
        """The cache or proxy MUST NOT change any aspect
        of the entity-body that is specified by this header,
        including the value of the entity-body itself.
        """
        self.is_no_transform = True

    def append_extension(self, extension):
        """Appends the ``extension`` to the Cache-Control HTTP header."""
        self.extensions.append(extension)

    def max_age(self, delta):
        """Accept a response whose age is no greater than the
        specified time in seconds.

        ``delta`` can be ``int`` or ``datetime.timedelta``.

        Not valid for ``no-cache`` cacheability, raise AssertionError.
        """
        assert self.fail_no_cache("max-age")
        self.max_age_delta = total_seconds(delta)

    def smax_age(self, delta):
        """If a response includes an s-maxage directive, then
        for a shared cache (but not for a private cache),
        the maximum age specified by this directive overrides
        the maximum age specified by either the max-age
        directive or the Expires header. Accept a response whose
        age is no greater than the specified time in seconds.

        ``delta`` can be ``int`` or ``datetime.timedelta``.

        Not valid for ``no-cache`` cacheability, raise AssertionError.
        """
        assert self.fail_no_cache("smax-age")
        self.smax_age_delta = total_seconds(delta)

    def expires(self, when):
        """The Expires entity-header field gives the date/time
        after which the response is considered stale.

        Not valid for ``no-cache`` cacheability, raise AssertionError.
        """
        assert self.fail_no_cache("expires")
        self.http_expires = format_http_datetime(when)

    def last_modified(self, when):
        """The Last-Modified entity-header field indicates the
        date and time at which the origin server believes
        the variant was last modified.

        Not valid for ``no-cache`` cacheability, raise AssertionError.
        """
        assert self.fail_no_cache("last_modified")
        self.modified = when
        self.http_last_modified = format_http_datetime(when)

    def etag(self, tag):
        """Provides the current value of the entity tag for the
        requested variant.

        Not valid for ``no-cache`` cacheability, raise AssertionError.
        """
        assert self.fail_no_cache("etag")
        self.http_etag = tag

    def vary(self, *headers):
        """The Vary field value indicates the set of request-header
        fields that fully determines, while the response is fresh,
        whether a cache is permitted to use the response to reply
        to a subsequent request without revalidation.

        Not valid for ``no-cache`` cacheability, raise AssertionError.
        """
        assert self.fail_no_cache("vary")
        if headers:
            self.vary_headers.extend(headers)
        else:
            self.vary_headers = ("*",)

    def http_vary(self):
        """Returns a value for Vary header."""
        return ("Vary", ", ".join(self.vary_headers))

    def http_cache_control(self):
        """Returns a value for Cache-Control header."""
        directives = [self.cacheability]
        append = directives.append
        if self.private_fields:
            append('private="' + ", ".join(self.private_fields) + '"')
        if self.no_cache_fields:
            append('no-cache="' + ", ".join(self.no_cache_fields) + '"')
        if self.is_no_store:
            append("no-store")
        if self.is_must_revalidate:
            append("must-revalidate")
        elif self.is_proxy_revalidate:
            append("proxy-revalidate")
        if self.is_no_transform:
            append("no-transform")
        if self.extensions:
            append(", ".join(self.extensions))
        if self.max_age_delta >= 0:
            append("max-age=" + str(self.max_age_delta))
        if self.smax_age_delta >= 0:
            append("smax-age=" + str(self.smax_age_delta))
        return ("Cache-Control", ", ".join(directives))
