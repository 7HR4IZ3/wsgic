from wsgic.helpers import config
from wsgic.http import request

engine = config.get("validation.engine", "v2")

if engine == "v3":
    from .v2 import *
else:
    from .v1 import *
