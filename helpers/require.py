from importlib.machinery import SourceFileLoader
from pathlib import Path
import sys


def _get(data, index=0, e=None):
    try:
        return data[index] if type(data) in (list, dict, set, tuple) else data
    except Exception:
        return e


def load(target, **namespace):
    # Source bottle.py:load
    module, target = target.split(":", 1) if ':' in target else (target, None)
    if module in globals():
        if hasattr(globals()[module], target):
            return getattr(globals()[module], target)
        else:
            return globals()[module]
    if module not in sys.modules:
        try:
            __import__(module)
        except ModuleNotFoundError as e:
            module_path = Path(module)
            if module_path.exists():
                try:
                    sys.path.append(module_path.parent.as_posix())
                    print(module_path.name, module_path)
                    module = SourceFileLoader(
                        module_path.name, module_path
                    ).load_module()
                except Exception:
                    raise e
            else:
                raise e

    if not target:
        return sys.modules[module]
    if target.isalnum():
        return getattr(sys.modules[module], target)
    package_name = module.split('.')[0]
    namespace[package_name] = sys.modules[package_name]
    return eval('%s.%s' % (module, target), namespace)


class require:
    def __init__(self, *module):
        """Import a module for only a particular function
The 'module' argument vspecifies the module to import

The 'package' argument is required when performing a relative import.
It specifies the package to use as the anchor point from which to resolve the relative import to an absolute import.

The function recieving the decorator must also recieve the module(s) as parameter(s)

Other function related arguments are passed when calling the function
```python
@require("numpy", "pandas")
def main(np, pd, x):
        ...
        print(x)

main(5)
# prints 5

@require("numpy")
def main(np):
        ...
```
You can also call specific functions from modules
```python
@require("numpy:array")
def plt(npfunc, data):
        arr = npfunc(data)
        return arr
plt([2,4,5,6,8])

# Is same as:

def plt(data):
        from numpy import array as npfunc
        arr = func(data)
        return arr
plt([2,4,5,6,8])
```
You could also assign the modules to variables..
just put an extra parentheses to simulate function call
```python
np = require("numpy")()

np, pd, plt = require("numpy", "pandas", "matplotlib.plot")()
```
"""

        self.modules = []
        for x in module:
            # name = str(x.split(':')[1])
            if isinstance(x, str):
                self.modules.append(load(x))
            else:
                self.modules.append(x)

    def __call__(self, func=None):
        if not func:
            return self.modules
        return __wrap(func, self.modules)


class __wrap:
    def __init__(self, f, m):
        self.f = f
        self.m = m

    def __call__(self, *args, **kwargs):
        return self.f(*self.m, *args, **kwargs)


class ModuleWrapper(object):
    def __init__(self, module):
        self._ = {'module': module}

    def __getattr__(self, name):
        return getattr(self._['module'], name)
