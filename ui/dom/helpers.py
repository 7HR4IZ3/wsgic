"""
    domonic.webapi.url
    ====================================
    https://developer.mozilla.org/en-US/docs/Web/API/URL

    # TODO - move the unit tests for this class from javascript to webapi
    # TODO - untested

"""
from re import sub
import urllib

class URL:
    """a-tag extends from URL"""

    def __update__(self):
        # print( "update URL:", type(self), self  )
        try:
            # make obj with all old props
            new = {}
            new["protocol"] = self.url.scheme
            new["hostname"] = self.url.hostname
            new["href"] = self.url.geturl()
            new["port"] = self.url.port
            new["host"] = ""  # self.url.hostname
            new["pathname"] = self.url.path
            new["hash"] = ""  # self.url.hash
            new["search"] = ""  # self.url.hash

            # update it with all the new ones
            new = {}
            new["protocol"] = self.protocol
            new["hostname"] = self.hostname
            new["href"] = self.href
            new["port"] = self.port
            new["host"] = self.host
            new["pathname"] = self.pathname
            new["hash"] = self.hash  # self.hash
            new["search"] = self.search  # self.url.query
            new["_searchParams"] = self._searchParams  # URLSearchParams(self.url.query)
            # NOTE - rebuild happening here
            self.url = urllib.parse.urlsplit(
                new["protocol"] + "://" + new["host"] + new["pathname"] + new["hash"] + new["search"]
            )

            self.href = self.url.geturl()

        except Exception:  # as e:
            # print('fails on props called by init as they dont exist yet')
            # print(e)
            pass

    def __init__(self, url: str = "", *args, **kwargs):  # TODO - relative to
        """URL

        builds a url

        Args:
            url (str): a url
        """
        self.url = urllib.parse.urlsplit(url)
        self.href = url  # self.url.geturl()
        self.protocol = self.url.scheme
        self.hostname = self.url.hostname
        self.port = self.url.port
        self.host = self.url.hostname
        self.pathname = self.url.path
        self.hash = ""
        self.search = self.url.query
        self._searchParams = URLSearchParams(self.url.query)

    @property
    def searchParams(self):
        return self._searchParams.toString()

    def toString(self):
        return str(self.href)

    # def toJson

    # @property
    # def href(self):
    # TODO - check js vs tag. does js version remove query?. if so detect self.
    #     return self.href

    # @href.setter
    # def href(self, href:str):
    #     self.url = href
    #     self.href = href

    @property
    def protocol(self):
        return self.__protocol

    @protocol.setter
    def protocol(self, p: str):
        self.__protocol = p
        # if self.ready : self.__update__() # TODO - this instead of silent err?
        self.__update__()

    @property
    def hostname(self):
        return self.__hostname

    @hostname.setter
    def hostname(self, h: str):
        if h is None:
            return
        if ":" in h:
            h = h.split(":")[0]
        self.__hostname = h
        self.__update__()

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, p: str):
        self.__port = p
        self.__update__()

    @property
    def host(self):
        if self.port is not None:
            return self.hostname + ":" + str(self.port)
        else:
            return self.hostname

    @host.setter
    def host(self, h: str):
        if h is None:
            return
        p = self.port
        if ":" in h:
            p = int(h.split(":")[1])
            h = h.split(":")[0]
        self.__host = h
        self.hostname = h
        self.port = p
        self.__update__()

    @property
    def pathname(self):
        return self.__pathname

    @pathname.setter
    def pathname(self, p: str):
        self.__pathname = p
        self.__update__()

    @property
    def hash(self):
        """ " hash Sets or returns the anchor part (#) of a URL"""
        if "#" in self.href:
            return "#" + self.href.split("#")[1]
        # return ''
        return self.__hash

    @hash.setter
    def hash(self, h: str):
        self.__hash = h
        self.__update__()

        # @property
        # def origin(self):
        """# origin    Returns the protocol, hostname and port number of a URL Location"""

    def __str__(self):
        return str(self.href)

    # NOTE - node -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # @staticmethod
    # def domainToASCII(domain: str):
    #     """[It returns the Punycode ASCII serialization of the domain.
    #     If domain is an invalid domain, the empty string is returned.]

    #     Args:
    #         domain (str): [description]
    #     """
    #     pass

    # @staticmethod
    # def domainToUnicode(domain: str):
    #     """[returns the Unicode serialization of the domain.
    #     If the domain is invalid, the empty string is returned]

    #     Args:
    #         domain (str): [description]
    #     """
    #     pass

    # @staticmethod
    # def fileURLToPath(url: str):
    #     """[ensures the correct decodings of percent-encoded characters as well as
    #     ensuring a cross-platform valid absolute path string.]

    #     Args:
    #         url (str): [The fully-resolved platform-specific file path.]
    #     """
    #     if url is None:
    #         return
    #     return urllib.parse.unquote(url)

    # @staticmethod
    # def format(URL, options):
    #     """[summary]

    #     Args:
    #         URL ([type]): [description]
    #         options ([type]): [description]
    #     """
    #     pass

    # @staticmethod
    # def pathToFileURL(path: str):
    #     """[summary]

    #     Args:
    #         path (str): [description]
    #     """
    #     pass

    # @staticmethod
    # def urlToHttpOptions(url: str):
    #     """[summary]

    #     Args:
    #         url (str): [description]
    #     """
    #     pass


