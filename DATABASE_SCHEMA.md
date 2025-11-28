# 📊 Database Schema

## Overview

The EHR database uses SQLAlchemy ORM with support for SQLite (development) and PostgreSQL (production).

## Entity Relationship Diagram

```
┌─────────────────┐
│  oauth_clients  │  (OAuth Authentication - Independent)
└─────────────────┘

┌─────────────┐                    ┌─────────────┐
│  providers  │◄───────────────────│appointments │
│             │  1:N               │             │
│ PK: id      │                    │ PK: id      │
│ UK: npi     │                    │ UK: appt_id │
└─────────────┘                    │ FK: patient │
                                   │ FK: provider│
                                   └──────┬──────┘
                                          │
                                          │ N:1
                                          │
┌─────────────┐                    ┌─────▼───────┐
│ medications │◄───────────────────┤  patients   │
│             │  N:1               │             │
│ PK: id      │                    │ PK: id      │
│ UK: med_id  │                    │ UK: mrn     │
│ FK: patient │                    └─────┬───────┘
└─────────────┘                          │
                                         │ 1:N
┌─────────────┐                          │
│  allergies  │◄─────────────────────────┤
│             │  N:1                     │
│ PK: id      │                          │
│ FK: patient │                          │
└─────────────┘                          │
                                         │
┌─────────────┐                          │
│ vital_signs │◄─────────────────────────┤
│             │  N:1                     │
│ PK: id      │                          │
│ FK: patient │                          │
└─────────────┘                          │
                                         │
┌─────────────┐                          │
│ lab_results │◄─────────────────────────┘
│             │  N:1
│ PK: id      │
│ UK: order_id│
│ FK: patient │
└─────────────┘

Legend:
  PK = Primary Key
  FK = Foreign Key
  UK = Unique Key
  1:N = One-to-Many relationship
  N:1 = Many-to-One relationship
```

## Relationship Details

### Patient-Centric Relationships

**patients (1) → appointments (N)**
- One patient can have many appointments
- Foreign Key: `appointments.patient_id` → `patients.id`
- Cascade: Delete patient → Delete all appointments
- Back-reference: `patient.appointments` (list)

**patients (1) → medications (N)**
- One patient can have many medications
- Foreign Key: `medications.patient_id` → `patients.id`
- Cascade: Delete patient → Delete all medications
- Back-reference: `patient.medications` (list)

**patients (1) → allergies (N)**
- One patient can have many allergies
- Foreign Key: `allergies.patient_id` → `patients.id`
- Cascade: Delete patient → Delete all allergies
- Back-reference: `patient.allergies` (list)

**patients (1) → vital_signs (N)**
- One patient can have many vital sign records
- Foreign Key: `vital_signs.patient_id` → `patients.id`
- Cascade: Delete patient → Delete all vital signs
- Back-reference: `patient.vital_signs` (list)

**patients (1) → lab_results (N)**
- One patient can have many lab results
- Foreign Key: `lab_results.patient_id` → `patients.id`
- Cascade: Delete patient → Delete all lab results
- Back-reference: `patient.lab_results` (list)

### Provider Relationships

**providers (1) → appointments (N)**
- One provider can have many appointments
- Foreign Key: `appointments.provider_id` → `providers.id`
- Cascade: None (preserve appointments if provider deleted)
- Back-reference: `provider.appointments` (list)

### Appointment Relationships

**appointments (N) → patients (1)**
- Many appointments belong to one patient
- Foreign Key: `appointments.patient_id` → `patients.id`
- Required: NOT NULL constraint
- Back-reference: `appointment.patient` (object)

**appointments (N) → providers (1)**
- Many appointments belong to one provider
- Foreign Key: `appointments.provider_id` → `providers.id`
- Required: NOT NULL constraint
- Back-reference: `appointment.provider` (object)

### Independent Tables

**oauth_clients**
- No foreign key relationships
- Standalone authentication table
- Used for OAuth 2.0 client credentials flow

## Tables

### 1. oauth_clients

