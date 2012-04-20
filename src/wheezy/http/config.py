
""" ``config`` module.
"""


def bootstrap_http_defaults(options):
    """ Bootstraps http default options.
    """
    options.setdefault('ENCODING', 'UTF-8')
    options.setdefault('MAX_CONTENT_LENGTH', 4 * 1024 * 1024)
    options.setdefault('HTTP_COOKIE_DOMAIN', None)
    options.setdefault('HTTP_COOKIE_SECURE', False)
    options.setdefault('HTTP_COOKIE_HTTPONLY', False)
    return None
