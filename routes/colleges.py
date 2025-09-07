from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import College
from schemas import College as CollegeSchema, CollegeCreate, StandardResponse

router = APIRouter()

@router.post("/colleges", response_model=CollegeSchema, status_code=status.HTTP_201_CREATED)
async def create_college(college: CollegeCreate, db: Session = Depends(get_db)):
    """Create a new college"""
    # Check if college name already exists
    db_college = db.query(College).filter(College.name == college.name).first()
    if db_college:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="College with this name already exists"
        )
    
    db_college = College(**college.dict())
    db.add(db_college)
    db.commit()
    db.refresh(db_college)
    return db_college

@router.get("/colleges", response_model=List[CollegeSchema])
async def get_colleges(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all colleges with optional search and pagination"""
    query = db.query(College)
    
    if search:
        query = query.filter(College.name.contains(search))
    
    colleges = query.offset(skip).limit(limit).all()
    return colleges

@router.get("/colleges/{college_id}", response_model=CollegeSchema)
async def get_college(college_id: int, db: Session = Depends(get_db)):
    """Get a specific college by ID"""
    college = db.query(College).filter(College.id == college_id).first()
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    return college

@router.put("/colleges/{college_id}", response_model=CollegeSchema)
async def update_college(
    college_id: int, 
    college_update: CollegeCreate, 
    db: Session = Depends(get_db)
):
    """Update a college"""
    db_college = db.query(College).filter(College.id == college_id).first()
    if not db_college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Check if new name conflicts with existing college
    if college_update.name != db_college.name:
        existing = db.query(College).filter(College.name == college_update.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="College with this name already exists"
            )
    
    for key, value in college_update.dict(exclude_unset=True).items():
        setattr(db_college, key, value)
    
    db.commit()
    db.refresh(db_college)
    return db_college

@router.delete("/colleges/{college_id}", response_model=StandardResponse)
async def delete_college(college_id: int, db: Session = Depends(get_db)):
    """Delete a college"""
    db_college = db.query(College).filter(College.id == college_id).first()
    if not db_college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Check if college has associated students or events
    if db_college.students or db_college.events:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete college with associated students or events"
        )
    
    db.delete(db_college)
    db.commit()
    return StandardResponse(message="College deleted successfully")