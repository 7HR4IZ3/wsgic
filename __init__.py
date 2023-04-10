from .thirdparty.bottle import _ImportRedirect

import sys; [sys.path.append(i) for i in [
    # "C:\\Users\\HP\\Desktop\\files\\programming\\projects",
    # "./wsgi",
    # './wsgi/apps'
]]

from .apps import *

_ImportRedirect('wsgic.ext' if __name__ == '__main__' else  __name__ + ".ext", 'wsgic_%s').module