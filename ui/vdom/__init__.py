'''
Jyserver is a framework for simplifying the creation of font ends for apps and
kiosks by providing real-time access to the browser's DOM and Javascript from
the server using Python syntax. It also provides access to the Python code from
the browser's Javascript. It can be used stand-alone or with other
frameworks such as Flask, Django, etc. See examples folder.

Source: https://github.com/ftrias/jyserver

Example using Bottle
-------------------------------
```
from bottle import route, run
import jyserver.Bottle as js
import time

@js.use
class App():
    def reset(self):
        self.start0 = time.time()

    @js.task
    def main(self):
        self.start0 = time.time()
        while True:
            t = "{:.1f}".format(time.time() - self.start0)
            self.js.dom.time.innerHTML = t
            time.sleep(0.1)

@route('/')
def index():
    html = """
        <p id="time">WHEN</p>
        <button id="b1" onclick="server.reset()">Reset</button>
    """
    App.main()
    return App.render(html)

run(host='localhost', port=8080)
```
'''

import random
from inspect import signature
from types import *
from functools import cached_property

import sys
import traceback

import json
import threading
import queue
import os
import copy
import re
import time
import uuid

from . import jscript
from ..html import NodeList
from ..jsbuilder import *
from ..jsbuilder import _Scope, _to_str

UNDEFINED = object()


def load_module(target, **namespace):
    """ Import a module or fetch an object from a module.

        * ``package.module`` returns `module` as a module object.
        * ``pack.mod:name`` returns the module variable `name` from `pack.mod`.
        * ``pack.mod:func()`` calls `pack.mod.func()` and returns the result.

        The last form accepts not only function calls, but any type of
        expression. Keyword arguments passed to this function are available as
        local variables. Example: ``load_module('re:compile(x)', x='[a-z]')``
    """
    module, target = target.split(":", 1) if ':' in target else (target, None)
    if module not in sys.modules: __import__(module)
    if not target: return sys.modules[module]
    if target.isalnum(): return getattr(sys.modules[module], target)
    package_name = module.split('.')[0]
    namespace[package_name] = sys.modules[package_name]
    return eval('%s.%s' % (module, target), namespace)

def makelist(data):  # This is just too handy
    if isinstance(data, (tuple, list, set, dict)):
        return list(data)
    elif data:
        return [data]
    else:
        return []

class JsRuntimeError(Exception):
    pass

def generateEncoder(state):
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, JsObject):
                return obj.code
            if callable(obj):
                return "server.%s"%obj.__name__
            # Let the base class default method raise the TypeError
            return super().default(self, obj)
    return JSONEncoder

def generateDecoder(state):
    class JSONDecoder(json.JSONDecoder):
        def __init__(self, *a, **kw):
            super().__init__(object_hook=self.object_hook, *a, **kw)

        def object_hook(self, item: dict):
            for key, val in item.items():
                if isinstance(val, list):
                    vall = [self.object_hook(x) if isinstance(x, dict) else x for x in val]
                    if key:
                        item[key] = vall
                    else:
                        return vall
                elif isinstance(val, set):
                    vall = {self.object_hook(x) if isinstance(x, dict) else x for x in val}
                    if key:
                        item[key] = vall
                    else:
                        return vall

            if item.get("type") == "js_proxy":
                if item["obj_type"] == "nodelist":
                    return NodeList(item["value"])
                return JsProxy(item, state=state)
            elif isinstance(item, dict):
                return JsDict(**item)
            return item
    return JSONDecoder

def generate_jsClass(proxy):
    cls = copy.deepcopy(JsClass)
    cls.proxy = proxy
    return cls

class JsClass(object):
    def __init__(self, *a, **kw):
        self.__object = self.proxy.new(*a, **kw)

    def __getattr__(self, name):
        return self.__object.__getattr__(name)

    def __call__(self, *a, **kw):
        return self.__object.__call__(*a, **kw)

    @staticmethod
    def to_js(chain, arg):
        item = chain.state.proxy_object(arg)
        return ["client.get_result("+item+")"]

class JsProxy:
    def __init__(self, data, state):
        self.__data__ = data
        self.__state__ = state
    
    @property
    def __name__(self):
        return ""

    def new(self, *a, **kw):
        return self.__state__.obj.browser.client.callProxyConstructor(self.__data__['key'], 
        *a, **kw).eval()
    
    @cached_property
    def cls(self):
        if self.__data__["obj_type"] == "function":
            return generate_jsClass(self)
        raise TypeError("JsProxy object is not a class.")

    def __call__(self, *a, **kw):
        return self.__state__.obj.browser.client.callProxy(self.__data__['key'], *a, **kw).eval()

    def __getattr__(self, name):
        return self.__state__.obj.browser.client.getProxyAttribute(self.__data__['key'], name).eval()

    def __getitem__(self, index):
        return self.__state__.obj.browser.client.getProxyIndex(self.__data__['key'], index).eval()

    def __setitem__(self, index, value):
        return self.__state__.obj.browser.client.setProxyIndex(self.__data__['key'], index, value).eval()

    def __setattr__(self, name, val):
        if name not in ["__data__", "__state__"]:
            self.__state__.obj.browser.client.setProxyAttribute(self.__data__['key'], name, val).eval()
        else:
            return super().__setattr__(name, val)
    
    def __str__(self):
        if self.__data__["obj_type"] == "element":
            return str(self.outerHTML)
        else:
            # try:
            #     return str(self.toString())
            # except:
            return f"JsProxy(key='{self.__data__['key']}', type='{self.__data__['obj_type']}')"
    
    def __repr__(self):
        return str(self)

    def __del__(self):
        # try:
        #     return self.__state__.obj.browser.client.delProxy(self.__data__['key']).eval()
        # except:pass
        pass

class JsDict(dict):
    def __getattr__(self, key):
        return self.get(key)
    
    def __setattr__(self, key, value):
        self[key] = value

