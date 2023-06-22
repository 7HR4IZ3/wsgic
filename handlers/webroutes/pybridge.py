import os
import sys
import json
import queue
import asyncio
import builtins
import traceback
from types import NoneType
from random import randint
from functools import wraps
from threading import Thread, RLock
from inspect import getfullargspec
from multiprocessing import Process

UNDEFINED = object()
DEBUG = False

def run_safe(func, *args, **kwargs):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return loop.call_soon(func, *args, **kwargs)


def task(func, handler=Thread, *ta, **tkw):
    @wraps(func)
    def wrapper(*a, **kw):
        thread = handler(*ta, target=func, args=a, kwargs=kw, **tkw)
        thread.start()
        return thread
    return wrapper


def daemon_task(func):
    return task(func, handler=Thread, daemon=True)


def process(func):
    return task(func, handler=Process)


class JsClass:
    def __serialize_bridge__(self, server):
        return self.__dict__

def has_argument(func, arg):
    try:
        args = getfullargspec(func)
        return arg in args.args
    except:
        return False

def get_encoder(server):
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, BridgeProxy):
                return {
                    'type': 'bridge_proxy',
                    'location': obj.__data__['location'],
                    'reverse': True
                }
            # if isinstance(obj, tuple):
            #     return server.generate_proxy(obj)

            if isinstance(obj, JsClass):
                obj = obj.__dict__
                return json.dumps(obj, cls=JSONEncoder)

            try:
                if issubclass(obj, JsClass):
                    obj = obj.__dict__
                    print("JsClass", obj)
                    return json.dumps(obj, cls=JSONEncoder)
            except:
                pass

            if hasattr(obj, "__serialize_bridge__"):
                obj = obj.__serialize_bridge__(server)

            try:
                return super().default(obj)
            except:
                return server.generate_proxy(obj)
    return JSONEncoder


def get_decoder(server):
    class JSONDecoder(json.JSONDecoder):
        def __init__(self, *a, **kw):
            super().__init__(object_hook=self.object_hook, *a, **kw)

        def object_hook(self, item: dict):
            for key, val in item.items():
                if isinstance(val, list):
                    vall = [
                        self.object_hook(x) if isinstance(x, dict) else x
                        for x in val
                    ]
                    item[key] = vall

            # if item.get("type") == "bridge_proxy" and item.get("location"):
            #     return server.proxy(server, item)
            return server.get_result(item)
    return JSONDecoder


def makeProxyClass(target):
    class JsClass(object):
        def __init__(self, *a, **kw):
            self.__object = self.proxy.new(*a, **kw)

        def __getattr__(self, name):
            return self.__object.__getattr__(name)

        def __call__(self, *a, **kw):
            return self.__object.__call__(*a, **kw)


def load_module(target, e=None, catch_errors=True, **namespace):
    try:
        if ':' in target:
            module, target = target.split(":", 1)
        else:
            module, target = (target, None)
        if module not in sys.modules:
            __import__(module)
        if not target:
            return sys.modules[module]
        if target.isalnum():
            return getattr(sys.modules[module], target)
        package_name = module.split('.')[0]
        namespace[package_name] = sys.modules[package_name]
        return eval('%s.%s' % (module, target), namespace)
    except Exception as err:
        if catch_errors:
            return e
        raise err


def generate_random_id(size=20):
    return "".join([str(randint(0, 9)) for i in range(size)])

class ThreadSafeQueue(queue.Queue):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.get_lock = RLock()
        self.put_lock = RLock()

    def get(self, *a, **kw):
        with self.get_lock:
            return super().get(*a, **kw)

    def put(self, *a, **kw):
        with self.put_lock:
            return super().put(*a, **kw)

