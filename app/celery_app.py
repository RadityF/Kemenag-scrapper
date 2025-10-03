from celery import Celery
import redis
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Test Redis connection
def test_redis_connection():
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        logger.info(f"Redis connection successful to {REDIS_URL}")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        return False

# Test connection on startup
if not test_redis_connection():
    logger.warning("Redis connection failed during startup. Make sure Redis server is running.")

# Create Celery app
app = Celery(
    'kemenag_scraper',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']
)

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'app.tasks.scrape_kemenag': {'queue': 'scraping'},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minute
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
)

# Optional: Beat schedule for periodic tasks (if needed later)
app.conf.beat_schedule = {}

logger.info("Celery app configured successfully")