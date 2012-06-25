
""" ``cache`` module
"""

from wheezy.http.response import HTTP_HEADER_CONTENT_LENGTH_ZERO


def response_cache(profile):
    """ Decorator that applies cache profile strategy to the
        wrapping handler.
    """
    def decorate(handler):
        if not profile.enabled:
            return handler

        if profile.request_vary:
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
            ('Cache-Control', 'private'), ('Content-Length', '0')]
        """
        headers = [header for header in response.headers
                   if header[0] != 'Content-Length']
        headers.append(HTTP_HEADER_CONTENT_LENGTH_ZERO)
        self.headers = headers

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
            ('Cache-Control', 'private'), ('Content-Length', '0')]
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
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
            >>> assert ntob('Hello', 'utf-8') in response.buffer
        """
        def capture_headers(status, headers):
            self.headers = headers
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
