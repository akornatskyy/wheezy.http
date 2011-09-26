
""" ``guestbook`` module.
"""

from datetime import datetime

from wheezy.http.request import HttpRequest
from wheezy.http.response import HttpResponse
from wheezy.http.response import redirect

greetings = []


class Greeting:
     author = ''
     message = ''

     def __init__(self):
       self.date = datetime.now()


def welcome(request):
    response = HttpResponse()
    response.write("""<html><body>
<form action='/add' method='post'>
    <p><label for='author'>Author:</label>
        <input name='author' type='text'/></p>
    <p><textarea name='message' rows='7' cols='40'></textarea></p>
    <p><input type='submit' value='Leave Message'></p>
</form>""")
    for greeting in greetings:
        response.write('<p>On %s, <b>%s</b> wrote:'
            % (greeting.date.strftime('%m/%d/%Y %I:%M %p'),
                greeting.author or 'anonymous'))
        response.write('<blockquote>%s</blockquote></p>'
                % greeting.message)
    response.write('</body></html>')
    return response


def add_record(request):
    if request.METHOD == 'POST':
        form = request.FORM
    else:
        form = request.QUERY
    greeting = Greeting()
    greeting.author = form['author'].strip()
    greeting.message = form['message'].strip()
    greetings.insert(0, greeting)

    return redirect('http://' + request.HOST + '/')


def main(environ, start_response):
    request = HttpRequest(environ)
    if request.PATH == '/add':
        response = add_record(request)
    else:
        response = welcome(request)
    return response(start_response)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    try:
        print('Visit http://localhost:8080/')
        make_server('', 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print('\nThanks!')
