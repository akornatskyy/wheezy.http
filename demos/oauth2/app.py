"""
"""

from base64 import b64encode
from hashlib import md5
from time import time
from uuid import uuid4

from wheezy.core.collections import attrdict
from wheezy.core.comp import json_loads
from wheezy.core.comp import urlencode
from wheezy.core.httpclient import HTTPClient
from wheezy.core.uuid import shrink_uuid
from wheezy.http import HTTPResponse
from wheezy.http import WSGIApplication
from wheezy.http import bootstrap_http_defaults
from wheezy.http import not_found
from wheezy.http import redirect
from wheezy.http import unauthorized
from wheezy.http.parse import parse_qs


# region: foundation

class Token(object):

    def __init__(self, name, access_token, expires_in):
        self.name = name
        self.access_token = str(access_token)
        self.expires = int(time()) + expires_in


class OAuth2Client(object):

    def __init__(self, client_id, client_secret, redirect_uri,
                 auth_uri, token_uri, scope, api_client=None,
                 response_type='code', grant_type='authorization_code',
                 name=''):
        if hasattr(scope, '__iter__'):
            scope = ' '.join(scope)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_uri = auth_uri
        self.token_uri = token_uri
        self.api_client = api_client
        self.grant_type = grant_type
        self.name = name
        self.auth_code_uri = self.auth_uri + '?' + urlencode({
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': response_type,
            'scope': scope
        }) + '&state='

    def get_auth_code_uri(self, state):
        return self.auth_code_uri + state

    def authorize(self, code):
        client = HTTPClient(self.token_uri)
        if 200 != client.post('', params={
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': self.grant_type
                }):
            return None
        m = client.json
        return Token(self.name, m.access_token, m.expires_in)

    def api(self, token):
        assert token.name == self.name
        if time() > token.expires:
            # Renew expired token
            return None
        return self.api_client(token.access_token)


# region: OAuth2 clients

def OAuth2GoogleClient(client_id, client_secret, redirect_uri, scope,
                       api_client=None):
    return OAuth2Client(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        auth_uri='https://accounts.google.com/o/oauth2/auth',
        token_uri='https://accounts.google.com/o/oauth2/token',
        api_client=api_client,
        redirect_uri=redirect_uri,
        scope=scope)


def OAuth2WindowsClient(client_id, client_secret, redirect_uri, scope,
                        api_client=None):
    return OAuth2Client(
        name='windows',
        client_id=client_id,
        client_secret=client_secret,
        auth_uri='https://login.live.com/oauth20_authorize.srf',
        token_uri='https://login.live.com/oauth20_token.srf',
        api_client=api_client,
        redirect_uri=redirect_uri,
        scope=scope)


class OAuth2FacebookClient(OAuth2Client):

    def __init__(self, client_id, client_secret, redirect_uri, scope,
                 api_client=None):
        super(OAuth2FacebookClient, self).__init__(
            name='facebook',
            client_id=client_id,
            client_secret=client_secret,
            auth_uri='https://www.facebook.com/dialog/oauth',
            token_uri='https://graph.facebook.com/oauth/access_token',
            api_client=api_client,
            redirect_uri=redirect_uri,
            scope=scope)

    def authorize(self, code):
        client = HTTPClient(self.token_uri)
        if 200 != client.post('', params={
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': self.grant_type
                }):
            return None
        m = parse_qs(client.body)
        return Token(self.name, m['access_token'][0], int(m['expires'][0]))


def OAuth2LinkedInClient(client_id, client_secret, redirect_uri, scope,
                         api_client=None):
    return OAuth2Client(
        name='linkedin',
        client_id=client_id,
        client_secret=client_secret,
        auth_uri='https://www.linkedin.com/uas/oauth2/authorization',
        token_uri='https://www.linkedin.com/uas/oauth2/accessToken',
        api_client=api_client,
        redirect_uri=redirect_uri,
        scope=scope)


class OAuth2YahooClient(OAuth2Client):

    def __init__(self, client_id, client_secret, redirect_uri,
                 api_client=None):
        super(OAuth2YahooClient, self).__init__(
            name='yahoo',
            client_id=client_id,
            client_secret=client_secret,
            auth_uri='https://api.login.yahoo.com/oauth2/request_auth',
            token_uri='https://api.login.yahoo.com/oauth2/get_token',
            api_client=api_client,
            redirect_uri=redirect_uri,
            scope='')

    def authorize(self, code):
        client = HTTPClient(self.token_uri, headers={
            'Authorization': 'Basic ' + b64encode(
                self.client_id + ':' + self.client_secret)
        })
        if 200 != client.post('', params={
                'code': code,
                'redirect_uri': self.redirect_uri,
                'grant_type': self.grant_type
                }):
            return None
        m = client.json
        return Token(self.name, m.access_token, m.expires_in)


# region: web handlers

