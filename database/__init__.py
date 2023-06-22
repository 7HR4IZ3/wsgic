# __all__ = ['Sqlite';Database', 'SqlalchemyDatabase']
if __name__ == "__main__":
    # from wsgic.helpers import config
    from sqlite import *
else:
    from wsgic.helpers import config
    from .sqlite.__init_ import *
    from wsgic.helpers.extra import load_module
import typing
from types import NoneType
from .base import BaseDatabase
# from .sqlalchemy import SqlalchemyDatabase

# class Database:
#     def __init__(self, **kwargs):
#         self.kwargs = kwargs
#         self.path = self.__config("path")
#         self.debug = self.__config("debug")
#         self.verbose = self.__config("verbose")
#         self.config = self.__config("config")
    
#     def __config(self, name, e=None):
#         return self.kwargs.get(name, config.get(name, e))

# db = SqliteDatabase(":memory:")

# @db.on("error")
# def error(e):raise e


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

if typing.TYPE_CHECKING:
    database: typing.Union[NoneType, BaseDatabase]

database = None
databases = {
    "base": BaseDatabase,
    "sqlite": load_module("wsgic.database.sqlite:SqliteDatabase"),
    "mysql": load_module("wsgic.database.mysql:MysqlDatabase", catch_errors=True),
}

if config.get("use.database", True):
    with config.prefix("database"):
        path = config.get("path", "sqlite:///database.sqlite")
        uri, path = path.split("://")

        if uri in databases:
            database = databases[uri](
                path, debug=config.get("debug", False),
                verbose=config.get("verbose", False),
                **config.get("config", {}, True)
            )
