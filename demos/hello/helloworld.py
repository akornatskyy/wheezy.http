
""" ``helloworld`` module.
"""

from wheezy.http import HTTPRequest
from wheezy.http import HTTPResponse
from wheezy.http import WSGIApplication
from wheezy.http import not_found
from wheezy.http.config import bootstrap_http_defaults


options = {}
bootstrap_http_defaults(options)


def welcome(request):
    response = HTTPResponse()
    response.write('Hello World!!!')
    return response


def router_middleware(request, following):
    path = request.path
    if path == '/':
        response = welcome(request)
    else:
        response = not_found()
    return response


main = WSGIApplication([
    lambda ignore: router_middleware
], options)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    try:
        print('Visit http://localhost:8080/')
        make_server('', 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print('\nThanks!')
