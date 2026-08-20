"""Public guest-only face demo routes."""
from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    request,
)
from flask_login import current_user
from ..utils.ui import render_ui_template

from ..extensions import limiter
from ..models.room import RoomList
from ..services import demo_service
from ..services.demo_service import (
    DEMO_COOKIE_NAME,
    DemoBusyError,
    DemoEnrollmentCompleteError,
)
from ..utils.upload_validation import parse_data_url_image


demo_bp = Blueprint('demo', __name__)


def _active_guest():
    cookie_value = request.cookies.get(DEMO_COOKIE_NAME)
    if not cookie_value:
        return None
    return demo_service.load_guest_from_signed_cookie(cookie_value)


def _guest_for_render():
    cookie_value = request.cookies.get(DEMO_COOKIE_NAME)
    if not cookie_value:
        return None
    return demo_service.load_guest_from_signed_cookie(cookie_value, include_expired=True)


def _sample_count(guest) -> int:
    return demo_service.get_embedding_count(guest) if guest else 0


def _image_bytes_from_request() -> bytes:
    if 'image' in request.files:
        return request.files['image'].read()
    if request.files:
        first_file = next(iter(request.files.values()))
        return first_file.read()
    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        raise ValueError('No image provided.')
    _, image_bytes = parse_data_url_image(data['image'])
    if not image_bytes:
        raise ValueError('Invalid image payload.')
    return image_bytes


@demo_bp.route('/demo')
def demo():
    """Render the public guest demo page."""
    guest = _guest_for_render()
    roomlist = RoomList.query.all()
    demo_state = guest.Status if guest else 'no_session'
    if guest and guest.ExpiresAt < datetime.utcnow():
        demo_state = 'expired'
    return render_ui_template(
        'demo.html',
        ui_group='public',
        user=current_user,
        roomlist=roomlist,
        roombookings=[],
        eventbookings=[],
        announcements=[],
        demo_state=demo_state,
        demo_required_samples=current_app.config['DEMO_SAMPLES_REQUIRED'],
        demo_frame_interval_ms=current_app.config['DEMO_FRAME_INTERVAL_MS'],
        demo_guest=guest,
        demo_sample_count=_sample_count(guest),
    )


@demo_bp.route('/demo/session', methods=['POST'])
@limiter.limit('3 per hour')
def create_session():
    """Start a new public demo session."""
    try:
        guest, raw_token = demo_service.create_demo_session(current_app)
    except DemoBusyError:
        return jsonify({'error': 'demo_busy'}), 503

    response = make_response(
        jsonify({
            'status': 'pending',
            'expires_in_hours': current_app.config['DEMO_SESSION_HOURS'],
        })
    )
    response.set_cookie(
        DEMO_COOKIE_NAME,
        demo_service.sign_demo_cookie(raw_token),
        httponly=True,
        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
        samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
        max_age=current_app.config['DEMO_SESSION_HOURS'] * 3600,
        expires=guest.ExpiresAt,
    )
    return response


@demo_bp.route('/demo/status', methods=['GET'])
def demo_status():
    """Return guest session status without invoking ML work."""
    guest = _active_guest()
    if guest is None:
        return jsonify({'error': 'invalid_session'}), 401

    return jsonify({
        'status': guest.Status,
        'sample_count': demo_service.get_embedding_count(guest),
        'required': current_app.config['DEMO_SAMPLES_REQUIRED'],
        'expires_at': guest.ExpiresAt.isoformat(),
    })


@demo_bp.route('/demo/register-frame', methods=['POST'])
@limiter.limit('10 per minute')
def register_frame():
    """Capture one guest enrollment sample."""
    guest = _active_guest()
    if guest is None:
        return jsonify({'error': 'invalid_session'}), 401
    if guest.Status not in ('pending', 'enrolling'):
        return jsonify({'error': 'invalid_state', 'status': guest.Status}), 403

    try:
        result = demo_service.add_demo_frame(guest, _image_bytes_from_request())
        return jsonify(result)
    except DemoEnrollmentCompleteError:
        return jsonify({'error': 'enrollment_complete'}), 429
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except RuntimeError as exc:
        current_app.logger.error('Demo register-frame runtime error: %s', exc)
        return jsonify({'error': str(exc)}), 503
    except Exception:
        current_app.logger.exception('Unexpected error in demo register-frame')
        return jsonify({'error': 'Internal error processing frame.'}), 500


@demo_bp.route('/demo/register-complete', methods=['POST'])
def register_complete():
    """Finalize guest enrollment after the required samples are captured."""
    guest = _active_guest()
    if guest is None:
        return jsonify({'error': 'invalid_session'}), 401

    try:
        demo_service.complete_demo_enrollment(guest)
        return jsonify({'status': 'ready'})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@demo_bp.route('/demo/recognize', methods=['POST'])
@limiter.limit('10 per minute')
def recognize():
    """Run guest-only recognition using stored demo embeddings."""
    guest = _active_guest()
    if guest is None:
        return jsonify({'error': 'invalid_session'}), 401
    if guest.Status != 'ready':
        return jsonify({'error': 'guest_not_ready', 'status': guest.Status}), 403

    try:
        result = demo_service.recognize_demo_guest(guest, _image_bytes_from_request())
        return jsonify(result)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except RuntimeError as exc:
        current_app.logger.error('Demo recognize runtime error: %s', exc)
        return jsonify({'error': str(exc)}), 503
    except Exception:
        current_app.logger.exception('Unexpected error in demo recognize')
        return jsonify({'error': 'Internal error during recognition.'}), 500


@demo_bp.route('/demo/reset', methods=['POST'])
@limiter.limit('5 per hour')
def reset():
    """Delete the active guest demo session and clear its cookie."""
    guest = _guest_for_render()
    if guest is None:
        return jsonify({'error': 'invalid_session'}), 401

    demo_service.cleanup_demo_guest(guest)
    response = make_response(jsonify({'status': 'reset'}))
    response.delete_cookie(DEMO_COOKIE_NAME)
    return response
