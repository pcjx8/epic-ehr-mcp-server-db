"""
Database Models for EHR System
SQLAlchemy ORM models for all healthcare entities
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class OAuthClient(Base):
    """OAuth 2.0 Client Credentials for app-to-app authentication"""
    __tablename__ = 'oauth_clients'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(256), nullable=False)
    app_id = Column(String(100), nullable=False, index=True)
    app_name = Column(String(200), nullable=False)
    
    # Permissions and scopes
    scopes = Column(Text)  # JSON array of allowed scopes
    role = Column(String(20), nullable=False)  # doctor, nurse, patient, admin, system
    
    # Metadata
    description = Column(Text)
    contact_email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    
    # Rate limiting
    rate_limit = Column(Integer, default=1000)  # requests per hour


class Patient(Base):
    """Patient demographics and information"""
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    mrn = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False, index=True)
    dob = Column(Date, nullable=False)
    gender = Column(String(20))
    ssn = Column(String(20))
    email = Column(String(100))
    phone = Column(String(20))
    
    # Address
    street = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    
    # Insurance
    insurance_provider = Column(String(100))
    policy_number = Column(String(50))
    group_number = Column(String(50))
    
    # Emergency Contact
    emergency_contact_name = Column(String(100))
    emergency_contact_relationship = Column(String(50))
    emergency_contact_phone = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")
    vital_signs = relationship("VitalSign", back_populates="patient", cascade="all, delete-orphan")


class Provider(Base):
    """Healthcare provider information"""
    __tablename__ = 'providers'
    
    id = Column(Integer, primary_key=True)
    npi = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100))
    department = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    accepting_new_patients = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="provider")


class Appointment(Base):
    """Patient appointments"""
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True)
    appointment_id = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    provider_id = Column(Integer, ForeignKey('providers.id'), nullable=False)
    
    date = Column(Date, nullable=False, index=True)
    time = Column(String(20), nullable=False)
    duration_minutes = Column(Integer, default=30)
    appointment_type = Column(String(50))
    department = Column(String(100))
    location = Column(String(200))
    status = Column(String(20), default='scheduled', index=True)  # scheduled, completed, cancelled
    reason = Column(Text)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("Provider", back_populates="appointments")


class Medication(Base):
    """Patient medications and prescriptions"""
    __tablename__ = 'medications'
    
    id = Column(Integer, primary_key=True)
    medication_id = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    
    name = Column(String(200), nullable=False)
    dosage = Column(String(50))
    frequency = Column(String(100))
    route = Column(String(50))
    prescribed_date = Column(Date, nullable=False)
    prescriber = Column(String(100))
    status = Column(String(20), default='active', index=True)  # active, discontinued, completed
    refills_remaining = Column(Integer, default=0)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="medications")


class Allergy(Base):
    """Patient allergies"""
    __tablename__ = 'allergies'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    
    allergen = Column(String(200), nullable=False)
    reaction = Column(Text)
    severity = Column(String(20))  # mild, moderate, severe
    onset_date = Column(Date)
    status = Column(String(20), default='active')
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="allergies")


class LabResult(Base):
    """Laboratory test results"""
    __tablename__ = 'lab_results'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    
    test_name = Column(String(200), nullable=False)
    ordered_date = Column(Date, nullable=False)
    collected_date = Column(Date)
    resulted_date = Column(Date, index=True)
    status = Column(String(20), default='pending')  # pending, in_progress, final
    ordered_by = Column(String(100))
    
    # Results stored as JSON-like text
    results_json = Column(Text)  # Will store JSON string of results
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="lab_results")


class VitalSign(Base):
    """Patient vital signs"""
    __tablename__ = 'vital_signs'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    
    recorded_date = Column(DateTime, nullable=False, index=True)
    
    # Vital measurements
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    heart_rate = Column(Integer)
    temperature = Column(Float)
    respiratory_rate = Column(Integer)
    oxygen_saturation = Column(Integer)
    weight = Column(Float)
    height = Column(Float)
    bmi = Column(Float)
    
    recorded_by = Column(String(100))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="vital_signs")
