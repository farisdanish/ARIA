from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session, current_app
from flask_login import login_required, current_user
from .app import db, mail
from .models import admin, staff, student, announcement, roomlist, roombookings, eventbookings, registeredfaces, roomaccesslog, feedback, report, attr_names,relations
from sqlalchemy import desc, and_, select
from datetime import datetime, timedelta
import json
import urllib.request
import os
import re
from os.path import join, dirname, realpath
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

views = Blueprint('views', __name__)

os.chdir('D:/Educational/FYP Web Development/website')

@views.route('/')#url of homepage
def home():
    announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
    rooms = db.session.query(roomlist)
    studList = db.session.query(student)
    staffList = db.session.query(staff)
    rBookList = db.session.query(roombookings)
    eBookList = db.session.query(eventbookings)
    if current_user.is_authenticated:
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Admin():
            return redirect(url_for('views.homeAdmin'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))
        else:
            return render_template("home.html", user=current_user, announcements=announcements)
    else:
        return render_template("home.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList,eventbookings=eBookList, 
                               announcements=announcements)

@views.route('/homeStud')
@login_required
def homeStud():
    currDateTime = datetime.now()
    currDate = currDateTime.strftime("%d-%m-%Y")
    announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
    if current_user.is_Student():
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        eBookList = db.session.query(eventbookings)
        regFaceExist = db.session.query(registeredfaces).filter_by(StudID = current_user.StudID).first()
        return render_template("homeStud.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList, eventbookings=eBookList, 
                               currentDate = currDate,regFaceExist=regFaceExist, announcements=announcements, is_Student=True, is_Staff=False, is_Admin=False)
    else:
        flash('Only students allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Admin():
            return redirect(url_for('views.homeAdmin'))

@views.route('/homeStaff')
@login_required
def homeStaff():
    currDateTime = datetime.now()
    currDate = currDateTime.strftime("%d-%m-%Y")
    announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
    if current_user.is_Staff():
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        eBookList = db.session.query(eventbookings)
        regFaceExist = db.session.query(registeredfaces).filter_by(StaffID = current_user.StaffID).first()
        return render_template("homeStaff.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList, eventbookings=eBookList, 
                               currentDate = currDate, regFaceExist=regFaceExist, announcements=announcements, is_Student=False, is_Staff=True, is_Admin=False)
    else:
        flash('Only staff members allowed on that URL.', category='error')
        if current_user.is_Student():
            return redirect(url_for('views.homeStud'))
        elif current_user.is_Admin():
            return redirect(url_for('views.homeAdmin'))

@views.route('/homeAdmin')
@login_required
def homeAdmin():
    if current_user.is_Admin():
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        eBookList = db.session.query(eventbookings)
        return render_template("homeAdmin.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList,eventbookings=eBookList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
UPLOAD_FOLDER = 'static\\uploads\\'
UPLOAD_FOLDER_ABSOLUTE = "D:/Educational/FYP Web Development/website/static/uploads"
basedir = os.path.abspath(os.path.dirname(__file__))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        #print('upload_image filename: ' + filename)
        flash('Image successfully uploaded and displayed below')
        return render_template('index.html', filename=filename)
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)
 
@views.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/'+filename), code=301)
     
@views.route('/ManageAnnouncements', methods=['GET','POST'])
@login_required
def ManagemetAnnouncements():
    if current_user.is_Admin():
        if request.method == 'POST': 
            ATitle = request.form.get('ATitle')#Gets the data from the HTML
            AContent = request.form.get('AContent')

            if len(ATitle) < 1:
                flash('Please Enter Announcement Title', category='error')
            elif len(AContent) < 1:
                flash('Please Enter Announcement Content', category='error') 
            else:
                current_dateTime = datetime.now()
                new_announcement = announcement(AdminID=current_user.AdminID,PostDate=current_dateTime,Title=ATitle,Content=AContent)  #providing the schema for the note
                db.session.add(new_announcement) #adding the note to the database 
                db.session.commit()
                flash('Announcement Added!', category='success')
                print("Announcement Added somehow")
        
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        return render_template("manageAnnounce.html", user=current_user, announcements=announcements, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/updateAnnounce/', methods = ['POST'])
def updateAnnounce():
    if request.method == "POST":
        Announce = db.session.query(announcement).filter_by(AnnounceID= request.form.get('AnnounceID')).first()
        
        Announce.Title = request.form.get('Title')#Gets the data from the HTML
        Announce.Content = request.form.get('Content')

        db.session.commit()
        flash("Announcement is updated")
        return redirect(url_for('views.ManagemetAnnouncements'))

@views.route('/delete-announcement', methods=['POST'])
def delete_announcement():  
    Announcement = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    AnnounceID = Announcement['AnnounceId']
    Announcement = db.session.query(announcement).get(AnnounceID)
    if Announcement:
        if current_user.is_Admin():
            db.session.delete(Announcement)
            db.session.commit()

    return jsonify({})

@views.route('/ManageRooms', methods=['GET','POST'])
@login_required
def ManagementRooms():
    if current_user.is_Admin():
        if request.method == 'POST': 
            AdminID = current_user.AdminID
            RoomName = request.form.get('roomName')#Gets the data from the HTML
            RoomInfo = request.form.get('roomInfo')
            RoomType = request.form.get('roomType')
            RoomStatus = request.form.get('roomStatus')
            img = request.files['file']
            newname = img.filename.replace(" ", "_")
            newname = re.sub(r"[\([{})\]]", "", newname)
            roomIMG = "roomImages/" + newname
            
            roomExist = db.session.query(roomlist).filter_by(RoomName = RoomName).first()
            if roomExist:
                flash('Room already in the list.', category='error')
            else:
                if img and allowed_file(img.filename):
                    filename = secure_filename(img.filename)
                    img.save(os.path.join(basedir, UPLOAD_FOLDER, "roomImages/" + filename))
                    #print('upload_image filename: ' + filename)
                    flash('Image successfully uploaded')
                    #providing the schema for the note
                    new_room = roomlist(AdminID=AdminID,RoomName=RoomName,roomIMG=roomIMG,
                                        RoomInfo=RoomInfo,RoomType=RoomType,RoomStatus=RoomStatus)
                    db.session.add(new_room) #adding the note to the database 
                    db.session.commit()
                    flash('Room Added!', category='success')
                else:
                    flash('Allowed image types are - png, jpg, jpeg, gif', category = 'info')
                    flash('Room was not added!', category='error')
                return redirect(url_for('views.ManagementRooms'))
        
        rooms = db.session.query(roomlist)
        return render_template("manageRoom.html", user=current_user, roomlist=rooms, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/updateRoom/', methods = ['POST'])
def updateRoom():
    if request.method == "POST":
        rooms = db.session.query(roomlist).filter_by(RoomID = request.form.get('roomID')).first()
        
        old_img_todelete = rooms.roomIMG
                
        rooms.RoomName = request.form.get('roomName')#Gets the data from the HTML
        rooms.RoomInfo = request.form.get('roomInfo')
        rooms.RoomType = request.form.get('roomType')
        rooms.RoomStatus = request.form.get('roomStatus')
        img = request.files['file']
        newname = img.filename.replace(" ", "_")
        newname = re.sub(r"[\([{})\]]", "", newname)
        rooms.roomIMG = "roomImages\\" + newname

        
        if img.filename == "":
            rooms.roomIMG = old_img_todelete
            db.session.commit()
            flash('Room is updated')
        elif img and allowed_file(img.filename):
            filename = secure_filename(img.filename)
            filepath = os.path.join(basedir, UPLOAD_FOLDER, "roomImages\\" + filename)
            print(filepath)
            check_file = os.path.isfile(filepath)
            print(check_file)
            if rooms.roomIMG != old_img_todelete:
                img.save(os.path.join(basedir, UPLOAD_FOLDER, "roomImages/" + filename))
                if old_img_todelete != "roomImages\\":
                    os.remove(os.path.join(basedir, UPLOAD_FOLDER, old_img_todelete))
            elif not check_file:
                img.save(os.path.join(basedir, UPLOAD_FOLDER, "roomImages/" + filename))
            #print('upload_image filename: ' + filename)
            flash('Image successfully uploaded')
            db.session.commit()
            flash('Room is updated')
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif', category = 'info')
            flash('Room was not updated!', category='error')
        return redirect(url_for('views.ManagementRooms'))
    
@views.route('/deleteRoom/<roomID>/', methods = ['GET', 'POST'])
def deleteRoom(roomID):
    room = db.session.query(roomlist).filter_by(RoomID = roomID).first()
    os.remove(os.path.join(basedir, UPLOAD_FOLDER, room.roomIMG))
    db.session.delete(room)
    db.session.commit()
    flash("Room has been deleted")
    return redirect(url_for('views.ManagementRooms'))

@views.route('/ManageRBookings', methods=['GET','POST'])
@login_required
def ManagementRoomBookings():
    if current_user.is_Admin():
        if request.method == 'POST': 
            print("no form received in ManagementRoomBookings")
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings).order_by(desc(roombookings.Start)).all()
        rBookTimeList = []
        
        for r in rBookList:
            rBookTime = {
                'RBookID': r.RBookID,
                'StartDate': r.Start.date().strftime("%Y-%m-%d"),
                'StartTime': r.Start.time().strftime("%H:%M:%S"),
                'EndDate': r.End.date().strftime("%Y-%m-%d"),
                'EndTime': r.End.time().strftime("%H:%M:%S")
            }
            rBookTimeList.append(rBookTime)
            
        return render_template("manageRBooking.html", 
                               user=current_user, roomlist=rooms, staff=staffList,student=studList, 
                               roombookings=rBookList, rBookTimeList=rBookTimeList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/ManageEBookings', methods=['GET','POST'])
@login_required
def ManagementEventBookings():
    if current_user.is_Admin():
        if request.method == 'POST': 
            print("no form sent in ManagementEventBookings")
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        eBookList = db.session.query(eventbookings).order_by(desc(eventbookings.Start)).all()
        eBookTimeList = []
        
        for e in eBookList:
            eBookTime = {
                'EBookID': e.EBookID,
                'StartDate': e.Start.date().strftime("%Y-%m-%d"),
                'StartTime': e.Start.time().strftime("%H:%M:%S"),
                'EndDate': e.End.date().strftime("%Y-%m-%d"),
                'EndTime': e.End.time().strftime("%H:%M:%S")
            }
            eBookTimeList.append(eBookTime)
        
        return render_template("manageEBooking.html", 
                               user=current_user, roomlist=rooms, staff=staffList,student=studList, 
                               eventbookings=eBookList, eBookTimeList=eBookTimeList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))
        
@views.route('/ManageFaces', methods=['GET','POST'])
@login_required
def ManagementFaces():
    if current_user.is_Admin():
        if request.method == 'POST': 
            print("no form in ManagementFaces")
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        RegFacesList = db.session.query(registeredfaces).all()
        return render_template("manageFaces.html", 
                               user=current_user, roomlist=rooms, staff=staffList,student=studList, 
                               registeredfaces=RegFacesList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))
        
@views.route('/deleteFace/<FaceID>/', methods = ['GET', 'POST'])
def deleteFace(FaceID):
    face = db.session.query(registeredfaces).filter_by(FaceID= FaceID).first()
    db.session.delete(face)
    db.session.commit()
    flash("Face has been deleted")
    return redirect(url_for('views.ManagementFaces'))

@views.route('/ManageRBookings/AddRBook', methods=['GET','POST'])
@login_required
def AddRBook_Admin():
    if current_user.is_Admin():
        if request.method == 'POST': 
            roomID = request.form.get('roomSelect')#Gets the data from the HTML
            StudID = request.form.get('studentid')
            StaffID = request.form.get('staffid')
            Purpose = request.form.get('RBookPurpose')
            
            dtStart = datetime.strptime(request.form.get('rbookstart'), '%Y-%m-%d').date()
            starttime = datetime.strptime(request.form.get('rbooktimeStart'), '%H:%M:%S').time()
            newStart = datetime.combine(dtStart, starttime)
            
            dtEnd = datetime.strptime(request.form.get('rbookend'), '%Y-%m-%d').date()
            endtime = datetime.strptime(request.form.get('rbooktimeEnd'), '%H:%M:%S').time()
            newEnd = datetime.combine(dtEnd, endtime)
            
            delta = newEnd - newStart
            sec = delta.total_seconds()
            hours = sec / (60 * 60)
            
            rbook = db.session.query(roombookings)
            existing_bookings = db.session.query(roombookings).filter(and_(roombookings.Start <= newEnd,
                                                                           roombookings.End >= newStart, 
                                                                           roombookings.RoomID == request.form.get('roomSelect'))).all()
            
            if newEnd < newStart:
                flash('Booking time invalid', category='error')
            elif hours > 2:
                #check if the hours booked is more than 2 hours
                flash('Booking time must be 2 hours or less', category='error')
            elif existing_bookings:
                # Handle the conflict, maybe return a message or perform another action
                flash('Room Already occupied for that time', category='error')
            elif Purpose == "":
                flash('Please fill in the purpose of your booking', category='error')
            else:
                new_rbook = roombookings(RoomID=roomID,StudID=StudID,StaffID=StaffID,Start=newStart,End=newEnd,Purpose=Purpose,RBookStatus="Upcoming")  #providing the schema for the note
                db.session.add(new_rbook) #adding the note to the database 
                db.session.commit()
                
                if StudID is not None:
                    bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                    subject = 'Room Booking on ' + request.form.get('rbookstart') + ' is confirmed'
                    stdnt = db.session.query(student).filter_by(StudID = StudID).first()
                    recipients = stdnt.StudEmail
                    content = 'Your Room Booking on ' + request.form.get('rbookstart') + ' at '+ bookedroom.RoomName +' is CONFIRMED'
                    send_mail(subject, recipients, content)
                elif StaffID is not None:
                    bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                    subject = 'Room Booking on ' + request.form.get('rbookstart') + ' is confirmed'
                    stff = db.session.query(staff).filter_by(StaffID = StaffID).first()
                    recipients = stff.StaffEmail
                    content = 'Your Room Booking on ' + request.form.get('rbookstart') + ' at '+ bookedroom.RoomName +' is CONFIRMED!'
                    send_mail(subject, recipients, content)
                
                flash('Room Booking was Added!', category='success')
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        return render_template("adminAddRBook.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/ManageEBookings/AddEBook', methods=['GET','POST'])
@login_required
def AddEBook_Admin():
    if current_user.is_Admin():
        if request.method == 'POST': 
            roomID = request.form.get('roomSelect')#Gets the data from the HTML
            StudID = request.form.get('studentid')
            StaffID = request.form.get('staffid')
            StaffID = request.form.get('staffid')
            Purpose = request.form.get('EBookPurpose')
            AddDetail = request.form.get('EBookAddDetails')
            
            dtStart = datetime.strptime(request.form.get('ebookstart'), '%Y-%m-%d').date()
            starttime = datetime.strptime(request.form.get('ebooktimeStart'), '%H:%M:%S').time()
            newStart = datetime.combine(dtStart, starttime)
            
            dtEnd = datetime.strptime(request.form.get('ebookend'), '%Y-%m-%d').date()
            endtime = datetime.strptime(request.form.get('ebooktimeEnd'), '%H:%M:%S').time()
            newEnd = datetime.combine(dtEnd, endtime)
            
            delta = newEnd - newStart
            sec = delta.total_seconds()
            hours = sec / (60 * 60)
            
            ebook = db.session.query(eventbookings)
            existing_bookings = db.session.query(eventbookings).filter(and_(eventbookings.Start <= newEnd, eventbookings.End >= newStart, eventbookings.RoomID == request.form.get('roomSelect'))).all()
            
            if newEnd < newStart:
                flash('Booking time invalid', category='error')
            elif existing_bookings:
                # Handle the conflict, maybe return a message or perform another action
                flash('Room Already occupied for that time', category='error')
            elif Purpose == "":
                flash('Please fill in the purpose of your booking', category='error')
            else:
                new_ebook = eventbookings(RoomID=roomID,StudID=StudID,StaffID=StaffID,Start=newStart,End=newEnd,Purpose=Purpose,AddDetail=AddDetail,EbookStatus="Upcoming")  #providing the schema for the note
                db.session.add(new_ebook) #adding the note to the database 
                db.session.commit()
                
                if StudID is not None:
                    bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                    subject = 'Event Room Booking on ' + request.form.get('ebookstart') + ' is CONFIRMED'
                    stdnt = db.session.query(student).filter_by(StudID = StudID).first()
                    recipients = stdnt.StudEmail
                    content = 'Your Event Room Booking on ' + request.form.get('ebookstart') + ' at '+ bookedroom.RoomName +' is confirmed!'
                    send_mail(subject, recipients, content)
                elif StaffID is not None:
                    bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                    subject = 'Event Room Booking on ' + request.form.get('ebookstart') + ' is CONFIRMED'
                    stff = db.session.query(staff).filter_by(StaffID = StaffID).first()
                    recipients = stff.StaffEmail
                    content = 'Your Event Room Booking on ' + request.form.get('ebookstart') + ' at '+ bookedroom.RoomName +' is confirmed!'
                    send_mail(subject, recipients, content)
                
                flash('Event Booking was Added!', category='success')
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        eBookList = db.session.query(eventbookings)
        return render_template("adminAddEBook.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, eventbookings=eBookList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/MyBookings', methods = ['GET', 'POST'])
def bookingHistory():
    currDateTime = datetime.now()
    currDate = currDateTime.strftime("%d-%m-%Y")
    if current_user.is_Student():
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        rBookList = db.session.query(roombookings)
        rBookTimeList = []
        
        for r in rBookList:
            rBookTime = {
                'RBookID': r.RBookID,
                'StartDate': r.Start.date().strftime("%Y-%m-%d"),
                'StartTime': r.Start.time().strftime("%H:%M:%S"),
                'EndDate': r.End.date().strftime("%Y-%m-%d"),
                'EndTime': r.End.time().strftime("%H:%M:%S")
            }
            rBookTimeList.append(rBookTime)
        
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        eBookList = db.session.query(eventbookings).order_by(desc(eventbookings.Start)).all()
        eBookTimeList = []
        
        for e in eBookList:
            eBookTime = {
                'EBookID': e.EBookID,
                'StartDate': e.Start.date().strftime("%Y-%m-%d"),
                'StartTime': e.Start.time().strftime("%H:%M:%S"),
                'EndDate': e.End.date().strftime("%Y-%m-%d"),
                'EndTime': e.End.time().strftime("%H:%M:%S")
            }
            eBookTimeList.append(eBookTime)
            
        return render_template("studBookings.html", user=current_user, roomlist=rooms,student=studList, roombookings=rBookList,
                               currentDate = currDate, eventbookings=eBookList, eBookTimeList=eBookTimeList,rBookTimeList=rBookTimeList, is_Student=True, is_Staff=False, is_Admin=False, announcements=announcements)
    elif current_user.is_Staff():
        rooms = db.session.query(roomlist)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        rBookTimeList = []
        
        for r in rBookList:
            rBookTime = {
                'RBookID': r.RBookID,
                'StartDate': r.Start.date().strftime("%Y-%m-%d"),
                'StartTime': r.Start.time().strftime("%H:%M:%S"),
                'EndDate': r.End.date().strftime("%Y-%m-%d"),
                'EndTime': r.End.time().strftime("%H:%M:%S")
            }
            rBookTimeList.append(rBookTime)
        
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        eBookList = db.session.query(eventbookings).order_by(desc(eventbookings.Start)).all()
        eBookTimeList = []
        
        for e in eBookList:
            eBookTime = {
                'EBookID': e.EBookID,
                'StartDate': e.Start.date().strftime("%Y-%m-%d"),
                'StartTime': e.Start.time().strftime("%H:%M:%S"),
                'EndDate': e.End.date().strftime("%Y-%m-%d"),
                'EndTime': e.End.time().strftime("%H:%M:%S")
            }
            eBookTimeList.append(eBookTime)
        return render_template("staffBookings.html", user=current_user, roomlist=rooms, staff=staffList, roombookings=rBookList, currentDate = currDate,
                               eventbookings=eBookList, eBookTimeList=eBookTimeList, rBookTimeList=rBookTimeList, is_Student=False, is_Staff=True, is_Admin=False, announcements=announcements)
    else:
        flash('Admin Not allowed on this URL', category='error')
        return redirect(url_for('views.homeAdmin'))

@views.route('/AddRBook', methods=['GET','POST'])
@login_required
def AddRBook():
    if current_user.is_Student():
        if request.method == 'POST': 
            roomID = request.form.get('roomSelect')#Gets the data from the HTML
            StudID = request.form.get('studid')
            StaffID = None
            Purpose = request.form.get('RBookPurpose')
            
            dtStart = datetime.strptime(request.form.get('rbookstart'), '%Y-%m-%d').date()
            starttime = datetime.strptime(request.form.get('rbooktimeStart'), '%H:%M:%S').time()
            newStart = datetime.combine(dtStart, starttime)
            
            dtEnd = datetime.strptime(request.form.get('rbookend'), '%Y-%m-%d').date()
            endtime = datetime.strptime(request.form.get('rbooktimeEnd'), '%H:%M:%S').time()
            newEnd = datetime.combine(dtEnd, endtime)
            
            delta = newEnd - newStart
            sec = delta.total_seconds()
            hours = sec / (60 * 60)
            
            rbook = db.session.query(roombookings)
            #existing_bookings = rbook.where((roombookings.Start <= newEnd) & (roombookings.End >= newStart) & roombookings.RoomID == request.form.get('roomSelect')).first()
            existing_bookings = db.session.query(roombookings).filter(and_(roombookings.Start <= newEnd, roombookings.End >= newStart, roombookings.RoomID == request.form.get('roomSelect'))).all()
            
            if newEnd < newStart:
                flash('Booking time invalid', category='error')
            elif hours > 2:
                #check if the hours booked is more than 2 hours
                flash('Booking time must be 2 hours or less', category='error')
            elif existing_bookings:
                # Handle the conflict, maybe return a message or perform another action
                flash('Room Already occupied for that time', category='error')
            elif Purpose == "":
                flash('Please fill in the purpose of your booking', category='error')
            else:
                new_rbook = roombookings(RoomID=roomID,StudID=StudID,StaffID=StaffID,Start=newStart,End=newEnd,Purpose=Purpose,RBookStatus="Upcoming")  #providing the schema for the note
                db.session.add(new_rbook) #adding the note to the database 
                db.session.commit()
                
                bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                subject = 'Room Booking on ' + request.form.get('rbookstart') + ' is CONFIRMED'
                recipients = current_user.StudEmail
                content = 'Your Room Booking on ' + request.form.get('rbookstart') + ' at '+ bookedroom.RoomName +' is confirmed!'
                send_mail(subject, recipients, content)
                
                flash('Room Booking was Added!', category='success')
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        #return render_template("homeStud.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList, is_Student=False, is_Staff=False, is_Admin=True, announcements=announcements)
        return redirect(url_for('views.bookingHistory'))
    elif current_user.is_Staff():
        if request.method == 'POST': 
            roomID = request.form.get('roomSelect')#Gets the data from the HTML
            StudID = None
            print(request.form.get('staffid'))
            StaffID = request.form.get('staffid')
            Purpose = request.form.get('RBookPurpose')
            
            dtStart = datetime.strptime(request.form.get('rbookstart'), '%Y-%m-%d').date()
            starttime = datetime.strptime(request.form.get('rbooktimeStart'), '%H:%M:%S').time()
            newStart = datetime.combine(dtStart, starttime)
            
            dtEnd = datetime.strptime(request.form.get('rbookend'), '%Y-%m-%d').date()
            endtime = datetime.strptime(request.form.get('rbooktimeEnd'), '%H:%M:%S').time()
            newEnd = datetime.combine(dtEnd, endtime)
            
            delta = newEnd - newStart
            sec = delta.total_seconds()
            hours = sec / (60 * 60)
            
            existing_bookings = db.session.query(roombookings).filter(and_(roombookings.Start <= newEnd, roombookings.End >= newStart, roombookings.RoomID == request.form.get('roomSelect'))).all()

            if newEnd < newStart:
                flash('Booking time invalid', category='error')
            elif hours > 2:
                #check if the hours booked is more than 2 hours
                flash('Booking time must be 2 hours or less', category='error')
            elif existing_bookings:
                # Handle the conflict, maybe return a message or perform another action
                flash('Room Already occupied for that time', category='error')
            elif Purpose == "":
                flash('Please fill in the purpose of your booking', category='error')
            else:
                new_rbook = roombookings(RoomID=roomID,StudID=StudID,StaffID=StaffID,Start=newStart,End=newEnd,Purpose=Purpose,RBookStatus="Upcoming")  #providing the schema for the note
                db.session.add(new_rbook) #adding the note to the database 
                db.session.commit()
                
                bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                subject = 'Room Booking on ' + request.form.get('rbookstart') + ' is CONFIRMED'
                recipients = current_user.StaffEmail
                content = 'Your Room Booking on ' + request.form.get('rbookstart') + ' at '+ bookedroom.RoomName +' is confirmed!'
                send_mail(subject, recipients, content)
                
                flash('Room Booking was Added!', category='success')
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        #return render_template("homeStaff.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList, is_Student=False, is_Staff=False, is_Admin=True, announcements=announcements)
        return redirect(url_for('views.bookingHistory'))
    else:
        flash('Admin Not allowed on this URL', category='error')
        return redirect(url_for('views.homeAdmin'))
       
@views.route('/AddEBook', methods=['GET','POST'])
@login_required
def AddEBook():
    if current_user.is_Student():
        if request.method == 'POST': 
            roomID = request.form.get('roomSelect')#Gets the data from the HTML
            StudID = request.form.get('studid')
            StaffID = None
            Purpose = request.form.get('EBookPurpose')
            AddDetail = request.form.get('EBookAddDetails')
            
            
            dtStart = datetime.strptime(request.form.get('ebookstart'), '%Y-%m-%d').date()
            starttime = datetime.strptime(request.form.get('ebooktimeStart'), '%H:%M:%S').time()
            newStart = datetime.combine(dtStart, starttime)
            
            dtEnd = datetime.strptime(request.form.get('ebookend'), '%Y-%m-%d').date()
            endtime = datetime.strptime(request.form.get('ebooktimeEnd'), '%H:%M:%S').time()
            newEnd = datetime.combine(dtEnd, endtime)
            
            delta = newEnd - newStart
            sec = delta.total_seconds()
            hours = sec / (60 * 60)
            
            existing_bookings = db.session.query(eventbookings).filter(and_(eventbookings.Start <= newEnd, eventbookings.End >= newStart, eventbookings.RoomID == request.form.get('roomSelect'))).all()
            
            if newEnd < newStart:
                flash('Booking time invalid', category='error')
            elif existing_bookings:
                # Handle the conflict, maybe return a message or perform another action
                flash('Room Already occupied for that time', category='error')
            elif Purpose == "":
                flash('Please fill in the purpose of your booking', category='error')
            else:
                new_ebook = eventbookings(RoomID=roomID,StudID=StudID,StaffID=StaffID,Start=newStart,End=newEnd,Purpose=Purpose,AddDetail=AddDetail,EbookStatus="Upcoming")  #providing the schema for the note
                db.session.add(new_ebook) #adding the note to the database 
                db.session.commit()
                
                bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                subject = 'Room Booking on ' + request.form.get('ebookstart') + ' is CONFIRMED'
                recipients = current_user.StudEmail
                content = 'Your Room Booking on ' + request.form.get('ebookstart') + ' at '+ bookedroom.RoomName +' is confirmed!'
                send_mail(subject, recipients, content)
                
                flash('Event Booking was Added!', category='success')
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        #return render_template("homeStud.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList, is_Student=False, is_Staff=False, is_Admin=True, announcements=announcements)
        return redirect(url_for('views.bookingHistory'))
    elif current_user.is_Staff():
        if request.method == 'POST': 
            roomID = request.form.get('roomSelect')#Gets the data from the HTML
            StudID = None
            StaffID = request.form.get('staffid')
            Purpose = request.form.get('EBookPurpose')
            AddDetail = request.form.get('EBookAddDetails')
            
            
            dtStart = datetime.strptime(request.form.get('ebookstart'), '%Y-%m-%d').date()
            starttime = datetime.strptime(request.form.get('ebooktimeStart'), '%H:%M:%S').time()
            newStart = datetime.combine(dtStart, starttime)
            
            dtEnd = datetime.strptime(request.form.get('ebookend'), '%Y-%m-%d').date()
            endtime = datetime.strptime(request.form.get('ebooktimeEnd'), '%H:%M:%S').time()
            newEnd = datetime.combine(dtEnd, endtime)
            
            delta = newEnd - newStart
            sec = delta.total_seconds()
            hours = sec / (60 * 60)
            
            existing_bookings = db.session.query(eventbookings).filter(and_(eventbookings.Start <= newEnd, eventbookings.End >= newStart, eventbookings.RoomID == request.form.get('roomSelect'))).all()
            
            if newEnd < newStart:
                flash('Booking time invalid', category='error')
            elif existing_bookings:
                # Handle the conflict, maybe return a message or perform another action
                flash('Room Already occupied for that time', category='error')
            elif Purpose == "":
                flash('Please fill in the purpose of your booking', category='error')
            else:
                new_ebook = eventbookings(RoomID=roomID,StudID=StudID,StaffID=StaffID,Start=newStart,End=newEnd,Purpose=Purpose,AddDetail=AddDetail,EbookStatus="Upcoming")  #providing the schema for the note
                db.session.add(new_ebook) #adding the note to the database 
                db.session.commit()
                
                bookedroom = db.session.query(roomlist).filter_by(RoomID = roomID).first()
                subject = 'Room Booking on ' + request.form.get('ebookstart') + ' is CONFIRMED'
                recipients = current_user.StaffEmail
                content = 'Your Room Booking on ' + request.form.get('ebookstart') + ' at '+ bookedroom.RoomName +' is confirmed!'
                send_mail(subject, recipients, content)
                
                flash('Event Booking was Added!', category='success')
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        #return render_template("homeStaff.html", user=current_user, roomlist=rooms, staff=staffList,student=studList, roombookings=rBookList, is_Student=False, is_Staff=False, is_Admin=True, announcements=announcements)
        return redirect(url_for('views.bookingHistory'))
    else:
        flash('Admin Not allowed on this URL', category='error')
        return redirect(url_for('views.homeAdmin'))       
 
@views.route('/deleteRBook/<RBookID>/', methods = ['GET', 'POST'])
def deleteRBook(RBookID):
    if current_user.is_Admin():
        rbook = db.session.query(roombookings).filter_by(RBookID = RBookID).first()
        db.session.delete(rbook)
        db.session.commit()
        flash("Room Booking has been deleted")
        return redirect(url_for('views.ManagementRoomBookings'))
    elif current_user.is_Student():
        rbook = db.session.query(roombookings).filter_by(RBookID = RBookID).first()
        if rbook.StudID == current_user.StudID:
            db.session.delete(rbook)
            db.session.commit()
            flash("Room Booking has been deleted")
        else:
            flash("No permissions for this action")
        return redirect(url_for('views.bookingHistory'))
    elif current_user.is_Staff():
        rbook = db.session.query(roombookings).filter_by(RBookID = RBookID).first()
        if rbook.StaffID == current_user.StaffID:
            db.session.delete(rbook)
            db.session.commit()
            flash("Room Booking has been deleted")
        else:
            flash("No permissions for this action")
        return redirect(url_for('views.bookingHistory'))
    else:
        flash('Access Forbidden', category='error')
        return redirect(url_for('views.home'))
    
@views.route('/deleteEBook/<EBookID>/', methods = ['GET', 'POST'])
def deleteEBook(EBookID):
    if current_user.is_Admin():
        ebook = db.session.query(eventbookings).filter_by(EBookID = EBookID).first()
        db.session.delete(ebook)
        db.session.commit()
        flash("Event Booking has been deleted")
        return redirect(url_for('views.ManagementEventBookings'))
    elif current_user.is_Student():
        ebook = db.session.query(eventbookings).filter_by(EBookID = EBookID).first()
        if ebook.StudID == current_user.StudID:
            db.session.delete(ebook)
            db.session.commit()
            flash("Event Booking has been deleted")
        else:
            flash("No permissions for this action")
        return redirect(url_for('views.bookingHistory'))
    elif current_user.is_Staff():
        ebook = db.session.query(eventbookings).filter_by(EBookID = EBookID).first()
        if ebook.StaffID == current_user.StaffID:
            db.session.delete(ebook)
            db.session.commit()
            flash("Event Booking has been deleted")
        else:
            flash("No permissions for this action")
        return redirect(url_for('views.bookingHistory'))
    else:
        flash('Access Forbidden', category='error')
        return redirect(url_for('views.home'))

@views.route('/updateRBook/', methods = ['POST'])
def updateRBook():
    if request.method == "POST":
        rbook = db.session.query(roombookings).filter_by(RBookID = request.form.get('RBookID')).first()
        
        dtStart = datetime.strptime(request.form.get('rbookstart'), '%Y-%m-%d').date()
        starttime = datetime.strptime(request.form.get('rbooktimeStart'), '%H:%M:%S').time()
        newStart = datetime.combine(dtStart, starttime)
            
        dtEnd = datetime.strptime(request.form.get('rbookend'), '%Y-%m-%d').date()
        endtime = datetime.strptime(request.form.get('rbooktimeEnd'), '%H:%M:%S').time()
        newEnd = datetime.combine(dtEnd, endtime)
            
        delta = newEnd - newStart
        sec = delta.total_seconds()
        hours = sec / (60 * 60)
        
        rbook.Start = newStart
        rbook.End = newEnd
        print(request.form.get('roomSelect'))
        rbook.RoomID = request.form.get('roomSelect')
        rbook.Purpose = request.form.get('RBookPurpose')
        rbook.RBookStatus = request.form.get('rBookStatusType')
        
        existing_bookings = db.session.query(roombookings).filter(and_(roombookings.Start <= newEnd, roombookings.End >= newStart, roombookings.RoomID == request.form.get('roomSelect'))).all()

        for rb in existing_bookings:
            if rb.RBookID == rbook.RBookID:
                matchingRBook = rb
        
        if newEnd < newStart:
            flash('Booking time invalid', category='error')
        elif hours > 2:
            #check if the hours booked is more than 2 hours
            flash('Booking time must be 2 hours or less', category='error')
        elif existing_bookings and not matchingRBook:
            # Handle the conflict, maybe return a message or perform another action
            flash('Room Already occupied for that time', category='error')
        elif rbook.Purpose == "":
            flash('Please fill in the purpose of your booking', category='error')
        else:
            db.session.commit()
                
            bookedroom = db.session.query(roomlist).filter_by(RoomID = rbook.RoomID).first()
            subject = 'Room Booking on ' + request.form.get('rbookstart') + ' is UPDATED'
            if rbook.StudID != None:
                stud = db.session.query(student).filter_by(StudID = rbook.StudID).first()
                recipients = stud.StudEmail
            elif rbook.StaffID != None:
                staff = db.session.query(staff).filter_by(StudID = rbook.StaffID).first()
                recipients = staff.StaffEmail
            content = 'Your Room Booking on ' + request.form.get('rbookstart') + ' at '+ bookedroom.RoomName +' was Updated!\nStart Time: ' + rbook.Start.strftime("%m/%d/%Y, %H:%M:%S") + '\nEnd Time: ' + rbook.End.strftime("%m/%d/%Y, %H:%M:%S") + '\nPurpose: ' + rbook.Purpose
            send_mail(subject, recipients, content)
                
            flash('Room Booking was updated!', category='success')
        
        if current_user.is_Admin():
            return redirect(url_for('views.ManagementRoomBookings'))
        if current_user.is_Student():
            return redirect(url_for('views.bookingHistory'))
        if current_user.is_Staff():
            return redirect(url_for('views.bookingHistory'))
    
@views.route('/updateEBook/', methods = ['POST'])
def updateEBook():
    if request.method == "POST":
        ebook = db.session.query(eventbookings).filter_by(EBookID = request.form.get('EBookID')).first()
        
        dtStart = datetime.strptime(request.form.get('ebookstart'), '%Y-%m-%d').date()
        starttime = datetime.strptime(request.form.get('ebooktimeStart'), '%H:%M:%S').time()
        newStart = datetime.combine(dtStart, starttime)
            
        dtEnd = datetime.strptime(request.form.get('ebookend'), '%Y-%m-%d').date()
        endtime = datetime.strptime(request.form.get('ebooktimeEnd'), '%H:%M:%S').time()
        newEnd = datetime.combine(dtEnd, endtime)
            
        delta = newEnd - newStart
        sec = delta.total_seconds()
        hours = sec / (60 * 60)
        
        ebook.Start = newStart
        ebook.End = newEnd
        ebook.RoomID = request.form.get('roomSelect')
        ebook.Purpose = request.form.get('EBookPurpose')
        ebook.AddDetail = request.form.get('EBookAddDetail')
        ebook.EbookStatus = request.form.get('eBookStatusType')
        
        existing_bookings = db.session.query(eventbookings).filter(and_(eventbookings.Start <= newEnd, eventbookings.End >= newStart, eventbookings.RoomID == request.form.get('roomSelect'))).all()

        for eb in existing_bookings:
            if eb.EBookID == ebook.EBookID:
                matchingRBook = eb
        
        if newEnd < newStart:
            flash('Booking time invalid', category='error')
        elif existing_bookings and not matchingRBook:
            # Handle the conflict, maybe return a message or perform another action
            flash('Room Already occupied for that time', category='error')
        elif ebook.Purpose == "":
            flash('Please fill in the purpose of your booking', category='error')
        else:
            db.session.commit()
                
            bookedroom = db.session.query(roomlist).filter_by(RoomID = ebook.RoomID).first()
            subject = 'Event Booking on ' + request.form.get('ebookstart') + ' is UPDATED'
            if ebook.StudID != None:
                stud = db.session.query(student).filter_by(StudID = ebook.StudID).first()
                recipients = stud.StudEmail
            elif ebook.StaffID != None:
                staff = db.session.query(staff).filter_by(StudID = ebook.StaffID).first()
                recipients = staff.StaffEmail
            content = 'Your Event Booking on ' + request.form.get('ebookstart') + ' at '+ bookedroom.RoomName +' was Updated!\nStart Time: ' + ebook.Start.strftime("%m/%d/%Y, %H:%M:%S") + '\nEnd Time: ' + ebook.End.strftime("%m/%d/%Y, %H:%M:%S") + '\nPurpose: ' + ebook.Purpose
            send_mail(subject, recipients, content)
                
            flash('Event Booking was updated!', category='success')
        
        if current_user.is_Admin():
            return redirect(url_for('views.ManagementEventBookings'))
        if current_user.is_Student():
            return redirect(url_for('views.bookingHistory'))
        if current_user.is_Staff():
            return redirect(url_for('views.bookingHistory'))    

@views.route('/ViewRoomAccessLog', methods=['GET','POST'])
@login_required
def ViewAccessLog():
    if current_user.is_Admin():
        if request.method == 'POST': 
            print("no form in ManagementFaces")
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        roomAccessList = db.session.query(roomaccesslog).order_by(desc(roomaccesslog.Timestamp)).all()
        return render_template("AccessLogView.html", 
                               user=current_user, roomlist=rooms, staff=staffList,student=studList, 
                               roomaccesslog=roomAccessList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/deleteRAccessLog/<rmaID>/', methods = ['GET', 'POST'])
def deleteRAccessLog(rmaID):
    if current_user.is_Admin():
        rma = db.session.query(roomaccesslog).filter_by(rmaID = rmaID).first()
        db.session.delete(rma)
        db.session.commit()
        flash("Room Access Log record has been deleted")
        return redirect(url_for('views.ViewAccessLog'))
    else:
        flash('Access Forbidden', category='error')
        return redirect(url_for('views.home'))

@views.route('/feedback', methods = ['GET', 'POST'])
@login_required
def feedback():
    print(relations)
    if current_user.is_Student():
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        rBookList = db.session.query(roombookings)
        #feedbackList = db.session.query(feedback) #throws "NotImplementedError: Operator 'contains' is not supported on this expression"
        rBookTimeList = []
        
        for r in rBookList:
            rBookTime = {
                'RBookID': r.RBookID,
                'StartDate': r.Start.date().strftime("%Y-%m-%d"),
                'StartTime': r.Start.time().strftime("%H:%M:%S"),
                'EndDate': r.End.date().strftime("%Y-%m-%d"),
                'EndTime': r.End.time().strftime("%H:%M:%S")
            }
            rBookTimeList.append(rBookTime)
        
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        eBookList = db.session.query(eventbookings).order_by(desc(eventbookings.Start)).all()
        eBookTimeList = []
        
        for e in eBookList:
            eBookTime = {
                'EBookID': e.EBookID,
                'StartDate': e.Start.date().strftime("%Y-%m-%d"),
                'StartTime': e.Start.time().strftime("%H:%M:%S"),
                'EndDate': e.End.date().strftime("%Y-%m-%d"),
                'EndTime': e.End.time().strftime("%H:%M:%S")
            }
            eBookTimeList.append(eBookTime)
            
        return render_template("Feedback.html", user=current_user, roomlist=rooms,student=studList, roombookings=rBookList, eventbookings=eBookList, 
                               eBookTimeList=eBookTimeList,rBookTimeList=rBookTimeList, is_Student=True, is_Staff=False, is_Admin=False, announcements=announcements)
    elif current_user.is_Staff():
        rooms = db.session.query(roomlist)
        staffList = db.session.query(staff)
        rBookList = db.session.query(roombookings)
        #feedbackList = db.session.query(feedback).filter_by(StaffID = current_user.StaffID)
        rBookTimeList = []
        
        for r in rBookList:
            rBookTime = {
                'RBookID': r.RBookID,
                'StartDate': r.Start.date().strftime("%Y-%m-%d"),
                'StartTime': r.Start.time().strftime("%H:%M:%S"),
                'EndDate': r.End.date().strftime("%Y-%m-%d"),
                'EndTime': r.End.time().strftime("%H:%M:%S")
            }
            rBookTimeList.append(rBookTime)
        
        announcements = db.session.query(announcement).order_by(desc(announcement.PostDate)).all()
        eBookList = db.session.query(eventbookings).order_by(desc(eventbookings.Start)).all()
        eBookTimeList = []
        
        for e in eBookList:
            eBookTime = {
                'EBookID': e.EBookID,
                'StartDate': e.Start.date().strftime("%Y-%m-%d"),
                'StartTime': e.Start.time().strftime("%H:%M:%S"),
                'EndDate': e.End.date().strftime("%Y-%m-%d"),
                'EndTime': e.End.time().strftime("%H:%M:%S")
            }
            eBookTimeList.append(eBookTime)
        return render_template("Feedback.html", user=current_user, roomlist=rooms, staff=staffList, roombookings=rBookList,
                               eventbookings=eBookList, eBookTimeList=eBookTimeList, rBookTimeList=rBookTimeList, is_Student=False, is_Staff=True, is_Admin=False, announcements=announcements)
    else:
        flash('Admin Not allowed on this URL', category='error')
        return redirect(url_for('views.homeAdmin'))

@views.route('/ManageReport', methods=['GET','POST'])
@login_required
def ManagementReport():
    if current_user.is_Admin():
        if request.method == 'POST': 
            print("no form in ManagementFaces")
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        reportList = db.session.query(report).all()
        return render_template("manageReport.html", 
                               user=current_user, roomlist=rooms, staff=staffList,student=studList, 
                               report=reportList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/getReport', methods=['GET','POST'])
@login_required
def getReport():
    if current_user.is_Admin():
        rooms = db.session.query(roomlist)
        studList = db.session.query(student)
        staffList = db.session.query(staff)
        reportList = db.session.query(report).all()
        rbookList = db.session.query(roombookings)
        ebookList = db.session.query(eventbookings)
        rooms = db.session.query(roomlist)
        if request.method == 'POST': 
            for rm in rooms:
                totalbookings = 0
                totalhoursbooked = 0
                monthyear = request.form.get('reportmonth')
                for r in rbookList:
                    # Extract year and month
                    year = r.Start.year
                    month = r.Start.month
                    # Combine year and month into "YYYY-MM" format
                    rbookmonthyear = f"{year:04d}-{month:02d}"
                    if r.RoomID == rm.RoomID and rbookmonthyear == monthyear:
                        totalbookings += 1
                        delta = r.End - r.Start
                        sec = delta.total_seconds()
                        totalhoursbooked += sec / (60 * 60)
                for e in ebookList:
                    # Extract year and month
                    year = e.Start.year
                    month = e.Start.month
                    # Combine year and month into "YYYY-MM" format
                    ebookmonthyear = f"{year:04d}-{month:02d}"
                    if e.RoomID == rm.RoomID and ebookmonthyear == monthyear:
                        totalbookings += 1
                        delta = e.End - e.Start
                        sec = delta.total_seconds()
                        totalhoursbooked += sec / (60 * 60)
                monthyeardt=datetime.strptime(monthyear, '%Y-%m').date()
                # Extract year and month
                year = monthyeardt.year
                month = monthyeardt.month

                # Format the month as its name
                month_name = monthyeardt.strftime('%B')

                # Combine year and month name
                title = f"{year}-{month_name}"
                new_report = report(ReportTitle=title,RoomID=rm.RoomID,totalNumBookings=totalbookings,totalHoursBooked=totalhoursbooked,MonthYear=monthyeardt)  #providing the schema for the note
                reportExists = db.session.query(report).filter(and_(report.RoomID == rm.RoomID, report.MonthYear == monthyeardt)).first()
                if reportExists:
                    if reportExists.totalNumBookings != totalbookings:
                        reportExists.totalNumBookings = totalbookings
                        reportExists.totalHoursBooked = totalhoursbooked
                        db.session.commit()
                        flash('Some reports were updated!', category='Success')
                else:
                    db.session.add(new_report) #adding the note to the database 
                    db.session.commit()
                    flash('Reports were added!', category='Success')
        return render_template("manageReport.html", 
                               user=current_user, roomlist=rooms, staff=staffList,student=studList, 
                               report=reportList, is_Student=False, is_Staff=False, is_Admin=True)
    else:
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))

@views.route('/deleteReport/<ReportID>/', methods = ['GET', 'POST'])
def deleteReport(ReportID):
    if current_user.is_Admin():
        rep = db.session.query(report).filter_by(ReportID = ReportID).first()
        db.session.delete(rep)
        db.session.commit()
        flash("Report record has been deleted")
        return redirect(url_for('views.ManagementReport'))
    else:
        flash('Access Forbidden', category='error')
        return redirect(url_for('views.home'))

def send_mail(subject, recipients_email, content):
    msg = Message(
        subject,
        sender = 'fyplibraryroomalert@gmail.com',
        recipients= [recipients_email]
    )
    msg.body = content
    mail.send(msg)
    return "Message sent"