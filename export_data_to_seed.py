"""
Export current database data to create a comprehensive seed_database.py file
This reads all data from ehr_database.db and generates Python code to recreate it
"""

import json
from database import get_db_session
from models import Patient, Provider, Appointment, Medication, Allergy, VitalSign, LabResult


def export_data():
    """Export all data from current database"""
    print("Exporting data from current database...")
    
    db = get_db_session()
    
    try:
        # Export Providers
        providers = db.query(Provider).all()
        providers_data = []
        for p in providers:
            providers_data.append({
                'npi': p.npi,
                'name': p.name,
                'specialty': p.specialty,
                'department': p.department,
                'phone': p.phone,
                'email': p.email,
                'accepting_new_patients': p.accepting_new_patients
            })
        
        # Export Patients
        patients = db.query(Patient).all()
        patients_data = []
        for p in patients:
            patients_data.append({
                'mrn': p.mrn,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'dob': p.dob.isoformat() if p.dob else None,
                'gender': p.gender,
                'ssn': p.ssn,
                'email': p.email,
                'phone': p.phone,
                'street': p.street,
                'city': p.city,
                'state': p.state,
                'zip_code': p.zip_code,
                'insurance_provider': p.insurance_provider,
                'policy_number': p.policy_number,
                'group_number': p.group_number,
                'emergency_contact_name': p.emergency_contact_name,
                'emergency_contact_relationship': p.emergency_contact_relationship,
                'emergency_contact_phone': p.emergency_contact_phone
            })
        
        # Export Appointments
        appointments = db.query(Appointment).all()
        appointments_data = []
        for a in appointments:
            appointments_data.append({
                'appointment_id': a.appointment_id,
                'patient_mrn': a.patient.mrn,
                'provider_npi': a.provider.npi,
                'date': a.date.isoformat() if a.date else None,
                'time': a.time,
                'duration_minutes': a.duration_minutes,
                'appointment_type': a.appointment_type,
                'department': a.department,
                'location': a.location,
                'status': a.status,
                'reason': a.reason,
                'notes': a.notes
            })
        
        # Export Medications
        medications = db.query(Medication).all()
        medications_data = []
        for m in medications:
            medications_data.append({
                'medication_id': m.medication_id,
                'patient_mrn': m.patient.mrn,
                'name': m.name,
                'dosage': m.dosage,
                'frequency': m.frequency,
                'route': m.route,
                'prescribed_date': m.prescribed_date.isoformat() if m.prescribed_date else None,
                'prescriber': m.prescriber,
                'status': m.status,
                'refills_remaining': m.refills_remaining,
                'notes': m.notes
            })
        
        # Export Allergies
        allergies = db.query(Allergy).all()
        allergies_data = []
        for a in allergies:
            allergies_data.append({
                'patient_mrn': a.patient.mrn,
                'allergen': a.allergen,
                'reaction': a.reaction,
                'severity': a.severity,
                'onset_date': a.onset_date.isoformat() if a.onset_date else None,
                'status': a.status,
                'notes': a.notes
            })
        
        # Export Vital Signs
        vitals = db.query(VitalSign).all()
        vitals_data = []
        for v in vitals:
            vitals_data.append({
                'patient_mrn': v.patient.mrn,
                'recorded_date': v.recorded_date.isoformat() if v.recorded_date else None,
                'systolic_bp': v.systolic_bp,
                'diastolic_bp': v.diastolic_bp,
                'heart_rate': v.heart_rate,
                'temperature': v.temperature,
                'respiratory_rate': v.respiratory_rate,
                'oxygen_saturation': v.oxygen_saturation,
                'weight': v.weight,
                'height': v.height,
                'bmi': v.bmi,
                'recorded_by': v.recorded_by,
                'notes': v.notes
            })
        
        # Export Lab Results
        labs = db.query(LabResult).all()
        labs_data = []
        for l in labs:
            labs_data.append({
                'order_id': l.order_id,
                'patient_mrn': l.patient.mrn,
                'test_name': l.test_name,
                'ordered_date': l.ordered_date.isoformat() if l.ordered_date else None,
                'collected_date': l.collected_date.isoformat() if l.collected_date else None,
                'resulted_date': l.resulted_date.isoformat() if l.resulted_date else None,
                'status': l.status,
                'ordered_by': l.ordered_by,
                'results_json': l.results_json
            })
        
        print(f"\n✅ Exported:")
        print(f"  - {len(providers_data)} providers")
        print(f"  - {len(patients_data)} patients")
        print(f"  - {len(appointments_data)} appointments")
        print(f"  - {len(medications_data)} medications")
        print(f"  - {len(allergies_data)} allergies")
        print(f"  - {len(vitals_data)} vital signs")
        print(f"  - {len(labs_data)} lab results")
        
        return {
            'providers': providers_data,
            'patients': patients_data,
            'appointments': appointments_data,
            'medications': medications_data,
            'allergies': allergies_data,
            'vitals': vitals_data,
            'labs': labs_data
        }
        
    finally:
        db.close()


