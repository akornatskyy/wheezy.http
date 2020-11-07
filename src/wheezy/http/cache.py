""" ``cache`` module
"""

from hashlib import md5
from zlib import crc32

from wheezy.http.cacheprofile import none_cache_profile


def response_cache(profile=None):
    """Decorator that applies cache profile strategy to the
    wrapping handler.
    """
    if not profile:
        profile = none_cache_profile

    def decorate(handler):
        if not profile.enabled:
            return handler

        cache_policy_func = profile.cache_policy
        if profile.request_vary:
            if profile.etag_func:
                etag_func = profile.etag_func

                def etag(request, *args, **kwargs):
                    response = handler(request, *args, **kwargs)
                    response.cache_profile = profile
                    response.cache_policy = cache_policy_func()
                    response.cache_policy.http_etag = etag_func(
                        response.buffer
                    )
                    return response

                return etag
            else:

                def cache(request, *args, **kwargs):
                    response = handler(request, *args, **kwargs)
                    response.cache_profile = profile
                    response.cache_policy = cache_policy_func()
                    return response

                return cache
        else:

            def no_cache(request, *args, **kwargs):
                response = handler(request, *args, **kwargs)
                response.cache_profile = None
                response.cache_policy = cache_policy_func()
                return response

            return no_cache

    return decorate


def wsgi_cache(profile):
    """Decorator that wraps wsgi app and set cache profile."""

    def decorate(wsgi_app):
        if not profile.enabled:
            return wsgi_app

        def wsgi_wrapper(environ, start_response):
            environ["wheezy.http.cache_profile"] = profile
            return wsgi_app(environ, start_response)

        return wsgi_wrapper

    return decorate


def make_etag(hasher):
    """Build etag function based on `hasher` algorithm."""

    def etag(buf):
        h = hasher()
        for chunk in buf:
            h.update(chunk)
        return '"' + h.hexdigest() + '"'

    return etag


etag_md5 = make_etag(md5)


def make_etag_crc32(hasher):
    """Build etag function based on `hasher` algorithm and crc32."""

    def etag(buf):
        h = hasher()
        for chunk in buf:
            h.update(chunk)
        return '"%08x"' % (crc32(h.hexdigest().encode("latin1")) & 0xFFFFFFFF)

    return etag


etag_md5crc32 = make_etag_crc32(md5)


class SurfaceResponse(object):
    """WSGI wrapper that returns ``response`` headers and buffer."""

    __slots__ = ("inner",)

    def __init__(self, response):
        """Initializes response."""
        self.inner = response

    def __call__(self, start_response):
        """WSGI call processing."""
        start_response("200 OK", self.inner.headers)
        return self.inner.buffer


class NotModifiedResponse(object):
    """Not modified cachable response."""

    status_code = 304
    __slots__ = ("headers",)

    def __init__(self, response):
        """Initializes not modified cachable response."""
        self.headers = [
            h for h in response.headers if h[0] != "Content-Length"
        ]

    def __call__(self, start_response):
        """WSGI call processing."""
        start_response("304 Not Modified", self.headers)
        return []


class CacheableResponse(object):
    """Cachable response."""

    status_code = 200
    last_modified = None
    etag = None

    def __init__(self, response):
        """Initializes cachable response."""

        def capture_headers(status, headers):
            self.headers = [h for h in headers if h[0] != "Set-Cookie"]

        self.buffer = tuple(response(capture_headers))
        cache_policy = response.cache_policy
        if cache_policy:
            self.last_modified = cache_policy.modified
            self.etag = cache_policy.http_etag

    def __call__(self, start_response):
        """WSGI call processing."""
        start_response("200 OK", self.headers)
        return self.buffer