class URLSearchParams:
    """[utility methods to work with the query string of a URL]"""

    def __init__(self, paramString):  # , **paramsObj):
        """[Returns a URLSearchParams object instance.]

        Args:
            paramString ([type]): [ i.e. q=URLUtils.searchParams&topic=api]
        """
        # TODO - escape
        # import ast
        # TODO - dont think i can do this cant urls params have duplicate keys?
        # self.params = ast.literal_eval(paramString)
        if isinstance(paramString, str):
            if paramString.startswith("?"):
                paramString = paramString[1 : len(paramString)]

            import urllib

            self.params = urllib.parse.parse_qs(paramString)
        elif hasattr(paramString, "__iter__"):
            self.params = [item for sublist in paramString for item in sublist]
        elif isinstance(paramString, dict):
            # self.params = dict([(key, item) for key, item in paramString.iteritems()])
            self.params = {key: item for key, item in paramString.iteritems()}
        else:
            raise TypeError(
                f"Malformed paramString.  Must be a string or a dict with dict like items. Got: {paramString}"
            )

    def __iter__(self):
        for attr in self.params.items():  # dir(self.params.items()):
            # if not attr.startswith("__"):
            yield attr

    def append(self, key, value):
        """Appends a specified key/value pair as a new search parameter"""
        # TODO - ordereddict?
        self.params[key].append(value)  # [key]=value

    def delete(self, key):
        """Deletes the given search parameter, and its associated value, from the list of all search parameters."""
        del self.params[key]

    def has(self, key):
        """Returns a Boolean indicating if such a given parameter exists."""
        return key in self.params

    def entries(self):
        """Returns an iterator allowing iteration through all key/value pairs contained in this object."""
        return self.params.items()

    def forEach(self, func):
        """Allows iteration through all values contained in this object via a callback function."""
        for key, value in self.params.items():
            func(key, value)

    def keys(self):
        """Returns an iterator allowing iteration through all keys of the key/value pairs contained in this object."""
        return self.params.keys()

    def get(self, key):
        """Returns the first value associated with the given search parameter."""
        try:
            return self.params.get(key, None)[0]
        except Exception:
            return None

    def sort(self):
        """Sorts all key/value pairs, if any, by their keys."""
        self.params.sort()

    def values(self):
        """Returns an iterator allowing iteration through all values of the key/value pairs
        contained in this object."""
        return self.params.values()

    def toString(self):
        """Returns a string containing a query string suitable for use in a URL."""
        # return '&'.join([str(x) for x in self.params])
        return urllib.parse.urlencode(self.params, doseq=True)
        # return str(self.params)

    def set(self, key, value):
        """Sets the value associated with a given search parameter to the given value.
        If there are several values, the others are deleted."""
        self.params[key] = value

    def getAll(self, key):
        """Returns all the values associated with a given search parameter."""
        return self.params.get(key)

    def __str__(self):
        return urllib.parse.urlencode(self.params, doseq=True)

