from pathlib import Path
from .pybridge import *

__file = Path(__file__).parent

with open((__file / "js_bridge_web.js").as_posix()) as f:
    BridgeJS = f.read()
