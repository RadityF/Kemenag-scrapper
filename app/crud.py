from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from .models import ScrapeRecord, Transaction
import logging

logger = logging.getLogger(__name__)

def create_scrape_record(db: Session, task_id: str, no_porsi: str) -> ScrapeRecord:
    """Create new scrape record with PENDING status"""
    record = ScrapeRecord(
        task_id=task_id,
        no_porsi=no_porsi,
        status="PENDING"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Created scrape record for task_id: {task_id}, no_porsi: {no_porsi}")
    return record

def get_record_by_id(db: Session, record_id: str) -> Optional[ScrapeRecord]:
    """Get scrape record by ID"""
    try:
        return db.query(ScrapeRecord).filter(ScrapeRecord.id == record_id).first()
    except Exception as e:
        logger.error(f"Error getting record by ID {record_id}: {str(e)}")
        return None

def get_record_by_task_id(db: Session, task_id: str) -> Optional[ScrapeRecord]:
    """Get scrape record by task ID"""
    try:
        return db.query(ScrapeRecord).filter(ScrapeRecord.task_id == task_id).first()
    except Exception as e:
        logger.error(f"Error getting record by task_id {task_id}: {str(e)}")
        return None

def get_records_by_no_porsi(db: Session, no_porsi: str, limit: int = 10):
    """Get scrape records by no_porsi"""
    try:
        return db.query(ScrapeRecord).filter(
            ScrapeRecord.no_porsi == no_porsi
        ).order_by(ScrapeRecord.created_at.desc()).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting records by no_porsi {no_porsi}: {str(e)}")
        return []

def update_record_started(db: Session, task_id: str) -> Optional[ScrapeRecord]:
    """Update record status to indicate processing started"""
    try:
        record = db.query(ScrapeRecord).filter(ScrapeRecord.task_id == task_id).first()
        if record:
            record.started_at = datetime.utcnow()
            record.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(record)
        return record
    except Exception as e:
        logger.error(f"Error updating record started for task_id {task_id}: {str(e)}")
        db.rollback()
        return None

def update_record_success(
    db: Session, 
    task_id: str, 
    scraped_data: dict,
    screenshot_filename: str = None,
    screenshot_url: str = None,
    attempts_used: int = 0
) -> Optional[ScrapeRecord]:
    """Update record with successful scraping results"""
    try:
        record = db.query(ScrapeRecord).filter(ScrapeRecord.task_id == task_id).first()
        if record:
            record.status = "SUCCESS"
            record.completed_at = datetime.utcnow()
            record.updated_at = datetime.utcnow()
            record.attempts_used = attempts_used
            record.screenshot_filename = screenshot_filename
            record.screenshot_url = screenshot_url
            
            # Update scraped data fields
            record.nama = scraped_data.get('nama')
            record.kabupaten = scraped_data.get('kabupaten')
            record.provinsi = scraped_data.get('provinsi')
            record.kuota_provinsi_kab_kota_khusus = scraped_data.get('kuota_provinsi_kab_kota_khusus')
            record.status_bayar = scraped_data.get('status_bayar')
            record.estimasi_keberangkatan = scraped_data.get('estimasi_keberangkatan')
            record.waktu_permintaan_informasi = scraped_data.get('waktu_permintaan_informasi')
            
            db.commit()
            db.refresh(record)
            logger.info(f"Updated record success for task_id: {task_id}")
        return record
    except Exception as e:
        logger.error(f"Error updating record success for task_id {task_id}: {str(e)}")
        db.rollback()
        return None

def update_record_failure(
    db: Session, 
    task_id: str, 
    error_message: str,
    attempts_used: int = 0
) -> Optional[ScrapeRecord]:
    """Update record with failure status and error message"""
    try:
        record = db.query(ScrapeRecord).filter(ScrapeRecord.task_id == task_id).first()
        if record:
            record.status = "FAILURE"
            record.completed_at = datetime.utcnow()
            record.updated_at = datetime.utcnow()
            record.attempts_used = attempts_used
            record.error_message = error_message
            
            db.commit()
            db.refresh(record)
            logger.info(f"Updated record failure for task_id: {task_id}")
        return record
    except Exception as e:
        logger.error(f"Error updating record failure for task_id {task_id}: {str(e)}")
        db.rollback()
        return None

def create_transaction(db: Session, scraped_data: dict):
    """Insert hasil scraping ke tabel transaction"""
    try:
        transaction = Transaction(
            no_porsi=scraped_data.get('no_porsi'),
            nama=scraped_data.get('nama'),
            kabupaten=scraped_data.get('kabupaten'),
            provinsi=scraped_data.get('provinsi'),
            kuota_provinsi_kab_kota_khusus=scraped_data.get('kuota_provinsi_kab_kota_khusus'),
            status_bayar=scraped_data.get('status_bayar'),
            estimasi_keberangkatan=scraped_data.get('estimasi_keberangkatan'),
            waktu_permintaan_informasi=scraped_data.get('waktu_permintaan_informasi'),
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        db.rollback()
        return None