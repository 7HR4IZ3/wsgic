from .session import SessionMiddleware as Sess, FilesystemSessionStore
from wsgic.thirdparty.bottle import request

class SessionMiddleware(Sess):
	def __init__(self, app, **kwargs):
		self.app = app
		super().__init__(app, FilesystemSessionStore(filename_template="wsgic_%s.sess"), **kwargs)

	def get_app(self):
		return self.app

# class AltSessionMiddleware(Sess):
# 	def __init__(self, app, **kwargs):
# 		self.app = app
# 		super().__init__(app, FilesystemSessionStore(filename_template="wsgic_%s.sess"), **kwargs)

# 	def get_app(self):
# 		return self.app

# class Cache(CacheMiddleware):
# 	def get_app(self):
# 		return self.app