
""" ``cache`` module
"""

from zlib import crc32

from wheezy.http.comp import b
from wheezy.http.comp import md5


def response_cache(profile):
    """ Decorator that applies cache profile strategy to the
        wrapping handler.
    """
    def decorate(handler):
        if not profile.enabled:
            return handler

        if profile.request_vary:
            if profile.etag_func:
                etag_func = profile.etag_func

                def etag(request, *args, **kwargs):
                    response = handler(request, *args, **kwargs)
                    response.cache_profile = profile
                    if response.cache_policy is None:
                        response.cache_policy = profile.cache_policy()
                        response.cache_policy.etag(etag_func(response.buffer))
                    return response
                return etag
            else:
                def cache(request, *args, **kwargs):
                    response = handler(request, *args, **kwargs)
                    response.cache_profile = profile
                    if response.cache_policy is None:
                        response.cache_policy = profile.cache_policy()
                    return response
                return cache
        else:
            def no_cache(request, *args, **kwargs):
                response = handler(request, *args, **kwargs)
                if response.cache_policy is None:
                    response.cache_policy = profile.cache_policy()
                return response
            return no_cache
    return decorate


def make_etag(hasher):
    """ Build etag function based on `hasher` algorithm.

        >>> from wheezy.http.comp import b
        >>> etag = make_etag(md5)
        >>> etag([b('test')])
        '"098f6bcd4621d373cade4e832627b4f6"'
        >>> etag([b('test')] * 2)
        '"05a671c66aefea124cc08b76ea6d30bb"'
    """
    def etag(buf):
        h = hasher()
        for chunk in buf:
            h.update(chunk)
        return '"%s"' % h.hexdigest()
    return etag


etag_md5 = make_etag(md5)


def make_etag_crc32(hasher):
    """ Build etag function based on `hasher` algorithm and crc32.

        >>> from wheezy.http.comp import b
        >>> etag = make_etag_crc32(md5)
        >>> etag([b('test')])
        '"fece0556"'
        >>> etag([b('test')] * 2)
        '"f4ff55a8"'
    """
    def etag(buf):
        h = hasher()
        for chunk in buf:
            h.update(chunk)
        return '"%08x"' % (crc32(b(h.hexdigest())) & 0xFFFFFFFF)
    return etag


etag_md5crc32 = make_etag_crc32(md5)


class NotModifiedResponse(object):
    """ Not modified cachable response.
    """

    status_code = 304

    def __init__(self, response):
        """
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response = NotModifiedResponse(response)
            >>> response.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
            ('Cache-Control', 'private')]
        """
        self.headers = [h for h in response.headers
                        if h[0] != 'Content-Length']

    def __call__(self, start_response):
        """
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response = NotModifiedResponse(response)
            >>> response.status_code
            304
            >>> status = None
            >>> headers = None
            >>> def start_response(s, h):
            ...     global status
            ...     global headers
            ...     status = s
            ...     headers = h
            >>> result = response(start_response)
            >>> assert result == []
            >>> status
            '304 Not Modified'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
            ('Cache-Control', 'private')]
        """
        start_response('304 Not Modified', self.headers)
        return []


class CacheableResponse(object):
    """ Cachable response.
    """

    status_code = 200
    last_modified = None
    etag = None

    def __init__(self, response):
        """
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.headers.append(('Set-Cookie', 'x'))
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
            >>> assert ntob('Hello', 'utf-8') in response.buffer
        """
        def capture_headers(status, headers):
            self.headers = [h for h in headers if h[0] != 'Set-Cookie']
        self.buffer = tuple(response(capture_headers))
        cache_policy = response.cache_policy
        if cache_policy:
            self.last_modified = cache_policy.modified
            self.etag = cache_policy.http_etag

    def __call__(self, start_response):
        """
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response.status_code
            200
            >>> status = None
            >>> headers = None
            >>> def start_response(s, h):
            ...     global status
            ...     global headers
            ...     status = s
            ...     headers = h
            >>> result = response(start_response)
            >>> assert ntob('Hello', 'utf-8') in result
            >>> status
            '200 OK'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
        """
        start_response('200 OK', self.headers)
        return self.buffer
