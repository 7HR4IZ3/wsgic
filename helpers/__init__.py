__all__ = ["Config", "config", "hooks", "is_main_app", "db"]

import os
from random import randint
from contextlib import contextmanager
from wsgic.thirdparty.bottle import ConfigDict, makelist, load

from .extra import get_global

_ = False
db = hooks = ordered = config = None

def compile_route(_route, **data):
	
    def main(seg):
        for x in list(data.keys()):
            if x in seg:
                if type(data[x]) is list and data[x] != []:
                    val = data[x].pop(0)
                    if data[x] == []:
                        data.pop(x)
                else:
                    val = data.pop(x)
                seg = seg.replace(x, str(val)).replace("<", '')
                if ":" in seg:
                    e = seg.find(">")
                    p = seg.find(":")
                    if e != -1:
                        seg = seg.replace(seg[p:e], "")
                seg = seg.replace(">", "")
        if "<" in seg and ">" in seg:
            raise Exception("No placeholder for: '%s' "%seg)
        return seg

    path = "/".join(str(main(x)) for x in _route.split("/"))
    return path

# class Dict(dict):
#     def __init__(self, *a, **kw):
#         super().__init__(*a, **kw)

#     def __getattr__(self, name):
#         return self[name]
    
#     def _make(self, obj=None):

#         def main(obj):
#             for item in obj:
#                 d = obj[item]
#                 if isinstance(d, dict):
#                     data = Dict(**d)
#                 elif isinstance(d, (list, tuple, set)):
#                     a = []
#                     for b in d:
#                         a.append(main(b))
#                     data = d.__new__(type(d), a)
#             return data
    
#         return main(obj or self)

# t = Dict({
#     "a": "ello",
#     "b": [{
#         "a": "Hiii",
#         "b": {
#             "a": "test"
#         }
#     },
#     {
#         "a": "Hiii",
#         "b": {
#             "a": "test"
#         }
#     }]
# })._make()
# print(t.a)
# print(t.b[0].a)
# print(t.b[1].b.a)

class Config(ConfigDict):
    prf = ""

    def use(self, module, begin=0, end=-1):
        self._source = None
        if type(module) is dict:
            self.load_dict(module)
        elif type(module) is str:
            if begin != 0 and end != -1:
                file = f"tmpconfig-{randint(0, 9)}.py"
                with open(file, "w") as config:
                    config.write(self._slicer(module, begin, end))
                self.load_module(file.replace(".py", ""))
                os.remove(file)
            else:
                self.load_module(module)
        return self

    def _slicer(self, module, begin, end):
        final = ""
        with open(module.__file__, "r") as code:
            write = False
            for i, line in enumerate(code):
                if isinstance(begin, int) and i == begin:
                    write = True
                elif isinstance(begin, str) and begin in line:
                    write = True

                elif isinstance(end, int) and i == end:
                    write = False
                    return final
                elif isinstance(end, str) and end in line:
                    write = False
                    return final

                if write:
                    final = final + "\n" + line
        return final
    
    @contextmanager
    def prefix(self, value):
        try:
            self.prf = str(value).rstrip(".") + "."
            yield self
        finally:
            self.prf = ""
    
    def get(self, key, e=None, raw=False):
        try:
            if raw:
                ret = self._source
                for item in key.split("."):
                    ret = ret[item]
                return ret
            return self[key]
        except:
            return e

    def set(self, key, value):
        self[key] = value
    
    def load_dict(self, source, namespace=''):
        if not self._source:self._source = source
        return super().load_dict(source, namespace)
    
    def __getattr__(self, name):
        name = str(self.prf.upper() + name)
        if name in self._source:
            return self._source[name]
        raise AttributeError
    
    def __getitem__(self, *key):
        try:
            return super().__getitem__(str(self.prf + key[0]).upper())
        except:
            if len(key) > 1:
                return key[1]
            raise KeyError(key[0])

    def __setitem__(self, key, value):
        # To Do: Improve -> config[key1, key2] = "Hii", "hey"
        # Improve -> config[key1, key2] = "Hii"
        return super().__setitem__(str(self.prf + key).upper(), value)


def _debug(*text):
    if config.get("debug", False):
        print("[debug]", *text)


