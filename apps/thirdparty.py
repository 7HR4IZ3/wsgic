from .base import *


class BottleApp(App):
    '''Application interface for bottle'''
    name = "bottle"

    def __init__(self, module, name=None):
        module = module.split(":")
        self.module = module[0]
        self._name = name
        if isinstance(self.module, str):
            self.module = load(self.module)
        if len(module) == 2:
            self.appname = module[1]
        else:
            self.appname = "app"
        try:
            self.app = getattr(self.module, self.appname)
        except AttributeError:
            self.app = getattr(self.module, "__app__")

    def _wsgi(self):
        return self.app.wsgi
    
    def _routes(self):
        routes = Routes()
        routes.data = self.app.routes
        return routes

class FlaskApp(BottleApp):
    '''Application interface for flask'''
    name = "flask"
    def __init__(self, module, name=None):
        super().__init__(module)
        self._name = name
        self.routes = Routes()
        self.map = self.app.url_map
        self.view_functions = self.app.view_functions

    def _wsgi(self):
        return self.app.wsgi_app
    
    def setup(self):
        for rule in self.map._rules:
            path = rule.rule
            method = rule.methods
            alias = rule.alias or None
            if self._name and alias:
                alias = self._name + "_" + alias
            endpoint = self.view_functions[rule.endpoint]

            for verb in method:
                self.routes.data.append(Route(self.remake_url(str(path)), verb, endpoint, name=alias))

    def _routes(self):
        return self.routes
    
    def remake_url(self, url):
        if "/" in url:
            new = "/".join([self.remake_url(u) for u in url.split("/")])
        if ":" in url and "<" in url and ">" in url:
            lb = url.find("<")
            rb = url.find(">")
            new = url[lb+1:rb]
            left, right = new.split(":")
            new = "<" + ":".join([right, left]) + ">"
        else:new = url
        return new

class PyramidApp(FlaskApp):
    '''Application interface for pyramid'''
    name = "pyramid"
    def __app__(self):
        return self.app

class DjangoApp:
    '''Application interface for django'''
    name = "django"
    def __init__(self, module, name=None):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.settings'%module)
        self._name = name
        self.module = module

    def setup(self):
        self.wsgi_app = load("%s.%s"%(self.module, "wsgi")).application
        self.asgi_app = load("%s.%s"%(self.module, "asgi")).application

        self.routes = Routes()
        self.URLPattern, self.URLResolver = require("django.urls.resolvers:URLPattern", "django.urls.resolvers:URLResolver")()
        self.make_routes(load("%s.%s"%(self.module, "urls")))

    def _routes(self):
        return self.routes

    def _wsgi(self):
        return self.wsgi_app
    
    def _asgi(self):
        return self.asgi_app

    def make_routes(self, urls):
        allurls = urls.urlpatterns
        for url in allurls:
            if isinstance(url, self.URLResolver):
                self.process_resolver(url)
            elif isinstance(url, self.URLPattern):
                self.process_pattern(url)
        return

    def remake_url(self, url):
        if "/" in url:
            new = "/".join([self.remake_url(u) for u in url.split("/")])
        if ":" in url and "<" in url and ">" in url:
            lb = url.find("<")
            rb = url.find(">")
            new = url[lb+1:rb]
            left, right = new.split(":")
            new = "<" + ":".join([right, left]) + ">"
        else:new = url
        return new

    def process_pattern(self, pattern, path=""):
        name = pattern.name
        if self._name and name:
            name = self._name + "_" + name
        path =  self.remake_url(str(path + str(pattern.pattern)))
        callback = pattern.callback
        self.routes.data.append(Route(path, "GET", callback, name=name))


    def process_resolver(self, resolver, path=""):
        name = resolver.urlconf_name
        path = path + str(resolver.pattern)

        if isinstance(name, list):
            for item in name:
                if isinstance(item, self.URLPattern):
                    self.process_pattern(item, path)
                elif isinstance(item, self.URLResolver):
                    self.process_resolver(item, path)
        elif isinstance(name, types.ModuleType):
            for item in name.urlpatterns:
                if isinstance(item, self.URLPattern):
                    self.process_pattern(item, path)
                elif isinstance(item, self.URLResolver):
                    self.process_resolver(item, path)

class WsgicApp(BottleApp):
    '''Application interface for wsgic'''
    name = "wsgic"
    def __init__(self, module, name=None):
        modules = module.split(":")
        modules[0] = modules[0].replace(".app", "") + ".app"
        module = "".join(modules)
        super().__init__(module, name)
    
    def _wsgi(self):
        return self.app._wsgi()
    
    def _asgi(self):
        return self.app._asgi()
    
    def setup(self):
        return self.app.setup()

    def _routes(self):
        return self.app._routes()

class SanicApp(FlaskApp):
    name = "sanic"
    pass

class GeventApp(App):
    name ="gevent"
    pass

__apps__ = {
    "bottle": BottleApp,
    "django": DjangoApp,
    "flask": FlaskApp,
    "pyramid": PyramidApp,
    "wsgic": WsgicApp
}

def get_app(app, framework=None, *a, **kw):
    if not framework:
        if isinstance(app, tuple(__apps__.values())):
            return app
    if framework in __apps__:
        return __apps__[framework](app, *a, **kw)
    else:
        return None