"""
    domonic.webapi.xpath
    ====================================
    https://developer.mozilla.org/en-US/docs/Glossary/XPath

    uses elementpath lib.

    TODO - content strings must be TextNodes for it to work.
        so will have to iterate and update them. i.e. Treewalker

"""

from typing import Any, Callable, Dict, List, Optional, Union

import elementpath


class XPathEvaluator:
    def __init__(self) -> None:
        pass

    def createExpression(self, expression: str):  # , namespaces: Dict[str, str]) -> None:
        return XPathExpression(expression)


class XPathException:
    def __init__(self) -> None:
        pass


class XPathExpression:
    def __init__(self, expr: str):  # , resolver):

        # TODO - hack.
        # need to allow non underscore accessors to get underscored.
        # when that's fixed can remove this.
        expr = expr.replace("[@", "[@_")
        expr = expr.replace("[@__", "[@_")
        expr = expr.replace("(@", "(@_")
        expr = expr.replace("(@__", "(@_")
        expr = expr.replace("/@", "/@_")
        expr = expr.replace("/@__", "/@_")

        if len(expr) <= 0:
            raise Exception("no expression")
        self.selector = elementpath.Selector(expr)

    # TODO - DRY - make some utils . just stole this from Treewalker.
    @staticmethod
    def _upgrade_dom(node):
        def upgrade(el):
            from domonic.dom import Text

            if isinstance(el, (Text, str)):
                return
            for child in el:
                if isinstance(child, str):
                    newchild = Text(child)
                    el.replaceChild(newchild, child)
                    newchild.parentNode = el

        node._iterate(node, upgrade)
        return node

    def evaluate(self, node, type=6):  # XPathResult.ANY_TYPE):
        # note: otherwise would fail on regular text?
        node = XPathExpression._upgrade_dom(node)
        return XPathResult(self.selector.select(node), type)


class XPathNSResolver:
    def __init__(self) -> None:
        pass


class XPathResult:

    ANY_TYPE = 0
    NUMBER_TYPE = 1
    STRING_TYPE = 2
    BOOLEAN_TYPE = 3
    UNORDERED_NODE_ITERATOR_TYPE = 4
    ORDERED_NODE_ITERATOR_TYPE = 5
    UNORDERED_NODE_SNAPSHOT_TYPE = 6
    ORDERED_NODE_SNAPSHOT_TYPE = 7
    ANY_UNORDERED_NODE_TYPE = 8
    FIRST_ORDERED_NODE_TYPE = 9

    def __init__(self, value, _type):
        if _type == XPathResult.ANY_TYPE:
            tov = type(value)
            if tov == "object":
                _type = self.UNORDERED_NODE_ITERATOR_TYPE
            if tov == "boolean":
                _type = self.BOOLEAN_TYPE
            if tov == "string":
                _type = self.STRING_TYPE
            if tov == "number":
                _type = self.NUMBER_TYPE

        if _type < self.NUMBER_TYPE or self.FIRST_ORDERED_NODE_TYPE < _type:
            raise Exception(f"unknown type: {_type}")

        self.resultType = _type

        if _type == self.NUMBER_TYPE:
            # self.numberValue=value.number() if getattr(value,'isNodeSet',None) else toNumber(value)
            if getattr(value, "isNodeSet", None):
                self.numberValue = value  # .number()
            else:
                self.numberValue = float(value)
        elif _type == self.STRING_TYPE:
            # self.stringValue=value.string() if getattr(value,'isNodeSet',None) else toString(value)
            if getattr(value, "isNodeSet", None):
                self.stringValue = value  # .string()
            else:
                self.stringValue = str(value)
        elif _type == self.BOOLEAN_TYPE:
            # self.booleanValue=value.bool() if getattr(value,'isNodeSet',None) else toBoolean(value)
            if getattr(value, "isNodeSet", None):
                self.booleanValue = value  # .bool()
            else:
                self.booleanValue = bool(value)
        elif _type == self.ANY_UNORDERED_NODE_TYPE or _type == self.FIRST_ORDERED_NODE_TYPE:
            self.singleNodeValue = value  # .first()
        else:
            self.nodes = value  # .list()
            self.snapshotLength = len(value)
            self.index = 0
            self.invalidIteratorState = False

    # def iterateNext(self):
    #     node = self.nodes[self.index]
    #     self.index += 1
    #     return node

    # def snapshotItem(self, i):
    #     return self.nodes[i]

