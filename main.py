import datetime
from flask import Flask, render_template,session
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
import functions
from datetime import timedelta
from datetime import datetime

import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jawad1.json"

app = Flask(__name__)
app.secret_key = 'assignment2'
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)

@app.route('/add_room',methods=['POST','GET'])
def add_room():
    if request.method == 'GET':
        return redirect('/')
    return render_template('add_room.html')

@app.route('/add_room_to_database',methods = ['POST','GET'])
def add_room_to_database():
    if request.method == 'GET':
        return root()
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
        msg = "Room Already Exists"
        return render_template('show_message.html',error=msg,form = 'add_room')

@app.route('/add_booking',methods = ['POST','GET'])
def add_booking():
    if request.method == 'GET':
        return root()
    room_id = request.form['room_id']
    return render_template('add_booking.html',room_id = room_id)

@app.route('/add_booking_to_database',methods=['POST','GET'])
def add_booking_to_database():
    if request.method == 'GET':
        return root()
    room_id = request.form['room_id']
    data = functions.addBooking(room_id)
    if data == False:
        return render_template('show_message.html',error='Booking is overlapping, Please select another time',room_id=room_id,form="add_booking")
        # return "<script>alert('Booking is overlapping, Please select another time'); window.history.back();</script>"
    bookings = functions.get_bookings_of_a_room(room_id)
    bookings = sorted(bookings,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
    return render_template("view_bookings.html",msg= "Room "+room_id+" have following bookings",bookings = bookings)

@app.route('/view_bookings',methods = ['POST','GET'])
def view_bookings():
    if request.method == 'GET':
        return root()
    room_id = request.form['room_id']
    bookings = functions.get_bookings_of_a_room(room_id)
    bookings = sorted(bookings,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
    return render_template("view_bookings.html",msg= "Room "+room_id+" have following bookings",bookings = bookings)

@app.route('/view_user_bookings',methods=['POST','GET'])
def view_user_bookings():
    if request.method == 'GET':
        return root()
    query = datastore_client.query(kind='BookingInfo')
    query.add_filter('booked_by','=',session['email'])
    user_bookings = query.fetch()
    user_bookings = sorted(user_bookings,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
    return render_template("show_user_bookings.html",bookings = user_bookings,msg=session['email']+"'s all bookings in all rooms")

@app.route('/search_own_bookings_in_room',methods=['POST','GET'])
def search_own_bookings_in_room():
    if request.method == 'GET':
        return root()
    room_id = request.form['room_id']
    bookings = functions.get_bookings_of_a_room_of_current_user(room_id)
    bookings = sorted(bookings,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
    return render_template("show_user_bookings.html",bookings = bookings,msg=session['email']+"'s all bookings in room: "+room_id)

@app.route('/delete_booking',methods = ['POST','GET'])
def delete_booking():
    if request.method == 'GET':
        return root()
    request_from = request.form['request_from']
    room_id = functions.delete_booking()
    if request_from == "room_bookings":
        return view_bookings()
    else:
        return view_user_bookings()

@app.route('/edit_booking',methods = ['POST','GET'])
def edit_booking():
    if request.method == 'GET':
        return root()
    booking_id = request.form['booking_id']
    booking_key = datastore_client.key('BookingInfo', int(booking_id))
    booking = datastore_client.get(booking_key)
    rooms = functions.get_all_rooms()
    return render_template('edit_booking.html',booking = booking,rooms = rooms)

@app.route('/edit_booking_in_database',methods = ['POST','GET'])
def edit_booking_in_database():
    if request.method == 'GET':
        return root()
    return functions.edit_booking_in_database()

@app.route('/search_using_filter',methods= ['POST','GET'])
def search_using_filter():
    if request.method == 'GET':
        return root()
    bookings_list = functions.search_using_filter()
    bookings_list = sorted(bookings_list,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
    return render_template("view_bookings.html",msg= "Bookings in Given Range",bookings = bookings_list)

@app.route('/delete_room',methods = ['POST','GET'])
def delete_room():
    if request.method == 'GET':
        return root()
    room_id = request.form['room_id']
    if functions.check_if_room_bookings_are_empty(room_id):  # room is empty
        functions.delete_room(room_id)
        return redirect('/')
    else:
        return render_template('show_message.html',error='Room have booking(s), Please delete all bookings first',form="root")
        #return "<script>alert('Room have booking(s), Please delete all bookings first'); window.history.back();</script>"

@app.route('/',methods = ['POST', 'GET'])
def root():
    if request.method == 'POST':
        return render_template('index.html')
    else:
        id_token = request.cookies.get("token")
        error_message = None
        rooms_list = []
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                session['name'] = claims['name']
                session['email'] = claims['email']
                user_info = functions.retrieveUserInfo(claims)
                if user_info == None:
                    functions.createUserInfo(claims)
                rooms_list = functions.get_all_rooms()
            except ValueError as exc:
                error_message = str(exc)
        else:
            session['name'] = None
            session['email'] = None
        return render_template('index.html', error_message=error_message, rooms = rooms_list)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)