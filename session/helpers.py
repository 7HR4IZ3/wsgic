# from wsgic.database.json import JsonDatabase

'''ModificationTrackingDict and support classes from werkzeug'''

def _calls_update(name):
	def oncall(self, *args, **kw):
		rv = getattr(super(ModificationTrackingDict, self), name)(*args, **kw)

		if self.on_update is not None:
			self.on_update()

		return rv

	oncall.__name__ = name
	return oncall


class ModificationTrackingDict(dict):
	__slots__ = ("modified",)

	def __init__(self, *args, **kwargs):
		self.modified = False
		dict.update(self, *args, **kwargs)

	def on_update(self):
		self.modified = True

	def copy(self):
		"""Create a flat copy of the dict."""
		missing = object()
		result = self.__class__.__new__(self)
		for name in self.__slots__:
			val = getattr(self, name, missing)
			if val is not missing:
				setattr(result, name, val)
		return result

	def setdefault(self, key, default=None):
		modified = key not in self
		rv = super().setdefault(key, default)
		if modified and self.on_update is not None:
			self.on_update(self)
		return rv

	def pop(self, key, default=None):
		modified = key in self
		if default is None:
			rv = super().pop(key)
		else:
			rv = super().pop(key, default)
		if modified and self.on_update is not None:
			self.on_update()
		return rv

	__setitem__ = _calls_update("__setitem__")
	__delitem__ = _calls_update("__delitem__")
	clear = _calls_update("clear")
	popitem = _calls_update("popitem")
	update = _calls_update("update")

	def __copy__(self):
		return self.copy()

	def __repr__(self):
		return f"<{type(self).__name__} {dict.__repr__(self)}>"
