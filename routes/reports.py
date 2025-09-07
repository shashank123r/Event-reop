from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import date
from database import get_db
from models import Event, Student, Registration, Attendance, Feedback, College
from schemas import (
    EventRegistrationReport,
    AttendanceReport,
    FeedbackReport,
    StudentParticipationReport,
    EventPopularityReport
)

router = APIRouter()

@router.get("/reports/event-registrations", response_model=List[EventRegistrationReport])
async def get_event_registrations_report(
    event_id: Optional[int] = None,
    college_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get registration report for events"""
    query = db.query(Event)
    
    if event_id:
        query = query.filter(Event.id == event_id)
    
    if college_id:
        query = query.filter(Event.college_id == college_id)
    
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    events = query.all()
    
    reports = []
    for event in events:
        # Count registrations by status
        confirmed_regs = db.query(Registration).filter(
            and_(Registration.event_id == event.id, Registration.status == "confirmed")
        ).count()
        
        cancelled_regs = db.query(Registration).filter(
            and_(Registration.event_id == event.id, Registration.status == "cancelled")
        ).count()
        
        total_regs = confirmed_regs + cancelled_regs
        available_spots = event.max_capacity - confirmed_regs
        
        reports.append(EventRegistrationReport(
            event_id=event.id,
            event_title=event.title,
            event_date=event.event_date,
            total_registrations=total_regs,
            confirmed_registrations=confirmed_regs,
            cancelled_registrations=cancelled_regs,
            available_spots=available_spots
        ))
    
    return reports

@router.get("/reports/attendance-percentage", response_model=List[AttendanceReport])
async def get_attendance_report(
    event_id: Optional[int] = None,
    college_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_attendance_rate: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get attendance percentage report for events"""
    query = db.query(Event)
    
    if event_id:
        query = query.filter(Event.id == event_id)
    
    if college_id:
        query = query.filter(Event.college_id == college_id)
    
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    events = query.all()
    
    reports = []
    for event in events:
        # Count confirmed registrations
        total_registered = db.query(Registration).filter(
            and_(Registration.event_id == event.id, Registration.status == "confirmed")
        ).count()
        
        # Count attendances
        total_attended = db.query(Attendance).filter(Attendance.event_id == event.id).count()
        
        attendance_percentage = (total_attended / total_registered * 100) if total_registered > 0 else 0
        
        # Filter by minimum attendance rate if specified
        if min_attendance_rate and attendance_percentage < min_attendance_rate:
            continue
        
        reports.append(AttendanceReport(
            event_id=event.id,
            event_title=event.title,
            event_date=event.event_date,
            total_registered=total_registered,
            total_attended=total_attended,
            attendance_percentage=round(attendance_percentage, 2)
        ))
    
    return reports

@router.get("/reports/feedback-summary", response_model=List[FeedbackReport])
async def get_feedback_report(
    event_id: Optional[int] = None,
    college_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_rating: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get feedback summary report for events"""
    query = db.query(Event)
    
    if event_id:
        query = query.filter(Event.id == event_id)
    
    if college_id:
        query = query.filter(Event.college_id == college_id)
    
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    events = query.all()
    
    reports = []
    for event in events:
        # Get feedback statistics
        feedback_list = db.query(Feedback).filter(Feedback.event_id == event.id).all()
        
        if not feedback_list:
            continue
        
        ratings = [f.rating for f in feedback_list]
        average_rating = sum(ratings) / len(ratings)
        
        # Filter by minimum rating if specified
        if min_rating and average_rating < min_rating:
            continue
        
        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[str(i)] = ratings.count(i)
        
        reports.append(FeedbackReport(
            event_id=event.id,
            event_title=event.title,
            event_date=event.event_date,
            total_feedback=len(feedback_list),
            average_rating=round(average_rating, 2),
            rating_distribution=rating_distribution
        ))
    
    return reports

@router.get("/reports/student-participation", response_model=List[StudentParticipationReport])
async def get_student_participation_report(
    student_id: Optional[int] = None,
    college_id: Optional[int] = None,
    min_events_attended: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get student participation report"""
    query = db.query(Student)
    
    if student_id:
        query = query.filter(Student.id == student_id)
    
    if college_id:
        query = query.filter(Student.college_id == college_id)
    
    students = query.all()
    
    reports = []
    for student in students:
        # Count registrations and attendances
        total_registrations = len(student.registrations)
        total_attendances = len(student.attendances)
        
        attendance_rate = (total_attendances / total_registrations * 100) if total_registrations > 0 else 0
        
        # Filter by minimum events attended if specified
        if min_events_attended and total_attendances < min_events_attended:
            continue
        
        # Get list of events attended
        events_attended = [att.event.title for att in student.attendances]
        
        reports.append(StudentParticipationReport(
            student_id=student.id,
            student_name=student.name,
            student_email=student.email,
            college_name=student.college.name,
            total_registrations=total_registrations,
            total_attendances=total_attendances,
            attendance_rate=round(attendance_rate, 2),
            events_attended=events_attended
        ))
    
    return reports

@router.get("/reports/event-popularity", response_model=List[EventPopularityReport])
async def get_event_popularity_report(
    limit: int = Query(20, description="Number of top events to return"),
    college_id: Optional[int] = None,
    event_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get event popularity report sorted by registrations"""
    query = db.query(Event)
    
    if college_id:
        query = query.filter(Event.college_id == college_id)
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    events = query.all()
    
    reports = []
    for event in events:
        # Count registrations and attendances
        registrations = db.query(Registration).filter(
            and_(Registration.event_id == event.id, Registration.status == "confirmed")
        ).count()
        
        attendance = db.query(Attendance).filter(Attendance.event_id == event.id).count()
        
        # Get average rating
        avg_rating = db.query(func.avg(Feedback.rating)).filter(Feedback.event_id == event.id).scalar()
        
        # Calculate popularity score (weighted combination of registrations, attendance, and rating)
        popularity_score = (registrations * 0.4) + (attendance * 0.4) + ((avg_rating or 0) * 4 * 0.2)
        
        reports.append(EventPopularityReport(
            event_id=event.id,
            event_title=event.title,
            event_type=event.event_type,
            event_date=event.event_date,
            college_name=event.college.name,
            registrations=registrations,
            attendance=attendance,
            average_rating=round(avg_rating, 2) if avg_rating else None,
            popularity_score=round(popularity_score, 2)
        ))
    
    # Sort by popularity score and limit results
    reports.sort(key=lambda x: x.popularity_score, reverse=True)
    return reports[:limit]

@router.get("/reports/top-active-students")
async def get_top_active_students(
    limit: int = Query(10, description="Number of top students to return"),
    college_id: Optional[int] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get top most active students based on attendance"""
    # Build subquery for filtering events by type if needed
    event_filter = db.query(Event.id)
    if event_type:
        event_filter = event_filter.filter(Event.event_type == event_type)
    event_ids = [e.id for e in event_filter.all()]
    
    # Query students with attendance count
    query = db.query(
        Student.id,
        Student.name,
        Student.email,
        College.name.label('college_name'),
        func.count(Attendance.id).label('attendance_count')
    ).join(College).outerjoin(Attendance)
    
    if college_id:
        query = query.filter(Student.college_id == college_id)
    
    if event_type and event_ids:
        query = query.filter(Attendance.event_id.in_(event_ids))
    
    results = query.group_by(
        Student.id, Student.name, Student.email, College.name
    ).order_by(desc('attendance_count')).limit(limit).all()
    
    active_students = []
    for result in results:
        # Get detailed attendance info for this student
        student_attendances = db.query(Attendance).filter(Attendance.student_id == result.id)
        if event_type and event_ids:
            student_attendances = student_attendances.filter(Attendance.event_id.in_(event_ids))
        
        attendances = student_attendances.all()
        events_attended = [att.event.title for att in attendances]
        
        active_students.append({
            "student_id": result.id,
            "student_name": result.name,
            "student_email": result.email,
            "college_name": result.college_name,
            "attendance_count": result.attendance_count,
            "events_attended": events_attended
        })
    
    return {
        "top_active_students": active_students,
        "total_count": len(active_students),
        "filter_applied": {
            "college_id": college_id,
            "event_type": event_type,
            "limit": limit
        }
    }

@router.get("/reports/dashboard-summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get overall dashboard summary statistics"""
    # Count totals
    total_colleges = db.query(College).count()
    total_students = db.query(Student).count()
    total_events = db.query(Event).count()
    total_registrations = db.query(Registration).filter(Registration.status == "confirmed").count()
    total_attendances = db.query(Attendance).count()
    total_feedback = db.query(Feedback).count()
    
    # Calculate rates
    overall_attendance_rate = (total_attendances / total_registrations * 100) if total_registrations > 0 else 0
    feedback_rate = (total_feedback / total_attendances * 100) if total_attendances > 0 else 0
    
    # Average rating
    avg_rating = db.query(func.avg(Feedback.rating)).scalar()
    
    # Recent activity (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    recent_events = db.query(Event).filter(Event.created_at >= thirty_days_ago).count()
    recent_registrations = db.query(Registration).filter(Registration.registration_date >= thirty_days_ago).count()
    
    # Event type distribution
    event_type_distribution = db.query(
        Event.event_type,
        func.count(Event.id)
    ).group_by(Event.event_type).all()
    
    event_types = {event_type: count for event_type, count in event_type_distribution}
    
    return {
        "overview": {
            "total_colleges": total_colleges,
            "total_students": total_students,
            "total_events": total_events,
            "total_registrations": total_registrations,
            "total_attendances": total_attendances,
            "total_feedback": total_feedback
        },
        "rates": {
            "overall_attendance_rate": round(overall_attendance_rate, 2),
            "feedback_rate": round(feedback_rate, 2),
            "average_rating": round(avg_rating, 2) if avg_rating else 0
        },
        "recent_activity": {
            "recent_events": recent_events,
            "recent_registrations": recent_registrations
        },
        "event_type_distribution": event_types
    }