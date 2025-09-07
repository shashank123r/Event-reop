from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from database import get_db
from models import Feedback, Student, Event, Attendance
from schemas import (
    Feedback as FeedbackSchema,
    FeedbackCreate,
    FeedbackWithDetails,
    StandardResponse
)

router = APIRouter()

@router.post("/feedback", response_model=FeedbackSchema, status_code=status.HTTP_201_CREATED)
async def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Submit feedback for an event"""
    # Check if student exists
    student = db.query(Student).filter(Student.id == feedback.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if event exists
    event = db.query(Event).filter(Event.id == feedback.event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if student attended the event
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.student_id == feedback.student_id,
            Attendance.event_id == feedback.event_id
        )
    ).first()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students who attended the event can submit feedback"
        )
    
    # Check if feedback already exists
    existing_feedback = db.query(Feedback).filter(
        and_(
            Feedback.student_id == feedback.student_id,
            Feedback.event_id == feedback.event_id
        )
    ).first()
    
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback already submitted for this event"
        )
    
    # Create feedback record
    db_feedback = Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@router.get("/feedback", response_model=List[FeedbackWithDetails])
async def get_feedback(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    event_id: Optional[int] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all feedback with optional filtering"""
    query = db.query(Feedback)
    
    if student_id:
        query = query.filter(Feedback.student_id == student_id)
    
    if event_id:
        query = query.filter(Feedback.event_id == event_id)
    
    if min_rating:
        query = query.filter(Feedback.rating >= min_rating)
    
    if max_rating:
        query = query.filter(Feedback.rating <= max_rating)
    
    feedback_list = query.order_by(Feedback.submitted_at.desc()).offset(skip).limit(limit).all()
    return feedback_list

@router.get("/feedback/{feedback_id}", response_model=FeedbackWithDetails)
async def get_feedback_by_id(feedback_id: int, db: Session = Depends(get_db)):
    """Get a specific feedback record by ID"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback record not found"
        )
    return feedback

@router.put("/feedback/{feedback_id}", response_model=FeedbackSchema)
async def update_feedback(
    feedback_id: int,
    feedback_update: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """Update existing feedback (within 24 hours of submission)"""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not db_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback record not found"
        )
    
    # Optional: Add time restriction for editing feedback
    # from datetime import datetime, timedelta
    # if datetime.now() - db_feedback.submitted_at > timedelta(hours=24):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Feedback can only be edited within 24 hours of submission"
    #     )
    
    # Update feedback
    for key, value in feedback_update.dict(exclude_unset=True).items():
        if key not in ['student_id', 'event_id']:  # Don't allow changing student or event
            setattr(db_feedback, key, value)
    
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@router.delete("/feedback/{feedback_id}", response_model=StandardResponse)
async def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """Delete a feedback record"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback record not found"
        )
    
    db.delete(feedback)
    db.commit()
    return StandardResponse(message="Feedback deleted successfully")

@router.get("/feedback/student/{student_id}/events")
async def get_student_feedback(student_id: int, db: Session = Depends(get_db)):
    """Get all feedback submitted by a specific student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    feedback_list = db.query(Feedback).filter(Feedback.student_id == student_id).order_by(Feedback.submitted_at.desc()).all()
    
    return {
        "student_id": student_id,
        "student_name": student.name,
        "feedback_list": feedback_list,
        "total_feedback": len(feedback_list)
    }

@router.get("/feedback/event/{event_id}/summary")
async def get_event_feedback_summary(event_id: int, db: Session = Depends(get_db)):
    """Get feedback summary for a specific event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get all feedback for the event
    feedback_list = db.query(Feedback).filter(Feedback.event_id == event_id).all()
    
    if not feedback_list:
        return {
            "event_id": event_id,
            "event_title": event.title,
            "total_feedback": 0,
            "average_rating": 0,
            "rating_distribution": {},
            "feedback_list": []
        }
    
    # Calculate statistics
    ratings = [f.rating for f in feedback_list]
    average_rating = sum(ratings) / len(ratings)
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[str(i)] = ratings.count(i)
    
    return {
        "event_id": event_id,
        "event_title": event.title,
        "event_date": event.event_date,
        "total_feedback": len(feedback_list),
        "average_rating": round(average_rating, 2),
        "rating_distribution": rating_distribution,
        "feedback_list": feedback_list
    }

@router.get("/feedback/statistics/overall")
async def get_overall_feedback_statistics(db: Session = Depends(get_db)):
    """Get overall feedback statistics across all events"""
    # Get total feedback count
    total_feedback = db.query(Feedback).count()
    
    if total_feedback == 0:
        return {
            "total_feedback": 0,
            "average_rating": 0,
            "rating_distribution": {},
            "events_with_feedback": 0
        }
    
    # Get average rating across all feedback
    average_rating = db.query(func.avg(Feedback.rating)).scalar()
    
    # Get rating distribution
    rating_counts = db.query(
        Feedback.rating,
        func.count(Feedback.rating)
    ).group_by(Feedback.rating).all()
    
    rating_distribution = {str(i): 0 for i in range(1, 6)}
    for rating, count in rating_counts:
        rating_distribution[str(rating)] = count
    
    # Get number of events with feedback
    events_with_feedback = db.query(Feedback.event_id).distinct().count()
    
    return {
        "total_feedback": total_feedback,
        "average_rating": round(average_rating, 2) if average_rating else 0,
        "rating_distribution": rating_distribution,
        "events_with_feedback": events_with_feedback
    }