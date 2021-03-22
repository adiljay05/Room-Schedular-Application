import datetime
from flask import Flask, render_template,session
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
import functions

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jawad1.json"

app = Flask(__name__)
app.secret_key = 'assignment2'
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()

@app.route('/add_room',methods=['POST'])
def add_room():
    return render_template('add_room.html')

@app.route('/add_room_to_database',methods = ['POST'])
def add_room_to_database():
    room_id = request.form['room_id']
    room_check_flag = True
    rooms = functions.check_room_in_database(room_id)
    for r in rooms:
        room_check_flag = False
        break
    if room_check_flag:
        functions.addRoom(room_id)
        return redirect('/')
    else:
        return "<script>alert('Room Already Exists'); window.history.back();</script>"

@app.route('/add_booking',methods = ['POST'])
def add_booking():
    room_id = request.form['room_id']
    return render_template('add_booking.html',room_id = room_id)

@app.route('/add_booking_to_database',methods=['POST'])
def add_booking_to_database():
    check = functions.add_booking_to_database()
    if check == "error":
        return "<script>alert('Booking is overlapping, Please select another time'); window.history.back();</script>"
    return redirect('/')

@app.route('/',methods = ['POST', 'GET'])
def root():
    if request.method == 'POST':
        return render_template('index.html', error_message=error_message)
    else:
        id_token = request.cookies.get("token")
        error_message = None
        rooms_list = None
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                session['name'] = claims['name']
                session['email'] = claims['email']
                rooms_list = functions.get_all_rooms()
            except ValueError as exc:
                error_message = str(exc)
        else:
            session['name'] = None
            session['email'] = None
        return render_template('index.html', error_message=error_message, rooms = rooms_list)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)