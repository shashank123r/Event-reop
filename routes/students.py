from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Student, College
from schemas import Student as StudentSchema, StudentCreate, StudentWithCollege, StandardResponse

router = APIRouter()

@router.post("/students", response_model=StudentSchema, status_code=status.HTTP_201_CREATED)
async def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student"""
    # Check if college exists
    college = db.query(College).filter(College.id == student.college_id).first()
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Check if email already exists
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if db_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student with this email already exists"
        )
    
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@router.get("/students", response_model=List[StudentWithCollege])
async def get_students(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    college_id: Optional[int] = None,
    year_of_study: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all students with optional filtering"""
    query = db.query(Student)
    
    if search:
        query = query.filter(
            (Student.name.contains(search)) | 
            (Student.email.contains(search))
        )
    
    if college_id:
        query = query.filter(Student.college_id == college_id)
    
    if year_of_study:
        query = query.filter(Student.year_of_study == year_of_study)
    
    students = query.offset(skip).limit(limit).all()
    return students

@router.get("/students/{student_id}", response_model=StudentWithCollege)
async def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get a specific student by ID"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student

@router.put("/students/{student_id}", response_model=StudentSchema)
async def update_student(
    student_id: int,
    student_update: StudentCreate,
    db: Session = Depends(get_db)
):
    """Update a student"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if college exists (if college_id is being updated)
    if student_update.college_id != db_student.college_id:
        college = db.query(College).filter(College.id == student_update.college_id).first()
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )
    
    # Check if new email conflicts with existing student
    if student_update.email != db_student.email:
        existing = db.query(Student).filter(Student.email == student_update.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student with this email already exists"
            )
    
    for key, value in student_update.dict(exclude_unset=True).items():
        setattr(db_student, key, value)
    
    db.commit()
    db.refresh(db_student)
    return db_student

@router.delete("/students/{student_id}", response_model=StandardResponse)
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if student has registrations, attendance, or feedback
    if db_student.registrations or db_student.attendances or db_student.feedback_entries:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete student with existing registrations, attendance, or feedback"
        )
    
    db.delete(db_student)
    db.commit()
    return StandardResponse(message="Student deleted successfully")

@router.get("/students/{student_id}/events")
async def get_student_events(student_id: int, db: Session = Depends(get_db)):
    """Get all events for a specific student (registered, attended)"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    registered_events = [reg.event for reg in student.registrations]
    attended_events = [att.event for att in student.attendances]
    
    return {
        "student_id": student_id,
        "student_name": student.name,
        "registered_events": registered_events,
        "attended_events": attended_events,
        "total_registrations": len(registered_events),
        "total_attendances": len(attended_events)
    }