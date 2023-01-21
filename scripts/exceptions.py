
class BaseException(Exception):
	def __repr__(self):
		return self.__name__

class ScriptNotFound(BaseException):
	pass