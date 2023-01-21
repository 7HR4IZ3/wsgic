from .bottle import *

class WSGIApp(Bottle):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def get_app(self):
		return self