class BridgeProxy:
    def __init__(self, server, data):
        self.__server__ = server
        self.__data__ = data

    @property
    def _(self):
        return self.__cast__()

    def __cast__(self, target=(lambda a: a)):
        return target(self.__server__.__recieve__(
            action="get_primitive",
            location=self.__data__['location']
        ))

    def __dir__(self):
        return self.__server__.__recieve__(
            action="get_proxy_attributes",
            location=self.__data__['location']
        )

    def __call__(self, *args, **kwargs):
        return self.__server__.__recieve__(
            action="call_proxy",
            location=self.__data__['location'],
            args=args,
            kwargs=kwargs
        )

    def __getattr__(self, name):
        if name == "new": return self.__new_constructor
        return self.__server__.__recieve__(
            action="get_proxy_attribute",
            location=self.__data__['location'],
            target=name
        )

    def __getitem__(self, index):
        return self.__server__.__recieve__(
            action="get_proxy_index",
            location=self.__data__['location'],
            target=index
        )

    def __setattr__(self, name, value):
        if name in ['__server__', '__data__']:
            return super().__setattr__(name, value)
        return self.__server__.__recieve__(
            action="set_proxy_attribute",
            location=self.__data__['location'],
            target=name,
            value=value
        )

    def __setitem__(self, index, value):
        return self.__server__.__recieve__(
            action="set_proxy_index",
            location=self.__data__['location'],
            target=index,
            value=value
        )

    def __str__(self):
        return self.__cast__(str)

    def __repr__(self):
        return object.__repr__(self)
    
    def __await__(self):
        yield
        return self.__server__.recieve(
            action="await",
            location=self.__data__['location']
        )

    # def __bool__(self):
    #     return self.__cast__(bool)

    # def __int__(self):
    #     return self.__cast__(int)

    # def __del__(self):
    #     try:
    #         return self.__server__.__recieve__(
    #             action="delete_proxy",
    #             location=self.__data__['location']
    #         )
    #     except Exception:
    #         pass

    # def __len__(self):
    #     length = self.length
    #     if length is not None:
    #         return length.__cast__()
    #     return 0

    def __new_constructor(self, *args, **kwargs):
        return self.__server__.__recieve__(
            action="call_proxy_constructor",
            location=self.__data__['location'],
            args=args,
            kwargs=kwargs
        )


class BridgeConnection:

    def __init__(self, bridge=None, transporter=None, mode="auto_eval", server=None):
        self.__transporter = transporter
        self.__bridge = bridge
        self.__mode = mode
        self.__require = None
        self.__server__ = server

    def __getattr__(self, name):
        if name == "let" or name == "var":
            return self.__handle_let
        if name == "await_":
            return self.__handle_await
        return self.__recieve__(action="evaluate", value=name)

    def __quit(self):
        self.__server__.stop()

    def __del__(self):
        self.__quit()

    def __enter__(self, *a, **kw):
        return self

    def __exit__(self, *a, **kw):
        self.__quit()
    
    def __recieve__(self, **kw):
        return self.__server__.recieve(**kw)

    def __handle_let(self, *keys, **values):
        target = []

        for key in key: target.append(f"{key}")

        if values:
            for key in values:
                target.append(f"globalThis.{key} = {values[key]}")

        self.__getattr__(
            name=f"{', '.join(target)};"
        )

    def __handle_await(self, item):
        return self.__recieve__(
            action="await_proxy",
            location=item.__data__['location']
        )

    def require(self, module):
        if not self.__require:
            self.__require = self.__recieve__(
                action="evaluate", value='require'
            )
        return self.__require(
            os.path.join(os.getcwd(), module) if "." in module
            else module
        )


    def get_result(self, data):
        func = self.__server__.formatters.get(data.get("obj_type"))

        if isinstance(data, dict):
            is_proxy = data.get("type") == "bridge_proxy"
            if func:
                return func(data)
            if is_proxy and data.get("location", UNDEFINED) != UNDEFINED:
                if data.get("reverse"):
                    return self.__server__.handle_get_stack_attribute(data)
                return self.__server__.proxy(self, data)
        return data

class MultiBridgeConnection(BridgeConnection):
    def __init__(self, conn_id=None, socket=None, *a, **kw):
        super().__init__(*a, **kw)
        self.__conn_id__ = conn_id
        self.__socket__  = socket
        self.__queue__ = ThreadSafeQueue()
        self.__context__ = dict()

    def __send__(self, **kw):
        data = self.__server__.encode(kw)
        self.__socket__.send(data)
        if DEBUG: print("[PY] Sent:", data)
        return None
    
    def __recieve__(self, **kw):
        kw["conn_id"] = self.__conn_id__
        return super().__recieve__(**kw)

    def __call__(self, name=None, func=None):
        if not isinstance(name, str) or callable(name):
            func, name = name, None

        def wrapper(func):
            nam = name or getattr(func, "__name__", f"anonyfunc_{generate_random_id(5)}")
            setattr(self.window, nam, func)
        return wrapper(func) if func else wrapper
    
    def __enter__(self, *a, **kw):
        return self
    
    def __exit__(self, *a, **kw):
        return self.__socket__.close()

