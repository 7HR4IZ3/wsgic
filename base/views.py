from wsgic.helpers.extra import switch
from wsgic.backend import request

class View:
	def __init__(self, *args, **kwargs):
		pass

class Single(View):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __call__(self, **kw):
		return self.as_view(**kw)

	# Dummy request handlers .... to be overwritten
	def get(self, request):
		pass
	def post(self, request):
		pass
	def delete(self, request):
		pass
	def put(self, request):
		pass

	def as_view(self, **kw):
		data = switch(request.method, _return=True, kwargs=kw)
		# data.case("GET", self.get, args=[request.GET])
		data.case("POST", self.post, args=[request.POST])
		data.case("PUT", self.put, args=[request])
		data.case("DELETE", self.delete, args=[request])
		return data.default(self.get, args=[request.GET[x] for x in request.GET])