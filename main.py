from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse  # Add this import
from database import init_db
import uvicorn

# Import route modules
from routes import events, students, colleges, registrations, attendances, feedback, reports

# Initialize FastAPI app
app = FastAPI(
    title="Campus Event Reporting System",
    description="A comprehensive system for managing campus events, registrations, attendance, and feedback",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API versioning
API_V1_PREFIX = "/api/v1"

app.include_router(colleges.router, prefix=API_V1_PREFIX, tags=["Colleges"])
app.include_router(students.router, prefix=API_V1_PREFIX, tags=["Students"])
app.include_router(events.router, prefix=API_V1_PREFIX, tags=["Events"])
app.include_router(registrations.router, prefix=API_V1_PREFIX, tags=["Registrations"])
app.include_router(attendances.router, prefix=API_V1_PREFIX, tags=["Attendances"])
app.include_router(feedback.router, prefix=API_V1_PREFIX, tags=["Feedback"])
app.include_router(reports.router, prefix=API_V1_PREFIX, tags=["Reports"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Campus Event Reporting System API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Campus Event Reporting System",
        "version": "1.0.0"
    }

# Serve the data entry interface - ADD THIS ROUTE
@app.get("/data-entry")
async def data_entry():
    return FileResponse("templates/index.html")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized successfully")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)