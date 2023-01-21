import math
import re
import uuid

def parse(string, globals={}):
    exec("""
def this(*a, **kw):
    return {'args': a, "kwargs": kw}
ret = this(%s)
""" %string, globals)
    return globals.get("ret", {"args": [], "kwargs": {}})


def _re_flatten(p):
    """ Turn all capturing groups in a regular expression pattern into
        non-capturing groups. """
    if '(' not in p:
        return p
    return re.sub(r'(\\*)(\(\?P<[^>]+>|\((?!\?))', lambda m: m.group(0) if len(m.group(1)) % 2 else m.group(1) + '(?:', p)

class Convertor:
    regex = r""
    to_python = None
    to_url = None

    def __init__(self, config):
        if config:
            self.config = parse(config)
        else:
            self.config = {"args": [], "kwargs": {}}

    def __call__(self):
        return (self.regex, self.to_python, self.to_url)


class StringConvertor(Convertor):
    regex = r"[^/]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        value = str(value)
        assert "/" not in value, "May not contain path separators"
        assert value, "Must not be empty"
        return value


class PathConvertor(Convertor):
    regex = r".+?"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)


class IntegerConvertor(Convertor):
    regex = r"[0-9]+"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        value = int(value)
        assert value >= 0, "Negative integers are not supported"
        return str(value)


class FloatConvertor(Convertor):
    regex = r"[0-9]+(.[0-9]+)?"

    def to_python(self, value):
        return float(value)

    def to_url(self, value):
        value = float(value)
        assert value >= 0.0, "Negative floats are not supported"
        assert not math.isnan(value), "NaN values are not supported"
        assert not math.isinf(value), "Infinite values are not supported"
        return ("%0.20f" % value).rstrip("0").rstrip(".")


class UUIDConvertor(Convertor):
    regex = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

    def to_python(self, value):
        return uuid.UUID(value)

    def to_url(self, value):
        return str(value)

class ReConvertor(Convertor):
    def __init__(self, conf):
        self.regex = _re_flatten(conf or r"[^/]+")

CONVERTORS = {
    "str": StringConvertor,
    "path": PathConvertor,
    "int": IntegerConvertor,
    "float": FloatConvertor,
    "uuid": UUIDConvertor,
    "re": ReConvertor
}

def add_converter(placeholder, convertor):
    assert isinstance(convertor, Convertor) or (hasattr(convertor, "to_url"), hasattr(convertor, "to_python"), hasattr(convertor, "regex"))
    CONVERTORS[placeholder] = convertor

def get_convertors():
    return CONVERTORS
