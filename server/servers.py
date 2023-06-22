
import os
import threading


class ServerAdapter(object):
    quiet = False

    def __init__(self, host='127.0.0.1', port=8080, **options):
        self.options = options
        self.host = host
        self.port = int(port)

    def run(self, handler):  # pragma: no cover
        pass

    def __repr__(self):
        args = ', '.join('%s=%s' % (k, repr(v))
                         for k, v in self.options.items())
        return "%s(%s)" % (self.__class__.__name__, args)

class CGIServer(ServerAdapter):
    quiet = True

    def run(self, handler):  # pragma: no cover
        from wsgiref.handlers import CGIHandler

        def fixed_environ(environ, start_response):
            environ.setdefault('PATH_INFO', '')
            return handler(environ, start_response)

        CGIHandler().run(fixed_environ)


# class FlupFCGIServer(ServerAdapter):
#     def run(self, handler):  # pragma: no cover
#         import flup.server.fcgi
#         self.options.setdefault('bindAddress', (self.host, self.port))
#         flup.server.fcgi.WSGIServer(handler, **self.options).run()


class WSGIRefServer(ServerAdapter):
    def run(self, app):  # pragma: no cover
        from wsgiref.simple_server import make_server
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
        import socket

        class FixedHandler(WSGIRequestHandler):
            def address_string(self):  # Prevent reverse DNS lookups please.
                return self.client_address[0]

            def log_request(*args, **kw):
                if not self.quiet:
                    return WSGIRequestHandler.log_request(*args, **kw)

        handler_cls = self.options.get('handler_class', FixedHandler)
        server_cls = self.options.get('server_class', WSGIServer)

        if ':' in self.host:  # Fix wsgiref for IPv6 addresses.
            if getattr(server_cls, 'address_family') == socket.AF_INET:

                class server_cls(server_cls):
                    address_family = socket.AF_INET6

        self.srv = make_server(self.host, self.port, app, server_cls,
                               handler_cls)
        # update port actual port (0 means random)
        self.port = self.srv.server_port
        try:
            self.srv.serve_forever()
        except KeyboardInterrupt:
            self.srv.server_close()  # Prevent ResourceWarning: unclosed socket
            raise

# class CherryPyServer(ServerAdapter):
#     def run(self, handler):  # pragma: no cover
#         depr(0, 13, "The wsgi server part of cherrypy was split into a new "
#                     "project called 'cheroot'.", "Use the 'cheroot' server "
#                     "adapter instead of cherrypy.")
#         from cherrypy import wsgiserver  # This will fail for CherryPy >= 9

#         self.options['bind_addr'] = (self.host, self.port)
#         self.options['wsgi_app'] = handler

#         certfile = self.options.get('certfile')
#         if certfile:
#             del self.options['certfile']
#         keyfile = self.options.get('keyfile')
#         if keyfile:
#             del self.options['keyfile']

#         server = wsgiserver.CherryPyWSGIServer(**self.options)
#         if certfile:
#             server.ssl_certificate = certfile
#         if keyfile:
#             server.ssl_private_key = keyfile

#         try:
#             server.start()
#         finally:
#             server.stop()


# class CherootServer(ServerAdapter):
#     def run(self, handler):  # pragma: no cover
#         from cheroot import wsgi
#         from cheroot.ssl import builtin
#         self.options['bind_addr'] = (self.host, self.port)
#         self.options['wsgi_app'] = handler
#         certfile = self.options.pop('certfile', None)
#         keyfile = self.options.pop('keyfile', None)
#         chainfile = self.options.pop('chainfile', None)
#         server = wsgi.Server(**self.options)
#         if certfile and keyfile:
#             server.ssl_adapter = builtin.BuiltinSSLAdapter(
#                 certfile, keyfile, chainfile)
#         try:
#             server.start()
#         finally:
#             server.stop()


# class WaitressServer(ServerAdapter):
#     def run(self, handler):
#         from waitress import serve
#         serve(handler, host=self.host, port=self.port,
#               _quiet=self.quiet, **self.options)


# class PasteServer(ServerAdapter):
#     def run(self, handler):  # pragma: no cover
#         from paste import httpserver
#         from paste.translogger import TransLogger
#         handler = TransLogger(handler, setup_console_handler=(not self.quiet))
#         httpserver.serve(handler,
#                          host=self.host,
#                          port=str(self.port), **self.options)


# class MeinheldServer(ServerAdapter):
#     def run(self, handler):
#         from meinheld import server
#         server.listen((self.host, self.port))
#         server.run(handler)


