import inspect
from wsgic.http import request,BaseResponse
from wsgic.plugins import KeywordPlugin

class RequestPlugin(KeywordPlugin):
	name = "request"
	api = 2

	def __init__(self, keyword="request"):
		super().__init__(keyword, request)


class ResponsePlugin(KeywordPlugin):
	name = "response"
	api = 2

	def __init__(self, keyword="response", response_object=BaseResponse):
		super().__init__(keyword, response_object)
