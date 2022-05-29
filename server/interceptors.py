from wsgic.middleware.session import FilesystemSessionStore
from wsgic.backend.bottle import response, load, static_file, request
from wsgic.helpers.routes import Router
from wsgic.helpers.extra import set_global, switch, _get, get_global

# from werkzeug.http import parse_cookie

######################
#### INTERCEPTORS ####
######################

def views_handler(app):
	d = switch(app.get("static.template.engine"), _return=True)
	d.case("jinja2", load, args=["wsgic.backend:jinja2_template"])
	d.case("mako", load, args=["wsgic.backend:mako_template"])
	d.case("cheetah", load, args=["wsgic.backend:cheetah_template"])
	global template, extra_func
	template = d.default(load, args=["wsgic.backend:template"])
	extra_func = {
		"url": lambda x: app.appRouter.find_route(value=x)
	}

# def session_handler(app):
# 	options = dict(app.get("session_options", raw=True))
# 	def _get_session_id():
# 		cookie = parse_cookie(request.environ.get("HTTP_COOKIE", ""))
# 		return cookie.get(options.get('name'), None)
# 	sid = _get_session_id()

# 	store = options.get('store', FilesystemSessionStore())
# 	if sid is None:
# 		try:session = store.new()
# 		except AttributeError:pass
# 	else:
# 		try:session = store.get(sid)
# 		except AttributeError:pass
	
# 	set_global(options.get("environ_key", "wsgic_session"), session)
	
# 	app.hook("after_request")(app._save_sess(store, session))

def session_handler(app):
	cfg = get_global("config")
	opt = cfg.get("session", raw=True)
	session_store = FilesystemSessionStore()
	sid = request.get_cookie("session_id")
	print(sid)

	if sid is None:
		session = session_store.new()
	else:
		session = session_store.get(sid)
	options = {x.lower(): "off" if opt[x] == False else opt[x] for x in opt if x not in ("STORE", "NAME", "KEY") and opt[x] is not None}
	
	set_global(cfg.get("environ_key", "wsgic_session"), session)
	set_global("session_store", session_store)
	
	def save_sess():
		if session.should_save:
			session_store.save(session)
			response.set_cookie("session_id", session.sid, **options)
			print(session.sid)
			print("Saved session", session, options)
	app.hook("after_request")(save_sess)

def database_handler(app, config):
	# db =  Database(app, config)
	# con = db.connect()
	# if con is False:
	# 	for conf in range(5):
	# 		app._debug(f"Using Fallback Database {conf}")
	# 		db =  Database(app, f"databases.failover.{conf}")
	# 		conn = db.connect()
	# 		if conn is False:continue
	# 		else:break
	# set_global("db", db)
	pass

def routes_handler(app, router=None):
	# if router:
	# 	app.appRouter = router
	# 	for x in app.url_routes:
	# 		app.appRouter.routes[x] = app.url_routes.all()[x]
	# 	return
	# else:
	app.appRouter = Router("", app)
	set_global("router", app.appRouter)
	app.appRouter.routes = app.url_routes
	app.appRouter.start()
	if app.get("use.static") == True:
		r_cnf = app.get("static.assets.url")
		app.url_routes[f"{r_cnf}/<file:path>"] = (static_handler(app.get("static.assets.dirs")), "GET")
	#app.appRouter.router()

def static_handler(root):
	def _static(file):
		for path in root:
			try:
				a = open(f"{path}{file}", "r")
				a.close()
				return static_file(file, root=path)
			except:
				continue
	return _static

def render(name, *args, **kwargs):
	try:context = _get(args, 0) or kwargs.pop("context")
	except:context = {}
	return template(name, dict(**extra_func, **context), *args, **kwargs)
