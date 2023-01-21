#pylint:disable=W0212
import asyncio
import json
import os
import pickle
import re
# import uuid
import sys
import difflib
from datetime import date


class Bytes(bytes):
	def __str__(self) -> int:
		return super().__hash__()

str_to_py = {
	"text": str,
	"string": str,
	"integer": int,
	"json": str,
	"boolean": bool,
	"decimal": float,
	"date": str,
	"bytes": str
}

# Helper Functions
def _compare(old, new):
	'''
	Checks between existing list and new list for added and removed values
	'''
	added, removed= [], []
	if old == new:
		return { 'added': added, 'removed': removed }
	for i, item in enumerate(old):
		if item not in new:
			removed.append({'item':item, 'index': i})
	for i, item in enumerate(new):
		if item not in old:
			added.append({'item': item, 'index': i})
	return {'added': added, 'removed': removed}


def load(target):
	module, target = target.split(":", 1) if ':' in target else (target, None)
	if module not in sys.modules: __import__(module)
	if not target: return sys.modules[module]
	if target.isalnum(): return getattr(sys.modules[module], target)

def dtype(name, schema=None):
		return str_to_py[schema[name].type]

# Helper Classes
class Dict(dict):
	def __init__(self, parent=None, **k):
		super(Dict, self).__init__(**k)
		self.modified = False
		self.parent = parent
	
	def json(self):
		return json.dumps(self)
	
	def __setitem__(self, name, value):
		super().__setitem__(name, value)
		self.on_change()
	
	def __delitem__(self, name):
		super().__delitem__(name)
		self.on_change()

	def __getattribute__(self, name):
		if name in self:
			return self[name]
		return super().__getattribute__(name)

	def __setattr__(self, name, value):
		if name in self:
			self[name] = value
			return
		return super().__setattr__(name, value)
	
	def undo(self):
		data = json.load('tmpfiledb.tmp')
		
		async def load_(dictobj, to=self, use=Dict):
			for x in dictobj:
				if x == "_tables":
					to[x] = Dict(self)
					for table in dictobj[x]:
						to[x][table] = Table(name=table, parent=self)
						await load_(dictobj[x][table], to=to[x][table])
				elif type(dictobj[x]) is dict:
					to[x] = use(self)
					await load_(dictobj[x], to=to[x])
				else:
					to[x] = dictobj[x]
		
		asyncio.run(load_(data))
	
	def on_change(self):
		cls = self.parent or self
		cls.modified = True
		file = open('tmpfiledb.tmp', "w")
		file.write(json.dumps(self))
		file.close()
	
	def close(self):
		os.remove("tmpfiledb.tmp")

class List(list):
	def __or__(self, other):
		return List(set([*self, *other]))
	
	def __and__(self, other):
		if self == other:
			return List(self)
		alll = []
		if self:
			for x in self:
				if other and x in other:
					alll.append(x)
		elif other:
			alll = other
		return List(alll)
		
	def json(self):
		return json.dumps(self)
		

class DB(Dict):
	def __getattribute__(self, name):
		if name in self['_tables']:
			return self['_tables'][name]
		return super().__getattribute__(name)

class Column:
	def __init__(self, table, data):
		self._data = data
		self._table = table
	
	def contains(self, word: str):
		ret = List()
		for i, x in enumerate(self._table["_values"]):
			if word in x[self._data]:
				ret.append(i)
		return ret if len(ret) > 0 else []

	def match(self, pattern: str):
		ret = List([i for i, x in enumerate(self._table["_values"]) if re.search(pattern, x[self._data])])
		return ret if len(ret) > 0 else []

	def get(self):
		return self._data
	
	def __str__(self):
		return self.get()
	
	def __eq__(self, value):
		ret = List()
		for x in self._table["_values"]:
			if x[self._data] == value:
				ret.append(x)
		return ret if len(ret) > 0 else []

	def __lt__(self, value):
		ret = List()
		for x in self._table["_values"]:
			if x[self._data] < value:
				ret.append(x)
		return ret if len(ret) > 0 else []

	def __gt__(self, value):
		ret = List()
		for x in self._table["_values"]:
			if x[self._data] > value:
				ret.append(x)
		return ret if len(ret) > 0 else []

	def __le__(self, value):
		return List([*self.__lt__(value), *self.__eq__(value)])

	def __ge__(self, value):
		return List([*self.__gt__(value), *self.__eq__(value)])
	
	def __hash__(self):
		return hash(self._data)

