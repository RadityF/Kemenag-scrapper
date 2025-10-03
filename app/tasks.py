from celery import current_task
from .celery_app import app
from .services.selenium_scraper import KemenagScraper
from .database import get_db_session
from .crud import (
    update_record_started,
    update_record_success,
    update_record_failure,
    create_transaction
)
from .config import settings
import logging

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_kemenag(self, task_id: str, no_porsi: str):
    """
    Celery task untuk melakukan scraping data Kemenag
    """
    db = None
    try:
        logger.info(f"Starting scraping task for no_porsi: {no_porsi}, task_id: {task_id}")
        
        # Update task state dan database record
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Starting scraping process...', 'progress': 0}
        )
        
        # Get database session
        db = get_db_session()
        
        # Update record started
        update_record_started(db, task_id)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Setting up browser...', 'progress': 20}
        )
        
        # Initialize scraper
        scraper = KemenagScraper()
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Scraping data...', 'progress': 40}
        )
        
        # Perform scraping
        success, filename, scraped_data, error_message, attempts_used = scraper.scrape(no_porsi)
        
        if success:
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Saving results...', 'progress': 80}
            )
            
            # Generate screenshot URL
            screenshot_url = f"http://localhost:{settings.api_port}/files/{filename}" if filename else None
            
            # Update database dengan hasil scraping (scrape_records)
            record = update_record_success(
                db=db,
                task_id=task_id,
                scraped_data=scraped_data,
                screenshot_filename=filename,
                screenshot_url=screenshot_url,
                attempts_used=attempts_used
            )
            # Tambahkan ke tabel transaction
            create_transaction(db, scraped_data)
            
            # Final update
            self.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Scraping completed successfully',
                    'progress': 100,
                    'result': {
                        'record_id': str(record.id) if record else None,
                        'no_porsi': no_porsi,
                        'filename': filename,
                        'screenshot_url': screenshot_url,
                        'scraped_data': scraped_data,
                        'attempts_used': attempts_used
                    }
                }
            )
            
            logger.info(f"Scraping task completed successfully for no_porsi: {no_porsi}")
            
            return {
                'status': 'SUCCESS',
                'record_id': str(record.id) if record else None,
                'no_porsi': no_porsi,
                'filename': filename,
                'screenshot_url': screenshot_url,
                'scraped_data': scraped_data,
                'attempts_used': attempts_used
            }
        
        else:
            # Update database with failure
            update_record_failure(
                db=db,
                task_id=task_id,
                error_message=error_message,
                attempts_used=attempts_used
            )
            
            # Update task state
            self.update_state(
                state='FAILURE',
                meta={
                    'status': 'Scraping failed',
                    'error': error_message,
                    'attempts_used': attempts_used
                }
            )
            
            logger.error(f"Scraping task failed for no_porsi: {no_porsi}, error: {error_message}")
            
            # Raise exception to mark task as failed
            raise Exception(error_message)
    
    except Exception as exc:
        logger.error(f"Task exception for no_porsi: {no_porsi}, error: {str(exc)}")
        
        # Update database with failure if not already done
        if db:
            try:
                update_record_failure(
                    db=db,
                    task_id=task_id,
                    error_message=str(exc),
                    attempts_used=0
                )
            except Exception as db_exc:
                logger.error(f"Error updating database on task failure: {str(db_exc)}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Task failed with exception',
                'error': str(exc)
            }
        )
        
        # Retry if retries are available
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task for no_porsi: {no_porsi} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=exc)
        
        # Final failure
        raise exc
    
    finally:
        # Close database session
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error closing database session: {str(e)}")

@app.task
def cleanup_old_results():
    """
    Periodic task untuk membersihkan hasil lama (optional)
    """
    # Implementation untuk cleanup files dan database records lama
    # Bisa dijadwalkan dengan Celery Beat
    pass