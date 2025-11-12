
from .app import app
from .app import db
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect
from flask_login import UserMixin

Base = automap_base()

class student(Base, UserMixin):
    __tablename__ = 'student'
    
    def get_id(self):
        return self.StudID
    
    def is_Student(self):
        return True
    
    def is_Staff(self):
        return False
    def is_Admin(self):
        return False

class staff(Base, UserMixin):
    __tablename__ = 'staff'
    
    def get_id(self):
        return self.StaffID
    
    def is_Staff(self):
        return True
    def is_Student(self):
        return False
    def is_Admin(self):
        return False
    
class admin(Base, UserMixin):
    __tablename__ = 'admin'
    announcements = db.relationship('announcement')

    def get_id(self):
        return self.AdminID
    
    def is_Admin(self):
        return True
    def is_Staff(self):
        return False
    def is_Student(self):
        return False

class announcement(Base):
    __tablename__ = 'announcement'
    
class roomlist(Base):
    __tablename__ = 'roomlist'
    
class roombookings(Base):
    __tablename__ = 'roombookings'

class eventbookings(Base):
    __tablename__ = 'eventbookings'

class registeredfaces(Base):
    __tablename__ = 'registeredfaces'

class roomaccesslog(Base):
    __tablename__ = 'roomaccesslog'

class feedback(Base):
    __tablename__ = 'feedback'
    
class report(Base):
    __tablename__ = 'report'

with app.app_context():
    Base.prepare(db.engine, reflect=True)
    
relations = inspect(feedback).relationships.items() #code to check table relations
attr_names = [c_attr.key for c_attr in inspect(feedback).mapper.column_attrs] #code to check table attributes/columns

# admin = Base.classes.admin
# # student = Base.classes.student
# staff = Base.classes.staff
# announcement = Base.classes.announcement

