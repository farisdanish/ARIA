"""Announcement management routes."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from ..services.announcement_service import AnnouncementService
from ..services.mail_service import MailService
from ..models.base import db
from ..schemas.announcement_schema import AnnouncementCreateSchema
from ..utils.validation import validate_form_data
from flask import current_app
import logging

logger = logging.getLogger(__name__)

announcements = Blueprint('announcements', __name__)


@announcements.route('/ManageAnnouncements', methods=['GET', 'POST'])
@login_required
def manage():
    """Manage announcements (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        # Validate form data
        form_data = {
            'Title': request.form.get('ATitle'),
            'Content': request.form.get('AContent')
        }
        
        is_valid, validated_data, error_msg = validate_form_data(AnnouncementCreateSchema, form_data)
        
        if not is_valid:
            flash(f'Validation error: {error_msg}', category='error')
        else:
            try:
                AnnouncementService.create(
                    admin_id=current_user.AdminID,
                    title=validated_data['Title'],
                    content=validated_data['Content']
                )
                flash('Announcement Added!', category='success')
                logger.info(f"Announcement created by admin {current_user.AdminID}")
            except Exception as e:
                logger.error(f"Error creating announcement: {str(e)}")
                flash('Failed to create announcement. Please try again.', category='error')
    
    all_announcements = AnnouncementService.get_all()
    return render_template(
        "manageAnnounce.html",
        user=current_user,
        announcements=all_announcements,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


@announcements.route('/updateAnnounce/', methods=['POST'])
@login_required
def update():
    """Update an announcement (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        announce_id = request.form.get('AnnounceID')
        title = request.form.get('Title')
        content = request.form.get('Content')
        
        if not announce_id:
            flash('Invalid announcement ID.', category='error')
            return redirect(url_for('announcements.manage'))
        
        try:
            announcement = AnnouncementService.update(
                int(announce_id),
                title=title,
                content=content
            )
            if announcement:
                flash('Announcement updated successfully!', category='success')
            else:
                flash('Announcement not found.', category='error')
        except ValueError:
            flash('Invalid announcement ID.', category='error')
        except Exception as e:
            logger.error(f"Error updating announcement: {str(e)}")
            flash('Failed to update announcement.', category='error')
    
    return redirect(url_for('announcements.manage'))


@announcements.route('/delete-announcement', methods=['POST'])
@login_required
def delete():
    """Delete an announcement (admin only)."""
    if not current_user.is_Admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        announce_id = data.get('AnnounceId')
        
        if not announce_id:
            return jsonify({'error': 'Invalid announcement ID'}), 400
        
        success = AnnouncementService.delete(int(announce_id))
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Announcement not found'}), 404
            
    except ValueError:
        return jsonify({'error': 'Invalid announcement ID'}), 400
    except Exception as e:
        logger.error(f"Error deleting announcement: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

