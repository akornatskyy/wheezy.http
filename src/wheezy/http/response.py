""" ``response`` module.
"""

from wheezy.core.json import json_encode

# see http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
# see http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
HTTP_STATUS = {
    # Informational
    100: "100 Continue",
    101: "101 Switching Protocols",
    # Successful
    200: "200 OK",
    201: "201 Created",
    202: "202 Accepted",
    203: "203 Non-Authoritative Information",
    204: "204 No Content",
    205: "205 Reset Content",
    206: "206 Partial Content",
    207: "207 Multi-Status",
    # Redirection
    300: "300 Multiple Choices",
    301: "301 Moved Permanently",
    302: "302 Found",
    303: "303 See Other",
    304: "304 Not Modified",
    305: "305 Use Proxy",
    307: "307 Temporary Redirect",
    # Client Error
    400: "400 Bad Request",
    401: "401 Unauthorized",
    402: "402 Payment Required",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    406: "406 Not Acceptable",
    407: "407 Proxy Authentication Required",
    408: "408 Request Timeout",
    409: "409 Conflict",
    410: "410 Gone",
    411: "411 Length Required",
    412: "412 Precondition Failed",
    413: "413 Request Entity Too Large",
    414: "414 Request-Uri Too Long",
    415: "415 Unsupported Media Type",
    416: "416 Requested Range Not Satisfiable",
    417: "417 Expectation Failed",
    # Server Error
    500: "500 Internal Server Error",
    501: "501 Not Implemented",
    502: "502 Bad Gateway",
    503: "503 Service Unavailable",
    504: "504 Gateway Timeout",
    505: "505 Http Version Not Supported",
}

HTTP_HEADER_CACHE_CONTROL_DEFAULT = ("Cache-Control", "private")


def permanent_redirect(absolute_url):
    """Shortcut function to return permanent redirect response.

    The HTTP response status code 301 Moved Permanently is used for
    permanent redirection.
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 301)
    return response


def redirect(absolute_url):
    """Shortcut function to return redirect response.

    The HTTP response status code 302 Found is a common way of
    performing a redirection.
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 302)
    return response


found = redirect


def see_other(absolute_url):
    """Shortcut function to return see other redirect response.

    The HTTP response status code 303 See Other is the correct manner
    in which to redirect web applications to a new URI, particularly
    after an HTTP POST has been performed.

    This response indicates that the correct response can be found
    under a different URI and should be retrieved using a GET method.
    The specified URI is not a substitute reference for the original
    resource.
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 303)
    return response


def temporary_redirect(absolute_url):
    """Shortcut function to return temporary redirect response.

    In this occasion, the request should be repeated with another
    URI, but future requests can still use the original URI.
    In contrast to 303, the request method should not be changed
    when reissuing the original request. For instance, a POST
    request must be repeated using another POST request.
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 307)
    return response


def ajax_redirect(absolute_url):
    """Shortcut function to return ajax redirect response.

    Browsers incorrectly handle redirect response to ajax
    request, so we return status code 207 that javascript
    is capable to receive and process browser redirect.

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
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 207)
    return response


bad_request = error400 = lambda: http_error(400)
unauthorized = error401 = lambda: http_error(401)
forbidden = error403 = lambda: http_error(403)
not_found = error404 = lambda: http_error(404)
method_not_allowed = error405 = lambda: http_error(405)
internal_error = error500 = lambda: http_error(500)


def http_error(status_code):
    """Shortcut function to return a response with
    given status code.
    """
    assert status_code >= 400 and status_code <= 505
    response = HTTPResponse()
    response.status_code = status_code
    return response


def json_response(obj, encoding="UTF-8"):
    """Returns json response."""
    response = HTTPResponse("application/json; charset=" + encoding, encoding)
    response.write_bytes(json_encode(obj).encode(encoding))
    return response


class HTTPResponse(object):
    """HTTP response.

    Response headers Content-Length and Cache-Control
    must not be set by user code directly. Use
    ``HTTPCachePolicy`` instead (``HTTPResponse.cache``).
    """

    status_code = 200
    cache_policy = None
    cache_profile = None

    def __init__(
        self, content_type="text/html; charset=UTF-8", encoding="UTF-8"
    ):
        """Initializes HTTP response."""
        self.content_type = content_type
        self.encoding = encoding
        self.headers = [("Content-Type", content_type)]
        self.buffer = []
        self.cookies = []
        self.cache_dependency = []

    def get_status(self):
        """Returns a string that describes the specified
        HTTP status code.
        """
        return HTTP_STATUS[self.status_code]

    status = property(get_status)

    def redirect(self, absolute_url, status_code=302):
        """Redirect response to ``absolute_url`` and sets
        ``status_code``.
        """
        self.status_code = status_code
        self.headers.append(("Location", absolute_url))

    def write(self, chunk):
        """Applies encoding to ``chunk`` and append it to response
        buffer.
        """
        self.buffer.append(chunk.encode(self.encoding))

    def write_bytes(self, chunk):
        """Appends chunk it to response buffer. No special checks performed.
        It must be valid object for WSGI response.
        """
        self.buffer.append(chunk)

    def __call__(self, start_response):
        """WSGI call processing."""
        headers = self.headers
        append = headers.append
        cache_policy = self.cache_policy
        if cache_policy:
            cache_policy.extend(headers)
        else:
            append(HTTP_HEADER_CACHE_CONTROL_DEFAULT)
        if self.cookies:
            encoding = self.encoding
            for cookie in self.cookies:
                append(cookie.http_set_cookie(encoding))
        buffer = self.buffer
        append(("Content-Length", str(sum([len(chunk) for chunk in buffer]))))
        start_response(HTTP_STATUS[self.status_code], headers)
        return buffer
