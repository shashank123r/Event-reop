from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date
from database import get_db
from models import Attendance, Student, Event, Registration
from schemas import (
    Attendance as AttendanceSchema,
    AttendanceCreate,
    AttendanceWithDetails,
    StandardResponse
)

router = APIRouter()

@router.post("/attendances", response_model=AttendanceSchema, status_code=status.HTTP_201_CREATED)
async def mark_attendance(attendance: AttendanceCreate, db: Session = Depends(get_db)):
    """Mark student attendance for an event"""
    # Check if student exists
    student = db.query(Student).filter(Student.id == attendance.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if event exists
    event = db.query(Event).filter(Event.id == attendance.event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if student is registered for the event
    registration = db.query(Registration).filter(
        and_(
            Registration.student_id == attendance.student_id,
            Registration.event_id == attendance.event_id,
            Registration.status == "confirmed"
        )
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student must be registered for the event to mark attendance"
        )
    
    # Check if attendance is already marked
    existing_attendance = db.query(Attendance).filter(
        and_(
            Attendance.student_id == attendance.student_id,
            Attendance.event_id == attendance.event_id
        )
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already marked for this student"
        )
    
    # Check if event date is today or in the past (can't mark attendance for future events)
    if event.event_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark attendance for future events"
        )
    
    # Create attendance record
    db_attendance = Attendance(**attendance.dict())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@router.get("/attendances", response_model=List[AttendanceWithDetails])
async def get_attendances(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    event_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all attendances with optional filtering"""
    query = db.query(Attendance)
    
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    
    if event_id:
        query = query.filter(Attendance.event_id == event_id)
    
    attendances = query.order_by(Attendance.attended_at.desc()).offset(skip).limit(limit).all()
    return attendances

@router.get("/attendances/{attendance_id}", response_model=AttendanceWithDetails)
async def get_attendance(attendance_id: int, db: Session = Depends(get_db)):
    """Get a specific attendance record by ID"""
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    return attendance

@router.delete("/attendances/{attendance_id}", response_model=StandardResponse)
async def delete_attendance(attendance_id: int, db: Session = Depends(get_db)):
    """Delete an attendance record (admin only)"""
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    db.delete(attendance)
    db.commit()
    return StandardResponse(message="Attendance record deleted successfully")

@router.get("/attendances/student/{student_id}/events")
async def get_student_attendances(student_id: int, db: Session = Depends(get_db)):
    """Get all event attendances for a specific student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    attendances = db.query(Attendance).filter(Attendance.student_id == student_id).order_by(Attendance.attended_at.desc()).all()
    
    return {
        "student_id": student_id,
        "student_name": student.name,
        "attendances": attendances,
        "total_attendances": len(attendances)
    }

@router.get("/attendances/event/{event_id}/students")
async def get_event_attendances(event_id: int, db: Session = Depends(get_db)):
    """Get all student attendances for a specific event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    attendances = db.query(Attendance).filter(Attendance.event_id == event_id).order_by(Attendance.attended_at.desc()).all()
    
    # Get total registrations for comparison
    total_registrations = db.query(Registration).filter(
        and_(
            Registration.event_id == event_id,
            Registration.status == "confirmed"
        )
    ).count()
    
    attendance_percentage = (len(attendances) / total_registrations * 100) if total_registrations > 0 else 0
    
    return {
        "event_id": event_id,
        "event_title": event.title,
        "event_date": event.event_date,
        "attendances": attendances,
        "total_attendances": len(attendances),
        "total_registrations": total_registrations,
        "attendance_percentage": round(attendance_percentage, 2)
    }

@router.post("/attendances/bulk", response_model=StandardResponse)
async def bulk_mark_attendance(
    event_id: int,
    student_ids: List[int],
    db: Session = Depends(get_db)
):
    """Mark attendance for multiple students at once"""
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if event date is valid
    if event.event_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark attendance for future events"
        )
    
    success_count = 0
    errors = []
    
    for student_id in student_ids:
        try:
            # Check if student is registered
            registration = db.query(Registration).filter(
                and_(
                    Registration.student_id == student_id,
                    Registration.event_id == event_id,
                    Registration.status == "confirmed"
                )
            ).first()
            
            if not registration:
                errors.append(f"Student {student_id}: Not registered for this event")
                continue
            
            # Check if attendance already exists
            existing_attendance = db.query(Attendance).filter(
                and_(
                    Attendance.student_id == student_id,
                    Attendance.event_id == event_id
                )
            ).first()
            
            if existing_attendance:
                errors.append(f"Student {student_id}: Attendance already marked")
                continue
            
            # Create attendance record
            attendance = Attendance(student_id=student_id, event_id=event_id)
            db.add(attendance)
            success_count += 1
            
        except Exception as e:
            errors.append(f"Student {student_id}: {str(e)}")
    
    db.commit()
    
    return StandardResponse(
        message=f"Bulk attendance completed. {success_count} students marked present.",
        data={
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors
        }
    )