from wsgic import App
from wsgic.thirdparty.bottle import load
from wsgic.http import request, response
from wsgic.helpers import hooks, config

from datetime import datetime

from .helpers import ModificationTrackingDict
from .stores import DatabaseSessionStore


class SessionDict(ModificationTrackingDict):
    """Subclass of a dict that keeps track of direct object changes.
    Changes in mutable structures are not tracked, for those you have to
    set ``modified`` to ``True`` by hand.
    """

    __slots__ = ModificationTrackingDict.__slots__ + ("sid", "new", "_deleted", "_store")

    def __init__(self, data, sid, new=False, store=None):
        super(SessionDict, self).__init__(data)
        self.sid = sid
        self.new = new
        self._store = store
        self._deleted = False

    def __repr__(self):
        return "{}({}{})".format(
            self.__class__.__name__,
            dict.__repr__(self),
            "*" if self.should_save else "",
        )
    
    def __getitem__(self, *items):
        ret = []
        for key in items:
            data = super().__getitem__(key)
            if key == "__wsgic_vars":
                return data
            if key in self["__wsgic_vars"]:
                self["__wsgic_vars"][key]["used"] += 1
                if self["__wsgic_vars"][key]["used"] == self["__wsgic_vars"][key]["limit"]:
                    self.pop(key)
                    self["__wsgic_vars"].pop(key)
            ret.append(data)

        return ret[0] if len(ret) == 1 else ret
    
    def get(self, name, default=None):
        try:
            return self[name]
        except LookupError:
            return default
    
    def limit(self, name, lim):
        if name in self:
            self["__wsgic_vars"][name] = {"used": 0, "limit": lim}
    
    def delimit(self, name):
        if name in self["__wsgic_vars"]:
            self["__wsgic_vars"].pop(name)
    
    def mark_as_flashdata(self, name):
        self.limit(name, 1)
    
    def unmark_as_flashdata(self, name):
        self.delimit(name)
    
    def set_flashdata(self, name, value):
        self[name] = value
        self.mark_as_flashdata(name)

    @property
    def should_save(self):
        """True if the session should be saved."""
        return self.modified
    
    def delete(self):
        copy = [x for x in self]
        for x in copy:
            self.pop(x)
        self._deleted = True
    
    # def save(self):
        # self._store.save(self)
    
    def __del__(self):
        self.delete()

class Sessions:
    session: SessionDict
    _session = SessionDict({
        "__wsgic_vars": {}
    }, '')
    store = DatabaseSessionStore(session_class=SessionDict)
    
    def __init__(self, config):
        self.config = config
        self.cookie_config = config.get("cookie", {
            'name': "wsgic_session",
            'path': "/",
            'expires': None, # None
            'maxage': 3600 * 24 * 31,
            'secret': 'wsgic_default_secret_key-jufjjgvssbionit4e4we6jbd4ri9k8',
            'secure': False,
            'domain': None,
            'httponly': False,
            'samesite': "Lax"
        })

        sclass = self.config.get('dict', 'wsgic.session:SessionDict')
        if type(sclass) is str:
            sclass = load(sclass)

        store = self.config.get('store')
        if type(store) is str:
            store = load(store)
        self.store = store(session_class=sclass) if store else self.store
    
    @property
    def session(self):
        return self._session

    def get(self, sid=None):
        sid = sid or request.get_cookie(self.cookie_config.get('name', 'wsgic_session'), secret=self.cookie_config.get("secret"))

        if sid:
            self._session = self.store.get(sid)
        else:
            self._session = self.store.new()
        if "__wsgic_vars" not in self.session:
            self._session["__wsgic_vars"] = {}
        # print(self._session.sid)
        request.session = self._session

    def save(self, session=None):
        autosave = str(self.config.get("autosave", True)).lower()
        if autosave in ("true", "if_modified"):
            if autosave == "if_modified":
                if dict(self.session) == dict(self.store.get(self.session.sid)):
                    return
            # sessconfig = {x: self.config[x] for x in self.config if self.config[x] and x not in ["class", 'dict', 'store', 'autosave']}
            sessconfig = {x: self.cookie_config[x] for x in self.cookie_config if self.cookie_config[x]}
            secret = sessconfig.pop("secret", None)

            session = session or self.session
            # print("save", session, session.sid)
            # print(session.should_save)
    
            self.store.save(session)
            self.session.modified = False
            return response.set_cookie(sessconfig.pop('name', 'wsgic_session'), session.sid, secret=secret, **sessconfig)

    def delete(self, session=None):
        session = session or self.session
        self.store.delete(self._session)
        return response.delete_cookie(self.cookie_config.get('name', 'wsgic_session'), domain=self.cookie_config.get("domain"), path=self.config.get("path"))

    def regenerate(self):
        self.delete()
        return self.get()

    def setup(self):
        hooks.attach('before_request', self.get)
        hooks.attach('after_request', self.save)

# Handle session
# class Session2(ModificationTrackingDict):
#     __slots__ = ModificationTrackingDict.__slots__ + ("sid", "_store", "modified")
    
#     def __init__(self, **kw):
#         super(ModificationTrackingDict, self).__init__(kw)
#         self.sid = None
#         self.modified = False
#         sclass = config.get('dict', 'wsgic.session:SessionDict')
#         if type(sclass) is str:
#             sclass = load(sclass)

#         store = config.get('store')
#         if type(store) is str:
#             store = load(store)
#         self._store = store(session_class=sclass) if store else DatabaseSessionStore(session_class=SessionDict)
#         hooks.attach('before_request', self.__get)
    
#     def __getattr__(self, name):
#         if name in self:
#             return self[name]
#         # elif name in self.__slots__:
#         #     return super().__getattr__(name)
#         raise LookupError("Session has no item names '%s'"%name)
    
#     def __setattr__(self, name, value):
#         if name in self.__slots__:
#             return super().__setattr__(name, value)
#         self[name] = value
    
#     def __get(self):
#         sid = request.get_cookie(config.get('name', 'wsgic_session'), secret=config.get("secret"))
#         if sid:
#             new = self._store.get(sid)
#         else:
#             new = self._store.new()

#         keys = list(self.keys())
#         for x in keys:
#             self.pop(x)

#         self.sid = new.sid
#         for x in new:
#             self[x] = new

#     def save(self):
#         sessconfig = {x.lower(): config.SESSION[x] for x in config.SESSION if config.SESSION[x] and x not in ["CLASS", 'DICT', 'STORE']}
#         secret = sessconfig.pop("secret", None)
#         self._store.save(self)
#         return response.set_cookie(sessconfig.pop('name', 'wsgic_session'), self.sid, secret=secret, **sessconfig)
    
#     def delete(self):
#         self._store.delete(self)
#         return response.delete_cookie(config.get('name', 'wsgic_session'), domain=config.get("domain"), path=config.get("path"))
    
#     def regenerate(self):
#         self.delete()
#         return self.get()

sessions: Sessions

def set_sessions(session):
    global sessions
    sessions = session

if config.get("use.session", True):
    sessions = Sessions(config.get("session", {}))
    sessions.setup()

# session = Session2()
