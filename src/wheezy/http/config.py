
""" ``config`` module.
"""

from sys import modules


ENCODING = 'utf-8'
CONTENT_TYPE = 'text/html'

MAX_CONTENT_LENGTH = 4 * 1024 * 1024

ENVIRON_HTTPS = 'wsgi.url_scheme'
#ENVIRON_HTTPS = 'HTTPS'
#ENVIRON_HTTPS = 'X-FORWARDED-PROTO'
#ENVIRON_HTTPS = 'SERVER_PORT_SECURE'

ENVIRON_HTTPS_VALUE = 'https'
#ENVIRON_HTTPS_VALUE = 'on'
#ENVIRON_HTTPS_VALUE = '1'

ENVIRON_HOST = 'HTTP_HOST'
#ENVIRON_HOST = 'HTTP_X_FORWARDED_HOST'

ENVIRON_REMOTE_ADDR = 'REMOTE_ADDR'
#ENVIRON_REMOTE_ADDR = 'HTTP_X_FORWARDED_FOR'

HTTP_COOKIE_DOMAIN = None
HTTP_COOKIE_SECURE = False
HTTP_COOKIE_HTTPONLY = False

CRYPTO_VALIDATION_KEY = ''
CRYPTO_ENCRYPTION_KEY = ''


class Config(object):
    """
        >>> c = Config(options={'TEST': True, 'ENCODING': 'ascii'})
        >>> c.TEST
        True

        ``options`` override ``master``.

        >>> c.ENCODING
        'ascii'

        If option is not defined it takes from ``master``.

        >>> c = Config()
        >>> c.ENCODING
        'utf-8'

        Configs can be nested

        >>> m = Config(dict(B='b'))
        >>> c = Config(dict(A='a'), master=m)
        >>> c.B
        'b'

        if ``options`` is an instance of ``Config`` than use
        borg pattern to share state.

        >>> options = Config(dict(A='a'))
        >>> c = Config(options)
        >>> c.A
        'a'
    """

    def __init__(self, options=None, master=None):
        if isinstance(options, Config):
            self.__dict__ = options.__dict__
        else:
            self.options = options or {}
            self.master = master or modules[self.__module__]

    def __getattr__(self, name):
        if name in self.options:
            val = self.options[name]
        else:
            val = getattr(self.master, name)
        setattr(self, name, val)
        return val
