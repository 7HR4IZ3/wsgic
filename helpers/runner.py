from wsgic.backend.bottle import run, app as App
from wsgic.server import interceptor, load
from wsgic.helpers.extra import set_global, get_global
from pathlib import Path
import sys, os

class Apprunner:
	def __init__(self, app):
		root = os.getcwd()
		sys.path.append(
			root + "/apps"
		)
		set_global("APPDIR", root+'/apps')
		set_global("ROOTDIR", root)
		set_global("installed_apps", [])
		set_global("router", None)
		self.app = load(
			f"{app}:" + f"{app}".title() + "App()"
		)
	
	def init_app(self):
		self.app.setup()
		interceptor(self.app)
	
	def get_middlewares(self, app=None):
		if not app:app=self.app
		middlewares = app.get("middlewares", e=None)
		if middlewares:
			App.push(app)
			mapp = App()
			entries = ["wsgic"]
			for a in get_global("installed_apps"):
				entries.append(a.lower().replace("app", ""))
			for middleware in middlewares:
				for apps in entries:
					try:
						middlewareclass = load(f"{apps}.middleware:{middleware}")
						break
					except:pass
				_args = app.get(f"{middleware}['args']", e=(), raw=True)
				_kwargs = app.get(f"{middleware}['kwargs']", e={}, raw=True)
				mapp = middlewareclass(mapp, *_args, **_kwargs)
		else:mapp = self.app
		return mapp

	def run(self, **kw):
		# print(get_global('installed_apps'))
		if self.app.get("server") == "gevent":from gevent import monkey;monkey.patch_all()
		run(app=self.get_middlewares(), **kw)