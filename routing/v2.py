import types
from wsgic.thirdparty.bottle import load
from wsgic.helpers.extra import get_global
from wsgic.helpers.require import require

def _get(data, index=0, e=None):
	try:return data[index] if type(data) in (list, dict, set, tuple) else data
	except:return e

def _url(x):
	if x == "mount":return x
	if x == "":x = "/"
	elif len(x) >= 1 and not x.startswith('/'):x = f'/{x}'
	while '//' in x:x = str(x).replace('//', '/')
	else:return x

class Routes(dict):
	def __init__(self, start="<", end=">", seperator=":",  engine="complex", **kw):
		self.data = super()
		self.data.__init__(**kw)
		self.start, self.end, self.sep, self.engine = start, end, seperator, engine
		self.filters = {}
		self.rfilters = {}
		self.config = {
			"base_view": None,
			"app": None
		}
	
	def all(self):
		return self

	def filter(self, name, regex, py=None, url=None):
		self.rfilters[name] = lambda conf: (regex, py, url)

	def set(self, start=None, end=None, seperator=None,  engine=None):
		self.start, self.end, self.sep, self.engine = start or self.start, end or self.end, seperator or self.sep, engine or self.engine

	def baseview(self, view):
		self.config['base_view'] = view

	def use(self, *app):
		self.config["app"] = app
		return self

	def compile_(self, url):
		if self.engine == "simple":
			return self.remake_simple(url, self.start, self.end, self.sep)
		else:
			return self.remake(url, self.start, self.end, self.sep)
	
	def remake(self, line, start="<", end=">", sep=":"):
		seg = line.split("/")
		d = {}
		for i, segment in enumerate(seg):
			if start in segment and end in segment:
				segment = self.conv(segment, start, end, sep)
			d[i] = segment
		data = "/".join(d[x] for x in d)
		return data
	
	def conv(self, line, start, end, sep):
		if type(start) is str and start != "" and start in line:
			line = f"{start}".join(x for x in line.split(start)[1:]).strip()
		if type(sep) is str and sep != "" and sep in line:
			new = line.split(sep)
			line = new[0].strip()+":"+new[1].strip()
		if type(end) is str and end != "" and end in line:
			line = f"{end}".join(x for x in line.split(end)[:1]).strip()
		line = "<"+line.strip()+">"
		return line
	
	def remake_simple(self, line, s="<", e=">", p=":"):
		if s != "":line = line.replace(s, "<")
		if p != "": line = line.replace(p, ":")
		if e != "":line = line.replace(e, ">")
		return line

	def getfunc(self, name):
		try:
			c = self.config['app']
			if c:
				if type(name) is types.FunctionType or type(name) is types.LambdaType:
					return name
				if len(c) == 1 and name=="self":
					return self.getclass(c)
				app = self.getclass(c, name)
				return app
					#if hasattr(app(), name):return getattr(app(), name)
					#else:pass
		except:pass

	def getclass(self, names, f=None):
		# try:
		func = f'.{f}' if f else '' 
		if type(names) is tuple:
			apps = get_global("installed_apps")
			ret = []
			for app in apps:
				aname = app.lower().replace('app', '')
				for name in names:
					if type(name) is not str:return name
					ret.append(f"{aname}.views:{name}{func}")
			return ret
		else:return names

	def __getitem__(self, name):
		name = name.split(" ")
		name = name[0]
		return self.data.__getitem__(name)

	def __setitem__(self, name, value):
		other = None
		name = name.split(" ")
		try:name, other = name[0], name[1]
		except:name = name[0]

		name = _url(name)
		if other:self.filters[name] = other
		if type(value) is dict and name != "mount":
			for r in value:
				self.__setitem__(name+_url(r), value[r])
			return
		if type(value) is tuple and type(_get(value, 0)) is str:
			value = (self.getfunc(value[0]), *value[1:])
		# print("Value: ", value)
		name = self.compile_(name)
		return self.data.__setitem__(name, value)


