import os
from random import randint, random
from urllib.parse import urljoin
from .extra import get_global
from wsgic.backend.bottle import ConfigDict, load


class finder:
	def __init__(self, app=None):
		self.appRouter = get_global("router")
	
	def __call__(self, name, e=None):
		r = self.appRouter
		try:
			return str(
				r.find_route(name)
			)
		except:return e

# def url_to(name):
# 	r = get_global("router")
# 	return str(
# 		r.find_route(value=name)
# 	)

class Configurator(ConfigDict):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.raw = self
	
	def __call__(self, *args, **kwds):
		return super().__init__(*args, **kwds)

	def _slicer(self, module, begin, end):
		final = ""
		with open(module.__file__, "r") as code:
			adding = False
			if type(begin) is int and type(end) is int:
				if end == -1:
					final = code.read()[begin:]
				else:final = code.read()[begin:end]
			if type(begin) is str and type(end) is str:
				for line in code:
					if begin in line:adding = True
					elif adding is True:final = final + f"\n{line}"
					elif end in line:adding = False
		return final

	def use(self, module, begin=0, end=-1):
		file = f"tmpconfig-{randint(0, 9)}.py"
		with open(file, "w") as config:
			config.write(self._slicer(module, begin, end))
		self.load_module(file.replace(".py", ""))
		self.raw.load_module(file.replace(".py", ""), False)
		os.remove(file)
		return
	
	def get(self, config=None, e=None, raw=False):
		conf = self if not raw else self.raw
		if not config:return conf
		config = config.upper()
		try:return conf[config]
		except:return e

	def set(self, config, value):
		if config.upper() not in self:
			self[config.upper()] = value
		else:return False

config = Configurator()

def find(word, keys):
	ret = {}
	def search(line, key):
		x = []
		for i, w in enumerate(line):
			if key in w:
				x.append(i+1)
		return x

	for key in keys:
		ret[key] = search(word, key)
	return ret
