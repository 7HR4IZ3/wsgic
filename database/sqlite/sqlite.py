from wsgic.database.base import BaseDatabase
import sqlite3

class SqliteDatabase(BaseDatabase):
    querykey = "?"

    def __init__(self, path, debug=False, verbose=False, initialize=True, **kwargs):
        kwargs["check_same_thread"] = False
        self.on("connect", self.onconnect)

        super().__init__(path, debug=debug, verbose=verbose, initialize=initialize, connector=sqlite3.connect, **kwargs)
    
    def onconnect(self, connection):
        connection.row_factory = sqlite3.Row

# db = SqliteDatabase(":memory:")

# @db.on("error")
# def error(e):raise e

# from wsgic.database.columns import *
# from wsgic.database.helpers import BaseObjects

# # class SelectColumn(Column):
# #     def __init__(self, *a, options=[], **kw):
# #         super().__init__(*a, **kw)
# #         self.options = options
    
# #     def validate(self, val):
# #         if val in self.options:
# #             return val
# #         return None
    
# #     def form(self, **attrs):
# #         options = [self.h.option("Select %s"%self.name, selected=True)] + [self.h.option(x, value=x) for x in self.options]
# #         return self.h.select(*options, **attrs)

# # class ForeignKeyColumn(Column):
# #     def __init__(self, model, *a, display_columns=None, **kw):
# #         super().__init__(*a, **kw)
# #         self.model = model
# #         self.dc = display_columns
    
# #     def setup(self, db, model):
# #         if isinstance(self.model, str):
# #             try:
# #                 self.model = db.models[self.model]
# #             except LookupError:
# #                 raise ValueError("%s.%s: Database has no model '%s'"%(model.__name__, self.name, self.model))
    
# #     def validate(self, val):
# #         val_id = val.id if hasattr(val, "id") else val
# #         data = self.model.id == val_id
# #         if data:
# #             return val_id
# #         raise ValueError("%s.%s: %s object has no object with id %s"%(self._table.__name__, self.name, self.model.__name__, val_id))
    
# #     def format(self, data):
# #         data = self.model.objects.get(id=data)
# #         if data:
# #             return data[0]

# class DjangoBaseObjects(BaseObjects):
#     def get(self, **kw):
#         assert kw
#         return self.db.get(self.model.__table_name__(), **kw)
    
#     def all(self):
#         return self.db.get(self.model.__table_name__())


# class Role(db.Model):
#     role: str #= SelectColumn(options=["admin", "editor", "user", "superuser"])
#     level: int = Column(null=False)

# class User(db.Model):
#     objects = DjangoBaseObjects()

#     username: str
#     # id: int = db.Column(primary_key=True)
#     role: str = "admin"

#     def get_tag(self):
#         return f"@{self.username.lower()}"

# class AdminUser(User):
#     is_admin: str = "True"

# # users = User()
# Role.objects.create(role="admin", level=100)
# Role.objects.create(role="user", level=50)


# User.objects.create(username="Admin", role=1)
# User.objects.create(username="Thraize")
# User.objects.create(username="Demian", role=1)
# User.objects.create(username="Ian")

# # User.objects.get(where=db.WhereIn(id=[1,2,3]))
# admin = Role.objects.get(id=1).first()
# print(admin)
# # print(User.objects.all(), admin)
# raise Exception