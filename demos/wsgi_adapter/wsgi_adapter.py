""" ``wsgi_adapter`` module.

    $ virtualenv env
    $ env/bin/easy_install wheezy.caching wheezy.http
    $ env/bin/python wsgi_adapter.py
"""

from datetime import datetime, timedelta

from wheezy.caching import MemoryCache

from wheezy.http import CacheProfile, WSGIApplication, bootstrap_http_defaults
from wheezy.http.cache import etag_md5crc32, wsgi_cache
from wheezy.http.comp import b
from wheezy.http.middleware import (
    environ_cache_adapter_middleware_factory,
    http_cache_middleware_factory,
    wsgi_adapter_middleware_factory,
)

cache = MemoryCache()
cache_profile = CacheProfile(
    "both",
    enabled=True,
    etag_func=etag_md5crc32,
    duration=timedelta(seconds=10),
)


@wsgi_cache(profile=cache_profile)
def welcome(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [
        b("Hello World!!!\nThe time is %s" % datetime.now().isoformat(" "))
    ]


options = {"wsgi_app": welcome, "http_cache": cache}
main = WSGIApplication(
    [
        bootstrap_http_defaults,
        http_cache_middleware_factory,
        environ_cache_adapter_middleware_factory,
        wsgi_adapter_middleware_factory,
    ],
    options,
)


if __name__ == "__main__":
    from wsgiref.handlers import BaseHandler
    from wsgiref.simple_server import make_server

    try:
        print("Visit http://localhost:8080/")
        BaseHandler.http_version = "1.1"
        make_server("", 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print("\nThanks!")
