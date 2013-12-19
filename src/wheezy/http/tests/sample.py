
""" ``sample`` module.
"""

from wheezy.http.comp import BytesIO
from wheezy.http.comp import ntob


def multipart(environ):  # pragma: nocover
    """ Setup multipart/form-data request.
    """
    body = """----A
Content-Disposition: form-data; name="name"

test
----A
Content-Disposition: form-data; name="file"; filename="f.txt"
Content-Type: text/plain

hello
----A--"""
    environ['wsgi.input'] = BytesIO(ntob(body, 'utf-8'))
    environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=--A'
    environ['CONTENT_LENGTH'] = str(len(body))


def urlencoded(environ):  # pragma: nocover
    """ Setup application/x-www-form-urlencoded request.
    """
    body = 'greeting=Hello+World&greeting=Hallo+Welt&lang=en'
    environ['wsgi.input'] = BytesIO(ntob(body, 'utf-8'))
    environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    environ['CONTENT_LENGTH'] = str(len(body))


def json(environ):  # pragma: nocover
    """ Setup application/json request.
    """
    body = '{}'
    environ['wsgi.input'] = BytesIO(ntob(body, 'utf-8'))
    environ['CONTENT_TYPE'] = 'application/json'
    environ['CONTENT_LENGTH'] = str(len(body))


def unknown(environ):  # pragma: nocover
    """ Setup unknown request.
    """
    body = ''
    environ['wsgi.input'] = BytesIO(ntob(body, 'utf-8'))
    environ['CONTENT_TYPE'] = 'application/unknown'
    environ['CONTENT_LENGTH'] = str(len(body))
