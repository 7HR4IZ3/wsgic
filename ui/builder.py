from .helpers import reactive_mappings, Reactive, BaseContext
from functools import partial
import random

SINGLE_TAGS = [
    'input', 'hr', 'br', 'img', 'area', 'link',
    'col', 'meta', 'base', 'param', 'wbr',
    'keygen', 'source', 'track', 'embed',
]

TAG_NAME_SUBSTITUTES = {
    'del_': 'del',
    'Del': 'del',
}

ATTRIBUTE_NAME_SUBSTITUTES = {
    # html tags colliding with python keywords
    'klass': 'class',
    'Class': 'class',
    'class_': 'class',
    'async_': 'async',
    'Async': 'async',
    'for_': 'for',
    'For': 'for',
    'In': 'in',
    'in_': 'in',

    # from XML
    'xmlns_xlink': 'xmlns:xlink',

    # from SVG ns
    'fill_opacity': 'fill-opacity',
    'stroke_width': 'stroke-width',
    'stroke_dasharray': ' stroke-dasharray',
    'stroke_opacity': 'stroke-opacity',
    'stroke_dashoffset': 'stroke-dashoffset',
    'stroke_linejoin': 'stroke-linejoin',
    'stroke_linecap': 'stroke-linecap',
    'stroke_miterlimit': 'stroke-miterlimit',
}

ATTRIBUTE_VALUE_SUBSTITUTES = {
    'True': 'true',
    'False': 'false',
    'None': 'null',
}

basecontext = BaseContext()

class HTML(object):
    """docstring for Form"""

    def __init__(self, main="html", context=None, indentby="\t"):
        self._main = None
        self._context = context or basecontext
        self._mainname = main
        self._indent = 0
        self._indentby = indentby
        self._page = None
        self._num = 0
        self._tracked_elems = {}

    def __getattr__(self, name):
        tag = Tag(name, self, single=name in SINGLE_TAGS)
        if not self._main and name == self._mainname:
            self._main = tag
        return tag

    def __call__(self, *a, **kw):
        return self.html(*a, **kw)
    
    def __getitem__(self, name):
        single = False
        if isinstance(name, tuple):
            name, single = name
        return Tag(name, self, single=single)

    def compile(self):
        return self._main._ret

    def get_num(self):
        self._num += 1
        return self._num

    def __str__(self):
        return self.compile()


class Tag:
    def __init__(self, name, parent, single=False):
        self._name = name
        self._single = single
        self._parent = parent
        self.attrs = ""
        self.children = []
        self._parent._indent += 1
        self._ret = "<" + self._name

    def __repr__(self):
        return self._ret

    def __str__(self):
        return self._ret
    
    def update_bound(self, target_id):
        pass

    def set_bound_value(self, browser):
        pass

    def __call__(self, *children, bind=None, **attrs):
        if bind:
            item_id = str(self._parent.get_num())
            reactive = reactive_mappings.get(bind, None)

            if reactive:
                assert isinstance(reactive, Reactive), "Only instances of 'Reactive' are bindable."

                if reactive.is_bidirectional:
                    attrs["onchange"] = self.set_bound_value

                attrs["bound_id"] = item_id
                reactive.set_onchange(partial(self.update_bound, target_id=item_id))

            self._parent._tracked_elems[item_id]

        for attr in attrs:
            name = ATTRIBUTE_NAME_SUBSTITUTES.get(attr, attr).replace("_", "-")

            value = attrs[attr]
            value = ATTRIBUTE_VALUE_SUBSTITUTES.get(value, value)

            if callable(value):
                default = f"temp_func_{self._parent.get_num()}"
                temp_name = getattr(value, "__name__", default)

                if temp_name == "<lambda>":
                    temp_name = default

                if not hasattr(self._parent._context, temp_name):
                    self._parent._context.__register__(temp_name, value)

                value = temp_name
                self.attrs = self.attrs + \
                    ((f'{name}="server.{value}()" ' if value !=
                      True else f"{name} ") if value else "")
            else:
                value = str(value)
                self.attrs = self.attrs + \
                    ((f'{name}="{value}" ' if value !=
                      True else f"{name} ") if value else "")

        self.attrs = self.attrs.strip()
        self._ret = self._ret + " " + self.attrs

        if self._single:
            self._ret = self._ret.strip() + "/>"
        else:
            self._ret = self._ret.strip() + ">"

            for child in children:
                self._ret = self._ret + \
                    f"\n{self._parent._indentby * self._parent._indent}" + \
                    str(child)

            self._ret = self._ret + \
                f"\n{self._parent._indentby * (self._parent._indent - 1) }" + \
                "</" + self._name + ">"

        self._parent._indent -= 1
        return self._ret

html = HTML()

# Html Elements

html.html

a = html.a
abbr = html.abbr
address = html.address
applet = html.applet
area = html.area
article = html.article
aside = html.aside
audio = html.audio
b = html.b
base = html.base
basefont = html.basefont
bdi = html.bdi
bdo = html.bdo
blockquote = html.blockquote
body = html.body
br = html.br
button = html.button
canvas = html.canvas
caption = html.caption
center = html.center
cite = html.cite
code = html.code
col = html.col
colgroup = html.colgroup
command = html.command
data = html.data
datalist = html.datalist
dd = html.dd
# del = html.del
details = html.details
dfn = html.dfn
dialog = html.dialog
dir = html.dir
div = html.div
dl = html.dl
dt = html.dt
em = html.em
embed = html.embed
fieldset = html.fieldset
figcaption = html.figcaption
figure = html.figure
font = html.font
footer = html.footer
form = html.form
h1 = html.h1
h2 = html.h2
h3 = html.h3
h4 = html.h4
h5 = html.h5
h6 = html.h6
head = html.head
header = html.header
hgroup = html.hgroup
hr = html.hr
# html = html.html
i = html.i
iframe = html.iframe
img = html.img
input = html.input
ins = html.ins
isindex = html.isindex
kbd = html.kbd
keygen = html.keygen
label = html.label
legend = html.legend
li = html.li
link = html.link
listing = html.listing
main = html.main
map = html.map
mark = html.mark
menu = html.menu
menuitem = html.menuitem
meta = html.meta
meter = html.meter
nav = html.nav
noscript = html.noscript
object = html.object
ol = html.ol
optgroup = html.optgroup
option = html.option
output = html.output
p = html.p
param = html.param
picture = html.picture
plaintext = html.plaintext
pre = html.pre
progress = html.progress
q = html.q
rp = html.rp
rt = html.rt
ruby = html.ruby
s = html.s
samp = html.samp
script = html.script
section = html.section
select = html.select
small = html.small
source = html.source
span = html.span
strike = html.strike
strong = html.strong
style = html.style
sub = html.sub
submit = html.submit
summary = html.summary
sup = html.sup
table = html.table
tbody = html.tbody
td = html.td
template = html.template
textarea = html.textarea
tfoot = html.tfoot
th = html.th
thead = html.thead
time = html.time
title = html.title
tr = html.tr
track = html.track
u = html.u
ul = html.ul
var = html.var
video = html.video
wbr = html.wbr
xmp = html.xmp
