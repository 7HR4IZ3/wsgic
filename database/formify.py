
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

class HTML(object):
    """docstring for Form"""
    def __init__(self, main="html", indentby="\t"):
        self._main = None
        self._mainname = main
        self._indent = 0
        self._indentby = indentby
    
    def __getattr__(self, name):
        tag = Tag(name, self, single=name in SINGLE_TAGS)
        if not self._main and name == self._mainname:
            self._main = tag
        return tag
    
    def compile(self):
        return self._main._ret

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
    
    def __call__(self, *children, **attrs):
        for attr in attrs:
            name = ATTRIBUTE_NAME_SUBSTITUTES.get(attr, attr)
            value = ATTRIBUTE_VALUE_SUBSTITUTES.get(attrs[attr], attrs[attr])
            self.attrs = self.attrs + (f'{name}="{value}" ' if value and value != True else f"{name} ")
        self.attrs = self.attrs.strip()
        self._ret = self._ret + " " + self.attrs

        if self._single:
            self._ret = self._ret.strip() + "/>"
        else:
            self._ret = self._ret.strip() + ">"

            for child in children:
                self._ret = self._ret + f"\n{self._parent._indentby * self._parent._indent}"+ str(child)

            self._ret = self._ret + f"\n{self._parent._indentby * (self._parent._indent - 1) }" + "</"+self._name+">"

        self._parent._indent -= 1
        return self._ret

html = HTML()

# html.html(
#     html.head(
#         html.meta(rel="stylesheet")
#     ),
#     html.body(
#         html.header(
#             html.nav(
#                 html.ul(
#                     html.li(html.a("Nav item 1", href="/1")),
#                     html.li(html.a("Nav item 2", href="/2")),
#                     html.li(html.a("Nav item 3", href="/3")),
#                     html.li(html.a("Nav item 4", href="/4")),
#                 )
#             )
#         ),
#         html.main(
#             html.div(
#                 html.h2("Hello World"),
#                 html.p("This is a paragraphed text")
#             )
#         ),
#         html.footer(
#             html.script(
#                 "var i = 0;"
#             )
#         ),
#         html.script(src="./jquery.js")
#     )
# )

# print(html)
