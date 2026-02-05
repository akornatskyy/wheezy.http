from wheezy.http import (
    WSGIApplication,
    accept_method,
    bad_request,
    bootstrap_http_defaults,
    json_response,
    not_found,
)


@accept_method("POST")
def welcome(request):
    if not request.ajax:
        return bad_request()
    name = request.form["name"][0]
    return json_response({"message": "Welcome, %s!" % name})


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
