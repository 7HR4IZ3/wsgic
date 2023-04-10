import types, os
from copy import copy

try:
    from a2wsgi import WSGIMiddleware, ASGIMiddleware
except ImportError:
    WSGIMiddleware = ASGIMiddleware = None

from wsgic.thirdparty.bottle import (TEMPLATE_PATH, Bottle, makelist, load, cached_property, static_file)
from wsgic.http import request
from wsgic.helpers import config as BaseConfig, Config, is_main_app, hooks, Hooks
from wsgic.helpers.require import require
from wsgic.helpers.extra import _get, get_global, set_global
from wsgic.routing import Route, Router, Routes


class App:
    '''Base interface for all apps.

    Required methods
        wsgi
            Returns the app wsgi interface
        asgi
            Returns the app asgi interface
        setup
            Initializes the app and calls necessary methods
        routes
            Returns `wsgic.routing.Routes` object containing app routes
'''
    mountpoint = None
    
    def __init__(self, module=None, name=None):
        pass
    def _wsgi(self):
        return self.wsgi
    def _asgi(self):
        return WSGIMiddleware(self._wsgi())
    def _routes(self):
        return getattr(self, "routes", Routes())
    def setup(self):
        pass

    @cached_property
    def wrapped_wsgi(self):
        app = self._wsgi()

        for middleware in self.config.get("middlewares.wsgi", []):
            middleware = makelist(middleware)
            main = middleware[0]

            if isinstance(main, str):
                main = load(main)
            app = main(app, *_get(middleware, 2, []), **_get(middleware, 3, {}))
        return app

    @cached_property
    def wrapped_asgi(self):
        app = self._asgi()

        for middleware in self.config.get("middlewares.asgi", []):
            middleware = makelist(middleware)
            main = middleware[0]

            if isinstance(main, str):
                main = load(main)
            app = main(app, *_get(middleware, 2, []), **_get(middleware, 3, {}))
        return app

    def wrapped_app(self, type="wsgi"):
        if type == "wsgi":
            return self.wrapped_wsgi
        elif type == "asgi":
            return self.wrapped_asgi
        else:
            raise ValueError("No app type %s"%type)
