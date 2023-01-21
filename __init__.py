from .thirdparty.bottle import _ImportRedirect
from .apps import *

_ImportRedirect('wsgic.ext' if __name__ == '__main__' else  __name__ + ".ext", 'wsgic_%s').module