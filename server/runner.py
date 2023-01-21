import sys
import os

from .helpers import runscript

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

def parse_args(argv):
    runscript("wsgic.server", *argv[1:])

    # args, parser = _cli_parse(argv)
    # def _cli_error(cli_msg=None):
    #     parser.print_help()
    #     if cli_msg:print('\nError: %s\n' % cli_msg)
    #     sys.exit(1)
    # if args.version:
    #     print('v1.0.0')
    #     sys.exit(0)
    # if args.new:
    #     return start_app(args.app[0])
    # if args.django:
    #     os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.settings'%args.app[0])
    #     try:
    #         from django.core.management import execute_from_command_line
    #     except ImportError as exc:
    #         raise ImportError(
    #                 "Couldn't import Django. Are you sure it's installed and "
    #                 "available on your PYTHONPATH environment variable? Did you "
    #                 "forget to activate a virtual environment?"
    #             ) from exc
    #     return execute_from_command_line(args.app)
    # if args.app:
    #     # Initialize global variables
    #     set_global("APPSDIR", root+'/apps')
    #     set_global("APPDIR", root+'/apps/'+args.app[0])
    #     set_global("ROOTDIR", root)
        
    #     set_global("APPMODULE", args.app[0])
    #     set_global("installed_apps", {})
        
    #     # Main application runner
    #     runner = Apprunner(str(args.app[0]))
    #     runner.init_app()
        
    #     set_global("app_runner", runner)
    #     if len(args.app) > 1:
    #         parse_scripts(*args.app)
    #         if not args.script:
    #             return
    # else:
    #     return _cli_error("No app entry specified.")

    # if args.param:
    #     for cval in args.param:
    #         if '=' in cval:
    #             k, v = cval.split("=")
    #             runner.app.config.set(k.upper(), v)
    #         else:
    #             runner.app.config.set(cval.upper(), True)

    # host, port = args.bind or runner.app.config.get("host") or "localhost", runner.app.config.get("port") or 7000

    # if ':' in host:
    #     host, port = host.split(':')

    # # for route in runner.app.router.routes.data:
    # #     print('<%s "%s" -> %s [name="%s"]>'%(
    # #         route.method, route.rule, route.callback, route.name
    # #     ))

    # server = args.server or runner.app.config.get("server", "wsgiref")
    # debug = args.debug or runner.app.config.get("debug") or True
    # apptype = "asgi" if args.asgi else "wsgi"

    # return runner.run(server=server, host=host, port=int(port), debug=debug, type=apptype)