def generate_seed_file(data):
    """Generate seed_database.py with all the data"""
    
    print("\n📝 Generating seed_database.py...")
    
    # Save data to JSON file first (for backup)
    with open('database_export.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Backup saved to database_export.json")
    
    # Generate the seed file
    seed_content = '''"""
Database Seeding Script with Production Data
Seeds OAuth clients and all production data
"""

import json
from datetime import datetime, date
from auth import register_client
from database import init_database, get_db_session
from models import Patient, Provider, Appointment, Medication, Allergy, VitalSign, LabResult, OAuthClient


# Production data exported from database
PROVIDERS_DATA = ''' + json.dumps(data['providers'], indent=4) + '''

PATIENTS_DATA = ''' + json.dumps(data['patients'], indent=4) + '''

APPOINTMENTS_DATA = ''' + json.dumps(data['appointments'], indent=4) + '''

MEDICATIONS_DATA = ''' + json.dumps(data['medications'], indent=4) + '''

ALLERGIES_DATA = ''' + json.dumps(data['allergies'], indent=4) + '''

VITALS_DATA = ''' + json.dumps(data['vitals'], indent=4) + '''

LABS_DATA = ''' + json.dumps(data['labs'], indent=4) + '''


def seed_oauth_clients():
    """Seed OAuth clients for authentication"""
    print("\\n" + "="*80)
    print("SEEDING OAUTH CLIENTS")
    print("="*80)
    
    clients_to_create = [
        {
            "app_id": "copilot-studio",
            "app_name": "Microsoft Copilot Studio",
            "role": "doctor",
            "scopes": ["read:patients", "write:patients", "read:appointments", "write:appointments", 
                      "read:medications", "write:medications", "read:labs", "read:vitals", "write:vitals", "read:allergies"],
            "description": "Microsoft Copilot Studio AI agent for healthcare",
            "contact_email": "admin@hospital.org"
        },
        {
            "app_id": "hospital-ehr-app",
            "app_name": "Hospital EHR Application",
            "role": "doctor",
            "scopes": ["read:patients", "write:patients", "read:appointments", "write:appointments", 
                      "read:medications", "write:medications", "read:labs", "read:vitals", "write:vitals"],
            "description": "Main hospital EHR system with full access",
            "contact_email": "admin@hospital.org"
        },
        {
            "app_id": "patient-portal",
            "app_name": "Patient Portal Web App",
            "role": "patient",
            "scopes": ["read:own_records", "read:appointments", "write:appointments"],
            "description": "Patient-facing portal for viewing records and scheduling",
            "contact_email": "support@patientportal.com"
        },
        {
            "app_id": "lab-integration",
            "app_name": "Laboratory Integration System",
            "role": "system",
            "scopes": ["read:patients", "read:labs", "write:labs"],
            "description": "Integration with external laboratory systems",
            "contact_email": "integration@labsystem.com"
        },
        {
            "app_id": "pharmacy-system",
            "app_name": "Pharmacy Management System",
            "role": "system",
            "scopes": ["read:patients", "read:medications", "write:medications"],
            "description": "Integration with pharmacy for prescription management",
            "contact_email": "tech@pharmacy.com"
        },
        {
            "app_id": "nurse-station",
            "app_name": "Nurse Station Application",
            "role": "nurse",
            "scopes": ["read:patients", "read:appointments", "read:medications", 
                      "read:vitals", "write:vitals", "read:allergies"],
            "description": "Nurse station app for patient care",
            "contact_email": "nursing@hospital.org"
        }
    ]
    
    created_clients = []
    
    for client_data in clients_to_create:
        print(f"\\n📱 Creating client: {client_data['app_name']}")
        result = register_client(**client_data)
        
        if result["status"] == "success":
            print(f"   ✅ Success!")
            print(f"   Client ID: {result['client_id']}")
            
            created_clients.append({
                "app_id": result['app_id'],
                "app_name": result['app_name'],
                "client_id": result['client_id'],
                "client_secret": result['client_secret'],
                "role": result['role'],
                "scopes": result['scopes']
            })
        else:
            print(f"   ❌ Error: {result['message']}")
    
    # Save credentials
    with open("oauth_clients_credentials.json", "w") as f:
        json.dump(created_clients, f, indent=2)
    
    print(f"\\n✅ Created {len(created_clients)} OAuth clients")
    print("📄 Credentials saved to: oauth_clients_credentials.json")
    
    return created_clients


def seed_providers(db):
    """Seed providers"""
    print("\\n" + "="*80)
    print("SEEDING PROVIDERS")
    print("="*80)
    
    for p_data in PROVIDERS_DATA:
        provider = Provider(**p_data)
        db.add(provider)
    
    db.commit()
    print(f"✅ Seeded {len(PROVIDERS_DATA)} providers")


def seed_patients(db):
    """Seed patients"""
    print("\\n" + "="*80)
    print("SEEDING PATIENTS")
    print("="*80)
    
    for p_data in PATIENTS_DATA:
        # Convert date string to date object
        if p_data.get('dob'):
            p_data['dob'] = datetime.fromisoformat(p_data['dob']).date()
        
        patient = Patient(**p_data)
        db.add(patient)
    
    db.commit()
    print(f"✅ Seeded {len(PATIENTS_DATA)} patients")


def seed_appointments(db):
    """Seed appointments"""
    print("\\n" + "="*80)
    print("SEEDING APPOINTMENTS")
    print("="*80)
    
    for a_data in APPOINTMENTS_DATA:
        # Get patient and provider IDs
        patient = db.query(Patient).filter(Patient.mrn == a_data['patient_mrn']).first()
        provider = db.query(Provider).filter(Provider.npi == a_data['provider_npi']).first()
        
        if patient and provider:
            # Convert date string
            if a_data.get('date'):
                a_data['date'] = datetime.fromisoformat(a_data['date']).date()
            
            appointment = Appointment(
                appointment_id=a_data['appointment_id'],
                patient_id=patient.id,
                provider_id=provider.id,
                date=a_data['date'],
                time=a_data['time'],
                duration_minutes=a_data['duration_minutes'],
                appointment_type=a_data['appointment_type'],
                department=a_data['department'],
                location=a_data['location'],
                status=a_data['status'],
                reason=a_data['reason'],
                notes=a_data['notes']
            )
            db.add(appointment)
    
    db.commit()
    print(f"✅ Seeded {len(APPOINTMENTS_DATA)} appointments")


def seed_medications(db):
    """Seed medications"""
    print("\\n" + "="*80)
    print("SEEDING MEDICATIONS")
    print("="*80)
    
    for m_data in MEDICATIONS_DATA:
        patient = db.query(Patient).filter(Patient.mrn == m_data['patient_mrn']).first()
        
        if patient:
            if m_data.get('prescribed_date'):
                m_data['prescribed_date'] = datetime.fromisoformat(m_data['prescribed_date']).date()
            
            medication = Medication(
                medication_id=m_data['medication_id'],
                patient_id=patient.id,
                name=m_data['name'],
                dosage=m_data['dosage'],
                frequency=m_data['frequency'],
                route=m_data['route'],
                prescribed_date=m_data['prescribed_date'],
                prescriber=m_data['prescriber'],
                status=m_data['status'],
                refills_remaining=m_data['refills_remaining'],
                notes=m_data['notes']
            )
            db.add(medication)
    
    db.commit()
    print(f"✅ Seeded {len(MEDICATIONS_DATA)} medications")


def seed_allergies(db):
    """Seed allergies"""
    print("\\n" + "="*80)
    print("SEEDING ALLERGIES")
    print("="*80)
    
    for a_data in ALLERGIES_DATA:
        patient = db.query(Patient).filter(Patient.mrn == a_data['patient_mrn']).first()
        
        if patient:
            if a_data.get('onset_date'):
                a_data['onset_date'] = datetime.fromisoformat(a_data['onset_date']).date()
            
            allergy = Allergy(
                patient_id=patient.id,
                allergen=a_data['allergen'],
                reaction=a_data['reaction'],
                severity=a_data['severity'],
                onset_date=a_data.get('onset_date'),
                status=a_data['status'],
                notes=a_data['notes']
            )
            db.add(allergy)
    
    db.commit()
    print(f"✅ Seeded {len(ALLERGIES_DATA)} allergies")


def seed_vitals(db):
    """Seed vital signs"""
    print("\\n" + "="*80)
    print("SEEDING VITAL SIGNS")
    print("="*80)
    
    for v_data in VITALS_DATA:
        patient = db.query(Patient).filter(Patient.mrn == v_data['patient_mrn']).first()
        
        if patient:
            if v_data.get('recorded_date'):
                v_data['recorded_date'] = datetime.fromisoformat(v_data['recorded_date'])
            
            vital = VitalSign(
                patient_id=patient.id,
                recorded_date=v_data['recorded_date'],
                systolic_bp=v_data['systolic_bp'],
                diastolic_bp=v_data['diastolic_bp'],
                heart_rate=v_data['heart_rate'],
                temperature=v_data['temperature'],
                respiratory_rate=v_data['respiratory_rate'],
                oxygen_saturation=v_data['oxygen_saturation'],
                weight=v_data['weight'],
                height=v_data['height'],
                bmi=v_data['bmi'],
                recorded_by=v_data['recorded_by'],
                notes=v_data['notes']
            )
            db.add(vital)
    
    db.commit()
    print(f"✅ Seeded {len(VITALS_DATA)} vital signs")


def seed_labs(db):
    """Seed lab results"""
    print("\\n" + "="*80)
    print("SEEDING LAB RESULTS")
    print("="*80)
    
    for l_data in LABS_DATA:
        patient = db.query(Patient).filter(Patient.mrn == l_data['patient_mrn']).first()
        
        if patient:
            if l_data.get('ordered_date'):
                l_data['ordered_date'] = datetime.fromisoformat(l_data['ordered_date']).date()
            if l_data.get('collected_date'):
                l_data['collected_date'] = datetime.fromisoformat(l_data['collected_date']).date()
            if l_data.get('resulted_date'):
                l_data['resulted_date'] = datetime.fromisoformat(l_data['resulted_date']).date()
            
            lab = LabResult(
                order_id=l_data['order_id'],
                patient_id=patient.id,
                test_name=l_data['test_name'],
                ordered_date=l_data['ordered_date'],
                collected_date=l_data.get('collected_date'),
                resulted_date=l_data.get('resulted_date'),
                status=l_data['status'],
                ordered_by=l_data['ordered_by'],
                results_json=l_data['results_json']
            )
            db.add(lab)
    
    db.commit()
    print(f"✅ Seeded {len(LABS_DATA)} lab results")


def main():
    """Main seeding function"""
    print("\\n" + "="*80)
    print("EPIC EHR MCP SERVER - PRODUCTION DATABASE SEEDING")
    print("="*80)
    print("\\nThis will seed the database with:")
    print(f"  - {len(PROVIDERS_DATA)} providers")
    print(f"  - {len(PATIENTS_DATA)} patients")
    print(f"  - {len(APPOINTMENTS_DATA)} appointments")
    print(f"  - {len(MEDICATIONS_DATA)} medications")
    print(f"  - {len(ALLERGIES_DATA)} allergies")
    print(f"  - {len(VITALS_DATA)} vital signs")
    print(f"  - {len(LABS_DATA)} lab results")
    print("  - 6 OAuth clients")
    print("\\n" + "="*80 + "\\n")
    
    # Initialize database
    print("Initializing database...")
    init_database()
    print("✅ Database initialized")
    
    # Seed OAuth clients
    oauth_clients = seed_oauth_clients()
    
    # Seed all data
    db = get_db_session()
    try:
        seed_providers(db)
        seed_patients(db)
        seed_appointments(db)
        seed_medications(db)
        seed_allergies(db)
        seed_vitals(db)
        seed_labs(db)
    finally:
        db.close()
    
    # Final summary
    print("\\n" + "="*80)
    print("✅ DATABASE SEEDING COMPLETE!")
    print("="*80)
    print(f"\\n📊 Total Records Seeded:")
    print(f"  - OAuth Clients: {len(oauth_clients)}")
    print(f"  - Providers: {len(PROVIDERS_DATA)}")
    print(f"  - Patients: {len(PATIENTS_DATA)}")
    print(f"  - Appointments: {len(APPOINTMENTS_DATA)}")
    print(f"  - Medications: {len(MEDICATIONS_DATA)}")
    print(f"  - Allergies: {len(ALLERGIES_DATA)}")
    print(f"  - Vital Signs: {len(VITALS_DATA)}")
    print(f"  - Lab Results: {len(LABS_DATA)}")
    print("\\n📄 OAuth credentials saved to: oauth_clients_credentials.json")
    print("⚠️  IMPORTANT: Backup this file securely!")
    print("\\n" + "="*80 + "\\n")


if __name__ == "__main__":
    main()
'''
    
    # Write the seed file
    with open('seed_database.py', 'w', encoding='utf-8') as f:
        f.write(seed_content)
    
    print("✅ Generated seed_database.py")
    print(f"   File size: {len(seed_content) / 1024:.1f} KB")


def main():
    print("\n" + "="*80)
    print("EXPORT DATABASE TO SEED FILE")
    print("="*80)
    print("\nThis will:")
    print("  1. Export all data from ehr_database.db")
    print("  2. Generate seed_database.py with embedded data")
    print("  3. Create database_export.json as backup")
    print("\n" + "="*80 + "\n")
    
    # Export data
    data = export_data()
    
    # Generate seed file
    generate_seed_file(data)
    
    print("\n" + "="*80)
    print("✅ EXPORT COMPLETE!")
    print("="*80)
    print("\nGenerated files:")
    print("  - seed_database.py (ready for deployment)")
    print("  - database_export.json (backup)")
    print("\nYou can now:")
    print("  1. Commit seed_database.py to git")
    print("  2. Deploy to droplet")
    print("  3. Run: python seed_database.py")
    print("  4. All your data will be recreated!")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
