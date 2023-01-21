
class Context:
	__data: dict

	def __init__(self, *args, **kwargs):
		self.__data = dict(*args, **kwargs)

	def as_dict(self):
		return self.__data
	
	def __getattr__(self, *args):
		return self.__data.get(*args)

	# def __setattr__(self, name, value):
	# 	if name.startswith("__"):
	# 		return super().__setattr__(name, value)
	# 	self.__data[name] = value

	def __getitem__(self, *args):
		return self.__data.get(*args)

	def __setitem__(self, name, value):
		self.__data[name] = value