class BridgeTransporter:
    listening = True

    def setup(self):
        return

    def get_setup_args(self, args, **kwargs):
        return args

    def start(self, on_message, server):
        self.on_message = on_message
        self.server = server
        self.setup()

    def start_client(self):
        pass

    def encode(self, data, raw=False):
        return (
            json.dumps(data) if raw
            else json.dumps(data, cls=self.server.encoder)
        )

    def decode(self, data, raw=False):
        return (
            json.loads(data) if raw
            else json.loads(data, cls=self.server.decoder)
        )

    def send(self, data):
        pass

    def stop(self):
        pass

class BaseHandler:
    proxy = BridgeProxy
    connection = BridgeConnection

    default_transporter = BridgeTransporter

    def __init__(self):
        self.proxies = dict()

        self.queue = ThreadSafeQueue()
        self.timeout = 5

        self.message_handlers = dict()
        self.context = {}

        self.encoder = get_encoder(self)
        self.decoder = get_decoder(self)

        self.formatters = {
            "number": lambda x: int(x['value']),
            "float": lambda x: float(x['value']),
            "string": lambda x: str(x['value']),
            "array": lambda x: list(x['value']),
            "Buffer": lambda x: bytes(x['data']),
            "object": lambda x: dict(x),
            "set": lambda x: set(x['value']),
            "boolean": lambda x: bool(x['value']),
            "callable_proxy": self.callable_proxy,
            "function": self.callable_proxy,
            # "bridge_proxy": lambda x: self.getProxyObject(x['value'])
        }

    def random_id(self, size=20):
        return generate_random_id(size)

    def proxy_object(self, arg):
        for k, v in self.proxies.items():
            try:
                if v == arg:
                    return k
            except Exception:
                continue

        key = generate_random_id(15) + str(id(arg))
        self.proxies[key] = arg
        return key

    def generate_proxy(self, arg):
        key = self.proxy_object(arg)

        t = str(type(arg).__name__)
        if t in ["function", "method", "lambda"]:
            t = "callable_proxy"

        return {
            "type": "bridge_proxy",
            "obj_type": t,
            "location": key
        }

    def get_proxy(self, key):
        return self.proxies.get(key)

    def callable_proxy(self, target):
        def wrapper(*args, **kwargs):
            return self.recieve(
                action="call_proxy",
                location=target['location'],
                args=args,
                kwargs=kwargs
            )
        return wrapper

    def send(self, raw=False, **data):
        self.transporter.send(data, raw)

    def recieve(self, **data):
        mid = generate_random_id()
        data["message_id"] = mid

        def handler(message):
            self.message_handlers.pop(mid, None)
            try:
                if isinstance(message, dict):
                    if message.get("response", UNDEFINED) != UNDEFINED:
                        message = message['response']
                    elif message.get("value", UNDEFINED) != UNDEFINED:
                        message = message['value']

                self.queue.put(message)
            except Exception:
                self.queue.put(message)

        self.message_handlers[mid] = handler
        self.send(**data)

        response = self.queue.get(timeout=self.timeout)
        self.queue.task_done()
        if isinstance(response, Exception):
            raise response
        return response

    __recieve__ = recieve

    def process_command(self, req, handler=None):
        func = getattr(self, "handle_" + req['action'])

        if (not func):
            raise Exception("Invalid action.")
        
        try:
            ret = func(req, handler)
            return {"response": ret}
        except Exception as e:
            return { "error": "\n".join(traceback.format_exception(e)) }


    def handle_attribute(self, req, handler):
        target = getattr(self.obj, req["item"], UNDEFINED)
        handle = None
        if not (target is UNDEFINED):
            t = str(type(target).__name__)
            if isinstance(target, BridgeProxy):
                target = target.__data__["location"]
                t = "bridge_proxy"
            elif not isinstance(
                target,
                (int, str, dict, set, tuple, bool, float, NoneType)
            ):
                handle = self.proxy_object(target)
                target = None

            if t in ["function", "method"]:
                t = "callable_proxy"
            try:
                return {"type": t, "value": target, "location": handle}
            except Exception:
                return {"type": t, "value": str(target), "location": handle}
        return {"type": None, "value": None, "error": True}

    def handle_evaluate(self, req, handler):
        target = getattr(builtins, req["value"], UNDEFINED)
        return target

    def handle_evaluate_stack_attribute(self, req, handler):
        stack = req["stack"]
        ret = handler.__context__.get(stack[0]) or getattr(builtins, stack[0], None)
        for item in stack[1:]:
            ret = getattr(ret, item)
        return ret

    def handle_get_stack_attribute(self, req, handler):
        stack = req.get("stack") or []
        ret = self.get_proxy(req["location"])
        for item in stack:
            ret = getattr(ret, item)
        return ret

    def handle_get_stack_attributes(self, req, handler):
        stack = req.get("stack") or []
        ret = self.get_proxy(req["location"])
        for item in stack:
            ret = getattr(ret, item)
        return dir(ret)

    def handle_set_stack_attribute(self, req, handler):
        stack = req["stack"]
        ret = self.get_proxy(req["location"])
        for item in stack[:-1]:
            ret = getattr(ret, item)
        setattr(ret, stack[-1], req["value"])
        return True

    def handle_call_stack_attribute(self, req, handler):
        stack = req["stack"]
        isolate = req.get("isolate", False)

        if req.get('location'):
            ret = self.get_proxy(req["location"])
        else:
            ret = handler.__context__.get(stack[0]) or getattr(builtins, stack[0], None)
            stack = stack[1:]
        for item in stack:
            ret = getattr(ret, item)

        args = req.get("args") or []
        kwargs = req.get("kwargs") or {}

        if not has_argument(ret, "this"):
            kwargs.pop("this", None)

        if not isolate:
            return ret(*args, **kwargs)
        else:
            t = Thread(
                target=ret,
                args=args,
                kwargs=kwargs,
                daemon=True
            )
            t.start()
            return True

    def __format_kwargs(self, data):
        ret = {}
        for key, item in data.items():
            if isinstance(item, dict) and ("location" in item):
                ret[key] = self.get_proxy(item["location"])
            else:
                ret[key] = item
        return ret

    def handle_execute(self, req, handler):
        return exec(
            req["code"], globals(),
            self.__format_kwargs(req["locals"])
        )

    def handle_evaluate_code(self, req, handler):
        return eval(
            req["code"], globals(),
            self.__format_kwargs(req["locals"])
        )

    # def handle_import(self, req, handler):
    #     target = req["item"]

    #     module = target.split(":")[0] if ":" in target else target

    #     handle = None
    #     if target and (
    #         (
    #           self.allowed_imports is not None and
    #           module in self.allowed_imports) or
    #           (module not in self.disallowed_imports)
    #     ):
    #         try:
    #             target = load_module(target)
    #         except Exception as e:
    #             return {
    #                 "type": None,
    #                 "value": None,
    #                 "error": str(e).replace('"', "'")
    #             }
    #         t = str(type(target).__name__)
    #         if isinstance(target, BridgeProxy):
    #             target = target.__data__["location"]
    #             t = "bridge_proxy"
    #         elif not isinstance(
    #             target,
    #             (int, str, dict, set, tuple, bool, float, NoneType)
    #         ):
    #             handle = self.proxy_object(target)
    #             target = None

    #         if t in ["function", "method"]:
    #             t = "callable_proxy"
    #         try:
    #             return {"type": t, "value": target, "location": handle}
    #         except Exception:
    #             return {"type": t, "value": str(target), "location": handle}
    #     return {"type": None, "value": None, "error": True}

    # def handle_builtin(self, req, handler):
    #     target = req["item"]
    #     handle = None
    #     if target and (
    #         (
    #           self.allowed_builtins is not None and
    #           target in self.allowed_builtins) or
    #           (target not in self.disallowed_builtins)
    #     ):
    #         target = load_module(f"builtins:{target}")
    #         t = str(type(target).__name__)
    #         if isinstance(target, BridgeProxy):
    #             target = target.__data__["location"]
    #             t = "bridge_proxy"
    #         elif not isinstance(
    #             target,
    #             (int, str, dict, set, tuple, bool, float, NoneType)
    #         ):
    #             handle = self.proxy_object(target)
    #             target = None

    #         if t in ["function", "method", "builtin_function_or_method"]:
    #             t = "callable_proxy"
    #         try:
    #             return {"type": t, "value": target, "location": handle}
    #         except Exception:
    #             return {"type": t, "value": str(target), "location": handle}
    #     return {"type": None, "value": None, "error": True}

    def handle_get_proxy_attributes(self, req, handler):
        target_attr = req.get("location", None)
        target = self.get_proxy(target_attr)
        if target:
            return dir(target)
        return False

    def handle_get_proxy_attribute(self, req, handler):
        target_attr = req.get("location", None)
        target = self.get_proxy(target_attr)
        return getattr(target, req["target"])

    def handle_set_proxy_attribute(self, req, handler):
        target_attr = req.get("location", None)
        target = self.get_proxy(target_attr)
        if target:
            try:
                setattr(target, req["target"], req["value"])
                return True
            except Exception as e:
                return {
                    "type": None,
                    "value": None,
                    "error": str(e).replace('"', "'")
                }
        return False

    def handle_delete_proxy_attribute(self, req, handler):
        target_attr = req.get("location", None)
        target = self.get_proxy(target_attr)
        if target:
            try:
                value = delattr(target, req["target"])
                return value
            except Exception as e:
                return {
                    "type": None,
                    "value": None,
                    "error": str(e).replace('"', "'")
                }
        return False

    def handle_has_proxy_attribute(self, req, handler):
        target_attr = req.get("location", None)
        target = self.get_proxy(target_attr)
        if target:
            try:
                value = hasattr(target, req["target"])
                return value
            except Exception as e:
                return {
                    "type": None,
                    "value": None,
                    "error": str(e).replace('"', "'")
                }
        return False

    def handle_call_proxy(self, req, handler):
        target_attr = req.get("location", None)
        target = self.get_proxy(target_attr)
        if target:
            return target(
                *req.get("args", []),
                **req.get("kwargs", {})
            )

    def handle_delete_proxy(self, req, handler):
        target_attr = req.get("location", None)
        if target_attr:
            try:
                self.proxies.pop(target_attr, False)
                return True
            except Exception as e:
                return {
                    "type": None,
                    "value": None,
                    "error": str(e).replace('"', "'")
                }
        return False

    def get_result(self, data):
        func = self.formatters.get(data.get("obj_type"))

        if isinstance(data, dict):
            is_proxy = data.get("type") == "bridge_proxy"
            if func:
                return func(data)
            if is_proxy and data.get("location", UNDEFINED) != UNDEFINED:
                if data.get("reverse"):
                    return self.handle_get_stack_attribute(data)
                return self.proxy(self, data)
        return data


