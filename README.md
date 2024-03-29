
# WSGIC Web Framework

WSGIC is a lightweight web framework built on top of WSGI. It aims to provide developers with a simple and flexible toolkit to build web applications in Python.

## Getting Started

To get started with WSGIC, you can clone the repository and run the demo application:

```
$ git clone https://github.com/7HR4IZ3/wsgic.git
$ cd wsgic
$ pip install -r requirements.txt
$ python demo.py
```

Then, navigate to http://localhost:8000/ in your web browser to see the demo in action.

## Features

WSGIC includes the following features:

- Routing: WSGIC includes a flexible routing system based on URL patterns.
- Middleware: WSGIC supports middleware components that can modify requests and responses.
- Templates: WSGIC includes a simple templating engine for generating HTML.
- Static files: WSGIC can serve static files from a directory on the filesystem.
- Websocket: WSGIC has built in support for websockets using gevent
- Customizable: WSGIC is designed to be easy to customize and extend, so you can add your own functionality as needed.

## Example

Here's an example of how to create a simple "Hello, world!" application in WSGIC:

```python
from wsgic import WSGIApp
from wsgic.routing import Router

router = Router()
routes = router.get_routes()

@routes.get("/")
def index():
    return "Hello, world!"

app = WSGIApp(router=router)
application = app.wrapped_app("wsgi") # 'asgi' also supported
# or just call app.run()
```

Or flask style
```python
from wsgic import WSGIApp

app = WSGIApp()

@app.get("/")
def index():
    return "Hello, world!"

application = app.wrapped_app("wsgi") # 'asgi' also supported
# or just call app.run()
```

Note: The 'application = app.wrapped_app("wsgi")' exposes the wsgi layer so you can run your app using other wsgi servers
else just call 'app.run()'

## Features

### Websocket
```python
from wsgic import WSGIApp

app = WSGIApp()

@app.websocket("/")
def index(socket, close):
    socket.receive() # Wait till client is ready
    socket.send("Name: ")
    name = socket.receive()
    socket.send(f"Hello {name}")
    close()

app.run()
```

### Web Routes
Allows you to control the client dom from the server

```python
from wsgic import WSGIApp
from wsgic.ui.dom import div, p, button

app = WSGIApp()

@app.web_route("/")
def index(response):
    response.send(
        div(
            p(0, id="counts"),
            button(id="increment")
        )
    )

    browser = request.browser
    counts = browser.document.querySelector("#counts")
    increment = browser.document.querySelector("#increment")

    def incr(event):
        current = int(counts.innerText)
        counts.innerText = current + 1

    increment.addEventListener("click", incr)

app.run()
```

### Static Files

```python
from wsgic import WSGIApp
from wsgic.handlers.files import FileSystemStorage

app = WSGIApp()

app.static("/assets", directory="./assets", store=FileSystemStore("./assets"))
# 'store' argument takes precedence over directory

@app.get("/")
def index(response):
    return "Hello World!"

app.run()
```

### Sessions

```python
from wsgic import WSGIApp
from wsgic.http import request

app = WSGIApp()

@app.get("/set/<name>")
def set(name):
    request.session['name'] = name
    return 'Set session name as %s'%name

@app.get("/get")
def get():
    return 'Current session: name = "%s"'%request.session.get('name')

app.run()
```


## Demo
```python
from wsgic import WSGIApp
from wsgic.views import FunctionView, view
from wsgic.http import request, redirect
from wsgic.services import service
from wsgic_auth.core.session import SessionAuth
from wsgic.routing.helpers import alias, named_route

app = WSGIApp()

authentication: SessionAuth = service("authentication")
validation = service("validation")

@app.view("/")
class HomeView(FunctionView):
    # FunctionView creates routes from all class methods with style '{method}_{path}'
    # Methods starting with '_' are ignored
    # Default method is get so 'profile' is interpreted as 'get_profile'

    @named_route("homepage") # Register name for the route
    @view("index.html") # Bind view to the route, interpreted as render("index.html", context=get_index())
    def get_index(self):
        return { "name": "World" }

@app.view("/auth")
class AuthView(FunctionView):

    @view("login.html")
    @named_route("login")
    def get_login(self):
        if authentication.is_logged_in(): return redirect("/")
        return

    def post_login(self):
        if authentication.is_logged_in(): return redirect("/")

        username = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember_me", False) == "on"

        if validation.set_rules({
            "username": "required",
            "password": "required"
        }).validate(request.POST):
            authenticated = authentication.login(username, password, remember)
            print(authentication.is_logged_in())
            if authenticated:
                return redirect().route("/").with_cookies()
            else:
                return redirect().back().error("Authentication failed.")
        else:
            error = validation.errors_list()
            return redirect().back().error(*error)

    def post_logout(self):
        if authentication.is_logged_in():
            authentication.logout()
        return redirect().to("/")
```

## Contributing

Contributions to WSGIC are welcome! To get started, fork the repository and create a new branch for your feature or bug fix. Then, submit a pull request with your changes.

## License

WSGIC is licensed under the MIT License. See `LICENSE` for more information.
