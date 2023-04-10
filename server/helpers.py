from ..scripts import __all_scripts
from ..scripts.exceptions import ScriptNotFound
from ..helpers.extra import load_module
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
            app = load_module(app.rstrip(".app")+".app")
        except ModuleNotFoundError:
            try:
                app = load_module(app.replace(".app", ""))
            except ModuleNotFoundError:
                raise ModuleNotFoundError(f"Module: {def_app} not found!.")

        self.app = getattr(app, "__app__", None) or getattr(app, "application")

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

    def run(self, server='werkzeug', host='127.0.0.1', port=8080, interval=1, type="wsgi", reloader=True, quiet=False, plugins=None, debug=False, config=None, **kargs):
        app = self.app.wrapped_app(type)
        apptype = self.servers.get(type)
        bottle_server = "geventws"

        if type == "asgi" and server == "werkzeug":
            server = "uvicorn"

        if server.startswith("bottle"):
            servers = server.split(".")
            if len(servers) > 1:
                server, bottle_server = servers[0], servers[1]

        func = apptype.get(server)
        if not func:
            if type == "wsgi":
                func = self.servers[type]["werkzeug"]
            elif type == "asgi":
                func = self.servers[type]["uvicorn"]
        
        if func:
            if server.startswith("bottle"):
                kargs["server"] = bottle_server

            func(app, host=host, port=port, interval=interval, reloader=reloader, quiet=quiet, plugins=plugins, debug=debug, config=None, **kargs)

        return

def runscript(app, *args):
    try:
        load_module(app.replace(".app", "")+".scripts")
    except:
        load_module(app)

    scripts = __all_scripts
    func = scripts.get(args[0])
    if func:
        return func(*args[1:])
    else:
        raise ScriptNotFound("%s has no script named %s"%(app, args[0]))
