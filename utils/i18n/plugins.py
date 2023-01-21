from wsgic.plugins import BasePlugin, RequestPlugin
from wsgic.http import request
from functools import wraps
from . import languages

class I18nPlugin(RequestPlugin, BasePlugin):
	name = "i18n"

	def __init__(self, keyword="locale", default_locale=None, supported_locales=None, force_locale=False):
		self.keyword = keyword
		self.locale = default_locale
		self.supported = supported_locales
		self.force_locale = force_locale

	def setup(self, app):
		super().setup(app)
		self.supported = self.supported or app.config.get("locale.supported", ["en"])
		self.locale = self.locale or app.config.get("locale.default", "en")
		self.force_locale = self.force_locale or app.config.get("locale.force_locale", False)
	
	def before(self):
		locale = request.environ["PATH_INFO"].strip("/").split("/")[0]
		if languages.has_language(locale):
			request.locale = locale
	
	def apply(self, callback, route):

		def wrapper(*a, **kw):
			locale = route.config.get("locale_keyword", kw.pop(self.keyword, None))
			request.locale = locale

			def main(locale):
				if locale in self.supported:
					if languages.has_language(locale):
						with languages.lang(locale):
							data = callback(*a, **kw)
						return data
				raise ValueError("Unsupported Locale '%s'"%locale)

			if locale:
				return main(locale)
			else:
				if self.force_locale:
					return main(self.locale)
				return callback(*a, **kw)

		if route.config.get("skip_locale") is True:
			return callback

		return wrapper
