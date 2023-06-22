import functools
from wsgic.http import redirect, request, BaseResponse

def check(validate, fail=None, error="", back=None):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*a, **kw):
            path = request.path
            if validate(request) is True:
                return func(*a, **kw)
            else:
                if callable(fail):
                    return fail()
                elif isinstance(fail, str):
                    return redirect().route(fail).error(error).with_next(path if back else None)
                elif isinstance(fail, BaseResponse):
                    return fail.with_next(path if back else None)
                else:
                    return redirect('/').error(error).with_next(path if back else None)
        return wrapped
    return wrapper
