from wsgic.server import request
from wsgic.thirdparty.bottle import HTTPError
from functools import wraps

def limit(*method):
	def main(callback):
		@wraps(callback)
		def wrapped(*a, **kw):
			if request.method in method:
				return callback(*a, **kw)
			raise HTTPError(405, "Method not allowed.", Allow=",".join(method))
		return wrapped
	return main

def alias(name, callback=None):
	def wrapper(callback):
		callback.__alias__ = name
		return callback
	return wrapper(callback) if callback else wrapper

def named_route(name, callback=None):
	def wrapper(callback):
		callback.__route_name__ = name
		return callback
	return wrapper(callback) if callback else wrapper

