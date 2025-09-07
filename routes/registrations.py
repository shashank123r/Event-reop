from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date
from database import get_db
from models import Registration, Student, Event
from schemas import (
    Registration as RegistrationSchema,
    RegistrationCreate,
    RegistrationWithDetails,
    StandardResponse
)

router = APIRouter()

@router.post("/registrations", response_model=RegistrationSchema, status_code=status.HTTP_201_CREATED)
async def create_registration(registration: RegistrationCreate, db: Session = Depends(get_db)):
    """Register a student for an event"""
    # Check if student exists
    student = db.query(Student).filter(Student.id == registration.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if event exists
    event = db.query(Event).filter(Event.id == registration.event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if event is active
    if event.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register for inactive or cancelled events"
        )
    
    # Check if event is in the future
    if event.event_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register for past events"
        )
    
    # Check if student is already registered
    existing_registration = db.query(Registration).filter(
        and_(
            Registration.student_id == registration.student_id,
            Registration.event_id == registration.event_id
        )
    ).first()
    
    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already registered for this event"
        )
    
    # Check event capacity
    current_registrations = db.query(Registration).filter(
        and_(
            Registration.event_id == registration.event_id,
            Registration.status == "confirmed"
        )
    ).count()
    
    if current_registrations >= event.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event has reached maximum capacity"
        )
    
    # Create registration
    db_registration = Registration(**registration.dict())
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    return db_registration

@router.get("/registrations", response_model=List[RegistrationWithDetails])
async def get_registrations(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    event_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all registrations with optional filtering"""
    query = db.query(Registration)
    
    if student_id:
        query = query.filter(Registration.student_id == student_id)
    
    if event_id:
        query = query.filter(Registration.event_id == event_id)
    
    if status:
        query = query.filter(Registration.status == status)
    
    registrations = query.order_by(Registration.registration_date.desc()).offset(skip).limit(limit).all()
    return registrations

@router.get("/registrations/{registration_id}", response_model=RegistrationWithDetails)
async def get_registration(registration_id: int, db: Session = Depends(get_db)):
    """Get a specific registration by ID"""
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )
    return registration

@router.put("/registrations/{registration_id}/cancel", response_model=StandardResponse)
async def cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    """Cancel a registration"""
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )
    
    if registration.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration is already cancelled"
        )
    
    # Check if event is in the future (allow cancellation only for future events)
    if registration.event.event_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel registration for past events"
        )
    
    registration.status = "cancelled"
    db.commit()
    
    return StandardResponse(
        message="Registration cancelled successfully"
    )

@router.delete("/registrations/{registration_id}", response_model=StandardResponse)
async def delete_registration(registration_id: int, db: Session = Depends(get_db)):
    """Delete a registration (admin only)"""
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )
    
    # Check if there's associated attendance or feedback
    if registration.student.attendances or registration.student.feedback_entries:
        # Check if attendance/feedback is for this specific event
        has_attendance = any(att.event_id == registration.event_id for att in registration.student.attendances)
        has_feedback = any(fb.event_id == registration.event_id for fb in registration.student.feedback_entries)
        
        if has_attendance or has_feedback:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete registration with associated attendance or feedback"
            )
    
    db.delete(registration)
    db.commit()
    return StandardResponse(message="Registration deleted successfully")

@router.get("/registrations/student/{student_id}/events")
async def get_student_registrations(
    student_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all event registrations for a specific student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    query = db.query(Registration).filter(Registration.student_id == student_id)
    
    if status:
        query = query.filter(Registration.status == status)
    
    registrations = query.order_by(Registration.registration_date.desc()).all()
    
    return {
        "student_id": student_id,
        "student_name": student.name,
        "registrations": registrations,
        "total_registrations": len(registrations)
    }

@router.get("/registrations/event/{event_id}/students")
async def get_event_registrations(
    event_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all student registrations for a specific event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    query = db.query(Registration).filter(Registration.event_id == event_id)
    
    if status:
        query = query.filter(Registration.status == status)
    
    registrations = query.order_by(Registration.registration_date.desc()).all()
    
    return {
        "event_id": event_id,
        "event_title": event.title,
        "event_date": event.event_date,
        "registrations": registrations,
        "total_registrations": len(registrations),
        "available_spots": event.max_capacity - len([r for r in registrations if r.status == "confirmed"])
    }