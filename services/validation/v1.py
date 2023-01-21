from wsgic.http import request
import re


def parse(code, context={}):
    exec("""
def prse(*a, **kw):
    return {'args': a, 'kwargs': kw}
___ = prse(%s)"""%code, context)
    return context.pop("___", {"args": [], "kwargs": {}})


class BaseFilters:
    def __init__(self, data):
        self.data = data
    
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
        return data <= min
    
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

class Validator:
    def __init__(self, rules=None, context=None, filterclass=BaseFilters):
        self.raw = rules

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
    
    def parse_rule(self, rule, context={}):
        rule_args = rule.split("(")

        if len(rule_args) > 1:
            rule, *args = rule_args
            args = "(".join(args)
            assert args[-1] == ")"
            args = parse(f"{args[:-1]}", context)
        else:
            rule, args = rule_args[0], {"args": [], "kwargs": {}}
        return rule, args
    
    def validate_rule(self, rule, item, value, filterclass, rules, context={}):
        if rule.startswith("!"):
            rule = rule[1:]
            inverse = lambda x: not x
        else:
            inverse = lambda x: x

        rule, args = self.parse_rule(rule, context)

        error = str(rules.get("errors", {}).get(rule, "{field}: '{value}' is invalid.")).format(field=item, value=value, args=args)

        try:
            rulefunc = getattr(filterclass, rule)
        except AttributeError:
            try:
                rulefunc = context[rule]
            except LookupError:
                raise ValueError("No filter named %s"%rule)
        
        assert callable(rulefunc), "Rule '%s' filter function must be callable"%rule

        ret = inverse(rulefunc(*args["args"], **args["kwargs"], data=value))
        return rule, ret, error

    def validate(self, data=None, context=None):
        self.__errors = {}
        data = data or request.POST
        assert self.rules, "No rules defined"
        context = dict(**self.context, **(context or {}))
        for item in set([*list(self.rules.keys()), *list(data.keys())]):
            value = data.get(item)
            rules = self.rules.get(item)
            
            if rules:
                filterclass = self.filters(data)
                for rule in rules["rules"]:
                    error_key = rule
                    if ":" in rule and "?" in rule:
                        ret = False
                        splits = rule.split(":")
                        condition, remains = splits[0], ":".join(splits[1:])
                        if_true, if_false = remains.split("?")
                        if_true, if_false = if_true.strip(), if_false.strip()

                        assert if_true not in (None, "")
                        assert if_false not in (None, "")

                        rule, condret, error = self.validate_rule(condition.strip(), item, value, filterclass, rules, context)
                        if condret:
                            rule, ret, error = self.validate_rule(if_true, item, value, filterclass, rules, context)
                            if not ret:
                                error_key = if_true
                        else:
                            rule, ret, error = self.validate_rule(if_false, item, value, filterclass, rules, context)
                            if not ret:
                                error_key = if_false

                    elif "??" in rule:
                        ret = False
                        for ruleitem in rule.split("??"):
                            rule, val, error = self.validate_rule(ruleitem.strip(), item, value, filterclass, rules, context)
                            if val:
                                ret = True
                                break
                            else:
                                error_key = ruleitem

                    else:
                        rule, ret, error = self.validate_rule(rule, item, value, filterclass, rules, context)

                    if not ret:
                        if item in self.__errors:
                            self.__errors[item][error_key] = error
                        else:
                            self.__errors[item] = {
                                error_key: error
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
#     "username": "required",
#     "password": {
#         "rules": "required",
#         "errors": {
#             "required": "Oops, No password specified."
#         }
#     },
#     "password2": {
#         "rules": "required",
#         "errors": {
#             "match": "Password2 must match password"
#         }
#     },
#     "data": {
#         "rules": "isinstance(int)"
#     }
# }

# v = Validator(rules, {})

# v.validate({
#     "username": "Thraize",
#     "password": "Avengers",
#     "password2": "Avengers",
#     "data": 2
# })
# print(v.is_valid(), v.errors())

