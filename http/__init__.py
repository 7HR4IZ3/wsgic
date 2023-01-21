import json
from html import escape
from xml.dom.minidom import parseString
from wsgic.thirdparty.bottle import DictProperty, LocalRequest, BaseRequest, LocalResponse, BaseResponse, request as req, response as res, SimpleCookie, urljoin, HTTPError as httperror, HTTPResponse, static_file as FileResponse, HTTP_CODES, FormsDict
from wsgic.thirdparty.dicttoxml import dicttoxml
from wsgic.routing import route
from wsgic.helpers import hooks, messages, errors

def get_session():
    from wsgic.session import sessions
    return sessions

class Methods:
    GET = "GET"
    POST = 'POST'
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    CLI = "CLI"
    
    GP = [GET, POST]
    API = [GET, PUT, POST, DELETE]
    ALL = [GET, PUT, POST, DELETE, CLI, HEAD]
    
    def __getattr__(self, name):
        if hasattr(self, name.upper()):
            return getattr(self, name.upper())

class Request(LocalRequest):
    @property
    def previous_url(self):
        sessions = get_session()
        referer = self.referrer or sessions.session['__wsgic_vars'].get('__previous_url', '/')
        return referer
    
    @property
    def oldinputs(self):
        sessions = get_session()
        inputs = sessions.session["__wsgic_vars"].get("__old_inputs", {})
        return inputs
    
    @property
    def var(self):
        return FormsDict(**self.GET, **self.POST)
    
    @property
    def referrer(self):
        return self.get('HTTP_REFERER') or self.GET.get('ref')
    
    @property
    def path(self):
        """ The value of ``PATH_INFO`` with exactly one prefixed slash (to fix broken clients and avoid the "empty path" edge case). """
        if self.app.mountpoint:
            mount = self.app.mountpoint + "/"
        else:
            mount = ""
        return '/' + mount.lstrip("/") + self.environ.get('PATH_INFO', '').lstrip('/')
    
    @DictProperty('environ', 'wsgi.url_scheme', read_only=True)
    def scheme(self):
        raise RuntimeError('This request has no url scheme.')
    
    @property
    def mountpoint(self):
        return self.app.mountpoint
    
    @property
    def is_popup(self):
        return self.GET.get("popup") == "true"

    @property
    def methods(self):
        return methods
    
    @property
    def next(self):
        return self.GET.get('next', None)

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return None
    
    def __setattr__(self, name, value):
        if name == 'environ': return object.__setattr__(self, name, value)
        key = 'bottle.request.ext.%s' % name
        # if key in self.environ:
        #     raise AttributeError("Attribute already defined: %s" % name)
        self.environ[key] = value

class Response(LocalResponse):
    def __init__(self, body='', status=None, headers=None, **more_headers):
        hooks.attach("after_request", self._)
        super().__init__(body, status, headers, **more_headers)
    
    def _(self):
        res.status = self.status
        res._headers = dict((k, v[:]) for (k, v) in self._headers.items())
        if self._cookies:
            cookies = res._cookies = SimpleCookie()
            for k,v in self._cookies.items():
                cookies[k] = v.value
                cookies[k].update(v) # also copy cookie attributes
        return res
    
    def __del__(self):
        hooks.detach("after_request", self._)

response = Response()
request = Request()

class redirect(LocalResponse):
    def __init__(self, url='/', code=None):
        """ Aborts execution and causes a 303 or 302 redirect, depending on
            the HTTP protocol version. """
        if not code:
            code = 303 if request.get('SERVER_PROTOCOL') == "HTTP/1.1" else 302
        super().__init__("", code)
        self.set_header('Location', urljoin(request.url, url))
    
    def with_cookies(self):
        if self._cookies:
            cookies = self._cookies = SimpleCookie()
            for k,v in response._cookies.items():
                cookies[k] = v.value
                cookies[k].update(v)
        return self
    
    def with_headers(self):
        self._headers = dict((k, v[:]) for (k, v) in response._headers.items())
        return self
    
    def with_next(self, path=None, e=None, i=0, **kw):
        if path:
            self.query(next=route(path, e=e, i=i, **kw))
        return self
    
    def with_inputs(self):
        sessions = get_session()
        sessions.session.set_flashdata("__old_inputs", dict(request.var))
        sessions.save()
        return self

    def next(self):
        self.to(request.next)
        return self

    def back(self, code=None):
        if code:
            self.status = code
        self.to(request.previous_url)
        return self
    
    def to(self, url):
        self.set_header('Location', urljoin(request.url, url))
        return self
    
    def query(self, **params):
        loc = self.get_header("Location")
        param = ("?" if "?" not in loc else "") +"&".join(f"{x}={params[x]}" for x in params)
        self.set_header("Location", loc+param)
        return self
    
    def route(self, name, e=None, i=0, **kw):
        return self.to(route(name, e=e, i=i, **kw))
    
    def message(self, *a):
        messages.add(*a)
        return self
    
    def error(self, *a):
        errors.add(*a)
        return self

class JsonResponse(Response):
    default_content_type = "application/json"

    def __init__(self, body='', status=None, headers=None, **more_headers):
        body = json.dumps(body, indent=4)
        super().__init__(body, status, headers, **more_headers)
        self.set_header("Content-Type", "application/json")
    
    def _(self):
        ret = super()._()
        hooks.detach("after_request", self._)
        return ret

class XmlResponse(Response):
    default_content_type = "application/xml"

    def __init__(self, body='', status=None, headers=None, **more_headers):
        body = dicttoxml(body, root=True, attr_type=False).decode("utf-8")
        # body = escape(body)
        super().__init__(body, status, headers, **more_headers)
        self.set_header("Content-Type", "application/xml")
    
    def _(self):
        ret = super()._()
        hooks.detach("after_request", self._)
        return ret


class HTTPError(httperror):
    def message(self, *a):
        messages.add(*a)
        return self
    
    def error(self, *a):
        errors.add(*a)
        return self

def abort(code, text=None, message="", error=""):
    if not text:
        text = HTTP_CODES.get(code, "Restricted Access")
    raise HTTPError(code, text).message(message).error(error)

methods = Methods()

@hooks.attach('after_request')
def set_previous_url():
    from wsgic.session import sessions
    if request.fullpath != sessions.session["__wsgic_vars"].get('__previous_url'):
        sessions.session["__wsgic_vars"]['__previous_url'] = request.fullpath
    # sessions.session["__wsgic_vars"]["__old_inputs"] = dict()


from wsgic.services import register

register("response", Response)
register("request", Request)