# from helpers import *
# from helpers import _get
import json
from types import GenericAlias
from ..helpers import *
from ..helpers import _get
from ..columns import *

UNDEFINED = object()

types_to_column = {
    str: Column,
    date: DateColumn,
    datetime: DateTimeColumn,
    int: IntegerColumn,
    bytes: BytesColumn
}


class MetaManager:
    objects: BaseObjects

    def __init__(self, meta=None):
        self.__meta = meta
        self.__alt_names__ = {}

    def __getattr__(self, name):
        if self.__meta:
            return getattr(self.__meta, name, None)

def parse_annotation(ann):
    if isinstance(ann, GenericAlias):
        return (ann.__origin__, ann.__args__)
    return (ann, None)


def get_column_from_type(annotation):

    def main(ann):
        ret = types_to_column.get(ann)
        if ret:
            return ret
        else:
            if issubclass(ann, Model):
                return partial(ForeignKeyColumn, ann)
            elif issubclass(ann, Column):
                return ann
        raise TypeError("Invalid type")

    origin, args = parse_annotation(annotation)
    if args:
        if origin == list or origin == List:
            arg = args[0]
            assert issubclass(arg, Model), "Invalid Type."
            return partial(OneToManyColumn, arg)
    else:
        return main(annotation)

    raise TypeError("Invalid type")


class ModelMetaclass(type):
    # @classmethod
    # def __prepare__(metacls, name, bases, **kwds):
    #     return dict()

    def __new__(cls, name, bases, namespace, **kwds):
        # print(cls, name, bases, namespace)
        namespace = dict(namespace)
        namespace["Meta"] = MetaManager(namespace.get("Meta"))
        result = type.__new__(cls, name, bases, namespace)
        if name == "Model":
            return result
        columns = {}
        # print(name, result.Meta.database, result.Meta.database.models)
        # print()
        result.Meta.objects = BaseObjects()
        result.Meta.objects.bind(result, result.Meta.database)

        for base in bases:
            if hasattr(base, "__columns__"):
                columns.update(base.__columns__)

        c = cls.get_columns(result)
        # print(c)
        columns.update(c)
        result.__columns__ = columns
        # print(name, columns)
        # print()
        if not result.Meta.abstract:
            result.Meta.database.init(result)
        return result

    def get_columns(model):
        annotations = model.__dict__.get("__annotations__", {})
        annotation = None
        columns = {}
        # db = getattr(model.Meta, "database", getattr(model, "db", None))

        c = set([*model.__dict__, *annotations])
        for x in sorted(c):
            if x.startswith("__"):
                continue

            data = model.__dict__.get(x)
            if not data and annotations.get(x):
                annotation = annotations.get(x, str)
                column = get_column_from_type(annotation)

                setattr(model, x, column(null=False))
                data = getattr(model, x)

            if isinstance(data, (*list(py_to_sql.keys()), Column)) and x not in ["objects", "_hooks", "_table_name", "db"]:
                columns[x] = data

                if not isinstance(columns[x], Column):
                    annotation = annotations.get(x)
                    if annotation:
                        columns[x] = get_column_from_type(
                            annotation)(default=data)
                        setattr(model, x, columns[x])

                columns[x].type = py_to_sql.get(annotation, columns[x].type)

                if columns[x].name:
                    model.Meta.__alt_names__[columns[x].name] = x
                else:
                    columns[x].name = x
                columns[x].bind(model, x)
                # columns[x].setup(db, model)
            # elif isinstance(data, BaseObjects):
            #     data.model = model
            #     data.db = db

        if not columns.get("id"):
            model.id = IntegerColumn(
                "integer", primary_key=True, null=False, html_type="integer", name="id")
            model.id.bind(model, "id")
            # model.id.setup(db, model)
            columns = dict(id=model.id, **columns)
        return columns


class Model(Hooks, metaclass=ModelMetaclass):
    id: type[int | None]
    objects: BaseObjects

    def __init__(self, **kwargs):
        self.__set_data__(**kwargs)

    def __set_data__(self, **kwargs):
        self.__update_data__(**kwargs)

    def __update_data__(self, **kwargs):
        # print(kwargs, self.__columns__)
        # for key in self.__columns__:
        #     setattr(self, self.Meta.__alt_names__.get(key, key), None)

        for columnname in kwargs:
            column = self.Meta.__alt_names__.get(columnname, columnname)
            if column in self.__columns__:
                d = kwargs.get(column, UNDEFINED)
                if d is UNDEFINED:
                    d = kwargs.get(columnname)
                setattr(self, column, d)
            # To Do... Check if column can provide default value.

    def __init_subclass__(cls, db=None, **kwargs):
        super().__init_subclass__(**kwargs)
        db = db or cls.Meta.database or getattr(cls, "db")
        cls.Meta.database = db
    #     db.init(cls)

    def reload(self):
        kw = {}
        asdict = self.asdict()

        if asdict.get("id"):
            kw["id"] = asdict["id"]
        else:
            kw = asdict

        data = self.Meta.objects.get_one(**kw)
        # print(data)
        if data:
            self.__update_data__(**data.asdict())
        return True

    @classmethod
    def __validation_rules__(cls):
        rules = {}
        for column in cls.__columns__:
            column = cls.__columns__[column]
            rules[column.name] = column.get_validation_rules([])

            if (not column.null or not column.default and not column.pk):
                rules[column.name].insert(0, "required")
        return rules

    @classmethod
    def __validation_context__(cls):
        context = {}
        for column in cls.__columns__:
            column = cls.__columns__[column]
            context = column.get_validation_context(context)
        return context

    @classmethod
    def __table_name__(cls):
        return getattr(cls.Meta, "table_name", None) or cls.__name__

    @classmethod
    def bind(cls, db):
        cls.db = db

    def __repr__(self):
        # return f"%s(id={self.id})"%self.__class__.__name__
        return "%s(%s)" % (self.__class__.__name__, ", ".join(f"{x}={repr(getattr(self, x))}" for x in self.__columns__ if self.__columns__[x].repr))

    def __str__(self):
        return repr(self)

    def __getitem__(self, *args):
        ret = []
        for arg in args:
            ret.append(getattr(self, arg))
        return ret[0] if len(ret) == 1 else ret

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def asdict(self, skip=None):
        skip = skip or []
        data = {}
        for column in self.__columns__:
            if column in skip:
                continue
            d = getattr(self, column)
            if not isinstance(d, Column):
                data[column] = d
        return data

    def serialize(self, skip=None):
        skip = skip or []
        data = {}
        for column in self.__columns__:
            if column in skip:
                continue
            d = getattr(self, column)
            data[column] = self.__columns__[column].serialize(d)
        return data

    def save(self):
        data = self.asdict()
        data.pop("id", None)

        id = getattr(self, "id")

        if id and not isinstance(id, Column):
            self.Meta.objects.update(data, id=self.id)
        else:
            self.Meta.objects.create(**data)
        self.reload()

    def json(self):
        return json.dumps(self.serialize())
