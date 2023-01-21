from wsgic.thirdparty.bottle import run, app as App, load, _ImportRedirect
from wsgic.helpers.extra import set_global, get_global 
from wsgic.helpers import ordered
import sys
import os

root = os.getcwd()
sys.path.append(
    os.path.join(root, "apps")
)

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


class Apprunner:
    '''Application interface to initialize and run apps
    ::params::
        :app:
            :type: String
            Name of module
'''
    def __init__(self, app):
        try:
            app = load(app.replace(".app", "")+".app")
        except ModuleNotFoundError:
            app = load(app.replace(".app", ""))
        
        self.app = app.__app__
        set_global("app", self.app)
    
    def init_app(self):
        self.app.setup()
        # handlers(self.app)
    
#     def get_middlewares(self, app=None):
#         if not app:app=self.app
#         middlewares = app.get("middlewares", e=None)
#         if middlewares:
#             App.push(app)
#             mapp = App()
#             entries = ["wsgic"]
#             for a in get_global("installed_apps"):
#                 entries.append(a.lower().replace("app", ""))
#             for middleware in middlewares:
#                 for apps in entries:
#                     try:
#                         middlewareclass = load(f"{apps}.middleware:{middleware}")
#                         break
#                     except:pass
#                 _args = app.get(f"{middleware}['args']", e=(), raw=True)
#                 _kwargs = app.get(f"{middleware}['kwargs']", e={}, raw=True)
#                 mapp = middlewareclass(mapp, *_args, **_kwargs)
#         else:mapp = self.app
#         return mapp

    def run(self, server='wsgiref', host='127.0.0.1', port=8080, interval=1, type="wsgi", reloader=False, quiet=False, plugins=None, debug=False, config=None, **kargs):
        app = self.app.wrapped_app(type)
        if type == "wsgi":
            from werkzeug import run_simple
            run_simple(
                host, port, app, True, debug
            )
            # from bottle import run
            # run(app, server=server, host=host, port=port, interval=interval, reloder=True, debug=True)
        elif type == "asgi":
            from uvicorn.main import run
            run(
                app, host=host, port=port, debug=debug
            )
        return
#         if server == "gevent":
#             from gevent import monkey
#             monkey.patch_all()
#         # run(app=self.get_middlewares(), **kw)
#         return run(self.app, server=server, host=host, port=port, debug=debug, interval=interval, reloader=reloader, quiet=quiet, plugins=plugins, config=config, **kargs)

# def url(func=None, method=None, name=None, apply=None, skip=None):
#     return (func, method, name, apply, skip)

def _cli_parse(args):  # pragma: no coverage
     from argparse import ArgumentParser

     parser = ArgumentParser(prog="wsgic", usage="python -m %(prog)s [options] package.module:app")
     opt = parser.add_argument
     opt("--version", action="store_true", help="show version number.")
     opt("-b", "--bind", metavar="ADDRESS", help="bind socket to ADDRESS.")
     opt("-se", "--server", help="use SERVER as backend.")
     opt("-p", "--plugin", action="append", help="install additional plugin/s.")
    #  opt("-c", "--conf", action="append", metavar="FILE", help="load config values from FILE.")
     opt("-C", "--param", action="append", metavar="NAME=VALUE", help="override config values.")
     opt("-n", "--new", action="store_true", help="create new wsgi app.")
     opt("-s", "--script", action="store_true", help="run script then app.")
     opt("-a", "--asgi", action="store_true", help="run the asgi version of an app.")
     opt("-d", "--django", action="store_true", help="Run the django cli.")
     opt("-env", default="dev", help="set app environment")
     opt("--debug", action="store_true", help="start server in debug mode.")
     opt("--reload", action="store_true", help="auto-reload on file changes.")
     opt('app', help='WSGI app entry point.', nargs='*')

     cli_args = parser.parse_args(args[1:])
     return cli_args, parser

