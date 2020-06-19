
""" ``comp`` module.
"""

import sys


PY3 = sys.version_info[0] >= 3

if PY3:  # pragma: nocover
    from io import BytesIO
    bytes_type = bytes
    str_type = str

    def ntob(n, encoding):
        """ Converts native string to bytes
        """
        return n.encode(encoding)

    def bton(b, encoding):
        """ Converts bytes to native string
        """
        return b.decode(encoding)

    def ntou(n, encoding):  # noqa
        """ Converts native to unicode string
        """
        return n

else:  # pragma: nocover
    from cStringIO import StringIO as BytesIO  # noqa
    bytes_type = str
    str_type = unicode  # noqa: F821

    def ntob(n, encoding):  # noqa
        """ Converts native string to bytes
        """
        return n

    def bton(b, encoding):  # noqa
        """ Converts bytes to native string
        """
        return b

    def ntou(n, encoding):  # noqa
        """ Converts native to unicode string
        """
        return n.decode(encoding)

if PY3:  # pragma: nocover

    def n(s, encoding='latin1'):
        if isinstance(s, str_type):
            return s
        return s.decode(encoding)

    def b(s):
        """ Converts native string to bytes
        """
        return s.encode('latin1')

else:  # pragma: nocover

    def n(s, encoding='latin1'):  # noqa
        if isinstance(s, bytes_type):
            return s
        return s.encode(encoding)

    def b(s):  # noqa
        """ Converts native string to bytes
        """
        return s


if PY3:  # pragma: nocover
    def iteritems(d):
        return d.items()

    def copyitems(d):
        return list(d.items())

else:  # pragma: nocover
    def iteritems(d):  # noqa
        return d.iteritems()  # noqa: B301

    def copyitems(d):  # noqa
        return d.items()


if PY3:  # pragma: nocover
    from http.cookies import SimpleCookie
else:  # pragma: nocover
    from Cookie import SimpleCookie  # noqa


if PY3:  # pragma: nocover
    from urllib.parse import unquote
    from urllib.parse import urlencode
else:  # pragma: nocover
    from urllib import urlencode  # noqa
    try:
        # Python 2.6+
        from urlparse import unquote  # noqa
    except ImportError:  # pragma: nocover
        # Python 2.5, 2.4
        from cgi import parse_qs as _parse_qs  # noqa
        from urllib import unquote  # noqa


try:  # pragma: nocover
    # Python 2.6+
    from functools import reduce
except ImportError:  # pragma: nocover
    reduce = reduce

try:  # pragma: nocover
    # Python 2.5+
    from hashlib import md5
except ImportError:  # pragma: nocover
    from md5 import md5  # noqa

try:  # pragma: nocover
    # Python 2.5+
    partition = str.partition
except AttributeError:  # pragma: nocover
    def partition(s, sep):
        if sep in s:
            a, b = s.split(sep, 1)
            return a, sep, b
        else:
            return s, sep, ''
