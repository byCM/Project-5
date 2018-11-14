import datetime

from flask.ext.bcrypt import generate_password_hash
from flask.ext.login import UserMixin
from peewee import *

DATABASE = SqliteDatabase('journal.db')

class User(UserMixin, Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    join_date = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)
    
    
    class Meta:
        database = DATABASE
        order_by = ('-join_date',)
        
        
    def get_posts(self):
        return Post.select().where(Post.user == self)
      
    def get_stream(self):
        return Post.select().where(
            (Post.user == self)
      )


    @classmethod   
    def create_user(cls, username, email, password, admin=False):
        try:
            with DATABASE.transaction(): 
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin)
        except IntegrityError:
            raise ValueError("User already exists")


class Post(Model):
    title = CharField(max_length=50)
    date = DateField()
    time_spent = CharField(max_length=50)
    learning = TextField()
    resources = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(
        rel_model=User,
        related_name='posts'
    )
    
    class Meta:
        database = DATABASE
        order_by = ('-date',)

        
    @classmethod
    def create_entry(cls, title, date, time_spent, learning,
                     resources, user):
        with DATABASE.transaction():
            cls.create(
                title=title,
                date=date,
                time_spent=time_spent,
                learning=learning,
                resources=resources,
                user=user,
            )
    
           
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post], safe=True)
    DATABASE.close()
