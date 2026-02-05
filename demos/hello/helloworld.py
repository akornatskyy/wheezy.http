from wheezy.http import (
    HTTPResponse,
    WSGIApplication,
    bootstrap_http_defaults,
    not_found,
)


def welcome(request):
    response = HTTPResponse()
    response.write("Hello World!!!")
    return response


def router_middleware(request, following):
    path = request.path
    if path == "/":
        response = welcome(request)
    else:
        response = not_found()
    return response


options = {}
main = WSGIApplication(
    [bootstrap_http_defaults, lambda ignore: router_middleware], options
)


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    try:
        print("Visit http://localhost:8080/")
        make_server("", 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print("\nThanks!")
