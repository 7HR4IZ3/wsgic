from argparse import ArgumentError
from contextlib import contextmanager
from cryptography.fernet import Fernet
from getpass import getpass
from hashlib import sha512
from inspect import signature
import pickle
import sqlite3

import secrets
from wsgic.thirdparty.bottle import redirect, abort, request, response


class InvalidUserException(Exception):
	def __init__(self):
		super().__init__("Invalid username or password.")

		
def create_hash(password, salt):
	return sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()

class User():
	def __init__(self, username, roles = [], info = {}):
		self.username = username
		self.roles = roles
		self.info = info
	
	def inrole(self, role):
		return role in self.roles
	
	def getinfo(self, key):
		return self.info[key]

class Cap():

	name = "cap"
	api = 2
	
	def __init__(self, loginroute = "/login", dbpath = ":memory:"):
		self.loginroute = loginroute
		self.dbpath = dbpath
		self.cookie_secret = Fernet.generate_key().decode("utf-8")
		self.fernet = Fernet(Fernet.generate_key())
	
	@contextmanager
	def __db(self):
		conn = sqlite3.connect(self.dbpath)
		conn.row_factory = sqlite3.Row;
		conn.execute("PRAGMA foreign_keys = ON;")
		try:
			yield conn
		finally:
			conn.close()
	
	# cookie serialization
	
	def __encrypt_user(self, user):
		p = pickle.dumps(user)
		return self.fernet.encrypt(p)
	
	def __decrypt_user(self, data):
		p = self.fernet.decrypt(data)
		return pickle.loads(p)
	
	# user management
	
	def list_users(self):
		users = []
		
		with self.__db() as db:
			cursor = db.cursor()
			cursor.execute("""SELECT user_name FROM user;""")
			users = [ u["user_name"] for u in cursor.fetchall() ]
		
		return users
	
	def get_user(self, username, password = None):
		with self.__db() as db:
			cursor = db.cursor()
			
			if password is not None:
				try:
					cursor.execute("""SELECT password, salt
										FROM user
									   WHERE user_name = ?;""", (username,))
					row = cursor.fetchone()
					
					hash, salt = row["password"], row["salt"]
					
					if hash != create_hash(password, salt):
						raise InvalidUserException()
				except Exception as e:
					raise InvalidUserException() from e
			
			cursor.execute("""SELECT role_name
								FROM user_roles
							   WHERE user_name = ?;""", (username,))
			
			roles = [ row["role_name"] for row in cursor.fetchall() ]
			
			cursor.execute("""SELECT info_key, info_value
								FROM user_info
							   WHERE user_name = ?;""", (username,))
			
			info = dict(( (row["info_key"], row["info_value"]) for row in cursor.fetchall() ))
		
		return User(username, roles, info)
	
	def create_user(self, username, password):
		if type(username) is not str:
			raise TypeError('Username must be a string')
		elif type(password) is not str:
			raise TypeError('Password must be a string')
		elif username == '':
			raise ArgumentError('Username must not be blank')
		elif password == '':
			raise ArgumentError('Password must not be blank')
		
		salt = Fernet.generate_key().decode("utf-8")
		hash = create_hash(password, salt)
		
		with self.__db() as db:
			db.execute("""INSERT INTO user (uuid, user_name, password, salt) VALUES (:uuid, :user, :hash, :salt);""",
					   { "uuid": str(secrets.SystemRandom().random())[2:15], "user": username, "hash": hash, "salt": salt })
			db.commit()
			return User(username)
			
	def delete_user(self, username):
		with self.__db() as db:
			db.execute("""DELETE FROM user WHERE user_name = ?;""", (username,))
			db.commit()
	
	def set_password(self, username, new_password):
		salt = Fernet.generate_key().decode("utf-8")
		hash = create_hash(new_password, salt)
		
		with self.__db() as db:
			db.execute("""UPDATE user SET password = :hash, salt = :salt WHERE user_name = :user;""",
					   { "user": username, "hash": hash, "salt": salt })
			db.commit()
	
	def create_roles(self, *roles):
		with self.__db() as db:
			db.executemany("""INSERT INTO role (role_name) VALUES (?);""", (roles,))
			db.commit()
	
	def delete_role(self, role):
		with self.__db() as db:
			db.execute("""DELETE FROM role WHERE role_name = ?;""", (role,))
			db.commit()
	
	def add_user_role(self, username, role):
		with self.__db() as db:
			db.execute("""INSERT INTO user_roles (user_name, role_name) VALUES (:user, :role);""",
					   { "user": username, "role": role})
			db.commit()
	
	def delete_user_role(self, username, role):
		with self.__db() as db:
			db.execute("""DELETE FROM user_roles WHERE user_name = :user AND role_name = :role;""",
					   { "user": username, "role": role})
			db.commit()
	
	def set_user_roles(self, username, roles):
		with self.__db() as db:
			db.execute("""DELETE FROM user_roles WHERE user_name = ?;""", (username,))
			db.executemany("""INSERT INTO user_roles (user_name, role_name) VALUES (:user, :role);""",
						   ( { "user": username, "role": role} for role in roles ))
			db.commit()
	
	def set_user_info(self, username, info):
		with self.__db() as db:
			db.execute("""DELETE FROM user_info WHERE user_name = ?;""", username)
			db.executemany("""INSERT INTO user_info (user_name, info_key, info_value) VALUES (:user, :key, :val);""",
						   ( { "user": username, "key": key, "val": info[key] } for key in info.keys() ))
			db.commit()
	
	def update_user(self, user):
		if not isinstance(user, User):
			raise TypeError("user must be of type User")
		
		with self.__db() as db:
			db.execute("""DELETE FROM user_roles WHERE user_name = ?;""", username)
			db.executemany("""INSERT INTO user_roles (user_name, role_name) VALUES (:user, :role);""",
						   ( { "user": username, "role": role} for role in roles ))
			db.execute("""DELETE FROM user_info WHERE user_name = ?;""", username)
			db.executemany("""INSERT INTO user_info (user_name, info_key, info_value) VALUES (:user, :key, :val);""",
						   ( { "user": username, "key": key, "val": info[key] } for key in info.keys() ))
			db.commit()
			
	
	# login/logout
	
	def login(self, username, password):
		try:
			user = self.get_user(username, password)
		except InvalidUserException:
			user = None

		response.set_cookie("cap_auth", value=self.__encrypt_user(user), secret=self.cookie_secret, max_age=60 * 60)
		
		return user
		
	def __load_cookie(self):
		data = request.get_cookie("cap_auth", secret=self.cookie_secret)
		
		user = self.__decrypt_user(data) if data is not None else None
		
		return user
	
	def logout(self):
		response.delete_cookie("cap_auth")
	
	# bottle plugin api
	
	def setup(self, app):
		self.app = app
	
	def apply(self, func, route):
		wantsuser = "user" in signature(route.callback).parameters
		
		def wrapper(*args, **kwargs):
			try:
				user = self.__load_cookie()
			except Exception as e:
				user = None
			
			if user is None and not hasattr(route.callback, "allow_anonymous"):
				self.logout()
				redirect(self.loginroute, 307)
			elif hasattr(route.callback, "roles") and not any(role in user.roles for role in route.callback.roles):
				abort(403, "Access Denied")
			else:
				if wantsuser:
					kwargs["user"] = user
					
				return func(*args, **kwargs)

		return wrapper
	
	def close(self):
		pass

