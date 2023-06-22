import io
import json
import os
import re

from datetime import datetime, date
from copy import copy

from wsgic.thirdparty.bottle import makelist
from wsgic.views import render
from wsgic.handlers.files import File, FileUpload, ImageFile, FileSystemStorage
from wsgic.http import request
from wsgic.routing import route
from wsgic.utils import conditional_kwargs

try:
    from PIL import Image
except ImportError:
    Image = None


from ..helpers import sql_to_form, List, py_to_sql, sql_to_py
from wsgic.services.validation import BaseFilters

try:
    from wsgic.ui import builder as formify
except ImportError:
    formify = None

class ColumnFilters(BaseFilters):
    pass

class Column:
    type = "text"
    default = False
    null = None
    html_type = None
    html_attrs = None
    no_label = False
    validators = None
    formatters = None
    
    def __init__(self, type=None, null=True, default=None, primary_key=None, unique=False, repr=True, name=None, max_length=None, label=None, html_type=None, html_attrs=None, helper_text=None, validators=None, formatters=None, serialize=None):
        self.type = type or self.type
        if not isinstance(self.type, str):
            self.type = py_to_sql.get(self.type)
        self.__error = []
        self.null = self.null or null
        self.default = default or self.default

        self.unique = unique
        self.pk = primary_key
        self.repr = repr
        self.name = name
        self.max_length = max_length
        self.helper_texts = makelist(helper_text)
        self.validators = (validators or []) + (self.validators or [])
        self.formatters = (formatters or []) + (self.formatters or [])
        self.serialize = serialize or self.serialize
        assert callable(self.serialize)

        self.h = formify.HTML() if formify else None
        self.html_attrs = html_attrs or self.html_attrs or {}
        self.__html_type = html_type or self.html_type or "text"
        self.__label = label
        
        self._table = None
    
    # def __setattr__(self, name, value):
    #     if hasattr(self, name):
    #         print(f"Overiding attribute {name} of {self.__class__.__name__}")
    #     return super().__setattr__(name, value)

    def errors(self):
        data = copy(self.__error)
        self.__error = []
        return data
    
    def add_error(self, message):
        self.__error.append(message)
    
    def has_error(self):
        return self.__error != []
    
    def get_label(self):
        return (self.__label or self.name)
    
    def get_html_type(self):
        return sql_to_form(self.__html_type or self.type)
    
    def get_attrs(self):
        return self.html_attrs
    
    def get_validation_rules(self, rules):
        if self.max_length:
            rules.append(f"max_length({self.max_length})")
        return rules
    
    def get_validation_context(self, context):
        return context
    
    @property
    def is_required(self):
        return (not self.pk and (self.default == None) and (self.null == False))
    
    def bind(self, model, name):
        # setattr(model, name, self)
        setattr(self, "_table", model)
    
    def validate(self, val):
        return val
        # except:
        #     return None
    
    def serialize(self, data):
        return str(data)
    
    def format(self, val):
        try:
            return sql_to_py.get(self.type)(val)
        except:
            return None
    
    def save(self, data):
        if data is None:
            return data
        if self.max_length:
            try:
                length = len(data)
            except:
                length = None
            if length:
                if length > self.max_length:
                    raise ValueError("%s.%s value exceeds max length"%(self._table.__name__, self.name))
        data = self.validate(data)
        for item in self.validators:
            try:
                data = getattr(item, "apply", item)(data)
            except Exception as e:
                for error in e.args:
                    self.add_error(error)
        return data
    
    def formatted(self, data, model):
        if not self.is_required:
            if data is None:return data

        data = conditional_kwargs(self.format, {"model": model})(data)
        for item in self.formatters:
            data = conditional_kwargs(getattr(item, "apply", item), {"model": model})(data)
        return data
    
    def setup(self, db, model):
        [x.setup(self) for x in self.validators if hasattr(x, "setup")]
        [x.setup(self) for x in self.formatters if hasattr(x, "setup")]
    
    def form(self, **attrs):
        if self.max_length:
            attrs['maxlength'] = self.max_length
        return self.h.input(type=self.get_html_type(), **attrs)
    
    def to_str(self, attrs):
        ret = "".join(f"{x}={attrs[x]} " if attrs[x] != True else f"{x}" for x in attrs).strip()
        return ret
    
    def _dtype(self):
        null = ' NOT NULL' if not self.null else ''

        if self.default:
            self.default = self.save(self.default)
        default = (f' DEFAULT "{self.default}"' if isinstance(self.default, str) else f' DEFAULT {self.default}') if self.default else ''
        unique = " UNIQUE" if (self.unique or self.pk) else ""
        type = f'{self.type} primary key' if self.pk else self.type
        
        return f'{type}{null}{default}{unique}'

    def _query(self):
        q = f'"{self.name}" {self._dtype()}'
        return q
    
    def __eq__(self, other):
        data = self._table.objects.get(**{self.name: other})
        return List(data)

    def contains(self, word):
        ret = List()
        for x in self._table.objects.get():
            if word in x[self.name]:
                ret.append(x)
        return ret
    
    def match(self, value: str):
        ret = List()
        for x in self._table.objects.get():
            if re.search(value, x[self.name]):
                ret.append(x)
        return ret
    
    def like(self, word):
        data = self._table.objects.like(self._name, word)
        return List(data)

    def __lt__(self, value):
        ret = List()
        for x in self._table.objects.get():
            if x[self.name] < value:
                ret.append(x)
        return ret

    def __gt__(self, value):
        ret = List()
        for x in self._table.objects.get():
            if x[self.name] > value:
                ret.append(x)
        return ret

    def __le__(self, value):
        return List(
            [*self.__lt__(value), *self.__eq__(value)]
        )

    def __ge__(self, value):
        return List(
            [*self.__gt__(value), *self.__eq__(value)]
        )


