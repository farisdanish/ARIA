"""Authentication service."""
import bcrypt
from typing import Optional
from ..models.user import Student, Staff, Admin
from ..models.base import db
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> bytes:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """Check if password matches hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password check failed: {str(e)}")
            return False
    
    @staticmethod
    def find_user(user_id: str) -> Optional[Student | Staff | Admin]:
        """Find a user by ID (checks all user types)."""
        student = db.session.query(Student).filter_by(StudID=user_id).first()
        if student:
            return student
        
        staff = db.session.query(Staff).filter_by(StaffID=user_id).first()
        if staff:
            return staff
        
        admin = db.session.query(Admin).filter_by(AdminID=user_id).first()
        if admin:
            return admin
        
        return None
    
    @staticmethod
    def authenticate_user(user_id: str, password: str) -> Optional[Student | Staff | Admin]:
        """
        Authenticate a user.
        
        Returns:
            User object if authentication successful, None otherwise
        """
        user = AuthService.find_user(user_id)
        if not user:
            return None
        
        # Check password based on user type
        if isinstance(user, Student):
            if AuthService.check_password(password, user.StudPassword):
                return user
        elif isinstance(user, Staff):
            if AuthService.check_password(password, user.StaffPassword):
                return user
        elif isinstance(user, Admin):
            if AuthService.check_password(password, user.AdminPassword):
                return user
        
        return None
    
    @staticmethod
    def create_student(stud_id: str, stud_name: str, stud_email: str, 
                      stud_contact: str, password: str) -> Student:
        """Create a new student account."""
        hashed_password = AuthService.hash_password(password)
        student = Student(
            StudID=stud_id,
            StudPassword=hashed_password.decode('utf-8'),
            StudName=stud_name,
            StudEmail=stud_email,
            StudContactNum=stud_contact,
            AccountStatus='Pending'
        )
        db.session.add(student)
        db.session.commit()
        logger.info(f"Student account created: {stud_id}")
        return student
    
    @staticmethod
    def create_staff(staff_id: str, staff_name: str, staff_email: str,
                    staff_contact: str, password: str) -> Staff:
        """Create a new staff account."""
        hashed_password = AuthService.hash_password(password)
        staff = Staff(
            StaffID=staff_id,
            StaffPassword=hashed_password.decode('utf-8'),
            StaffName=staff_name,
            StaffEmail=staff_email,
            StaffContactNum=staff_contact,
            AccountStatus='Pending'
        )
        db.session.add(staff)
        db.session.commit()
        logger.info(f"Staff account created: {staff_id}")
        return staff

