'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Dict

# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    salt: Mapped[str] = mapped_column(String) 
    role: Mapped[str] = mapped_column(String)
    mute: Mapped[int] = mapped_column(Integer)   
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data o
    # f type string
    # in other words we've mapped the username Python object property to an SQL column of type String  
    
class Friend(Base):
    __tablename__ = "friends"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    friend: Mapped[str] = mapped_column(String)
    
class Request(Base):
    __tablename__ = "requests"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    friend: Mapped[str] = mapped_column(String)
    
class Message(Base):
    __tablename__ = "messages"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    sender: Mapped[str] = mapped_column(String)
    recipient: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    timestamp: Mapped[int] = mapped_column(Integer)

class Online(Base):
    __tablename__ = "online"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    
class Userrooms(Base):
    __tablename__ = "userrooms"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    room: Mapped[str] = mapped_column(Integer)    
    
    
class Articles(Base):
    __tablename__ = "articles"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    
class Comments(Base):
    __tablename__ = "comments"
    
    title: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String)
    comment: Mapped[str] = mapped_column(String)

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
    # gets the room id from a user
    def reset_room_id(self, user: str):
        del self.dict[user]
    
