from .helpers import db

class sessions(db.Model):
	id = db.Column('integer', primary_key=True)
	key = db.Column('text', null=True)
	data = db.Column("text")

db.init(sessions)
