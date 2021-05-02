import datetime
from flask import Flask, render_template,session
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
import random
from datetime import datetime

import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jawad1.json"


app = Flask(__name__)
app.secret_key = 'assignment2'
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


def authenticateUsers():
    id_token = request.cookies.get("token")
    return google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)


def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'email': claims['email'],
        'name': claims['name']
    })
    datastore_client.put(entity)

def get_user_data():
    id_token = request.cookies.get("token")
    claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
    return retrieveUserInfo(claims)

def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity

def addRoom(room_id):
    entity_key = datastore_client.key('RoomInfo', room_id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'room_id': room_id,
        'added_by':session['email']
    })
    datastore_client.put(entity)

def check_room_in_database(room_id):
    query = datastore_client.query(kind = 'RoomInfo')
    query.add_filter('room_id','=',room_id)
    return query.fetch()

def get_all_rooms():
    query = datastore_client.query(kind = 'RoomInfo')
    return query.fetch()

def check_boookings_of_a_room(room_id,start_time,end_time):
    query = datastore_client.query(kind='BookingInfo')
    query.add_filter('room_id','=',room_id)
    bookings_list = query.fetch()
    for b in bookings_list:
        st_time = datetime.strptime(b['start_date_time'], '%Y-%m-%dT%H:%M')
        en_time = datetime.strptime(b['end_date_time'], '%Y-%m-%dT%H:%M')
        latest_start = max(start_time, st_time)
        earliest_end = min(end_time, en_time)
        change = (earliest_end - latest_start).days + 1
        overlap = max(0, change)
        if overlap>0:
            return False
        # return not (start_time <= en_time) and (st_time <= end_time)
        # if start_time > st_time and start_time < en_time:
        #     return False
        # if end_time > st_time and end_time < en_time:
        #     return False
    return True

def validate_dates(start_time,end_time):
    if end_time<start_time:
        return False
    return True

def addBooking(room_id):
    start_date_time = request.form['start_date_time']
    end_date_time = request.form['end_date_time']

    start_time = datetime.strptime(start_date_time, '%Y-%m-%dT%H:%M')
    end_time = datetime.strptime(end_date_time, '%Y-%m-%dT%H:%M')

    if validate_dates(start_time,end_time):
        if check_boookings_of_a_room(room_id,start_time,end_time):
            booking_id = random.getrandbits(63)

            entity_key = datastore_client.key('BookingInfo', booking_id)
            entity = datastore.Entity(key = entity_key)
            entity.update({
                'room_id': room_id,
                'start_date_time': start_date_time,
                'end_date_time': end_date_time,
                'booked_by': session['email']
            })
            datastore_client.put(entity)
            return [booking_id,room_id]
        else:
            return False
    else:
        return False

def add_booking_to_database(room_id):
    data = addBooking(room_id)
    if data == False:
        return data
    return data[1]

def get_bookings_of_a_room(room_id):
    query = datastore_client.query(kind='BookingInfo')
    query.add_filter('room_id','=',room_id)
    bookings_list = query.fetch()
    return bookings_list

def check_if_room_bookings_are_empty(room_id):
    query = datastore_client.query(kind='BookingInfo')
    query.add_filter('room_id','=',room_id)
    bookings_list = query.fetch()
    for b in bookings_list:
        return False
    return True

def get_bookings_of_a_room_of_current_user(room_id):
    query = datastore_client.query(kind='BookingInfo')
    query.add_filter('booked_by','=',session['email'])
    query.add_filter('room_id','=',room_id)
    return query.fetch()

def delete_booking():
    booking_id = request.form['booking_id']
    room_id = request.form['room_id']
    booking_key = datastore_client.key('BookingInfo', int(booking_id))
    datastore_client.delete(booking_key)
    return room_id

def check_boookings_of_a_room_for_edit(room_id,start_time1,end_time1,booking_id):
    query = datastore_client.query(kind='BookingInfo')
    query.add_filter('room_id','=',room_id)
    bookings_list = query.fetch()
    start_time = datetime.strptime(start_time1, '%Y-%m-%dT%H:%M')
    end_time = datetime.strptime(end_time1, '%Y-%m-%dT%H:%M')
    for b in bookings_list:
        if str(b.key.id) == booking_id: # if same booking is edited, let it changed
            continue
        st_time = datetime.strptime(b['start_date_time'], '%Y-%m-%dT%H:%M')
        en_time = datetime.strptime(b['end_date_time'], '%Y-%m-%dT%H:%M')
        latest_start = max(start_time, st_time)
        earliest_end = min(end_time, en_time)
        change = (earliest_end - latest_start).days + 1
        overlap = max(0, change)
        if overlap>0:
            return False
        # return not (start_time <= en_time) and (st_time <= end_time)    # if overlapping exists return true
    return True

def edit_booking_in_database():
    room_id = request.form['room_id']
    booking_id = request.form['booking_id']
    start_date_time = request.form['start_date_time']
    end_date_time = request.form['end_date_time']

    start_time = datetime.strptime(start_date_time, '%Y-%m-%dT%H:%M')
    end_time = datetime.strptime(end_date_time, '%Y-%m-%dT%H:%M')

    if validate_dates(start_time,end_time):
        if check_boookings_of_a_room_for_edit(room_id,start_date_time,end_date_time,booking_id):
            booking_key = datastore_client.key('BookingInfo', int(booking_id))
            booking = datastore_client.get(booking_key)
            booking['start_date_time'] = start_date_time
            booking['end_date_time'] = end_date_time
            booking['room_id'] = room_id
            datastore_client.put(booking)
            bookings = get_bookings_of_a_room(room_id)
            bookings = sorted(bookings,key=lambda x:datetime.strptime(x['start_date_time'],"%Y-%m-%dT%H:%M"))
            return render_template("view_bookings.html",msg= "Room "+room_id+" have following bookings",bookings = bookings)
        else:
            return render_template('show_message.html',error='Booking is overlapping, Please select another time',booking_id=booking_id,form="edit_booking")
    else:
        return "<script>alert('Invalid Date time, Please select another time'); window.history.back();</script>"

def search_using_filter():
    start_date_time = request.form['start_date_time']
    end_date_time = request.form['end_date_time']
    if validate_dates(start_date_time,end_date_time):
        start_time = datetime.strptime(start_date_time, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_date_time, '%Y-%m-%dT%H:%M')

        query = datastore_client.query(kind='BookingInfo')
        all_bookings = query.fetch()

        bookings_list = []
        for b in all_bookings:
            st_time = datetime.strptime(b['start_date_time'], '%Y-%m-%dT%H:%M')
            en_time = datetime.strptime(b['end_date_time'], '%Y-%m-%dT%H:%M')
            if st_time>start_time and en_time<end_time:
                bookings_list.append(b)
        return bookings_list
    else:
        return list()

def delete_room(room_id):
    entity_key = datastore_client.key('RoomInfo', room_id)
    datastore_client.delete(entity_key)
