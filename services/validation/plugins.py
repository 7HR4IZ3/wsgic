from wsgic.plugins import RequestPlugin
from wsgic.http import request
from . import Validator

class ValidationPlugin(RequestPlugin):
    v = Validator()
    
    def is_valid(self, rules, data=None, filter_class=None, context=None):
        v = self.v.set_rules(rules)
        if filter_class:
            v.set_filters(filter_class)
        if context:
            v.set_context(context)
        return v.validate(data).is_valid()
    
    def before(self):
        if not request.validation:
            request.validation = self.v.reset()
            request.is_valid = self.is_valid
