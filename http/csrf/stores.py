from . import request, response
from wsgic.session import sessions
import uuid

class CSRFStorage:
    def check(self, supplied_token=None):
        """ Returns ``True`` if the ``supplied_token`` is valid."""
        supplied_token = supplied_token or self.get_token()
        expected_token = self.get()
        return expected_token == supplied_token

class SessionCSRFStorage(CSRFStorage):
    def __init__(self, key='_csrft_'):
        self.key = key

    def new(self):
        """ Sets a new CSRF token into the session and returns it. """
        token = (uuid.uuid4().hex).decode()
        sessions.session[self.key] = token
        return token

    def get(self):
        """Returns the currently active CSRF token from the session,
        generating a new one if needed."""
        token = sessions.session.get(self.key, None)
        if not token:
            token = self.new()
        return token



class CookieCSRFStorage(CSRFStorage):
    """An alternative CSRF implementation that stores its information in
    unauthenticated cookies, known as the 'Double Submit Cookie' method in the
    `OWASP CSRF guidelines
    <https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#double-submit-cookie>`_.
    This gives some additional flexibility with
    regards to scaling as the tokens can be generated and verified by a
    front-end server.

    .. versionadded:: 1.9

    .. versionchanged: 1.10

       Added the ``samesite`` option and made the default ``'Lax'``.

    """

    def __init__(
        self,
        cookie_name='csrf_token',
        secure=False,
        httponly=False,
        domain=None,
        max_age=None,
        path='/',
        samesite='Lax',
        secret=None
    ):
        self.cookie_name = cookie_name
        self.config = {
            'secure': secure,
            'httponly': httponly,
            'domain': domain,
            'maxage': max_age,
            'path': path,
            'samesite': samesite,
            'secret': secret
        }


    def new(self):
        """ Sets a new CSRF token into the request and returns it. """
        token = (uuid.uuid4().hex).decode()
        response.set_cookie(self.cookie_name, token, **self.config)

        return token

    def get(self):
        """Returns the currently active CSRF token by checking the cookies
        sent with the current request."""
        token = request.get_cookie(self.cookie_name) or request.get_header('X-CSRF-Token', "").decode()
        if not token:
            token = self.new()
        return token
