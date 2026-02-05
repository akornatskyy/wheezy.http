import inspect
import unittest
from unittest.mock import Mock

from wheezy.http.application import WSGIApplication, wrap_middleware


class WrapMiddlewareTestCase(unittest.TestCase):
    """Test the ``wrap_middleware``."""

    def test_callable(self):
        """Ensure ``wrap_middleware`` returns a valid
        callable for adapted middleware.
        """
        try:
            spec = inspect.getfullargspec(wrap_middleware)
            self.assertEqual(["following", "func"], spec.args)
            self.assertEqual(None, spec.varargs)
            self.assertEqual(None, spec.varkw)
            self.assertEqual(None, spec.defaults)

            def middleware(request, following):
                assert "request" == request
                assert "following" == following
                return "response"

            adapted_middleware = wrap_middleware("following", middleware)
            spec = inspect.getfullargspec(adapted_middleware)
            self.assertEqual(["request"], spec.args)
            assert "response" == adapted_middleware("request")
        except TypeError:  # pragma: nocover
            pass


class WSGIApplicationInitTestCase(unittest.TestCase):
    """Test the ``WSGIApplication.__init__``."""

    def test_options_and_encoding(self):
        """Ensure options and encoding are set."""
        options = {"ENCODING": "UTF-8"}
        mock_factory_a = Mock(return_value="a")

        app = WSGIApplication(middleware=[mock_factory_a], options=options)

        self.assertEqual(options, app.options)
        self.assertEqual("UTF-8", app.encoding)

    def test_middleware_factory(self):
        """Ensure each middleware factory is called with ``options``."""
        options = {"ENCODING": "UTF-8"}
        mock_factory_a = Mock(return_value="a")
        mock_factory_b = Mock(return_value="b")

        WSGIApplication(
            middleware=[mock_factory_a, mock_factory_b], options=options
        )

        mock_factory_a.assert_called_once_with(options)
        mock_factory_b.assert_called_once_with(options)

    def test_wrap_middleware(self):
        """Ensure middleware is stacked in order."""
        options = {"ENCODING": "UTF-8"}
        mock_middleware_a = Mock()
        mock_factory_a = Mock(return_value=mock_middleware_a)
        mock_middleware_b = Mock()
        mock_factory_b = Mock(return_value=mock_middleware_b)

        app = WSGIApplication(
            middleware=[mock_factory_a, mock_factory_b], options=options
        )
        app.middleware("request")
        assert mock_middleware_a.called
        assert not mock_middleware_b.called
        request, following = mock_middleware_a.call_args[0]
        assert "request" == request

        mock_middleware_a.reset_mock()
        following(request)
        assert not mock_middleware_a.called
        assert mock_middleware_b.called
        request, following = mock_middleware_b.call_args[0]
        assert "request" == request
        assert following is None


class WSGIApplicationCallTestCase(unittest.TestCase):
    """Test the ``WSGIApplication.__call__``."""

    def test_not_found(self):
        """If middleware returns ``None`` response replace it
        with ``not_found``.
        """
        environ = {"REQUEST_METHOD": "GET"}
        options = {"ENCODING": "UTF-8"}
        mock_middleware = Mock(return_value=None)
        mock_factory = Mock(return_value=mock_middleware)
        mock_start_response = Mock()

        app = WSGIApplication(middleware=[mock_factory], options=options)

        app(environ, mock_start_response)

        assert mock_middleware.called
        request, following = mock_middleware.call_args[0]
        assert environ == request.environ
        assert options["ENCODING"] == request.encoding
        assert options == request.options
        assert mock_start_response.called
        status, headers = mock_start_response.call_args[0]
        assert "404 Not Found" == status

    def test_middleware_response(self):
        """Middleware response is returned as WSGI application
        response.
        """
        environ = {"REQUEST_METHOD": "GET"}
        options = {"ENCODING": "UTF-8"}
        mock_response = Mock(return_value="result")
        mock_middleware = Mock(return_value=mock_response)
        mock_factory = Mock(return_value=mock_middleware)
        mock_start_response = Mock()

        app = WSGIApplication(middleware=[mock_factory], options=options)

        result = app(environ, mock_start_response)
        mock_response.assert_called_once_with(mock_start_response)
        assert "result" == result

    def test_middleware_call_order(self):
        """Middleware is called is exact order."""
        call_order = []

        def named_middleware(name):
            def middleware(request, following):
                call_order.append(name)
                if following:
                    return following(request)
                else:
                    return None

            return middleware

        environ = {"REQUEST_METHOD": "GET"}
        options = {"ENCODING": "UTF-8"}
        mock_start_response = Mock()

        app = WSGIApplication(
            middleware=[
                Mock(return_value=named_middleware(1)),
                Mock(return_value=named_middleware(2)),
                Mock(return_value=named_middleware(3)),
            ],
            options=options,
        )

        app(environ, mock_start_response)
        assert [1, 2, 3] == call_order
