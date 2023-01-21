from functools import partial, wraps
from datetime import date, datetime
from copy import copy
import json

py_to_sql = {
    float: "real",
    int: "integer",
    str: "text",
    bytes: "blob",
    date: "date",
    datetime: "timestamp"
}

sql_to_py = {py_to_sql[x]: x for x in py_to_sql}
sql_to_py['date'] = date.fromisoformat
sql_to_py['timestamp'] = datetime.fromisoformat

def makelist(data):  # This is just too handy
    if isinstance(data, (tuple, list, set, dict)):
        return list(data)
    elif data:
        return [data]
    else:
        return []

def _get(data, index=0, e=None):
    try:return data[index] if type(data) in (list, dict, set, tuple) else data
    except:return e

def sql_to_form(type):
    if type == "integer":
        return "number"
    elif type == "blob":
        return "file"
    elif type == "timestamp":
        return "datetime-local"
    return type

class BaseObjects:
    
    def bind(self, model, db):
        self.model = model
        # self.table_name = table_name
        self.db = db

    def __getattr__(self, name):
        if name in self.db._model_methods:
            func = partial(getattr(self.db, name), self.model.__table_name__())

            def wrapper(*a, **kw):
                self.model.trigger("before_"+name, {"args": a, "kwargs": kw})
                data = func(*a, **kw)
                if data is not None:
                    self.model.trigger(name, data)
                else:
                    self.model.trigger(name)
                return data
            
            return wrapper
    
    def all(self):
        return self.get()
    
    def get_one(self, *args, **kwargs):
        data = self.get(*args, **kwargs)
        if data:
            return data[0]
        return None

class BaseValidator:
    def setup(self, column):
        pass
    
    def apply(self, data):
        return data

class BaseFormatter:
    def setup(self, column):
        pass
    
    def apply(self, data):
        return data

class Hooks:
    def __init_subclass__(self, **kw):
        super().__init_subclass__(**kw)
        self._hooks = {}
    
    @classmethod
    def on(self, event, func=None, override=False):
        def wrap(func):
            funcs = makelist(func or [])
            if event not in self._hooks:
                self._hooks[event] = funcs
            else:
                self._hooks[event] += funcs
        return wrap(func) if func else wrap
    
    @classmethod
    @property
    def hooks(self):
        return self._hooks
    
    @classmethod
    def trigger(self, event, *args, **kwargs):
        if event in self._hooks:
            for func in self._hooks[event]:
                if callable(func):
                    func(*args, **kwargs)
    
    @classmethod
    def remove(self, event):
        if event in self._hooks:
            self._hooks.pop(event)
    
    @classmethod
    def detach(self, event, func):
        if event in self._hooks and func in self._hooks[event]:
            self._hooks[event].remove(func)


class List(list):
    def __or__(self, other):
        return List(set([*self, *other]))
    
    def __and__(self, other):
        if self == other:
            return self
        alll = List()
        if self:
            for x in self:
                if other and x in other:
                    alll.append(x)
        elif other:
            alll = other
        return alll
    
    def orderby(self, key):
        return sorted(self, key=lambda x: x[key])
    
    def first(self):
        return self[0]
    
    def last(self):
        return self[-1]
    
    def asdict(self):
        return List([x.asdict() for x in self])
    
    def serialize(self):
        return List([x.serialize() for x in self])
    
    def filter(self, fn):
        return List(filter(fn, self))
    
    def json(self):
        return json.dumps(self)

    # def filter(self, **kwargs):
    #     ret = []
    #     for x in self:
    #         add = False
    #         for kw in kwargs:
    #             if getattr(x, kw) != kwargs[kw]:
    #                 add = False
    #                 break
    #             else:
    #                 add = True
    #         if add:
    #             ret.append(x)
    #     return ret


# class Column:
#     type = "text"
#     default = False
#     null = None
#     html_type = None
#     html_attrs = None
#     no_label = False
#     validators = None
#     formatters = None
    
#     def __init__(self, type=None, null=True, default=None, primary_key=None, unique=False, repr=True, name=None, max_length=None, label=None, html_type=None, html_attrs=None, helper_text=None, validators=None, formatters=None):
#         self.type = type or self.type
#         if not isinstance(self.type, str):
#             self.type = py_to_sql.get(self.type)
#         self.__error = []
#         self.null = self.null or null
#         self.default = default or self.default

