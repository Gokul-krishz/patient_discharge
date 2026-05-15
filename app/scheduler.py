from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.conversation_service import ConversationService


def check_conversation_timeouts():
    """
    Scheduled task to check for conversations that have timed out.
    """
    db = SessionLocal()
    try:
        service = ConversationService(db)
        service.check_timeouts()
        print("Timeout check completed")
    except Exception as e:
        print(f"Error checking timeouts: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler for periodic tasks.
    """
    scheduler = BackgroundScheduler()
    
    # Check timeouts every hour
    scheduler.add_job(
        func=check_conversation_timeouts,
        trigger=IntervalTrigger(hours=1),
        id='timeout_check',
        name='Check conversation timeouts',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler
