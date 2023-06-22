import sys
from .server.runner import parse_args
from .server.scripts import *

# Parse command line arguments
parse_args(sys.argv)