from pathlib import Path

# Build paths inside the project like this: BASE_DIR / "subdir"
BASE_DIR = Path(__file__).resolve().parent.parent

MOUNT = "/"

ENV = "DEV"
HOST = "127.0.0.1"
PORT = 8081
DEBUG = False

APPS = [
	"app"
]

SERVER = "gevent"

VIEWS ={
	"ENGINE": "jinja2",
	"ID": "*View"
}

ROUTER = {
	"ENGINE": "default"
}

STATIC = {
	"TEMPLATE": {
		"ENGINE": "jinja2",
		"DIRS": [
			BASE_DIR / "templates/"
		]
	},
	"ASSETS": {
		"URL": "/serve",
		"DIRS": [
			BASE_DIR / "templates/assets/"
		]
	}
}

DATABASES ={
	"DEFAULT": {
		"ENGINE": "sqlite3",
		"PATH": BASE_DIR / "db.sqlite",
		"DEBUG": DEBUG,
		"CONFIG": {}
	},
	"FAILOVER": {
		 "1": {},
		 "2": {}
	}
}

USE = {
	"DATABASE": True,
	"STATIC": True
}