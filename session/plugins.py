import inspect
from wsgic.plugins import KeywordPlugin
from . import sessions

class SessionPlugin(KeywordPlugin):
	name = "session"
	api = 2

	def __init__(self, keyword="session"):
		super().__init__(keyword, sessions.session)