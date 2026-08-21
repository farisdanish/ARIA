"""Public guest-only face demo routes."""
from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    request,
    url_for,
)
from flask_login import current_user, login_required
from ..utils.ui import render_ui_template

from ..extensions import limiter
from ..models.base import db
from ..models.demo_visit import DemoVisitLog
from ..models.room import RoomList
from ..services import demo_service
from ..services.demo_service import (
    DEMO_COOKIE_NAME,
    DemoBusyError,
    DemoEnrollmentCompleteError,
)
from ..utils.upload_validation import parse_data_url_image


demo_bp = Blueprint('demo', __name__)


def _client_ip() -> str:
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


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
@limiter.limit('30 per hour; 10 per minute')
def create_session():
    """Start a new public demo session."""
    try:
        guest, raw_token = demo_service.create_demo_session(current_app, ip_address=_client_ip())
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
        result = demo_service.add_demo_frame(guest, _image_bytes_from_request(), ip_address=_client_ip())
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
        demo_service.complete_demo_enrollment(guest, ip_address=_client_ip())
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
        result = demo_service.recognize_demo_guest(guest, _image_bytes_from_request(), ip_address=_client_ip())
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
@limiter.limit('30 per hour; 10 per minute')
def reset():
    """Delete the active guest demo session and clear its cookie."""
    guest = _guest_for_render()
    if guest is None:
        return jsonify({'error': 'invalid_session'}), 401

    demo_service.cleanup_demo_guest(guest, ip_address=_client_ip())
    response = make_response(jsonify({'status': 'reset'}))
    response.delete_cookie(DEMO_COOKIE_NAME)
    return response


@demo_bp.route('/ManageDemoLogs', methods=['GET'])
@login_required
def manage_demo_logs():
    """View public demo visitor logs (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    logs = DemoVisitLog.query.order_by(DemoVisitLog.Timestamp.desc()).limit(500).all()
    return render_ui_template(
        'ManageDemoLogs.html',
        ui_group='admin',
        user=current_user,
        logs=logs,
        is_Student=False,
        is_Staff=False,
        is_Admin=True,
    )


@demo_bp.route('/deleteDemoLog/<int:log_id>/', methods=['POST'])
@login_required
def delete_demo_log(log_id: int):
    """Delete a single demo visit log record (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    log_entry = db.session.query(DemoVisitLog).filter_by(id=log_id).first()
    if log_entry:
        db.session.delete(log_entry)
        db.session.commit()
        flash('Demo log record deleted.', category='success')
    else:
        flash('Record not found.', category='error')
    return redirect(url_for('demo.manage_demo_logs'))


@demo_bp.route('/clearDemoLogs', methods=['POST'])
@login_required
def clear_demo_logs():
    """Purge all demo visit logs (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    DemoVisitLog.query.delete()
    db.session.commit()
    flash('All demo visit logs have been purged.', category='success')
    return redirect(url_for('demo.manage_demo_logs'))