class ClientContext:
    contextMap = {}
    taskTimeout = 5

    def __init__(self, cls, uid=None, verbose=False, tasks=None, socket=None):
        self.appClass = cls.__class__
        self.obj = cls
        self.queries = {}
        # self.lock = threading.Lock()
        self.fxn = {}
        self.verbose = verbose
        # self.tasks = queue.Queue()
        self.uid = uid
        self._error = None
        self._signal = None
        self.obj.browser = JSroot(self)

        self.decoder = generateDecoder(self)
        self.encoder = generateEncoder(self)

        self.singleThread = False
        self.socket = None
        self.dom = None

        self.allowed_builtins = None
        self.allowed_imports = None

        self.disallowed_builtins = []
        self.disallowed_imports = []

        self.socket = socket
        self.command_tasks = tasks or {}
        self.signals = {}

        self.command_tasks["state"] = lambda req: ""
        self.command_tasks["run"] = lambda req: self.run(req['function'], req['args'], req)
        self.command_tasks["get"] = lambda req: self.get(req['expression'],req)
        self.command_tasks["set"] = lambda req: bool(self.set(req['property'], req['value']))
        self.command_tasks["async"] = lambda req: self.run(req['function'], req['args'], req, block=False)
        self.command_tasks["next"] = lambda req: self.getNextTask()
        self.command_tasks["unload"] = lambda req: self.addEndTask() or ""

        self.command_tasks["exec_python"] = lambda req: exec(req.code, self.obj.__dict__)

        self.command_tasks["error"] = self.setError
        self.command_tasks["get_type"] = self.handle_get_type
        self.command_tasks["attribute"] = self.handle_attribute

        self.command_tasks["get_proxy_attribute"] = self.get_proxy_attribute
        self.command_tasks["set_proxy_attribute"] = self.set_proxy_attribute
        self.command_tasks["get_proxy_attributes"] = self.get_proxy_attributes
        self.command_tasks["has_proxy_attribute"] = self.has_proxy_attribute
        self.command_tasks["delete_proxy_attribute"] = self.delete_proxy_attribute
        self.command_tasks["delete_proxy"] = self.delete_proxy
        self.command_tasks["call_proxy"] = self.call_proxy
        self.command_tasks["signal"] = self.handle_signal

        self.command_tasks["import"] = self.handle_import
        self.command_tasks["builtin"] = self.handle_builtin

    def __getattr__(self, name):
        if name in self.signals:
            return self.attach(name)

    def __getitem__(self, *args):
        return self.signals.get(*args, [])

    def attach(self, event, func=None, override=False):
        def wrapper(func):
            funcs = makelist(func or [])
            if event not in self.signals:
                self.signals[event] = funcs
            else:
                if override:
                    self.signals[event] = funcs
                else:
                    self.signals[event] += funcs
            return func
        return wrapper(func) if func else wrapper
    
    def trigger(self, event, apply=None, *args, **kwargs):
        if event in self.signals:
            for func in self.signals[event]:
                if callable(func):
                    if apply:
                        apply(func)(*args, **kwargs)
                    else:
                        func(*args, **kwargs)
        return True
    
    def remove(self, event):
        if event in self.signals:
            self.signals.pop(event)
    
    def detach(self, event, func):
        if event in self.signals and func in self.signals[event]:
            self.signals[event].remove(func)
    
    def handle_signal(self, req):
        target = req["signal"]
        self.trigger(target, *req["args"])
        user_func = getattr(self.obj, "on_client_"+target, None)
        if user_func:
            user_func(*req["args"])
        return None

    def render(self, html):
        '''
        Add Javascript to the given html that will enable use of this
        module. If using Django, this gets reassigned to `render_django()`.
        '''
        page = HtmlPage(html=html)
        html = page.html(self.uid)
        return html

    def render_django(self, inp):
        '''
        Version of `render()` for use with Django.
        '''
        # for Django support
        page = HtmlPage(html=inp.content)
        inp.content = page.html(self.uid)
        return inp

    def htmlsend(self, html=None, file=None):
        page = HtmlPage(html=html, file=file)
        html = page.html(self.uid)
        self._handler.reply(html)
        self.log_message("SET SIGNAL %s", id(self._signal))
        self._signal.set()
        return page

    def hasMethod(self, name):
        return hasattr(self.obj, name)

    def callMethod(self, name, args=None):
        if hasattr(self.obj, name):
            f = getattr(self.obj, name)
            if args is None:
                f()
            else:
                f(*args)
        else:
            raise ValueError("Method not found: " + name)

    def __getattr__(self, attr):
        '''
        Unhandled calls to the context get routed to the app
        object.
        '''
        return self.obj.__getattribute__(attr)

    def getJS(self):
        '''
        Return the JS object tied to this context. Use the return value to
        create JS statements.
        '''
        return self.obj.js

    @classmethod
    def _getContextForPage(self, uid, appClass, create = False, verbose = False):
        '''
        Retrieve the Client instance for a given session id. If `create` is
        True, then if the app is not found a new one will be created. Otherwise
        if the app is not found, return None.
        '''
        if uid and not isinstance(uid, str):
            # if uid is a cookie, get it's value
            uid = uid.value

        # if we're not using cookies, direct links have uid of None
        if uid is None:
            # get first key
            if len(self.contextMap) > 0:
                uid = list(self.contextMap.items())[0][0]
            else:
                uid = None

        # existing app? return it
        if uid in self.contextMap:
            return self.contextMap[uid]
        else:
            # this is a new session or invalid session
            # assign it a new id
            # Instantiate Client, call initialize and save it.
            context = ClientContext(appClass, uid, verbose=verbose)
            self.contextMap[uid] = context
            context.log_message("NEW CONTEXT %s ID=%s", uid, id(self))
            # If there is a "main" function, then start a new thread to run it.
            # _mainRun will run main and terminate the server after main returns.
            context.mainRun()
            return context

        raise ValueError("Invalid or empty seession id: %s" % uid)
    
    def setSocket(self, socket):
        self.socket = socket

    def setSocketIo(self, socket):
        self.socketio = socket
    
    def setDom(self, document):
        self.dom = document

    def setError(self, req):
        self._error = RuntimeError(req['error'] + ": " + req["expr"])
    
    def toJson(self, req, data, *a, **kw):
        if req:
            if req.get("message_id"):
                data["message_id"] = req["message_id"]
        return json.dumps(data, *a, cls=self.encoder, **kw)

    def processCommand(self, req):
        '''
        Process the /__process_srv0 requests. All client requests are directed to this
        URL and the framework is responsible for calling this function to process
        them.
        '''
        # pageid = req["session"]
        # if pageid in HtmlPage.pageMap:
        #     self.uid = HtmlPage.pageMap[pageid]
        # else:
        #     self.log_message("Invalid page id session %s", pageid)
        #     return 'Invalid pageid session: ' + pageid
        #     # raise RuntimeError("Invalid pageid session: " + pageid)

        # HtmlPage.pageActive[pageid] = time.time()

        task = req["task"]
        self.log_message("RECEIVE TASK %s %s", task, req)
        t = self.command_tasks.get(task, None)
        if t:
            data = t(req)
            self.log_message("CUSTOM RETURNED %s", data)
            return data
        return ""

    def getQuery(self, query):
        '''
        Each query sent to the browser is assigned to it's own Queue to wait for 
        a response. This function returns the Queue for the given session id and query.
        '''
        return self.queries[query]

    def addQuery(self):
        '''
        Set query is assigned to it's own Queue to wait for 
        a response. This function returns the Queue for the given session id and query.
        '''
        q = queue.Queue()
        self.queries[id(q)] = q
        return id(q), q

    def delQuery(self, query):
        '''
        Delete query is assigned to it's own Queue to wait for 
        a response. This function returns the Queue for the given session id and query.
        '''
        return self.queries[query]

    def addTask(self, stmt):
        '''
        Add a task to the queue. If the queue is too long (5 in this case)
        the browser is too slow for the speed at which we are sending commands.
        In that case, wait for up to one second before sending the command.
        Perhaps the wait time and queue length should be configurable because they
        affect responsiveness.
        '''
        for _ in range(10):
            if self.tasks.qsize() < 5:
                self.tasks.put(stmt)
                self.log_message("ADD TASK %s ON %d", stmt, id(self.tasks))
                return
            time.sleep(0.1)
        self._error = TimeoutError("Timeout (deadlock?) inserting task: " + stmt)

    def handle_get_type(self, req):
        target = getattr(self.obj, req["function"], None)
        if target:
            return self.toJson(req, {"value": str(type(target).__name__)})
        return self.toJson(req, {"value": None})
    
    def proxy_object(self, item):
        handle = None
        t = str(type(item).__name__)
        if isinstance(item, JsProxy):
            item = item.__data__["key"]
            t = "jsproxy"
        elif not isinstance(item, (int, str, dict, set, tuple, bool, float, NoneType)):
            handle = self.register_proxy(item)
            item = None

        if t in ["function", "method"]:
            t = "callable_proxy"

        try:
            return self.toJson(None, {"type": t, "value": item, "location": handle})
        except:
            return self.toJson(None, {"type": t, "value": str(item), "location": handle})

    def handle_attribute(self, req):
        target = getattr(self.obj, req["item"], UNDEFINED)
        handle = None
        if not (target is UNDEFINED):
            t = str(type(target).__name__)
            if isinstance(target, JsProxy):
                target = target.__data__["key"]
                t = "jsproxy"
            elif not isinstance(target, (int, str, dict, set, tuple, bool, float, NoneType)):
                handle = self.register_proxy(target)
                target = None

            if t in ["function", "method"]:
                t = "callable_proxy"
            try:
                return self.toJson(req, {"type": t, "value": target, "location": handle})
            except:
                return self.toJson(req, {"type": t, "value": str(target), "location": handle})
        return self.toJson(req, {"type": None, "value": None, "error": True})

    def handle_import(self, req):
        target = req["item"]

        module = target.split(":")[0] if ":" in target else target

        handle = None
        if target and (
            (self.allowed_imports is not None and module in self.allowed_imports) or 
            (module not in self.disallowed_imports)
        ):
            try:
                target = load_module(target)
            except Exception as e:
                return self.toJson(req, {"type": None, "value": None, "error": str(e).replace('"', "'")})
            t = str(type(target).__name__)
            if isinstance(target, JsProxy):
                target = target.__data__["key"]
                t = "jsproxy"
            elif not isinstance(target, (int, str, dict, set, tuple, bool, float, NoneType)):
                handle = self.register_proxy(target)
                target = None

            if t in ["function", "method"]:
                t = "callable_proxy"
            try:
                return self.toJson(req, {"type": t, "value": target, "location": handle})
            except:
                return self.toJson(req, {"type": t, "value": str(target), "location": handle})
        return self.toJson(req, {"type": None, "value": None, "error": True})

    def handle_builtin(self, req):
        target = req["item"]
        handle = None
        if target and (
            (self.allowed_builtins is not None and target in self.allowed_builtins) or 
            (target not in self.disallowed_builtins)
        ):
            target = load_module(f"builtins:{target}")
            t = str(type(target).__name__)
            if isinstance(target, JsProxy):
                target = target.__data__["key"]
                t = "jsproxy"
            elif not isinstance(target, (int, str, dict, set, tuple, bool, float, NoneType)):
                handle = self.register_proxy(target)
                target = None

            if t in ["function", "method", "builtin_function_or_method"]:
                t = "callable_proxy"
            try:
                return self.toJson(req, {"type": t, "value": target, "location": handle})
            except:
                return self.toJson(req, {"type": t, "value": str(target), "location": handle})
        return self.toJson(req, {"type": None, "value": None, "error": True})

    def get_proxy_attributes(self, req):
        target_attr = req.get("target", None)
        target = self.fxn.get(target_attr)
        if target:
            return self.toJson(req, {"value": dir(target)})

    def get_proxy_attribute(self, req):
        target_attr = req.get("target", None)
        target = self.fxn.get(target_attr)
        handle = None
        if target:
            attribute = getattr(target, req["prop"], None)
            if attribute:
                t = str(type(attribute).__name__)
                if isinstance(attribute, JsProxy):
                    attribute = attribute.__data__["key"]
                    t = "jsproxy"
                elif not isinstance(attribute, (int, str, dict, set, tuple, bool, float, NoneType)):
                    handle = self.register_proxy(attribute)
                    target = None

                if t in ["function", "method"]:
                    t = "callable_proxy"
                try:
                    return self.toJson(req, {"type": t, "value": attribute, "location": handle})
                except:
                    return self.toJson(req, {"type": t, "value": str(attribute), "location": handle})
        return self.toJson(req, {"type": None, "value": None, "error": True})


    def set_proxy_attribute(self, req):
        target_attr = req.get("target", None)
        target = self.fxn.get(target_attr)
        if target:
            try:
                setattr(target, req["prop"], req["value"])
                return self.toJson(req, {"value": True})
            except Exception as e:
                return self.toJson(req, {"type": None, "value": None, "error": str(e).replace('"', "'")})
        return self.toJson(req, {"value": False})

    def delete_proxy_attribute(self, req):
        target_attr = req.get("target", None)
        target = self.fxn.get(target_attr)
        if target:
            try:
                value = delattr(target, req["prop"])
                return self.toJson(req, {"value": value})
            except Exception as e:
                return self.toJson(req, {"type": None, "value": None, "error": str(e).replace('"', "'")})
        return self.toJson(req, {"type": None, "value": None, "error": True})

    def has_proxy_attribute(self, req):
        target_attr = req.get("target", None)
        target = self.fxn.get(target_attr)
        if target:
            try:
                value = hasattr(target, req["prop"])
                return self.toJson(req, {"value": value})
            except Exception as e:
                return self.toJson(req, {"type": None, "value": None, "error": str(e).replace('"', "'")})
        return self.toJson(req, {"type": None, "value": None, "error": True})

    def call_proxy(self, req):
        target_attr = req.get("target", None)
        target = self.fxn.get(target_attr)
        print(req, target, self.fxn)
        handle = None
        if target:
            try:
                # print(req)
                attribute = target(*req.get("args", []), **req.get("kwargs", {}))
                if attribute:
                    t = str(type(attribute).__name__)
                    if isinstance(attribute, JsProxy):
                        attribute = attribute.__data__["key"]
                        t = "jsproxy"
                    elif not isinstance(attribute, (int, str, dict, set, tuple, bool, float, NoneType)):
                        handle = self.register_proxy(attribute)
                        target = None

                    if t in ["function", "method"]:
                        t = "callable_proxy"
                    try:
                        return self.toJson(req, {"type": t, "value": attribute, "location": handle})
                    except:
                        return self.toJson(req, {"type": t, "value": str(attribute), "location": handle})
                return self.toJson(req, {"error": False, "value": None})
            except Exception as e:
                raise e
                return self.toJson(req, {"type": None, "value": None, "error": str(e).replace('"', "'")})
        return self.toJson(req, {"type": None, "value": None, "error": "AttributeError: No such proxy"})
    
    def delete_proxy(self, req):
        target_attr = req.get("target", None)
        if target_attr:
            try:
                self.fxn.pop(target_attr, False)
                return self.toJson(req, {"value": True})
            except Exception as e:
                return self.toJson(req, {"type": None, "value": None, "error": str(e).replace('"', "'")})
        return self.toJson(req, {"type": None, "value": None, "error": True})

    def register_proxy(self, target):
        if target in self.fxn.values():
            for k, v in self.fxn.items():
                if target == v:
                    return k

        unique_id = id(target)
        self.fxn[unique_id] = target
        # print(self.fxn, unique_id)
        return unique_id

    def run(self, function, args, req, block=True):
        '''
        Called by the framework to execute a method. This function will look for a method
        with the given name. If it is found, it will execute it. If it is not found it
        will return a string saying so. If there is an error during execution it will
        return a string with the error message.
        '''
        self.log_message("RUN %s %s", function, args)
        if block:
            if not self.lock.acquire(blocking = False):
                raise RuntimeError("App is active and would block")
        
        try:
            if function == "_callfxn":
                # first argument is the function name
                # subsequent args are optional
                fxn = args.pop(0)
                f = self.fxn[fxn]
            elif callable(function):
                f = function
            else:
                f = getattr(self.obj, function, None)

            if f:
                try:
                    result = f(*args)
                    ret = self.toJson(req, {"value":JSroot._v(result)})
                except Exception as ex:
                    s = "%s: %s" % (type(ex).__name__, str(ex))
                    if self.verbose: traceback.print_exc()
                    self.log_message("Exception passed to browser: %s", s)
                    ret = self.toJson(req, {"error":s.replace('"', "'")})
            else:
                result = "Unsupported: " + function + "(" + str(args) + ")"
                ret = self.toJson(req, {"error":str(result).replace('"', "'")})
            self.log_message("RUN RESULT %s", ret)
            return ret
        finally:
            if block:
                self.lock.release()

    def get(self, expr, req):
        '''
        Called by the framework to execute a method. This function will look for a method
        with the given name. If it is found, it will execute it. If it is not found it
        will return a string saying so. If there is an error during execution it will
        return a string with the error message.
        '''
        self.log_message("GET EXPR %s", expr)
        if not self.lock.acquire(blocking = False):
            raise RuntimeError("App is active and would block")
        
        try:
            if hasattr(self.obj, expr):
                value = getattr(self.obj, expr)
                if callable(value):
                    value = "(function(...args) { return handleApp('%s', args) })" % expr 
                    return self.toJson(req, {"type":"expression", "expression":value})       
                else:
                    return self.toJson(req, {"type":"value", "value":value})
            return None
        finally:
            self.lock.release()

    def set(self, expr, value):
        '''
        Called by the framework to set a propery.
        '''
        self.log_message("SET EXPR %s = %s", expr, value)
        self.obj.__setattr__(expr, value)
        return value

    def getNextTask(self):
        '''
        Wait for new tasks and return the next one. It will wait for 1 second and if
        there are no tasks return None.
        '''
        try:
            self.log_message("TASKS WAITING %d ON %d", self.tasks.qsize(), id(self.tasks))
            return self.tasks.get(timeout=self.taskTimeout)
        except queue.Empty:
            return None

    def addEndTask(self):
        '''
        Add a None task to end the queue.
        '''
        self.log_message("TASKS END %d ON %d", self.tasks.qsize(), id(self.tasks))
        self.tasks.put(None)

    def mainRun(self):
        '''
        If there is a method called `main` in the client app, then run it in its own
        thread.
        '''
        if hasattr(self.obj, "main"):
            server_thread = threading.Thread(
                target=self.mainRunThread, daemon=True)
            server_thread.start()

    def mainRunThread(self):
        '''
        Run the main function. When the function ends, terminate the server.
        '''
        try:
            self.obj.main()
        except Exception as ex:
            self.log_message("FATAL ERROR: %s", ex)

    def showPage(self, handler, path, query):
        '''
        Called by framework to return a queried page. When the browser requests a web page
        (for example when a user clicks on a link), the path will get put in `path` and
        any paramters passed through GET or POST will get passed in `query`. This will
        look for a Client method with the same name as the page requested. If found, it will
        execute it and return the results. If not, it will return "not found", status 404.
        '''
        if callable(path):
            f = path
        else:
            fxn = path[1:].replace('/', '_').replace('.', '_')
            if hasattr(self.obj, fxn):
                f = getattr(self.obj, fxn)
            elif path == "/favicon.ico":
                handler.reply("Not found %s" % path, 404)
                return
            else:
                raise RuntimeWarning("Page not found: " + path)
                # return "Not found", 404

        self._handler = handler
        self._signal = threading.Event()
        self.log_message("START PAGE %s %d", path, id(self._signal))
        server_thread = threading.Thread(target=self.run_callable, 
                args=(f, {"page": path, "query": query}), daemon=True)
        server_thread.start()
        self.log_message("WAIT ON SIGNAL %s %d", path, id(self._signal))
        self._signal.wait() # set when HTML is sent
        self._signal = None

    def run_callable(self, f, args):
        '''
        Execute a callable (function, etc) and catch any exceptions. This
        is called when running pages asynchonously.
        '''
        params = signature(f).parameters
        try:
            if len(params) == 0:
                f()
            else:
                f(args)
        except Exception as ex:
            traceback.print_exc()
            self.log_message("Exception: %s" % str(ex))

    def showHome(self):
        '''
        Get the home page when "/" is queried and inject the appropriate javascript
        code. Returns a byte string suitable for replying back to the browser.
        '''
        if hasattr(self.obj, "html"):
            block = self.obj.html.encode("utf8")
            page = HtmlPage(block)
            self.activePage = page.pageid
            return page.html(self.uid)
        elif hasattr(self.obj, "home"):
            path = self.obj.home
        elif os.path.exists("index.html"):
            path = "index.html"
        elif hasattr(self.obj, "index"):
            return self.obj.index
        else:
            raise ValueError("Could not find index or home")

        with open(path, "rb") as f:
            block = f.read()
            page = HtmlPage(block)
            self.activePage = page.pageid
            return page.html(self.uid)

    def log_message(self, format, *args):
        if self.verbose:
            print(format % args)

    def log_error(self, format, *args):
        print(format % args)