class BridgeServer(BaseHandler):
    def __init__(self, transporter=None, keep_alive=False, timeout=None):
        self.transporter = transporter
        if not self.transporter:
            self.transporter = self.default_transporter()

        self.timeout = timeout
        self.__keep_alive = keep_alive

        super().__init__()
        self.formatters = {
            # "number": lambda x: int(x['value']),
            # "float": lambda x: float(x['value']),
            # "string": lambda x: str(x['value']),
            # "array": lambda x: list(x['value']),
            # "Buffer": lambda x: bytes(x['data']),
            # "object": lambda x: dict(x),
            # "set": lambda x: set(x['value']),
            # "boolean": lambda x: bool(x['value']),
            # "callable_proxy": self.callable_proxy,
            # "function": self.callable_proxy,
            # "bridge_proxy": lambda x: self.getProxyObject(x['value'])
        }

    def setup(self, *a, name=None, **k):
        conn = self.start(*a, **k)
        return conn

    def start(self, bridge=None, mode="auto_eval"):
        self.bridge = bridge
        self.conn = self.create_connection(mode=mode)
        self.transporter.start(
            on_message=self.on_message,
            server=self
        )
        return self.conn

    def create_connection(self, mode):
        return self.connection(
            transporter=self.transporter,
            bridge=self.bridge, mode=mode,
            server=self
        )

    def on_message(self, message):
        if isinstance(message, dict):
            if 'action' in message:
                response = self.process_command(message)
                response['message_id'] = message['message_id']
                return self.send(**response)
            elif message.get('error'):
                return self.queue.put_nowait(
                    Exception(message['error'])
                )
            else:
                handler = self.message_handlers.get(message.get("message_id"))

                if handler:
                    return handler(message)
                else:
                    if message.get("response", UNDEFINED) != UNDEFINED:
                        message = message['response']
                    elif message.get("value", UNDEFINED) != UNDEFINED:
                        message = message['value']
                    return self.queue.put_nowait(message)
        return self.queue.put_nowait(message)

    def encode(self, data, raw=False):
        return (
            json.dumps(data) if raw
            else json.dumps(data, cls=self.encoder)
        )

    def decode(self, data, handler=None, raw=False):
        return (
            json.loads(data) if raw
            else json.loads(data, cls=(self.decoder if not handler else get_decoder(handler)))
        )

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.stop()

    def __keep_alive__(self):
        self.__keep_alive = True

    def stop(self, force=False):
        if not force and self.__keep_alive:
            return
        self.transporter.stop()
        # self.bridge.close()

    def __del__(self):
        self.stop()

