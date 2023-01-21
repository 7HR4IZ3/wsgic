import os, sys
from wsgic.helpers.extra import get_global as _gg, set_global as _sg
from wsgic.scripts import BaseScripts, script, __all_scripts
from wsgic.scripts.exceptions import ScriptNotFound
from .helpers import runscript, Apprunner as _ar

_root = os.getcwd()
sys.path.append(
    os.path.join(_root, "apps")
)
_sg("APPSDIR", _root+'/apps')
_sg("ROOTDIR", _root)

@script("create")
def create(target, *a, **kw):
    if target == "app":
        return start_app(*a, **kw)
    elif target == "ext":
        return create_wsgic_app(*a, **kw)
    raise ScriptNotFound

@script("create-app")
def start_app(name, type="full"):
    files_full = {
        "__init__": f"""from .app import __app__ as {name.title()}
from . import scripts
from . import services
""",
        "app": f"""from wsgic import WSGIApp
from wsgic.helpers import config

class {name.title()}App(WSGIApp):
    def __init__(self):
        super().__init__("{name}.urls:router", config)

__app__ = {name.title()}App()
""",
        "views" : """from wsgic.http import request

def index():
    return f"Hello World from {request.path}"
""",
        "urls" : """from wsgic.routing import Router
from .views import *

router = Router()
routes = router.get_routes()

routes.get("*", index)
""",
        "models" : """
""",
        "scripts" : """
""",
#         "helpers": """
# """,
        "services": """
""",
        "plugins": """from wsgic.plugins import *
""",
        "panels": """from wsgic_admin.helpers import AdminPanel, register
from .models import *

register()
""",
        "wsgi": f"""from .app import __app__ as {name.title()}App

application = {name.title()}App.wrapped_app("wsgi")
""",
        "asgi": f"""from .app import __app__ as {name.title()}App

application = {name.title()}App.wrapped_app("asgi")
"""
    }
    files_single = {
        "__init__": """from wsgic import WSGIApp
from wsgic.http import request
from wsgic.routing import Router

router, routes = Router().get_routes()

@routes.get("*")
def index():
    return f"Hello World from {request.path}"

__app__ = WSGIApp(router)
application = __app__.wrapped_app("wsgi")
"""
    }
    files_basic = {
        "__init__": """from wsgic import WSGIApp
from wsgic.http import request

app = WSGIApp()

@app.get("*")
def index():
    return f"Hello World from {request.path}"

__app__ = app
application = __app__.wrapped_app("wsgi")
"""
    }
    files_basic_django = {
        "__init__": """from wsgic import WSGIApp
from wsgic.http.plugins import RequestPlugin

app = WSGIApp()
app.routes.install(RequestPlugin)

@app.get("*")
def index(request):
    return f"Hello World from {request.path}"

__app__ = app
application = __app__.wrapped_app("wsgi")
"""
    }
    if type in ("full", "-f"):
        files = files_full
    elif type in ("single", "-s"):
        files = files_single
    elif type in ("basic", "-b"):
        files = files_basic
    elif type in ("basic.django", "-bd"):
        files = files_basic_django
    else:
        raise ValueError

    cwd = str(os.getcwd())
    if not cwd.endswith('apps'):
        print('Not currently in apps directory')
        y = input('Create in apps directory? [y, n, q]: ')
        if y.lower() == 'y':
            nm = name
            name = os.path.join('apps', name)
        elif y.lower() == 'n':
            nm = name
        else:
            print("Terminating operation...")
            return
        print(f'Creating at {os.path.join(cwd, name)}')
    
    while True:
        try:
            os.mkdir(name)
            break
        except:
            print()
            print(f"Folder Already exists with name {name}")
            inp = str(input("Do you want to override it? [y, n]: ")).lower()
            if inp == "n":
                n = str(input("Enter new app name: "))
                if y.lower() == 'y':
                    nm = n
                    name = os.path.join('apps', n)
            elif inp == "y":
                os.rmdir(name)
    print()
    print(f"Creating WSGI App: {nm}")
    print()
    for m in files:
        try:
            print(f"Generating File: {os.path.join(name, m)}.py")
            with open(f"{os.path.join(name, m)}.py", "x") as file:
                file.write(files[m])
        except FileExistsError:
            print("File {os.path.join(name, m)}.py Already Exists")
            pass
    print()
    print(f"Created WSGI App: {nm}")

@script("create-ext")
def create_wsgic_app(name):
    return start_app("wsgic_"+name.lstrip("wsgic_").strip())

@script("run", "-r")
class Runner:
    def __get_run_parser(self):
        from argparse import ArgumentParser

        parser = ArgumentParser(prog="wsgic", usage="python -m %(prog)s [options] package.module:app")
        opt = parser.add_argument
        # opt("--version", action="store_true", help="show version number.")
        opt("-b", "--bind", metavar="ADDRESS", help="bind socket to ADDRESS.")
        opt("-s", "--server",default="werkzeug", help="use SERVER as backend.")
        # opt("-p", "--plugin", action="append", help="install additional plugin/s.")
        #  opt("-c", "--conf", action="append", metavar="FILE", help="load config values from FILE.")
        opt("-C", "--param", action="append", metavar="NAME=VALUE", help="override config values.")
        # opt("-p", "--port", action="store_true", help="create new wsgi app.")
        # opt("-s", "--script", action="store_true", help="run script then app.")
        opt("-a", "--asgi", action="store_true", help="run the asgi version of an app.")
        # opt("-r", "--asgi", action="store_true", help="run the asgi version of an app.")
        # opt("-d", "--django", action="store_true", help="Run the django cli.")
        opt("-env", default="dev", help="set app environment")
        opt("--debug", action="store_true", help="start server in debug mode.")
        opt("--ipyshell", action="store_true", help="start an interactive shell powered by ipython.")
        opt("--no-reload", action="store_true", help="auto-reload on file changes.")
        return parser

    def __init__(self, app=os.environ.get("WSGIC_APP"), *args):
        args = self.__get_run_parser().parse_args(args)
        appname = app
        _sg("APPDIR", _root+'/apps/'+app)
        _sg("APPMODULE", app)
        _sg("installed_apps", {})
        runner = _ar(app)

        kwargs = {}
        _sg("app_runner", runner)
        runner.init_app()

        if args.bind:
            host = args.bind
            port = None
            if ':' in host:
                host, port = host.split(':')
            kwargs["host"] = host
            
            if port:
                kwargs["port"] = int(port)

        if args.no_reload:
            kwargs["reloader"] = False
        if args.debug:
            kwargs["debug"] = True
        if args.server:
            kwargs["server"] = args.server
        if args.asgi:
            kwargs["type"] = "asgi"

        if args.ipyshell:
            import IPython
            app = runner.app
            IPython.embed()
        else:
            runner.run(**kwargs)


script("run-script", func=runscript)
