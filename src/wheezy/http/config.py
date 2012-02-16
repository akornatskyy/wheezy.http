
""" ``config`` module.
"""


def bootstrap_http_defaults(options):
    """ Bootstraps http default options.
    """
    options.setdefault('ENCODING', 'UTF-8')
    options.setdefault('CONTENT_TYPE', 'text/html; charset=UTF-8')
    options.setdefault('MAX_CONTENT_LENGTH', 4 * 1024 * 1024)
    # ENVIRON_HTTPS:
    # 'wsgi.url_scheme', 'HTTPS', 'HTTP_X_FORWARDED_PROTO',
    # 'SERVER_PORT_SECURE'
    options.setdefault('ENVIRON_HTTPS', 'wsgi.url_scheme')
    # ENVIRON_HTTPS_VALUE:
    # 'https', 'on', '1'
    options.setdefault('ENVIRON_HTTPS_VALUE', 'https')
    # ENVIRON_HOST:
    # 'HTTP_HOST', 'HTTP_X_FORWARDED_HOST'
    options.setdefault('ENVIRON_HOST', 'HTTP_HOST')
    # ENVIRON_REMOTE_ADDR:
    # 'REMOTE_ADDR', 'HTTP_X_FORWARDED_FOR'
    options.setdefault('ENVIRON_REMOTE_ADDR', 'REMOTE_ADDR')
    options.setdefault('HTTP_COOKIE_DOMAIN', None)
    options.setdefault('HTTP_COOKIE_SECURE', False)
    options.setdefault('HTTP_COOKIE_HTTPONLY', False)
    return None