# class FapwsServer(ServerAdapter):
#     """ Extremely fast webserver using libev. See http://www.fapws.org/ """

#     def run(self, handler):  # pragma: no cover
#         depr(0, 13, "fapws3 is not maintained and support will be dropped.")
#         import fapws._evwsgi as evwsgi
#         from fapws import base, config
#         port = self.port
#         if float(config.SERVER_IDENT[-2:]) > 0.4:
#             # fapws3 silently changed its API in 0.5
#             port = str(port)
#         evwsgi.start(self.host, port)
#         # fapws3 never releases the GIL. Complain upstream. I tried. No luck.
#         if 'BOTTLE_CHILD' in os.environ and not self.quiet:
#             _stderr("WARNING: Auto-reloading does not work with Fapws3.")
#             _stderr("         (Fapws3 breaks python thread support)")
#         evwsgi.set_base_module(base)

#         def app(environ, start_response):
#             environ['wsgi.multiprocess'] = False
#             return handler(environ, start_response)

#         evwsgi.wsgi_cb(('', app))
#         evwsgi.run()


class TornadoServer(ServerAdapter):
    """ The super hyped asynchronous server by facebook. Untested. """

    def run(self, handler):  # pragma: no cover
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop
        container = tornado.wsgi.WSGIContainer(handler)
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port=self.port, address=self.host)
        tornado.ioloop.IOLoop.instance().start()


# class AppEngineServer(ServerAdapter):
#     """ Adapter for Google App Engine. """
#     quiet = True

#     def run(self, handler):
#         depr(0, 13, "AppEngineServer no longer required",
#              "Configure your application directly in your app.yaml")
#         from google.appengine.ext.webapp import util
#         # A main() function in the handler script enables 'App Caching'.
#         # Lets makes sure it is there. This _really_ improves performance.
#         module = sys.modules.get('__main__')
#         if module and not hasattr(module, 'main'):
#             module.main = lambda: util.run_wsgi_app(handler)
#         util.run_wsgi_app(handler)


# class TwistedServer(ServerAdapter):
#     """ Untested. """

#     def run(self, handler):
#         from twisted.web import server, wsgi
#         from twisted.python.threadpool import ThreadPool
#         from twisted.internet import reactor
#         thread_pool = ThreadPool()
#         thread_pool.start()
#         reactor.addSystemEventTrigger('after', 'shutdown', thread_pool.stop)
#         factory = server.Site(wsgi.WSGIResource(reactor, thread_pool, handler))
#         reactor.listenTCP(self.port, factory, interface=self.host)
#         if not reactor.running:
#             reactor.run()


# class DieselServer(ServerAdapter):
#     """ Untested. """

#     def run(self, handler):
#         depr(0, 13, "Diesel is not tested or supported and will be removed.")
#         from diesel.protocols.wsgi import WSGIApplication
#         app = WSGIApplication(handler, port=self.port)
#         app.run()


class GeventServer(ServerAdapter):
    """ Untested. Options:

        * See gevent.wsgi.WSGIServer() documentation for more options.
    """

    def run(self, handler):
        from gevent import pywsgi, local
        if not isinstance(threading.local(), local.local):
            msg = "Bottle requires gevent.monkey.patch_all() (before import)"
            raise RuntimeError(msg)
        if self.quiet:
            self.options['log'] = None
        address = (self.host, self.port)
        server = pywsgi.WSGIServer(address, handler, **self.options)
        if 'BOTTLE_CHILD' in os.environ:
            import signal
            signal.signal(signal.SIGINT, lambda s, f: server.stop())
        server.serve_forever()


class GunicornServer(ServerAdapter):
    """ Untested. See http://gunicorn.org/configure.html for options. """

    def run(self, handler):
        from gunicorn.app.base import BaseApplication

        if self.host.startswith("unix:"):
            config = {'bind': self.host}
        else:
            config = {'bind': "%s:%d" % (self.host, self.port)}

        config.update(self.options)

        class GunicornApplication(BaseApplication):
            def load_config(self):
                for key, value in config.items():
                    self.cfg.set(key, value)

            def load(self):
                return handler

        GunicornApplication().run()


