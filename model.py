from peewee import Model, CharField, SqliteDatabase

db = SqliteDatabase('messages.db')

class Message(Model):
    role = CharField()
    content = CharField()

    class Meta:
        database = db

db.connect()
db.create_tables([Message])
