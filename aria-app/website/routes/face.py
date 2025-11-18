"""Face recognition routes."""
from flask import Blueprint, Response, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from ..services.face_service import FaceService
from ..models.user import Student, Staff
from ..models.face import RegisteredFace
from ..models.base import db
from ..app import executor
import cv2
import logging

logger = logging.getLogger(__name__)

facenet = Blueprint('facenet', __name__)

# Initialize face service
face_service = FaceService()


def generate_face_registration_stream(user_id: str):
    """Generate video stream for face registration."""
    video_capture = cv2.VideoCapture(0)
    count = 0
    train_limit = 9
    face_paths = []
    
    try:
        while count < train_limit:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            face, x1, x2, y1, y2 = face_service.get_face(frame)
            
            if face is not None and count < train_limit:
                count += 1
                face_resized = cv2.resize(face, (200, 200))
                
                # Save face image
                is_training = count < train_limit
                saved_path = face_service.save_face_image(user_id, face_resized, count, is_training)
                if saved_path:
                    face_paths.append(saved_path)
                
                cv2.putText(frame, str(count), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            elif face is None and count < train_limit:
                cv2.putText(frame, "No face found", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            
            if count >= train_limit:
                # Save to database
                try:
                    with current_app.app_context():
                        student = db.session.query(Student).filter_by(StudID=user_id).first()
                        staff = db.session.query(Staff).filter_by(StaffID=user_id).first()
                        
                        face_paths_str = "\n".join(face_paths)
                        
                        if student:
                            new_face = RegisteredFace(
                                FaceIMG=face_paths_str,
                                StudID=user_id,
                                StaffID=None
                            )
                        elif staff:
                            new_face = RegisteredFace(
                                FaceIMG=face_paths_str,
                                StudID=None,
                                StaffID=user_id
                            )
                        else:
                            logger.warning(f"User {user_id} not found for face registration")
                            break
                        
                        db.session.add(new_face)
                        db.session.commit()
                        logger.info(f"Face registered for user {user_id}")
                except Exception as e:
                    logger.error(f"Error saving face registration: {str(e)}")
                
                msg = "Face Registered!,\nPlease Press the Back Button!"
                y0, dy = 50, 24
                for i, line in enumerate(msg.split('\n')):
                    y = y0 + i * dy
                    cv2.putText(frame, line, (50, y), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                
                count += 1
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    finally:
        video_capture.release()


def generate_face_recognition_stream():
    """Generate video stream for face recognition."""
    if not face_service.load_trained_model():
        logger.error("Failed to load face recognition model")
        return
    
    video_capture = cv2.VideoCapture(0)
    video_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    
    confidence_threshold = current_app.config.get('FACE_CONFIDENCE_THRESHOLD', 0.85)
    
    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            face, x1, x2, y1, y2 = face_service.get_face(frame)
            
            if face is not None:
                identity, confidence = face_service.recognize_face(face, confidence_threshold)
                
                if identity and confidence > confidence_threshold:
                    label = f"{identity} ({confidence:.1%})"
                    color = (0, 128, 0)  # Green
                else:
                    label = f"Unknown ({confidence:.1%})" if identity else "No match"
                    color = (0, 0, 255)  # Red
                
                cv2.putText(frame, label, (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            else:
                cv2.putText(frame, "No face found", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    finally:
        video_capture.release()


@facenet.route('/face_recog', methods=['GET', 'POST'])
@login_required
def face_recognition():
    """Face recognition stream route."""
    return Response(
        generate_face_recognition_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@facenet.route('/register_face', methods=['GET', 'POST'])
@login_required
def register_face():
    """Face registration page."""
    if current_user.is_Student():
        return render_template(
            "faceRegister.html",
            user=current_user,
            is_Student=True,
            is_Staff=False,
            is_Admin=False
        )
    elif current_user.is_Staff():
        return render_template(
            "faceRegister.html",
            user=current_user,
            is_Student=False,
            is_Staff=True,
            is_Admin=False
        )
    else:
        flash('Only students and staff can register faces.', category='error')
        return redirect(url_for('views.home'))


@facenet.route('/face_registration_stream')
@login_required
def face_registration_stream():
    """Face registration video stream."""
    if current_user.is_Student():
        user_id = current_user.StudID
    elif current_user.is_Staff():
        user_id = current_user.StaffID
    else:
        flash('Only students and staff can register faces.', category='error')
        return redirect(url_for('views.home'))
    
    return Response(
        generate_face_registration_stream(user_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@facenet.route('/train_data')
@login_required
def train_data():
    """Train face recognition model (admin only)."""
    if not current_user.is_Admin():
        flash('Only administrators can train the face recognition model.', category='error')
        return redirect(url_for('views.home'))
    
    # Run training in background
    executor.submit(face_service.train_model)
    flash('Face Detection Model is refreshing...', category='info')
    return redirect(url_for('views.home'))

