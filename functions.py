import datetime
from flask import Flask, render_template,session
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jawad1.json"

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

def addRoom():
    room_id = request.form['room_id']
    entity_key = datastore_client.key('RoomInfo', room_id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'room_id': room_id,
        'bookings_list': []
    })
    datastore_client.put(entity)

def addBooking():
    room_id = request.form['room_id']
    start_date_time = request.form['start_date_time']
    end_date_time = request.form['end_date_time']
    booked_by = request.form['booked_by']

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