class HtmlPage:
    # Patterns for matching HTML to figure out where to inject the javascript code
    _pscript = re.compile(
        b'\\<script.*\\s+src\\s*=\\s*"jyserver.js"')
    _plist = [re.compile(b'\\{\\{JSCRIPT\\}\\}', re.IGNORECASE),
        re.compile(b'\\<script\\>', re.IGNORECASE),
        re.compile(b'\\<\\/head\\>', re.IGNORECASE),
        re.compile(b'\\<body\\>', re.IGNORECASE),
        re.compile(b'\\<html\\>', re.IGNORECASE)]

    pageMap = {}
    pageActive = {}
    # pageThread = {}
                       
    def __init__(self, html=None, file=None):
        if file:
            with open(file, "rb") as f:
                self.result = f.read()
        elif html:
            if isinstance(html, bytes):
                self.result = html
            else:
                self.result = html.encode("utf8")
        else:
            self.result = None
        self.pageid = uuid.uuid1().hex

    def alive(self):
        '''
        See if the current page is in the active page list and has not been
        expired.
        '''
        return self.pageid in self.pageActive

    @classmethod
    def expire(cls, item=None):
        '''
        Expire objects in the page cache.
        '''
        if item:
            del cls.pageActive[item]
            del cls.pageMap[item]
            
        old = time.time() - 5
        remove = []
        for k,v in cls.pageActive.items():
            if v < old:
                remove.append(k)
        for k in remove:
            del cls.pageActive[k]
            del cls.pageMap[k]

    def html(self, uid):
        '''
        Once the page has been loaded, this will return the appropriate
        HTML for the uid given.
        '''
        return self.insertJS(uid, self.result)

    def insertJS(self, uid, html):
        '''
        Insert the Javascript library into HTML. The strategy is that it will look for patterns
        to figure out where to insert. If "<script src="jyscript.js">" is found, it will not
        make changes and will return the Javascript when the browser requests the jyscript.js
        file. Otherwise, it will insert it into a <script> section, the <head> or at the start
        of the HTML. In any case, this function will insert the global variable UID containing
        the session id.
        '''
        self.pageMap[self.pageid] = uid
        # self.pageThread[self.pageid] = threading.get_ident()
        self.pageActive[self.pageid] = time.time()

        U = "var UID='{}';var PAGEID='{}';\n".format(uid, self.pageid).encode("utf8")
        m = self._pscript.search(html)
        if m:
            sx, ex = m.span()
            return html[:sx] + b"<script>"+U+b"</script>" + html[sx:]
        for i, p in enumerate(self._plist):
            m = p.search(html)
            if m:
                sx, ex = m.span()
                if i == 0:
                    return html[:sx] + U + jscript.JSCRIPT + html[ex:]
                elif i == 1:
                    return html[:sx] + b"<script>" + U + jscript.JSCRIPT + b"</script>" + html[sx:]
                elif i == 2:
                    return html[:sx] + b"<script>" + U + jscript.JSCRIPT + b"</script>" + html[sx:]
                else:
                    return html[:sx] + b"<head><script>" + U + jscript.JSCRIPT + b"</script></head>" + html
        return b"<head><script>" + U + jscript.JSCRIPT + b"</script></head>" + html