OAuth 2.0 client credentials for app-to-app authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| client_id | VARCHAR(100) | UNIQUE, NOT NULL, INDEXED | Unique client identifier |
| client_secret_hash | VARCHAR(256) | NOT NULL | SHA-256 hashed secret |
| app_id | VARCHAR(100) | NOT NULL, INDEXED | Application identifier |
| app_name | VARCHAR(200) | NOT NULL | Human-readable app name |
| scopes | TEXT | | JSON array of allowed scopes |
| role | VARCHAR(20) | NOT NULL | doctor, nurse, patient, admin, system |
| description | TEXT | | Optional description |
| contact_email | VARCHAR(100) | | Contact email |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |
| is_active | BOOLEAN | DEFAULT TRUE | Enable/disable client |
| last_used | DATETIME | | Last authentication timestamp |
| rate_limit | INTEGER | DEFAULT 1000 | Requests per hour |

**Indexes:**
- `client_id` (UNIQUE)
- `app_id`

**Example:**
```sql
INSERT INTO oauth_clients (client_id, client_secret_hash, app_id, app_name, role, scopes)
VALUES ('client_abc123', 'hash...', 'copilot-studio', 'Microsoft Copilot Studio', 'doctor', '["read:patients"]');
```

---

### 2. patients

Patient demographics and contact information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| mrn | VARCHAR(20) | UNIQUE, NOT NULL, INDEXED | Medical Record Number |
| first_name | VARCHAR(50) | NOT NULL | Patient first name |
| last_name | VARCHAR(50) | NOT NULL, INDEXED | Patient last name |
| dob | DATE | NOT NULL | Date of birth |
| gender | VARCHAR(20) | | Gender |
| ssn | VARCHAR(20) | | Social Security Number |
| email | VARCHAR(100) | | Email address |
| phone | VARCHAR(20) | | Phone number |
| street | VARCHAR(200) | | Street address |
| city | VARCHAR(100) | | City |
| state | VARCHAR(50) | | State |
| zip_code | VARCHAR(20) | | ZIP code |
| insurance_provider | VARCHAR(100) | | Insurance company |
| policy_number | VARCHAR(50) | | Policy number |
| group_number | VARCHAR(50) | | Group number |
| emergency_contact_name | VARCHAR(100) | | Emergency contact name |
| emergency_contact_relationship | VARCHAR(50) | | Relationship |
| emergency_contact_phone | VARCHAR(20) | | Emergency phone |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |
| updated_at | DATETIME | DEFAULT NOW | Last update timestamp |

**Indexes:**
- `mrn` (UNIQUE)
- `last_name`

**Relationships:**
- One-to-many with appointments
- One-to-many with medications
- One-to-many with allergies
- One-to-many with vital_signs
- One-to-many with lab_results

---

### 3. providers

Healthcare providers (doctors, nurses, specialists).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| npi | VARCHAR(20) | UNIQUE, NOT NULL, INDEXED | National Provider Identifier |
| name | VARCHAR(100) | NOT NULL | Provider name |
| specialty | VARCHAR(100) | | Medical specialty |
| department | VARCHAR(100) | | Department |
| phone | VARCHAR(20) | | Phone number |
| email | VARCHAR(100) | | Email address |
| accepting_new_patients | BOOLEAN | DEFAULT TRUE | Accepting new patients |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |

**Indexes:**
- `npi` (UNIQUE)

**Relationships:**
- One-to-many with appointments

---

### 4. appointments

Patient appointments with providers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| appointment_id | VARCHAR(20) | UNIQUE, NOT NULL, INDEXED | Appointment identifier |
| patient_id | INTEGER | FOREIGN KEY, NOT NULL | References patients(id) |
| provider_id | INTEGER | FOREIGN KEY, NOT NULL | References providers(id) |
| date | DATE | NOT NULL, INDEXED | Appointment date |
| time | VARCHAR(20) | NOT NULL | Appointment time |
| duration_minutes | INTEGER | DEFAULT 30 | Duration in minutes |
| appointment_type | VARCHAR(50) | | Type of appointment |
| department | VARCHAR(100) | | Department |
| location | VARCHAR(200) | | Location |
| status | VARCHAR(20) | DEFAULT 'scheduled', INDEXED | scheduled, completed, cancelled |
| reason | TEXT | | Reason for visit |
| notes | TEXT | | Appointment notes |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |
| updated_at | DATETIME | DEFAULT NOW | Last update timestamp |

**Indexes:**
- `appointment_id` (UNIQUE)
- `date`
- `status`

**Foreign Keys:**
- `patient_id` → patients(id)
- `provider_id` → providers(id)

---

### 5. medications

