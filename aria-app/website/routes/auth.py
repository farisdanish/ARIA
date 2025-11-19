"""Authentication routes."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user
from ..services.auth_service import AuthService
from ..models.user import Student, Staff, Admin
from ..models.base import db
import logging

logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login route."""
    if request.method == 'POST':
        user_id = request.form.get('userID')
        password = request.form.get('userPassword')
        
        if not user_id or not password:
            flash('Please enter both user ID and password.', category='error')
            return render_template("login.html", user=current_user)
        
        user = AuthService.authenticate_user(user_id, password)
        
        if user:
            flash('Logged in successfully!', category='success')
            login_user(user, remember=True)
            session.permanent = True
            
            # Redirect based on user type
            if user.is_Student():
                return redirect(url_for('home.student'))
            elif user.is_Staff():
                return redirect(url_for('home.staff'))
            elif user.is_Admin():
                return redirect(url_for('home.admin'))
        else:
            flash('Invalid user ID or password. Please try again.', category='error')
    
    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    """Logout route."""
    logout_user()
    flash('You have logged out.', category='warning')
    return redirect(url_for('auth.login'))


@auth.route('/RegisterSelect', methods=['GET', 'POST'])
def register_select():
    """Registration selection page."""
    return render_template("registerSelect.html", user=current_user)


@auth.route('/studRegister', methods=['GET', 'POST'])
def register_student():
    """Student registration route."""
    if request.method == 'POST':
        stud_id = request.form.get('StudID')
        stud_name = request.form.get('StudName')
        stud_email = request.form.get('StudEmail')
        stud_contact = request.form.get('StudContactNum')
        password1 = request.form.get('StudPassword1')
        password2 = request.form.get('StudPassword2')
        
        # Check if student already exists
        existing_student = db.session.query(Student).filter_by(StudID=stud_id).first()
        if existing_student:
            flash('Student ID already registered.', category='error')
            return render_template("register.html", user=current_user)
        
        # Validate registration data
        from ..utils.validators import validate_student_registration
        is_valid, error_msg = validate_student_registration(
            stud_id, stud_name, stud_email, stud_contact, password1, password2
        )
        
        if not is_valid:
            flash(error_msg, category='error')
            return render_template("register.html", user=current_user)
        
        # Create student account
        try:
            AuthService.create_student(stud_id, stud_name, stud_email, stud_contact, password2)
            flash('Account registration successful!', category='success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Failed to create student account: {str(e)}")
            flash('Registration failed. Please try again.', category='error')
    
    return render_template("register.html", user=current_user)


@auth.route('/staffRegister', methods=['GET', 'POST'])
def register_staff():
    """Staff registration route."""
    if request.method == 'POST':
        staff_id = request.form.get('StaffID')
        staff_name = request.form.get('StaffName')
        staff_email = request.form.get('StaffEmail')
        staff_contact = request.form.get('StaffContactNum')
        password1 = request.form.get('StaffPassword1')
        password2 = request.form.get('StaffPassword2')
        
        # Check if staff already exists
        existing_staff = db.session.query(Staff).filter_by(StaffID=staff_id).first()
        if existing_staff:
            flash('Staff ID already registered.', category='error')
            return render_template("registerStaff.html", user=current_user)
        
        # Validate registration data
        from ..utils.validators import validate_staff_registration
        is_valid, error_msg = validate_staff_registration(
            staff_id, staff_name, staff_email, staff_contact, password1, password2
        )
        
        if not is_valid:
            flash(error_msg, category='error')
            return render_template("registerStaff.html", user=current_user)
        
        # Create staff account
        try:
            AuthService.create_staff(staff_id, staff_name, staff_email, staff_contact, password2)
            flash('Account registration successful!', category='success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Failed to create staff account: {str(e)}")
            flash('Registration failed. Please try again.', category='error')
    
    return render_template("registerStaff.html", user=current_user)

