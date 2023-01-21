import types
import inspect
from functools import partial
from wsgic.thirdparty.bottle import getargspec
from wsgic.helpers import hooks
from wsgic.helpers.extra import _get
from wsgic.routing import Route, route
from wsgic.http import JsonResponse, XmlResponse, request, response
from wsgic.helpers import config, messages, errors
from wsgic.utils import conditional_kwargs

from .templates import template, view, load, Jinja2Template
from .context import Context

adapter = config.get("static.template.engine", Jinja2Template)

if isinstance(adapter, str):
    adapter = load(adapter)

class List(list):
    def add(self, item):
        if item not in self:
            super().append(item)
        return ""

GLOBALS = {
    "route": route,
    "request": request,
    "response": response,
    "load": load,
    "config": config,
    "messages": messages,
    "errors": errors,
    "repr": repr,
    "len": len,

    "setattr": setattr,
    "getattr": getattr,
    "scripts": List(),
    "styles": List(),
}

class BaseView:
    decorators = []

class View(BaseView):
    def __init__(self, *args, **kwargs):
        self.__name__ = self.__class__.__name__
        super().__init__(*args, **kwargs)
        self._ = [
            Route("", "GET", self.get, name="_get"),
            Route("", "POST", self.post, name="_post"),
            Route("<id:int>", "GET", self.retrieve, name="_retrieve"),
            Route("<id:int>", "PUT", self.put, name="_put"),
            Route("<id:int>", "DELETE", self.delete, name="_delete"),
        ]

    # Dummy request handlers .... to be overwritten
    def get(self):
        pass
    def post(self):
        pass
    def delete(self, id):
        pass
    def put(self, id):
        pass
    def retrieve(self, id):
        pass

class FunctionView(BaseView):
    _restricted_methods = None

    def __init__(self):
        super().__init__()
        self._ = []
        self._restricted_methods = self._restricted_methods or []

        for item in self.__class__.__dict__:
            data = self.__class__.__dict__[item]

            if isinstance(data, (types.MethodType, types.LambdaType)) and not item.startswith("_") and item not in self._restricted_methods:
                if item.lower().startswith("get_"):
                    name = item[4:]
                    method = "GET"
                elif item.lower().startswith("post_"):
                    name = item[5:]
                    method = "POST"
                elif item.lower().startswith("put_"):
                    name = item[4:]
                    method = "PUT"
                elif item.lower().startswith("delete_"):
                    name = item[7:]
                    method = "DELETE"
                else:
                    name = item
                    method = "GET"
                paths = list(self._yieldroutes(data, name=name or "/"))
                for path in paths:
                    self._.append(
                        Route(path, method, data, name="_"+item)
                    )

    def _yieldroutes(self, func, name=None):
        path = '/' + (name or func.__name__).replace('__', '/').lstrip('/')
        spec = getargspec(func)
        argc = len(spec[0]) - len(spec[3] or [])
        path += ('/<%s>' * (argc)) % tuple(spec[0][:argc])
        yield path
        for arg in spec[0][argc:]:
            path += '/<%s>' % arg
            yield path


# class Wrap:
#     def __init__(self, f, m):
#         self.f = f
#         self.m = m
    
#     def __call__(self, *args, **kwargs):
#         return self.f(*self.m, *args, **kwargs)

# def requests(*a):
#     def wraps(view):
#         return Wrap(view, a)
#     return wraps


# @singledispatch
def render(source, *args, engine=adapter, **kwargs):
    context = kwargs.pop("context", None) or _get(args, 1) or {}
    context = Context(**GLOBALS, **config.get("static.template.globals", {}, raw=True), **context)

    templat = partial(template, template_adapter=engine)
    template_setings=config.get("static.template.config")

    hooks.trigger(
        "before_render",
        lambda callback: conditional_kwargs(callback, {
            "source": source,
            "name": source,
            "context": context,
            "engine": templat
        })
    )

    return templat(source, context.as_dict(), *args, template_setings=template_setings, **kwargs)

# @render.register(types.FunctionType)
# def _(func, engine=adapter):
#     return partial(view, template_adapter=engine)