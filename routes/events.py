from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime
from database import get_db
from models import Event, College, Registration
from schemas import (
    Event as EventSchema, 
    EventCreate, 
    EventUpdate, 
    EventWithCollege, 
    StandardResponse,
    EventStatus,
    EventType
)

router = APIRouter()

@router.post("/events", response_model=EventSchema, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    # Check if college exists
    college = db.query(College).filter(College.id == event.college_id).first()
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Validate event date is not in the past
    if event.event_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event date cannot be in the past"
        )
    
    # Validate start_time < end_time if both provided
    if event.start_time and event.end_time and event.start_time >= event.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )
    
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/events", response_model=List[EventWithCollege])
async def get_events(
    skip: int = 0,
    limit: int = 100,
    college_id: Optional[int] = None,
    event_type: Optional[EventType] = None,
    status: Optional[EventStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all events with optional filtering"""
    query = db.query(Event)
    
    if college_id:
        query = query.filter(Event.college_id == college_id)
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if status:
        query = query.filter(Event.status == status)
    
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    if search:
        query = query.filter(
            (Event.title.contains(search)) |
            (Event.description.contains(search))
        )
    
    events = query.order_by(Event.event_date.desc()).offset(skip).limit(limit).all()
    return events

@router.get("/events/{event_id}", response_model=EventWithCollege)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event

@router.put("/events/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db)
):
    """Update an event"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    update_data = event_update.dict(exclude_unset=True)
    
    # Validate date if being updated
    if 'event_date' in update_data:
        if update_data['event_date'] < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event date cannot be in the past"
            )
    
    # Validate time constraints
    start_time = update_data.get('start_time', db_event.start_time)
    end_time = update_data.get('end_time', db_event.end_time)
    if start_time and end_time and start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )
    
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/events/{event_id}", response_model=StandardResponse)
async def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if event has registrations
    if db_event.registrations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete event with existing registrations"
        )
    
    db.delete(db_event)
    db.commit()
    return StandardResponse(message="Event deleted successfully")

@router.get("/events/{event_id}/availability")
async def check_event_availability(event_id: int, db: Session = Depends(get_db)):
    """Check event availability and registration status"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Count current registrations
    current_registrations = db.query(Registration).filter(
        and_(
            Registration.event_id == event_id,
            Registration.status == "confirmed"
        )
    ).count()
    
    available_spots = event.max_capacity - current_registrations
    is_available = available_spots > 0 and event.status == "active"
    
    return {
        "event_id": event_id,
        "event_title": event.title,
        "event_date": event.event_date,
        "max_capacity": event.max_capacity,
        "current_registrations": current_registrations,
        "available_spots": available_spots,
        "is_available": is_available,
        "event_status": event.status
    }

@router.post("/events/{event_id}/cancel", response_model=StandardResponse)
async def cancel_event(event_id: int, db: Session = Depends(get_db)):
    """Cancel an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active events can be cancelled"
        )
    
    event.status = "cancelled"
    db.commit()
    
    return StandardResponse(
        message=f"Event '{event.title}' has been cancelled successfully"
    )