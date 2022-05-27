from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine

from wsgic.helpers.extra import _get

class SqlalchemyDatabase:
	def __init__(self, path=None, debug=False, initialize=True, **kwargs):
		self.debug = debug
		self.path = path
		
		if isinstance(_get(kwargs, "metadata"), MetaData):
			self.metadata = _get(kwargs, "metadata")
		else:self.metadata = MetaData()
		self.Model = declarative_base(metadata=self.metadata)

		if initialize:
			self.initialize(**kwargs)
	
	def __call__(*args, **kwargs):
		return Session(*args, **kwargs)

	def _debug(self, text):
		if self.debug:print("[DEBUG]", text)

	def initialize(self, **kwargs):
		eng = kwargs.pop("engine") if _get(kwargs, "engine") else None
		sess = kwargs.pop("session") if _get(kwargs, "session") else None

		if type(eng) is dict:self.engine = create_engine(**eng)
		elif isinstance(eng, Engine):self.engine = eng
		else:self.engine = create_engine(self.path, encoding="utf-8")

		if type(sess) is dict:self.session = Session(bind=self.engine, **sess)
		elif isinstance(sess, (Session, sessionmaker)):self.session = sess
		else:self.session = Session(bind=self.engine, autocommit=True)
		
		self.s = self.session
	
	def create(self):
		self.metadata.create_all(self.engine)
