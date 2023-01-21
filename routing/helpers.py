from wsgic.helpers import config
from wsgic.server import request
from wsgic.thirdparty.bottle import makelist, HTTPError
from functools import wraps

# def url(path):
# 	if not config.get('use.endslash', False):
# 		return path.rstrip('/')
# 	return path

# def previousUrl():
# 	request.__dict__['previous_url'] = request.session['previous_url', None]

# def before():
# 	previousUrl()
# 	print('Before', request.session, str(request.url))

# def after():
# 	# if request.session['previous_url', None] != url(request.url):
# 	request.session['previous_url'] = url(request.url)
# 	print('After', request.session, url(request.url), "Similiar?", request.session['previous_url'] == url(request.url))

def limit(*method):
	def main(callback):
		@wraps(callback)
		def wrapped(*a, **kw):
			if request.method in method:
				return callback(*a, **kw)
			raise HTTPError(405, "Method not allowed.", Allow=",".join(method))
		return wrapped
	return main

def alias(alias, callback=None):
	def wrapper(callback):
		callback.__alias__ = alias
		return callback
	return wrapper(callback) if callback else wrapper