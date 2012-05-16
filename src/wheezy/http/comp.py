
""" ``comp`` module.
"""

import sys


PY3 = sys.version_info[0] >= 3

if PY3:  # pragma: nocover
    from io import BytesIO
    bytes_type = bytes
    str_type = str

    def n(s, encoding='latin1'):
        if isinstance(s, str_type):
            return s
        return s.decode(encoding)

    def ntob(n, encoding):
        """ Converts native string to bytes
        """
        return n.encode(encoding)

    def bton(b, encoding):
        """ Converts bytes to native string
        """
        return b.decode(encoding)

    b = lambda s: s.encode('latin1')

else:  # pragma: nocover
    from cStringIO import StringIO as BytesIO
    bytes_type = str
    str_type = unicode

    def n(s, encoding='latin1'):
        if isinstance(s, bytes_type):
            return s
        return s.encode(encoding)

    def ntob(n, encoding):
        """ Converts native string to bytes
        """
        return n

    def bton(b, encoding):
        """ Converts bytes to native string
        """
        return b

    b = lambda s: s


if PY3:  # pragma: nocover
    iteritems = lambda d: d.items()
    copyitems = lambda d: list(d.items())
else:  # pragma: nocover
    iteritems = lambda d: d.iteritems()
    copyitems = lambda d: d.items()


if PY3:  # pragma: nocover
    from http.cookies import SimpleCookie
else:  # pragma: nocover
    from Cookie import SimpleCookie


if PY3:  # pragma: nocover
    from urllib.parse import urlencode
    from urllib.parse import parse_qs as _parse_qs

    def parse_qs(qs, encoding):
        return _parse_qs(qs, keep_blank_values=True, encoding=encoding)
else:  # pragma: nocover
    from urllib import urlencode
    try:
        # Python 2.6+
        from urlparse import parse_qs as _parse_qs
    except ImportError:  # pragma: nocover
        # Python 2.5, 2.4
        from cgi import parse_qs as _parse_qs

    def parse_qs(qs, encoding):
        return _parse_qs(qs, keep_blank_values=True)


try:  # pragma: nocover
    # Python 2.6+
    from functools import reduce
except ImportError:  # pragma: nocover
    reduce = reduce
