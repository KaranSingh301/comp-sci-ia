from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime
from pymongo import MongoClient
import re
from flask import Flask, render_template, request, jsonify, session, flash
from pymongo import MongoClient
from datetime import datetime, time
import hashlib
from flask_mail import Mail, Message

app = Flask(__name__)

app.secret_key = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = ''
# app.config['MAIL_PASSWORD'] = ''

mail = Mail(app)

def connectToDatabase():
    client = MongoClient('mongodb+srv://singhkaran5567:biks%401209@cluster0.wq4ok.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['comp-sci-ia']
    col_events = db['events']
    col_users = db['users']
    return col_events, col_users

col_events, col_users = connectToDatabase()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        filters = request.form
        
        query = {}
        if filters.get('price'):
            if filters['price'] != "Please select":
                query['fees_type'] = filters['price']
        if filters.get('mode'):
            if filters['mode'] != "Please select":
                query['mode'] = filters['mode']

        if filters.get('datetime'):
            if filters['datetime']:
                month = int(str(filters['datetime']).split("-")[1])
                year = int(str(filters['datetime']).split("-")[0])
                month_year_start = datetime(year, month, 1)
                month_year_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
                query['start_datetime'] = {'$gte': month_year_start, '$lt': month_year_end}
        if filters.get('destination'):
            if filters['destination'] != "Please select":
                query['destination_country'] = {"$regex": filters['destination'], "$options": "i"}
        
        events = list(col_events.find(query))
    
    else:
        events = list(col_events.find({}))
    
    return render_template('index.html', events = events, events_count = len(events))

def hash_password(password):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password.encode('utf-8'))
    return sha256_hash.hexdigest()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        filters = request.form

        query = {}

        if filters.get('email'):
            if filters['email']:
                query['email'] = filters['email']
        if filters.get('password'):
            if filters['password']:
                query['password'] = filters['password']
        
        print('Query:', query)

        if col_users.find_one({"email": query['email']}):
            hashed_password_actual = col_users.find_one({"email": query['email']}).get('password')
            hash_password_given = hash_password(query['password'])
            if hash_password_given == hashed_password_actual:
                session['username'] = col_users.find_one({"email": query['email']}).get('fullname')
                session['useremail'] = query['email']
                events = list(col_events.find({}))
                return render_template("index.html", events = events, events_count = len(events))
            else:
                return render_template("login.html", error = "Incorrect Password")
        else:
            return render_template("register.html", error = "Not Registered")
    else:
        if 'username' in session:
            events = list(col_events.find({}))
            return render_template("index.html", events = events, events_count = len(events))
        else:
            return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        filters = request.form

        query = {}

        if filters.get('fullname'):
            if filters['fullname']:
                query['fullname'] = filters['fullname']
        if filters.get('email'):
            if filters['email']:
                query['email'] = filters['email']
        if filters.get('password'):
            if filters['password']:
                query['password'] = filters['password']

        print('Query:', query)
        
        if 'password' in query:
            if not col_users.find_one({"email": query['email']}):
                col_users.insert_one({
                    "fullname": query['fullname'],
                    "email": query['email'],
                    "password": hash_password(query['password'])
                })
                session['username'] = query['fullname']
                session['useremail'] = query['email']

                # msg = Message(f"{session['username']}, Welcome to University Fairs!!",
                #     sender = app.config['MAIL_USERNAME'], 
                #     recipients = [session['useremail']]
                # )
                # msg.body = f"""Hi {session['username']},
                            
                # Thank you for registering on University Fairs!!
                            
                # We hope you can find events that suit you based on your unique requirements.

                                
                # Thank You
                # University Fairs Team"""
                # mail.send(msg)
                
                events = list(col_events.find({}))

                return render_template("index.html", events = events, events_count = len(events))
            else:
                return render_template("login.html", error = "Already Registered")
        else:
            return render_template("register.html", error = "Registered", fullname = query['fullname'], email = query['email'])
    else:
        if 'username' in session:
            events = list(col_events.find({}))
            return render_template("index.html", events = events, events_count = len(events))
        else:
            return render_template("register.html")

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        session.pop('useremail', None)
        events = list(col_events.find({}))
        return render_template("index.html", events = events, events_count = len(events))
    else:
        events = list(col_events.find({}))
        return render_template("index.html", events = events, events_count = len(events))

if __name__ == '__main__':
    app.run(debug=True)