class JsObject:
    def __init__(self, code=None, client=None):
        self.code = code or ""
        self.chain = JSchain()
        if client:
            self.bind(client)

    def bind(self, client):
        self.chain._bind(client)
        return self

    def eval(self, client=None):
        if client:
            self.bind(client)
        self.chain.chain = []
        self.chain._add(self.code)
        return self.chain.eval()
    
    def __call__(self):
        return self.eval()


class JSFunc(JsObject):
    def __init__(self, func, py_scope={}, *a, **kw):
        super().__init__(*a, **kw)
        self._orig = func
        self._py_scope = py_scope

        source_code = inspect.getsource(func)
        code_ast = ast.parse(textwrap.dedent(source_code))
        self._code = code_ast.body[0].body

    def compile(self):
        empty_scope = _Scope()
        initial_code_py = '\n'.join(
            "%s = %s" % (k, self.chain._formatArg(v)[0])
            for (k, v) in self._py_scope.items()
        )

        if initial_code_py:
            initial_code_ast = ast.parse(textwrap.dedent(initial_code_py))
            self._initial_code_js = _to_str(
                initial_code_ast.body, empty_scope) + ";"
        else:
            self._initial_code_js = ""

        self.code = self._initial_code_js + _to_str(
            self._code,
            _Scope(self._py_scope)
        )
        print(self.code)
    
    def eval(self, scope=None, client=None):
        if scope:
            self._py_scope = scope
        if client:
            self.bind(client)
        self.compile()
        return super().eval()

    def __str__(self):
        return self.code

