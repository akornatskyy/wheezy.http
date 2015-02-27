
""" ``guestbook`` module.
"""

from datetime import datetime
from datetime import timedelta

from wheezy.core.collections import last_item_adapter

from wheezy.caching.memory import MemoryCache
from wheezy.caching.patterns import CacheDependency
from wheezy.http import CacheProfile
from wheezy.http import HTTPResponse
from wheezy.http import WSGIApplication
from wheezy.http import accept_method
from wheezy.http import bootstrap_http_defaults
from wheezy.http import none_cache_profile
from wheezy.http import not_found
from wheezy.http import redirect
from wheezy.http.cache import etag_md5crc32
from wheezy.http.cache import response_cache
from wheezy.http.comp import ntou
from wheezy.http.middleware import http_cache_middleware_factory
from wheezy.http.transforms import gzip_transform
from wheezy.http.transforms import response_transforms


cache = MemoryCache()
cache_dependency = CacheDependency(cache)
cache_profile = CacheProfile('public',
                             enabled=True,
                             etag_func=etag_md5crc32,
                             duration=timedelta(minutes=1),
                             http_max_age=0,
                             vary_environ=['HTTP_ACCEPT_ENCODING'],
                             http_vary=['Accept-Encoding'])
gz = gzip_transform(compress_level=9, min_length=250)

greetings = []


class Greeting(object):
    author = ''
    message = ''

    def __init__(self):
        self.date = datetime.now()


@accept_method('GET')
@response_cache(profile=cache_profile)
@response_transforms(gz)
def welcome(request):
    response = HTTPResponse()
    response.write("""<html><body>
<form action='/add' method='post'>
    <p><label for='author'>Author:</label>
        <input name='author' type='text'/></p>
    <p><textarea name='message' rows='7' cols='40'></textarea></p>
    <p><input type='submit' value='Leave Message'></p>
</form>""")
    for greeting in greetings:
        response.write('<p>On %s, <b>%s</b> wrote:' % (
                       greeting.date.strftime('%m/%d/%Y %I:%M %p'),
                       greeting.author or 'anonymous'))
        response.write('<blockquote>%s</blockquote></p>' %
                       greeting.message.replace('\n', '<br/>'))
    response.write('</body></html>')
    response.cache_dependency = ('greetings',)
    return response


@accept_method(('GET', 'POST'))
@response_cache(profile=none_cache_profile)
def add_record(request):
    if request.method == 'POST':
        form = last_item_adapter(request.form)
    else:
        form = last_item_adapter(request.query)
    greeting = Greeting()
    greeting.author = ntou(form['author'].strip(), request.encoding)
    m = ntou(form['message'].replace('\r', '').strip(), request.encoding)
    greeting.message = m
    greetings.insert(0, greeting)
    cache_dependency.delete('greetings')
    return redirect('http://' + request.host + '/')


def router_middleware(request, following):
    path = request.path
    if path == '/':
        response = welcome(request)
    elif path.startswith('/add'):
        response = add_record(request)
    else:
        response = not_found()
    return response


options = {
    'http_cache': cache
}
main = WSGIApplication([
    bootstrap_http_defaults,
    http_cache_middleware_factory,
    lambda ignore: router_middleware
], options)


if __name__ == '__main__':
    from wsgiref.handlers import BaseHandler
    from wsgiref.simple_server import make_server
    try:
        print('Visit http://localhost:8080/')
        BaseHandler.http_version = '1.1'
        make_server('', 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print('\nThanks!')