class Router:
	'''
Router to handle routes
Adds the set namespace to all route set by the class instance

Parameters:
  During Creation:
	base url: '/auth'
	base route: usually Bottle.route or route or <Your Bottle instance>.route
	routes (optional): a list of your app routes
	
  Calling route and new method:
	the default routes arguments i.e path, method, name, function, skip etc

Usage:
	Router.route:
		auth = Router('/auth', route)
		@auth.route(url='/login', method="GET")
		def login():
			...
	
		produces:
			route('/auth/login', method="GET")
			
	
	Router.new and Router.router:
		auth = Router('/auth', route)
		def login():
		   ...
		   
		# Create route
		auth.new(url='/login', func=login, method='POST')
		
		# Instantiate all created routes
		auth.router()

'''
	def __init__(self, baseUrl, app, r={}):
		self.baseUrl = _url(baseUrl)
		self.app = app
		self.routes = r
		self.ordered = {}
		self.filters = {}
		self.apps = [self.app.__class__.__name__]
		invalids = ("callback", "func")

		self.vars = [x for x in self.app.route.__code__.co_varnames[2:] if x not in invalids]

	def start(self):
		self.order(self.routes.all())
		self.make_mounts()
		self.router()
		# try:
		# 	self.router()
		# except:
		# 	self.make_mounts()
		# 	self.router()
	
	def make(self, routes):
		if len(routes) < 0:return {}
		al = {}
		for i, x in enumerate(self.vars):
			try:al[x] = routes[i]
			except IndexError:break
		return al

	def error(self, code, func):
		self.app.error(code, callback=func)

	def _route(self, url='', func=None, **kwargs):
		url = _url(self.baseUrl+url)
		return self.app.route(url, **kwargs)(func)

	def route(self, url='', **kwargs):
		url = _url(self.baseUrl+url)
		return self.app.route(url, **kwargs)

	def new(self, **config):
		route = {x: config[x] for x in config}
		self.routes.append(route)

	def mnt(self, url):
		self.baseUrl = _url(url)

	def makefilters(self, filters):
		return filters 
		
	def makefunc(self, funcs):
		for func in funcs:
			a = func.split('.')
			cls, func = '.'.join(a[:-1]), a[-1]
			try:
				cls = load(cls)
				print(cls)
				if hasattr(cls(), func):
					func = getattr(cls(), func)
					return func
			except Exception as e:
				print(e)

	# def _url(self, url):
	# 	url = str(url)
	# 	if not url.startswith("/"):url = "/"+url
	# 	if not url.endswith("/"):url = url+"/"
	# 	return url

	def make_mounts(self):
		mounts = self.routes.get("mount", None)

		if not mounts:return
		for x in mounts:
			if "::" in mounts[x]:
				app, framework = mounts[x].split("::")
			else:
				app = mounts[x]
				framework = "bottle"
			app = get_app(app, framework)
			if framework == "bottle":
				self.order(app.url_routes, x)
				self.router(app.url_routes, x)
			else:
				self.app.mount(x, app)
		
	def router_v2(self, config=[]):
		routes = config if config != [] else self.routes.all()
		def make(routes, base_url=''):
			for x in routes:
				if type(x) is str:
					base_url = base_url + _url(x)
				elif type(x) is dict:
					path = _get(data=x, index='url')
					func = _get(data=x, index='func')
					url=base_url+_url(path)
					decorators =  _get(x, "decorators")
					if decorators and type(decorators) is set:
						oths = self.make(x[2:-1])
						for decorator in decorators:
							func = decorator(func)
					else:oths = self.make(x[2:])
					self._route(url, func=func, **oths)
				elif type(x) is tuple:
					make(x[1], x[0])
				elif type(x) is list:
					make(x, base_url=base_url)
		make(routes)

	def find_route(self, name, routes=[]):
		routes = routes if routes != [] else self.ordered
		return routes[name]

	def order(self, routes={}, url=""):
		routes = routes if routes != [] else self.routes.all()
		for x in routes.rfilters:
			self.app.router.add_filter(x, routes.rfilters[x])
		def make(routes, base_url):
			for x in routes:
				if type(routes[x]) is tuple:
					name = _get(routes[x], 2)
					#print(name, str(base_url + x))
					if name:
						self.ordered[name] = str(base_url + x)
				elif type(routes[x]) is dict:
					make(routes[x], base_url=base_url+x)
				else:pass
		make(routes, base_url=url)
	
	def router(self, config=[], url=""):
		routes = config if config != [] else self.routes.all()
		def make(routes, base_url=''):
			for x in routes:
				if type(x) is str:
					if x == "use":
						return self.routes.use(routes[x])
				if type(x) is int:
					func = _get(routes[x], 0)
					self.error(int(x), func)
				elif type(routes[x]) is list:
					make(routes[x], x)
				elif type(routes[x]) is tuple:
					func = _get(data=routes[x], index=0)
					url = base_url+_url(x)
					# filters =  _get(routes[x], -1)
					if type(func) is list:
						func = self.makefunc(func)

					name = _get(routes[x], 2)
					if name:
						try:self.ordered[name] = str(base_url + x)
						except:pass
					
					decorators =  _get(routes[x], -1)
					if decorators and type(decorators) is set:
						oths = self.make(routes[x][1:-1])
						for decorator in decorators:func = decorator(func)
					else:oths = self.make(routes[x][1:])
					self._route(url, func=func, **oths)

				elif type(routes[x]) is dict:
					make(routes[x], base_url=base_url+x)
		make(routes, url)
		
def make_django_routes(urls):
	ptrn, resl = require("django.urls.resolvers:URLPattern", "django.urls.resolvers:URLResolver")()
	allurls = urls.urlpatterns
	for url in allurls:
		if isinstance(url, resl):
			name = url.urlconf_name
			path = url.pattern
			for item in name:
				if isinstance(item, ptrn):
					pass#print(item.name)

def get_app(appn, framework):
	if framework == "bottle":
		app = load(f"{appn}:" + f"{appn}".title() + "App()")
		app.setup(subapp=True)
		return app
	elif framework == "django":
		app = load(f"{appn}.wsgi")
		make_django_routes(load(f"{appn}.urls"))
		return app.application
	elif framework == 'flask':
		if "." in appn:
			app, ins = appn.split(".")
		else:
			app = appn
			ins = "app"
		app = load(app)
		return getattr(getattr(app, ins), "wsgi_app")
	elif framework == "pyramid":
		if "." in appn:
			app, ins = appn.split(".")
		else:
			app = appn
			ins = "app"
		app = load(app)
		return getattr(app, ins)