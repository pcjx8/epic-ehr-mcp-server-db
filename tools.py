"""
Tool Implementations for EHR Database Operations
"""

import json
import uuid
from datetime import datetime, date
from database import get_db_session
from models import Patient, Provider, Appointment, Medication, Allergy, LabResult, VitalSign
from sqlalchemy import or_


async def get_patient_tool(access_token: str, mrn: str) -> dict:
    """Get patient by MRN from database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        return {
            "status": "success",
            "patient": {
                "mrn": patient.mrn,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "dob": patient.dob.isoformat(),
                "gender": patient.gender,
                "email": patient.email,
                "phone": patient.phone,
                "address": {
                    "street": patient.street,
                    "city": patient.city,
                    "state": patient.state,
                    "zip": patient.zip_code
                },
                "insurance": {
                    "provider": patient.insurance_provider,
                    "policy_number": patient.policy_number
                } if patient.insurance_provider else None
            }
        }
    finally:
        db.close()


async def search_patients_tool(access_token: str, search_term: str) -> dict:
    """Search patients by name"""
    db = get_db_session()
    try:
        patients = db.query(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search_term}%"),
                Patient.last_name.ilike(f"%{search_term}%"),
                Patient.mrn.ilike(f"%{search_term}%")
            )
        ).limit(10).all()
        
        results = [{
            "mrn": p.mrn,
            "name": f"{p.first_name} {p.last_name}",
            "dob": p.dob.isoformat(),
            "email": p.email
        } for p in patients]
        
        return {
            "status": "success",
            "count": len(results),
            "patients": results
        }
    finally:
        db.close()


async def create_patient_tool(access_token: str, first_name: str, last_name: str,
                              dob: str, gender: str = None, email: str = None, phone: str = None) -> dict:
    """Create new patient in database"""
    db = get_db_session()
    try:
        # Generate unique MRN
        mrn = f"MRN{uuid.uuid4().hex[:6].upper()}"
        
        # Parse date
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        
        patient = Patient(
            mrn=mrn,
            first_name=first_name,
            last_name=last_name,
            dob=dob_date,
            gender=gender,
            email=email,
            phone=phone
        )
        
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        return {
            "status": "success",
            "message": "Patient created successfully",
            "patient": {
                "mrn": patient.mrn,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "dob": patient.dob.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def get_appointments_tool(access_token: str, mrn: str, status: str = "all") -> dict:
    """Get patient appointments from database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        query = db.query(Appointment).filter(Appointment.patient_id == patient.id)
        
        if status != "all":
            query = query.filter(Appointment.status == status)
        
        appointments = query.order_by(Appointment.date.desc()).all()
        
        results = [{
            "appointment_id": apt.appointment_id,
            "date": apt.date.isoformat(),
            "time": apt.time,
            "type": apt.appointment_type,
            "provider": apt.provider.name,
            "department": apt.department,
            "location": apt.location,
            "status": apt.status,
            "reason": apt.reason
        } for apt in appointments]
        
        return {
            "status": "success",
            "mrn": mrn,
            "appointments": results
        }
    finally:
        db.close()