Patient medications and prescriptions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| medication_id | VARCHAR(20) | UNIQUE, NOT NULL, INDEXED | Medication identifier |
| patient_id | INTEGER | FOREIGN KEY, NOT NULL | References patients(id) |
| name | VARCHAR(200) | NOT NULL | Medication name |
| dosage | VARCHAR(50) | | Dosage |
| frequency | VARCHAR(100) | | Frequency |
| route | VARCHAR(50) | | Route (Oral, IV, etc.) |
| prescribed_date | DATE | NOT NULL | Prescription date |
| prescriber | VARCHAR(100) | | Prescribing provider |
| status | VARCHAR(20) | DEFAULT 'active', INDEXED | active, discontinued, completed |
| refills_remaining | INTEGER | DEFAULT 0 | Refills remaining |
| notes | TEXT | | Medication notes |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |
| updated_at | DATETIME | DEFAULT NOW | Last update timestamp |

**Indexes:**
- `medication_id` (UNIQUE)
- `status`

**Foreign Keys:**
- `patient_id` → patients(id)

---

### 6. allergies

Patient allergies.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| patient_id | INTEGER | FOREIGN KEY, NOT NULL | References patients(id) |
| allergen | VARCHAR(200) | NOT NULL | Allergen name |
| reaction | TEXT | | Reaction description |
| severity | VARCHAR(20) | | mild, moderate, severe |
| onset_date | DATE | | Date of onset |
| status | VARCHAR(20) | DEFAULT 'active' | active, inactive |
| notes | TEXT | | Additional notes |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |

**Foreign Keys:**
- `patient_id` → patients(id)

---

### 7. vital_signs

Patient vital sign measurements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| patient_id | INTEGER | FOREIGN KEY, NOT NULL | References patients(id) |
| recorded_date | DATETIME | NOT NULL, INDEXED | Recording timestamp |
| systolic_bp | INTEGER | | Systolic blood pressure |
| diastolic_bp | INTEGER | | Diastolic blood pressure |
| heart_rate | INTEGER | | Heart rate (bpm) |
| temperature | FLOAT | | Temperature (°F) |
| respiratory_rate | INTEGER | | Respiratory rate |
| oxygen_saturation | INTEGER | | O2 saturation (%) |
| weight | FLOAT | | Weight (lbs) |
| height | FLOAT | | Height (inches) |
| bmi | FLOAT | | Body Mass Index |
| recorded_by | VARCHAR(100) | | Recorded by |
| notes | TEXT | | Additional notes |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |

**Indexes:**
- `recorded_date`

**Foreign Keys:**
- `patient_id` → patients(id)

---

### 8. lab_results

Laboratory test results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| order_id | VARCHAR(20) | UNIQUE, NOT NULL, INDEXED | Lab order identifier |
| patient_id | INTEGER | FOREIGN KEY, NOT NULL | References patients(id) |
| test_name | VARCHAR(200) | NOT NULL | Test name |
| ordered_date | DATE | NOT NULL | Order date |
| collected_date | DATE | | Collection date |
| resulted_date | DATE | INDEXED | Result date |
| status | VARCHAR(20) | DEFAULT 'pending' | pending, in_progress, final |
| ordered_by | VARCHAR(100) | | Ordering provider |
| results_json | TEXT | | JSON string of results |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |
| updated_at | DATETIME | DEFAULT NOW | Last update timestamp |

**Indexes:**
- `order_id` (UNIQUE)
- `resulted_date`

**Foreign Keys:**
- `patient_id` → patients(id)

**Results JSON Format:**
```json
{
  "WBC": "7.5",
  "RBC": "4.8",
  "Hemoglobin": "14.2",
  "Platelets": "250"
}
```

---

## Relationship Constraints

### Foreign Key Constraints

| Child Table | Foreign Key Column | Parent Table | Parent Column | On Delete |
|-------------|-------------------|--------------|---------------|-----------|
| appointments | patient_id | patients | id | CASCADE |
| appointments | provider_id | providers | id | RESTRICT |
| medications | patient_id | patients | id | CASCADE |
| allergies | patient_id | patients | id | CASCADE |
| vital_signs | patient_id | patients | id | CASCADE |
| lab_results | patient_id | patients | id | CASCADE |

### Cascade Behavior

