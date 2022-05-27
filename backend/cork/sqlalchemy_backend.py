from wsgic.helpers.extra import _get
from sqlalchemy import create_engine, delete, select, MetaData, Table
from sqlalchemy.engine import Engine

class SqlRowProxy(dict):
	def __init__(self, sql_dict, key, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		self.sql_dict = sql_dict
		self.key = key

	def __setitem__(self, key, value):
		dict.__setitem__(self, key, value)
		if self.sql_dict is not None:
			self.sql_dict[self.key] = {key: value}

class Table:
	"""Provides dictionary-like access to an SQL table."""

	def __init__(self, engine, table, key_col_name):
		self._engine = engine
		self._table = table.__table__
		self._key_col = table.__table__.c[key_col_name]

	def _row_to_value(self, row):
		row_key = row[self._key_col]
		row_value = SqlRowProxy(self, row_key,
			((k, row[k]) for k in row.keys() if k != self._key_col.name))
		return row_key, row_value

	def __len__(self):
		query = self._table.count()
		c = self._engine.execute(query).scalar()
		return int(c)

	def __contains__(self, key):
		query = select([self._key_col], self._key_col == key)
		row = self._engine.execute(query).fetchone()
		return row is not None

	def __setitem__(self, key, value):
		if key in self:
			values = value
			query = self._table.update().where(self._key_col == key)

		else:
			values = {self._key_col.name: key}
			values.update(value)
			query = self._table.insert()

		self._engine.execute(query.values(**values))

	def __getitem__(self, key):
		query = select([self._table], self._key_col == key)
		row = self._engine.execute(query).fetchone()
		if row is None:
			raise KeyError(key)
		return self._row_to_value(row)[1]

	def __set(self, col, key, value):
		if key in self:
			values = value
			query = self._table.update().where(self._table[col] == key)

		else:
			values = {self._table[col].name: key}
			values.update(value)
			query = self._table.insert()

		self._engine.execute(query.values(**values))

	def __get(self, col, key):
		query = select([self._table], self._table[col] == key)
		row = self._engine.execute(query).fetchone()
		if row is None:
			raise KeyError(key)
		return self._row_to_value(row)[1]

	def __iter__(self):
		"""Iterate over table index key values"""
		query = select([self._key_col])
		result = self._engine.execute(query)
		for row in result:
			key = row[0]
			yield key

	def iteritems(self):
		"""Iterate over table rows"""
		query = select([self._table])
		result = self._engine.execute(query)
		for row in result:
			key = row[0]
			d = self._row_to_value(row)[1]
			yield (key, d)

	def pop(self, key):
		query = select([self._table], self._key_col == key)
		row = self._engine.execute(query).fetchone()
		if row is None:
			raise KeyError

		query = delete(self._table, self._key_col == key)
		self._engine.execute(query)
		return row

	def insert(self, d):
		query = self._table.insert(d)
		self._engine.execute(query)

	def empty_table(self):
		query = self._table.delete()
		self._engine.execute(query)


class SqlSingleValueTable(Table):
	def __init__(self, engine, table, key_col_name, col_name):
		Table.__init__(self, engine, table, key_col_name)
		self._col_name = col_name

	def _row_to_value(self, row):
		return row[self._key_col], row[self._col_name]

	def __setitem__(self, key, value):
		Table.__setitem__(self, key, {self._col_name: value})


class SqlAlchemyBackend:
	def __init__(self, db, users, roles, pending_reg, initialize=False, metadata=None, **kwargs):
		self.db = db
		if metadata:
			self.metadata = metadata
		else:self.metadata = self.db.metadata

		if initialize:
			self.initialize(**kwargs)

		self.users = Table(self.engine, users, 'username')
		self.roles = SqlSingleValueTable(self.engine, roles, 'role', "level")
		self.pending_registrations = Table(self.engine, pending_reg, 'code')


	def initialize(self, **kwargs):
		# Create new database if needed.
		try:
			self.engine = self.db.engine
		except:
			eng = kwargs.pop("engine") if _get(kwargs, "engine") else None
			if type(eng) is dict:
				self.engine = create_engine(**eng)
			elif isinstance(eng, Engine):
				self.engine = eng
			else:
				self.engine = create_engine(encoding='utf-8', **kwargs)


	def _initialize_storage(self, db_name):
		self.metadata.create_all(self.engine)

	def _drop_all_tables(self):
		for table in reversed(self.metadata.sorted_tables):
			self.engine.execute(table.delete())

	def save_users(self): pass
	def save_roles(self): pass
	def save_pending_registrations(self): pass
