# import json
# from ..helpers import List

# class Query:
#     placeholder = "?"

#     def create(self, table, **data):
#         if data:
#             # Data syntax
#             # ('test', 'test@test.com')
#             data = self.validate(table, data, action="create")

#             columns = List(data.keys())
            
#             query = "INSERT INTO %(table)s (%(columns)s) VALUES (%(qmarks)s)" %{
#                 'table': table,
#                 'columns': ','.join(columns),
#                 'qmarks': str(f'{self.placeholder}, ' * len(columns))[:-2]
#             }
#             self.execute(query, args=List(data.values()))

#             self.connection.commit()

#     def get(self, table, *select, as_json=False, **where):
#         if not select:
#             select = ("*",)
        
#         where = self.validate(table, where, action="read")

#         if where:
#             values = List(where.values())
#             where = "WHERE " +  "".join(f"{x} = {self.placeholder} AND " for x in where)[:-5]
#         else:
#             where = ''
#             values = []
#         query = "SELECT %(select)s FROM %(table)s %(where)s" % {
#                 'select': ','.join(select),
#                 'table': table,
#                 'where': where
#             }

#         data = self.execute(query, args=values, table=table)

#         if as_json:
#             data = json.dumps(data)
#         return data


#     def update(self, table, data=None, **where):
#         update = self.validate(table, data or {}, action="update")
#         if update:
#             # Data syntax
#             # name = {self.placeholder}, email = {self.placeholder}, ('example', 'example@gmail.com')
#             values = List(update.values())
#             update = "".join(f"{x} = {self.placeholder}, " for x in update)[:-2]
            
#             if where:
#                 values += List(where.values())
#                 where = "WHERE " +  "".join(f"{x} = {self.placeholder} AND " for x in where)[:-5]
#             else:
#                 where = ''
            
#             query = "UPDATE %(table)s SET %(update)s %(where)s" %{
#                 'table': table,
#                 'update': update,
#                 'where': where
#             }
#             self.execute(query, args=values)
            
#             self.connection.commit()


#     def like(self, table, *select, sep="and", **data):
#         data  = self.validate(table, data or {}, action="like")
#         l = "".join(f"%s like {self.placeholder} %s "%(x, sep) for x in data)[:-(2+len(sep))]
#         select = "*" if not select else ",".join(select)
#         query = "select %s from %s where %s"%(select, table, l)
#         data = self.execute(query, args=list(data.values()), table=table)
#         return data


#     def delete(self, table, **where):
#         where = self.validate(table, where, action="delete")
#         if where:
#             values = List(where.values())
#             where = "WHERE " + "".join(f"{x} = {self.placeholder} AND " for x in where)[:-5]
            
#             query = f"DELETE FROM %(table)s %(where)s"%{
#                 'table': table,
#                 'where': where
#             }
            
#             self.execute(query, args=values)
#             self.connection.commit()
#         else:
#             self.execute(f"DELETE FROM %s"%table)
#             self.connection.commit()
#         return True

from pypika.queries import Query as _Query

class Query(_Query):
    def __get__(self, obj, type=None):
        print(str(self))

q = Query().from_("users").select("*")
print(q)