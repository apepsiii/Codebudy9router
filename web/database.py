"""
Kiro Web Dashboard - Database Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    account_type = Column(String, default="login")  # login or register
    status = Column(String, default="pending")  # pending, processing, success, failed
    refresh_token = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    injected_to_9router = Column(Boolean, default=False)
    injected_at = Column(DateTime, nullable=True)
    router_connection_id = Column(String, nullable=True)  # 9router connection ID


class Config(Base):
    __tablename__ = "config"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProcessLog(Base):
    __tablename__ = "process_logs"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, nullable=False)
    log_type = Column(String, nullable=False)  # info, error, success
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./kiro.db"
engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""), connect_args={"check_same_thread": False})


def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)
    print("[+] Database initialized")


def get_session():
    """Get database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


if __name__ == "__main__":
    init_db()
