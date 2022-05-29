from werkzeug.http import dump_cookie, parse_cookie
from .backend import Bottle, app, request, response
from .server import set_global, load, TEMPLATE_PATH, routes_handler
from .helpers import config
from .helpers.extra import get_global

class WSGIApp(Bottle):
	def __init__(self, file, conf="settings", **opts):
		super().__init__()
		fname = file.split("/")
		self.pkg = fname[-1].replace(".py", "") if fname[-1] != "__init__.py" else fname[-2].replace(".py", "")
		self.stack = app
		self.appConfig = config
		self.conf = conf
		self.conf_opts = opts
		self.catch_all = False

		set_global(str(self.__class__.__name__).replace("App", ""), self)
		get_global('installed_apps').append(str(self.__class__.__name__))
		
	def setup(self, subapp=False):
		self.url_routes = load(f"{self.pkg}.urls:routes")
		if subapp:
			return
		self.hook("before_request")(self._strip)

		self.store = self.get("session.store")
		if self.conf.startswith("."):m = load(f"{self.pkg}{self.conf}")
		else:m = load(f"{self.conf}")
		self.appConfig.use(m, **self.conf_opts)
		set_global("config", self.appConfig)
		# self.hook("before_request")(self._setup_sess)
		TEMPLATE_PATH.append(*self.get("static.template.dirs"))

	def _strip(self):
		request.environ["PATH_INFO"] = request.environ["PATH_INFO"].rstrip("/")

	def get(self, conf=None, e=None, raw=False):
		return self.appConfig.get(conf, e, raw)

	def set(self, config, value, c=None):
		self.appConfig.set(config, value)

	def _debug(self, text):
		if self.get("debug"):print("[DEBUG]", text)
