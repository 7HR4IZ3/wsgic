from functools import wraps
from wsgic.helpers import config
from wsgic.helpers.extra import _get
from wsgic.helpers.require import load

class Services:
	def __init__(self):
		self.__data = {}
		self.__cache = {}

	def __call__(self, name, new=False, *a, **kw):
		service = self.__data.get(name)
		new = new or (name not in self.__cache)
		can_cache = getattr(service, "__services_cacheable__", False)
		if callable(can_cache):
			can_cache = can_cache({"args": a, "kwargs": kw})
		if new is True:
			if service:
				ret = service(*a, **kw)
				if can_cache:
					self.__cache[name] = ret
				return ret
		else:
			service = self.__cache.get(
				name, self.__data.get(name)
			)
			if service:
				return service
		raise ValueError("Service named '%s' not defined"%name)

	
	def register(self, name, service=None, override=False, cache=False):
		def wrapper(service):
			if self.__data.get(name):
				if override is False:
					raise ValueError("Service named '%s' already defined"%name)
			service.__services_cacheable__ = cache
			self.__data[name] = service
			return service
		return wrapper(service) if service else wrapper

service = Services()

def register(name, service=None, override=False, cache=False):
	def wrapper(func):
		global service
		service.register(name, func, override=override, cache=cache)
		return func
	return wrapper(service) if service else wrapper

def __():
	from .validation import Validator
	from .cache import SimpleCache, SafeCache, SimpleDiskCache, DiskCache, JsonDiskCache
	from wsgic.utils.i18n import LanguagesDict

	for service in config.get("services", []):
		try:
			load(str(service).rstrip(".services")+".services")
		except:
			load(str(service))

	register("validation", Validator)
	register("cache", SimpleCache, cache=True)
	register("language", LanguagesDict, cache=True)
	register("cache.simple", SimpleCache)
	register("cache.safe", SafeCache)
	register("cache.disk", SimpleDiskCache)
	register("cache.disk.pickle", DiskCache)
	register("cache.disk.json", JsonDiskCache)

__()