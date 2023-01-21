import configparser, json, sys
import os
from wsgic.helpers.extra import set_global
from wsgic.thirdparty.bottle import run, app as App
from .runner import Apprunner

def load(target, **namespace):
	# Source bottle.py:load
	module, target = target.split(":", 1) if ':' in target else (target, None)
	if module not in sys.modules: __import__(module)
	if not target: return sys.modules[module]
	if target.isalnum(): return getattr(sys.modules[module], target)
	package_name = module.split('.')[0]
	namespace[package_name] = sys.modules[package_name]
	return eval('%s.%s' % (module, target), namespace)

def _get(data, index=0, e=None):
	try:return data[index] if type(data) in (list, dict, set, tuple) else data
	except:return e

# def url(func=None, method=None, name=None, apply=None, skip=None):
# 	return (func, method, name, apply, skip)

def _cli_parse(args):  # pragma: no coverage
	 from argparse import ArgumentParser

	 parser = ArgumentParser(prog=args[0], usage="%(prog)s [options] package.module:app")
	 opt = parser.add_argument
	 opt("--version", action="store_true", help="show version number.")
	 opt("-b", "--bind", metavar="ADDRESS", help="bind socket to ADDRESS.")
	 opt("-s", "--server", help="use SERVER as backend.")
	 opt("-p", "--plugin", action="append", help="install additional plugin/s.")
	#  opt("-c", "--conf", action="append", metavar="FILE", help="load config values from FILE.")
	 opt("-C", "--param", action="append", metavar="NAME=VALUE", help="override config values.")
	 opt("-new", action="store_true", help="create new wsgi app.")
	 opt("-env", default="dev", help="set app environment")
	 opt("--debug", action="store_true", help="start server in debug mode.")
	 opt("--reload", action="store_true", help="auto-reload on file changes.")
	 opt('app', help='WSGI app entry point.', nargs='?')

	 cli_args = parser.parse_args(args)
	 return cli_args, parser

def parse_args(argv):  # pragma: no coverage
	args, parser = _cli_parse(argv)
	def _cli_error(cli_msg):
		parser.print_help()
		print('\nError: %s\n' % cli_msg)
		sys.exit(1)
	if args.version:
		print('v1.0.0')
		sys.exit(0)
	if args.new:
		return start_app(args.app)
	if args.app:
		root = os.getcwd()
		sys.path.append(
			root + "/apps"
		)
		set_global("APPSDIR", root+'/apps')
		set_global("APPDIR", root+'/apps/'+args.app)
		set_global("ROOTDIR", root)
		runner = Apprunner(str(args.app))
	else:
		return _cli_error("No App Entry Specified.")

	if args.param:
		for cval in args.param:
			if '=' in cval:
				k, v = cval.split("=")
				runner.app.set(k.upper(), v)
			else:
				runner.app.set(cval.upper(), True)

	host, port = args.bind or runner.app.get("host") or "localhost", runner.app.get("port") or 8080

	if ':' in host:
		host, port = host.split(':')

	runner.init_app()
	runner.run(server=(args.server or runner.app.get("server", e="gevent")), host=host, port=port, debug=(args.debug or runner.app.get("debug")))

	# if args.conf:
	# 	for cfile in args.conf:
	# 		try:
	# 			runner.app.get().clear()
	# 			if cfile.endswith('.json'):
	# 				with open(cfile, 'r') as fp:
	# 					runner.app.get["appConfig"].load_dict(json.loads(fp.read()))
	# 			elif cfile.endswith(".ini"):
	# 				runner.app.get["appConfig"].load_config(cfile)
	# 			else:
	# 				runner.app.get["appConfig"].load_module(cfile)
	# 		except configparser.Error as parse_error:
	# 			_cli_error(parse_error)
	# 		except IOError:
	# 			_cli_error("Unable to read config file %r" % cfile)
	# 		except (UnicodeError, TypeError, ValueError) as error:
	# 			_cli_error("Unable to parse config file %r: %s" % (cfile, error))

	# middlewares = app.get("middlewares", e=None)
	# if middlewares:
	# 	App.push(app)
	# 	mapp = App()
	# 	entries = ["wsgic"]
	# 	for mw in middlewares:
	# 		if type(mw) is list:
	# 			entries.append(*mw)
	# 			pass
	# 		else:
	# 			for apps in entries:
	# 				try:
	# 					m = load(f"{apps}.middleware")
	# 					miw = getattr(m, mw)
	# 					break
	# 				except:
	# 					pass

	# 		_args = app.get(f"{mw}_args", e=(), raw=True)
	# 		_kwargs = app.get(f"{mw}_kwargs", e={}, raw=True)

	# 		mapp = miw(mapp, *_args, **_kwargs)
	# else:mapp = app

	# run(app=mapp, server=(args.server or app.get("server", e="gevent")), host=host, port=port, reloader=(args.reload or True), debug=(args.debug or app.get("debug")))

def start_app(name):
	import os
	files = {
		"__init__": f"""from wsgic import WSGIApp

class {name.title()}App(WSGIApp):
	def __init__(self):
		super().__init__(__package__)
""",
		"views" : """from wsgic.base.views import View

class HomeView(View):
	def __init__(self):
		super().__init__(self)

	def index(self):
		return "Homepage"
""",
		"urls" : """from .views import HomeView
hv = HomeView()

mount = "/"

routes = {}
routes['/'] = (hv.index, ["GET", "POST"], "homepage")
""",
		"models" : """from wsgic.base.models import Model, Field

class Blog(Model):
	def __init__(self):
		super().__init__()
		self.column.name = Field(type="text")
		self.column.title = Field(type="text", null=False)
		self.column.rating = Field(type="integer", default=1)
		self.create()
""",
		"controllers" : """
""",
		"helpers": """
""",
		"database": """from wsgic.helpers.database.sqlite import SqliteDatabase
from wsgic.helpers import get_global


"""
	}
	cwd = str(os.getcwd())
	if not cwd.endswith('apps'):
		print('Not currently in apps directory')
		y = input('Create in apps directory? [y, n]: ')
		if y.lower() == 'y':
			nm = name
			name = os.path.join('apps', name)
			print(f'Creating at {os.path.join(cwd, name)}')
	
	while True:
		try:
			os.mkdir(name)
			break
		except:
			print()
			print(f"Folder Already exists with name {name}")
			if str(input("Do you want to override it? [y, n]: ")).lower() != "y":
				n = str(input("Enter new app name: "))
				if y.lower() == 'y':
					nm = n
					name = os.path.join('apps', n)
	print()
	print(f"Creating WSGI App: {nm}")
	print()
	for m in files:
		try:
			print(f"Generating File: {os.path.join(name, m)}.py")
			#with open(f"{os.path.join(cwd, name, m)}.py", "x") as file:
				#file.write(files[m])
		except FileExistsError:
			print("File {os.path.join(name, m)}.py Already Exists")
			pass
	print()
	print(f"Created WSGI App: {nm}")