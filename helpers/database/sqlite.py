import json
import sqlite3
try:
	import pypika
	pypika_available = True
except:pypika_available = False

class SqliteDatabase:
	def __init__(self, path, debug=False, initialize=True, **kwargs):
		self.debug = debug
		self.path = path
		global db
		db = self

		if initialize:
			self.connect(**kwargs)

	def _debug(self, text):
		if self.debug:print("[DEBUG]", text)

	def connect(self, **kwargs):
		try:
			self._debug('[+] Connecting To Database %s' %self.path)
			self.conn = sqlite3.connect(self.path)
			self.cursor = self.conn.cursor()
			self._debug('[+] Connected Successfully To %s \n' %self.path)
			return True
		except Exception:
			self._debug(f'[-] An Error Occured: {Exception} .. Try Again \n')
			return False

	def _tables(self):
		self.cursor.execute(
			"SELECT * FROM sqlite_master WHERE type='table'"
		)
		tables = self.cursor.fetchall()
		return [x[1] for x in tables]

	def _columns_(self, table, str=False):
		self.cursor.execute(f"SELECT name, type FROM pragma_table_info('{table}')")
		data = self.cursor.fetchall()

		return {x[0]: x[1] for x in data} if str == False else [x[0] for x in data]
	 
	def table(self, table, data=None):
		try:
			if table not in self._tables():
				self._debug('[+] Creating Database Table "%s"' %table)
				if data != None:
					# Data syntax
					# 
					ret = []
					for x in data:
						ret.append(data[x])
					tbl = pypika.Query.create_table(table).columns(*ret)

					self.cursor.execute(str(tbl))
					self.conn.commit()
					self._debug('[+] Database Table Sucessfully Created \n')
			else:
				self._debug('[-] Table Already Exists')
		except:
			self._debug(f'[-] Database Table Could Not Be Created Or Already Exists \n')

	def add_column(self, table, data=None, default=None):
		try:
			if table in self._tables():
				self._debug('[+] Altering Database Table "%s"' %table)
				if data != None:
					# Data syntax
					# {'id': 'INTEGER PRIMARY KEY', 'name': 'text', 'email': 'text'}
					data = ''.join(f'"{x}" {data[x]}, ' for x in data)[:-2]
					default = f' DEFAULT {default}' if default != None else ''
					self.cursor.execute(f"ALTER TABLE {table} ADD {data}{default}")
					self.conn.commit()
					self._debug('[+] Database Table Sucessfully Altered \n')
			else:
				self._debug('[-] Table Does Not Exists')
		except:
			self._debug('[-] Database Table Could Not Be Altered Or Does Not Exists \n')
	
	def drop_column(self, table, column):
		try:
			if table in self._tables():
				self._debug('[+] Altering Database Table "%s"' %table)
				if column != None:
					# Data syntax
					# {'id': 'INTEGER PRIMARY KEY', 'name': 'text', 'email': 'text'}
					if type(column) is str:
						self.cursor.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
					else:
						for x in column:
							self.cursor.execute(f"ALTER TABLE {table} DROP COLUMN {x}")
					self.conn.commit()
					self._debug('[+] Database Table Column Sucessfully Dropped \n')
			else:
				self._debug('[-] Table Does Not Exists')
		except:
			self._debug('[-] Database Table Column Could Not Be Droped Or Does Not Exists \n')

	def insert(self, table, data=None):
		# try:
		self._debug('[+]Inserting Data To Database Table "%s"' %table)
		if data != None:
			# Data syntax
			# ('test', 'test@test.com')
			query = str(pypika.Table(table).insert(*data))
			self.cursor.execute(query)
			self.conn.commit()
			self._debug('[+] Data Sucessfully Inserted \n')
		# except:
		# 	self._debug('[+] An Error Occured \n')

	def read(self, table, *select, as_json=False, model_=None, **where):
		try:
			if not select:select = ("*",)
			tbl = pypika.Table(table)
			w = []
			if where:
				if not model_:model_ = tbl
				for x in where:
					w.append(
						getattr(model_, x) == where[x]
					)
				query = str(tbl.select(*select).where(*w))
			else:query = str(tbl.select(*select))

			self.cursor.execute(query)

			v = self.cursor.fetchall()
			columns = select if select != ("*",) else self._columns_(table, str=True)
			data = self.serialize(columns, v)
			if as_json:
				data = json.dumps(data)
				self._debug('[+] Returning as json')
			self._debug('[+] Read From Table "%s" Successful' %table)
			return data
		except:
			self._debug('[-] Could Not Read From Table "%s" .. The table Might Not Exist' %table)

	def get(self, table, select='*', where=None, as_json=False, one=False):
		# Data syntax
		# {
		#  'name=': 'example',
		#  'age <': 5
		# }
		self.cursor.execute(f"SELECT * FROM {table}")
		print("All: ", self.cursor.fetchall())
		try:
			self._debug('[+] Reading Data From Table "%s" ' %table)
			select = "".join(f"{x}, " for x in select) if select != '*' else "".join(f"{x}, " for x in self._columns(table, str=True))
			where = f" WHERE {where}" if where != None else ""

			query = f"SELECT {select[:-2]} FROM {table}{where}"
			print(query)
			self.cursor.execute(query)
			if one == True:data = self.serialize(select, self.cursor.fetchone())
			else:data = self.cursor.fetchall()

			if as_json:
				data = json.dumps(data)
				self._debug('[+] Returning as json')
			self._debug('[+] Read From Table "%s" Successful' %table)
			return data
		except:
			self._debug('[-] Could Not Read From Table "%s" .. The table Might Not Exist' %table)

	def update(self, table, data=None, **kw):
		try:
			self._debug('[+] Updating Data To Database Table "{}" With Id "{}"'.format(table, id))
			where = self._get(kw, 'where')
			if data and id != None:
				# Data syntax
				# name = ?, email = ?, ('example', 'example@gmail.com')
				self.cursor.execute(f"UPDATE {table} SET "+''.join(f'{x} = {data[x]}, ' for x in data)[:-2]+f" WHERE ?", (where, ))
				self.conn.commit()
				self._debug('[+] Data Updated')
		except:
			self._debug('[-] Could Not Update Data In Table "%s" .. The table Might Not Exist' %table)

	def delete(self, table, where=None):
		try:
			if where != None:
				self.cursor.execute(f"DELETE FROM {table} WHERE {where}")
				self.conn.commit()
			else:
				self.cursor.execute(f"DELETE FROM {table}")
				self.conn.commit()
		except:
			pass

	def execute(self, query, one=False, args=None):
		try:
			self._debug('[+] Running Query ')
			print(str(query))
			if args:
				self.cursor.execute(str(query), args)
			else:
				self.cursor.execute(str(query))

			data = self.cursor.fetchone() if one else self.cursor.fetchall()
			self.conn.commit()
			self._debug('[+] Query Successfully Executed \n')
			return data
		except:
			self._debug('[-] An Error Occured.. Check The Query \n')
	
	def execute_many(self, query):
		try:
			self._debug('[+] Running Query ')
			self.cursor.executescript(str(query))
			data = self.cursor.fetchall()
			self.conn.commit()
			self._debug('[+] Query Successfully Executed \n')
			return data
		except:
			self._debug('[-] An Error Occured.. Check The Query \n') 
		
	def serialize(self, columns, data):
		try:
			dic = dict()
			for n, value in enumerate(data):
				t = dict()
				for x, key in enumerate(columns):
					t[key] = value[x]
				dic[n+1] = t
			return dic
		except:
			pass
	
	def drop(self, table):
		self.cursor.execute(f"DROP {table}")
		self.conn.commit()

	class Model:
		def __init__(self, initialize=False):
			self.tableName = self.__class__.__name__
			self._db = pypika
			self._query = self._db.Query
			self._table = self._query.from_(self.tableName)
			self.table = self._db.Table(self.tableName)
			self.columns = {}

			if initialize:
				self.create()

		def __call__(self, *args, **kwds):
			return self.new(*args, **kwds)

		def _compare(self, old, new):
			added, removed= {}, {}
			if old == new:return {'added': added, 'removed': removed}
			for a in old:
				if a not in new:removed[a] = old[a]
			for b in new:
				if b not in old:added[b] = new[b]
			return {'added': added, 'removed': removed}

		def all(self, begin=0, end=-1, step=1):
			data = db.execute(
				self.table.select("*")
			)
			return data[begin:end:step]

		def column(self, name, type="text", null=None, default=None):
			c = pypika.Column(name, type, null, default)
			self.columns[name] = c

		def create(self):
			self.column("id", type="integer primary key")
			compare = self._compare(db._columns_(self.tableName), self.columns)
			if self.tableName not in db._tables():
				db.table(self.tableName, self.columns)
				return
			if compare['added'] != {}:
				db.add_column(self.tableName, compare['added'])
				self._debug(f"Added: {compare['added']}")
			if compare['removed'] != {}:
				db.drop_column(self.tableName, compare['removed'])
				self._debug(f"Removed: {compare['removed']}")

		def get(self, *select, as_json=False, model_=None, **where):
			data = db.read(self.tableName, *select, as_json=as_json, **where, model_=model_)
			return data

		def new(self, data=None, **kw):
			try:
				dta = [pypika.NULL]
				if not data:data = kw
				try:
					for x in data:dta.append(data[x])
				except:raise TypeError
				db.execute(
					self.table.insert(*dta)
				)
				return True
			except:return False

	def __del__(self):
		self.conn.close()

db = SqliteDatabase("db.sqlite")

class Users(db.Model):
	pass