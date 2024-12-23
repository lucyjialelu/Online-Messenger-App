'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.orm import Session
import sqlalchemy as sql
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=True)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str, salt: str, role: str): #hashed_pwd: str hashed_pwd=hashed_pwd
    with Session(engine) as session:        
        user = User(username=username, password=password, salt=salt, role=role, mute=0)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

# get a user's password
def get_user_password(username: str):
    with Session(engine) as session:
        res = session.query(User.password).filter(User.username==username).all()
        if res:
            return res[0][0]
        else:
            return None

# get a user's salt    
def get_user_salt(username: str):
    with Session(engine) as session:
        res = session.query(User.salt).filter(User.username==username).all()
        if res:
            return res[0][0]
        else:
            return None
    

# get a user's role
def get_user_role(username: str):
    with Session(engine) as session:
        res = session.query(User.role).filter(User.username==username).all()
        if res:
            return res[0][0]
        else:
            return None
        
# update a user's role
def update_role(username: str, role: str):
    with Session(engine) as session:
        session.query(User).filter_by(username=username).update({"role": role})
        session.commit()
        
# find out if user is muted
def is_user_muted(username: str):
    with Session(engine) as session:
        res = session.query(User.mute).filter(User.username==username).first()
        if res:
            return res[0]
        else:
            return None

# mute a user (only accessible by staff)
def mute_user(username: str):
    with Session(engine) as session:
        session.query(User).filter_by(username=username).update({"mute": 1})
        session.commit()
        
# unmute a user (only accessible by staff)
def unmute_user(username: str):
    with Session(engine) as session:
        session.query(User).filter_by(username=username).update({"mute": 0})
        session.commit()
    
# remove a user from the database
def delete_user(username:str):
    with Session(engine) as session:
        user = User.__table__.delete().filter(User.username==username)
        session.execute(user)
        session.commit()
    
# inserts a friend request into the database
def add_request(username: str, friend: str):
    with Session(engine) as session:
        requests = Request(username=username, friend=friend)
        session.add(requests)
        session.commit()
        
# remove a friend request from the database
def delete_request(username:str, friend: str):
    with Session(engine) as session:
        req = Request.__table__.delete().filter(Request.username==friend).filter(Request.friend==username)
        session.execute(req)
        session.commit()

# gets a list of names of users that the current user has sent a friend request to
def get_requests_by(username: str):
    with Session(engine) as session:
        return session.query(Request.friend).filter(Request.username==username)

# gets a list of names of users that have sent the current user a friend request
def get_requests_for(username: str):
    with Session(engine) as session:
        return session.query(Request.username).filter(Request.friend==username)
        
# inserts a friend into the database
def add_friend(username: str, friend: str):
    with Session(engine) as session:
        friends = Friend(username=username, friend=friend)
        session.add(friends)
        session.commit()
    
# gets a friend from the database
def get_friends(username: str):
    with Session(engine) as session:
        return session.query(Friend.friend).filter(Friend.username==username)
    
# remove a friend from the database
def delete_friend(username:str, friend: str):
    with Session(engine) as session:
        friend = Friend.__table__.delete().filter(Friend.username==friend).filter(Friend.friend==username)
        session.execute(friend)
        session.commit()
        
        
# remove yourself as someone's friend from the database
def delete_friend2(username:str, friend: str):
    with Session(engine) as session:
        friend = Friend.__table__.delete().filter(Friend.username==username).filter(Friend.friend==friend)
        session.execute(friend)
        session.commit()

# inserts a message into the database for a user who is a sender
def add_message_sender(username: str, recipient: str, message: str, timestamp: int):
    with Session(engine) as session:
        # Store one message history for the current user (sender)
        messages = Message(username=username, sender=username, recipient=recipient, message=message, timestamp=timestamp)
        session.add(messages)
        session.commit()
        
# inserts a message into the database for a user who is a recipient
def add_message_recipient(username: str, sender: str, message: str, timestamp: int):
    with Session(engine) as session:
        # Store one message history for the current user (sender)
        messages = Message(username=username, sender=sender, recipient=username, message=message, timestamp=timestamp)
        session.add(messages)
        session.commit()
        
def get_messages(username: str, recipient: str):
    with Session(engine) as session:
        # Retrieve messages and their timestamps for current user
        # Retrieve timestamps where current user is sender and friend is recipient
        timestamp = session.query(Message.timestamp).filter(Message.username==username).filter(Message.sender==username).filter(Message.recipient==recipient).all()
        # Retrieve timestamps where current user is recipient and friend is sender
        timestamp2 = session.query(Message.timestamp).filter(Message.username==username).filter(Message.sender==recipient).filter(Message.recipient==username).all()
        # Retrieve messages where username is sender and friend is recipient
        messages = session.query(Message.message).filter(Message.username==username).filter(Message.sender==username).filter(Message.recipient==recipient).all()
        # Retrieve messages where current user is recipient and friend is sender
        messages2 = session.query(Message.message).filter(Message.username==username).filter(Message.sender==recipient).filter(Message.recipient==username).all()

        dict = {}

        # Make a dictionary containing key:value pairs with format timestamp:[sender, message]
        for i in range(len(timestamp)):
            dict[int(timestamp[i][0])] = [username, messages[i][0]]
        
        # Continue with lists where recipient was the sender and username was recipient
        for i in range(len(timestamp2)):
            dict[int(timestamp2[i][0])] = [recipient, messages2[i][0]]
            
        return dict
    
