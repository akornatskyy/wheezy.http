
""" Unit tests for ``wheezy.http.parse``.
"""

import unittest


class ParseQSTestCase(unittest.TestCase):
    """ Test the ``parse_qss``.
    """

    def test_parse(self):
        """ Ensure query string is parsed correctly.
        """
        from wheezy.http.parse import parse_qs
        for s, e in (
                ('', {'': ['']}),
                ('&', {'': ['', '']}),
                ('&&', {'': ['', '', '']}),
                ('=', {'': ['']}),
                ('=a', {'': ['a']}),
                ('a', {'a': ['']}),
                ('a=', {'a': ['']}),
                ('a=', {'a': ['']}),
                ('&a=b', {'': [''], 'a': ['b']}),
                ('a=a+b&b=b+c', {'a': ['a b'], 'b': ['b c']}),
                ('a=1&a=2', {'a': ['1', '2']}),
                ('a+=', {'a ': ['']}),
                ('a%20=', {'a ': ['']}),
                ('a=a%20b', {'a': ['a b']}),
                ('a=1,2,3', {'a': ['1', '2', '3']}),
                ('a=1,2&b=3,4', {'a': ['1', '2'], 'b': ['3', '4']})):
            assert e == parse_qs(s)


class ParseMultiPartTestCase(unittest.TestCase):
    """ Test the ``parse_multipart``.
    """

    def test_parse(self):
        """ Ensure form and file data are parsed correctly.
        """
        from wheezy.http.comp import ntob
        from wheezy.http.tests import sample
        from wheezy.http.parse import parse_multipart

        environ = {}
        sample.multipart(environ)

        form, files = parse_multipart(
            environ['wsgi.input'],
            environ['CONTENT_TYPE'],
            environ['CONTENT_LENGTH'],
            'utf-8')

        assert ['test'] == form['name']
        f = files['file'][0]
        assert 'file' == f.name
        assert 'f.txt' == f.filename
        assert ntob('hello', 'utf-8') == f.value


class ParseCookieTestCase(unittest.TestCase):
    """ Test the ``parse_cookie``.
    """

    def test_parse(self):
        """ Ensure cookies are parsed correctly.
        """
        from wheezy.http.parse import parse_cookie

        assert {
            'PREF': 'abc',
            'ID': '1234'
        } == parse_cookie('ID=1234; PREF=abc')