# attributes

class roles():
	def __init__(self, *roles):
		self.roles = roles
	
	def __call__(self, func):
		func.roles = self.roles
		return func

def anonymous(func):
	func.allow_anonymous = True
	return func

# quick-and-dirty command-line interface for initialization and management

def setup_db():
	import sys
	
	if "--help" in sys.argv or "--db-path" not in sys.argv:
		print("""cap.py command line - manage a Cap authentication database

Usage:
	python cap.py --db-path PATH [action]

Options:
	--db-path PATH		  This is required for all commands to specify the
							database to affect.  The script will attempt to 
							create all necessary tables (if they do not 
							already exist) before taking other actions.
	
	--add-user USER		 Adds USER to the database.  Will prompt for a 
							password before acting.
	
	--del-user USER		 Removes USER from the database.
	
	--chg-pwd USER		  Changes USER's password.
	
	--create-role ROLE	  Create ROLE.
	
	--delete-role ROLE	  Delete ROLE.
	
	--add-role USER ROLE	Adds ROLE to USER.
	
	--rem-role USER ROLE	Removes ROLE from USER.

""")
		exit()
	
	dbpath = sys.argv[sys.argv.index("--db-path") + 1]
	
	conn = sqlite3.connect(dbpath)
	conn.row_factory = sqlite3.Row;
	conn.execute("PRAGMA foreign_keys = ON;")
	conn.executescript("""
CREATE TABLE IF NOT EXISTS role
(
	role_name VARCHAR NOT NULL PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS user
(
	uuid INTEGER NOT NULL,
	user_name VARCHAR NOT NULL PRIMARY KEY,
	password VARCHAR NOT NULL,
	salt VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS user_roles
(
	user_name VARCHAR NOT NULL REFERENCES user (user_name) ON UPDATE CASCADE ON DELETE CASCADE,
	role_name VARCHAR NOT NULL REFERENCES role (role_name) ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY (user_name, role_name)
);
CREATE TABLE IF NOT EXISTS user_info
(
	user_name VARCHAR NOT NULL REFERENCES user (user_name) ON UPDATE CASCADE ON DELETE CASCADE,
	info_key VARCHAR NOT NULL,
	info_value VARCHAR,
	PRIMARY KEY (user_name, info_key)
);
""")
	conn.commit()
	conn.close()
	
	cap = Cap(dbpath=dbpath)
	
	
	for i in range(0, len(sys.argv)):
		if sys.argv[i] == "--add-user":
			username = sys.argv[i + 1]
			
			print("Enter password for new user `{}`:".format(username))
			password = getpass("> ")
			
			print("Creating user...")
			cap.create_user(username, password)
			print("User `{}` created.".format(username))
			
		elif sys.argv[i] == "--del-user":
			username = sys.argv[i + 1]
			
			print("Deleting user...")
			cap.delete_user(username, password)
			print("User `{}` deleted.".format(username))
			
		elif sys.argv[i] == "--chg-pwd":
			username = sys.argv[i + 1]
			
			print("Enter new password for user `{}`:".format(username))
			password = getpass("> ")
			
			print("Changing password...")
			cap.set_password(username, password)
			print("Password changed for user `{}`.".format(username))
		
		elif sys.argv[i] == "--create-role":
			role = sys.argv[i + 1]
			
			print("Creating role `{}`...".format(role))
			cap.create_roles(role)
			print("Role created.")
		
		elif sys.argv[i] == "--delete-role":
			role = sys.argv[i + 1]
			
			print("Deleting role `{}`...".format(role))
			cap.create_roles(role)
			print("Role deleted.")
		
		elif sys.argv[i] == "--add-role":
			user = sys.argv[i + 1]
			role = sys.argv[i + 2]
			
			print("Adding role `{}` to user `{}`...".format(user, role))
			cap.set_user_roles(user, [role])
			print("Role added.")
		
		elif sys.argv[i] == "--rem-role":
			user = sys.argv[i + 1]
			role = sys.argv[i + 2]
			
			print("Removing role `{}` from user `{}`...".format(user, role))
			cap.set_user_role(user, role)
			print("Role removed.")
		
if __name__ == "__main__":setup_db()