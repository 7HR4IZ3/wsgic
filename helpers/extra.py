import sys
from wsgic.thirdparty.bottle import ConfigDict

class Globalizer:
	def __init__(self):
		self.storage = ConfigDict()
		
	def validate(self):
		return True
	
	def get(self, name, e=None):
		if self.validate():
			return self.storage.get(name.upper(), e)
	
	def set(self, name, value):
		if self.validate():
			self.storage[name.upper()] = value
			return value

ext = Globalizer()

def set_global(name, value, override=True):
	if not override and ext.get(name, None):
		return False
	ext.set(name, value)
	return True

def get_global(name, e=None):return ext.get(name, e)

def load_module(target, e=None, catch_errors=True, **namespace):
	try:
		module, target = target.split(":", 1) if ':' in target else (target, None)
		if module not in sys.modules: __import__(module)
		if not target: return sys.modules[module]
		if target.isalnum(): return getattr(sys.modules[module], target)
		package_name = module.split('.')[0]
		namespace[package_name] = sys.modules[package_name]
		return eval('%s.%s' % (module, target), namespace)
	except Exception as err:
		if catch_errors:
			return e
		raise err

def _get(data, index=0, e=None):
	try:return data[index] if type(data) in (list, dict, set, tuple) else data
	except:return e

class switch:
	def __init__(self, match, _return=False, args=None, kwargs=None, decorators=None):
		self.match, self._return, self.cases = match, _return, {}
		self.args, self.kwargs = args or [], kwargs or {}
		self.decs = decorators or []
		self.cases = {}

	def default(self, func, args=None, kwargs=None):
		kwargs = kwargs or {}
		args = args or []
		self.cases["default"] = {
			"func": func,
			"args": self.args+args,
			"kwargs": dict(**self.kwargs, **kwargs)
		}
		return self.make()

	def make(self):
		matched = False
		for case in self.cases:
			if self.match == case:
				matched = True
				if self._return:return self.cases[case]['func'](*self.cases[case]['args'], **self.cases[case]['kwargs'])
				else:self.cases[case]['func'](*self.cases[case]['args'], **self.cases[case]['kwargs'])
				break
		
		if not matched:
			if self._return:return self.cases["default"]['func'](*self.cases[case]['args'], **self.cases[case]['kwargs'])
			else:self.cases["default"]['func'](*self.cases[case]['args'], **self.cases[case]['kwargs'])

	def case(self, case, call, args=None, kwargs=None):
		kwargs = kwargs or {}
		args = args or []
		self.cases[f"{case}"] = {
			"func": call,
			"args": self.args+args,
			"kwargs": dict(**self.kwargs, **kwargs)
		}
		return self