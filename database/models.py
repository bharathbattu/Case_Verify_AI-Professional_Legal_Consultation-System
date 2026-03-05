"""
Database models for Case-Verify AI User Management System
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# Create Base here to avoid circular imports
Base = declarative_base()

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    organization = Column(String(255))
    role = Column(String(50), default="user")  # user, lawyer, admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    cases = relationship("Case", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

class Case(Base):
    """Case model for storing legal case information"""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Case basic information
    title = Column(String(500))
    facts = Column(Text, nullable=False)
    relief_sought = Column(String(500))
    pin_code = Column(String(10))
    case_type = Column(String(100))
    case_category = Column(String(100))
    
    # Case status and metadata
    status = Column(String(50), default="draft")  # draft, analyzed, filed, closed
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    tags = Column(JSON)  # List of tags for categorization
    
    # Analysis results
    limitation_period = Column(String(100))
    court_suggestion = Column(String(200))
    confidence_score = Column(Float)
    days_remaining = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    analyzed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="cases")
    analyses = relationship("Analysis", back_populates="case", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Case(id={self.id}, title={self.title}, user_id={self.user_id})>"

class Analysis(Base):
    """Analysis model for storing AI analysis results"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    
    # Analysis details
    analysis_type = Column(String(50), default="full")  # full, quick, detailed
    ai_model_used = Column(String(100))
    analysis_version = Column(String(20), default="1.0")
    
    # Core analysis results
    raw_response = Column(JSON)  # Full AI response
    processed_results = Column(JSON)  # Processed and structured results
    
    # Specific analysis components
    case_classification = Column(JSON)
    limitation_analysis = Column(JSON)
    court_recommendation = Column(JSON)
    cost_estimation = Column(JSON)
    timeline_prediction = Column(JSON)
    success_probability = Column(JSON)
    alternative_remedies = Column(JSON)
    legal_reasoning = Column(Text)
    
    # Quality metrics
    confidence_score = Column(Float)
    processing_time = Column(Float)  # seconds
    tokens_used = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    case = relationship("Case", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, case_id={self.case_id}, type={self.analysis_type})>"

# Additional utility models

class UserSession(Base):
    """User session model for tracking active sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Session metadata
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    device_info = Column(JSON)

class AuditLog(Base):
    """Audit log model for tracking user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))  # case, user, analysis
    resource_id = Column(String(50))
    details = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class SystemConfig(Base):
    """System configuration model for app settings"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
