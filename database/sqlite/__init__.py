from copy import copy

# if __name__ == "__main__":
#     from bottle import makelist
#     # from helpers import *
#     # from models import Model
#     # from columns import Column
# else:
from wsgic.thirdparty.bottle import makelist
from ..helpers import *
from ..models import Model
from ..columns import Column

# from bottle import makelist
# from helpers import *
# from models import Model
 
import json, re
import sqlite3

class SqliteDatabase(Hooks):

    def __init__(self, path, debug=False, verbose=False, initialize=True, **kwargs):
        
        self.debug = debug
        self.path = path
        
        self.Model = Model
        self.Model.bind(self)
        self.Column = Column
        self.Column._table = self.Model
        self.List = List
        
        self.models = {}
        self.verbose = verbose
        self.kw = kwargs
        self.last_query = None
        self.last_query_args = None
        self.last_query_data = None
        kwargs["check_same_thread"] = False

        self._model_methods = ["get", "create", "update", "delete", "like"]

        if initialize:
            self.connect()
    
    def __getattr__(self, name):
        if hasattr(self.connection, name):
            return getattr(self.connection, name)
        raise AttributeError

    def _debug(self, *text):
        if self.debug:print("[DEBUG]", *text)

    def _debug_(self, *text):
        if self.verbose:print("[VERBOSE]", *text)

    def connect(self):
        try:
            self._debug('[+] Connecting To Database %s' %self.path)
            self.connection = sqlite3.connect(self.path, **self.kw)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            self.trigger("connect")
            self._debug('[+] Connected Successfully To %s \n' %self.path)
            return True
        except Exception as e:
            self._debug(f'[-] An Error Occured: .. Try Again \n')
            self._debug('[INFO]', e)
            self.trigger("error", e)
            return False

    def _tables(self):
        self.cursor.execute(
            "SELECT * FROM sqlite_master WHERE type='table'"
        )
        tables = self.cursor.fetchall()
        return [x[1] for x in tables]

    def _columns_(self, table, as_str=False):
        data = self._table_sql(table)
        
        ret = {}
        if data:
            data = data.split("(")[1].split(")")[0].split(",")
            for x in data:
                x = x.strip().split(" ")
                ret[x[0].replace('"', "")] = x[1]
        else:
            self.cursor.execute(f"SELECT sql FROM sqlite_master where type='table' AND name NOT LIKE 'sqlite_%'")
            self._debug(self.cursor.fetchall())

        return ret if as_str == False else [x for x in ret]
    
    def _table_sql(self, table):
        self.cursor.execute(f"SELECT sql FROM sqlite_master where type='table' AND name NOT LIKE 'sqlite_%' AND name='{table}'")
        data = self.cursor.fetchone()
        return data[0] if data else ""
     
    def table(self, table, data=None):
        try:
            # if table not in self._tables():
            self._debug("")
            self._debug('[+] Creating Database Table "%s"' %table)
            if data:
                columns = ",".join(data[x]._query() for x in data)
                query = "CREATE TABLE IF NOT EXISTS %(table)s (%(columns)s)"%{
                    'table': table,
                    'columns': columns
                }

                self.execute(query)
                self.connection.commit()
                self._debug('[+] Database Table Sucessfully Created \n')
            # else:
            #     self._debug('[-] Table Already Exists')
        except Exception as e:
            self._debug(f'[-] Database Table Could Not Be Created Or Already Exists \n')
            self._debug('[INFO]', e)
            self.trigger("error", e)

    def add_column(self, table, data=None, default={}):
        try:
            # if table in self._tables():
            self._debug("")
            self._debug('[+] Altering Database Table "%s"' %table)
            if data:
                # Data syntax
                # {'id': 'INTEGER PRIMARY KEY', 'name': 'text', 'email': 'text'}
                for x in data:
                    d = " DEFAULT ?" if default.get(x) else ""
                    self.execute(f'ALTER TABLE {table} ADD COLUMN '+str(data[x]._query()))
                self._debug('[+] Database Table Sucessfully Altered \n')
            # else:
            #     self._debug('[-] Table Does Not Exists')
        except Exception as e:
            self._debug('[-] Database Table Could Not Be Altered Or Does Not Exists \n')
            self._debug('[INFO]', e)
            self.trigger("error", e)
    
    def drop_column(self, table, columns):
        try:
            # if table in self._tables():
            self._debug("")
            self._debug('[+] Altering Database Table "%s"' %table)
            if columns:
                # Data syntax
                # {'id', 'name', 'email'}
                if type(columns) is str:
                    self.execute(f"ALTER TABLE {table} DROP COLUMN {columns}")
                else:
                    for x in columns:
                        self.execute(f"ALTER TABLE {table} DROP COLUMN {x}")
                self.connection.commit()
                self._debug('[+] Database Table Column Sucessfully Dropped \n')
            # else:
            #     self._debug('[-] Table Does Not Exists')
        except Exception as e:
            self._debug('[-] Database Table Column Could Not Be Droped Or Does Not Exists \n')
            self._debug('[INFO]', e)
            self.trigger("error", e)

    def create(self, table, **data):
        try:
            self._debug("")
            self._debug('[+] Inserting Data To Database Table "%s"' %table)
            if data:
                # Data syntax
                # ('test', 'test@test.com')
                data = self.validate(table, data, action="create")
                model = self.models[table]

                columns = [getattr(model, x).name for x in list(data.keys())]
                
                query = "INSERT INTO %(table)s (%(columns)s) VALUES (%(qmarks)s)" %{
                    'table': table,
                    'columns': ', '.join(columns),
                    'qmarks': str('?, ' * len(columns))[:-2]
                }
                self.execute(query, args=List(data.values()))
    
                self.connection.commit()
                self._debug('[+] Data Sucessfully Inserted \n')
        except Exception as e:
            self._debug('[+] An Error Occured \n')
            self._debug('[INFO]', e)
            self.trigger("error", e)

    def get(self, table, *select, as_json=False, **where):
        try:
            self._debug("")
            if not select:
                select = ("*",)
            
            where = self.validate(table, where, action="read")

            if where:
                model = self.models[table]
                values = List(where.values())
                where = "WHERE " +  "".join(f"{getattr(model, x).name} = ? AND " for x in where)[:-5]
            else:
                where = ''
                values = []
            query = "SELECT %(select)s FROM %(table)s %(where)s" % {
                    'select': ','.join(select),
                    'table': table,
                    'where': where
                }

            data = self.execute(query, args=values, table=table)

            if as_json:
                data = json.dumps(data)
                self._debug('[+] Returning as json')
            self._debug('[+] Read From Table "%s" Successful' %table)
            return data
        except Exception as e:
            self._debug('[-] Could Not Read From Table "%s" .. The table Might Not Exist' %table)
            self._debug('[INFO]', e)
            self.trigger("error", e)

    def update(self, table, data=None, **where):
        try:
            self._debug("")
            self._debug('[+] Updating Data To Database Table "{}" Where "{}"'.format(table, where))
            update = self.validate(table, data or {}, action="update")
            if update:
                # Data syntax
                # name = ?, email = ?, ('example', 'example@gmail.com')
                values = List(update.values())
                update = "".join(f"{x} = ?, " for x in update)[:-2]
                
                if where:
                    values += List(where.values())
                    model = self.models[table]
                    where = "WHERE " +  "".join(f"{getattr(model, x).name} = ? AND " for x in where)[:-5]
                else:
                    where = ''
                
                query = "UPDATE %(table)s SET %(update)s %(where)s" %{
                    'table': table,
                    'update': update,
                    'where': where
                }
                self.execute(query, args=values)
                
                self.connection.commit()
                self._debug('[+] Data Updated')
        except Exception as e:
            self._debug('[-] Could Not Update Data In Table "%s" .. The table Might Not Exist' %table)
            self._debug('[INFO]', e)
            self.trigger("error", e)

    def like(self, table, *select, sep="and", **data):
        try:
            self._debug("")
            data  = self.validate(table, data or {}, action="like")
            l = "".join("%s like ? %s "%(x, sep) for x in data)[:-(2+len(sep))]
            select = "*" if not select else ",".join(select)
            query = "select %s from %s where %s"%(select, table, l)
            data = self.execute(query, args=list(data.values()), table=table)
            return data
        except Exception as e:
            self._debug('[-] Could Not Read From Table "%s" .. The table Might Not Exist' %table)
            self._debug('[INFO]', e)
            self.trigger("error", e)

    def delete(self, table, **where):
        try:
            self._debug("")
            where = self.validate(table, where, action="delete")
            if where:
                values = List(where.values())
                model = self.models[table]
                where = "WHERE " + "".join(f"{getattr(model, x).name} = ? AND " for x in where)[:-5]
                
                query = f"DELETE FROM %(table)s %(where)s"%{
                    'table': table,
                    'where': where
                }
                
                self.execute(query, args=values)
                self.connection.commit()
            else:
                self.execute(f"DELETE FROM %s"%table)
                self.connection.commit()
            return True
        except Exception as e:
            self._debug('[INFO]', e)
            self.trigger("error", e)
            return False

    def execute(self, query, args=None, one=False, serialize=True, table=None):
        #try:
        self._debug('[+] Running Query ')
        self.trigger("query", query, args=args)
        # print(query, args)
        if args:
            self.cursor.execute(query, args)
        else:
            self.cursor.execute(query)
        
        self.last_query = query
        self.last_query_args = args
        
        self._debug_('[QUERY]', str(query), args or '')

        data = self.cursor.fetchone() if one else self.cursor.fetchall()
        if serialize:
            data = self.serialize(data, table=table)
        self.last_query_data = data

        self._debug_('[RESPONSE]', data)
        self.connection.commit()
        self._debug('[+] Query Successfully Executed')
        return data
        #except :
