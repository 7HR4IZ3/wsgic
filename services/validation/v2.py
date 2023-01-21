from wsgic.http import request
import re
from lark import Lark, Transformer

def parse(code, context={}):
    exec("""
def prse(*a, **kw):
    return {'args': a, 'kwargs': kw}
___ = prse(%s)"""%code, context)
    return context.pop("___", {"args": [], "kwargs": {}})

class BaseFilters:
    def __init__(self, data):
        self.data = data
    
    def true(self, data):
        return True
    
    def false(self, data):
        return False
    
    def required(self, data):
        if data is not None:
            return data
        return False
    
    def match(self, column, data):
        return data == self.data[column]

    def max_length(self, max, data):
        return len(data) <= max

    def min_length(self, min, data):
        return len(data) >= min

    def max_value(self, max, data):
        return data <= max

    def min_value(self, min, data):
        return data >= min
    
    def in_choices(self, *val, data=None):
        return data in val
    
    def requires(self, value, data):
        return value in data
    
    def isinstance(self, val, data):
        return isinstance(data, val)
    
    def custom(self, func, data):
        assert callable(func), "Function must be callable"
        return func(data)
    
    def equals(self, val, data):
        if not callable(val):
            val = lambda: val
        return data == val()
    
    def re_match(self, regex, data=None, **config):
        return re.match(regex, data, **config)

    def re_search(self, regex, data=None, **config):
        return re.search(regex, data, **config)
    
    def unique(self, age=None, data=None):
        return False

filters = BaseFilters({})

grammer = """
start: rule ("|" rule ["|"]?)*

torf: rule "??" rule
ifcond: rule "?" rule (":" rule)?

rule: [[singlerule | "(" singlerule ")"] | [torf|"(" torf ")"] | [ifcond | "(" ifcond ")"]]

singlerule: [simplerule | inverserule]

simplerule: NAME ("(" arguments ")")?
inverserule: "!" rule

arguments: argvalue ("," argvalue)*  ("," [ starargs | kwargs])?
         | starargs
         | kwargs
         | comprehension{test}

starargs: stararg ("," stararg)* ("," argvalue)* ["," kwargs]
stararg: "*" test
kwargs: "**" test ("," argvalue)*

?argvalue: test ("=" test)?

%import common (WS)
%import python (NAME, test, comprehension)
%ignore WS
"""

class ValidationTransformer(Transformer):
    singlerule = rule = lambda s, x: x[0]
    NAME = lambda s, x: str(x)
    
    def set_data(self, data):
        self.__data = data
    
    def set_key(self, key):
        self.__key = key
    
    def set_filters(self, filters):
        self.__filters = filters
    
    def set_context(self, context):
        self.__context = context
    
    def start(self, args):
        ret = False
        for item in args:
            ret = bool(item) or False
        return ret
    
    def simplerule(self, args):
        data = self.__data.get(self.__key)
        if len(args) > 1:
            d = parse(args[1], context=self.__context)
            try:
                ret = getattr(self.__filters, args[0])(*d["args"], data=data, **d["kwargs"])
            except:
                return False
        else:
            try:
                ret = getattr(self.__filters, args[0])(data=data)
            except:
                return False
        return ret
    
    def inverserule(self, args):
        return not args[0]
    
    def torf(self, args):
        return args[0] or args[1]
    
    def ifcond(self, args):
        if args[0]:
            return args[1]
        else:
            if len(args) == 3:
                return args[2]
    
    def arguments(self, args):
        return ", ".join(str(x) for x in args)
    
    def argvalue(self, args):
        if len(args) > 1:
            return "=".join(args)
        return args[0]
    
    def starargs(self, args):
        return "*" + args[0]
    
    def kwargs(self, args):
        return "**" + args[0]
    
    def __default__(self, data, children, meta):
        if len(children) == 1:
            return children[0]
        return children

    def __default_token__(self, token):
        """Default function that is called if there is no attribute matching ``token.type``

        Can be overridden. Defaults to returning the token as-is.
        """
        return token.value


# parser = Lark(grammer)
# t = ValidationTransformer()

# tree = parser.parse("required|unique")
# print(t.transform(tree))
# print()