"""
    domonic.geom.vec3
    ====================================
    written by.ai
"""
import math

# from domonic.javascript import Math


class vec3:
    """[vec3]"""

    def __init__(self, x: float = 0, y: float = 0, z: float = 0, w: float = 0):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.w: float = w

    def __add__(self, other):
        if isinstance(other, vec3):
            return self.__class__((self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w))
        else:
            return self.__class__((self.x + other, self.y + other, self.z + other, self.w + other))

    def __sub__(self, other):
        if isinstance(other, vec3):
            return self.__class__((self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w))
        else:
            return self.__class__((self.x - other, self.y - other, self.z - other, self.w - other))

    def __mul__(self, other):
        if isinstance(other, vec3):
            return self.__class__((self.x * other.x, self.y * other.y, self.z * other.z, self.w * other.w))
        else:
            return self.__class__((self.x * other, self.y * other, self.z * other, self.w * other))

    # def __rmul__(self, other):
    #     return vec3(other.x * self.x, other.y * self.y, other.z * self.z, other.w * self.w)

    def __truediv__(self, other):
        if isinstance(other, vec3):
            return self.__class__(self.x / other.x, self.y / other.y, self.z / other.z, self.w / other.w)
        else:
            return self.__class__(self.x / other, self.y / other, self.z / other, self.w / other)

    # def __pow__(self, other):
    #     return vec3(self.x ** other.x, self.y ** other.y, self.z ** other.z, self.w ** other.w)

    # def __mod__(self, other):
    #     return vec3(self.x % other.x, self.y % other.y, self.z % other.z, self.w % other.w)

    def __getitem__(self, item):
        if isinstance(item, int):
            if item == 0:
                return self.x
            elif item == 1:
                return self.y
            elif item == 2:
                return self.z
            elif item == 3:
                return self.w
        elif isinstance(item, str):
            if item == "x":
                return self.x
            elif item == "y":
                return self.y
            elif item == "z":
                return self.z
            elif item == "w":
                return self.w

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        self.w += other.w

    def add(self, point):
        self.x += point.x
        self.y += point.y
        self.z += point.z
        return self

    def subtract(self, point):
        """Subtract from this point."""
        self.x -= point.x
        self.y -= point.y
        self.z -= point.z
        return self

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w

    def cross(self, other):
        return (
            self.x * other.y - self.y * other.x,
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
        )

    def mul(self, v):
        return v.x * self.x + v.y * self.y + v.z * self.z + v.w * self.w

    def copy(self):
        """Creates a copy of this object."""
        return vec3(self.x, self.y, self.z, self.w)

    def angleBetween(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)

    def distance(self, other):
        """Returns the distance between this point and another vector3."""
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2 + (self.w - other.w) ** 2
        # return sqrt(pow(self.x - other.x, 2) + pow(self.y - other.y, 2) + pow(self.z - other.z, 2) + pow(self.w - other.w, 2))

    def equals(self, other):
        """Determine whether two objects are identical."""
        return self.x == other.x and self.y == other.y and self.z == other.z and self.w == other.w

    def intersects(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        dw = self.w - other.w
        return (
            (dx * dy - dy * dz) > 0
            and (dx * dw - dw * dz) > 0
            and (dx * dz + dz * dw) > 0
            and (dy * dw - dw * dy) > 0
            and (dy * dw - dw * dw) > 0
        )

    def clone(self):
        """Returns a new instance of this vector3."""
        return vec3(self.x, self.y, self.z, self.w)

    def apply(self, point, amount):
        """Moves the points x,y,z,w by amount."""
        return vec3(
            point.x + amount.x,
            point.y + amount.y,
            point.z + amount.z,
            point.w + amount.w,
        )

    def __str__(self):
        return str(self.x) + " " + str(self.y) + " " + str(self.z)


class Object:
    def __init__(self, obj=None, *args, **kwargs) -> None:
        """[Creates a Javascript-like Object in python]

        Args:
            obj ([type]): [pass an object, dict or callable to the contructor]
        """
        # print('object created!')
        if obj is None:
            obj = {}

        self.prototype = self.__class__
        self.__extensible = True
        self.__frozen = False
        self.__sealed = False

        for arg in args:
            self.__dict__.update(arg)
        self.__dict__.update(kwargs)

        # self.__dict__ = {}
        if callable(obj):
            self.__dict__.update(obj())
        if isinstance(obj, dict):
            self.__dict__.update(obj)
        else:
            try:
                self.__dict__ = {}
                self.__dict__.update(obj.__dict__)
                self.__dict__.update(kwargs)
                self.__dict__.update(args)
                # self.__dict__['__class__'] = obj.__class__.__name__
                # self.__dict__['__module__'] = obj.__module__
                # self.__dict__['__doc__'] = obj.__doc__
                # self.__dict__['__proto__'] = obj
                # self.__dict__['__proto__'].__class__ = Object
                # self.__dict__['__proto__'].__dict__ = self.__dict__
            except Exception as e:
                print("Object.__init__() failed to set attribs", e)

    def __str__(self):
        """Returns a string representation of the object"""
        d = self.__dict__.copy()
        for k, v in list(d.items()):
            if "__" in k:
                del d[k]
            if "prototype" in k:
                del d[k]
        return str(d)

    # def __repr__(self):
    #     """ Returns a string representation of the object."""
    #     return self.toString()

    @staticmethod
    def fromEntries(entries):
        """
        transforms a list of lists containing key and value into an object.
        @param entries: a list containing key and value tuples. The key and value are separated by ':'
        @type entries: list of tuple(string, string)
        @returns: a dict object.

        >>> fromEntries(entries)
        {'a': 1, 'b': 2, 'c': 3}
        """
        return {k: v for k, v in entries}

    @staticmethod
    def assign(target, source):
        """Copies the values of all enumerable own properties from one or more source objects to a target object."""
        if isinstance(target, dict):
            if isinstance(source, dict):
                for k, v in source.items():
                    target[k] = v
            else:
                for k, v in source.__dict__.items():
                    target[k] = v
        else:
            if isinstance(source, dict):
                for k, v in source.items():
                    setattr(target, k, v)
            else:
                for k, v in source.attribs.items():
                    setattr(target, k, v)

        # return target
        # for prop in source.__dict__:
        #     if source.propertyIsEnumerable(prop):
        #         target.__dict__[prop] = source.__dict__[prop]
        return target

    @staticmethod
    def create(proto, propertiesObject=None):
        """Creates a new object with the specified prototype object and properties."""
        if propertiesObject is None:
            return Object(proto)

        if isinstance(propertiesObject, dict):
            return Object(propertiesObject)
        elif isinstance(propertiesObject, Object):
            return propertiesObject
        elif isinstance(propertiesObject, list):
            return Object.fromEntries(propertiesObject)
        else:
            return propertiesObject

        # return Object(propertiesObject)

    #     obj = {}
    #     for key in proto.keys():
    #         obj[key] = propertiesObject[key]
    #     return obj

    @staticmethod
    def defineProperty(obj, prop, descriptor):
        """Adds the named property described by a given descriptor to an object."""
        obj[prop] = descriptor

    # @staticmethod
    # def defineProperties(obj, props):
    #     """ Adds the named properties described by the given descriptors to an object. """
    #     for prop, desc in props.items():
    #         obj.__define_property__(prop, desc)  # TODO - obviously that wont work

    @staticmethod
    def entries(obj):
        """Returns an array containing all of the [key, value] pairs in the object."""
        if isinstance(obj, dict):
            return [[k, v] for k, v in obj.items()]
        if isinstance(obj, (float, int)):
            return []

    @staticmethod
    def keys(obj):
        """Returns an array containing the names of all of the given object's own enumerable string properties."""
        if isinstance(obj, dict):
            return obj.keys()
        if isinstance(obj, (float, int)):
            return []
        return obj.__dict__.keys()  # TODO - this is probably wrong

    @staticmethod
    def values(obj):
        """Returns an array containing the values that correspond to
        all of a given object's own enumerable string properties."""
        if isinstance(obj, dict):
            return obj.values()
        if isinstance(obj, (float, int)):
            return []
        return obj.__dict__.values()  # TODO - this is probably wrong

    @staticmethod
    def getOwnPropertyDescriptor(obj, prop):
        """Returns a property descriptor for a named property on an object."""
        if isinstance(obj, dict):
            return obj[prop]
        return obj.__dict__[prop]

    @staticmethod
    def getOwnPropertyNames(obj):
        """Returns an array containing the names of all of the given object's
        own enumerable and non-enumerable properties."""
        if isinstance(obj, dict):
            return obj.keys()
        elif isinstance(obj, Object):
            return obj.__dict__.keys()
        elif isinstance(obj, object):
            return [prop for prop in dir(obj) if not prop.startswith("__")]
        return obj.__dict__.keys()

    # @staticmethod
    # def _is(value1, value2):
    #     """ Compares if two values are the same value.
    #     Equates all NaN values (which differs from both Abstract Equality Comparison
    #  and Strict Equality Comparison)."""
    #     pass

    @staticmethod
    def getOwnPropertySymbols(obj):
        """Returns an array of all symbol properties found directly upon a given object."""
        if isinstance(obj, dict):
            return []
        return [prop for prop in dir(obj) if not prop.startswith("__")]

    @staticmethod
    def getPrototypeOf(obj):
        """Returns the prototype (internal [[Prototype]] property) of the specified object."""
        if isinstance(obj, dict):
            return obj
        elif isinstance(obj, Object):
            return obj.prototype
        elif isinstance(obj, object):
            return obj.__class__
        return obj.__proto__

    # @property #TODO - static or prop?
    # def isExtensible(obj):
    #     """ Determines if extending of an object is allowed """
    #     return obj.__extensible

    # @property #TODO - static or prop?
    # def isSealed(obj):
    #     """ Determines if an object is sealed """
    #     return obj.__sealed

    # @property
    # def preventExtensions(obj):
    #     """ Prevents any extensions of an object. """
    #     if isinstance(obj, dict):
    #         return False
    #     elif isinstance(obj, Object):
    #         obj.extensible = False
    #         return True
    #     elif isinstance(obj, object):
    #         return False
    #     return False

    # @property
    # def seal(obj):
    #     """ Prevents other code from deleting properties of an object. """
    #     if isinstance(obj, dict):
    #         return False
    #     elif isinstance(obj, Object):
    #         obj.sealed = True
    #         return True
    #     elif isinstance(obj, object):
    #         return False
    #     return False

    # @property
    # def setPrototypeOf(obj, prototype):
    #     """ Sets the object's prototype (its internal [[Prototype]] property). """
    #     if isinstance(obj, dict):
    #         return False
    #     elif isinstance(obj, Object):
    #         obj.prototype = prototype
    #         return True
    #     elif isinstance(obj, object):
    #         return False
    #     return False

    @property  # TODO - static or prop?
    def isFrozen(self, obj):
        """Determines if an object was frozen."""
        return self.__isFrozen

    @staticmethod  # TODO - static or prop?
    def freeze(obj):
        """Freezes an object. Other code cannot delete or change its properties."""
        obj.__isFrozen = True

    # def prototype(self, obj):
    #     """
    #     prototype and allows you to add properties and methods to this object
    #     """
    #     if isinstance(obj, dict):
    #         return False
    #     elif isinstance(obj, Object):
    #         obj.prototype = self
    #         return True
    #     elif isinstance(obj, object):
    #         return False
    #     return False

    def __defineGetter__(self, prop, func):
        """Adds a getter function for the specified property."""
        self.__dict__[prop] = property(func)
        return self

    def __defineSetter__(self, prop, func):
        """Associates a function with a property that, when set, calls the function."""
        self.__dict__[prop] = property(func)
        return self

    def __lookupGetter__(self, prop):
        """
        Returns the getter function for the specified property.
        """
        return self.__dict__[prop]

    def __lookupSetter__(self, prop):
        """Returns the function associated with the specified property by the __defineSetter__() method."""
        return self.__dict__[prop]

    def hasOwnProperty(self, prop):
        """Returns a boolean indicating whether an object contains the specified property
        as a direct property of that object and not inherited through the prototype chain."""
        # raise NotImplementedError
        # return hasattr(self, prop)
        return self.__dict__.get(prop, None) != None

    def isPrototypeOf(self, obj):
        """Returns a boolean indicating whether an object is a copy of this object."""
        if isinstance(obj, Object):
            return obj.prototype == self
        elif isinstance(obj, dict):
            return obj == self
        elif isinstance(obj, object):
            return obj.__class__ == self.__class__ and obj.__dict__ == self.__dict__
        return obj.__class__ == self.__class__ and obj.__proto__ == self

    # def propertyIsEnumerable(self, prop):
    #     """ Returns a boolean indicating whether the specified property is enumerable. """
    #     pass

    def toLocaleString(self):
        """Calls toString()"""
        return self.toString()

    def toString(self):
        """Returns a string representation of the object."""
        return "[" + self.__class__.__name__ + ": " + str(self.__dict__) + "]"

    def valueOf(self):
        """Returns the value of the object."""
        return self

    def __iter__(self):
        """Iterates over object's properties."""
        for prop in self.__dict__:
            yield prop
        for key in self.__dict__:
            yield key
        # return
        # return self.__dict__.__iter__()

    def __hash__(self):
        """Returns the hash of the object."""
        return hash(self.toString())

    def __eq__(self, other):
        """Compares two objects."""
        if isinstance(other, Object):
            return self.toString() == other.toString()
        return False

    def __ne__(self, other):
        """Compares two objects."""
        if isinstance(other, Object):
            return self.toString() != other.toString()
        return True

    def __nonzero__(self):
        """Returns whether the object is false."""
        return self.toString() != ""

    def __bool__(self):
        """Returns whether the object is false."""
        return self.toString() != ""

    # def __dict__(self):
    #     """ Returns the object's attributes as a dictionary. """
    #     return self.__dict__

    def __getitem__(self, key):
        """Returns the value of the specified property."""
        # return self.__dict__[key]
        # return self.__dict__.get(key, None)
        return self.__dict__.get(key)

    def __deepcopy__(self, memo):
        """Makes a deep copy of the object."""
        return self.__class__(self.__dict__)

    def __setitem__(self, key, value):
        """Sets the value of the specified property."""
        # self.__dict__[key] = value
        return self.__dict__.__setitem__(key, value)

    def __delitem__(self, key):
        """Deletes the specified property."""
        del self.__dict__[key]

    def __len__(self):
        """Returns the number of properties."""
        return len(self.__dict__)

    def __contains__(self, key):
        """[Returns whether the specified property exists.]

        Args:
            key ([str]): [The name of the property to check for.]

        Returns:
            [bool]: [True if the specified property exists. Otherwise, False.]
        """
        return key in self.__dict__

    def __getattr__(self, name):
        """[gets the value of the specified property]

        Args:
            name ([str]): [the name of the property]

        Returns:
            [str]: [the value of the specified property]
        """
        return self.__getitem__(name)

    def __setattr__(self, name, val):
        """[sets the value of the specified property]

        Args:
            name ([str]): [the name of the property]
            val ([str]): [the value of the property]

        Returns:
            [str]: [the value of the property]
        """
        return self.__setitem__(name, val)

    def __delattr__(self, name):
        """[deletes the specified property]

        Args:
            name ([str]): [the name of the property]

        Returns:
            [type]: [the value of the property]
        """
        return self.__delitem__(name)

    # def __call__(self, *args, **kwargs):
    #     """ Calls the object. """
    #     return self.toString()


def case_kebab(s: str) -> str:
    """
    kebab('camelCase') # 'camel-case'
    """
    return "-".join(
        sub(
            r"(\s|_|-)+",
            " ",
            sub(
                r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                lambda mo: " " + mo.group(0).lower(),
                s,
            ),
        ).split()
    )

def case_camel(s: str) -> str:
    """case_camel('camel-case') > 'camelCase'"""
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]