class Configurator(ConfigDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.raw = self
        self.prfix = ''
    
    def __call__(self, *args, **kwds):
        return super().__init__(*args, **kwds)

    def __getitem__(self, name):
        return super().__getitem__(name.upper())

    def __setitem__(self, name, value):
        super().__setitem__(name.upper(), value)

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
        config = str(self.prfix+config)
        config = config.upper()
        try:return conf.__getitem__(config)
        except:return e

    def set(self, config, value):
        config = str(self.prfix+config)
        if config.upper() not in self:
            self[config.upper()] = value
        else:return False
    
    @contextmanager
    def prefix(self, prf):
        try:
            self.prfix = prf
        finally:
            self.prfix = ''


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


class Hooks:
    _ = {
        'before_request': [],
        'after_request': [],
        'config': [],
        'app_reset': [],
        'app_setup': [],
        'before_app_setup': [],
        'before_plugin_setup': [],
        'plugin_setup': []
    }

    app = None
    
    @classmethod
    def from_dict(cls, data):
        ret = cls.__new__(cls)
        ret._ = data
        return ret

    def __getattr__(self, name):
        if name in self._:
            return self.attach(name)
    
    def __getitem__(self, *args):
        return self._.get(*args, [])

    def attach(self, event, func=None, override=False):
        def wrapper(func):
            funcs = makelist(func or [])
            if event not in self._:
                self._[event] = funcs
            else:
                if override:
                    self._[event] = funcs
                else:
                    self._[event] += funcs
            return func
        return wrapper(func) if func else wrapper
    
    def trigger(self, event, apply=None, *args, **kwargs):
        if event in self._:
            for func in self._[event]:
                if callable(func):
                    if apply:
                        apply(func)(*args, **kwargs)
                    else:
                        func(*args, **kwargs)
        return True
    
    def remove(self, event):
        if event in self._:
            self._.pop(event)
    
    def detach(self, event, func):
        if event in self._ and func in self._[event]:
            self._[event].remove(func)

class Messages:
    def __init__(self):
        self.__data = []
        self.__old = ""

    @property
    def data(self):
        return self.__data
    
    def has_new(self):
        return len(self.data) > 0

    def add(self, *args):
        for arg in args:
            if arg:
                self.data.insert(0, arg)
    
    def get(self):
        self.__old = self.data.copy()
        self.__data = []
        return self.__old

class NamedRoutes:
    __data = {}

    @property
    def __app(self):
        app = get_global("APPMODULE")
        if not isinstance(app, str):
            app = str(app.__class__.__name__)
        app = app.lower().replace("app", '')
        return app

    @property
    def data(self):
        return self.__data
    
    def __contains__(self, name):
        return name in self.data[self.__app]

    def add(self, name, route, app=None):
        app = app or self.__app
        if app not in self.__data:
            self.__data[app] = {}
        if name not in self.__data[app]:
            self.__data[app][name] = []
        self.__data[app][name].append(route)
    
    __setitem__ = add
    
    def get(self, name, app=None, index=0, e=None):
        app = app or self.__app
        if app in self.__data:
            if name in self.__data[app]:
                return self.__data[app][name][index]
        return e or name
    
    __getitem__ = get
    
    def remove(self, name, app=None):
        app = app or self.__app
        if app in self.__data:
            if name in self.__data[app]:
                return self.__data[app].pop(name)

    def pop(self, name, app=None, index=0):
        app = app or self.__app
        if app in self.__data:
            if name in self.__data[app]:
                return self.__data[app][name].pop(index)

    def reverse(self, name,e=None, **kwargs):
        names = name.split(':')
        if len(names) == 1:
            name = names[0]
            app = self.__app
            index= 0
        elif len(names) == 2:
            app, name = names
            index = 0
        elif len(names) == 3:
            app, name, index = names
        else:
            app, name, *others = names
            index = 0
        
        try:
            return compile_route(self.__data[app][name][index], kwargs)
        except:
            return e or name


def is_main_app(name):
    if not type(name) is str:
        name = str(name.__class__.__name__)
    name = name.lower().replace("app", '')
    main = get_global("APPMODULE")
    if not type(main) is str:
        main = str(main.__class__.__name__)
    main = main.lower().replace("app", '')
    return name == main


class DatabaseStack(list):
    def push(self, db):
        self.insert(0, db)
        return

    def __getattr__(self, name):
        if len(self) > 0:
            item = getattr(self[0], name, None)
            if item:
                return item
        raise AttributeError

def setup():
    global db, hooks, config, ordered, messages, errors
    config = Config()

    try:
        config.use("settings")
    except ImportError:
        try:
            config.load_config("./settings.ini")
        except:
            pass

    ordered = NamedRoutes()
    hooks = Hooks()
    db = DatabaseStack()
    messages =  Messages()
    errors =  Messages()

if not _:
    setup()
    _ = True