'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, session
from flask_socketio import SocketIO
import db
import secrets
import hashlib
import os
import bcrypt

import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    session.permanent = True
    session["user_id"] = username

    password = request.json.get("password")

    user = db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    # Server side hashing to compare with hash digest stored
    # pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest() # returns hex of a pwd
    # first_hash = bytes.fromhex(user.salt) + bytes.fromhex(pwd_hash) # convert into bytes
    # hashed_pwd = hashlib.sha256(first_hash).hexdigest()

    hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), user.salt.encode('utf-8'))

    if user.password != hashed_pwd.decode('utf-8'):
        # need to hash things then compare
        return "Error: Password does not match!"
    
    return url_for('home', username=username)

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
        
    username = request.json.get("username")
    password = request.json.get("password")
    salt = request.json.get("salt")

    # # Server-side hashing
    # salt = os.urandom(64) # returns 64 bytes
    # pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest() # returns hex of a string
    # first_hash = salt + bytes.fromhex(pwd_hash) # bytes
    # hashed_pwd = hashlib.sha256(first_hash).hexdigest() # sha256(sha265(pwd)+salt)

    if db.get_user(username) is None:
        session.permanent = True
        session["user_id"] = username
        db.insert_user(username, password, salt, "Student") #hashed_pwd
        db.add_online(username) # log the user as online
        # Add user to Admin's friend list and vice versa
        db.add_friend("Admin", username)
        db.add_friend(username, "Admin")
        return url_for('home', username=username)
    return "Error: User already exists!"

# handles a post request when the user clicks the add friend button
@app.route("/home", methods=["POST"])
def add_request():
    if not request.is_json:
        abort(404)
    username = request.cookies.get("username")
    # maybe = session.get("user_id")? 
    friend = request.json.get("friend")
    
    # Check if user is trying to add themselves
    if username == friend:
        return "Error: You can't add yourself!"
    # Check if new friend exists as a user
    elif not db.get_user(friend):
        return "Error: User does not exist!"

    # Check if user already has this friend (prevents duplicate entries)
    friend_exists = False  
    for i in db.get_friends(username):
        if i[0] == friend:
            friend_exists = True
            break
        
    # Check if user has already sent this friend a request
    request_exists_by = False  
    for i in db.get_requests_by(username):
        if i[0] == friend:
            request_exists_by = True
            break
    
    # Check if user has already received a request from this friend
    request_exists_for = False
    for i in db.get_requests_for(username):
        if i[0] == friend:
            request_exists_for = True
            break
    
    # If user already has this friend
    if friend_exists:
        return "Error: Friend already exists!"  
    # If user has already sent this friend a request
    elif request_exists_by:
        return "Error: Request already sent!"
    # If user has already received a request from this friend
    elif request_exists_for:
        return None
    else:
        # Add friend to database
        db.add_request(username, friend)     
        return url_for('home', username=username)

# handles accepting of friends requests
@app.route("/accept_friend", methods=["POST"])
def accept_friend():
    if not request.is_json:
        abort(404)

    username = request.cookies.get("username")
    friend = request.json.get("friend")
    
    # Add friend to database
    db.add_friend(username, friend)
    # Do the same for the friend (add current user as a friend of theirs)
    db.add_friend(friend, username)
    # Remember to remove the friend request from the database
    db.delete_request(username, friend)
    return url_for('home', username=username)

# handles declined friends requests
@app.route("/decline_friend", methods=["POST"])
def decline_friend():
    if not request.is_json:
        abort(404)
    
    username = request.cookies.get("username")
    friend = request.json.get("friend")
    
    # Remove the friend request from the database
    db.delete_request(username, friend)
    return url_for('home', username=username)

# handles declined friends requests
@app.route("/delete_friend", methods=["POST"])
def delete_friend():
    if not request.is_json:
        abort(404)
    
    username = request.cookies.get("username")
    friend = request.json.get("friend")
    
    # Check if user is trying to delete themselves
    if username == friend:
        return "Error: Cannot delete yourself!"
    # Prevent user from tyring to delete Admin
    elif friend == "Admin":
        return "Error: Cannot delete Admin!"
    

    # Check if user actually has this friend
    friend_exists = False  
    for i in db.get_friends(username):
        if i[0] == friend:
            friend_exists = True
            break

    if friend_exists:
        # Remove the friend request from the database
        db.delete_friend(username, friend)
        db.delete_friend2(username, friend)
        return url_for('home', username=username)
    else:
        return "Error: Friend doesn't exist!"
    
