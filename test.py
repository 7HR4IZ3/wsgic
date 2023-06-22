
class Test:
    pass

def browser(*args):
    print(args)

t = Test()
t.browser = browser
t.browser()

b = Test()
b.browser = property(browser)
b.browser()
