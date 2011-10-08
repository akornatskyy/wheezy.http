
""" ``comp`` module.
"""

import sys


PY3 = sys.version_info[0] >= 3

if PY3:  # pragma: nocover
    from io import BytesIO

    def ntob(n, encoding):
        """ Converts native string to bytes
        """
        return n.encode(encoding)

    def ntou(n, encoding):
        """ Converts native string to unicode
        """
        return n

    def bton(b, encoding):
        """ Converts bytes to native string
        """
        return b.decode(encoding)

    chr = lambda i: bytes([i])
    ord = lambda b: b
    b = lambda s: s.encode('latin1')
    n = lambda s: s.decode('latin1')

else:  # pragma: nocover
    from cStringIO import StringIO as BytesIO

    def ntob(n, encoding):
        """ Converts native string to bytes
        """
        return n

    def ntou(n, encoding):
        """ Converts native string to unicode
        """
        return n.decode(encoding)

    def bton(b, encoding):
        """ Converts bytes to native string
        """
        return b

    chr = chr
    ord = ord
    b = lambda s: s
    n = lambda s: s


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
    from urllib.parse import parse_qs as _parse_qs

    def parse_qs(qs, encoding):
        return _parse_qs(qs, keep_blank_values=True, encoding=encoding)
else:  # pragma: nocover
    try:
        # Python 2.6+
        from urlparse import parse_qs as _parse_qs
    except ImportError:  # pragma: nocover
        # Python 2.5, 2.4
        from cgi import parse_qs as _parse_qs

    def parse_qs(qs, encoding):
        return _parse_qs(qs, keep_blank_values=True)


# Hash functions
try:  # pragma: nocover
    # Python 2.5+
    from hashlib import md5
    from hashlib import sha1
    digest_size = lambda d: d().digest_size
except ImportError:  # pragma: nocover
    import md5
    import sha as sha1
    digest_size = lambda d: d.digest_size


# Encryption interface
block_size = None
encrypt = None
decrypt = None

# Supported cyphers
aes128 = None
aes192 = None
aes256 = None

# Python Cryptography Toolkit (pycrypto)
try:  # pragma: nocover
    from Crypto.Cipher import AES

    # pycrypto interface
    block_size = lambda c: c.block_size
    encrypt = lambda c, v: c.encrypt(v)
    decrypt = lambda c, v: c.decrypt(v)

    # suppored cyphers
    def aes(key, key_size=32):
        key = key[-key_size:]
        iv = key[-16:]
        return lambda: AES.new(key, AES.MODE_CBC, iv)

    aes128 = lambda key: aes(key, 16)
    aes192 = lambda key: aes(key, 24)
    aes256 = lambda key: aes(key, 32)
except ImportError:  # pragma: nocover
    # TODO: add fallback to other encryption providers
    pass
