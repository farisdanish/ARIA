from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from .models import admin, staff, student, announcement
from .app import db
# from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

# In auth there will be login,logout and signup

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        userID = request.form.get('userID')
        userPassword = request.form.get('userPassword')
        
        Student = db.session.query(student).filter_by(StudID = userID).first()
        Staff = db.session.query(staff).filter_by(StaffID = userID).first()
        Admin = db.session.query(admin).filter_by(AdminID = userID).first()
        
        if Student:
            if bcrypt.checkpw(userPassword.encode('utf8'),Student.StudPassword.encode('utf8')):
                flash('Logged in successfully!', category='success')
                login_user(Student, remember=True)#remembers that user is logged in while web server is running
                session.permanent = True
                return redirect(url_for('views.homeStud'))
            else:
                flash('Incorrect password, try again.', category='error')
        elif Staff:
            if bcrypt.checkpw(userPassword.encode('utf8'),Staff.StaffPassword.encode('utf8')):
                flash('Logged in successfully!', category='success')
                login_user(Staff, remember=True)#remembers that user is logged in while web server is running
                session.permanent = True
                return redirect(url_for('views.homeStaff'))
            else:
                flash('Incorrect password, try again.', category='error')
        elif Admin:
            if bcrypt.checkpw(userPassword.encode('utf8'),Admin.AdminPassword.encode('utf8')):
                flash('Logged in successfully!', category='success')
                login_user(Admin, remember=True)#remembers that user is logged in while web server is running
                session.permanent = True
                return redirect(url_for('views.homeAdmin'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('No user by that ID found, please try again.', category='error')
    return render_template("login.html",user=current_user)

@auth.route('/logout')
@login_required #can only logout if logged in
def logout():
    logout_user()
    flash('You have logged out.', category='warning')
    return redirect(url_for('auth.login'))

@auth.route('/RegisterSelect', methods=['GET','POST'])
def registerSelect():
    return render_template("registerSelect.html", user=current_user)

@auth.route('/studRegister', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        StudID = request.form.get('StudID')
        StudName = request.form.get('StudName')
        StudEmail = request.form.get('StudEmail')
        StudContactNum = request.form.get('StudContactNum')
        StudPassword1 = request.form.get('StudPassword1')
        StudPassword2 = request.form.get('StudPassword2')
        
        Student = db.session.query(student).filter_by(StudID = StudID).first()
        
        if Student:
            flash('Student ID already registered.', category='error')
        elif len(StudID) < 10:
            flash('Matric Number must be 10 characters', category='error')
        elif StudName == "":
            flash('Please submit your name', category='error')
        elif len(StudEmail) < 4:
            flash('Email too short', category='error')
        elif len(StudContactNum) < 10:
            flash('Contact number too short', category='error')
        elif StudPassword2 != StudPassword1:
            flash('Passwords entered are not identical', category='error')
        elif len(StudPassword1) < 8:
            flash('Password must be atleast 8 characters long', category='error')
        else:
            #add student to the database
            new_student = student(StudID=StudID, StudPassword=bcrypt.hashpw(StudPassword2.encode('utf8'), bcrypt.gensalt()) 
                                  ,StudName=StudName,StudEmail=StudEmail,StudContactNum=StudContactNum, AccountStatus="Pending")
            db.session.add(new_student)
            db.session.commit()
            flash('Account registration successful!', category='success')
            return redirect(url_for('auth.login'))
            
    return render_template("register.html", user=current_user)

@auth.route('/staffRegister', methods=['GET','POST'])
def registerStaff():
    if request.method == 'POST':
        StaffID = request.form.get('StaffID')
        StaffName = request.form.get('StaffName')
        StaffEmail = request.form.get('StaffEmail')
        StaffContactNum = request.form.get('StaffContactNum')
        StaffPassword1 = request.form.get('StaffPassword1')
        StaffPassword2 = request.form.get('StaffPassword2')
        
        Staff = db.session.query(staff).filter_by(StaffID = StaffID).first()
        
        if Staff:
            flash('Staff ID already registered.', category='error')
        elif len(StaffID) < 10:
            flash('Matric Number must be 10 characters', category='error')
        elif StaffName == "":
            flash('Please submit your name', category='error')
        elif len(StaffEmail) < 4:
            flash('Email too short', category='error')
        elif len(StaffContactNum ) < 10:
            flash('Contact number too short', category='error')
        elif StaffPassword2 != StaffPassword1:
            flash('Passwords entered are not identical', category='error')
        elif len(StaffPassword1) < 8:
            flash('Password must be atleast 8 characters long', category='error')
        else:
            #add student to the database
            #new_Student = Student
            new_staff = staff(StaffID=StaffID, StaffPassword=bcrypt.hashpw(StaffPassword2.encode('utf8'), bcrypt.gensalt()) ,StaffName=StaffName,StaffEmail=StaffEmail,StaffContactNum=StaffContactNum, AccountStatus="Pending")
            db.session.add(new_staff)
            db.session.commit()
            flash('Account registration successful!', category='success')
            return redirect(url_for('auth.login'))
            
    return render_template("registerStaff.html", user=current_user)