class Table(Dict):
	def __init__(self, name=None, **kw):
		self._name = name
		super().__init__(**kw)
		self.table_schema =  {}
		
	def __call__(self, data=None, **datas):
		data = data or datas
		return self.new(data)
	
	def __str__(self):
		return self.json()
	
	def json(self):
		return self.all().json()

	def all(self) -> List:
		return List([Dict(**x) for x in self._values])
	
	def save(self):
		return self.parent.commit()

	def get(self, indexes: List=None, select: list=None, as_dict=False) -> List:
		alll = List() if not as_dict else dict()
		if not indexes:
			indexes = [x for x in range(len(self._values))]
		for i, index in enumerate(indexes):
			if select:
				d = Dict()
				for column in select:
					if isinstance(column, Column):
						column = column.get()
					d[column] = self._values[index][column]
			else:
				d = Dict(**self._values[index])
			if as_dict:
				alll[i] = d
			else:
				alll.append(d)
		if len(alll) == 1:
			return alll[0] if not as_dict else alll[1]
		return alll
	
	def update(self, where: List, data: dict) -> None:
		if where == []:
			raise Exception('No column matching query')
		target = self._values.pop(where[0])
		for item in data:
			if item not in target:
				raise Exception(f'No such column "{item}" in table "{self._name}"')
			item_dtype = self.parent._dtype(self._name, item)
			if isinstance(data[item], item_dtype):
				target[item] = data[item]
			else:
				raise ValueError(f'Column "{item}" value should be {item_dtype}')
		self._values.insert(where[0], target)
		return

	async def _get_default(self, column: str):
			# Check and call if default value is callable
			dvalue = self.table_schema[column].default
			if isinstance(dvalue, dict):
				call_ = dvalue.get('call', lambda: '')
				args = dvalue.get('args', ())
				kwargs = dvalue.get('kwargs', {})
				format_ = dvalue.get('format', 'string')
				if call_.startswith('::'):
					dvalue = str_to_py[format_](load(call_.replace('::', ''))(*args, **kwargs))
				elif call_ in self.parent.extfunct:
					dvalue = self.parent.extfunct[call_]
					if callable(dvalue):
						dvalue = str_to_py[format_](dvalue(*args, **kwargs))
				if isinstance(dvalue, self.parent._dtype(self.table_schema[column].type, column)):
					return dvalue
				else:
					raise ValueError(f'Column "{column}" value should be {self.table_schema[column].type}')

	def new(self, data=None, **datas):
		data = data or {}
		data = dict(**data, **datas)
		return asyncio.run(self._new(data))

	async def _new(self, data: dict):
		'''
		Insert new values into database table "{}"
		'''.format(self._name)
		
		self.table_schema =  self.parent['_schema'][self._name]
		ret = Dict()
		
		for column in self._columns:
			# No value specified for column
			if column not in data:
				# If column is a primary key
				if dtype(column, self.table_schema) is int and self.table_schema[column].primary_key is True:
					val = self._values
					value = 0
					if len(val) > 0:
						value = val[-1][column]
					ret[column] = value+1
				# Check for default values
				elif self.table_schema[column].default:
					ret[column] = await self._get_default(column)
				elif self.table_schema[column].null is True:
					ret[column] = None
				else:
					raise AssertionError(f'No value specified for not defaulted or nulled column: "{column}"')
			# Check if column value matches column datatype
			elif isinstance(data[column], self.parent._dtype(self._name, column)):
				# Check if column value limit is set and if value is within the limit
				limit = self.table_schema[column].max_length
				if limit and len(data[column]) > limit:
					raise ValueError(f'Length of column "{column}" exceeds specified limit: {limit}')
				# Check if column value should be unique and if it is unique
				if self.table_schema[column].unique:
					for value in self._values:
						if value[column] == data[column]:
							raise ValueError(f'Column "{column}" value should be unique but already exists')
				# Add the item to database
				ret[column] = data[column]
		self._values.append(ret)
		return ret

	def __getattribute__(self, name):
		try:
			if name in self:
				return self[name]
			return Column(self, self["_columns"][name])
		except KeyError:
			try:
				return super().__getattribute__(name)
			except AttributeError:
				raise KeyError('Unknown column "%s"'%name)

