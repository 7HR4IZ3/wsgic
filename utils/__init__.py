import inspect
from types import FunctionType
from functools import wraps, singledispatch, partial

def as_kwargs(callback, data):
	args = inspect.getfullargspec(callback)[0]

	if isinstance(data, dict):
		kwargs = {
			x: data.get(x) for x in args if data.get(x)
		}
	else:
		kwargs = {
			arg: val for arg, val in zip(args, data[:len(args)+1])
		}
	return kwargs

@singledispatch
def conditional_kwargs(callback, mapping=None):
	@wraps(callback)
	def wrapper(*a, **kw):
		# if isinstance(mapping, dict) or (kw and isinstance(kw, dict)):
		# 	kws = dict(**(mapping or {}), **kw)
		# else:
		# 	kws = set([*(mapping or []), *a])

		kwargs = as_kwargs(callback, dict(**(mapping or {}), **kw))
		return callback(*a, **kwargs)
	return wrapper

@conditional_kwargs.register(dict)
def _(mapping):
	return partial(conditional_kwargs, mapping=mapping)

# @conditional_kwargs.register(list)
# def _(*args):
# 	return partial(conditional_kwargs, args[0])