class SelectColumn(Column):
    def __init__(self, *a, options=[], form=True, **kw):
        super().__init__(*a, **kw)
        self.options = options
        self.useform = form
    
    def get_validation_rules(self, rules):
        rules.append(f"in_choices(*select_choices_{self.name})")
        return rules
    
    def get_validation_context(self, context):
        context[f"select_choices_{self.name}"] = self.options
        return context
    
    def validate(self, val):
        if val in self.options:
            return val
        raise ValueError("%s.%s value must be in the specified options"%(self._table.__name__, self.name))
    
    def form(self, **attrs):
        selected = attrs.pop('value', None)
        options = [self.h.option("Select %s"%self.name, selected=True)] + [self.h.option(x, value=x, selected=selected == x) for x in self.options]
        return self.h.select(*options, **attrs)

class BackRef:
    def __init__(self, parent):
        self.par = parent
        if hasattr(parent, "Meta"):
            self.par = parent.Meta.table_name

        # super().__init__(null=True, label="")
        self.form = lambda *a, **k: ""
        self.formatted = self.save = lambda d, *a: d

class QuillEditorColumn(Column):
    type = str

    def __init__(self, *a, editor="full", config=None, **kw):
        super().__init__(*a, **kw)
        self.editor = editor
        self.config = config or ({
                "theme": "snow"
            } if self.editor != 'bubble' else {
                'theme': 'bubble'
            })
    
    def form(self, **attrs):
        attrs['rows'] = 5
        return render("admin/formeditor.html", attrs=attrs, editorconfig=json.dumps(self.config))

class RichTextColumn(Column):
    type = str

    def __init__(self, editor="classic", config=None, *a, **kw):
        super().__init__(*a, **kw)
        self.editor = editor
        assert editor in ["classic", "inline", "bubble", "document"]
        self.config = config or {}
    
    def form(self, **attrs):
        return render("ckeditor.html", attrs=attrs, editorconfig=json.dumps(self.config), editor=self.editor)

class RegexColumn(Column):
    type = str
    html_type = "email"

    def __init__(self, pattern, *a, invalid="Invalid regex", **kw):
        self.pattern = pattern
        self._msg = invalid
        super().__init__(*a, **kw)
    
    def get_validation_rules(self, rules):
        rules.append("contains('@')")
        return rules

    def validate(self, data):
        if re.match(self.pattern, data):
            return data
        raise ValueError(self._msg.format(table=self._table.__name__, column=self.name))

