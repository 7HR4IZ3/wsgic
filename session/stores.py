import json
import os
import pickle
import re
import tempfile
from hashlib import sha1
from random import randint, random
from threading import Thread
from time import time

from wsgic.database.sqlite import SqliteDatabase
from wsgic.database.columns import *
from wsgic.helpers import config
from wsgic.http import request


def _urandom():
    if hasattr(os, "urandom"):
        return os.urandom(30)
    return str(random()).encode("ascii")

class BaseSessionStore(object):
    """Base class for all session stores.
    :param session_class: The session class to use.
    """

    def __init__(self, session_class=None):
        self.session_class = session_class

    def is_valid_key(self, key):
        """Check if a key has the correct format."""
        return re.compile(r"^[a-f0-9]{40}$").match(key) is not None

    def generate_key(self, salt=None):
        """Simple function that generates a new session key."""
        if salt is None:
            salt = repr(salt).encode("ascii")
        return sha1(b"".join([salt, str(time()).encode("ascii"), _urandom()])).hexdigest()

    def new(self):
        """Generate a new session."""
        return self.session_class({}, self.generate_key(), True, store=self)

    def save(self, session):
        """Save a session."""

    def save_if_modified(self, session):
        """Save if a session class wants an update."""
        if session.should_save:
            self.save(session)

    def delete(self, session):
        """Delete a session."""

    def get(self, sid):
        """Get a session for this sid or a new session object. This
        method has to check if the session key is valid and create a new
        session if that wasn't the case.
        """
        return self.session_class({}, sid, True, store=self)


# Used for temporary files by the filesystem session store.
_fs_transaction_suffix = ".__session"


class FilesystemSessionStore(BaseSessionStore):
    """Simple example session store that saves sessions on the
    filesystem.

    :param path: The path to the folder used for storing the sessions.
        If not provided the default temporary directory is used.
    :param filename_template: A string template used to give the session
        a filename. ``%s`` is replaced with the session id.
    :param session_class: The session class to use.
    :param renew_missing: Set to ``True`` if you want the store to give
        the user a new sid if the session was not yet saved.

    .. versionchanged:: 0.1.0
        ``filename_template`` defaults to ``secure_cookie_%s.session``
        instead of ``werkzeug_%s.sess``.
    """

    def __init__(
        self,
        path=None,
        filename_template="wsgic_cookie_%s.session",
        session_class=None,
        renew_missing=False,
        mode=0o644,
    ):
        super(FilesystemSessionStore, self).__init__(session_class=session_class)

        if path is None:
            path = tempfile.gettempdir()

        self.path = path

        assert not filename_template.endswith(_fs_transaction_suffix), (
            "filename templates may not end with %s" % _fs_transaction_suffix
        )
        self.filename_template = filename_template
        self.renew_missing = renew_missing
        self.mode = mode

    def get_session_filename(self, sid):
        # Out of the box this should be a strict ASCII subset, but you
        # might reconfigure the session object to have a more arbitrary
        # string.
        return os.path.join(self.path, self.filename_template % sid)

    def save(self, session):
        fn = self.get_session_filename(session.sid)
        fd, tmp = tempfile.mkstemp(suffix=_fs_transaction_suffix, dir=self.path)
        f = os.fdopen(fd, "wb")

        try:
            pickle.dump(dict(session), f, pickle.HIGHEST_PROTOCOL)
        finally:
            f.close()

        try:
            os.rename(tmp, fn)
            os.chmod(fn, self.mode)
        except (IOError, OSError):  # noqa: B014
            pass

    def delete(self, session):
        fn = self.get_session_filename(session.sid)

        try:
            os.unlink(fn)
        except OSError:
            pass

    def get(self, sid):
        if not self.is_valid_key(sid):
            return self.new()

        try:
            f = open(self.get_session_filename(sid), "rb")
        except IOError:
            if self.renew_missing:
                return self.new()
            data = {}
        else:
            try:
                try:
                    data = pickle.load(f)
                except Exception:
                    data = {}
            finally:
                f.close()

        return self.session_class(data, sid, False)

    def list(self):
        """List all sessions in the store."""
        before, after = self.filename_template.split("%s", 1)
        filename_re = re.compile(
            r"{}(.{{5,}}){}$".format(re.escape(before), re.escape(after))
        )
        result = []
        for filename in os.listdir(self.path):
            # this is a session that is still being saved.
            if filename.endswith(_fs_transaction_suffix):
                continue
            match = filename_re.match(filename)
            if match is not None:
                result.append(match.group(1))
        return result
    
class DatabaseSessionStore(BaseSessionStore):
    def __init__(self, db=None, session_class=None):
        super().__init__(session_class=session_class)
        self.db = db or SqliteDatabase('./.sessions', config.get('databases.sqlite.debug', False), verbose=False, check_same_thread=False)
        self.connect()
    
    def connect(self):
        class Session(self.db.Model):
            _table_name = "wsgic_session"

            key: str = Column(null=True)
            data: str = JSONColumn(null=True)
            ipaddress: str = Column(null=True)
            expires: datetime = DateTimeColumn(null=True)
            created: datetime = DateTimeColumn(null=True)
            last_used: datetime = DateTimeColumn(null=True)
        
        self.sessions = Session

    def get(self, sid):
        # n = randint(0, 100)
        # print("Session cleanup:", n)
        # if n <= 20:
        #     # Thread(target=self.cleanup).start()
        #     (self.cleanup)()

        if self.is_valid_key(sid):
            data = self.sessions.objects.get(key=sid)
            if data:
                data = data[0]
                sid = data.key
                data = data.data
                self.sessions.objects.update({"last_used": datetime.now()}, key=sid)
                return self.session_class(data, sid, False, store=self)
            else:
                return self.session_class({}, sid, False, store=self)

        return self.new()
    
    def cleanup(self):
        ips = []
        for item in self.sessions.objects.all():
            if (not item.ipaddress in ips) and item.expires.timestamp() <= datetime.now().timestamp():
                self.sessions.objects.delete(key=item.key)
            else:
                continue
            ips.append(item.ipaddress)

    def list(self):
        data = self.sessions.objects.get()
        return [self.session_class(data[x].data, data[x].key, False) for x in data]

    def delete(self, session):
        if self.is_valid_key(session.sid):
            self.sessions.objects.delete(key=session.sid)

    def save(self, session):
        if self.is_valid_key(session.sid):
            if session._deleted:
                self.delete(session)
            elif self.sessions.objects.get(key=session.sid):
                self.sessions.objects.update({'data': session, "ipaddress": request.remote_addr, "expires": datetime.fromtimestamp(datetime.now().timestamp() + config.get("session.validity", 3600 * 24)), "last_used": datetime.now()}, key=session.sid)
            else:
                self.sessions.objects.create(key=session.sid, data=session, ipaddress=request.remote_addr, expires= datetime.fromtimestamp(datetime.now().timestamp() + config.get("session.validity", 3600 * 24)), created=datetime.now(), last_used=datetime.now())
            self.modifed = False
