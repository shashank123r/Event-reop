from database import SessionLocal, init_db
from models import College, Student, Event, Registration, Attendance, Feedback
from datetime import date, timedelta
import random

def create_basic_data():
    """Create minimal sample data for testing"""
    # Initialize database first
    init_db()
    
    db = SessionLocal()
    
    try:
        print("Creating basic sample data...")
        
        # Create 3 colleges
        colleges = [
            College(name="IIT Bangalore", location="Bangalore", contact_email="admin@iitb.ac.in"),
            College(name="NITK Surathkal", location="Surathkal", contact_email="admin@nitk.edu.in"),
            College(name="BMSCE", location="Bangalore", contact_email="admin@bmsce.ac.in")
        ]
        
        for college in colleges:
            db.add(college)
        db.commit()
        
        # Create 10 students
        students = [
            Student(name="Rahul Sharma", email="rahul@iitb.ac.in", college_id=1, year_of_study=3),
            Student(name="Priya Patel", email="priya@iitb.ac.in", college_id=1, year_of_study=2),
            Student(name="Karthik Kumar", email="karthik@nitk.edu.in", college_id=2, year_of_study=4),
            Student(name="Sneha Singh", email="sneha@nitk.edu.in", college_id=2, year_of_study=1),
            Student(name="Vivek Reddy", email="vivek@bmsce.ac.in", college_id=3, year_of_study=2)
        ]
        
        for student in students:
            db.add(student)
        db.commit()
        
        # Create 5 events
        events = [
            Event(title="Python Workshop", description="Learn Python basics", event_type="workshop", 
                  event_date=date.today() + timedelta(days=7), venue="Lab 1", college_id=1, max_capacity=50),
            Event(title="AI Seminar", description="AI trends discussion", event_type="seminar", 
                  event_date=date.today() + timedelta(days=14), venue="Auditorium", college_id=2, max_capacity=100),
            Event(title="Coding Competition", description="Programming contest", event_type="competition", 
                  event_date=date.today() + timedelta(days=21), venue="Computer Lab", college_id=3, max_capacity=30)
        ]
        
        for event in events:
            db.add(event)
        db.commit()
        
        print("✅ Basic sample data created successfully!")
        print(f"Colleges: {len(colleges)}")
        print(f"Students: {len(students)}")
        print(f"Events: {len(events)}")
        print("\n🚀 You can now run: uvicorn main:app --reload")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_basic_data()