# ImmuTrack – Child Vaccination Management System

A production-ready Python & Django academic capstone web application with automated Universal Immunization Programme (UIP) scheduling, health worker record administration, notification reminders, ReportLab PDF vaccination certificates, and scikit-learn machine learning defaulter-risk prediction.

---

## 1. Features Overview
- **Parent/Guardian Portal:** Register children, track personalized immunization timelines, receive alerts, and download PDF immunization certificates.
- **Health Worker Dashboard:** Search clinic records, record administered doses with vaccine lot/batch numbers, record adverse events (AEFI), and monitor overdue patient queues.
- **Admin Analytics:** Population coverage surveillance, vaccine administration bar charts (Chart.js), clinic-level KPIs, and full CSV exports.
- **Automated Scheduling Engine:** Generates official timelines based on India's MoHFW Universal Immunization Programme (UIP) guidelines with calendar date handling.
- **Machine Learning Module:** Random Forest classification model using non-leaking historical adherence features (lag days, missed dose ratios) to predict dropout vulnerability.
- **Reminders & Alerts:** Management command supporting upcoming and overdue notifications with duplicate-send prevention and console/SMTP email options.

---

## 2. Quick Setup & Run Instructions

### Step 1: Create and Activate Virtual Environment
**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```
**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Database Migrations
```bash
python manage.py makemigrations accounts children vaccination notifications analytics
python manage.py migrate
```

### Step 4: Seed Demonstration Data & UIP Reference Schedule
This command seeds the official India UIP schedule, sample clinics, pre-configured accounts (admin, nurse, parent), sample children (Aarav and Ananya), and trains the initial ML model:
```bash
python manage.py seed_demo_system
```

### Step 5: Start Local Development Server
```bash
python manage.py runserver
```
Open **http://127.0.0.1:8000/** in your browser.

---

## 3. Pre-Configured Demo Accounts
| Role | Username | Password | Notes |
|---|---|---|---|
| **Administrator** | `admin` | `Admin@12345` | Access to Analytics, ML Engine & Django Admin |
| **Health Worker** | `nurse_priya` | `Worker@12345` | Assigned to Safdarjung PHC, Delhi |
| **Parent / Guardian** | `rajesh_kumar` | `Parent@12345` | Father of Aarav & Ananya |

---

## 4. Key Management Commands
- **Send Vaccination Reminders (Console/Email):**
  ```bash
  python manage.py send_vaccination_reminders
  # Or test in dry-run mode:
  python manage.py send_vaccination_reminders --dry-run
  ```
- **Run Automated Test Suite:**
  ```bash
  python manage.py test
  ```

---

## Nashik 2026 sample dataset (included)

This build ships with a synthetic dataset of **500 children from Nashik city** (born Jan-Sep 2026,
all vaccinations dated 2026) in `data/nashik/`.

**Quick start**
- Windows: double-click `setup_and_run.bat`
- macOS / Linux: `bash setup_and_run.sh`

**Manual start**
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations accounts children vaccination notifications analytics
python manage.py migrate
python manage.py seed_demo_system          # admin + demo users
python manage.py import_nashik_dataset     # 500 Nashik children  (--reset to reload, --skip-ml to skip risk scoring)
python manage.py runserver
```

| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin@12345 |
| Health worker (Nashik) | nurse_nsk_01 ... nurse_nsk_10 | Worker@12345 |
| Parent (Nashik) | nsk_parent_0001 ... nsk_parent_0500 | Parent@12345 |
| Demo parent (Delhi) | rajesh_kumar | Parent@12345 |

All names, phone numbers and e-mails in the dataset are fictional (e-mails use example.com).
Regenerate with: `python data/nashik/generate_nashik_dataset.py --seed 7`
