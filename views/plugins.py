import inspect
from wsgic.plugins import BasePlugin
from . import render

class ViewPlugin(BasePlugin):
    keyword = "view"
    def apply(self, callback, route):
        view = route.get(self.keyword, None)
        if not self.keyword:
            return callback

        def wrapper(*args, **kwargs):
            return render(view, callback(*args, **kwargs))
        return wrapper