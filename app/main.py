from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import os
import logging
from typing import Optional
import redis

from .database import get_db, test_connection, Base, engine
from .crud import (
    create_scrape_record,
    get_record_by_id,
    get_record_by_task_id,
    get_records_by_no_porsi
)
from .tasks import scrape_kemenag
from .celery_app import app as celery_app
from .config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")

# FastAPI app
app = FastAPI(
    title="Kemenag Scraper API with Celery",
    description="API service untuk scraping data Kemenag dengan background processing menggunakan Celery",
    version="3.0.0"
)

# Test Redis connection on startup
def test_redis():
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        logger.info("Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        return False

# Pydantic models
class EnqueueRequest(BaseModel):
    no_porsi: str

class EnqueueResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    record_id: str

class TaskStatusResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    meta: Optional[dict] = None

class RecordResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None

class HealthResponse(BaseModel):
    success: bool
    message: str
    timestamp: str
    services: dict

@app.post("/enqueue", response_model=EnqueueResponse)
async def enqueue_scraping_task(request: EnqueueRequest, db: Session = Depends(get_db)):
    """
    Enqueue scraping task ke Celery dan buat record di database
    """
    try:
        # Validasi input
        no_porsi = request.no_porsi.strip()
        
        if not no_porsi:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="no_porsi tidak boleh kosong"
            )
        
        if len(no_porsi) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nomor porsi harus minimal 3 karakter"
            )
        
        logger.info(f"Enqueue request received for no_porsi: {no_porsi}")
        
        # Test Redis connection sebelum enqueue
        if not test_redis():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service not available. Make sure Redis server is running."
            )
        
        # Create Celery task
        try:
            task = scrape_kemenag.delay(task_id="temp", no_porsi=no_porsi)
            task_id = task.id
        except Exception as e:
            logger.error(f"Error creating Celery task: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to enqueue task. Error: {str(e)}"
            )
        
        # Create database record dengan task_id yang benar
        try:
            record = create_scrape_record(db=db, task_id=task_id, no_porsi=no_porsi)
        except Exception as e:
            logger.error(f"Error creating database record: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create database record. Error: {str(e)}"
            )
        
        logger.info(f"Task enqueued successfully: {task_id}, record_id: {record.id}")
        
        return EnqueueResponse(
            success=True,
            message="Scraping task berhasil di-enqueue",
            task_id=task_id,
            record_id=str(record.id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enqueuing task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enqueuing task: {str(e)}"
        )

@app.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get task status dari Celery result backend
    """
    try:
        # Test Redis connection
        if not test_redis():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service not available"
            )
        
        # Get task result dari Celery
        task_result = celery_app.AsyncResult(task_id)
        
        # Get task info
        task_info = {
            "task_id": task_id,
            "status": task_result.status,
            "result": None,
            "error": None,
            "meta": None,
            "progress": None
        }
        
        if task_result.status == 'PENDING':
            task_info["meta"] = {"status": "Task is waiting to be processed"}
            
        elif task_result.status == 'PROGRESS':
            task_info["meta"] = task_result.info
            task_info["progress"] = task_result.info.get('progress', 0)
            
        elif task_result.status == 'SUCCESS':
            task_info["result"] = task_result.result
            task_info["progress"] = 100
            
        elif task_result.status == 'FAILURE':
            task_info["error"] = str(task_result.info)
            task_info["meta"] = {"status": "Task failed"}
        
        return TaskStatusResponse(
            success=True,
            **task_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting task status: {str(e)}"
        )

@app.get("/records/{record_id}", response_model=RecordResponse)
async def get_record_by_record_id(record_id: str, db: Session = Depends(get_db)):
    """
    Get permanent record dari database berdasarkan record ID
    """
    try:
        record = get_record_by_id(db, record_id)
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record tidak ditemukan"
            )
        
        return RecordResponse(
            success=True,
            data=record.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting record: {str(e)}"
        )

@app.get("/records/by-task/{task_id}", response_model=RecordResponse)
async def get_record_by_task_id_endpoint(task_id: str, db: Session = Depends(get_db)):
    """
    Get record dari database berdasarkan task ID
    """
    try:
        record = get_record_by_task_id(db, task_id)
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record tidak ditemukan"
            )
        
        return RecordResponse(
            success=True,
            data=record.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting record: {str(e)}"
        )

@app.get("/records/by-porsi/{no_porsi}")
async def get_records_by_no_porsi_endpoint(no_porsi: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get records dari database berdasarkan nomor porsi
    """
    try:
        records = get_records_by_no_porsi(db, no_porsi, limit)
        
        return {
            "success": True,
            "count": len(records),
            "data": [record.to_dict() for record in records]
        }
        
    except Exception as e:
        logger.error(f"Error getting records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting records: {str(e)}"
        )

@app.get("/files/{filename}")
async def serve_file(filename: str):
    """
    Serve screenshot file
    """
    try:
        # Sanitize filename
        filename = os.path.basename(filename)
        filepath = os.path.join(settings.screenshot_folder, filename)
        
        if os.path.exists(filepath):
            return FileResponse(
                path=filepath,
                media_type='image/png',
                filename=filename
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File tidak ditemukan"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error serving file: {str(e)}"
        )

@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests"""
    return {"message": "No favicon available"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    try:
        services = {}
        
        # Test database
        try:
            db_healthy = test_connection()
            services["database"] = "healthy" if db_healthy else "unhealthy"
        except Exception as e:
            services["database"] = f"unhealthy: {str(e)}"
        
        # Test Redis
        try:
            redis_healthy = test_redis()
            services["redis"] = "healthy" if redis_healthy else "unhealthy"
        except Exception as e:
            services["redis"] = f"unhealthy: {str(e)}"
        
        # Test Celery
        try:
            # Check if we can inspect Celery
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            services["celery"] = "healthy" if active_tasks is not None else "unhealthy"
        except Exception as e:
            services["celery"] = f"unhealthy: {str(e)}"
        
        overall_health = all("healthy" in status for status in services.values())
        
        return HealthResponse(
            success=overall_health,
            message="Health check completed",
            timestamp=datetime.utcnow().isoformat(),
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthResponse(
            success=False,
            message=f"Health check failed: {str(e)}",
            timestamp=datetime.utcnow().isoformat(),
            services={"error": str(e)}
        )

@app.get("/")
async def root():
    """
    Root endpoint dengan informasi API
    """
    return {
        "name": "Kemenag Scraper API with Celery",
        "version": "3.0.0",
        "description": "Scalable web scraping service with background processing",
        "architecture": {
            "api": "FastAPI",
            "task_queue": "Celery",
            "message_broker": "Redis",
            "database": "PostgreSQL",
            "scraper": "Selenium + OCR"
        },
        "endpoints": {
            "POST /enqueue": "Enqueue scraping task",
            "GET /status/{task_id}": "Get task status from Redis",
            "GET /records/{record_id}": "Get permanent record from database",
            "GET /records/by-task/{task_id}": "Get record by task ID",
            "GET /records/by-porsi/{no_porsi}": "Get records by nomor porsi",
            "GET /files/{filename}": "Download screenshot file",
            "GET /health": "Health check",
            "GET /docs": "API Documentation (Swagger UI)",
            "GET /redoc": "API Documentation (ReDoc)"
        },
        "workflow": {
            "1": "POST /enqueue creates database record with PENDING status and enqueues Celery task",
            "2": "Celery worker processes task in background and updates database",
            "3": "GET /status/{task_id} checks real-time status from Redis",
            "4": "GET /records/{record_id} gets permanent results from database"
        },
        "redis_url": settings.redis_url,
        "database_url": settings.database_url.replace(settings.database_url.split('@')[0].split('//')[1], "***:***") if '@' in settings.database_url else settings.database_url
    }