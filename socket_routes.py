'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request, session
import db

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

room = Room()

timestamp = 0

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = session.get("user_id")
    # prevents client from changing username 
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

# send message event handler for status messages
@socketio.on("send") 
def send(username, friend, message, room_id):
    # If Staff user issues a command using "!", then don't store in message history + execute the command
    if db.get_user_role(username) != "Student" and message[0] == "!":
        if username == "Admin":
            is_failed = False
            if "!role set" in message and len(message.split()) > 3:
                # Check that Admin is not setting their own role, that that user gaining the role exists
                if message.split()[2] != "Admin":
                    if not db.get_user(message.split()[2]):
                        emit("incoming", "User Doesn't Exist!", to=None, include_self=True)
                        return
                    db.update_role(message.split()[2], message.split()[3])
                    emit("incoming", "Role set.", to=None, include_self=True)
                else:
                    emit("incoming", "Can't Set Your Own Role!", to=None, include_self=True)
                    return
            elif "!role delete" in message:
                # Check that Admin is not setting their own role, that that user gaining the role exists
                if message.split()[2] != "Admin":
                    if not db.get_user(message.split()[2]):
                        emit("incoming", "User Doesn't Exist!", to=None, include_self=True)
                        return
                    db.update_role(message.split()[2], "Student")
                    emit("incoming", "Role deleted.", to=None, include_self=True)
                else:
                    emit("incoming", "Can't Delete Your Own Role!", to=None, include_self=True)
                    return
            elif "!mute" in message and len(message.split()) > 1:
                # Check that user is not muting themselves, that that user being muted exists, and that they're a student
                if message.split()[1] != username:
                    if not db.get_user(message.split()[1]):
                        emit("incoming", "User Doesn't Exist!", to=None, include_self=True)
                        return
                    db.mute_user(message.split()[1])
                    emit("incoming", "User Muted.", to=None, include_self=True)
                else:
                    emit("incoming", "You Cannot Mute Yourself!", to=None, include_self=True)
                    return
            elif "!unmute" in message and len(message.split()) > 1:
                # Check that user is not muting themselves, that that user being muted exists, and that they're a student
                if message.split()[1] != username:
                    if not db.get_user(message.split()[1]):
                        emit("incoming", "User Doesn't Exist!", to=None, include_self=True)
                        return
                    db.unmute_user(message.split()[1])
                    emit("incoming", "User Unmuted.", to=None, include_self=True)
                else:
                    emit("incoming", "You Cannot Unmute Yourself!", to=None, include_self=True)
                    return    
                
            else:
                is_failed = True
                
            if is_failed:
                msg = ["Admin Commands:", "- !role set <username> <role>", "- !role delete <username>", "- !mute <username>", "- !unmute <username>"]
                for m in msg:
                    emit("incoming", m, to=None, include_self=True)
        # For all remaining staff
        else:        
            is_failed = False
            if "!mute" in message and len(message.split()) > 1:
                # Check that user is not muting themselves, that that user being muted exists, and that they're a student
                if message.split()[1] != username:
                    if not db.get_user(message.split()[1]):
                        emit("incoming", "User Doesn't Exist!", to=None, include_self=True)
                        return
                    elif message.split()[1] == "Admin":
                        emit("incoming", "You Cannot Mute Admin!", to=None, include_self=True)
                        return
                    elif db.get_user_role(message.split()[1]) != "Student":
                        emit("incoming", "You Cannot Mute Staff Members!", to=None, include_self=True)
                        return
                    db.mute_user(message.split()[1])
                    emit("incoming", "User muted.", to=None, include_self=True)
                else:
                    emit("incoming", "You Cannot Mute Yourself!", to=None, include_self=True)
                    return
            elif "!unmute" in message and len(message.split()) > 1:
                # Check that user is not muting themselves, that that user being muted exists, and that they're a student
                if message.split()[1] != username:
                    if not db.get_user(message.split()[1]):
                        emit("incoming", "User Doesn't Exist!", to=None, include_self=True)
                        return
                    elif message.split()[1] == "Admin":
                        emit("incoming", "You Cannot Unmute Admin!", to=None, include_self=True)
                        return
                    elif db.get_user_role(message.split()[1]) != "Student":
                        emit("incoming", "You Cannot Unmute Staff Members!", to=None, include_self=True)
                        return
                    db.unmute_user(message.split()[1])
                    emit("incoming", "User Unmuted.", to=None, include_self=True)
                else:
                    emit("incoming", "You Cannot Unmute Yourself!", to=None, include_self=True)
                    return
            else:
                    is_failed = True
          
            if is_failed:
                msg = ["Staff Commands:", "- !mute <username>", "- !unmute <username>"]
                for m in msg:
                    emit("incoming", m, to=None, include_self=True)
        
        return
        
    global timestamp
    timestamp += 1
    emit("incoming", (f"{username}: {message}"), to=room_id)
    
    # Get the latest timestamp
    tm = db.get_latest_timestamp()
    if tm:
        tm += 1
    else:
        tm = timestamp
    
    # Store messages in database for current user and their friend (person they clicked on to join the chat)
    db.add_message_sender(username, friend, message, tm)
    db.add_message_recipient(friend, username, message, tm)
    
    # Get a list of the people in the current chatroom
    room_id = db.get_userroom_id(username)
    friends = db.get_userroom_names(room_id[0][0])

    # Store messages in database for all other users in the chatroom
    for fr in friends:
        if fr[0] != username and fr[0] != friend:
            db.add_message_sender(username, fr[0], message, tm)
            db.add_message_recipient(fr[0], username, message, tm)
          
    
# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):
    if db.is_user_muted(sender_name):
        return "You Have Been Muted!"
    
    global timestamp
    
    receiver = db.get_user(receiver_name)
    
    if receiver is None:
        return "User doesn't exist!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"
    
    room_id = room.get_room_id(receiver_name)

    # if the user is already inside of a room 
    if room_id is not None:
        room.join_room(sender_name, room_id)
        join_room(room_id)
        
        # Update userroom database with an entry of current user + room_id
        if not db.get_userroom_id(sender_name):
            db.add_userroom(sender_name, room_id)

        # Retrieve message history of users in current chatroom
        friends = db.get_userroom_names(room_id)
        
        dict = db.get_messages(sender_name, receiver_name)
        dict_new = {}
        
        for fr in friends:
            if fr[0] != sender_name and fr[0] != receiver_name:
                # Retrieve message history for both sender and receiver
                dict_new = db.get_messages(sender_name, fr[0])
                dict.update(dict_new)
            
        # If message history exists
        if dict:
            # Sort the entries by their keys (by timestamp)
            keys = list(dict.keys())
            keys.sort()
            # Store last timestamp in the global variable
            timestamp = keys[-1]
            # Update dict with sorted entries based on timestamps
            dict = {i: dict[i] for i in keys}
            
            # Make a list of the sorted values (usernames/messages)
            values = list(dict.values())
        else:
            timestamp = 0
            values = []
            
        # emit message history to current user only
        if values:
            for v in values:
                emit("incoming", (f"{v[0]}: {v[1]}"), to=None, include_self=True)
                
        for i in range(len(friends)):
            if friends[i][0] == sender_name:
                friends.remove(friends[i])
                
        talking_to = ""
        if len(friends) > 1:
            for i in range(len(friends)):
                if i != len(friends) - 1:
                    talking_to += friends[i][0]
                    if len(friends) > 2:
                        talking_to += ", "
                else:
                    talking_to += " and " + friends[i][0]
        else:
            talking_to = receiver_name
        
        # emit to everyone in the room except the sender
        emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
        # emit only to the sender
        emit("incoming", (f"{sender_name} has joined the room. Now talking to {talking_to}.", "green"))
        
        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone
    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)
    
    # Update userroom database with an entry of current user + room_id
    if not db.get_userroom_id(sender_name):
        db.add_userroom(sender_name, room_id)
    
    # Retrieve message history of users in current chatroom
    friends = db.get_userroom_names(room_id)
    
    dict = db.get_messages(sender_name, receiver_name)
    dict_new = {}
    
    for fr in friends:
        if fr[0] != sender_name and fr[0] != receiver_name:
            # Retrieve message history for both sender and receiver
            dict_new = db.get_messages(sender_name, fr[0])
            dict.update(dict_new)
        
    # If message history exists
    if dict:
        # Sort the entries by their keys (by timestamp)
        keys = list(dict.keys())
        keys.sort()
        # Store last timestamp in the global variable
        timestamp = keys[-1]
        # Update dict with sorted entries based on timestamps
        dict = {i: dict[i] for i in keys}
        
        # Make a list of the sorted values (usernames/messages)
        values = list(dict.values())
    else:
        timestamp = 0
        values = []
        
    # emit message history to current user only
    if values:
        for v in values:
            emit("incoming", (f"{v[0]}: {v[1]}"), to=None, include_self=True)
            
    emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"), to=room_id)

    return room_id

# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username)    

# add user to online table in db when opening or refreshing the window
@socketio.on('client_connecting')
def client_connecting(username):
    db.add_online(username)

# remove user from online table in db when closing window or tab
@socketio.on('client_disconnecting')
def client_disconnecting(username):
    db.delete_online(username)

# clear user's entry in userrooms table when leaving a chatroom
@socketio.on('leave_room')
def leave_room(username):
    db.delete_userroom(username)
    room.reset_room_id(username)