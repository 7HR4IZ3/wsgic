from wsgic.backend.bottle import load, TEMPLATE_PATH, request
from threading import Thread
from .interceptors import (
	set_global,
	routes_handler,
	views_handler,
	session_handler,
	render
)

def interceptor(app):
	session_handler(app)
	#Thread(target=views_handler, args=(app,)).start()
	#Thread(target=routes_handler, args=(app,)).start()
	#Thread(target=session_handler).start()
	views_handler(app)
	routes_handler(app)