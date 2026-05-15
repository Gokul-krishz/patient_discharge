from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import patients, conversation, summaries, logs
from app.scheduler import start_scheduler

# Create database tables
Base.metadata.create_all(bind=engine)

# Start background scheduler
scheduler = start_scheduler()

# Create FastAPI app
app = FastAPI(
    title="SMS Outreach and AI Summary API",
    description="API for managing SMS outreach conversations with patients using AI-generated questions and generating AI summaries for care teams",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients.router)
app.include_router(conversation.router)
app.include_router(summaries.router)
app.include_router(logs.router)


@app.get("/")
def root():
    return {
        "message": "SMS Outreach and AI Summary API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
