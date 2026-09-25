
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "healthcare.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ============================================================
# DROP EXISTING TABLES
# ============================================================

cur.executescript("""
DROP TABLE IF EXISTS eval_results;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS medical_records;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS patients;
""")

# ============================================================
# CREATE TABLES
# ============================================================

cur.executescript("""
CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    phone TEXT,
    email TEXT,
    alert TEXT
);

CREATE TABLE medical_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    record_date TEXT,
    diagnosis TEXT,
    treatment TEXT,
    notes TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE doctors (
    doctor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    specialty TEXT,
    clinic TEXT
);

CREATE TABLE appointments (
    appointment_id TEXT PRIMARY KEY,
    doctor_id TEXT,
    appointment_date TEXT,
    appointment_time TEXT,
    status TEXT,
    FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    payload TEXT,
    status TEXT,
    duration_ms REAL
);

CREATE TABLE eval_results (
    eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    patient_id TEXT,
    question TEXT,
    reference TEXT,
    prediction TEXT,
    grade TEXT,
    score REAL,
    judge TEXT,
    created_at TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
""")

# ============================================================
# 20 PATIENTS
# ============================================================

patients = [
    ("P001", "Rajesh Kumar", 58, "Male",
     "+91-9000000001", "rajesh.kumar@example.com",
     "Monitor blood pressure"),

    ("P002", "Anita Kumar", 46, "Female",
     "+91-9000000002", "anita.kumar@example.com",
     "Monitor renal function"),

    ("P003", "Suresh Reddy", 63, "Male",
     "+91-9000000003", "suresh.reddy@example.com",
     "Diabetes monitoring"),

    ("P004", "Priya Sharma", 39, "Female",
     "+91-9000000004", "priya.sharma@example.com",
     "No critical alerts"),

    ("P005", "Arun Patel", 67, "Male",
     "+91-9000000005", "arun.patel@example.com",
     "Monitor renal function"),

    ("P006", "Meena Iyer", 52, "Female",
     "+91-9000000006", "meena.iyer@example.com",
     "Monitor blood pressure"),

    ("P007", "Vikram Singh", 71, "Male",
     "+91-9000000007", "vikram.singh@example.com",
     "Review medications"),

    ("P008", "Lakshmi Nair", 44, "Female",
     "+91-9000000008", "lakshmi.nair@example.com",
     "No critical alerts"),

    ("P009", "Rohan Gupta", 35, "Male",
     "+91-9000000009", "rohan.gupta@example.com",
     "Monitor blood pressure"),

    ("P010", "Sneha Das", 49, "Female",
     "+91-9000000010", "sneha.das@example.com",
     "Monitor renal function"),

    ("P011", "Karthik Rao", 61, "Male",
     "+91-9000000011", "karthik.rao@example.com",
     "Diabetes monitoring"),

    ("P012", "Divya Menon", 33, "Female",
     "+91-9000000012", "divya.menon@example.com",
     "No critical alerts"),

    ("P013", "Manoj Verma", 56, "Male",
     "+91-9000000013", "manoj.verma@example.com",
     "Monitor renal function"),

    ("P014", "Pooja Shah", 42, "Female",
     "+91-9000000014", "pooja.shah@example.com",
     "Review medications"),

    ("P015", "Sanjay Mehta", 69, "Male",
     "+91-9000000015", "sanjay.mehta@example.com",
     "Monitor blood pressure"),

    ("P016", "Nisha Kapoor", 51, "Female",
     "+91-9000000016", "nisha.kapoor@example.com",
     "Monitor renal function"),

    ("P017", "Amit Joshi", 47, "Male",
     "+91-9000000017", "amit.joshi@example.com",
     "No critical alerts"),

    ("P018", "Kavita Rao", 64, "Female",
     "+91-9000000018", "kavita.rao@example.com",
     "Diabetes monitoring"),

    ("P019", "Deepak Nair", 73, "Male",
     "+91-9000000019", "deepak.nair@example.com",
     "Monitor renal function"),

    ("P020", "Neha Agarwal", 37, "Female",
     "+91-9000000020", "neha.agarwal@example.com",
     "No critical alerts"),
]