def parse_args(argv):  # pragma: no coverage
    args, parser = _cli_parse(argv)
    def _cli_error(cli_msg=None):
        parser.print_help()
        if cli_msg:print('\nError: %s\n' % cli_msg)
        sys.exit(1)
    if args.version:
        print('v1.0.0')
        sys.exit(0)
    if args.new:
        return start_app(args.app[0])
    if args.django:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.settings'%args.app[0])
        try:
            from django.core.management import execute_from_command_line
        except ImportError as exc:
            raise ImportError(
                    "Couldn't import Django. Are you sure it's installed and "
                    "available on your PYTHONPATH environment variable? Did you "
                    "forget to activate a virtual environment?"
                ) from exc
        return execute_from_command_line(args.app)
    if args.app:
        # Initialize global variables
        set_global("APPSDIR", root+'/apps')
        set_global("APPDIR", root+'/apps/'+args.app[0])
        set_global("ROOTDIR", root)
        
        set_global("APPMODULE", args.app[0])
        set_global("installed_apps", {})
        
        # Main application runner
        runner = Apprunner(str(args.app[0]))
        runner.init_app()
        
        set_global("app_runner", runner)
        if len(args.app) > 1:
            parse_scripts(*args.app)
            if not args.script:
                return
    else:
        return _cli_error("No app entry specified.")

    if args.param:
        for cval in args.param:
            if '=' in cval:
                k, v = cval.split("=")
                runner.app.config.set(k.upper(), v)
            else:
                runner.app.config.set(cval.upper(), True)

    host, port = args.bind or runner.app.config.get("host") or "localhost", runner.app.config.get("port") or 7000

    if ':' in host:
        host, port = host.split(':')

    # for route in runner.app.router.routes.data:
    #     print('<%s "%s" -> %s [name="%s"]>'%(
    #         route.method, route.rule, route.callback, route.name
    #     ))

    server = args.server or runner.app.config.get("server", "wsgiref")
    debug = args.debug or runner.app.config.get("debug") or True
    apptype = "asgi" if args.asgi else "wsgi"

    return runner.run(server=server, host=host, port=int(port), debug=debug, type=apptype)

    # if args.conf:
    #     for cfile in args.conf:
    #         try:
    #             runner.app.get().clear()
    #             if cfile.endswith('.json'):
    #                 with open(cfile, 'r') as fp:
    #                     runner.app.get["appConfig"].load_dict(json.loads(fp.read()))
    #             elif cfile.endswith(".ini"):
    #                 runner.app.get["appConfig"].load_config(cfile)
    #             else:
    #                 runner.app.get["appConfig"].load_module(cfile)
    #         except configparser.Error as parse_error:
    #             _cli_error(parse_error)
    #         except IOError:
    #             _cli_error("Unable to read config file %r" % cfile)
    #         except (UnicodeError, TypeError, ValueError) as error:
    #             _cli_error("Unable to parse config file %r: %s" % (cfile, error))

    # middlewares = app.get("middlewares", e=None)
    # if middlewares:
    #     App.push(app)
    #     mapp = App()
    #     entries = ["wsgic"]
    #     for mw in middlewares:
    #         if type(mw) is list:
    #             entries.append(*mw)
    #             pass
    #         else:
    #             for apps in entries:
    #                 try:
    #                     m = load(f"{apps}.middleware")
    #                     miw = getattr(m, mw)
    #                     break
    #                 except:
    #                     pass

    #         _args = app.get(f"{mw}_args", e=(), raw=True)
    #         _kwargs = app.get(f"{mw}_kwargs", e={}, raw=True)

    #         mapp = miw(mapp, *_args, **_kwargs)
    # else:mapp = app

    # run(app=mapp, server=(args.server or app.get("server", e="gevent")), host=host, port=port, reloader=(args.reload or True), debug=(args.debug or app.get("debug")))

def parse_scripts(app, *args):
    app = load(app.replace(".app", "")+".scripts")
    appglobals = {x: getattr(app, x) for x in dir(app)}
    func = appglobals.get(args[0])
    if func:
        return func(*args[1:])
    
    else:
        for item in appglobals.values():
            if isinstance(item, object):
                item = item()
                func = getattr(item, args[0], None)
                if func:
                    return func(*args[1:])

def start_app(name):
    import os
    files = {
        "__init__": "",
        "app": f"""from wsgic import WSGIApp
from wsgic.helpers import config

class {name.title()}App(WSGIApp):
    def __init__(self):
        super().__init__("{name}.urls:router", config)

__app__ = {name.title()}App()
""",
        "views" : """from wsgic.http import request

def index():
    return "Hello World from {request.path}"
""",
        "urls" : """from wsgic.routing import Router
from .views import *

router = Router()
routes = router.get_routes()

routes.get("*", index)
""",
        "models" : """
""",
        "controllers" : """
""",
        "helpers": """
""",
        "services": """
""",
        "plugins": """from wsgic.plugins import *
""",
        "panels": """from wsgic_admin.helpers import AdminPanel, register
from .models import *

register()
""",
        "wsgi": f"""from .app import __app__ as {name.title()}App

application = {name.title()}App.wrapped_app("wsgi")
""",
        "asgi": f"""from .app import __app__ as {name.title()}App

application = {name.title()}App.wrapped_app("asgi")
"""
    }
    cwd = str(os.getcwd())
    if not cwd.endswith('apps'):
        print('Not currently in apps directory')
        y = input('Create in apps directory? [y, n, q]: ')
        if y.lower() == 'y':
            nm = name
            name = os.path.join('apps', name)
        elif y.lower() == 'n':
            nm = name
        else:
            print("Terminating operation...")
            return
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
            with open(f"{os.path.join(name, m)}.py", "x") as file:
                file.write(files[m])
        except FileExistsError:
            print("File {os.path.join(name, m)}.py Already Exists")
            pass
    print()
    print(f"Created WSGI App: {nm}")