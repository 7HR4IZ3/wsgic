import types, inspect
import uuid
import asyncio

from functools import partial, wraps
from string import ascii_letters
from wsgic.thirdparty.bottle import load, Route as Route_, Router as Router_, makelist, py3k, redirect, getargspec
from wsgic.helpers.extra import get_global
from wsgic.helpers import config, ordered, hooks

from contextlib import contextmanager

from .convertors import get_convertors

def _get(data, index=0, e=None):
    try:return data[index] if type(data) in (list, dict, set, tuple) else data
    except:return e

def _url(x, ignore=None):
    if not ignore:
        ignore = not config.get("use.endslash", False)
    if len(x) >= 1:
        if not x.startswith('/'):x = f'/{x}'
    while '//' in x:
        x = x.replace('//', '/')
    if ignore is True:
        if x.endswith("/"):x = x[:-1]
    if x == "":x = "/"
    return x

def wrap(callback):
    def main(*a, **kw):
        return asyncio.run(callback(*a, **kw))
    return main


def yieldroutes(func):
    """ Return a generator for routes that match the signature (name, args)
    of the func parameter. This may yield more than one route if the function
    takes optional keyword arguments. The output is best described by example::

        a()         -> '/a'
        b(x, y)     -> '/b/<x>/<y>'
        c(x, y=5)   -> '/c/<x>' and '/c/<x>/<y>'
        d(x=5, y=6) -> '/d' and '/d/<x>' and '/d/<x>/<y>'
    """
    path = '/' + getattr(func, "__alias__", func.__name__).replace('__', '/').lstrip('/')
    spec = getargspec(func)
    argc = len(spec[0]) - len(spec[3] or [])
    path += ('/<%s>' * argc) % tuple(spec[0][:argc])
    yield path
    for arg in spec[0][argc:]:
        path += '/<%s>' % arg
        yield path

def compile_route(_route, **data):

    def main(seg):
        for x in list(data.keys()):
            if x in seg:
                if type(data[x]) is list and data[x] != []:
                    val = data[x].pop(0)
                    if data[x] == []:
                        data.pop(x)
                else:
                    val = data.pop(x)
                seg = seg.replace(x, str(val)).replace("<", '')
                if ":" in seg:
                    e = seg.find(">")
                    p = seg.find(":")
                    if e != -1:
                        seg = seg.replace(seg[p:e], "")
                seg = seg.replace(">", "")
        if "<" in seg and ">" in seg:
            raise Exception("No placeholder for: '%s' "%seg)
        return seg

    path = "/".join(str(main(x)) for x in _route.split("/"))
    return path

def route(name, e=None, app=None, i=0, query=None, **kw):
    data = ordered.get(name, index=i, app=app)
    if query:
        query = "?" + "&".join(f"{x}={str(query[x])}" for x in query)

    if data:
        if kw:
            data = compile_route(data, **kw)
        return data+(query or "")
    return (e or name)+(query or "")

class Route(Route_):
    def __init__(self, rule, method, callback, name=None, plugins=None, skiplist=None, **config):
        #: The path-rule string (e.g. ``/wiki/<page>``).
        self.rule = rule
        #: The HTTP method as a string (e.g. ``GET``).
        self.method = method
        #: The original callback with no plugins applied. Useful for introspection.
        self.callback = callback
        #: The name of the route (if specified) or ``None``.
        self.name = name or None
        #: A list of route-specific plugins (see :meth:`Bottle.route`).
        self.plugins = plugins or []
        #: A list of plugins to not apply to this route (see :meth:`Bottle.route`).
        self.skiplist = skiplist or []
        #: Additional keyword arguments passed to the :meth:`Bottle.route`
        #: decorator are stored in this dictionary. Used for route-specific
        #: plugin configuration and meta-data.
        self.config = config
    
    def re_init(self, app):
        self.app = app
        self.config = app.config._make_overlay().load_dict(self.config)
        return self
    
    def get_undecorated_callback(self):
        """ Return the callback. If the callback is a decorated function, try to
            recover the original function. """
        try:
            func = self.callback
            func = getattr(func, '__func__' if py3k else 'im_func', func)
            closure_attr = '__closure__' if py3k else 'func_closure'
            while hasattr(func, closure_attr) and getattr(func, closure_attr):
                attributes = getattr(func, closure_attr)
                func = attributes[0].cell_contents
    
                # in case of decorators with multiple arguments
                if not isinstance(func, types.FunctionType):
                    # pick first FunctionType instance from multiple arguments
                    func = filter(lambda x: isinstance(x, types.FunctionType),
                                  map(lambda x: x.cell_contents, attributes))
                    func = list(func)[0]  # py3 support
            return func
        except IndexError:
            return self.callback
    
    
    def __repr__(self):
        cb = self.callback
        return '<%s %s -> %s:%s>' % (self.method, self.rule, cb.__module__, cb.__name__)

