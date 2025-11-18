"""User models: Student, Staff, Admin."""
from flask_login import UserMixin
from sqlalchemy import Column, String, Enum
from .base import db


class UserMixinBase(UserMixin):
    """Base mixin for user models."""
    
    def is_Student(self):
        return False
    
    def is_Staff(self):
        return False
    
    def is_Admin(self):
        return False


class Student(db.Model, UserMixinBase):
    """Student model."""
    __tablename__ = 'student'
    
    StudID = Column(String(50), primary_key=True)
    StudPassword = Column(String(255), nullable=False)
    StudName = Column(String(255), nullable=False)
    StudEmail = Column(String(255), nullable=False)
    StudContactNum = Column(String(20), nullable=False)
    AccountStatus = Column(Enum('Pending', 'Approved', 'Rejected', name='account_status'), 
                          default='Pending', nullable=False)
    
    def get_id(self):
        return self.StudID
    
    def is_Student(self):
        return True
    
    def __repr__(self):
        return f'<Student {self.StudID}: {self.StudName}>'


class Staff(db.Model, UserMixinBase):
    """Staff model."""
    __tablename__ = 'staff'
    
    StaffID = Column(String(50), primary_key=True)
    StaffPassword = Column(String(255), nullable=False)
    StaffName = Column(String(255), nullable=False)
    StaffEmail = Column(String(255), nullable=False)
    StaffContactNum = Column(String(20), nullable=False)
    AccountStatus = Column(Enum('Pending', 'Approved', 'Rejected', name='account_status'),
                          default='Pending', nullable=False)
    
    def get_id(self):
        return self.StaffID
    
    def is_Staff(self):
        return True
    
    def __repr__(self):
        return f'<Staff {self.StaffID}: {self.StaffName}>'


class Admin(db.Model, UserMixinBase):
    """Admin model."""
    __tablename__ = 'admin'
    
    AdminID = Column(String(50), primary_key=True)
    AdminPassword = Column(String(255), nullable=False)
    AdminName = Column(String(255), nullable=False)
    AdminEmail = Column(String(255), nullable=False)
    AdminContactNum = Column(String(20), nullable=False)
    
    # Relationships
    announcements = db.relationship('Announcement', backref='admin', lazy=True)
    
    def get_id(self):
        return self.AdminID
    
    def is_Admin(self):
        return True
    
    def __repr__(self):
        return f'<Admin {self.AdminID}: {self.AdminName}>'

