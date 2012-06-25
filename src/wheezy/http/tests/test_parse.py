
""" Unit tests for ``wheezy.http.parse``.
"""

import unittest


class ParseMultiPartTestCase(unittest.TestCase):
    """ Test the ``parse_multipart``.
    """

    def test_parse(self):
        """ Ensure form and file data are parsed correctly.
        """
        from wheezy.http.comp import ntob
        from wheezy.http.tests import sample
        from wheezy.http.parse import parse_multipart
        fp, ctype, clength, encoding = sample.multipart()

        form, files = parse_multipart(fp, ctype, clength, encoding)

        assert ['test'] == form['name']
        f = files['file'][0]
        assert 'file' == f.name
        assert 'f.txt' == f.filename
        assert ntob('hello', encoding) == f.value


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
        } == parse_cookie('ID=1234;PREF=abc')
