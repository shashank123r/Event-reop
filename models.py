from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class College(Base):
    __tablename__ = "colleges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    location = Column(String(100))
    contact_email = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    students = relationship("Student", back_populates="college")
    events = relationship("Event", back_populates="college")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    phone = Column(String(15))
    year_of_study = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    college = relationship("College", back_populates="students")
    registrations = relationship("Registration", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    feedback_entries = relationship("Feedback", back_populates="student")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(50), nullable=False)  # workshop, seminar, competition, etc.
    event_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time)
    end_time = Column(Time)
    venue = Column(String(100))
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    max_capacity = Column(Integer, default=100)
    status = Column(String(20), default="active")  # active, cancelled, completed
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    college = relationship("College", back_populates="events")
    registrations = relationship("Registration", back_populates="event")
    attendances = relationship("Attendance", back_populates="event")
    feedback_entries = relationship("Feedback", back_populates="event")

class Registration(Base):
    __tablename__ = "registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    registration_date = Column(DateTime, default=func.now())
    status = Column(String(20), default="confirmed")  # confirmed, cancelled
    
    # Relationships
    student = relationship("Student", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
    
    # Unique constraint to prevent duplicate registrations
    __table_args__ = (UniqueConstraint('student_id', 'event_id', name='unique_student_event_registration'),)

class Attendance(Base):
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    attended_at = Column(DateTime, default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="attendances")
    event = relationship("Event", back_populates="attendances")
    
    # Unique constraint to prevent duplicate attendance
    __table_args__ = (UniqueConstraint('student_id', 'event_id', name='unique_student_event_attendance'),)

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comments = Column(Text)
    submitted_at = Column(DateTime, default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="feedback_entries")
    event = relationship("Event", back_populates="feedback_entries")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('student_id', 'event_id', name='unique_student_event_feedback'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range_check'),
    )