class MultiServer(BridgeServer):
    connection = MultiBridgeConnection
    handlers: dict[str, connection]

    def __init__(self, transporter=None, keep_alive=False, timeout=None):
        super().__init__(transporter, keep_alive, timeout)
        self.handlers = {}
        self.conn_queues = ThreadSafeQueue()
 
    def handle_connection(self, socket, conn_id):
        handler = self.create_connection(conn_id=conn_id, socket=socket)
        self.handlers[conn_id] = handler
        self.conn_queues.put(conn_id)

        @daemon_task
        def _(message):
            self.on_message(self.decode(message, handler))

        while not socket.closed:
            msg = socket.receive()
            if DEBUG: print("[PY] Recieved: ", msg)
            if msg: _(msg)

        self.handlers.pop(conn_id)
        del handler
        return []

    def create_connection(self, mode=None, conn_id=None, socket=None):
        return self.connection(
            socket=socket,
            server=self, conn_id=conn_id
        )

    def get_connection(self, conn_id):
        while True:
            try:
                item_id = self.conn_queues.get(timeout=60)
                if item_id == conn_id:
                    self.conn_queues.task_done()
                    return self.handlers[conn_id]
            except queue.Empty:
                break

        raise Exception("No connection was made.")

    def send(self, conn_id=None, **kw):
        handler = self.handlers.get(conn_id)
        if handler: return handler.__send__(**kw)

    def recieve(self, conn_id=None, **data):
        mid = generate_random_id()
        data["message_id"] = mid

        handler = self.handlers[conn_id]
        queue  = handler.__queue__

        def handler(message):
            self.message_handlers.pop(mid, None)
            try:
                if isinstance(message, dict):
                    if message.get("response", UNDEFINED) != UNDEFINED:
                        message = message['response']
                    elif message.get("value", UNDEFINED) != UNDEFINED:
                        message = message['value']

                queue.put(message)
            except Exception:
                queue.put(message)

        self.message_handlers[mid] = handler

        data["conn_id"] = conn_id
        self.send(**data)

        response = queue.get(timeout=self.timeout)
        queue.task_done()
        if isinstance(response, Exception):
            raise response

        return response

    def on_message(self, message):
        if isinstance(message, dict):
            handler = self.handlers.get(message.get("conn_id"))

            if not handler:
                return

            queue = handler.__queue__

            if 'action' in message:
                response = self.process_command(message, handler)
                response['message_id'] = message['message_id']
                response["conn_id"] = message.get("conn_id")
                return self.send(**response)
            elif message.get('error'):
                return queue.put_nowait(
                    Exception(message['error'])
                )
            else:
                handler = self.message_handlers.get(message.get("message_id"))

                if handler:
                    return handler(message)
                else:
                    if message.get("response", UNDEFINED) != UNDEFINED:
                        message = message['response']
                    elif message.get("value", UNDEFINED) != UNDEFINED:
                        message = message['value']
                    return queue.put_nowait(message)
        return queue.put_nowait(message)
