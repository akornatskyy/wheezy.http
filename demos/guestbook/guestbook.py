
""" ``guestbook`` module.
"""

from datetime import datetime

from wheezy.core.collections import last_item_adapter

from wheezy.http import HTTPResponse
from wheezy.http import WSGIApplication
from wheezy.http import bootstrap_http_defaults
from wheezy.http import not_found
from wheezy.http import redirect


greetings = []


class Greeting(object):
    author = ''
    message = ''

    def __init__(self):
        self.date = datetime.now()


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
    return response


def add_record(request):
    if request.method == 'POST':
        form = last_item_adapter(request.form)
    else:
        form = last_item_adapter(request.query)
    greeting = Greeting()
    greeting.author = form['author'].strip()
    m = form['message'].replace('\r', '').strip()
    greeting.message = m
    greetings.insert(0, greeting)
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


options = {}
main = WSGIApplication([
    bootstrap_http_defaults,
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
