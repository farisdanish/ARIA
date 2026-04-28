"""Face recognition routes."""
from flask import Blueprint, Response, request, flash, redirect, url_for, current_app, session, jsonify
from flask_login import login_required, current_user
from ..extensions import limiter
from ..services.face_service import FaceService
from ..models.user import Student, Staff
from ..models.face import RegisteredFace
from ..models.base import db
from ..app import executor
from ..utils.ui import render_ui_template
from ..utils.file_utils import allowed_file
from ..utils.upload_validation import parse_data_url_image, validate_image_upload
import cv2
import logging
import time
import numpy as np

logger = logging.getLogger(__name__)

facenet = Blueprint('facenet', __name__)

# Initialize face service
face_service = FaceService()


# Legacy streaming function - deprecated in favor of client-side capture
# def generate_face_registration_stream(user_id: str):
#     ...


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
            
            # Throttling to 15 FPS for mobile stability
            time.sleep(1/15)
            
            # Downscale for mobile processing efficiency
            frame_optimized = cv2.resize(frame, (480, 360))
            
            # Higher compression (Quality 70) to save bandwidth and CPU decoding
            ret, buffer = cv2.imencode('.jpg', frame_optimized, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    finally:
        video_capture.release()


@facenet.route('/face_recog', methods=['GET', 'POST'])
@login_required
@limiter.limit('5 per minute', exempt_when=lambda: request.method != 'POST')
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
    # Reset registration state
    session['registration_count'] = 0
    session['registration_faces'] = []
    
    if current_user.is_Student():
        return render_ui_template(
            "faceRegister.html",
            ui_group="dashboards",
            user=current_user,
            is_Student=True,
            is_Staff=False,
            is_Admin=False
        )
    elif current_user.is_Staff():
        return render_ui_template(
            "faceRegister.html",
            ui_group="dashboards",
            user=current_user,
            is_Student=False,
            is_Staff=True,
            is_Admin=False
        )
    else:
        flash('Only students and staff can register faces.', category='error')
        return redirect(url_for('home.index'))


@facenet.route('/process_scanner_frame', methods=['POST'])
@login_required
@limiter.limit('5 per minute')
def process_scanner_frame():
    """Process a single frame sent from the client-side scanner."""
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'status': 'error', 'message': 'No image data'})
    
    try:
        mime_declared, image_bytes = parse_data_url_image(data['image'])
        if not image_bytes:
            return jsonify({'status': 'error', 'message': 'Invalid image data'})
        ok, err_msg, _ = validate_image_upload(
            image_bytes,
            mime_declared,
            require_content_type=mime_declared is not None,
        )
        if not ok:
            return jsonify({'status': 'error', 'message': err_msg or 'Invalid image'})
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'status': 'error', 'message': 'Invalid image'})
        
        if current_user.is_Student():
            user_id = current_user.StudID
        elif current_user.is_Staff():
            user_id = current_user.StaffID
        else:
            return jsonify({'status': 'error', 'message': 'Unauthorized'})
            
        # Get registration state from session
        count = session.get('registration_count', 0)
        face_paths = session.get('registration_faces', [])
        train_limit = 9
        
        if count >= train_limit:
            return jsonify({'status': 'complete', 'message': 'Registration already finished'})
        
        # Detect face
        face, x1, x2, y1, y2 = face_service.get_face(frame)
        
        if face is not None:
            count += 1
            face_resized = cv2.resize(face, (200, 200))
            
            # Save face image
            is_training = count < train_limit
            saved_path = face_service.save_face_image(user_id, face_resized, count, is_training)
            if saved_path:
                face_paths.append(saved_path)
            
            # Update session
            session['registration_count'] = count
            session['registration_faces'] = face_paths
            
            if count >= train_limit:
                # Save to database
                student = db.session.query(Student).filter_by(StudID=user_id).first()
                staff = db.session.query(Staff).filter_by(StaffID=user_id).first()
                
                face_paths_str = "\n".join(face_paths)
                
                # Check for existing
                existing_face = None
                if student:
                    existing_face = db.session.query(RegisteredFace).filter_by(StudID=user_id).first()
                elif staff:
                    existing_face = db.session.query(RegisteredFace).filter_by(StaffID=user_id).first()
                
                if existing_face:
                    existing_face.FaceIMG = face_paths_str
                else:
                    if student:
                        new_face = RegisteredFace(FaceIMG=face_paths_str, StudID=user_id, StaffID=None)
                    else:
                        new_face = RegisteredFace(FaceIMG=face_paths_str, StudID=None, StaffID=user_id)
                    db.session.add(new_face)
                
                db.session.commit()
                logger.info(f"Face registered for user {user_id} via scanner")
                executor.submit(face_service.train_model)
                
                return jsonify({
                    'status': 'success', 
                    'message': 'Face Registered!', 
                    'count': count, 
                    'limit': train_limit,
                    'redirect': url_for('home.homeStud' if student else 'home.homeStaff')
                })
            
            return jsonify({'status': 'processing', 'message': f'Capturing... {count}/{train_limit}', 'count': count, 'limit': train_limit})
        
        return jsonify({'status': 'searching', 'message': 'No face found', 'count': count, 'limit': train_limit})
        
    except Exception as e:
        logger.error(f"Error processing scanner frame: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal error'})


# @facenet.route('/face_registration_stream')
# @login_required
# def face_registration_stream():
#     ...


@facenet.route('/register_face_upload', methods=['POST'])
@login_required
@limiter.limit('5 per minute')
def register_face_upload():
    """Handle face registration via image upload."""
    if 'face_image' not in request.files:
        flash('No image uploaded.', category='error')
        return redirect(url_for('facenet.register_face'))
    
    file = request.files['face_image']
    if file.filename == '' or not allowed_file(file.filename):
        flash('No image selected or file type not allowed (JPEG/PNG only).', category='error')
        return redirect(url_for('facenet.register_face'))
    
    if current_user.is_Student():
        user_id = current_user.StudID
    elif current_user.is_Staff():
        user_id = current_user.StaffID
    else:
        flash('Registration not allowed.', category='error')
        return redirect(url_for('home.index'))
    
    try:
        raw = file.read()
        if not file.content_type:
            flash('Invalid upload: missing Content-Type.', category='error')
            return redirect(url_for('facenet.register_face'))
        ok, err_msg, _ = validate_image_upload(raw, file.content_type)
        if not ok:
            flash(err_msg or 'Invalid image file.', category='error')
            return redirect(url_for('facenet.register_face'))
        file_bytes = np.frombuffer(raw, np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image is None:
            flash('Invalid image format.', category='error')
            return redirect(url_for('facenet.register_face'))
        
        # Extract face
        face, x1, x2, y1, y2 = face_service.get_face(image)
        if face is None:
            flash('No face detected in the uploaded image. Please try another photo.', category='error')
            return redirect(url_for('facenet.register_face'))
        
        # Save multiple versions for better training (since we only have one upload)
        # We simulate the 9 images by saving the same face multiple times
        face_paths = []
        for i in range(1, 10):
            is_training = i < 9
            saved_path = face_service.save_face_image(user_id, face, i, is_training)
            if saved_path:
                face_paths.append(saved_path)
        
        # Update database
        student = db.session.query(Student).filter_by(StudID=user_id).first()
        staff = db.session.query(Staff).filter_by(StaffID=user_id).first()
        
        face_paths_str = "\n".join(face_paths)
        
        # Check for existing face
        existing_face = None
        if student:
            existing_face = db.session.query(RegisteredFace).filter_by(StudID=user_id).first()
        elif staff:
            existing_face = db.session.query(RegisteredFace).filter_by(StaffID=user_id).first()
            
        if existing_face:
            existing_face.FaceIMG = face_paths_str
        else:
            if student:
                new_face = RegisteredFace(FaceIMG=face_paths_str, StudID=user_id, StaffID=None)
            else:
                new_face = RegisteredFace(FaceIMG=face_paths_str, StudID=None, StaffID=user_id)
            db.session.add(new_face)
            
        db.session.commit()
        
        flash('Face registered successfully from upload!', category='success')
        # Re-trigger training in background
        executor.submit(face_service.train_model)
        
        if student:
            return redirect(url_for('home.homeStud'))
        return redirect(url_for('home.homeStaff'))
        
    except Exception as e:
        logger.error(f"Error processing face upload: {str(e)}")
        flash('An error occurred while processing your image.', category='error')
        return redirect(url_for('facenet.register_face'))


@facenet.route('/train_data')
@login_required
def train_data():
    """Train face recognition model (admin only)."""
    if not current_user.is_Admin():
        flash('Only administrators can train the face recognition model.', category='error')
        return redirect(url_for('home.index'))
    
    # Run training in background
    executor.submit(face_service.train_model)
    flash('Face Detection Model is refreshing...', category='info')
    return redirect(url_for('home.index'))
