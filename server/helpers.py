from ..scripts import BaseScripts, __all_scripts
from ..scripts.exceptions import ScriptNotFound
from ..thirdparty.bottle import run, load
from ..helpers.extra import set_global, get_global, load_module
from ..helpers import config

class Apprunner:
    '''Application interface to initialize and run apps
    ::params::
        :app:
            :type: String
            Name of module
'''
    def __init__(self, app):
        try:
            def_app = app
            app = load(app.rstrip(".app")+".app")
        except ModuleNotFoundError:
            try:
                app = load(app.replace(".app", ""))
            except ModuleNotFoundError:
                raise ModuleNotFoundError(f"Module: {def_app} not found!.")

        self.app = app.__app__
        set_global("app", self.app)

        self.servers = {
            "wsgi": {
                "werkzeug": lambda app, host=str(config.get("server.host", '127.0.0.1')), port=int(config.get("server.port", 7000)), interval=int(config.get("server.interval", 1)), reloader=config.get("server.reloader", False), debug=config.get("server.debug", False), quiet=False, plugins=None, config=None, **kw: load_module("werkzeug:run_simple")(
                    host, port, app, reloader, debug, reloader_interval=interval, passthrough_errors=True, **kw
                ),
                "bottle": lambda app, host=str(config.get("server.host", '127.0.0.1')), port=int(config.get("server.port", 7000)), interval=int(config.get("server.interval", 60)), server='wsgiref', reloader=config.get("server.reloader", False), quiet=False, plugins=None, debug=config.get("server.debug", False), config=None, **kw: load_module("wsgic.thirdparty.bottle:run")(
                        app, server, host, port, interval, reloader, quiet, plugins, debug, config, **kw
                    )
            },
            "asgi": {
                "uvicorn": lambda app, host=str(config.get("server.host", '127.0.0.1')), port=int(config.get("server.port", 7000)), interval=int(config.get("server.interval", 1)), reloader=config.get("server.reloader", False), quiet=False, plugins=None, debug=config.get("server.debug", False), config=None, **kw: load_module("uvicorn.main:run")(
                        app, host=host, port=port, **kw
                    )
            }
        }
    
    def init_app(self):
        self.app.setup()

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

    def run(self, server='werkzeug', host='127.0.0.1', port=8080, interval=1, type="wsgi", reloader=True, quiet=False, plugins=None, debug=False, config=None, **kargs):
        app = self.app.wrapped_app(type)
        apptype = self.servers.get(type)
        bottle_server = "wsgiref"

        if type == "asgi" and server == "werzkeug":
            server = "uvicorn"

        func = apptype.get(server)

        if server.startswith("bottle"):
            servers = server.split(".")
            if len(servers) > 1:
                server, bottle_server = servers[0], servers[1]

        if not func:
            if type == "wsgi":
                func = self.servers[type]["werkzeug"]
            elif type == "asgi":
                func = self.servers[type]["uvicorn"]
        
        if func:
            if server.startswith("bottle"):
                kargs["server"] = bottle_server

            func(app, host=host, port=port, interval=interval, reloader=reloader, quiet=quiet, plugins=plugins, debug=debug, config=None, **kargs)

        # if type == "wsgi":
        #     from werkzeug import run_simple
        #     run_simple(
        #         host, port, app, reloader, debug, reloader_interval=interval
        #     )
        #     # from bottle import run
        #     # if server == "gevent":
        #     #     from gevent import monkey;monkey.patch_all()
        #     # run(app, server=server, host=host, port=port, interval=interval, reloader=reloader, debug=debug, qquiet=quiet)
        # elif type == "asgi":
        #     from uvicorn.main import run
        #     run(
        #         app, host=host, port=port, debug=debug
        #     )
        return
#         if server == "gevent":
#             from gevent import monkey
#             monkey.patch_all()
#         # run(app=self.get_middlewares(), **kw)
#         return run(self.app, server=server, host=host, port=port, debug=debug, interval=interval, reloader=reloader, quiet=quiet, plugins=plugins, config=config, **kargs)

# def url(func=None, method=None, name=None, apply=None, skip=None):
#     return (func, method, name, apply, skip)


# def runscript(app, *args):
#     targetapp = load(app.replace(".app", "")+".scripts")
#     appglobals = {x: getattr(targetapp, x) for x in dir(targetapp)}
#     func = appglobals.get(args[0])
#     if func:
#         return func(*args[1:])
#     else:
#         for item in appglobals.values():
#             if callable(item) and hasattr(item, args[0]):
#                 item = item()
#                 func = getattr(item, args[0], None)
#                 if func:
#                     return func(*args[1:])
#     raise AttributeError

def runscript(app, *args):
    try:
        load(app.replace(".app", "")+".scripts")
    except:
        load(app)
    scripts = __all_scripts
    func = scripts.get(args[0])
    if func:
        return func(*args[1:])
    else:
        raise ScriptNotFound("%s has no script named %s"%(app, args[0]))
