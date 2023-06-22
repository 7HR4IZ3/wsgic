
reactive_mappings = {}

class BaseContext:
    def __init__(self):
        self.__customs = {}

    @property
    def customs(self):
        return self.__customs

    def __getattr__(self, name):
        if name in self.__customs:
            def wrapper(*a, **kw):
                return self.__customs[name](*a, **kw)
            return wrapper
        raise AttributeError("No attribute named", name)

    def __register__(self, name, func):
        self.__customs[name] = func

class Reactive:
    def __init__(self, initial=None, two_ways=False, onchange=None):
        self.__onchange =  onchange
        self.initial = initial
        self.is_bidirectional = two_ways
    
    def set_onchange(self, onchange):
        self.__onchange =  onchange
        return self
    
    def onchange(self, owner):
        if isinstance(self.__onchange, str):
            onchange = getattr(owner, self.__onchange, None)
        else:
            onchange = self.__onchange

        if not onchange:
            onchange = getattr(owner, f"on_{self.public_name}_change", None)
        return onchange or (lambda *a: None)

    def __get__(self, obj, objtype=None):
        value = getattr(obj, self.private_name)
        reactive_mappings[id(value)] = self
        return value

    def __set__(self, obj, value):
        initial = getattr(obj, self.private_name, None)
        setattr(obj, self.private_name, value)

        if not (initial is None):
            self.onchange(obj)(initial, value)
    
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = '__original_' + name + "__"

        if self.initial:
            setattr(owner, self.private_name, self.initial)

class LocalStorage(Reactive):
    def __init__(self, default=None, *a, type=str, **kw):
        super().__init__(*a, **kw)
        self.type = type
        self.default = default

    def __get__(self, obj, objtype=None):
        try:
            browser = getattr(obj, "browser", None)
            if browser:
                item = browser.localStorage.getItem(self.public_name)
                return self.type(item) if item else self.default
            else:
                return self.default 
        except Exception as e:
            print(e)
            return self.default

    def __set__(self, obj, value):
        browser = getattr(obj, "browser", None)
        if browser:
            initial = browser.localStorage.getItem(self.public_name)
            browser.localStorage.setItem(self.public_name, value)

            if initial:
                self.onchange(obj)(initial, value)
    
    def __set_name__(self, owner, name):
        self.public_name = name

        if self.initial:
            self.__set__(owner, self.initial)

class SessionStorage(Reactive):
    def __init__(self, default=None, *a, type=str, **kw):
        super().__init__(*a, **kw)
        self.type = type
        self.default = default

    def __get__(self, obj, objtype=None):
        try:
            browser = getattr(obj, "browser", None)
            if browser:
                item = browser.sessionStorage.getItem(self.public_name)
                return self.type(item) if item else self.default
            else:
                return self.default
        except Exception as e:
            print(e)
            return self.default

    def __set__(self, obj, value):
        browser = getattr(obj, "browser", None)
        if browser:
            initial = browser.sessionStorage.getItem(self.public_name)
            browser.sessionStorage.setItem(self.public_name, value)

            if initial:
                self.onchange(obj)(initial, value)
    
    def __set_name__(self, owner, name):
        self.public_name = name

        if self.initial:
            self.__set__(owner, self.initial)

def default_apply(element, value):
    element.innerText = f"{value}"

def bind(element, value=None, apply=None):
    def onchange(initial, current):
        (apply or default_apply)(element, current)
    
    if isinstance(value, Reactive):
        value.set_onchange(onchange)
        return value
    else:
        reactive = Reactive(value, onchange)
        return reactive
