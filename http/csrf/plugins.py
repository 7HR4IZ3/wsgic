from wsgic.plugins import RequestPlugin
from wsgic.http import abort

from . import csrf, request

class CSRFPlugin(RequestPlugin):
	def before(self):
		if request.method == request.methods.POST:
			csrftoken = request.POST.get("__csrf_token")
			if not csrf.check(csrftoken):
				raise abort(400, "Invalid CSRF Token.")