# articles page
@app.route("/articles")
def articles():
    # Get username and role
    username = session.get("user_id")
    user_role = db.get_user_role(username)
    
    # Retrieve all articles        
    articles = db.get_all_articles()
    student_articles = []
    staff_articles = []
    
    # Populate student and staff article lists with tuples: (article title, username)
    for i in articles:
        if i[1] == "Student":
            student_articles.append((i[2], i[0]))
        else:
            staff_articles.append((i[2], i[0]))
        
    student_articles.sort(key=lambda tuple: tuple[0].lower())
    staff_articles.sort(key=lambda tuple: tuple[0].lower())
        
    return render_template("articles.jinja", username=username, user_role=user_role, student_articles=student_articles, staff_articles=staff_articles)

# leave article creation, display, or modify pages back to articles page
@app.route("/leave", methods=["POST"])
def leave():
    if not request.is_json:
        abort(404)
    
    return url_for('articles')

# articles creation page
@app.route("/articles_creation")
def load_creation():
    # Get username and role
    username = session.get("user_id")
    user_role = db.get_user_role(username)

    # Grab article name and remove the dictionary entry
    article_title = session.get("article_title")
    del session["article_title"]
   
    return render_template("articles_create.jinja", username=username, user_role=user_role, article_title=article_title)

# articles creation page
@app.route("/articles_creation", methods=["POST"])
def articles_creation():
    if not request.is_json:
        abort(404)
    
    # Get username and check if user has been muted
    username = session.get("user_id")
    if db.is_user_muted(username):
        return "You Have Been Muted!"
    
    # Grab the article name from the javascript and assign it to session dictionary
    article_title = request.json.get("article")
    session["article_title"] = article_title
    
    for i in db.get_all_articles():
        if i[2] == article_title:
            return "Error: An article with this title already exists!"
    
    return url_for('articles_creation')

# handles article creation
@app.route("/create_article", methods=["POST"])
def create_article():
    if not request.is_json:
        abort(404)
        
    username = session.get("user_id")
    if db.is_user_muted(username):
        return "You Have Been Muted!"
    
    user_role = db.get_user_role(username)

    # get username from javascript in case anonymous
    if request.json.get("username"):
        username = request.json.get("username")
    
    # get article title and article content
    article_title = request.json.get("article_title")
    content = request.json.get("content")
    
    # create article
    db.create_article(username, user_role, article_title, content)
    
    return url_for('articles')

# articles creation page
@app.route("/articles_display")
def load_display():
    # Get username and role
    username = session.get("user_id")
    user_role = db.get_user_role(username)

    # Grab article name and remove the dictionary entry
    article_title = session.get("article_title")
    del session["article_title"]
    article_owner = db.get_article_owner(article_title)
    content = db.get_article_content(article_title)
    article_owner_role = db.get_article_owner_role(article_title)
    
    comments = db.get_articles_comments(article_title)
    
    return render_template("articles_display.jinja", username=username, user_role=user_role, article_title=article_title, article_owner=article_owner, article_owner_role=article_owner_role, content=content, comments=comments)

# articles creation page
@app.route("/articles_display", methods=["POST"])
def articles_display():
    if not request.is_json:
        abort(404)
        
    # Grab the article name from the javascript and assign it to session dictionary
    article_title = request.json.get("article")
    session["article_title"] = article_title
    
    return url_for('articles_display')

# articles modify page
@app.route("/articles_modify")
def load_modify():
    # Get username and role
    username = session.get("user_id")
    user_role = db.get_user_role(username)

    # Grab article name and remove the dictionary entry
    article_title = session.get("article_title")
    del session["article_title"]
    
    article_owner = db.get_article_owner(article_title)
    content = db.get_article_content(article_title)
    article_owner_role = db.get_user_role(article_owner)
   
    return render_template("articles_modify.jinja", username=username, user_role=user_role, article_title=article_title, article_owner=article_owner, article_owner_role=article_owner_role, content=content)

# articles modify page
@app.route("/articles_modify", methods=["POST"])
def articles_modify():
    if not request.is_json:
        abort(404)
    
    # Get username and check if user has been muted
    username = session.get("user_id")
    if db.is_user_muted(username):
        return "You Have Been Muted!"
    
    # Get current user's role, article title, owner of the article
    user_role = db.get_user_role(username)
    article_title = request.json.get("article")
    article_owner = db.get_article_owner(article_title)
    
    # Check that the article exists and that the current user is either the owner or a staff member
    if article_owner:
        if username == "Admin":
            pass
        # If user is a staff member and article is owned by another staff member
        elif article_owner != username and user_role != "Student" and db.get_article_owner_role(article_title) != "Student":
            return "Error: You can't modify articles owned by other staff members!"
        # If user is not the owner of the article
        elif article_owner != username and user_role == "Student" :
            return "Error: Your are not the owner of this article!"
    else:
        return "Error: Article doesn't exist!"
    
    session["article_title"] = article_title
    
    return url_for('articles_modify')

