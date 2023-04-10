from . import Routes, makelist, load_module, inspect, wrap, ordered, _url
from ..thirdparty.bottle import HTTPError
from ..http import request

from werkzeug.routing import Map, RuleFactory, Rule
from werkzeug.exceptions import MethodNotAllowed, NotFound
from werkzeug.routing import *


class MapRoute(Rule):
    def call(self, **kw):
        return self.endpoint(**kw)

class MapRoutes(Routes, RuleFactory):
    def __init__(self, data=None, start="<", end=">", seperator=":", engine="complex", **kw):
        super().__init__(data, start, end, seperator, engine, **kw)
        self.view_functions = {}

    def get_rules(self, map):
        return self.data

    def add(self, path, callback=None, method=["GET", "POST", 'PUT', 'DELETE', "CLI"], name=None, apply=None, skip=None, **config):
        rule = makelist(path(callback, name) if callable(path) else path)

        def wrapper(callback):
            data = []
            if isinstance(callback, str):
                if self.config['base_view'] and hasattr(self.config['base_view'], callback):
                    callback = getattr(self.config['base_view'], callback)
                    for dec in self.config['base_view'].decorators:
                        callback = dec(callback)
                else:
                    callback = load_module(callback)

            if inspect.iscoroutinefunction(callback):
                callback = wrap(callback)

            for path in rule:
                if self.config['prefix']:
                    path = self.config['prefix'] + "/" + path
                path = self._compile(_url(path))
                if name:
                    ordered.add(name, path)

                route = MapRoute(path, methods=makelist(method), endpoint=callback, **config)
                data.append(route)

            self.data = self.data + data
            return data[0] if len(data) == 1 else data
        return wrapper(callback) if callback else wrapper

    def websocket(self, path=None, callback=None, name=None, apply=None, skip=None, **config):
        def decorator(callback):
            if isinstance(callback, str):
                callback = load_module(callback)
            return self.get(
                path=path, websocket=True,
                callback=self.__websocket_responder(callback),
                name=name, **config
            )
        return decorator(callback) if callback else decorator

class MapRouter:
    def __init__(self, routes=None):
        if routes:
            if isinstance(routes, list):
                self.routes = MapRoutes(routes)
            elif isinstance(routes, MapRoutes):
                self.routes = routes
        else:
            self.routes = MapRoutes()
    
    def add(rule, method, route, name):
        pass

    def match(self, environ):
        try:
            return Map(self.routes).bind_to_environ(environ).match()
        except NotFound:
            raise HTTPError(404, "Not found: " + repr(request.path)) from None
        except MethodNotAllowed:
            raise HTTPError(405, "Method not allowed.") from None
