
""" ``wsgi_adapter`` module.

    $ virtualenv env
    $ env/bin/easy_install wheezy.caching wheezy.http
    $ env/bin/python wsgi_adapter.py
"""

from wheezy.caching import MemoryCache
from wheezy.http import CacheProfile
from wheezy.http import HTTPCachePolicy
from wheezy.http import WSGIApplication
from wheezy.http import bootstrap_http_defaults
from wheezy.http.comp import b
from wheezy.http.middleware import environ_cache_adapter_middleware_factory
from wheezy.http.middleware import http_cache_middleware_factory
from wheezy.http.middleware import wsgi_adapter_middleware_factory


cache = MemoryCache()
cache_factory = lambda: cache
cache_profile = CacheProfile('both', duration=60)


def welcome(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    policy = HTTPCachePolicy('public')
    policy.etag('12345')
    environ['wheezy.http.cache_policy'] = policy
    environ['wheezy.http.cache_profile'] = cache_profile
    return [b('Hello World!!!')]


options = {
    'wsgi_app': welcome,
    'http_cache_factory': cache_factory
}
main = WSGIApplication([
    bootstrap_http_defaults,
    http_cache_middleware_factory,
    environ_cache_adapter_middleware_factory,
    wsgi_adapter_middleware_factory
], options)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    try:
        print('Visit http://localhost:8080/')
        make_server('', 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print('\nThanks!')
