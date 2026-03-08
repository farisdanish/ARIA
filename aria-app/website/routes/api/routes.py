"""API route handlers."""
from flask_restx import Resource, Namespace, fields
from flask import send_from_directory, current_app, request
from datetime import datetime
from ...models.user import Student, Staff
from ...models.room import RoomList, RoomBooking
from ...models.access import RoomAccessLog
from ...models.base import db
from ...services.mail_service import MailService
from ...services.room_service import RoomService
from ...services.face_service import FaceService
import logging
import base64
import numpy as np
import cv2

logger = logging.getLogger(__name__)

ns = Namespace("api", description="ARIA API endpoints", path="/")

# Persistent face service to avoid reloading models on every frame
face_service = FaceService()

# API Models
student_model = ns.model("Student", {
    "StudID": fields.String(required=True, description="Student ID"),
    "StudName": fields.String(description="Student Name"),
    "StudEmail": fields.String(description="Student Email"),
    "StudContactNum": fields.String(description="Contact Number"),
    "AccountStatus": fields.String(description="Account Status")
})

staff_model = ns.model("Staff", {
    "StaffID": fields.String(required=True, description="Staff ID"),
    "StaffName": fields.String(description="Staff Name"),
    "StaffEmail": fields.String(description="Staff Email"),
    "StaffContactNum": fields.String(description="Contact Number"),
    "AccountStatus": fields.String(description="Account Status")
})

room_model = ns.model("Room", {
    "RoomID": fields.Integer(description="Room ID"),
    "RoomName": fields.String(description="Room Name"),
    "roomIMG": fields.String(description="Room Image Path"),
    "RoomInfo": fields.String(description="Room Information"),
    "RoomType": fields.String(description="Room Type"),
    "RoomStatus": fields.String(description="Room Status")
})

room_booking_model = ns.model("RoomBooking", {
    "RBookID": fields.Integer(description="Booking ID"),
    "RoomID": fields.Integer(description="Room ID"),
    "StudID": fields.String(description="Student ID"),
    "StaffID": fields.String(description="Staff ID"),
    "Start": fields.DateTime(description="Start Time"),
    "End": fields.DateTime(description="End Time"),
    "Purpose": fields.String(description="Purpose"),
    "RBookStatus": fields.String(description="Booking Status")
})

access_log_model = ns.model("AccessLog", {
    "rmaID": fields.Integer(description="Access Log ID"),
    "RoomID": fields.Integer(description="Room ID"),
    "StudID": fields.String(description="Student ID"),
    "StaffID": fields.String(description="Staff ID"),
    "Status": fields.Integer(description="Access Status (0=denied, 1=granted)"),
    "Timestamp": fields.DateTime(description="Timestamp")
})

access_log_input_model = ns.model("AccessLogInput", {
    "RoomID": fields.Integer(required=True, description="Room ID"),
    "StudID": fields.String(description="Student ID"),
    "StaffID": fields.String(description="Staff ID"),
    "Status": fields.Integer(required=True, description="Access Status"),
    "Timestamp": fields.DateTime(description="Timestamp (optional, defaults to now)")
})


@ns.route("/studentlist")
class StudentListAPI(Resource):
    """Get list of all students."""
    
    @ns.marshal_list_with(student_model)
    @ns.doc(description="Get all students")
    def get(self):
        """Get all students."""
        try:
            students = db.session.query(Student).all()
            return students, 200
        except Exception as e:
            logger.error(f"Error fetching students: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/students/<string:StudID>")
class StudentAPI(Resource):
    """Get student by ID."""
    
    @ns.marshal_with(student_model)
    @ns.doc(description="Get student by ID")
    def get(self, StudID):
        """Get a specific student."""
        try:
            student = db.session.query(Student).filter_by(StudID=StudID).first()
            if not student:
                ns.abort(404, f"Student {StudID} not found")
            return student, 200
        except Exception as e:
            logger.error(f"Error fetching student {StudID}: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/stafflist")
class StaffListAPI(Resource):
    """Get list of all staff."""
    
    @ns.marshal_list_with(staff_model)
    @ns.doc(description="Get all staff")
    def get(self):
        """Get all staff."""
        try:
            staff_list = db.session.query(Staff).all()
            return staff_list, 200
        except Exception as e:
            logger.error(f"Error fetching staff: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/staff/<string:StaffID>")
class StaffAPI(Resource):
    """Get staff by ID."""
    
    @ns.marshal_with(staff_model)
    @ns.doc(description="Get staff by ID")
    def get(self, StaffID):
        """Get a specific staff member."""
        try:
            staff = db.session.query(Staff).filter_by(StaffID=StaffID).first()
            if not staff:
                ns.abort(404, f"Staff {StaffID} not found")
            return staff, 200
        except Exception as e:
            logger.error(f"Error fetching staff {StaffID}: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/roomlist")
class RoomListAPI(Resource):
    """Get list of all rooms."""
    
    @ns.marshal_list_with(room_model)
    @ns.doc(description="Get all rooms")
    def get(self):
        """Get all rooms."""
        try:
            rooms = RoomService.get_all()
            return rooms, 200
        except Exception as e:
            logger.error(f"Error fetching rooms: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/rbooklists")
class RBookListAPI(Resource):
    """Get list of all room bookings."""
    
    @ns.marshal_list_with(room_booking_model)
    @ns.doc(description="Get all room bookings")
    def get(self):
        """Get all room bookings."""
        try:
            bookings = db.session.query(RoomBooking).all()
            return bookings, 200
        except Exception as e:
            logger.error(f"Error fetching room bookings: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/RoomBookings/<int:RBookID>")
