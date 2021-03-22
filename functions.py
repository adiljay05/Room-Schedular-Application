import datetime
from flask import Flask, render_template,session
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
import random
from datetime import datetime

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jawad1.json"


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
        'bookings_list': []
    })
    datastore_client.put(entity)

def check_room_in_database(room_id):
    query = datastore_client.query(kind = 'RoomInfo')
    query.add_filter('room_id','=',room_id)
    return query.fetch()

def get_all_rooms():
    query = datastore_client.query(kind = 'RoomInfo')
    return query.fetch()

def check_boookings_of_a_room(room_id,start_time1,end_time1):
    entity_key = datastore_client.key('RoomInfo', room_id)
    room = datastore_client.get(entity_key)
    bookings_list = room['bookings_list']
    start_time = datetime.strptime(start_time1, '%Y-%m-%dT%H:%M')
    end_time = datetime.strptime(end_time1, '%Y-%m-%dT%H:%M')
    for b in bookings_list:
        e_key = datastore_client.key('BookingInfo', b)
        booking = datastore_client.get(e_key)
        st_time = datetime.strptime(booking['start_date_time'], '%Y-%m-%dT%H:%M')
        en_time = datetime.strptime(booking['end_date_time'], '%Y-%m-%dT%H:%M')
        if start_time > st_time and start_time < en_time:
            return False
        if end_time > st_time and end_time < en_time:
            return False
    return True

def addBooking():
    room_id = request.form['room_id']
    start_date_time = request.form['start_date_time']
    end_date_time = request.form['end_date_time']

    if check_boookings_of_a_room(room_id,start_date_time,end_date_time):
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
        return "error"

def add_booking_to_database():
    data = addBooking()
    if data == "error":
        return data
    entity_key = datastore_client.key('RoomInfo', data[1])
    room = datastore_client.get(entity_key)
    bookings_list = room['bookings_list']
    bookings_list.append(data[0])
    room.update({
        'bookings_list': bookings_list
    })
    datastore_client.put(room)
    return data[1]

def get_bookings_of_a_room(room_id):
    entity_key = datastore_client.key('RoomInfo', room_id)
    room = datastore_client.get(entity_key)
    bookings = room['bookings_list']
    bookings_list = []
    for b in bookings:
        e_key = datastore_client.key('BookingInfo', b)
        bookings_list.append(datastore_client.get(e_key))
    return bookings_list

def get_bookings_of_a_room_of_current_user(room_id):
    entity_key = datastore_client.key('RoomInfo', room_id)
    room = datastore_client.get(entity_key)
    bookings = room['bookings_list']
    bookings_list = []
    for b in bookings:
        e_key = datastore_client.key('BookingInfo', b)
        booking = datastore_client.get(e_key)
        if session['email'] == booking['booked_by']:
            bookings_list.append(booking)
    return bookings_list