# tree = parser.parse("required|unique|in_choices([1,2,3])")
# print(t.transform(tree))
# print()

# tree = parser.parse("isinstance(int) ? (unique ?? !min_value(98)) : min_value(80000)")
# print(t.transform(tree))
# print()

# tree = parser.parse("required|unique ?? min_value(7)")
# print(t.transform(tree))
# print()


class Validator:
    def __init__(self, rules=None, context=None, filterclass=BaseFilters):
        self.raw = rules
        self.parser = Lark(grammer)
        self.transformer = ValidationTransformer()

        if rules:
            self.rules = self.format(rules)
        else:
            self.rules = None
        self.filters = filterclass
        self.__errors = {}
        self.context = context or {}
    
    def set_rules(self, rules):
        self.raw = rules
        self.rules = self.format(rules)
        return self

    def set_filters(self, filters):
        self.filters = filters
        return self

    def set_context(self, context):
        self.context = context
        return self

    def to_set(self, value):
        if isinstance(value, str):
            return set(value.split("|"))
        return set(value)
    
    def reset(self):
        self.__errors = {}
        self.rules = None
        self.raw = None
        self.context = {}
        self.filters = BaseFilters
        return self
    
    def format(self, rules):
        for item in rules:
            value = rules[item]
            assert isinstance(value, (str, dict, list, tuple, set))
            if isinstance(value, (str, list, tuple, set)):
                rules[item] = {
                    "rules": self.to_set(value)
                }
            elif isinstance(value, dict):
                if "rules" in value:
                    rules[item]["rules"] = self.to_set(rules[item].get("rules", []))
                else:
                    rules[item]["rules"] = set(value.keys())
                    rules[item]["errors"] = {x.split("(")[0]: value[x]  for x in value}
        return rules

    def validate(self, data=None, context=None):
        self.__errors = {}
        data = data or request.POST
        assert self.rules, "No rules defined"
        context = dict(**self.context, **(context or {}))
        
        filterclass = self.filters(data)
        self.transformer.set_data(data)
        self.transformer.set_filters(filterclass)
        self.transformer.set_context(context)
        
        for item in set([*list(self.rules.keys()), *list(data.keys())]):
            value = data.get(item)
            rules = self.rules.get(item)
            
            if rules:
                self.transformer.set_key(item)
                ret = False

                for rule in rules["rules"]:
                    nret = self.transformer.transform(
                        self.parser.parse(rule)
                    )
                    if not nret:
                        ret = False
                        rule = rule.split("(")[0].strip()
                        error = str(rules.get("errors", {}).get(rule, "{field}: '{value}' is invalid.")).format(field=item, value=value)

                        if item in self.__errors:
                            self.__errors[item][rule] = error
                        else:
                            self.__errors[item] = {
                                rule: error
                            }
        return self
    
    def is_valid(self, field=None):
        if field:
            return field in self.__errors
        return self.__errors == {}
    
    def get_error(self, field):
        return self.__errors.get(field, {})

    def has_error(self, field):
        return field in self.__errors
    
    def errors(self):
        return self.__errors
    
    def errors_dict(self):
        errs = self.__errors
        return {
            x: [errs[x][y] for y in errs[x]] for x in errs
        }
    
    def errors_list(self):
        errors = []
        for error in self.errors_dict().values():
            for item in error:
                errors.append(item)
        return errors


# rules = {
#     "username": "required|requires('a')",
#     "password": {
#         "rules": "required",
#         "errors": {
#             "required": "Oops, No password specified."
#         }
#     },
#     "password2": {
#         "rules": "required|match('password')",
#         "errors": {
#             "match": "Password2 must match password"
#         }
#     },
#     "data": {
#         "rules": "isinstance(int) ? (min_value(1) ?? custom(func)) : (equals('admin') ?? max_length(8))"
#     }
# }

# v = Validator(rules, {
#     "func": lambda x: x == 0
# })

# v.validate({
#     "username": "Thraize",
#     "password": "Avengers",
#     "password2": "Avengers22",
#     "data": 3
# })

# print(v.is_valid(), v.errors_list())

