import types
from contextlib import contextmanager
from wsgic.services import service
from wsgic.helpers import ConfigDict, config

class LanguagesDict(ConfigDict):
	__lang = None

	def add_language(self, language, data):
		if isinstance(data, dict):	
			self.load_dict(data, namespace=language)
		elif isinstance(data, types.ModuleType):
			self[language] = ConfigDict({}).load_module(data)
		elif isinstance(data, str):
			self[language] = ConfigDict({}).load_config(data)
	
	def has_language(self, language):
		for item in self.keys():
			if str(item).startswith(language):
				return True
		return False

	def remove_language(self, language):
		for item in self.keys():
			if str(item).startswith(language):
				self.pop(item)
		return True

	@contextmanager
	def lang(self, lang):
		try:
			self.__lang = lang
			yield self.__lang
		finally:
			self.__lang = None
	
	def __call__(self, text, *args, lang=None, default=None, **kwargs):
		lang = str(lang or self.__lang or config.get('lang_code', "en"))
		return str(self.get(f"{lang}.{text}", default or text)).format(*args, **kwargs)