class Routes:
    def __init__(self, start="<", end=">", seperator=":",  engine="complex", **kw):
        self.data = []
        self.plugins = []
        self.mounts = {}
        self.filters = {}
        self.errors = {}
        self.placeholder_ = kw.pop("placeholder", None) or "arg"

        self.start, self.end, self.sep, self.engine = start, end, seperator, engine
        self.config = {
            "base_view": None,
            "app": None,
            "prefix": ""
        }

    def placeholder(self, name, regex, to_py=None, in_url=None):
        self.filters[name] = lambda conf: (regex, to_py, in_url)

    def set(self, start=None, end=None, seperator=None,  engine=None):
        self.start, self.end, self.sep, self.engine = start or self.start, end or self.end, seperator or self.sep, engine or self.engine

    @contextmanager
    def use(self, view):
        try:
            self.config["base_view"] = view
            yield self
        finally:
            self.config["base_view"] = None

    @contextmanager
    def group(self, path):
        try:
            pf = self.config["prefix"]
            self.config["prefix"] = path
            yield self
        finally:
            self.config["prefix"] = pf


    def _compile(self, url):
        if self.engine == "simple":
            return self._remake_simple(url, self.start, self.end, self.sep)
        else:
            return self._remake(url, self.start, self.end, self.sep, self.placeholder_)
    
    def _remake(self, line, start="<", end=">", sep=":", placeholder="arg"):
        seg = line.split("/")
        d = []
        anons_count = 0
        for segment in seg:
            if start in segment and end in segment:
                segment = self._conv(segment, start, end, sep)
            elif segment != "" and ("(" in segment or "[" in segment or segment.lstrip()[0] not in ascii_letters) and (not segment.startswith('<') and not segment.endswith('>')):
                if segment == "*":
                    segment = ".*"
                segment = "<"+(placeholder+str(anons_count) if anons_count >= 1 else placeholder)+":re:"+segment+">"
                anons_count+=1
            d.append(segment)
        data = "/".join(d)
        return data
    
    def _conv(self, line, start, end, sep):
        if type(start) is str and start != "" and start in line:
            line = f"{start}".join(x for x in line.split(start)[1:]).strip()
        if type(sep) is str and sep != "" and sep in line:
            new = line.split(sep)
            line = ":".join(x.strip() for x in new)#new[0].strip()+":"+new[1].strip()
        if type(end) is str and end != "" and end in line:
            line = f"{end}".join(x for x in line.split(end)[:1]).strip()
        line = "<"+line.strip()+">"
        return line
    
    def _remake_simple(self, line, s="<", e=">", p=":"):
        if s != "":line = line.replace(s, "<").strip()
        if p != "": line = line.replace(p, ":").strip()
        if e != "":line = line.replace(e, ">").strip()
        return line
    
    def add_name(self, name, rule, strict=False):
        if name in ordered and not strict:
            if rule not in ordered[name]:
                ordered[name].insert(0, rule)
        else:
            ordered[name] = makelist(rule)
    
    def route(self, name, e=None, i=0, **kw):
        return route(name, e=e, i=i, **kw)

    def add(self, path, callback=None, method=["GET", "POST", 'PUT', 'DELETE', "CLI"], name=None, apply=None, skip=None, **config):
        plugins = makelist(apply)
        skiplist = makelist(skip)
        rule = makelist(path(callback, name) if callable(path) else path)

        def wrapper(callback):
            data = []
            if isinstance(callback, str):
                if self.config['base_view'] and hasattr(self.config['base_view'], callback):
                    callback = getattr(self.config['base_view'], callback)
                    for dec in self.config['base_view'].decorators:
                        callback = dec(callback)
                else:
                    callback = load(callback)

            if inspect.iscoroutinefunction(callback):
                callback = wrap(callback)

            for path in rule:
                if self.config['prefix']:
                    path = self.config['prefix'] + "/" + path
                path = self._compile(_url(path))
                if name:
                #     print("add", name, path)
                    ordered.add(name, path)
                for verb in makelist(method):
                    route = Route(path, verb, callback, name=name, plugins=plugins, skiplist=skiplist, **config)
                    data.append(route)
            self.data = self.data + data
            return data[0] if len(data) == 1 else data
        return wrapper(callback) if callback else wrapper
    
    def include(self, routes=None, path=""):
        for route in routes.data:
            if self.config["prefix"]:
                route.rule = _url(self.config['prefix'] + "/" + path + "/" + route.rule)
            else:
                route.rule = _url(path + "/" + route.rule)
            self.data.append(route)
        for mount in routes.mounts:
            self.mounts[mount] = routes.mounts[mount]
    
    def get(self, path, callback=None, name=None, **kwargs):
        return self.add(path, callback, name=name, method="GET", **kwargs)

    def post(self, path, callback=None, name=None, **kwargs):
        return self.add(path, callback, name=name, method="POST", **kwargs)

    def put(self, path, callback=None, name=None, **kwargs):
        return self.add(path, callback, name=name, method="PUT", **kwargs)

    def delete(self, path, callback=None, name=None, **kwargs):
        return self.add(path, callback, name=name, method="DELETE", **kwargs)

    def cli(self, path, callback=None, name=None, **kwargs):
        return self.add(path, callback, name=name, method="CLI", **kwargs)
    
    def resource(self, path, callback=None, mapping=None, name=None, key="id", create=None, skip=None, methods=None, **kwargs):

        def wrapper(callback, wrapped=False):
            if wrapped:
                callback = callback()
            mappings = {
                'index': '{path}',
                'create': '{path}/',
                'retrieve': '{path}/{key}',
                'edit': '{path}/{key}/edit',
                'update': '{path}/{key}',
                'delete': '{path}/{key}',
            }
            mappings.update(mapping or {})

            methodss = {
                "index": "get",
                "create": "post",
                "retrieve": "get",
                "edit": "put",
                "update": ["put", "patch"],
                "delete": "delete"
            }
            methodss.update(methods or {})

            createw = create or list(mappings.keys())
            skipp = skip or []

            for func, rule in mappings.items():
                if func in createw and func not in skipp:
                    callback_func = getattr(callback, func, None)

                    if callback_func is None:
                        continue

                    if hasattr(callback, "get_auth_wrapper"):
                        callback_func = callback.get_auth_wrapper(callback_func)

                    for dec in getattr(callback, 'decorators', []):
                        callback_func = dec(callback_func)

                    for method in makelist(methodss.get(func)):
                        if self.config['prefix']:
                            _ = self.config['prefix'] + "/" + path
                        else:_=path
                        rule = _url(rule.format(path=_, key=f"<{key}>"))
                        self.data.append(
                            Route(rule, method.upper(), callback_func, name=name, **kwargs)
                        )
        return wrapper(callback) if callback else partial(wrapper, wrapped=True)

    def error(self, code=404, callback=None):
        def decorator(callback):
            for c in makelist(code):
                if isinstance(callback, str): callback = load(callback)
                self.errors[int(c)] = callback
            return callback

        return decorator(callback) if callback else decorator

    def redirect(self, path, target, code=302, data={}, method=["GET", "POST", 'PUT', 'DELETE'], name=None):
        if str(target).startswith(":"):
            if target[1:] not in ordered:
                raise LookupError("No route with name'%s'"%target[1:])
            target = route(target[1:], **data)
        if self.config['prefix']:
            path = self.config['prefix'] + "/" + path.rstrip("/")
        return self.add(path, lambda: redirect(target, code), method, name=name)
    
    def mount(self, mount, app, apptype="wsgi", name=None, wrapped=False):
        from wsgic.apps import get_app
        if type(app) is str:
            app, framework = str(app).split("::")
            app = get_app(app, framework)
        else:
            framework = app.name

        if self.config['prefix']:
            mount = self.config['prefix'] + "/" + mount.rstrip("/")

        if app:
            url = _url("/"+mount)
            app.mountpoint = url
            app.setup()

            if wrapped:
                app_ = app.wrapped_app(apptype)
            else:
                if apptype == "wsgi":
                    app_ = app._wsgi()
                elif apptype == "asgi":
                    app_ = app._asgi()
                else:
                    raise Exception
            
            routes = app._routes()

            for filtr in routes.filters:
                self.filters[filtr] = routes.filters[filtr]

            for route in routes.data:
                route.rule = _url("/" + mount + "/" + route.rule, framework != 'django')
                if route.name:
            #         print('mount', route.name, route.rule)
                    ordered.pop(route.name, app=name, index=-1)
                    ordered.add(route.name, route.rule, app=name)
                self.data.append(route)
            self.mounts[url] = app_
    
    def view(self, rule, view=None, name=None, apply=None, skip=None, **config):
        def main(view, wrapped=False):
            if wrapped or (not hasattr(view, "_")):
                view = view()
            if hasattr(view, "setup_routes"):
                routes = view.setup_routes(self)
            routes = view._
            
            plugins = makelist(apply)
            skiplist = makelist(skip)
        
            for route in routes:
                if self.config["prefix"]:
                    route.rule = _url(self.config['prefix'] + "/" + rule + "/" + route.rule)
                else:
                    route.rule = _url(rule + "/" + route.rule)
                if name:
                    route.name = name + route.name
                    ordered.add(route.name, route.rule)
                route.plugins = plugins
                route.skiplist = skiplist
                route.config = config

                for dec in getattr(view, 'decorators', []):
                    route.callback = dec(route.callback)
                    
                self.data.append(route)
        return main(view) if view else partial(main, wrapped=True)
    
    def expose(self, callback=None, method=["GET", "POST", 'PUT', 'DELETE', "CLI"], name=None, apply=None, skip=None, **config):
        return self.add(lambda func, name: list(yieldroutes(func)), callback, method, name=name, apply=apply, skip=skip, **config)
    
    def static(self, rule, store=None, name=None, apply=None, skip=None, **config):
        def main(store):
            if self.config["prefix"]:
                rulee = _url(self.config['prefix'] + "/" + rule)
            else:
                rulee = rule
            namee = name or rulee.strip("/")
            rulee = rulee.rstrip("/")+"/<path:path>"
            store._main()._handlers[store.config["directory"]] = namee
            if namee:
                ordered.add(namee, rulee)
            route_ = Route(rulee, "GET", lambda path: store.handler(path, **config), name=namee, plugins=makelist(apply), skiplist=makelist(skip), **config)
            self.data.append(route_)
            return route_
        return main(store) if store else main

    def install(self, plugin=None):
        """ Add a plugin to the list of plugins and prepare it for being
            applied to all routes of this application. A plugin may be a simple
            decorator or an object that implements the :class:`Plugin` wsgic.
        """
        def main(plugin):
            self.plugins.append(plugin)
            return plugin
        return main(plugin) if plugin else main

    def uninstall(self, plugin):
        """ Uninstall plugins. Pass an instance to remove a specific plugin, a type
            object to remove all plugins that match that type, a string to remove
            all plugins with a matching ``name`` attribute or ``True`` to remove all
            plugins. Return the list of removed plugins. """
        removed, remove = [], plugin
        for i, plugin in list(enumerate(self.plugins))[::-1]:
            if remove is True or remove is plugin or remove is type(plugin) \
            or getattr(plugin, 'name', True) == remove:
                removed.append(plugin)
                del self.plugins[i]
                if hasattr(plugin, 'close'): plugin.close()
        if removed: self.reset()
        return removed

    def reset(self, route=None):
        """ Reset all routes (force plugins to be re-applied) and clear all
            caches. If an ID or route object is given, only that specific route
            is affected. """
        if route is None: routes = self.data
        elif isinstance(route, Route): routes = route.data
        else: routes = [self.data[route]]
        for route in routes:
            route.reset()
        if config.get('DEBUG'):
            for route in routes:
                route.prepare()
        hooks.trigger('app_reset')