#         self.unique = unique
#         self.pk = primary_key
#         self.repr = repr
#         self.name = name
#         self.max_length = max_length
#         self.helper_texts = makelist(helper_text)
#         self.validators = (validators or []) + (self.validators or [])
#         self.formatters = (formatters or []) + (self.formatters or [])

#         self.h = formify.HTML() if formify else None
#         self.html_attrs = html_attrs or self.html_attrs or {}
#         self.__html_type = html_type or self.html_type or "text"
#         self.__label = label
        
#         self._table = None
    
#     # def __setattr__(self, name, value):
#     #     if hasattr(self, name):
#     #         print(f"Overiding attribute {name} of {self.__class__.__name__}")
#     #     return super().__setattr__(name, value)

#     def errors(self):
#         data = copy(self.__error)
#         self.__error = []
#         return data
    
#     def add_error(self, message):
#         self.__error.append(message)
    
#     def has_error(self):
#         return self.__error != []
    
#     def get_label(self):
#         return (self.__label or self.name)
    
#     def get_html_type(self):
#         return sql_to_form(self.__html_type or self.type)
    
#     def get_attrs(self):
#         return self.html_attrs
    
#     def get_validation_rules(self, rules):
#         if self.max_length:
#             rules.append(f"max_length({self.max_length})")
#         return rules
    
#     def get_validation_context(self, context):
#         return context
    
#     def bind(self, model, name):
#         # setattr(model, name, self)
#         setattr(self, "_table", model)
    
#     def validate(self, val):
#         if self.max_length:
#             try:
#                 length = len(val)
#             except:
#                 length = None
#             if length:
#                 if length > self.max_length:
#                     raise ValueError("%s.%s value exceeds max length"%(self._table.__name__, self.name))
#         return val
#         # except:
#         #     return None
    
#     def format(self, val):
#         try:
#             return sql_to_py.get(self.type)(val)
#         except:
#             return None
    
#     def save(self, data):
#         data = self.validate(data)
#         for validator in self.validators:
#             try:
#                 data = validator.apply(data)
#             except Exception as e:
#                 for error in e.args:
#                     self.add_error(error)
#         return data
    
#     def formatted(self, data):
#         data = self.format(data)
#         for formatter in self.formatters:
#             data = formatter.apply(data)
#         return data
    
#     def setup(self, db, model):
#         [x.setup(self) for x in self.validators]
#         [x.setup(self) for x in self.formatters]
    
#     def form(self, **attrs):
#         if self.max_length:
#             attrs['maxlength'] = self.max_length
#         return self.h.input(type=self.get_html_type(), **attrs)
    
#     def to_str(self, attrs):
#         ret = "".join(f"{x}={attrs[x]} " if attrs[x] != True else f"{x}" for x in attrs).strip()
#         return ret
    
#     def _dtype(self):
#         null = ' NOT NULL' if not self.null else ''

#         if self.default:
#             self.default = self.save(self.default)
#         default = (f' DEFAULT "{self.default}"' if isinstance(self.default, str) else f' DEFAULT {self.default}') if self.default else ''
#         unique = " UNIQUE" if (self.unique or self.pk) else ""
#         type = f'{self.type} primary key' if self.pk else self.type
        
#         return f'{type}{null}{default}{unique}'
    
#     def _query(self):
#         q = f'"{self.name}" {self._dtype()}'
#         return q
    
#     def __eq__(self, other):
#         data = self._table.objects.get(**{self.name: other})
#         return List(data)

#     def contains(self, word):
#         ret = List()
#         for x in self._table.objects.get():
#             if word in x[self.name]:
#                 ret.append(x)
#         return ret
    
#     def match(self, value: str):
#         ret = List()
#         for x in self._table.objects.get():
#             if re.search(value, x[self.name]):
#                 ret.append(x)
#         return ret
    
#     def like(self, word):
#         data = self._table.objects.like(self._name, word)
#         return List(data)

#     def __lt__(self, value):
#         ret = List()
#         for x in self._table.objects.get():
#             if x[self.name] < value:
#                 ret.append(x)
#         return ret

#     def __gt__(self, value):
#         ret = List()
#         for x in self._table.objects.get():
#             if x[self.name] > value:
#                 ret.append(x)
#         return ret

#     def __le__(self, value):
#         return List(
#             [*self.__lt__(value), *self.__eq__(value)]
#         )

#     def __ge__(self, value):
#         return List(
#             [*self.__gt__(value), *self.__eq__(value)]
#         )
