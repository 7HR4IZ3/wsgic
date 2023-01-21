import inspect
from wsgic.thirdparty.bottle import PluginError, request, response
from wsgic.helpers import config, hooks

class InspectMixin:
	def get_kwargs(self, callback):
		a = inspect.getfullargspec(callback)
		data = zip(a.args[::-1][:len(a.defaults)], a.defaults[::-1])
		kwargs = {x[0]: x[1] for x in data[::-1]}
		return kwargs

	def get_args(self, callback):
		a = inspect.getfullargspec(callback)
		return a.args

class BasePlugin(InspectMixin):
	name = None
	api = 2

	def __init__(self, name=None, api=None):
		self.name = name or self.name or self.__class__.__name__.replace("Plugin", "").lower()
		self.api = api or self.api

	def setup(self, app):
		pass

	def apply(self, callback, route):
		return callback

class HookPlugin(InspectMixin):
	name = None
	api = 2

	def __init__(self, name=None, api=None, hooks=None):
		self.name = name or self.name or self.__class__.__name__.replace("Plugin", "")
		self.api = api or self.api
		self.hooks = hooks

	def setup(self, app):
		if not self.hooks:
			self.hooks = {x: x for x in app._hooks._}
		if isinstance(self.hooks, (list, set, tuple)):
			hoks = {x: x for x in self.hooks}
			self.hooks = hoks

		for x in self.hooks:
			if hasattr(self, self.hooks[x]):
				hooks.attach(x, getattr(self, self.hooks[x]))

class KeywordPlugin(InspectMixin):
	name = None
	api = 2

	def __init__(self, keyword=None, object=None, name=None, api=None):
		self.name = name or self.name or self.__class__.__name__.replace("Plugin", "")
		self.api = api or self.api
		self.keyword = keyword
		self.object = object

	def setup(self, app):
		for other in app.plugins:
			if not isinstance(other, BasePlugin):
				continue
			if other.keyword == self.keyword:
				raise PluginError("Found another plugin with similiar keyword. You probably installed the plugin twice.")

	def apply(self, callback, route):
		a = inspect.getfullargspec(route.callback)
		if self.keyword not in a.args:
			return callback

		def wrapper(*args, **kwargs):
			kwargs[self.keyword] = self.object
			return callback(*args, **kwargs)
		return wrapper

class RequestPlugin(HookPlugin):
	def __init__(self, name=None, api=None):
		super().__init__(name=name, api=api, hooks={"before_request": "before", "after_request": "after"})

class ContextPlugin(HookPlugin):
	def __init__(self, name=None, api=None):
		super().__init__(name=name, api=api, hooks={"before_render": "render"})
