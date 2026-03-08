"""Room management routes."""
from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from ..services.room_service import RoomService
from ..schemas.room_schema import RoomCreateSchema, RoomUpdateSchema
from ..utils.validation import validate_form_data
from ..utils.file_utils import save_uploaded_file, delete_file
from ..models.base import db
from ..utils.ui import render_ui_template
import logging

logger = logging.getLogger(__name__)

rooms = Blueprint('rooms', __name__)


@rooms.route('/ManageRooms', methods=['GET', 'POST'])
@login_required
def manage():
    """Manage rooms (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        # Get form data
        room_name = request.form.get('roomName')
        room_info = request.form.get('roomInfo')
        room_type = request.form.get('roomType')
        room_status = request.form.get('roomStatus', 'Available')
        img = request.files.get('file')
        
        # Validate room name
        if not room_name or len(room_name.strip()) < 1:
            flash('Room name is required.', category='error')
        else:
            # Check if room already exists
            existing_room = RoomService.get_by_name(room_name)
            if existing_room:
                flash('Room already exists.', category='error')
            else:
                # Handle image upload
                room_img = None
                if img and img.filename:
                    saved_path = save_uploaded_file(img, subfolder='roomImages')
                    if saved_path:
                        room_img = saved_path
                    else:
                        flash('Failed to upload image.', category='error')
                        return redirect(url_for('rooms.manage'))
                
                try:
                    RoomService.create(
                        admin_id=current_user.AdminID,
                        room_name=room_name,
                        room_info=room_info,
                        room_type=room_type,
                        room_status=room_status,
                        room_img=room_img
                    )
                    flash('Room Added!', category='success')
                    logger.info(f"Room created: {room_name}")
                except Exception as e:
                    logger.error(f"Error creating room: {str(e)}")
                    flash('Failed to create room. Please try again.', category='error')
    
    all_rooms = RoomService.get_all()
    return render_ui_template(
        "manageRoom.html",
        ui_group="admin",
        user=current_user,
        roomlist=all_rooms,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


@rooms.route('/updateRoom/', methods=['POST'])
@login_required
def update():
    """Update a room (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        room_id = request.form.get('roomID')
        if not room_id:
            flash('Invalid room ID.', category='error')
            return redirect(url_for('rooms.manage'))
        
        try:
            room = RoomService.get_by_id(int(room_id))
            if not room:
                flash('Room not found.', category='error')
                return redirect(url_for('rooms.manage'))
            
            # Get form data
            room_name = request.form.get('roomName')
            room_info = request.form.get('roomInfo')
            room_type = request.form.get('roomType')
            room_status = request.form.get('roomStatus')
            img = request.files.get('file')
            
            # Handle image update
            room_img = None
            if img and img.filename:
                # Delete old image if exists
                if room.roomIMG:
                    delete_file(room.roomIMG)
                
                # Save new image
                saved_path = save_uploaded_file(img, subfolder='roomImages')
                if saved_path:
                    room_img = saved_path
            
            # Update room
            updated_room = RoomService.update(
                int(room_id),
                room_name=room_name,
                room_info=room_info,
                room_type=room_type,
                room_status=room_status,
                room_img=room_img
            )
            
            if updated_room:
                flash('Room updated successfully!', category='success')
            else:
                flash('Failed to update room.', category='error')
                
        except ValueError:
            flash('Invalid room ID.', category='error')
        except Exception as e:
            logger.error(f"Error updating room: {str(e)}")
            flash('Failed to update room. Please try again.', category='error')
    
    return redirect(url_for('rooms.manage'))


@rooms.route('/deleteRoom/<int:room_id>/', methods=['GET', 'POST'])
@login_required
def delete(room_id):
    """Delete a room (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    try:
        room = RoomService.get_by_id(room_id)
        if not room:
            flash('Room not found.', category='error')
            return redirect(url_for('rooms.manage'))
        
        # Delete associated image
        if room.roomIMG:
            delete_file(room.roomIMG)
        
        # Delete room
        success = RoomService.delete(room_id)
        if success:
            flash('Room deleted successfully!', category='success')
        else:
            flash('Failed to delete room.', category='error')
            
    except Exception as e:
        logger.error(f"Error deleting room: {str(e)}")
        flash('Failed to delete room. Please try again.', category='error')
    
    return redirect(url_for('rooms.manage'))


@rooms.route('/rooms/discovery', methods=['GET'])
@login_required
def discovery():
    """Get the interactive room discovery list (HTMX)."""
    type_code = request.args.get('type', 'r')
    room_type = "Normal Room" if type_code == 'r' else "Event Room"
    active_id = request.args.get('active_id', type=int)
    
    rooms_data = RoomService.get_rooms_with_status(room_type=room_type)
    
    return render_template(
        "partials/_room_discovery_list.html",
        rooms=rooms_data,
        active_room_id=active_id
    )
