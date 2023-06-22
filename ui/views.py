from wsgic.views import BaseView
# from .builder import HTML, BaseContext

class UiView(BaseView):
    def __init__(self):
        super().__init__()
        # BaseContext.__init__(self)

        # self.html = HTML(context=self)

    def setup_routes(self, routes, config):
        conf = config.pop("config")
        config["callback"] = self.decorate(self.__renderer)
        config["path"] = config.pop("rule")
        routes.web_route(**config, **conf)
    
    def render(self, *a, **kw):
        return ""

    def __renderer(self, response, *a, **kw):
        response.send(self.render(*a, **kw))
        if hasattr(self, "onrender"):
            self.onrender(response.browser)

class UIView(BaseView):
    def __call__(self, response, *args, **kwargs):
        response.send(self.render(*args, **kwargs))
        if hasattr(self, "onrender"):
            self.browser = response.browser
            self.onrender()

    def render(self, *a, **kw):
        return ""