class RBookAPI(Resource):
    """Get room booking by ID."""
    
    @ns.marshal_with(room_booking_model)
    @ns.doc(description="Get room booking by ID")
    def get(self, RBookID):
        """Get a specific room booking."""
        try:
            booking = db.session.query(RoomBooking).filter_by(RBookID=RBookID).first()
            if not booking:
                ns.abort(404, f"Room booking {RBookID} not found")
            return booking, 200
        except Exception as e:
            logger.error(f"Error fetching room booking {RBookID}: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/accesslogs")
class AccessLogListAPI(Resource):
    """Access log endpoints."""
    
    @ns.marshal_list_with(access_log_model)
    @ns.doc(description="Get all access logs")
    def get(self):
        """Get all access logs."""
        try:
            logs = db.session.query(RoomAccessLog).all()
            return logs, 200
        except Exception as e:
            logger.error(f"Error fetching access logs: {str(e)}")
            ns.abort(500, "Internal server error")
    
    @ns.expect(access_log_input_model)
    @ns.marshal_with(access_log_model)
    @ns.doc(description="Create a new access log entry")
    def post(self):
        """Create a new access log entry."""
        try:
            payload = ns.payload
            
            # Use current timestamp if not provided
            timestamp = payload.get("Timestamp")
            if not timestamp:
                timestamp = datetime.utcnow()
            
            # Create access log entry
            access_log = RoomAccessLog(
                RoomID=payload["RoomID"],
                StudID=payload.get("StudID"),
                StaffID=payload.get("StaffID"),
                Status=payload["Status"],
                Timestamp=timestamp
            )
            db.session.add(access_log)
            db.session.commit()
            
            # Send notification email
            room = RoomService.get_by_id(payload["RoomID"])
            if room:
                mail_service = MailService(current_app.extensions.get('mail'))
                
                if payload.get("StudID"):
                    user = db.session.query(Student).filter_by(StudID=payload["StudID"]).first()
                    if user:
                        mail_service.send_access_notification(
                            user.StudEmail,
                            user.StudName,
                            room.RoomName,
                            str(timestamp)
                        )
                elif payload.get("StaffID"):
                    user = db.session.query(Staff).filter_by(StaffID=payload["StaffID"]).first()
                    if user:
                        mail_service.send_access_notification(
                            user.StaffEmail,
                            user.StaffName,
                            room.RoomName,
                            str(timestamp)
                        )
            
            logger.info(f"Access log created: {access_log.rmaID}")
            return access_log, 201
            
        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            ns.abort(400, f"Missing required field: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating access log: {str(e)}")
            db.session.rollback()
            ns.abort(500, "Internal server error")


@ns.route("/faces")
class GetFacesFileAPI(Resource):
    """Get face database file."""
    
    @ns.doc(description="Download face database file")
    def get(self):
        """Download the face database file."""
        faces_db_path = current_app.config.get('FACES_DB_FILE')
        if not faces_db_path or not faces_db_path.exists():
            return {"message": "Face database file not found"}, 404

        try:
            return send_from_directory(
                str(faces_db_path.parent),
                faces_db_path.name,
                as_attachment=True
            )
        except Exception as e:
            logger.error(f"Error serving face database file: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route("/facesembeds")
class GetFacesEmbedsFileAPI(Resource):
    """Get face embeddings file."""
    
    @ns.doc(description="Download face embeddings file")
    def get(self):
        """Download the face embeddings file."""
        faces_embeds_path = current_app.config.get('FACES_EMBEDDINGS_PATH')
        if not faces_embeds_path or not faces_embeds_path.exists():
            return {"message": "Face embeddings file not found"}, 404

        try:
            return send_from_directory(
                str(faces_embeds_path.parent),
                faces_embeds_path.name,
                as_attachment=True
            )
        except Exception as e:
            logger.error(f"Error serving face embeddings file: {str(e)}")
            ns.abort(500, "Internal server error")

@ns.route("/recognize_frame")
class RecognizeFrameAPI(Resource):
    """Recognize face from video frame."""
    
    @ns.doc(description="Process a base64 encoded frame for face recognition")
    def post(self):
        """Process a webcam frame."""
        data = request.json
        if not data or 'image' not in data:
            return {"status": "error", "message": "No image data provided"}, 400
            
        try:
            # Decode the base64 image
            image_data = data['image'].split(',')[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return {"status": "error", "message": "Invalid image payload structure"}, 400
                
            # Ensure model is loaded implicitly or explicitly
            face_service.load_trained_model()
            
            # Detect face
            face, x1, x2, y1, y2 = face_service.get_face(frame)
            if face is None:
                return {"status": "searching", "message": "No face detected in frame"}
            
            # Recognize face
            confidence_threshold = current_app.config.get('FACE_CONFIDENCE_THRESHOLD', 0.85)
            identity, confidence = face_service.recognize_face(face, confidence_threshold)
            
            if identity and confidence >= confidence_threshold:
                # Resolve true name if possible, assuming identity is StudentID or StaffID
                user = db.session.query(Student).filter_by(StudID=identity).first()
                if not user:
                    user = db.session.query(Staff).filter_by(StaffID=identity).first()
                
                real_name = getattr(user, 'StudName', getattr(user, 'StaffName', identity)) if user else identity
                
                return {
                    "status": "success",
                    "identity": real_name,
                    "confidence": confidence,
                    "access": "granted"
                }
            else:
                return {
                    "status": "success",
                    "identity": "Unknown",
                    "confidence": confidence if identity else 0.0,
                    "access": "denied"
                }
                
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")
            return {"status": "error", "message": "Server-side processing error"}, 500