class EmailColumn(RegexColumn):
    type = str
    html_type = "email"

    def __init__(self, *a, **kw):
        super().__init__(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", *a, invalid="Invalid Email address", **kw)

class UrlColumn(RegexColumn):
    type = str
    html_type = "url"

    def __init__(self, *a, **kw):
        super().__init__(r"^htt[ps | p]?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$", *a, invalid="Invalid url address", **kw)

class UUIDColumn(RegexColumn):
    type = str
    html_type = "text"

    def __init__(self, *a, **kw):
        super().__init__(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}$", *a, invalid="Invalid UUID", **kw)

class IpAddressColumn(RegexColumn):
    type = str
    html_type = "text"

    def __init__(self, type="ipv4", *a, **kw):
        type = type.lower()
        assert type in ("ipv4", "ipv6")
        if type == "ipv4":
            super().__init__(r"^(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", *a, invalid="Invalid ipv4 address", **kw)
        else:
            super().__init__(r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$", *a, invalid="Invalid ipv6 address", **kw)

class BytesColumn(Column):
    type = bytes
    html_type ="text"

    def __init__(self, encoding="utf-8", *a, **kw):
        super().__init__(*a, **kw)
        self.enc = encoding
    
    def format(self, data):
        try:
            return data.decode(self.enc)
        except:
            return data
        
    def get_validation_rules(self, rules):
        name = self.name
        rules.append(f"isinstance(str) ? custom(bytes, enc_{name}) : isinstance(bytes) ? true : custom(bytes)")
        return rules
    
    def get_validation_context(self, context):
        name = self.name
        context[f"enc_{name}"] = self.enc
        return context
    
    def validate(self, data):
        try:
            data = bytes(data, self.enc) if isinstance(data, str) else bytes(data) if not isinstance(data, bytes) else data
            return data
        except:
            raise ValueError("%s.%s value can't be converted to bytes"%(self._table.__name__, self.name))

class DateColumn(Column):
    type = date

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
    
    def get_validation_rules(self, rules):
        name = self.name
        rules.append(f"isinstance(date) ? custom(func_{name}) : custom(func2_{name})")
        return rules
    
    def get_validation_context(self, context):
        name = self.name

        context["date"] = date
        context[f"func_{name}"] = lambda x: x.isoformat()
        context[f"func2_{name}"] = lambda x: date.fromisoformat(x)
        return context
    
    def validate(self, val):
        try:
            if isinstance(val, date):
                return val.isoformat()
            else:test = date.fromisoformat(val)
            return val
        except ValueError as e:
            print(e)
            raise ValueError("%s.%s value must be an instance of 'date' or datetime isoformat string"%(self._table.__name__, self.name, self.type))
    
    def format(self, val):
        return date.fromisoformat(val)
    
    def form(self, **attrs):
        if "value" in attrs:
            if isinstance(attrs["value"], date):
                attrs['value'] = attrs['value'].isoformat(timespec="seconds")
        return self.h.input(type="date", **attrs) 

class DateTimeColumn(Column):
    type = datetime

    def validate(self, val):
        try:
            if isinstance(val, datetime):
                return val.isoformat()
            else:test = datetime.fromisoformat(str(val))
            return val
        except ValueError as e:
            raise ValueError("%s.%s value must be an instance of 'datetime' or datetime isoformat string"%(self._table.__name__, self.name, self.type))
    
    def get_validation_rules(self, rules):
        name = self.name
        rules.append(f"isinstance(datetime) ? custom(func_{name}) : custom(func2_{name})")
        return rules
    
    def get_validation_context(self, context):
        name = self.name
        
        return dict(context, **{
            "datetime": datetime,
            f"func_{name}": lambda x: x.isoformat(),
            f"func2_{name}": lambda x: datetime.fromisoformat(x)
        })
    
    def format(self, val):
        return datetime.fromisoformat(val)
    
    def form(self, **attrs):
        if "value" in attrs:
            if isinstance(attrs["value"], datetime):
                attrs['value'] = attrs['value'].isoformat(timespec="seconds")
        return self.h.input(type="datetime-local", **attrs) 

class IntegerColumn(Column):
    type = "integer"

    def __init__(self, *a, min=None, max=None, **kw):
        super().__init__(*a, **kw)
        self.min = min
        self.max = max
        if self.min is not None:
            self.html_attrs['min'] = self.min
        if self.max is not None:
            self.html_attrs['max'] = self.max
    
    def get_validation_rules(self, rules):
        name = self.name
        if self.min is not None:
            rules.append(f"min_value(min_{name})")
        if self.max is not None:
            rules.append(f"max_value(max_{name})")
        return rules
    
    def get_validation_context(self, context):
        name = self.name
        return dict(context, **{
            f"min_{name}": self.min,
            f"max_{name}": self.max
        })
    
    def validate(self, val):
        val = int(val)
        if self.min is not None:
            if val < self.min:
                raise ValueError("%s.%s value exceeds the minimum limit"%(self._table.__name__, self.name))
        if self.max is not None:
            if val > self.max:
                raise ValueError("%s.%s value exceeds the maximum limit"%(self._table.__name__, self.name))
        return val

class BooleanColumn(Column):
    type = int
    html_type = "checkbox"
    no_label = True
            
    def get_validation_rules(self, rules):
        name = self.name
        rules.append("in_choices(False, True, 'off', 'on')")
        return rules
    
    def get_validation_context(self, context):
        name = self.name
        return context

    def validate(self, val):
        if val in (False, "off"):
            return 0
        elif val in (True, "on"):
            return 1
        raise ValueError("%s.%s value must be boolean"%(self._table.__name__, self.name))
    
    def format(Self, data):
        if data == 1:
            return True
        elif data == 0:
            return False
    
    def form(self, **attrs):
        attrs["class"] = "form-check-input"
        if attrs.pop("value", None):
            attrs["checked"] = True
        return self.h.div(self.h.div(
                self.h.label(self.get_label()),
                self.h.input(type=self.get_html_type(), **attrs)
            ), class_="form-check"
        )

class JSONColumn(Column):
    type = str

    def __init__(self, *a, dumpconfig={"indent": 2}, loadconfig={}, **kw):
        super().__init__(*a, **kw)
        self.dumpconfig = dumpconfig
        self.loadconfig = loadconfig
    
    def validate(self, val):
        if isinstance(val, (dict, list)):
            return json.dumps(val, **self.dumpconfig)
        raise ValueError("%s.%s value must be json serializable"%(self._table.__name__, self.name))
    
    def get_validation_rules(self, rules):
        name = self.name
        rules.append("isinstance((list, dict))")
        return rules
    
    def format(self, data):
        return json.loads(data)
    
    def form(self, **attrs):
        value = attrs.pop("value", "")
        return f"""<input type="text" {self.to_str(attrs)} value='{value}' />"""

class FileColumn(Column):
    store: FileSystemStorage
    html_type = "file"
    
    def __init__(self, store, extensions=None, multiple=False, display_text=None, default=None, *a, **kw):
        if default:
            default = store.get(default)
        super().__init__(*a, default=default, **kw)
        self.store = store
        self.is_multiple = multiple
        self.extensions = tuple(extensions) if extensions else None
        self.display_text = ("Choose Files" if multiple else "Choose File") if not display_text else display_text
        if self.is_multiple:
            self.html_attrs["multiple"] = True
    
    def setup(self, db, model):
        super().setup(db, model)
        if isinstance(self.default, str):
            self.default = self.store.get(self.default)
    
    def validate(self, file):
        files = makelist(file)
        ret = []
        for file in files:
            if isinstance(file, str):
                file = self.store.get(file)
            item = file

            filename = getattr(item, "filename", item.name)
            
            if not isinstance(file, (FileUpload, File, io.IOBase)):
                raise ValueError("%s.%s value must be of instance File or FileUpload"%(self._table.__name__, self.name))

            if isinstance(file, FileUpload):
                file = file.file
            
            if filename == "empty":
                continue

            name, ext = os.path.splitext(filename)
            ext = ext.lstrip().lstrip(".")
            if self.extensions:
                if ext not in self.extensions:
                    raise ValueError("%s.%s value's extension '%s' is not in allowed extension"%(self._table.__name__, self.name, ext))
            
            data = b""
            offset = file.tell()
            while True:
                buf = file.read(2 ** 16)
                if not buf:
                    break
                data = data + buf
            file.seek(offset)
            self.store.save(getattr(item, "filename", item.name), data)
            ret.append(getattr(item, "filename", item.name))
        return ",".join(ret) if ret else None
    
    def format(self, val, file=File):
        files = val.split(",")
        ret = []
        for item in files:
            data = self.store.get(item, filebuffer=True)
            ret.append(file(data, data.name, store=self.store))
        if not self.is_multiple:
            if len(ret) == 1:
                return ret[0]
        return ret
    
    def form(self, **attrs):
        value = attrs.pop("value", None)
        attrs["class"] = "form-file-input"
        return self.h.div(
            self.h.input(type="file", **attrs),
            self.h.label(
                self.h.span(self.display_text, class_="form-file-text"),
                self.h.span(
                    self.h.i(data_feather="upload"),
                    class_="form-file-button btn-primary ml-3"
                ),
                class_="form-file-label"
            ),
            class_="form-file"
        )

class ImageColumn(FileColumn):
    html_attrs = {
        "accept": "image/*"
    }

    def format(self, val):
        return super().format(val, file=ImageFile)

class ForeignKeyColumn(Column):
    type = int

    def __init__(self, model, *a, display_columns=None, backref=None, **kw):
        super().__init__(*a, **kw)
        self.model = model
        self.dc = display_columns
        self.bckref = backref
    
    def setup(self, db, model):
        super().setup(db, model)
        if isinstance(self.model, str):
            try:
                self.model = db.models[self.model]
            except LookupError:
                raise ValueError("%s.%s: Database has no model '%s'"%(model.__name__, self.name, self.model))
    
    def get_validation_rules(self, rules):
        name = self.name
        rules.append(f"custom(check_{name}) ? false : custom(func_{name})")
        return rules
    
    def get_validation_context(self, context):
        name = self.name
        context[f"check_{name}"] = lambda x: str(x).startswith("Select %s"%name),
        context[f"func_{name}"] = self.validate_id
        return context
    
    def validate_id(self, val):
        val_id = val.id if hasattr(val, "id") else val
        data = self.model.id == val_id
        if data:
            return val_id
        return False
    
    def validate(self, val):
        if str(val).startswith("Select %s"%self.name):
            return None
        val_id = getattr(val, "id", val)
        data = self.model.id == val_id
        if data:
            return val_id
        raise ValueError("%s.%s: %s object has no object with id %s"%(self._table.__name__, self.name, self.model.__name__, val_id))

    def format(self, data, model):
        data = self.model.objects.get(id=data)
        if data:
            if self.bckref:
                column = model.__columns__.get(self.bckref, None)
                if column and isinstance(column, BackRef):
                    parent = column.par
                    if parent == self._table.__name__:
                        setattr(data[0], self.bckref, model)
                    else:raise Exception("Not Valid Parent")
                else:raise Exception("Backref is is not an instance of BackRef")
            return data[0]
    
    def form(self, **attrs):
        selected = attrs.pop('value', None)
        if isinstance(selected, str):
            if selected.startswith("Select %s"%self.name):
                return None
            selected = self.model.objects.get(id=int(selected))[0]
        options = [
            self.h.option("Select %s"%self.name, value="", selected=True)
        ] + [self.h.option(
                f"{str(x)} ",
                value=x.id, 
                selected=(selected.id == x.id) if selected else False
            ) for x in self.model.objects.get()]
        return self.h.div(
            self.h.select(*options, **attrs),
            self.h.div(
                self.h.a("+", class_="btn btn-primary", href=route("admin_single", url=self.model.admin_url, query={"next": request.path, "popup": "true"})),#, onclick="window.open(this.href, '_blank', 'resizeable=true, width=500, height=700'); return false"),
                class_="input-group-append ml-3"
            ), class_="input-group"
        )

class OneToManyColumn(Column):
    def __init__(self, model, *a, backref=None, **kw):
        super().__init__(*a, **kw)
        self.model = model
        self.bckref = backref

    def format(self, data, model):
        ret = List()
        if data:
            for id in data.split(","):
                item = self.model.objects.get_one(id=int(id))
                if item:
                    if self.bckref:
                        column = model.__columns__.get(self.bckref, None)
                        if isinstance(column, BackRef):
                            parent = column.par
                            if parent == self._table.__name__:
                                setattr(item, self.bckref, model)
                            else:raise Exception("Not Valid Parent")
                        else:raise Exception(f"{column} is is not an instance of BackRef or is not defined.")
                    ret.append(item)
        return ret

    def validate(self, data):
        return ",".join(str(int(getattr(x, "id", x))) for x in data)
    
    def get_validation_rules(self, rules):
        name = self.name
        rules.append("isinstance(list)")
        return rules
    
    def form(self, **attrs):
        value = [getattr(x, "id", x) for x in attrs.pop("value", [])]
        
        return self.h.div(
            self.h.select(
                self.h.optgroup(
                    *[self.h.option(str(x), value=f"{x.id}", selected=(True if x.id in value else False)) for x in self.model.objects.get()], label="Select "+self.name
                ), class_="choices form-select multiple-remove", multiple="multiple", **attrs
            ), self.h.div(
                self.h.a("+", class_="btn btn-primary", href=route("admin_single", url=self.model.admin_url, query={"next": request.path, "popup": "true"})),#, onclick="window.open(this.href, '_blank', 'resizeable=true, width=500, height=700'); return false"),
                class_="input-group-append ml-3"
            ), class_="form-group"
        )
