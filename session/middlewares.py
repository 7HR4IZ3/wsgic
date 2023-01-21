from werkzeug.http import dump_cookie
from werkzeug.http import parse_cookie
from werkzeug.wsgi import ClosingIterator

class SessionMiddleware(object):
	"""A middleware that puts the session object of a store into the
	WSGI environ. It automatically sets cookies and restores sessions.

	However a middleware is not the preferred solution because it won't
	be as fast as sessions managed by the application itself and will
	put a key into the WSGI environment only relevant for the
	application which is against the concept of WSGI.

	The cookie parameters are the same as for the :func:`~dump_cookie`
	function just prefixed with ``cookie_``. Additionally ``max_age`` is
	called ``cookie_age`` and not ``cookie_max_age`` because of
	backwards compatibility.

	.. versionchanged:: 0.1.0
		``environ_key`` defaults to ``secure_cookie.session`` instead of
		``werkzeug.session``.
	"""

	def __init__(
		self,
		app,
		store,
		cookie_name="session_id",
		cookie_age=None,
		cookie_expires=None,
		cookie_path="/",
		cookie_domain=None,
		cookie_secure=None,
		cookie_httponly=False,
		cookie_samesite="Lax",
		environ_key="secure_cookie.session",
	):
		self.app = app
		self.store = store
		self.cookie_name = cookie_name
		self.cookie_age = cookie_age
		self.cookie_expires = cookie_expires
		self.cookie_path = cookie_path
		self.cookie_domain = cookie_domain
		self.cookie_secure = cookie_secure
		self.cookie_httponly = cookie_httponly
		self.cookie_samesite = cookie_samesite
		self.environ_key = environ_key

	def __call__(self, environ, start_response):
		sid = self._get_session_id(environ)

		if sid is None:
			session = self.store.new()
		else:
			session = self.store.get(sid)

		environ[self.environ_key] = session

		def injecting_start_response(status, headers, exc_info=None):
			if session.should_save:
				self.store.save(session)
				headers.append(("Set-Cookie", self._dump_cookie(session)))

			return start_response(status, headers, exc_info)

		return ClosingIterator(
			self.app(environ, injecting_start_response),
			lambda: self.store.save_if_modified(session),
		)

	def _get_session_id(self, environ):
		cookie = parse_cookie(environ.get("HTTP_COOKIE", ""))
		return cookie.get(self.cookie_name, None)

	def _dump_cookie(self, session):
		return dump_cookie(
			key=self.cookie_name,
			value=session.sid,
			max_age=self.cookie_age,
			expires=self.cookie_expires,
			path=self.cookie_path,
			domain=self.cookie_domain,
			secure=self.cookie_secure,
			httponly=self.cookie_httponly,
			samesite=self.cookie_samesite,
		)
