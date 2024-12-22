from peewee import Model, CharField, SqliteDatabase, ForeignKeyField, DateTimeField
from datetime import datetime

db = SqliteDatabase('messages.db')

class Thread(Model):
    name = CharField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db

class Message(Model):
    role = CharField()
    content = CharField()
    thread = ForeignKeyField(Thread, backref='messages')

    class Meta:
        database = db

db.connect()
db.create_tables([Thread, Message])