# Retrieve the lastest timestamp for a user
def get_latest_timestamp():
    with Session(engine) as session:
        # get timestamps
        timestamp = session.query(Message.timestamp).all()

        timestamps = []

        # Populate list with timestamps
        if timestamp:
            for i in range(len(timestamp)):
                timestamps.append(int(timestamp[i][0]))
            
            # Return max timestamp 
            return max(timestamps)
        # Else return nothing        
        else:
            return timestamps

# adds a user as online to the database
def add_online(username: str): #hashed_pwd: str hashed_pwd=hashed_pwd
    with Session(engine) as session:
        user = Online(username=username)
        session.add(user)
        session.commit()

# gets a user from the database
def get_online():
    with Session(engine) as session:
        return session.query(Online.username)
    
# remove a friend request from the database
def delete_online(username:str):
    with Session(engine) as session:
        user = Online.__table__.delete().filter(Online.username==username)
        session.execute(user)
        session.commit()

# Assign a room number for people joining a room
def add_userroom(username: str, room_id: int):
    with Session(engine) as session:
        user = Userrooms(username=username, room=room_id)
        session.add(user)
        session.commit()

# Get the room number that a user is in 
def get_userroom_id(username: str):
    with Session(engine) as session:
        return session.query(Userrooms.room).filter(Userrooms.username==username).all()

# Get all the names of users in a room  
def get_userroom_names(room_id: int):
    with Session(engine) as session:
        return session.query(Userrooms.username).filter(Userrooms.room==room_id).all()

# Remove a userroom entry
def delete_userroom(username: str):
    with Session(engine) as session:
        user = Userrooms.__table__.delete().filter(Userrooms.username==username)
        session.execute(user)
        session.commit()
        
# creates a new article entry in the database
def create_article(username: str, role: str, title: str, content: str):
    with Session(engine) as session:        
        article = Articles(username=username, role=role, title=title, content=content)
        session.add(article)
        session.commit()
        
# gets the name of a user that owns an article
def get_article_owner(title: str):
    with Session(engine) as session:        
        res = session.query(Articles.username).filter(Articles.title==title).all()
        if res:
            return res[0][0]
        else:
            return None
        
# gets the role of a user that owns an article
def get_article_owner_role(title: str):
    with Session(engine) as session:        
        res = session.query(Articles.role).filter(Articles.title==title).all()
        if res:
            return res[0][0]
        else:
            return None
        
# gets the role of a user that owns an article
def get_article_owner_role_by_name(username: str):
    with Session(engine) as session:        
        res = session.query(Articles.role).filter(Articles.username==username).all()
        if res:
            return res[0][0]
        else:
            return None
        
# gets the content of an article
def get_article_content(title: str):
    with Session(engine) as session:        
        res = session.query(Articles.content).filter(Articles.title==title).all()
        if res:
            return res[0][0]
        else:
            return None
        
# update article content
def update_content(title: str, content: str):
    with Session(engine) as session:
        session.query(Articles).filter_by(title=title).update({"content": content})
        session.commit()
        
# update article title
def update_title(title: str, new_title: str):
    with Session(engine) as session:
        session.query(Articles).filter_by(title=title).update({"title": new_title})
        session.commit()

# retrieves all student articles
def get_all_articles():
    with Session(engine) as session:
        # Get usernames, roles, article titles and content
        users = session.query(Articles.username).all()
        roles = session.query(Articles.role).all()
        titles = session.query(Articles.title).all()
        content = session.query(Articles.content).all()
    
        articles = []

        # Make a dictionary containing key:value pairs with format timestamp:[sender, message]
        if users:
            for i in range(len(users)):
                articles.append((users[i][0], roles[i][0], titles[i][0], content[i][0]))
          
        return articles
    
# retrieves all staff articles
def get_staff_articles():
    with Session(engine) as session:
        role = ""
        # Get usernames and article titles
        users = session.query(Articles.username).filter(Articles.role==role).all()
        titles = session.query(Articles.title).filter(Articles.role==role).all()
        content = session.query(Articles.content).filter(Articles.role==role).all()
    
        articles = []

        if users:
            for i in range(len(users)):
                articles.append((users[i][0], titles[i][0], content[i][0]))
          
        return articles
        
# deletes an article from the database
def delete_article(title: str):
    with Session(engine) as session:        
        article = Articles.__table__.delete().filter(Articles.title==title)
        session.execute(article)
        session.commit()
        
# creates a new comment entry in the database
def add_comment(title: str, username: str, comment: str):
    with Session(engine) as session:        
        com = Comments(title=title, username=username, comment=comment)
        session.add(com)
        session.commit()
        
# retrieves all comments for an article
def get_articles_comments(title: str):
    with Session(engine) as session:
        # Get user comments
        users = session.query(Comments.username).filter(Comments.title==title).all()
        coms = session.query(Comments.comment).filter(Comments.title==title).all()
    
        comments = []

        if users:
            for i in range(len(users)):
                comments.append((users[i][0], coms[i][0]))
          
        return comments
    
# update article title for comments when title is modified
def update_article_title_comments(title: str, new_title: str):
    with Session(engine) as session:
        session.query(Comments).filter_by(title=title).update({"title": new_title})
        session.commit()
        
# deletes a comment from the database
def delete_comment(title: str, username: str, comment: str):
    with Session(engine) as session:        
        com = Comments.__table__.delete().filter(Comments.title==title).filter(Comments.username==username).filter(Comments.comment==comment)
        session.execute(com)
        session.commit()
        
# deletes all comments for an article from the database
def delete_articles_comments(title: str):
    with Session(engine) as session:        
        com = Comments.__table__.delete().filter(Comments.title==title)
        session.execute(com)
        session.commit()