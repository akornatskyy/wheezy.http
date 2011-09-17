
""" ``sample`` module.
"""


def request(environ):
    environ.setdefault('REQUEST_METHOD', 'GET')
    environ.setdefault('SCRIPT_NAME', '')
    environ.setdefault('PATH_INFO', '')
    environ.setdefault('QUERY_STRING', '')
    environ.setdefault('SERVER_NAME', 'localhost')
    environ.setdefault('SERVER_PORT', '8080')
    environ.setdefault('SERVER_PROTOCOL', 'HTTP/1.1')
    environ.setdefault('wsgi.url_scheme', 'http')


def request_headers(environ):
    environ.setdefault('HTTP_ACCEPT', 'text/plain')
    environ.setdefault(
            'HTTP_ACCEPT_CHARSET',
            'ISO-8859-1,utf-8;q=0.7,*;q=0.3'
    )
    environ.setdefault(
            'HTTP_ACCEPT_ENCODING',
            'gzip,deflate,sdch'
    )
    environ.setdefault('HTTP_ACCEPT_LANGUAGE', 'en-US,en;q=0.8')
    environ.setdefault('HTTP_CONNECTION', 'keep-alive')
    environ.setdefault('HTTP_HOST', 'localhost:8080')
    environ.setdefault(
            'HTTP_USER_AGENT',
            'Mozilla/5.0 (X11; Linux i686)'
    )


def request_multipart(environ):
    fp, ct, cl, enc = multipart()
    environ['wsgi.input'] = fp
    environ['CONTENT_TYPE'] = ct
    environ['CONTENT_LENGTH'] = cl


def request_urlencoded(environ):
    from wheezy.http.p2to3 import BytesIO
    body = urlencoded()
    environ['wsgi.input'] = BytesIO(body.encode('utf-8'))
    environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    environ['CONTENT_LENGTH'] = str(len(body))


def multipart():
    from wheezy.http.p2to3 import BytesIO
    body = """----A
Content-Disposition: form-data; name="name"

test
----A
Content-Disposition: form-data; name="file"; filename="f.txt"
Content-Type: text/plain

hello
----A--"""
    return (BytesIO(body.encode('utf-8')),
            'multipart/form-data; boundary=--A',
            str(len(body)),
            'utf-8')


def urlencoded():
    return "greeting=Hello+World&greeting=Hallo+Welt&lang=en"
