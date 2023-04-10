from functools import partial
from wsgic.helpers import config
from wsgic.thirdparty.bottle import TemplateError, BaseTemplate, MakoTemplate, TemplatePlugin, Jinja2Template, SimpleTemplate, CheetahTemplate, template, jinja2_template, mako_template, cheetah_template, load, view, jinja2_view, mako_view, cheetah_view


class MustacheTemplate(BaseTemplate):
	def prepare(self, **options):
		Renderer = config.get("static.template.config.renderer", "pystache:Renderer")
		if isinstance(Renderer, str):
			Renderer = load(Renderer)
		self.renderer = Renderer(**options)
		if self.source:
			self.tpl = partial(self.renderer._render_string, self.source)
		else:
			self.tpl = partial(self.renderer.render_path, self.name)

	def render(self, *args, **kwargs):
		for dictarg in args:
			kwargs.update(dictarg)
		_defaults = self.defaults.copy()
		_defaults.update(kwargs)
		return self.tpl(**_defaults)

mustache_template = partial(template, template_adapter=MustacheTemplate)
mustache_view = partial(view, template_adapter=MustacheTemplate)
