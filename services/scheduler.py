from apscheduler.schedulers.background import BackgroundScheduler
import logging
from ml.trainer import MLTrainer

def weekly_retrain():
    logging.info("Starting weekly ML model retraining task...")
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            # In a real app, you'd fetch data from DB here and pass it to trainer
            MLTrainer.train_and_save()
            logging.info("Weekly ML model retraining completed successfully.")
    except Exception as e:
        logging.error(f"Error during weekly retraining: {str(e)}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run every Sunday at 2 AM
    scheduler.add_job(func=weekly_retrain, trigger="cron", day_of_week='sun', hour=2, minute=0)
    scheduler.start()
    logging.info("Weekly Retraining Scheduler started.")
