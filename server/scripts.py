import os, sys
from wsgic.helpers.extra import get_global as __getglobal, set_global as __set_global__
from wsgic.scripts import BaseScripts, script, __all_scripts
from wsgic.scripts.exceptions import ScriptNotFound
from .helpers import runscript
from .runner import Apprunner as __app_runner__

_root = os.getcwd()
# sys.path.append(
#     os.path.join(_root, "apps")
# )
# sys.path.append(
#     "C:\\Users\\HP\\Desktop\\files\\programming\\projects"
# )
__set_global__("APPSDIR", _root+'/apps')
__set_global__("ROOTDIR", _root)

@script("create", "-c")
def create(target, *a, **kw):
    if target == "app":
        return start_app(*a, **kw)
    elif target == "ext":
        return create_wsgic_app(*a, **kw)
    raise ScriptNotFound

@script("create-app")
def start_app(name, type="full", mode="wsgi"):
    assert (mode in ["asgi", "wsgi"]), "Invalid application type."

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
        "views" : """from wsgic.views import render
from wsgic.http import request

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
#         "plugins": """from wsgic.plugins import *
# """,
#         "panels": """from wsgic_admin.helpers import AdminPanel, register
# from .models import *

# register()
# """,
        "wsgi": f"""from .app import __app__ as {name.title()}App

application = {name.title()}App.wrapped_app("wsgi")
""",
        "asgi": f"""from .app import __app__ as {name.title()}App

application = {name.title()}App.wrapped_app("asgi")
"""
    }
    files_single = {
        "__init__": f"""from wsgic import WSGIApp
from wsgic.http import request
from wsgic.routing import create_router

router, routes = create_router()

@routes.get("*")
def index():
    return f"Hello World from {'{'}request.path{'}'}"

app = WSGIApp(router)
application = app.wrapped_app({mode})
"""
    }
    files_basic = {
        "__init__": f"""from wsgic import WSGIApp

app = WSGIApp()

@app.get("/")
def index():
    return f"Hello World"

application = app.wrapped_app({mode})
"""
    }
    files_basic_django = {
        "__init__": f"""from wsgic import WSGIApp
from wsgic.http.plugins import RequestPlugin

app = WSGIApp()
app.routes.install(RequestPlugin)

@app.get("/")
def index(request):
    return f"Hello World from {'{'}request.path{'}'}"

application = app.wrapped_app({mode})
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
    nm = name

    if not cwd.endswith('apps'):
        # print('Not currently in apps directory')
        y = 'n' #input('Create in apps directory? [y, n, q]: ')
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
    
    if len(files) == 1:
        fp = os.path.join(name, '__init__')
        try:
            print(f"Generating File: {fp}.py")
            with open(f"{fp}.py", "x") as file:
                file.write(files['__init__'])
        except FileExistsError:
            print(f"File {fp}.py Already Exists")

    else:
        for m in files:
            fp = os.path.join(name, m)
            try:
                print(f"Generating File: {fp}.py")
                with open(f"{fp}.py", "x") as file:
                    file.write(files[m])
            except FileExistsError:
                print(f"File {fp}.py Already Exists")

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
        arg = parser.add_argument

        # arg("--version", action="store_true", help="show version number.")
        arg("-b", "--bind", metavar="ADDRESS", help="bind socket to ADDRESS.")
        arg("-s", "--server", default="werkzeug", help="use SERVER as backend.")
        # arg("-p", "--plugin", action="append", help="install additional plugin/s.")
        #  arg("-c", "--conf", action="append", metavar="FILE", help="load config values from FILE.")
        arg("-C", "--param", action="append", metavar="NAME=VALUE", help="override config values.")
        # arg("-p", "--port", action="store_true", help="create new wsgi app.")
        # arg("-s", "--script", action="store_true", help="run script then app.")
        arg("-a", "--asgi", action="store_true", help="run the asgi version of an app.")
        # arg("-d", "--django", action="store_true", help="Run the django cli.")
        arg("-env", default="dev", help="set app environment")
        arg("--debug", action="store_true", help="start server in debug mode.")
        arg("--ipyshell", action="store_true", help="start an interactive shell powered by ipython.")
        arg("--no-reload", action="store_true", help="auto-reload on file changes.")
        return parser

    def __init__(self, app=os.environ.get("WSGIC_APP"), *args):
        args = self.__get_run_parser().parse_args(args)
        if not app: raise ValueError("App was not specified.")

        runner = __app_runner__(app)

        kwargs = {}

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
        else: runner.run(**kwargs)

script("run-script", func=runscript)