**CASCADE (Patient deletion):**
- When a patient is deleted, all related records are automatically deleted:
  - All appointments
  - All medications
  - All allergies
  - All vital signs
  - All lab results

**RESTRICT (Provider deletion):**
- Providers cannot be deleted if they have appointments
- Must reassign or delete appointments first

### SQLAlchemy Relationship Configuration

```python
# In Patient model
appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
allergies = relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")
vital_signs = relationship("VitalSign", back_populates="patient", cascade="all, delete-orphan")
lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")

# In Appointment model
patient = relationship("Patient", back_populates="appointments")
provider = relationship("Provider", back_populates="appointments")
```

## Sample Queries

### Get Patient with All Records

```sql
SELECT 
    p.*,
    COUNT(DISTINCT a.id) as appointment_count,
    COUNT(DISTINCT m.id) as medication_count,
    COUNT(DISTINCT al.id) as allergy_count,
    COUNT(DISTINCT v.id) as vital_sign_count,
    COUNT(DISTINCT l.id) as lab_result_count
FROM patients p
LEFT JOIN appointments a ON p.id = a.patient_id
LEFT JOIN medications m ON p.id = m.patient_id
LEFT JOIN allergies al ON p.id = al.patient_id
LEFT JOIN vital_signs v ON p.id = v.patient_id
LEFT JOIN lab_results l ON p.id = l.patient_id
WHERE p.mrn = 'MRN001'
GROUP BY p.id;
```

### Get Complete Patient Record (All Related Data)

```sql
-- Patient demographics
SELECT * FROM patients WHERE mrn = 'MRN001';

-- Patient appointments with provider info
SELECT a.*, pr.name as provider_name, pr.specialty
FROM appointments a
JOIN providers pr ON a.provider_id = pr.id
WHERE a.patient_id = (SELECT id FROM patients WHERE mrn = 'MRN001');

-- Patient medications
SELECT * FROM medications 
WHERE patient_id = (SELECT id FROM patients WHERE mrn = 'MRN001');

-- Patient allergies
SELECT * FROM allergies 
WHERE patient_id = (SELECT id FROM patients WHERE mrn = 'MRN001');

-- Patient vital signs
SELECT * FROM vital_signs 
WHERE patient_id = (SELECT id FROM patients WHERE mrn = 'MRN001')
ORDER BY recorded_date DESC;

-- Patient lab results
SELECT * FROM lab_results 
WHERE patient_id = (SELECT id FROM patients WHERE mrn = 'MRN001')
ORDER BY resulted_date DESC;
```

### Get Upcoming Appointments

```sql
SELECT 
    a.*,
    p.first_name,
    p.last_name,
    pr.name as provider_name
FROM appointments a
JOIN patients p ON a.patient_id = p.id
JOIN providers pr ON a.provider_id = pr.id
WHERE a.date >= CURRENT_DATE
  AND a.status = 'scheduled'
ORDER BY a.date, a.time;
```

### Get Active Medications

```sql
SELECT 
    m.*,
    p.first_name,
    p.last_name
FROM medications m
JOIN patients p ON m.patient_id = p.id
WHERE m.status = 'active'
ORDER BY p.last_name, m.name;
```

---

## Database Migrations

### Initial Setup

```python
from database import init_database
init_database()
```

### Seed Data

```python
python seed_production.py
```

---

## Performance Optimization

### Recommended Indexes

Already implemented:
- `patients.mrn` (UNIQUE)
- `patients.last_name`
- `providers.npi` (UNIQUE)
- `appointments.date`
- `appointments.status`
- `medications.status`
- `vital_signs.recorded_date`
- `lab_results.resulted_date`

### Query Optimization Tips

1. Use indexed columns in WHERE clauses
2. Limit result sets with LIMIT
3. Use JOIN instead of subqueries
4. Avoid SELECT * in production
5. Use connection pooling

---

## Backup & Recovery

### Backup

```bash
# SQLite
cp ehr_database.db ehr_database_backup.db

# PostgreSQL
pg_dump ehr_db > ehr_db_backup.sql
```

### Restore

```bash
# SQLite
cp ehr_database_backup.db ehr_database.db

# PostgreSQL
psql ehr_db < ehr_db_backup.sql
```

---

**Database Engine:** SQLite 3.x / PostgreSQL 12+  
**ORM:** SQLAlchemy 2.0  
**Total Tables:** 8  
**Relationships:** 7 foreign keys