class Router(Router_):
    def __init__(self, routes=None, strict=False):
        self.routes = routes or Routes()
        super().__init__(strict=strict)
        self.app = None
        self.filters = get_convertors()
        # self.filters['uuid'] = lambda conf: (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", uuid.UUID, lambda x: str(x))
    
    def get_routes(self):
        return self, self.routes
    
    def set_routes(self, routes):
        self.routes = routes
        return routes
    
    def init(self, app):
        self.app = app
#         self.app.__dict__['plugins'] = self.routes.plugins
        for filtr in self.routes.filters:
            self.add_filter(filtr, self.routes.filters[filtr])
        for route in self.routes.data:
            route.re_init(app)
            # if route.name:
            #     print("init", route.name, route.rule)
            #     ordered.add(route.name, route.rule)
            self.add_route(route)
        return self
    
    def route(self, name, e=None, i=0):
        data = ordered.get(name, e=e, index=i)
        return data

    def add_route(self, route):
        super().add(route.rule, route.method, route, name=route.name)
    
    def add_name(self, name, rule, strict=False):
        if name in ordered and not strict:
            if rule not in ordered[name]:
                ordered[name].insert(0, rule)
        else:
            ordered[name] = makelist(rule)
    
    def remove_name(self, name):
        if name in ordered:
            return ordered.pop(name)
    
    def make_mounts(self):

        mounts = self.routes.mounts
        for mount in mounts:
            self.app.mount(mount, mounts[mount])
    
    def import_router(self, path, router):
        for mount in router.routes.mounts:
            self.routes.mounts[mount] = router.routes.mounts[mount]
        for route in router.routes.data:
            route.rule = _url(path + "/" + route.rule)
            self.routes.data.append(route)