async def schedule_appointment_tool(access_token: str, mrn: str, provider_npi: str,
                                    date: str, time: str, reason: str = "") -> dict:
    """Schedule new appointment in database"""
    db = get_db_session()
    try:
        # Get patient
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        # Get provider
        provider = db.query(Provider).filter(Provider.npi == provider_npi).first()
        if not provider:
            raise ValueError(f"Provider with NPI {provider_npi} not found")
        
        # Parse date
        apt_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Check for conflicts
        existing = db.query(Appointment).filter(
            Appointment.provider_id == provider.id,
            Appointment.date == apt_date,
            Appointment.time == time,
            Appointment.status == "scheduled"
        ).first()
        
        if existing:
            raise ValueError("Time slot already booked")
        
        # Create appointment
        appointment = Appointment(
            appointment_id=f"APT{uuid.uuid4().hex[:6].upper()}",
            patient_id=patient.id,
            provider_id=provider.id,
            date=apt_date,
            time=time,
            appointment_type="Office Visit",
            department=provider.department,
            location="Main Clinic",
            status="scheduled",
            reason=reason
        )
        
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        return {
            "status": "success",
            "message": "Appointment scheduled successfully",
            "appointment": {
                "appointment_id": appointment.appointment_id,
                "date": appointment.date.isoformat(),
                "time": appointment.time,
                "provider": provider.name,
                "department": appointment.department
            }
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def get_medications_tool(access_token: str, mrn: str) -> dict:
    """Get patient medications from database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        medications = db.query(Medication).filter(
            Medication.patient_id == patient.id,
            Medication.status == "active"
        ).all()
        
        results = [{
            "medication_id": med.medication_id,
            "name": med.name,
            "dosage": med.dosage,
            "frequency": med.frequency,
            "route": med.route,
            "prescribed_date": med.prescribed_date.isoformat(),
            "prescriber": med.prescriber,
            "refills_remaining": med.refills_remaining
        } for med in medications]
        
        return {
            "status": "success",
            "mrn": mrn,
            "medications": results
        }
    finally:
        db.close()


async def prescribe_medication_tool(access_token: str, mrn: str, medication_name: str,
                                    dosage: str, frequency: str, refills: int = 0) -> dict:
    """Prescribe new medication in database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        medication = Medication(
            medication_id=f"MED{uuid.uuid4().hex[:6].upper()}",
            patient_id=patient.id,
            name=medication_name,
            dosage=dosage,
            frequency=frequency,
            route="Oral",
            prescribed_date=date.today(),
            prescriber="Current Provider",
            status="active",
            refills_remaining=refills
        )
        
        db.add(medication)
        db.commit()
        db.refresh(medication)
        
        return {
            "status": "success",
            "message": "Medication prescribed successfully",
            "medication": {
                "medication_id": medication.medication_id,
                "name": medication.name,
                "dosage": medication.dosage,
                "frequency": medication.frequency
            }
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def get_lab_results_tool(access_token: str, mrn: str) -> dict:
    """Get patient lab results from database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        lab_results = db.query(LabResult).filter(
            LabResult.patient_id == patient.id
        ).order_by(LabResult.resulted_date.desc()).all()
        
        results = [{
            "order_id": lab.order_id,
            "test_name": lab.test_name,
            "ordered_date": lab.ordered_date.isoformat(),
            "resulted_date": lab.resulted_date.isoformat() if lab.resulted_date else None,
            "status": lab.status,
            "results": json.loads(lab.results_json) if lab.results_json else []
        } for lab in lab_results]
        
        return {
            "status": "success",
            "mrn": mrn,
            "lab_results": results
        }
    finally:
        db.close()


async def get_vital_signs_tool(access_token: str, mrn: str) -> dict:
    """Get patient vital signs from database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        vitals = db.query(VitalSign).filter(
            VitalSign.patient_id == patient.id
        ).order_by(VitalSign.recorded_date.desc()).limit(10).all()
        
        results = [{
            "recorded_date": v.recorded_date.isoformat(),
            "blood_pressure": f"{v.systolic_bp}/{v.diastolic_bp}" if v.systolic_bp else None,
            "heart_rate": v.heart_rate,
            "temperature": v.temperature,
            "oxygen_saturation": v.oxygen_saturation,
            "weight": v.weight,
            "bmi": v.bmi,
            "recorded_by": v.recorded_by
        } for v in vitals]
        
        return {
            "status": "success",
            "mrn": mrn,
            "vital_signs": results
        }
    finally:
        db.close()


async def record_vital_signs_tool(access_token: str, mrn: str, **kwargs) -> dict:
    """Record new vital signs in database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        vital_sign = VitalSign(
            patient_id=patient.id,
            recorded_date=datetime.now(),
            systolic_bp=kwargs.get("systolic_bp"),
            diastolic_bp=kwargs.get("diastolic_bp"),
            heart_rate=kwargs.get("heart_rate"),
            temperature=kwargs.get("temperature"),
            respiratory_rate=kwargs.get("respiratory_rate"),
            oxygen_saturation=kwargs.get("oxygen_saturation"),
            weight=kwargs.get("weight"),
            height=kwargs.get("height"),
            recorded_by="Current User"
        )
        
        # Calculate BMI if height and weight provided
        if vital_sign.height and vital_sign.weight:
            height_m = vital_sign.height * 0.0254  # inches to meters
            weight_kg = vital_sign.weight * 0.453592  # lbs to kg
            vital_sign.bmi = round(weight_kg / (height_m ** 2), 1)
        
        db.add(vital_sign)
        db.commit()
        
        return {
            "status": "success",
            "message": "Vital signs recorded successfully"
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def get_allergies_tool(access_token: str, mrn: str) -> dict:
    """Get patient allergies from database"""
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.mrn == mrn).first()
        if not patient:
            raise ValueError(f"Patient with MRN {mrn} not found")
        
        allergies = db.query(Allergy).filter(
            Allergy.patient_id == patient.id,
            Allergy.status == "active"
        ).all()
        
        results = [{
            "allergen": allergy.allergen,
            "reaction": allergy.reaction,
            "severity": allergy.severity,
            "onset_date": allergy.onset_date.isoformat() if allergy.onset_date else None
        } for allergy in allergies]
        
        return {
            "status": "success",
            "mrn": mrn,
            "allergies": results
        }
    finally:
        db.close()


# Provider Management Tools

async def search_providers_tool(access_token: str, search_term: str) -> dict:
    """Search providers by name or specialty"""
    db = get_db_session()
    try:
        # Search by name or specialty
        providers = db.query(Provider).filter(
            or_(
                Provider.first_name.ilike(f"%{search_term}%"),
                Provider.last_name.ilike(f"%{search_term}%"),
                Provider.specialty.ilike(f"%{search_term}%")
            )
        ).limit(20).all()
        
        results = [{
            "npi": provider.npi,
            "name": f"Dr. {provider.first_name} {provider.last_name}",
            "specialty": provider.specialty,
            "phone": provider.phone,
            "email": provider.email
        } for provider in providers]
        
        return {
            "status": "success",
            "count": len(results),
            "providers": results
        }
    finally:
        db.close()


async def get_provider_tool(access_token: str, npi: str) -> dict:
    """Get provider details by NPI"""
    db = get_db_session()
    try:
        provider = db.query(Provider).filter(Provider.npi == npi).first()
        
        if not provider:
            raise ValueError(f"Provider with NPI {npi} not found")
        
        return {
            "status": "success",
            "provider": {
                "npi": provider.npi,
                "first_name": provider.first_name,
                "last_name": provider.last_name,
                "full_name": f"Dr. {provider.first_name} {provider.last_name}",
                "specialty": provider.specialty,
                "phone": provider.phone,
                "email": provider.email,
                "license_number": provider.license_number,
                "license_state": provider.license_state
            }
        }
    finally:
        db.close()
