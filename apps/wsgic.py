import functools
import os

from ..http import *
from ..routing.exceptions import *
from ..thirdparty.bottle import ResourceManager, run
from ..helpers.extra import _get, set_global as _sg

from .base import *


_root = os.getcwd()
if os.path.exists(os.path.join(_root, "apps")):
    _sg("APPSDIR", os.path.join(_root, "apps"))
else:
    _sg("APPSDIR", _root)

_sg("ROOTDIR", _root)
_sg("APPDIR", os.path.join(_root, 'apps'))


class WSGIApp(Bottle, App):
    name = "wsgic"
    mountpoint = None

    def __init__(self, router=None, config=None):
        #: A :class:`ConfigDict` for app specific configuration.
        self.__initialized = False
        self.config = Config().use(config) if config else BaseConfig
        self.config.meta_set('catchall', 'validate', bool)

        self.config._add_change_listener(
            functools.partial(self.trigger_hook, 'config')
        )

        self.config.update({
            "catchall": True
        })
        self.config['json.disable'] = True

        _sg("APPMODULE", self)
        _sg("installed_apps", {})

        #: A :class:`ResourceManager` for application files
        self.resources = ResourceManager()

        # self.routes = []  # List of installed :class:`Route` instances.
        # self.router = Router()  # Maps requests to :class:`Route` instances.
        self.error_handler = {}

        # Core plugins
        self.plugins = [] 
        # List of installed plugins.
        # self.install(JSONPlugin())
        # self.install(TemplatePlugin())

        #: If true, most exceptions are caught and returned as :exc:`HTTPError`
        self.catchall = self.config.get('catchall', False)

        if not router:
            self.router = Router()
        elif type(router) is str:
            self.router = load(router)
        elif isinstance(router, Router):
            self.router = router
        else:
            raise TypeError("Router object must either be a string or a 'Router' instance.")

        if is_main_app(str(self.__class__.__name__)) and self.config.get("use.static", False):
            store = self.config.get("static.assets.store", "wsgic.handlers.files:FileSystemStorage")
            if isinstance(store, str):
                store = load(store)
            self.static(
                self.config.get('static.assets.url', '/assets').rstrip('/'),
                store(directory=self.config.get("static.assets.dir", "./assets"))
            )

        self.error_handler = self.router.routes.errors
        self.trigger_hook("app_created", self)

    def add(self, path, callback=None, method=["GET", "POST", 'PUT', 'DELETE', "CLI"], name=None, apply=None, skip=None, **config):
        return self.router.routes.add(path, callback, method, name, apply, skip, **config)

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
        return self.router.routes.resource(path, callback, mapping, name, key, create, skip, methods, **kwargs)

    def error(self, code=404, callback=None):
        return self.router.routes.error(code, callback)

    def view(self, rule, view=None, name=None, apply=None, skip=None, **config):
        return self.router.routes.view(rule, view, name, apply, skip, **config)
    
    def expose(self, callback=None, method=["GET", "POST", 'PUT', 'DELETE', "CLI"], name=None, apply=None, skip=None, **config):
        return self.router.routes.expose(callback, method, name, apply, skip, **config)
    
    def redirect(self, path, target, code=302, data={}, method=["GET", "POST", 'PUT', 'DELETE'], name=None):
        return self.router.routes.redirect(path, target, code, data, method, name)

    def static(self, rule, store=None, name=None, apply=None, skip=None, **config):
        return self.router.routes.static(rule, store, name, apply, skip, **config)

    def websocket(self, path, callback=None, name=None, apply=None, skip=None, **config):
        return self.router.routes.websocket(path, callback, name, apply, skip, **config)
 
    def web_route(self, path, callback=None, name=None, apply=None, skip=None, **config):
        return self.router.routes.web_route(path, callback, name, apply, skip, **config)
 
    @property
    def _hooks(self):
        return Hooks.from_dict(hooks._)

    @property
    def routes(self):
        return self.router.routes.data

    def _routes(self):
        return self.router.routes
    
    def trigger_hook(self, name, *args, **kwargs):
        return self._hooks.trigger(name, *args, **kwargs)
    
    def wrapped_app(self, type="wsgi"):
        self.setup()
        return super().wrapped_app(type=type)

    def setup(self):
        if self.__initialized:
            return

        self.trigger_hook("before_app_setup", self)
        self.router.init(self)
    
        if self.router.routes.mounts != {}:
            self.router.make_mounts()
        
        for path in self.config.get("static.template.dirs", ["./templates/", "./apps/{app_name}/templates/", "./apps/{app_name}/template/"]):
            if path not in TEMPLATE_PATH:
                path = str(path).format(app_name=str(self.__class__.__name__).lower().replace('app', ''))
                TEMPLATE_PATH.insert(0, path)
        
        self.setup_plugins()

        self.trigger_hook("app_setup", self)
        self.__initialized = True
        from wsgic import services
        return self
    
    def setup_plugins(self):
        for plugin in self.config.get("plugins", []) + self.router.routes.plugins:
            plugin = makelist(plugin)

            args = _get(plugin, 1) or []
            kwargs = _get(plugin, 2) or {}

            plugin = plugin[0]

            if isinstance(plugin, str):
                plugin = load(plugin)
            plugin = plugin(*args, **kwargs)
            
            self.trigger_hook("before_plugin_setup", plugin)
            if hasattr(plugin, 'setup'): plugin.setup(self)
            self.trigger_hook("plugin_setup", plugin)

            if callable(plugin) or hasattr(plugin, 'apply'):
                self.plugins.append(plugin)
                self.reset()

        if not self.config.get("use.endslash", False):
            self.add_hook("before_request", self._strip)

        b_hooks = self.config.get("hooks.before_request")
        if b_hooks:
            for hook in makelist(b_hooks):
                if type(hook) == str:
                    hook = load(hook)
                if callable(hook):
                    self.add_hook("before_request", hook)

        a_hooks = self.config.get("hooks.after_request")
        if a_hooks:
            for hook in makelist(a_hooks):
                if type(hook) == str:
                    hook = load(hook)
                if callable(hook):
                    self.add_hook("after_request", hook)


    def _strip(self):
        if request.method == request.methods.GET:
            request.environ["PATH_INFO"] = request.environ["PATH_INFO"].rstrip("/")

    def _debug(self, text):
        if self.config.get("debug", True):print("[DEBUG]", text)
    
    def run(self, app=None, **kwargs):
        self.setup()
        app = app or self.wrapped_app("wsgi")
        run(app, **kwargs)

    def __setattr__(self, name, value):
        self.__dict__[name] = value
