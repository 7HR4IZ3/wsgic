from cap import Cap, anonymous, roles
from bottle import Bottle, route, get, post, run, request, redirect

cap = Cap(loginroute="/login", dbpath="users.db")
app = Bottle()

app.install(cap)

@app.get("/login")
@anonymous
def login():
	return '''
<!DOCTYPE html>
<html>
	<body>
		<form action="/login" method="post">
			<input type="text" placeholder="username" name="username" />
			<input type="password" placeholder="password" name="password" />
			<button type="submit">Log In</button>
		</form>
	</body>
</html>
'''

@app.post("/login")
@anonymous
def dologin():
	username = request.forms.username
	password = request.forms.password
	
	user = cap.login(username, password)
	
	if(user is None):
		redirect("/login", 303)
	else:
		redirect("/", 302)


@app.post("/logout")
def logout():
	cap.logout()
	redirect("/login")

@app.get('/')
def index(user):
	if 'admin' in user.roles:
		adminlink = '<p><a href="/admin">Admin Page</a></p>'
	else:
		adminlink = ''
	
	return '''
<!DOCTYPE html>
<html>
	<body>
		<p>I'm authenticated!</p>
''' + adminlink + '''
		<form action="/logout" method="post">
			<button type="submit">Log Out</button>
		</form>
	</body>
</html>
'''

@app.get('/admin')
@roles('admin')
def admin():
	 return '''
<!DOCTYPE html>
<html>
	<body>
		<p>Role required for access.</p>
		<p><a href="/">Home</a></p>
	</body>
</html>
'''




run(app=app, url="0.0.0.0", port=8080, debug=True)