# handles article modification
@app.route("/modify_article", methods=["POST"])
def modify_article():
    if not request.is_json:
        abort(404)
        
    username = session.get("user_id")
    if db.is_user_muted(username):
        return "You Have Been Muted!"

    # get username and role
    username = request.cookies.get("username")
    
    # get article title and article content
    article_title = request.json.get("article_title")
    new_title = request.json.get("new_title")
    content = request.json.get("content")
    
    for i in db.get_all_articles():
        if i[2] == new_title:
            return "Error: An article with this title already exists!"
    
    # update article
    db.update_title(article_title, new_title)
    db.update_content(new_title, content)
    db.update_article_title_comments(article_title, new_title)
    
    return url_for('articles')
    
# handles declined friends requests
@app.route("/delete_article", methods=["POST"])
def delete_article():
    if not request.is_json:
        abort(404)
         
    # Get username and check if user has been muted
    username = request.cookies.get("username")
    if db.is_user_muted(username):
        return "You Have Been Muted!"
    
    # Get current user's role, article title, owner of the article
    user_role = db.get_user_role(username)
    article_title = request.json.get("article")
    article_owner = db.get_article_owner(article_title)
    
    # Check that the article exists and that the current user is either the owner or a staff member
    if article_owner:
        if username == "Admin":
            db.delete_article(article_title)
            db.delete_articles_comments(article_title)
            return url_for('articles')
        # If user is a staff member and article is owned by another staff member
        elif article_owner != username and user_role != "Student" and db.get_article_owner_role(article_title) != "Student":
            return "Error: You can't delete articles owned by other staff members!"
        # If user is not the owner of the article
        elif article_owner != username and user_role == "Student":
            return "Error: Your are not the owner of this article!"
        else:
            db.delete_article(article_title)
            db.delete_articles_comments(article_title)
            return url_for('articles')
    else:
        return "Error: Article doesn't exist!"
    
    
# post a comment
@app.route("/post_comment", methods=["POST"])
def post_comment():
    if not request.is_json:
        abort(404)
        
    # Get username and check if user has been muted
    username = request.cookies.get("username")
    if db.is_user_muted(username):
        return "You Have Been Muted!"
    
    if username == None:
        return url_for('articles_display')
    
    # get username from javascript in case anonymous
    if request.json.get("username"):
        username = request.json.get("username")
    
    article_title = request.json.get("article_title")
    session["article_title"] = article_title
    comment = request.json.get("comment")
    
    db.add_comment(article_title, username, comment)
    
    return url_for('articles_display')

# post a comment
@app.route("/delete_comment", methods=["POST"])
def delete_comment():
    
    if not request.is_json:
        abort(404)
        
    # Get username and check if user has been muted
    username = request.cookies.get("username")
    if db.is_user_muted(username):
        return "You Have Been Muted!"
    
    user_role = db.get_user_role(username)
    
    article_title = request.json.get("article_title")
    session["article_title"] = article_title
    com = request.json.get("stored_comment")
    
    if com == "":
        return "Error: Please select a comment to delete!"
    
    comments = db.get_articles_comments(article_title)
    
    comment_user = ""
    comment = ""
    
    for i in comments:
        comm_temp = f"{i[1]} - {i[0]}"
        if com == comm_temp:
            comment_user = i[0]
            comment = i[1]
            break

    # Check that the article exists and that the current user is either the owner or a staff member
    if comment_user:
        if username == "Admin":
            pass
        # If user is a staff member and article is owned by another staff member
        elif comment_user != username and user_role != "Student" and db.get_user_role(comment_user) != "Student":
            return "Error: You can't modify comments by other staff members!"
        # If user is not the owner of the article
        elif comment_user != username:
            return "Error: Your are not the owner of this comment!"
    
    db.delete_comment(article_title, comment_user, comment)
    
    return url_for('articles_display')

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    # Get username
    username = session.get("user_id")
    user_role = db.get_user_role(username)

    # Create a list to store friends
    friends = []
    # Populate friends list
    for i in db.get_friends(username):
        friends.append(i[0])
    
    # Store online and offline friends in a list and their roles in another list
    online_friends = []
    # Populate users online list
    for i in db.get_online():
        if i[0] in friends:
            role = db.get_user_role(i[0])
            fr = (i[0], role)
            online_friends.append(fr)
            
    offline_friends = []
    for i in friends:
        if i not in online_friends:
            role = db.get_user_role(i)
            fr = (i, role)
            offline_friends.append(fr)
            
    # Create a list to store requests
    requests_for = []
    # Populate friends list
    for i in db.get_requests_for(username):
        requests_for.append(i[0])
        
    requests_by = []
    # Populate friends list
    for i in db.get_requests_by(username):
        requests_by.append(i[0])
    
    return render_template("home.jinja", username=username, user_role=user_role, online_friends=online_friends, offline_friends=offline_friends, requests_for=requests_for, requests_by=requests_by) 
        
if __name__ == '__main__':
        socketio.run(app, ssl_context=('./certs/localhost.crt', './certs/localhost.key'))