def welcome(request):
    t = request.get_param('t')
    if t:
        t = tokens.get(t)
        if t:
            api = auth[t.name].api(t)
            m = api.userinfo()
            if not m:
                return unauthorized()
            response = HTTPResponse()
            response.write('Hello, ' + m.email)
            return response
    response = HTTPResponse()
    response.write(
        'Sign In with '
        '<a href="/oauth2/google">Google</a>, '
        '<a href="/oauth2/windows">Windows</a>, '
        '<a href="/oauth2/facebook">Facebook</a>, '
        '<a href="/oauth2/linkedin">LinkedIn</a> or '
        '<a href="/oauth2/yahoo">Yahoo</a> account')
    return response


def oauth2(request):
    if request.get_param('error'):
        return redirect('/')
    c = auth[request.path[8:]]
    code = request.get_param('code')
    if not code:
        x = shrink_uuid(uuid4())
        response = redirect(c.get_auth_code_uri(state=x))
        response.headers.append(('Set-Cookie', 'x=' + x + '; HttpOnly'))
        return response
    if request.get_param('state') != request.cookies.get('x'):
        return unauthorized()
    token = c.authorize(code)
    if not token:
        return redirect('/')
    token_id = md5(token.access_token).hexdigest()[:4]
    tokens[token_id] = token
    response = redirect('/?t=' + token_id)
    response.headers.append((
        'Set-Cookie', 'x=; Expires=Thu, 01-Jan-1970 00:00:01 GMT; HttpOnly'))
    return response


# region: API clients

class GoogleAPIClient(object):

    def __init__(self, access_token):
        self.client = HTTPClient(
            'https://www.googleapis.com',
            headers={
                'Authorization': 'Bearer ' + access_token
            })

    def userinfo(self):
        if 200 != self.client.get('/userinfo/v2/me'):
            return None
        m = self.client.json
        return attrdict(
            email=m.email
        )


class WindowsAPIClient(object):

    def __init__(self, access_token):
        self.client = HTTPClient(
            'https://apis.live.net/v5.0/',
            headers={
                'Authorization': 'Bearer ' + access_token
            })

    def userinfo(self):
        if 200 != self.client.get('me'):
            return None
        m = self.client.json
        return attrdict(
            email=m.emails.preferred
        )


class FacebookAPIClient(object):

    def __init__(self, access_token):
        self.client = HTTPClient(
            'https://graph.facebook.com/',
            headers={
                'Authorization': 'Bearer ' + access_token
            })

    def userinfo(self):
        if 200 != self.client.get('me'):
            return None
        m = json_loads(self.client.content)
        return attrdict(
            email=m['email']
        )


class LinkedInAPIClient(object):

    def __init__(self, access_token):
        self.client = HTTPClient(
            'https://api.linkedin.com/v1/',
            headers={
                'Authorization': 'Bearer ' + access_token,
                'X-Li-Format': 'json'
            })

    def userinfo(self):
        if 200 != self.client.get('people/~:(email-address)'):
            return None
        m = self.client.json
        return attrdict(
            email=m.emailAddress
        )


class YahooAPIClient(object):

    def __init__(self, access_token):
        self.client = HTTPClient(
            'https://query.yahooapis.com/v1/yql',
            headers={
                'Authorization': 'Bearer ' + access_token
            })

    def userinfo(self):
        if 200 != self.client.get('', params={
                'q': 'select * from social.profile where guid=me',
                'format': 'json'
                }):
            return None
        email = ''
        m = self.client.json.query.results.profile
        if 'emails' in m:
            for e in m.emails:
                if 'primary' in e and e.primary == 'true':
                    email = e.handle
                    break
        return attrdict(
            email=email
        )


# region: authentication clients

auth = {
    'google': OAuth2GoogleClient(
        client_id='',
        client_secret='',
        redirect_uri='http://.../oauth2/google',
        api_client=GoogleAPIClient,
        scope=('email', 'profile')),

    'windows': OAuth2WindowsClient(
        client_id='',
        client_secret='',
        # does not support localhost
        redirect_uri='http://.../oauth2/windows',
        api_client=WindowsAPIClient,
        scope=('wl.signin,wl.basic', 'wl.emails')),

    'facebook': OAuth2FacebookClient(
        client_id='',
        client_secret='',
        redirect_uri='http://.../oauth2/facebook',
        api_client=FacebookAPIClient,
        scope=('public_profile', 'email')),

    'linkedin': OAuth2LinkedInClient(
        client_id='',
        client_secret='',
        redirect_uri='http://.../oauth2/linkedin',
        api_client=LinkedInAPIClient,
        scope=('r_fullprofile', 'r_emailaddress')),

    # Permission: Social Directory (Profiles): Read/Write Public and Private
    'yahoo': OAuth2YahooClient(
        client_id='',
        client_secret='',
        # does not support port in uri
        redirect_uri='http://.../oauth2/yahoo',
        api_client=YahooAPIClient)
}


# region: urls

urls = {
    '/': welcome,
    '/oauth2/google': oauth2,
    '/oauth2/windows': oauth2,
    '/oauth2/facebook': oauth2,
    '/oauth2/linkedin': oauth2,
    '/oauth2/yahoo': oauth2
}


def router_middleware(request, following):
    handler = urls.get(request.path)
    if not handler:
        return not_found()
    return handler(request)


# region: samples

tokens = {}

# region: config

options = {}

# region: app

main = WSGIApplication([
    bootstrap_http_defaults,
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
