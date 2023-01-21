from functools import singledispatch
import types
__all_scripts = {}

class BaseScripts:
    def __init__(self, *args):
        self.args = args

class ParserScripts(BaseScripts):
    def __init__(self, *args):
        self.args = self.parser(args)
        script()
        if hasattr(self, "__post_init__"):
            self.__post_init__()


@singledispatch
def script(name=None, *shorthand, help=None, func=None):
    def wrapper(func):
        func.__wsgic_script__ = True
        func.__script_alias__ = name or func.__name__
        func.__script_help__ = help or ""
        __all_scripts[func.__script_alias__] = func
        for na in shorthand:
            __all_scripts[na] = func
        return func
    return wrapper(func) if func else wrapper

@script.register(types.FunctionType)
def wrapper(func):
    func.__wsgic_script__ = True
    func.__script_alias__ = func.__name__
    func.__script_help__ = ""
    __all_scripts[func.__script_alias__] = func
    return func

def __get_scripts():
    return __all_scripts
