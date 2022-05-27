from bottle import request, route, template, default_app, run
from beaker.middleware import SessionMiddleware
from cork import Cork

app = default_app()
aaa = Cork('example_conf')
app = SessionMiddleware(app, {
                        'beaker.session.auto': True,
                        'beaker.session.type': 'cookie',
                        'beaker.session.validate_key': True,
                        'beaker.session.cookie_expires': True,
                        'beaker.session.timeout': 3600 * 24})

@route('/createuser')
def createuser():
    tstamp = str(datetime.utcnow())
    username = 'root'
    password = 'pwd'
    cork._store.users[username] = {
        'role': 'admin',
        'hash': cork._hash(username, password),
        'email_addr': username + '@localhost.local',
        'desc': username + ' test user',
        'creation_date': tstamp
    }
    return "User created"

@route('/login', method=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return template("""
        <html>
        <form method="post" action="/login">
            <input name="user" required="required" type="text" placeholder="user">
            <input name="password" type="password" required="required" placeholder="password">
            <input type="submit" name="login" value="login">
        </form>
        </html>
        """)
    if request.method == 'POST':
        username = request.POST.get('user','')
        password = request.POST.get('password','')
        print username, password
        aaa.login(username=username, password=password, success_redirect='/', fail_redirect='/login')

@route('/')
def home():
    aaa.require(role='admin',  fail_redirect='/login')
    return 'welcome'

run(app=app,  host='0.0.0.0', port=8888)