#            self._debug('[-] An Error Occured.. Check The Query \n')
#            raise e
    
    def execute_many(self, query, serialize=True):
        try:
            self._debug('[+] Running Query ')
            self.cursor.executescript(str(query))
            data = self.cursor.fetchall()
            if serialize:
                data = self.serialize(data)
            self.connection.commit()
            self._debug('[+] Query Successfully Executed')
            return data
        except Exception as e:
            self._debug('[-] An Error Occured.. Check The Query')
        
    def serialize(self, data, table=None):
        try:
            dic = List()

            def wrap(row):
                # d = {key: val for key, val in zip(row.keys(), row)}
                # if table:
                #     dic.append(self.models[table](**d))
                # else:
                #     dic.append(d)
                if table:
                    model = self.models[table]
                    instance = self.models[table]()
                    for key, val in zip(row.keys(), row):
                        instance.__update_data__(**{key: getattr(self.models[table], model.Meta.__alt_names__.get(key, key)).formatted(val, instance)})
                    dic.append(instance)
                else:
                    d = {key: val for key, val in zip(row.keys(), row)}
                    dic.append(d)

            if isinstance(data, list):
                for row in data:
                    wrap(row)
            elif isinstance(data, sqlite3.Row):
                wrap(data)
            return dic#[0] if len(dic) == 1 else dic
        except Exception as e:
            self._debug('[INFO]', e)
            self.trigger("error", e)
    
    def drop(self, table):
        self.execute(f"DROP {table}")
        self.connection.commit()
    
    def backup(self, target, progress=None):
        if isinstance(target, SqliteDatabase):
            targetconn = target.connection
        else:
            targetconn = target

        with targetconn:
            self.connection.backup(targetconn, pages=0, progress=progress)
    
    def restore(self, source, progress=None):
        if isinstance(source, SqliteDatabase):
            targetconn = source.connection
        else:
            targetconn = source

        targetconn.backup(self.connection, pages=0, progress=progress)

    def _compare(self, old, new):
        added, removed= {}, {}
        if old == new:return {'added': added, 'removed': removed}

        for a in old:
            if a in new and new.get(a) == old.get(a):
                continue
            else:
                removed[a] = old[a]

        for b in new:
            if b in old and old.get(b) == new.get(b):
                continue
            else:
                added[b] = new[b]

        return {'added': added, 'removed': removed}

    def __create(self, model):
        table_name = model.__table_name__()
        db = model.Meta.database

        for key, value in model.__dict__.items():
            if isinstance(value, Column):
                value.setup(self, model)
            elif isinstance(value, BaseObjects):
                value.model = model
                value.db = self

        columns = model.__columns__

        # parent = super(model, model())._columns


        # annotations = model.__dict__.get("__annotations__", {})
        
        # c = set([*annotations, *model.__dict__, *parent])
        # for x in sorted(c):
        #     if not hasattr(model, x):
        #         setattr(model, x, Column(null=False))
        #     data = model.__dict__.get(x) or copy(parent.get(x))

        #     if not x.startswith("_") and isinstance(data, (*list(py_to_sql.keys()), Column)) and x not in ["objects", "_hooks", "_table_name", "db"]:
        #         columns[x] = data
        #         if not isinstance(columns[x], Column):
        #             columns[x] = Column(default=columns[x])

        #         columns[x].type = py_to_sql.get(annotations.get(x, str), annotations.get(x))
        #         columns[x].name = columns[x].name or x
        #         columns[x].bind(model, x)
        #         columns[x].setup(db, model)
        #     elif isinstance(data, BaseObjects):
        #         data.model = model
        #         data.db = db
    
        # if not columns.get("id"):
        #     model.id = Column("integer", primary_key=True, null=False, html_type="integer", name="id")
        #     model.id.bind(model, "id")
        #     model.id.setup(db, model)
        #     columns = dict(id=model.id, **columns)
        
        # model._columns = columns

        old_query = (self._table_sql(table_name)).strip()
        new_query = (f"CREATE TABLE {table_name} (" + ",".join(columns[x]._query() for x in columns) + ")").strip()

        if table_name not in self._tables():
            self.table(table_name, columns)

        if old_query != new_query:
            compare = self._compare(self._columns_(table_name), {x: columns[x].type for x in columns})

            if compare['removed'] != {}:
                # self.drop_column(table_name, compare['removed'])
                # self._debug(f"Removed: {compare['removed']}")
                pass

            if compare['added'] != {}:
                # self.add_column(table_name, {x: columns[x] for x in compare['added']})
                self._debug(f"Added: {compare['added']}")
        self.models[table_name] = model


    def validate(self, table, data, action="create"):
        model = self.models[table]
        columns = model.__columns__

        ret = {}
        for x in columns:
            column = columns[x]
            v = data.get(x)
            c = None

            try:
                c = column.save(v)
                if c is not None:
                    ret[x] = c
            except Exception as e:
                for error in e.args:
                    column.add_error(error)
                raise e

            if action == "create" and not c and (not column.pk and not column.default and not column.null):
                raise AssertionError("No data specified for column '%s.%s'"%(model.__table_name__(), column.name))

        return ret

    def init(self, *models):
        for model in models:
            if not hasattr(model, "db"):
                model.db = self
            if not hasattr(model, "objects"):
                model.objects = BaseObjects()
                model.objects.bind(model, model.db)

            self.__create(model)
            self.trigger("init_model", model)
        return

    def __del__(self):
        self.connection.close()
