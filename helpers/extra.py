import sys
from wsgic.backend import ConfigDict

ext = ConfigDict()

def set_global(name, value):
	# print("Set:", name, " As:", value)
	ext[name.upper()] = value
	return True

def get_global(name):
	# print("Get:", name)
	return ext[name.upper()]


def load_module(target, **namespace):
	module, target = target.split(":", 1) if ':' in target else (target, None)
	if module not in sys.modules: __import__(module)
	if not target: return sys.modules[module]
	if target.isalnum(): return getattr(sys.modules[module], target)
	package_name = module.split('.')[0]
	namespace[package_name] = sys.modules[package_name]
	return eval('%s.%s' % (module, target), namespace)


def _get(data, index=0, e=None):
	try:return data[index] if type(data) in (list, dict, set, tuple) else data
	except:return e

class switch:
	def __init__(self, match, _return=False, args=[], kwargs={}):
		self.match, self._return, self.cases = match, _return, {}
		self.args, self.kwargs = args, kwargs
		self.cases = {}

	def default(self, func, args=[], kwargs={}):
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

	def case(self, case, call, args=[], kwargs={}):
		self.cases[f"{case}"] = {
			"func": call,
			"args": self.args+args,
			"kwargs": dict(**self.kwargs, **kwargs)
		}
		return self