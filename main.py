import datetime
from flask import Flask, render_template,session
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
import functions
from datetime import timedelta
from datetime import datetime


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
        return root()
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
        return "<h1>Room Already Exists</h1><br><form action='/add_room' method='post'><input type='submit' value='Click to go back'></form>"

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
    check = functions.add_booking_to_database()
    if check == "error":
        return "<script>alert('Booking is overlapping, Please select another time'); window.history.back();</script>"
    return redirect('/')

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
    user_info = functions.get_user_data()
    room = functions.get_all_rooms()
    user_bookings = []
    for r in room:
        bookings_list = r['bookings_list']
        for b in bookings_list:
            e_key = datastore_client.key('BookingInfo', b)
            booking = datastore_client.get(e_key)
            if booking['booked_by'] == user_info['email']:
                user_bookings.append(booking)
    user_bookings = sorted(user_bookings,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
    return render_template("show_user_bookings.html",bookings = user_bookings)

@app.route('/search_own_bookings_in_room',methods=['POST','GET'])
def search_own_bookings_in_room():
    if request.method == 'GET':
        return root()
    room_id = request.form['room_id']
    bookings = functions.get_bookings_of_a_room_of_current_user(room_id)
    bookings = sorted(bookings,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
    return render_template("show_user_bookings.html",bookings = bookings)

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
    return render_template('edit_booking.html',booking = booking)

@app.route('/edit_booking_in_database',methods = ['POST','GET'])
def edit_booking_in_database():
    if request.method == 'GET':
        return root()
    if functions.edit_booking_in_database():
        return redirect('/')
    else:
        return "<script>alert('Booking is overlapping, Please select another time'); window.history.back();</script>"

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
    bookings = functions.get_bookings_of_a_room(room_id)
    empty_flag = True
    for b in bookings:
        empty_flag = False
    if not empty_flag:
        #room has bookings
        return "<script>alert('Room have booking(s), Please delete all bookings first'); window.history.back();</script>"
    else:
        #room is empty
        functions.delete_room(room_id)
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
                user_info = functions.get_user_data()
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