class GeventWebSocketServer(ServerAdapter):
    """ Untested. Options:

        * See gevent.wsgi.WSGIServer() documentation for more options.
    """

    def run(self, handler):
        import logging
        from gevent import pywsgi, local
        from geventwebsocket.handler import WebSocketHandler
        from geventwebsocket.logging import create_logger

        from gevent.monkey import patch_all; patch_all()

        if not isinstance(threading.local(), local.local):
            msg = "Bottle requires gevent.monkey.patch_all() (before import)"
            raise RuntimeError(msg)
        if self.quiet:
            self.options['log'] = None
        address = (self.host, self.port)
        server = pywsgi.WSGIServer(address, handler, handler_class=WebSocketHandler, **self.options)
        if 'BOTTLE_CHILD' in os.environ:
            import signal
            signal.signal(signal.SIGINT, lambda s, f: server.stop())
        if not self.quiet:
            server.logger = create_logger('geventwebsocket.logging')
            server.logger.setLevel(logging.INFO)
            server.logger.addHandler(logging.StreamHandler())
        server.serve_forever()

# class EventletServer(ServerAdapter):
#     """ Untested. Options:

#         * `backlog` adjust the eventlet backlog parameter which is the maximum
#           number of queued connections. Should be at least 1; the maximum
#           value is system-dependent.
#         * `family`: (default is 2) socket family, optional. See socket
#           documentation for available families.
#     """

#     def run(self, handler):
#         from eventlet import wsgi, listen, patcher
#         if not patcher.is_monkey_patched(os):
#             msg = "Bottle requires eventlet.monkey_patch() (before import)"
#             raise RuntimeError(msg)
#         socket_args = {}
#         for arg in ('backlog', 'family'):
#             try:
#                 socket_args[arg] = self.options.pop(arg)
#             except KeyError:
#                 pass
#         address = (self.host, self.port)
#         try:
#             wsgi.server(listen(address, **socket_args), handler,
#                         log_output=(not self.quiet))
#         except TypeError:
#             # Fallback, if we have old version of eventlet
#             wsgi.server(listen(address), handler)


# class BjoernServer(ServerAdapter):
#     """ Fast server written in C: https://github.com/jonashaag/bjoern """

#     def run(self, handler):
#         from bjoern import run
#         run(handler, self.host, self.port, reuse_port=True)


# class AsyncioServerAdapter(ServerAdapter):
#     """ Extend ServerAdapter for adding custom event loop """

#     def get_event_loop(self):
#         pass


# class AiohttpServer(AsyncioServerAdapter):
#     """ Asynchronous HTTP client/server framework for asyncio
#         https://pypi.python.org/pypi/aiohttp/
#         https://pypi.org/project/aiohttp-wsgi/
#     """

#     def get_event_loop(self):
#         import asyncio
#         return asyncio.new_event_loop()

#     def run(self, handler):
#         import asyncio
#         from aiohttp_wsgi.wsgi import serve
#         self.loop = self.get_event_loop()
#         asyncio.set_event_loop(self.loop)

#         if 'BOTTLE_CHILD' in os.environ:
#             import signal
#             signal.signal(signal.SIGINT, lambda s, f: self.loop.stop())

#         serve(handler, host=self.host, port=self.port)


# class AiohttpUVLoopServer(AiohttpServer):
#     """uvloop
#        https://github.com/MagicStack/uvloop
#     """

#     def get_event_loop(self):
#         import uvloop
#         return uvloop.new_event_loop()


# class AutoServer(ServerAdapter):
#     """ Untested. """
#     adapters = [WaitressServer, PasteServer, TwistedServer, CherryPyServer,
#                 CherootServer, WSGIRefServer]

#     def run(self, handler):
#         for sa in self.adapters:
#             try:
#                 return sa(self.host, self.port, **self.options).run(handler)
#             except ImportError:
#                 pass

server_names = {
    'cgi': CGIServer,
    'wsgiref': WSGIRefServer,
    'tornado': TornadoServer,
    'gunicorn': GunicornServer,
    'geventws': GeventWebSocketServer,
    'gevent': GeventServer,
    # 'flup': FlupFCGIServer,
    # 'waitress': WaitressServer,
    # 'cherrypy': CherryPyServer,
    # 'cheroot': CherootServer,
    # 'paste': PasteServer,
    # 'fapws3': FapwsServer,
    # 'gae': AppEngineServer,
    # 'twisted': TwistedServer,
    # 'diesel': DieselServer,
    # 'meinheld': MeinheldServer,
    # 'eventlet': EventletServer,
    # 'bjoern': BjoernServer,
    # 'aiohttp': AiohttpServer,
    # 'uvloop': AiohttpUVLoopServer,
    # 'auto': AutoServer,
}