#	def __setattr__(self, name, value):
#		if name in self:
#			self[name] = value
#			return
#		return super().__setattr__(name, value)

# Main class
class JsonDatabase(DB):
	'''
	Dictionary like database storage using json to store values
	```python
	
	db = JsonDatabase("database.json")

	db.table("users", {
		"name": db.column("text", default='Thraize'),
		"age": db.column("integer", default = 6)
	})

	db.table("admin", {
		"name": db.column("integer"),
		"uuid": db.column("integer", default={
			'call': '::uuid:uuid4',
			'format': 'string'#	})
	})

	db.insert('users', {
		'name': 'Thraize',
		'age': 19
	})

	db.insert('admin', {
		'name': 'Thraize'
	})

	db.update(db.admin, db.admin.id == 1, {'name': 'Demian'})

	db.commit()
	```
	'''
	def __init__(self, path="database.json", encrypt=False):
		super(JsonDatabase, self).__init__(_tables = Dict(parent=self), _schema = Dict(parent=self))
		self.mod = Dict(parent=self, _tables=Dict(self), _schema = Dict(parent=self))
		self.path = path.replace("$","")
		self.encrypt = encrypt
		asyncio.run(self.load())
		self.haspk = False
		self.modified = True
		self.extfunct = {}
		
		self._schema_datatypes = str_to_py
		self.List = List
		self.Dict = Dict
		
	def _dtype(self, table, name):
		return dtype(name, schema=self._schema[table])

	def register(self, **data):
		for x in data:
			self.extfunct[x] = data[x]
	
	def table(self, name: str, _columns: Dict):
		'''
		Create new table in the database
		'''
		# Add id column if not already present in column dictionary
		if "id" not in _columns:
				_columns = dict(id=self.column("integer", primary_key = True), **_columns)
		table__schema = Dict(self,
				**{x: Dict(
					self,
					type=_columns[x].type,
					default=_columns[x].deft,
					max_length=_columns[x].ml,
					primary_key=_columns[x].pk,
					unique=_columns[x].unq,
					null=_columns[x].null
				) for x in _columns}
			)
		
		# If table dosent exist create else update
		if name not in self["_tables"]:
			self["_tables"][name] = Table(
				parent=self,
				name = name,
				_values = [],
				_columns = {x: x for x in _columns.keys()}
			)
			self["_schema"][name] = table__schema
		else:
			compare = _compare(self._schema[name], table__schema)

			if compare["added"] != [] or compare["removed"] != []:
				values = self["_tables"][name]['_values']
				self["_tables"].pop(name)
				self["_schema"].pop(name)

				for item in values:
					for column in compare['added']:
						dvalue = table__schema[column['item']].default
						if isinstance(dvalue, dict):
							call_ = dvalue.get('call')
							args = dvalue.get('args', ())
							kwargs = dvalue.get('kwargs', {})
							format_ = dvalue.get('format', 'string')
							if call_.startswith('::'):
								dvalue = str_to_py[format_](load(call_.replace('::', ''))(*args, **kwargs))
							elif call_ in self.extfunct:
								dvalue = self.extfunct[call_]
								if callable(dvalue):
									dvalue = str_to_py[format_](dvalue(*args, **kwargs))
						item[column['item']] = dvalue
					for column in compare['removed']:
						item.pop(column['item'])

				self["_tables"][name] = Table(
					parent=self,
					name = name,
					_values = values,
					_columns = {x: x for x in _columns.keys()}
				)
				self["_schema"][name] = table__schema
			# self.updatetable(self._schema[name], table__schema)
		self.haspk = False
		return self["_tables"][name]
	
	def updatetable(self, _schema: list, table__schema: list):
		'''
		Update the schema of a table by adding or removing columns
		'''
		if _schema != table__schema:
			_schema_comp = _compare(_schema, table__schema)
			
			if len(_schema_comp['removed']) > 0:
				for item in _schema_comp['removed']:
					_schema.pop(item['item'])
			
			if len(_schema_comp['added']) > 0:
				for item in _schema_comp['added']:
					_schema.insert(item['index'], item['item'])
	
	def update(self, table: Table, where: List, data: dict):
		return self._tables[table._name].update(where, data)

	def get(self, table: str, indexes: List, select: list=None):
		values = self._tables[table].get(indexes, select=select)
		return values

	def insert(self, name, data):
		return self._tables[name].new(data)

	def column(self, _type, default=None, primary_key=False, max_length=None, unique=False, null=False):
		if primary_key:
			if not self.haspk:
				self.haspk = True
			else:
				primary_key = False
		if default and max_length:
			if len(default) > max_length:
				raise ValueError(f'Length of default "{default}" exceeds specified limit: {max_length}')
		return Dict(type=_type, deft=default, pk=primary_key, ml=max_length, unq=unique, null=null)
	
	@property
	def should_save(self):
		return self.modified
	
	async def load(self):
		if self.modified:
			await self._commit()
		try:
			if self.encrypt:
				file = open(self.path, "rb")
				data = pickle.loads(file.read())
			else:
				file = open(self.path, "r")
				data = file.read()
			data = json.loads(data)
			file.close()

			async def load_(dictobj, to=self, use=Dict):
				for x in dictobj:
					if x == "_tables":
						to[x] = Dict(self)
						for table in dictobj[x]:
							to[x][table] = Table(name=table, parent=self)
							await load_(dictobj[x][table], to=to[x][table])
					elif type(dictobj[x]) is dict:
						to[x] = use(self)
						await load_(dictobj[x], to=to[x])
					else:
						to[x] = dictobj[x]
			await load_(data)

			self.mod = self
		except:
			data = "{}"
			if self.encrypt:
				file = open(self.path, "wb")
				data = pickle.dumps(data)
			else:
				file = open(self.path, "w")
			file.write(data)
			file.close()
			await self.load()
	
	async def _commit(self):
		async def save(dictobj, to=self):
			for x in dictobj:
				if x not in self.items():
					if isinstance(dictobj[x], Dict):
						if len(dictobj[x]) > 0:
							await save(dictobj[x], to=to[x])
						else:
							to[x] = Dict()
					to[x] = dictobj[x]
		await save(self.mod)

		if os.path.exists(self.path):
			os.remove(self.path)
		if self.encrypt:
			file = open(self.path, "wb")
			data = pickle.dumps(self)
		else:
			file = open(self.path, 'w')
			data = json.dumps(self, indent=4)
		file.write(data)

		self.modified = False
		return
		
	def commit(self):
		asyncio.run(self._commit())

#db = JsonDatabase("C:\\Users\\user.user-PC\\Desktop\\BACK-UPS\\javascript\\wsgi\\database.json")

#Books = db.Books
# Books(title="Indenmity only", rating=5)
# Books(title="New School Physics", rating=4)

#print(Books.id == 2)

#db.table("users", {
#	"name": db.column("text", default='Thraize'),
#	"age": db.column("integer", default = 6)
#})

#db.table("admin", {
#	"name": db.column("integer"),
#	"uuid": db.column("integer", default={
#		'call': '::uuid:uuid4',
#		'format': 'string'#	})
#})

#db.insert('users', {
#	'name': 'Thraize',
#	'age': 19
#})

#db.insert('admin', {
#	'name': 'Thraize'
#})

#db.update(db.admin, db.admin.id == 1, {'name': 'Demian'})
#print((db.posts.title.match(r"^Get .+ 2022$")) & (db.posts.id < 5))
#db.commit()
