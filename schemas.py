from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum

# Enums
class EventStatus(str, Enum):
    active = "active"
    cancelled = "cancelled"
    completed = "completed"

class EventType(str, Enum):
    workshop = "workshop"
    seminar = "seminar"
    competition = "competition"
    conference = "conference"
    hackathon = "hackathon"
    cultural = "cultural"

class RegistrationStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"

# Base schemas
class CollegeBase(BaseModel):
    name: str = Field(..., max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None

class CollegeCreate(CollegeBase):
    pass

class College(CollegeBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    college_id: int
    phone: Optional[str] = Field(None, max_length=15)
    year_of_study: Optional[int] = Field(None, ge=1, le=4)

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudentWithCollege(Student):
    college: College

class EventBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    event_type: EventType
    event_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    venue: Optional[str] = Field(None, max_length=100)
    college_id: int
    max_capacity: int = Field(100, ge=1)

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    venue: Optional[str] = Field(None, max_length=100)
    max_capacity: Optional[int] = Field(None, ge=1)
    status: Optional[EventStatus] = None

class Event(EventBase):
    id: int
    status: EventStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class EventWithCollege(Event):
    college: College

class RegistrationBase(BaseModel):
    student_id: int
    event_id: int

class RegistrationCreate(RegistrationBase):
    pass

class Registration(RegistrationBase):
    id: int
    registration_date: datetime
    status: RegistrationStatus
    
    class Config:
        from_attributes = True

class RegistrationWithDetails(Registration):
    student: Student
    event: Event

class AttendanceBase(BaseModel):
    student_id: int
    event_id: int

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    attended_at: datetime
    
    class Config:
        from_attributes = True

class AttendanceWithDetails(Attendance):
    student: Student
    event: Event

class FeedbackBase(BaseModel):
    student_id: int
    event_id: int
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackWithDetails(Feedback):
    student: Student
    event: Event

# Response schemas
class StandardResponse(BaseModel):
    message: str
    data: Optional[dict] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    per_page: int
    pages: int

# Report schemas
class EventRegistrationReport(BaseModel):
    event_id: int
    event_title: str
    event_date: date
    total_registrations: int
    confirmed_registrations: int
    cancelled_registrations: int
    available_spots: int

class AttendanceReport(BaseModel):
    event_id: int
    event_title: str
    event_date: date
    total_registered: int
    total_attended: int
    attendance_percentage: float

class FeedbackReport(BaseModel):
    event_id: int
    event_title: str
    event_date: date
    total_feedback: int
    average_rating: float
    rating_distribution: dict

class StudentParticipationReport(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    college_name: str
    total_registrations: int
    total_attendances: int
    attendance_rate: float
    events_attended: List[str]

class EventPopularityReport(BaseModel):
    event_id: int
    event_title: str
    event_type: str
    event_date: date
    college_name: str
    registrations: int
    attendance: int
    average_rating: Optional[float]
    popularity_score: float

# Error schemas
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None