from flask_restx import Resource, Api, Namespace, fields
from flask import Blueprint,jsonify,send_from_directory,send_file
from .app import db, mail
from flask_mail import Mail, Message
import os
import numpy as np
from numpy import savez_compressed
import json
from .models import admin, staff, student, announcement, roomlist, roombookings, roomaccesslog

apiroute = Blueprint('apiroute', __name__, url_prefix='/api')
api = Api(apiroute)

ns = Namespace("api")

#models for api to use to send and receive data
student_model = api.model("student", {
    "StudID": fields.String,
    "StudPassword": fields.String,
    "StudName": fields.String,
    "StudEmail": fields.String,
    "StudContactNum": fields.String,
    "AccountStatus": fields.String
})

staff_model = api.model("staff", {
    "StaffID": fields.String,
    "StaffPassword": fields.String,
    "StaffName": fields.String,
    "StaffEmail": fields.String,
    "StaffContactNum": fields.String,
    "AccountStatus": fields.String
})

rooms_model = api.model("roomlist", {
    "RoomID": fields.Integer,
    "RoomName": fields.String,
    "roomIMG": fields.String,
    "RoomInfo": fields.String,
    "RoomType": fields.String,
    "RoomStatus": fields.String
})

roombookings_model = api.model("roombookings", {
    "RBookID": fields.Integer,
    "RoomID": fields.Integer,
    "StudID": fields.String,
    "StaffID": fields.String,
    "Start": fields.DateTime,
    "End": fields.DateTime,
    "Purpose": fields.String,
    "RBookStatus": fields.String
})

#models for api to use to send and receive data
rAccessLog_model = api.model("rAccessLog", {
    "rmaID": fields.Integer,
    "RoomID": fields.Integer,
    "StudID": fields.String,
    "StaffID": fields.String,
    "Status": fields.Integer,
    "Timestamp": fields.DateTime
})

rAccessLog_input_model = api.model("rAccessLogInput", {
    "RoomID": fields.Integer,
    "StudID": fields.String,
    "StaffID": fields.String,
    "Status": fields.Integer,
    "Timestamp": fields.DateTime
})


@ns.route("/studentlist")
class StudentListAPI(Resource):
    @ns.marshal_list_with(student_model)
    def get(self): 
        return db.session.query(student).all()

@ns.route("/students/<string:StudID>")
class StudentAPI(Resource):
    @ns.marshal_with(student_model)
    def get(self, StudID):
        Student = db.session.query(student).filter_by(StudID = StudID).first()
        return Student

@ns.route("/stafflist")
class StaffListAPI(Resource):
    @ns.marshal_list_with(staff_model)
    def get(self):
        return db.session.query(staff).all()

@ns.route("/staff/<string:StaffID>")
class StaffAPI(Resource):
    @ns.marshal_with(staff_model)
    def get(self, StaffID):
        Staff = db.session.query(staff).filter_by(StaffID = StaffID).first()
        return Staff

@ns.route("/roomlist")
class RoomListAPI(Resource):
    @ns.marshal_list_with(rooms_model)
    def get(self):
        return db.session.query(roomlist).all()

@ns.route("/rbooklists")
class RBookListAPI(Resource):
    @ns.marshal_list_with(roombookings_model)
    def get(self):
        return db.session.query(roombookings).all()

@ns.route("/RoomBookings/<int:RBookID>")
class RBookAPI(Resource):
    @ns.marshal_with(roombookings_model)
    def get(self, RBookID):
        Rbook = db.session.query(roombookings).filter_by(RBookID = RBookID).first()
        return Rbook

#ADD API ROUTE FOR ADDING ACCESS LOG TO DB
@ns.route("/accesslogs")
class rAccessLogListAPI(Resource):
    @ns.marshal_list_with(rAccessLog_model)
    def get(self):
        return db.session.query(roomaccesslog).all()
    
    @ns.expect(rAccessLog_input_model)
    @ns.marshal_with(rAccessLog_model)
    def post(self):
        print(ns.payload["StudID"])
        ral = roomaccesslog(RoomID=ns.payload["RoomID"], StudID=ns.payload["StudID"], StaffID=ns.payload["StaffID"], Status=ns.payload["Status"], 
                            Timestamp=ns.payload["Timestamp"])
        db.session.add(ral)
        db.session.commit()
        
        bookedroom = db.session.query(roomlist).filter_by(RoomID = ns.payload["RoomID"]).first()
        subject = 'Room Access Notification at ' + bookedroom.RoomName + ' Issued'
        if ns.payload["StudID"] != None:
            user = db.session.query(student).filter_by(StudID = ns.payload["StudID"]).first()
            recipients = user.StudEmail
            content = 'You ('+ user.StudName +') have just been cleared to enter room: ' + bookedroom.RoomName + ' at '+ ns.payload["Timestamp"]
        elif ns.payload["StaffID"] != None:
            user = db.session.query(staff).filter_by(StaffID = ns.payload["StaffID"]).first()
            recipients = user.StaffEmail
            content = 'You ('+ user.StaffName +') have just been cleared to enter room: ' + bookedroom.RoomName + ' at '+ ns.payload["Timestamp"]
        send_mail(subject, recipients, content)
        
        return ral, 201

@ns.route("/faces") 
class GetFacesFileAPI(Resource):
    def get(self):
        #download to device
        return send_from_directory('D:/Educational/FYP Web Development/website/static/','registered-faces-db.npz', as_attachment=True)
    
@ns.route("/facesembeds") 
class GetFacesEmbedsFileAPI(Resource):
    def get(self):
        #download to device
        return send_from_directory('D:/Educational/FYP Web Development/website/static/','registered-faces-db-embeddings.npz', as_attachment=True)
    
def send_mail(subject, recipients_email, content):
    msg = Message(
        subject,
        sender = 'fyplibraryroomalert@gmail.com',
        recipients= [recipients_email]
    )
    msg.body = content
    mail.send(msg)
    return "Message sent"