cur.executemany("""
INSERT INTO patients
(patient_id, name, age, gender, phone, email, alert)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", patients)

# ============================================================
# MEDICAL RECORDS
# ============================================================

medical_records = [

    ( "P001", "2026-01-10",
      "Chronic Kidney Disease Stage 3",
      "Blood pressure control and renal diet",
      "eGFR moderately reduced. Follow-up recommended."),

    ( "P001", "2026-04-15",
      "Hypertension",
      "ACE inhibitor therapy",
      "Blood pressure improved. Continue monitoring."),

    ( "P002", "2026-02-05",
      "Chronic Kidney Disease Stage 2",
      "ACE inhibitor therapy",
      "Stable renal function."),

    ( "P002", "2026-05-20",
      "Hypertension",
      "Antihypertensive therapy",
      "Continue home BP monitoring."),

    ( "P003", "2026-01-18",
      "Type 2 Diabetes",
      "Metformin and lifestyle management",
      "HbA1c above target. Diet counselling provided."),

    ( "P003", "2026-04-22",
      "Diabetic Kidney Disease",
      "Glycemic and blood pressure control",
      "Urine albumin elevated. Renal monitoring required."),

    ( "P004", "2026-03-12",
      "Urinary Tract Infection",
      "Antibiotic therapy",
      "Symptoms improving after treatment."),

    ( "P005", "2026-01-25",
      "Chronic Kidney Disease Stage 4",
      "Nephrology follow-up and medication review",
      "Advanced CKD. Electrolytes require monitoring."),

    ( "P005", "2026-05-02",
      "Chronic Kidney Disease Stage 4",
      "Renal diet and medication review",
      "Renal function remains reduced."),

    ( "P006", "2026-02-14",
      "Hypertension",
      "Antihypertensive therapy",
      "BP controlled on current medication."),

    ( "P007", "2026-03-01",
      "Chronic Kidney Disease Stage 3",
      "Blood pressure control and renal diet",
      "Moderate CKD with stable symptoms."),

    ( "P008", "2026-02-19",
      "Kidney Stone",
      "Hydration and stone management",
      "Small renal calculus identified."),

    ( "P009", "2026-04-05",
      "Hypertension",
      "Antihypertensive therapy",
      "BP slightly elevated."),

    ( "P010", "2026-01-30",
      "Chronic Kidney Disease Stage 2",
      "ACE inhibitor therapy",
      "Stable kidney function."),

    ( "P011", "2026-02-11",
      "Type 2 Diabetes",
      "Metformin and lifestyle management",
      "Glucose levels require continued monitoring."),

    ( "P012", "2026-03-17",
      "Urinary Tract Infection",
      "Antibiotic therapy",
      "Treatment completed successfully."),

    ( "P013", "2026-01-08",
      "Chronic Kidney Disease Stage 3",
      "Renal diet and blood pressure control",
      "eGFR moderately reduced."),

    ( "P014", "2026-04-10",
      "Hypertension",
      "Antihypertensive therapy",
      "Medication adherence discussed."),

    ( "P015", "2026-02-28",
      "Chronic Kidney Disease Stage 4",
      "Nephrology follow-up",
      "Requires close renal monitoring."),

    ( "P016", "2026-05-12",
      "Chronic Kidney Disease Stage 3",
      "Renal diet",
      "Stable condition."),

    ( "P017", "2026-03-22",
      "Kidney Stone",
      "Hydration and stone management",
      "Follow-up ultrasound planned."),

    ( "P018", "2026-01-16",
      "Type 2 Diabetes",
      "Metformin and lifestyle management",
      "HbA1c monitoring recommended."),

    ( "P019", "2026-04-01",
      "Chronic Kidney Disease Stage 4",
      "Nephrology follow-up and medication review",
      "Advanced CKD requiring regular follow-up."),

    ( "P020", "2026-05-18",
      "Hypertension",
      "Antihypertensive therapy",
      "Blood pressure within acceptable range.")
]

cur.executemany("""
INSERT INTO medical_records
(patient_id, record_date, diagnosis, treatment, notes)
VALUES (?, ?, ?, ?, ?)
""", medical_records)

# ============================================================
# DOCTORS
# ============================================================

doctors = [
    ("D001", "Dr. Meera Nair", "Nephrologist",
     "Chennai Kidney Care"),

    ("D002", "Dr. Arjun Rao", "Nephrologist",
     "Apollo Renal Clinic"),

    ("D003", "Dr. Priya Sharma", "Nephrologist",
     "City Renal Centre"),

    ("D004", "Dr. Vikram Iyer", "Nephrologist",
     "Lifeline Kidney Institute"),

    ("D005", "Dr. Kavita Menon", "Endocrinologist",
     "Chennai Diabetes Centre"),

    ("D006", "Dr. Sanjay Gupta", "General Physician",
     "City Medical Centre")
]

cur.executemany("""
INSERT INTO doctors
(doctor_id, name, specialty, clinic)
VALUES (?, ?, ?, ?)
""", doctors)

# ============================================================
# APPOINTMENTS
# ============================================================

appointments = [

    ("A001", "D001", "2026-10-01", "09:00", "AVAILABLE"),
    ("A002", "D001", "2026-10-01", "10:00", "AVAILABLE"),
    ("A003", "D001", "2026-10-02", "11:00", "AVAILABLE"),

    ("A004", "D002", "2026-10-01", "09:30", "AVAILABLE"),
    ("A005", "D002", "2026-10-02", "10:30", "AVAILABLE"),
    ("A006", "D002", "2026-10-03", "14:00", "AVAILABLE"),

    ("A007", "D003", "2026-10-01", "11:30", "AVAILABLE"),
    ("A008", "D003", "2026-10-03", "09:00", "AVAILABLE"),
    ("A009", "D003", "2026-10-04", "15:00", "AVAILABLE"),

    ("A010", "D004", "2026-10-02", "09:00", "AVAILABLE"),
    ("A011", "D004", "2026-10-03", "10:00", "AVAILABLE"),
    ("A012", "D004", "2026-10-05", "11:00", "AVAILABLE"),

    ("A013", "D005", "2026-10-01", "14:00", "AVAILABLE"),
    ("A014", "D005", "2026-10-03", "15:00", "AVAILABLE"),

    ("A015", "D006", "2026-10-01", "16:00", "AVAILABLE"),
    ("A016", "D006", "2026-10-02", "16:30", "AVAILABLE"),

    ("A017", "D001", "2026-10-06", "09:00", "AVAILABLE"),
    ("A018", "D002", "2026-10-06", "10:00", "AVAILABLE"),
    ("A019", "D003", "2026-10-07", "11:00", "AVAILABLE"),
    ("A020", "D004", "2026-10-07", "14:00", "AVAILABLE")
]

cur.executemany("""
INSERT INTO appointments
(appointment_id, doctor_id, appointment_date, appointment_time, status)
VALUES (?, ?, ?, ?, ?)
""", appointments)

conn.commit()
conn.close()

print("Healthcare seed database created successfully.")
print("Patients       : 20")
print("Medical records: 23")
print("Doctors        : 6")
print("Appointments   : 20")
print("Evaluation table: created (empty, populated as queries are run)")