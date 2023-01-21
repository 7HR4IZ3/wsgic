
false = False
true = True
null = None
empty = bool
is_array = lambda x: isinstance(x, list)
is_numeric = lambda x: isinstance(x, int)
is_string = lambda x: isinstance(x, str)
in_array = lambda arr, key, e: key in arr
array_column = lambda arr, key: [x.get(key) for x in arr] 
lang = lambda *x: "Lang..."
