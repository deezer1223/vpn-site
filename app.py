#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from threading import Lock
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO
import uuid
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '123154687513545641213546541313'
app.config['DATABASE_FILE'] = 'db.dat'
socketio = SocketIO(app)
db_lock = Lock()

# Hacker renk paleti
HACKER_COLORS = ['#00FF00', '#FF0000', '#00FFFF', '#FF00FF', '#FFFF00']

def load_db():
    try:
        with open(app.config['DATABASE_FILE'], 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}, "messages": [], "files": {}}

def save_db(data):
    with db_lock:
        with open(app.config['DATABASE_FILE'], 'w') as f:
            json.dump(data, f)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = load_db()
        user_id = str(uuid.uuid4())
        color = random.choice(HACKER_COLORS)
        
        db['users'][user_id] = {
            "nickname": request.form['nickname'],
            "color": color,
            "last_seen": datetime.now().isoformat()
        }
        
        save_db(db)
        
        session['user_id'] = user_id
        session['nickname'] = request.form['nickname']
        session['color'] = color
        
        return redirect(url_for('index'))
    return render_template('login.html')

@socketio.on('message')
def handle_message(msg):
    db = load_db()
    message_id = str(uuid.uuid4())
    
    db['messages'].append({
        "id": message_id,
        "user_id": session['user_id'],
        "text": msg,
        "timestamp": datetime.now().isoformat(),
        "color": session['color']
    })
    
    save_db(db)
    
    socketio.emit('new_message', {
        "user": session['nickname'],
        "text": msg,
        "color": session['color'],
        "time": datetime.now().strftime("%H:%M")
    })

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE_FILE']):
        save_db({"users": {}, "messages": [], "files": {}})
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
