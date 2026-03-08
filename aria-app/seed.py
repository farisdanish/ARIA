import os
import sys
from datetime import datetime, timedelta
from website.app import create_app
from website.models.base import db
from website.models.user import Student, Staff, Admin
from website.models.room import RoomList, RoomBooking, EventBooking
from website.models.announcement import Announcement
from website.services.auth_service import AuthService

def seed_database():
    app = create_app()
    with app.app_context():
        print("Starting database seeding...")
        
        # 1. Create Admin
        admin_id = "admin1"
        if not db.session.query(Admin).filter_by(AdminID=admin_id).first():
            hashed_pw = AuthService.hash_password("admin123").decode('utf-8')
            admin = Admin(
                AdminID=admin_id,
                AdminPassword=hashed_pw,
                AdminName="System Admin",
                AdminEmail="admin@aria.com",
                AdminContactNum="0123456789"
            )
            db.session.add(admin)
            print(f"Admin created: {admin_id}")
        
        # 2. Create Student
        stud_id = "stud1"
        if not db.session.query(Student).filter_by(StudID=stud_id).first():
            hashed_pw = AuthService.hash_password("stud123").decode('utf-8')
            student = Student(
                StudID=stud_id,
                StudPassword=hashed_pw,
                StudName="John Doe",
                StudEmail="john@student.com",
                StudContactNum="0112233445",
                AccountStatus="Approved"
            )
            db.session.add(student)
            print(f"Student created: {stud_id}")
            
        # 3. Create Staff
        staff_id = "staff1"
        if not db.session.query(Staff).filter_by(StaffID=staff_id).first():
            hashed_pw = AuthService.hash_password("staff123").decode('utf-8')
            staff = Staff(
                StaffID=staff_id,
                StaffPassword=hashed_pw,
                StaffName="Jane Smith",
                StaffEmail="jane@staff.com",
                StaffContactNum="0198765432",
                AccountStatus="Approved"
            )
            db.session.add(staff)
            print(f"Staff created: {staff_id}")
            
        # 4. Create Rooms
        rooms_data = [
            {"name": "Meeting Room A", "type": "Normal Room", "info": "Standard meeting room with TV"},
            {"name": "Lab 101", "type": "Normal Room", "info": "Computer lab"},
            {"name": "Grand Hall", "type": "Event Room", "info": "Large hall for major events"},
            {"name": "Seminar Hall B", "type": "Event Room", "info": "Medium seminar hall"}
        ]
        
        created_rooms = []
        for r_data in rooms_data:
            room = db.session.query(RoomList).filter_by(RoomName=r_data["name"]).first()
            if not room:
                room = RoomList(
                    RoomName=r_data["name"],
                    RoomType=r_data["type"],
                    RoomInfo=r_data["info"],
                    RoomStatus="Available",
                    AdminID=admin_id
                )
                db.session.add(room)
                db.session.flush() # To get RoomID
                print(f"Room created: {r_data['name']}")
            created_rooms.append(room)
            
        # 5. Create Announcements
        if not db.session.query(Announcement).first():
            announcements = [
                Announcement(Title="Welcome to ARIA", Content="Welcome to the new ARIA Smart Booking Platform!", AdminID=admin_id),
                Announcement(Title="Maintenance Notice", Content="Meeting Room A will be closed for maintenance tomorrow.", AdminID=admin_id),
                Announcement(Title="Upcoming Career Fair", Content="Grand Hall will host the Career Fair next week.", AdminID=admin_id)
            ]
            db.session.add_all(announcements)
            print("Announcements created")
            
        # 6. Create some bookings
        if not db.session.query(RoomBooking).first() and created_rooms:
            # Past booking
            past_rb = RoomBooking(
                RoomID=created_rooms[0].RoomID,
                StudID=stud_id,
                Start=datetime.now() - timedelta(days=1, hours=2),
                End=datetime.now() - timedelta(days=1),
                Purpose="Group Project",
                RBookStatus="Completed"
            )
            # Upcoming booking
            future_rb = RoomBooking(
                RoomID=created_rooms[1].RoomID,
                StudID=stud_id,
                Start=datetime.now() + timedelta(days=1),
                End=datetime.now() + timedelta(days=1, hours=1),
                Purpose="Study Session",
                RBookStatus="Upcoming"
            )
            db.session.add_all([past_rb, future_rb])
            print("Room bookings created")
            
        if not db.session.query(EventBooking).first() and created_rooms:
            event_hall = next((r for r in created_rooms if r.RoomType == "Event Room"), None)
            if event_hall:
                eb = EventBooking(
                    RoomID=event_hall.RoomID,
                    StaffID=staff_id,
                    Start=datetime.now() + timedelta(days=2),
                    End=datetime.now() + timedelta(days=2, hours=4),
                    Purpose="Staff Training",
                    AddDetail="Need projector and 20 chairs",
                    EbookStatus="Upcoming"
                )
                db.session.add(eb)
                print("Event booking created")
        
        db.session.commit()
        print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