class JSchain:
    '''
    JSchain keeps track of the dynamically generated Javascript. It
    tracks names, data item accesses and function calls. JSchain
    is usually not used directly, but accessed through the JS class.

    Attributes
    -----------
    state
        A JSstate instance. This instance should be the same
        for all call of the same session.
        
    Notes
    -----------
    There is a special name called `dom` which is shorthand for
    lookups. For example,

        js.dom.button1.innerHTML

    Becomes

        js.document.getElementById("button1").innerHTML

    Example
    --------------
    ```
    state = JSstate(server)
    js = JSchain(state)
    js.document.getElementById("txt").value
    ```
    '''

    def __init__(self, state=None):
        self.state: ClientContext = state
        self.chain = []
        self.keep = True
    
    def _bind(self, state):
        self.state = state

    def _dup(self):
        '''
        Duplicate this chain for processing.
        '''
        js = JSchain(self.state)
        js.chain = self.chain.copy()  # [x[:] for x in self.chain]
        return js

    def _add(self, attr, prepend="."):
        '''
        Add item to the chain. If `dot` is True, then a dot is added. If
        not, this is probably a function call and not dot should be added.
        '''
        if not attr:
            # this happens when __setattr__ is called when the first
            # item of a JSchain is an assignment
            return self
        if prepend and len(self.chain) > 0:
            self.chain.append(prepend)
        
        self.chain.append(attr)
        return self

    def _prepend(self, attr):
        '''
        Add item to the start of the chain. 
        '''

        self.chain.insert(0, attr)
        return self

    def _last(self):
        '''
        Last item on the chain.
        '''
        return self.chain[-1]
    
    def new(self, *args, **kwargs):
        self._prepend(" ")
        self._prepend("new")
        all_args = list(args) +  list(kwargs.values())

        self._add('(', prepend="")
        [self._add(x, prepend="") for x in self._formatArgs(all_args)]
        if self._last() == ",":
            self.chain.pop()
        self._add(')', prepend="")
        return self.eval()
    
    def js(self, code, eval=False):
        self._add(code, prepend="")
        if eval:
           return self.eval()
        return self

    def __getattr__(self, attr):
        '''
        Called to process items in a dot chain in Python syntax. For example,
        in a.b.c, this will get called for "b" and "c".
        '''
        # __iter__ calls should be ignored
        if attr == "__iter__":
            return self
        return self.getdata(attr)

    def getdata(self, attr, aprepend="."):
        if self._last() == 'dom':
            # substitute the `dom` shortcut
            self.chain[-1] = 'document'
            self._add('getElementById')
            self._add('("{}")'.format(attr), prepend="")
        else:
            # add the item to the chain
            self._add(attr, prepend=aprepend)
        return self

    def __setattr__(self, attr, value):
        value = JSroot._v(value)
        if attr == "chain" or attr == "state" or attr == "keep":
            # ignore our own attributes. If an attribute is added to "self" it
            # should be added here. I suppose this could be evaluated dynamically
            # using the __dict__ member.
            super(JSchain, self).__setattr__(attr, value)
            return value
        # print("SET", attr, value)
        self.setdata(attr, value)
        self.execExpression()

    def setdata(self, attr, value, aprepend="."):
        '''
        Called during assigment, as in `self.js.x = 10` or during a call
        assignement as in `self.js.onclick = func`, where func is a function.
        '''
        # if callable(value):
        #     # is this a function call?
        #     idx = self.state.proxy_object(value)
        #     self._add("eval::"+attr, prepend=aprepend)
        #     # self._add("=function(){{server._callfxn(%s);}}" % idx, prepend="")
        #     self._add(" = client.formatters.callable_proxy('', client.parse(`%s`));" % idx, prepend="")
        # else:
        # otherwise, regular assignment
        self._add(attr, prepend=aprepend)
        self._add("=", prepend="")
        [self._add(x, prepend="") for x in self._formatArg(value)]

        # print(self.chain)
        return value

    def __setitem__(self, key, value):
        jkey = "['%s']" % str(key)
        self.setdata(jkey, value, aprepend="")
        self.execExpression()
        return value

    def __getitem__(self, key):
        # all keys are strings in json, so format it
        key = str(key)
        c = self._dup()
        c._prepend("'%s' in " % key)
        haskey = c.eval()
        if not haskey:
            raise KeyError(key)
        jkey = "['%s']" % key
        c = self.getdata(jkey, aprepend="")
        return c.eval()
    
    # def _formatArg(self, arg):
    #     arg = JSroot._v(arg)

    #     # print(arg, type(arg))
    #     # print()
    #     if isinstance(arg, JsObject):
    #         self._add(arg.code, prepend="")
    #     elif isinstance(arg, JsProxy):
    #         self._add(f"client.getProxyObject('{arg.__data__['key']}')", prepend="")
    #     elif isinstance(arg, JsClass):
    #         item = self.state.proxy_object(arg)
    #         return self._add("client.PyProxy("+item+")", prepend="")
    #     elif isinstance(arg, list):
    #         self._add("[", prepend="")
    #         self._formatArgs(arg)
    #         self._add("]", prepend="")
    #     elif isinstance(arg, tuple):
    #         self._add("(", prepend="")
    #         self._formatArgs(arg)
    #         self._add(")", prepend="")
    #     elif isinstance(arg, set):
    #         self._add("{", prepend="")
    #         self._formatArgs(arg)
    #         self._add("}", prepend="")
    #     elif isinstance(arg, dict):
    #         self._add("{", prepend="")
    #         for k,v in arg.items():
    #             self._add(self._formatArg(k), prepend="")
    #             self._add(":", prepend="")
    #             self._add(self._formatArg(v), prepend="")
    #             self._add(",", prepend="")
    #         if self._last() == ",":
    #             self.chain.pop()
    #         self._add("}", prepend="")
    #     elif hasattr(arg, "to_js"):
    #         arg.to_js(self, arg)
    #         # self._add(f'{val}', prepend="")
    #     elif callable(arg):
    #         temp_name = getattr(arg, "__name__", f"temp_func_{random.randint(0, 100000000)}")

    #         if not hasattr(self.state.obj, temp_name):
    #             self.state.obj.__register__(temp_name, arg)
    #             # print(temp_name, self.state.obj.customs)

    #         self._add(f"(...args) => server.{temp_name}.then(f => f(...args))", prepend="")
    #     else:
    #         val = repr(arg)
    #         self._add(f'{val}', prepend="")

    def _formatArg(self, arg):
        # arg = JSroot._v(arg)

        ret = []

        # print(arg, type(arg))
        # print()
        if isinstance(arg, JsObject):
            ret.append(arg.code)
        elif isinstance(arg, JSchain):
            ret.append(arg._statement())
        elif isinstance(arg, JsProxy):
            ret.append(f"client.getProxyObject('{arg.__data__['key']}')")
        elif isinstance(arg, JsClass):
            item = self.state.proxy_object(arg)
            ret.append("client.get_result("+item+")")
        elif isinstance(arg, list):
            ret.append("[")
            [ret.append(x) for x in self._formatArgs(arg)]
            ret.append("]")
        elif isinstance(arg, tuple):
            ret.append("(")
            [ret.append(x) for x in self._formatArgs(arg)]
            ret.append(")")
        elif isinstance(arg, set):
            ret.append("{")
            [ret.append(x) for x in self._formatArgs(arg)]
            ret.append("}")
        elif isinstance(arg, dict):
            ret.append("{")
            for k,v in arg.items():
                [ret.append(x) for x in self._formatArg(k)]
                ret.append(":")
                [ret.append(x) for x in self._formatArg(v)]
                ret.append(",")
            if len(ret) > 1 and ret[-1] == ",":
                ret.pop()
            ret.append("}")
        elif hasattr(arg, "to_js"):
            [ret.append(x) for x in arg.to_js(self, arg)]
            # ret.append(f'{val}')
        elif isinstance(arg, NoneType):
            ret.append("null")
        # elif isinstance(arg, (FunctionType, MethodType)):
        #     pass
        else:
            if not isinstance(arg, (int, str, dict, set, tuple, bool, float)):
                item = self.state.proxy_object(arg)
                ret.append("client.get_result("+item+")")
            else:
                # try:
                #     val = json.dumps(arg)
                # except:
                val = repr(arg)
                ret.append(f'{val}')
        # elif callable(arg):
        #     temp_name = getattr(arg, "__name__", f"temp_func_{random.randint(0, 100000000)}")

        #     if not hasattr(self.state.obj, temp_name):
        #         self.state.obj.__register__(temp_name, arg)
        #         # print(temp_name, self.state.obj.customs)

        #     ret.append(f"server.{temp_name}")
        # else:
        #     val = repr(arg)
        #     ret.append(f'{val}')
        return ret

    def _formatArgs(self, args):
        ret = []

        for item in args[:-1]:
            [ret.append(x) for x in self._formatArg(item)]
            ret.append(",")
            # self._add(",", prepend="")

        if len(args) > 0:
            [ret.append(x) for x in self._formatArg(args[-1])]
        return ret

            # self._formatArg(args[-1])

    # def __call__(self, *args, **kwargs):
    #     '''
    #     Called when we are using in a functiion context, as in
    #     `self.js.func(15)`.
    #     '''
    #     # evaluate the arguments
    #     p1 = [self.toJson(req, JSroot._v(v)) for v in args]
    #     p2 = [self.toJson(req, JSroot._v(v)) for k, v in kwargs.items()]
    #     s = ','.join(p1 + p2)
    #     # create the function call
    #     self._add('('+s+')', prepend="")
    #     return self
    def __call__(self, *args, **kwargs):
        '''
        Called when we are using in a functiion context, as in
        `self.js.func(15)`.
        '''
        # evaluate the arguments
        # p1 = [self.toJson(req, JSroot._v(v)) for v in args]
        # p2 = [self.toJson(req, JSroot._v(v)) for k, v in kwargs.items()]
        all_args = list(args) +  list(kwargs.values())

        # print(all_args)

        self._add('(', prepend="")

        [self._add(x, prepend="") for x in self._formatArgs(all_args)]

        if self._last() == ",":
            self.chain.pop()
        self._add(')', prepend="")
        # print(self.chain)
        return self

    def _statement(self):
        '''
        Join all the elements and return a string representation of the
        Javascript expression.
        '''
        return ''.join(self.chain)

    def __bytes__(self):
        '''
        Join the elements and return as bytes encode in utf8 suitable for
        sending back to the browser.
        '''
        return (''.join(self.chain)).encode("utf8")

    def evalAsync(self):
        if self.keep:
            stmt = self._statement()
            self.state.addTask(stmt)
            # mark it as evaluated
            self.keep = False

    def __del__(self):
        '''
        Execute the statment when the object is deleted.

        An object is deleted when it goes out of scope. That's when it is put
        together and sent to the browser for execution. 

        For statements,
        this happens when the statement ends. For example,

           self.js.func(1)

        goes out of scope when the statement after func(1). However,

           v = self.js.myvalue

        goes out of scope when the "v" goes out of scope, usually at then end of
        the function where it was used. In this case, the Javascript will be
        evaluated when "v" itself is evaluated. This happens when you perform
        an operation such as "v+5", saving or printing.

        "v" in the example above is assigned an object and not a value. This
        means that every time it is evaluated in an expression, it goes back 
        to the server and retrieves the current value.

        On the other hand,

           self.v = self.js.myvalue

        will probably never go out of scope because it is tied to the class.
        To force an evaluation, call the "eval()"
        method, as in "self.js.myvalue.eval()".
        '''
        if not self.keep: return
        # print("!!!DEL!!!")
        try:
            if self.state:
                self.execExpression()
        except Exception as ex:
            if self.state:
                self.state._error = ex
                self.state.log_error("Uncatchable exception: %s", str(ex))
            raise ex

    def execExpression(self):
        # Is this a temporary expression that cannot evaluated?
        if self.keep:
            stmt = self._statement()
            # print("EXEC", stmt)
            if self.state.singleThread:
                # print("ASYNC0", stmt)
                # can't run multiple queries, so just run it async
                self.state.addTask(stmt)
            else:
                # otherwise, wait for evaluation
                # print("SYNC", stmt)
                try:
                    self.eval()
                finally:
                    self.keep = False

            # mark it as evaluated
            self.keep = False

    def eval(self, timeout=10):
        '''
        Evaluate this object by converting it to Javascript, sending it to the browser
        and waiting for a response. This function is automatically called when the object
        is used in operators or goes out of scope so it rarely needs to
        be called directly.

        However, it is helpful
        to occasionally call this to avoid out-of-order results. For example,

            v = self.js.var1
            self.js.var1 = 10
            print(v)

        This will print the value 10, regardless of what var1 was before the assignment.
        That is because "v" is the abstract statemnt, not the evaluated value. 
        The assigment "var1=10" is evaluated immediately. However,
        "v" is evaluated by the Browser 
        when "v" is converted to a string in the print statement. If this is a problem,
        the code should be changed to:

            v = self.js.var1.eval()
            self.js.var1 = 10
            print(v)

        In that case, "v" is resolved immediately and hold the value of var1 before the
        assignment.

        Attributes
        -------------
        timeout
            Time to wait in seconds before giving up if no response is received.
        '''
        if not self.keep:
            return 0
            # raise ValueError("Expression cannot be evaluated")
        else:
            self.keep = False

        stmt = self._statement()
        # print("EVAL", stmt)

        c = self.state

        # if not c.lock.acquire(blocking = False):
        #     c.log_error("App is active so you cannot wait for result of JS: %s" % stmt)
        #     c.addTask(stmt)
        #     return 0
        #     # raise RuntimeError("App is active so you cannot evaluate JS for: %s" % stmt)

        try:
            # idx, q = c.addQuery()
            data = c.toJson(None, stmt)
            cmd = 'client.sendFromBrowserToServer(%s)'%(data)
            socket = c.socket or c.socketio
            value = {
                "msg": None
            }

            if socket:
                socket.send(c.toJson(None, {"expression": cmd}))
            elif c.socketio:
                socket.emit("message", c.toJson(None, {"expression": cmd}))

                on_msg = socket.handlers["/"].get("message")
                
                @socket.on("message")
                def _(ev, data):
                    print(data)
                    value["msg"] = data
                    socket.on("message")(on_msg)

            # else:
                # c.addTask(cmd)
            try:
                c.log_message("WAITING ON RESULT QUEUE")

                if c.socket:
                    try:
                        recv  = socket.receive()
                        result = json.loads(recv, cls=c.decoder)
                    except Exception as e:
                        raise e
                elif c.socketio:
                    try:
                        while True:
                            time.sleep(0.1)
                            if value["msg"]:
                                break
                        result = json.loads(value["msg"], cls=c.decoder)
                    except Exception as e:
                        raise e
                else:
                    result = {}
                # else:
                #     result = q.get(timeout=timeout)
                # print("Result is", result)
                c.log_message("RESULT QUEUE %s", result)
                # c.delQuery(idx)
            except Exception as e:
                raise e
                raise RuntimeError("Socker Error executing: ", cmd)
            except queue.Empty:
                c.log_message("TIMEOUT waiting on: %s", stmt)
                raise TimeoutError("Timout waiting on: %s" % stmt)

            if result.get("error", "") != "":
                c.log_error("ERROR EVAL %s : %s", result["error"], stmt)
                raise JsRuntimeError(result["error"] + ": " + stmt)
            
            if "value" in result:
                return result["value"]
            else:
                return 0

        finally:
            pass
            # c.lock.release()

    #
    # Magic methods. We create these methods for force the
    # Javascript to be evaluated if it is used in any
    # opreation.
    #
    def __cmp__(self, other): return self.eval().__cmp__(other)
    def __eq__(self, other): return self.eval().__eq__(other)
    def __ne__(self, other): return self.eval().__ne__(other)
    def __gt__(self, other): return self.eval().__gt__(other)
    def __lt__(self, other): return self.eval().__lt__(other)
    def __ge__(self, other): return self.eval().__ge__(other)
    def __le__(self, other): return self.eval().__le__(other)

    def __pos__(self): return self.eval().__pos__()
    def __neg__(self): return self.eval().__neg__()
    def __abs__(self): return self.eval().__abs__()
    def __invert__(self): return self.eval().__invert__()
    def __round__(self, n): return self.eval().__round__(n)
    def __floor__(self): return self.eval().__floor__()
    def __ceil__(self): return self.eval().__ceil__()
    def __trunc__(self): return self.eval().__trunc__()

    def __add__(self, other): return self.eval().__add__(other)
    def __and__(self, other): return self.eval().__and__(other)
    def __div__(self, other): return self.eval().__div__(other)
    def __divmod__(self, other): return self.eval().__divmod__(other)
    def __floordiv__(self, other): return self.eval().__floordiv__(other)
    def __lshift__(self, other): return self.eval().__lshift__(other)
    def __mod__(self, other): return self.eval().__mod__(other)
    def __mul__(self, other): return self.eval().__mul__(other)
    def __or__(self, other): return self.eval().__or__(other)
    def __pow__(self, other): return self.eval().__pow__(other)
    def __rshift__(self, other): return self.eval().__rshift__(other)
    def __sub__(self, other): return self.eval().__sub__(other)
    def __truediv__(self, other): return self.eval().__truediv__(other)
    def __xor__(self, other): return self.eval().__xor__(other)

    def __radd__(self, other): return self.eval().__radd__(other)
    def __rand__(self, other): return self.eval().__rand__(other)
    def __rdiv__(self, other): return self.eval().__rdiv__(other)
    def __rdivmod__(self, other): return self.eval().__rdivmod__(other)
    def __rfloordiv__(self, other): return self.eval().__rfloordiv__(other)
    def __rlshift__(self, other): return self.eval().__rlshift__(other)
    def __rmod__(self, other): return self.eval().__rmod__(other)
    def __rmul__(self, other): return self.eval().__rmul__(other)
    def __ror__(self, other): return self.eval().__ror__(other)
    def __rpow__(self, other): return self.eval().__rpow__(other)
    def __rrshift__(self, other): return self.eval().__rrshift__(other)
    def __rsub__(self, other): return self.eval().__rsub__(other)
    def __rtruediv__(self, other): return self.eval().__rtruediv__(other)
    def __rxor__(self, other): return self.eval().__rxor__(other)

    def __coerce__(self, other): return self.eval().__coerce__(other)
    def __complex__(self): return self.eval().__complex__()
    def __float__(self): return self.eval().__float__()
    def __hex__(self): return self.eval().__hex__()
    def __index__(self): return self.eval().__index__()
    def __int__(self): return self.eval().__int__()
    def __long__(self): return self.eval().__long__()
    def __oct__(self): return self.eval().__oct__()
    def __str__(self): return self.eval().__str__()
    def __dir__(self): return self.eval().__dir__()
    def __format__(self, formatstr): return self.eval().__format__(formatstr)
    def __hash__(self): return self.eval().__hash__()
    def __nonzero__(self): return self.eval().__nonzero__()
    def __repr__(self): return self.eval().__repr__()
    def __sizeof__(self): return self.eval().__sizeof__()
    def __unicode__(self): return self.eval().__unicode__()

    def __iter__(self): return self.eval().__iter__()
    def __reversed__(self): return self.eval().__reversed__()
    def __contains__(self, item): 
        d = self.eval()
        if isinstance(d, dict):
            # json makes all keys strings
            return d.__contains__(str(item))
        else:
            return d.__contains__(item)
    # def __missing__(self, key): return self.eval().__missing__(key)


