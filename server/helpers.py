from ..scripts import __all_scripts
from ..scripts.exceptions import ScriptNotFound
from ..helpers.extra import load_module

def runscript(app, *args):
    try:
        load_module(app.replace(".app", "")+".scripts")
    except:
        load_module(app)

    scripts = __all_scripts
    func = scripts.get(args[0])
    if func:
        return func(*args[1:])
    else:
        raise ScriptNotFound("%s has no script named %s"%(app, args[0]))
