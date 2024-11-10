# models.py
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./main.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True, unique=True)
    guide = Column(String, index=True)
    name = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    login = Column(String, index=True, unique=True)
    password = Column(String, index=True)
    role = Column(String, index=True, default='admin') # может быть superadmin
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Devises(Base):
    __tablename__ = "devises"
    
    # Генерируем UUID при создании
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    admin_id = Column(Integer, index=True)
    department = Column(String, index=True)
    modify_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DepartmentSettings(Base):
    __tablename__ = "department_settings"

    department_id = Column(String, index=True, primary_key=True)
    max_photo_count = Column(Integer)
    max_divice_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)


class LogConfirm(Base):
    __tablename__ = "log_confirm"

    id = Column(Integer, primary_key=True, index=True)
    guide = Column(String, index=True)
    user_name = Column(String)
    devise_guid = Column(String, index=True)
    department_id = Column(String, index=True)
    inout = Column(String)
    response = Column(String)
    json_data = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)