class JSroot:
    '''
    JS handles the lifespan of JSchain objects and things like setting
    and evaluation on the root object.

    Example:
    --------------
    ```
    state = ClientContext(AppClass)
    js = JSroot(state)
    js.document.getElementById("txt").value = 25
    ```
    '''

    def __init__(self, state):
        # state is a JSstate instance unique for each session
        self.state = state
        # keep track of assignments
        self.linkset = {}
        # keep track of calls
        self.linkcall = {}

    @staticmethod
    def _v(value):
        '''
        If `value` is a JSchain, evaluate it. Otherwise, return value.
        '''
        if isinstance(value, JSchain):
            return value.eval()
        else:
            return value

    def __getattr__(self, attr):
        '''
        Called when using "." operator for the first time. Create a new chain and use it.
        Subsequent "." operators get processed by JSchain.
        '''
        # rasise any pending errors; these errors can get
        # generate on __del__() or other places that Python
        # will ignore.
        if self.state._error:
            e = self.state._error
            self.state._error = None
            raise e

        chain = JSchain(self.state)
        chain._add(attr)
        return chain
 
    def __setattr__(self, attr, value):
        '''
        Called when assiging attributes. This means no JSchain was created, so just process
        it directly.
        '''
        # if the value to be assigned is itself a JSchain, evaluate it
        value = JSroot._v(value)
        # don't process our own attributes
        if attr == "state" or attr == "linkset" or attr == "linkcall":
            super(JSroot, self).__setattr__(attr, value)
            return value
        # create a new JSchain
        c = self.__getattr__(attr)
        if len(c.chain) <= 1:
            c._prepend("window.")
        c.__setattr__(None, value)
        # c._add("=" + json.dumps(value), prepend="")
        return c.eval()

    def __getitem__(self, key):
        # this should never be called
        pass

    def __setitem__(self, key, value):
        value = JSroot._v(value)
        if key in self.linkcall:
            c = self.linkcall[key]
            if isinstance(c, JSchain):
                js = c._dup()
                if isinstance(value, list) or isinstance(value, tuple):
                    js.__call__(*value)
                else:
                    js.__call__(value)
            elif callable(c):
                c(value)
        elif key in self.linkset:
            c = self.linkset[key]
            if isinstance(c, JSchain):
                js = c._dup()
                js._add("=" + json.dumps(value), prepend="")

    def eval(self, stmt):
        '''
        Evaluate a Javascript statement `stmt` in on the Browser.
        '''
        chain = JSchain(self.state)
        chain._add(stmt)
        return chain.eval()

    def __call__(self, item=None, name=None):
        def main(item):
            chain = JSchain(self.state)
            item_name = name or getattr(item, "__name__")
            stmt = f"window.{item_name} = "
            chain._add(stmt)
            [chain._add(x, prepend="") for x in chain._formatArg(item)]
            chain.eval()
            return item
        return main(item) if item else main

    def js(self, code):
        return JsObject(code, self.state)

    def Function(self, code):
        return JsObject("function() {" + code + "}", self.state)

    def val(self, key, callback):
        self.linkset[key] = callback
        callback.keep = False

    def call(self, key, callback):
        self.linkcall[key] = callback
        if isinstance(callback, JSchain):
            callback.keep = False

    def __enter__(self):
        '''
        For use in "with" statements, as in:
            with server.js() as js:
                js.runme()
        '''
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
