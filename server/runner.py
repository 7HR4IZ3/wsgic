import sys
import os
import webbrowser
from geventwebsocket.handler import WebSocketHandler

from .helpers import runscript
from ..helpers import config

root = os.getcwd()
sys.path.append(
    os.path.join(root, "apps")
)


def load(target, **namespace):
    # Source bottle.py:load
    module, target = target.split(":", 1) if ':' in target else (target, None)
    if module not in sys.modules:
        __import__(module)
    if not target:
        return sys.modules[module]
    if target.isalnum():
        return getattr(sys.modules[module], target)
    package_name = module.split('.')[0]
    namespace[package_name] = sys.modules[package_name]
    return eval('%s.%s' % (module, target), namespace)


def _get(data, index=0, e=None):
    try:
        return data[index] if type(data) in (list, dict, set, tuple) else data
    except:
        return e


def _cli_parse(args):  # pragma: no coverage
    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog="wsgic", usage="python -m %(prog)s [options] package.module:app")
    opt = parser.add_argument
    opt("--version", action="store_true", help="show version number.")
    opt("-b", "--bind", metavar="ADDRESS", help="bind socket to ADDRESS.")
    opt("-se", "--server", help="use SERVER as backend.")
    opt("-p", "--plugin", action="append", help="install additional plugin/s.")
    #  opt("-c", "--conf", action="append", metavar="FILE", help="load config values from FILE.")
    opt("-C", "--param", action="append",
        metavar="NAME=VALUE", help="override config values.")
    opt("-n", "--new", action="store_true", help="create new wsgi app.")
    opt("-s", "--script", action="store_true", help="run script then app.")
    opt("-a", "--asgi", action="store_true",
        help="run the asgi version of an app.")
    opt("-d", "--django", action="store_true", help="Run the django cli.")
    opt("-env", default="dev", help="set app environment")
    opt("--debug", action="store_true", help="start server in debug mode.")
    opt("--reload", action="store_true", help="auto-reload on file changes.")
    opt('app', help='WSGI app entry point.', nargs='*')

    cli_args = parser.parse_args(args[1:])
    return cli_args, parser


def parse_args(argv):
    runscript("wsgic.server", *argv[1:])

from werkzeug import run_simple

# run_simple()

class Apprunner:
    '''Application interface to initialize and run apps
    ::params::
        :app:
            :type: String
            Name of module
'''
    def __init__(self, app=None):
        self.wrapped = False
        self.servers = {
            "wsgi": {
                "werkzeug": lambda config: load("werkzeug:run_simple")(
                    config['host'], config['port'], config['app'], config['reloader'], config['debug'], reloader_interval=config['interval'], passthrough_errors=True, request_handler=WebSocketHandler, **config['kw']
                ),
                "bottle": lambda config: load("wsgic.thirdparty.bottle:run")(
                    config['app'], config['server'], config['host'], config['port'], config['interval'], config['reloader'], config['quiet'], config['plugins'], config['debug'], config['config'], **config['kw']
                )
            },
            "asgi": {
                "uvicorn": lambda config: load("uvicorn.main:run")(
                    config['app'], host=config['host'], port=config['port'], **config['kw']
                )
            }
        }

        if app:
            if isinstance(app, str):
                def_app = app
                try:
                    app = load(app.rstrip(".app")+".app")
                except ModuleNotFoundError:
                    try:
                        app = load(app.replace(".app", ""))
                    except ModuleNotFoundError:
                        raise ModuleNotFoundError(f"Module: {def_app} not found!") from None

                self.app = getattr(app, "__app__", None) or getattr(
                    app, "app", None)

                if not self.app:
                    self.app = getattr(app, "application")
                    self.wrapped = True
            else:
                self.wrapped = True
                self.app = app

    def run(self, server='bottle', host='127.0.0.1', port=None, interval=None, type="wsgi", reloader=None, quiet=None, plugins=None, debug=None, **kargs):
        app = (self.app.wrapped_app(type) if not self.wrapped else self.app)
        apptype = self.servers.get(type)
        bottle_server = "geventws"

        if type == "asgi" and server == "werkzeug":
            server = "uvicorn"

        if server.startswith("bottle"):
            servers = server.split(".")
            if len(servers) > 1:
                server, bottle_server = servers[0], servers[1]
            if bottle_server == "geventws":
                from gevent.monkey import patch_all; patch_all()

        func = apptype.get(server)
        if not func:
            if type == "wsgi":
                func = self.servers[type]["bottle"]
            elif type == "asgi":
                func = self.servers[type]["uvicorn"]

        func_config = {
            "app": app,
            "host": host or str(config.get("server.host", '127.0.0.1')),
            "port": port or int(config.get("server.port", 8100)),
            "interval": interval or int(config.get("server.interval", 1)),
            "reloader": reloader if reloader is not None else config.get("server.reloader", True),
            "quiet": quiet or config.get("server.debug", False),
            "plugins": plugins or None,
            "debug": debug or config.get("server.debug", False),
            "server": bottle_server,
            "config": None,
            "kw": kargs
        }

        if func:
            func(func_config)
        return

def run(app, **kwargs):
    runner = Apprunner(app)
    runner.run(**kwargs)
