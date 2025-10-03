from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import VARCHAR, UUID
from datetime import datetime
import uuid
from .database import Base

class ScrapeRecord(Base):
    __tablename__ = "scrape_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    task_id = Column(String(255), unique=True, index=True, nullable=False)
    no_porsi = Column(VARCHAR(3000), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, SUCCESS, FAILURE
    
    # Scraped data fields
    nama = Column(VARCHAR(3000), nullable=True)
    kabupaten = Column(VARCHAR(3000), nullable=True)
    provinsi = Column(VARCHAR(3000), nullable=True)
    kuota_provinsi_kab_kota_khusus = Column(VARCHAR(3000), nullable=True)
    status_bayar = Column(VARCHAR(3000), nullable=True)
    estimasi_keberangkatan = Column(VARCHAR(3000), nullable=True)
    waktu_permintaan_informasi = Column(VARCHAR(3000), nullable=True)
    
    # File info
    screenshot_filename = Column(String(500), nullable=True)
    screenshot_url = Column(String(1000), nullable=True)
    
    # Processing info
    attempts_used = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "task_id": self.task_id,
            "no_porsi": self.no_porsi,
            "status": self.status,
            "nama": self.nama,
            "kabupaten": self.kabupaten,
            "provinsi": self.provinsi,
            "kuota_provinsi_kab_kota_khusus": self.kuota_provinsi_kab_kota_khusus,
            "status_bayar": self.status_bayar,
            "estimasi_keberangkatan": self.estimasi_keberangkatan,
            "waktu_permintaan_informasi": self.waktu_permintaan_informasi,
            "screenshot_filename": self.screenshot_filename,
            "screenshot_url": self.screenshot_url,
            "attempts_used": self.attempts_used,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Transaction(Base):
    __tablename__ = "transaction"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    no_porsi = Column(VARCHAR(3000), nullable=False, index=True)
    nama = Column(VARCHAR(3000), nullable=True)
    kabupaten = Column(VARCHAR(3000), nullable=True)
    provinsi = Column(VARCHAR(3000), nullable=True)
    kuota_provinsi_kab_kota_khusus = Column(VARCHAR(3000), nullable=True)
    status_bayar = Column(VARCHAR(3000), nullable=True)
    estimasi_keberangkatan = Column(VARCHAR(3000), nullable=True)
    waktu_permintaan_informasi = Column(VARCHAR(3000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)