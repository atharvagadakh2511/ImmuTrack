"""
Generates a SYNTHETIC (fictional) child-immunization dataset for Nashik city.

Output (CSV files written next to this script):
  nashik_clinics.csv       10 sample urban health centres + 1 health worker each
  nashik_children_2026.csv 500 children + guardian details
  nashik_vaccinations_2026.csv  every vaccine dose actually administered

All people, phone numbers and e-mails are made up. E-mails use example.com.

Usage (from the project root):
  python data/nashik/generate_nashik_dataset.py
  python data/nashik/generate_nashik_dataset.py --count 500 --seed 2026
"""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from dateutil.relativedelta import relativedelta

OUT = Path(__file__).resolve().parent
REF_DATE = date(2026, 10, 5)  # "today" for the dataset: no record is dated after this

# ---------------------------------------------------------------- clinics
CLINICS = [
    # code, name, locality, pincode, weight, poor-adherence probability
    ("PHC-NSK-01", "Panchavati Urban Primary Health Centre", "Panchavati", "422003", 12, 0.12),
    ("PHC-NSK-02", "Nashik Road Urban Primary Health Centre", "Nashik Road", "422101", 14, 0.14),
    ("PHC-NSK-03", "CIDCO New Nashik Urban Health Centre", "CIDCO", "422008", 13, 0.10),
    ("PHC-NSK-04", "Satpur MIDC Urban Primary Health Centre", "Satpur", "422007", 11, 0.16),
    ("PHC-NSK-05", "Ambad Urban Primary Health Centre", "Ambad", "422010", 10, 0.18),
    ("PHC-NSK-06", "Gangapur Road Maternal & Child Health Clinic", "Gangapur Road", "422013", 9, 0.09),
    ("PHC-NSK-07", "Deolali Camp Urban Primary Health Centre", "Deolali Camp", "422401", 8, 0.17),
    ("PHC-NSK-08", "Indira Nagar Urban Primary Health Centre", "Indira Nagar", "422009", 8, 0.11),
    ("PHC-NSK-09", "Old Nashik Community Health Centre", "Old Nashik", "422001", 9, 0.20),
    ("PHC-NSK-10", "Adgaon Urban Primary Health Centre", "Adgaon", "422003", 6, 0.22),
]

NURSE_FIRST = ["Sunita", "Rupali", "Kavita", "Swati", "Vandana", "Madhuri", "Shital", "Archana", "Manisha", "Jyoti"]
NURSE_LAST = ["Patil", "Jadhav", "Pawar", "Shinde", "Kale", "More", "Gaikwad", "Chavan", "Sonawane", "Wagh"]

# ---------------------------------------------------------------- names
HINDU_M = ["Aarav", "Atharv", "Shreyas", "Om", "Sahil", "Rohan", "Pranav", "Arnav", "Vihaan", "Ishaan",
           "Aryan", "Yash", "Soham", "Omkar", "Tanmay", "Sarthak", "Rudra", "Advait", "Veer", "Kabir",
           "Shlok", "Harsh", "Parth", "Dev", "Ayush", "Vedant", "Prathamesh", "Swayam", "Ojas", "Raj",
           "Siddharth", "Kunal", "Aditya", "Tejas", "Chinmay", "Nishant", "Sairaj", "Mayur", "Darshan", "Hrithik"]
HINDU_F = ["Aadhya", "Anaya", "Diya", "Ira", "Myra", "Saanvi", "Siya", "Aarohi", "Isha", "Kavya",
           "Riya", "Shravani", "Ovi", "Anvi", "Prisha", "Sanvi", "Tanvi", "Avni", "Pari", "Aditi",
           "Gauri", "Mrunal", "Manasvi", "Radhika", "Janhavi", "Vaishnavi", "Sakshi", "Trisha", "Ananya", "Nidhi",
           "Swara", "Samiksha", "Aarya", "Kiara", "Anushka", "Pranjal", "Rutuja", "Sara", "Ruchika", "Sai"]
HINDU_SUR = ["Patil", "Deshmukh", "Pawar", "Jadhav", "Shinde", "Gaikwad", "More", "Kale", "Bhosale", "Chavan",
             "Sonawane", "Kulkarni", "Joshi", "Deshpande", "Kadam", "Salunke", "Wagh", "Gavit", "Ahire", "Bagul",
             "Thakur", "Sharma", "Gupta", "Yadav", "Nikam", "Dhole", "Borse", "Aher", "Khairnar", "Mahale",
             "Pagar", "Jagtap", "Gholap", "Raut", "Bhalerao", "Kothawade", "Dhamale", "Shirsath", "Kasar", "Thorat",
             "Sawant", "Mali", "Londhe"]
HINDU_GM = ["Rajesh", "Sachin", "Amit", "Nitin", "Sandeep", "Prashant", "Vishal", "Santosh", "Ganesh", "Mahesh",
            "Yogesh", "Ramesh", "Anil", "Dinesh", "Sunil", "Vijay", "Ajay", "Rahul", "Kiran", "Pravin"]
HINDU_GF = ["Sunita", "Priya", "Pooja", "Sneha", "Rupali", "Kavita", "Swati", "Anjali", "Vandana", "Madhuri",
            "Shital", "Archana", "Manisha", "Deepali", "Jyoti", "Rashmi", "Neha", "Komal", "Pallavi", "Smita"]

MUSLIM_M = ["Ayaan", "Zayan", "Arham", "Rayyan", "Ayan", "Zaid", "Hamza", "Arman"]
MUSLIM_F = ["Zoya", "Inaya", "Aaliyah", "Mehek", "Sana", "Hiba", "Alina", "Noor"]
MUSLIM_SUR = ["Shaikh", "Pathan", "Khan", "Sayyed", "Ansari", "Momin"]
MUSLIM_GM = ["Imran", "Salman", "Irfan", "Javed", "Asif", "Faisal", "Nadeem", "Rizwan"]
MUSLIM_GF = ["Shabana", "Nasreen", "Farzana", "Rukhsar", "Shaheen", "Ayesha", "Samina", "Rehana"]

BLOOD = [("B+", 32), ("O+", 28), ("A+", 22), ("AB+", 8), ("B-", 3), ("O-", 3), ("A-", 2), ("AB-", 2)]
ALLERGIES = [("None known", 93), ("Dust allergy", 2), ("Egg allergy", 1), ("Cow's milk protein", 2),
             ("Penicillin (family history)", 1), ("Eczema / skin allergy", 1)]

# ---------------------------------------------------------------- UIP schedule (mirrors seed_immunization_data.py)
# code, dose_no, label, offset_days, offset_months
SCHEDULE = [
    ("BCG", 1, "BCG (At Birth)", 0, 0), ("OPV", 1, "OPV Zero Dose (At Birth)", 0, 0),
    ("HepB", 1, "Hepatitis B Birth Dose", 0, 0),
    ("OPV", 2, "OPV-1 (6 Weeks)", 42, 0), ("Penta", 1, "Pentavalent-1 (6 Weeks)", 42, 0),
    ("Rota", 1, "Rotavirus-1 (6 Weeks)", 42, 0), ("fIPV", 1, "fIPV-1 (6 Weeks)", 42, 0),
    ("PCV", 1, "PCV-1 (6 Weeks)", 42, 0),
    ("OPV", 3, "OPV-2 (10 Weeks)", 70, 0), ("Penta", 2, "Pentavalent-2 (10 Weeks)", 70, 0),
    ("Rota", 2, "Rotavirus-2 (10 Weeks)", 70, 0),
    ("OPV", 4, "OPV-3 (14 Weeks)", 98, 0), ("Penta", 3, "Pentavalent-3 (14 Weeks)", 98, 0),
    ("Rota", 3, "Rotavirus-3 (14 Weeks)", 98, 0), ("fIPV", 2, "fIPV-2 (14 Weeks)", 98, 0),
    ("PCV", 2, "PCV-2 (14 Weeks)", 98, 0),
    ("MR", 1, "MR-1 (9-12 Months)", 0, 9), ("PCV", 3, "PCV Booster (9 Months)", 0, 9),
    ("MR", 2, "MR-2 (16-24 Months)", 0, 16), ("DPT_Booster", 1, "DPT Booster-1 (16-24 Months)", 0, 16),
    ("OPV_Booster", 1, "OPV Booster (16-24 Months)", 0, 16),
]


def due_date(dob, off_days, off_months):
    d = dob
    if off_months > 0:
        d = d + relativedelta(months=off_months)
    if off_days > 0:
        d = d + relativedelta(days=off_days)
    return d


def wchoice(rng, pairs):
    items, weights = zip(*pairs)
    return rng.choices(items, weights=weights, k=1)[0]


def delay_for(rng, profile):
    if profile == "GOOD":
        return 0 if rng.random() < 0.70 else (rng.randint(1, 3) if rng.random() < 0.88 else rng.randint(4, 10))
    if profile == "AVERAGE":
        return int(rng.triangular(0, 21, 5))
    return rng.randint(10, 60)  # POOR


MISS_P = {"GOOD": 0.02, "AVERAGE": 0.10, "POOR": 0.40}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=500)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--dob-start", default="2026-01-01")
    ap.add_argument("--dob-end", default="2026-09-30")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    dob_start, dob_end = date.fromisoformat(a.dob_start), date.fromisoformat(a.dob_end)
    span = (dob_end - dob_start).days

    clinic_rows, workers = [], {}
    for i, (code, name, loc, pin, _, _) in enumerate(CLINICS):
        wu = f"nurse_nsk_{i + 1:02d}"
        workers[code] = wu
        clinic_rows.append({
            "registration_code": code, "name": name,
            "address": f"{loc}, Nashik, Maharashtra {pin}",
            "contact_phone": f"+91-253-{rng.randint(2300000, 2799999)}",
            "contact_email": f"{code.lower()}@example.org",
            "worker_username": wu, "worker_first_name": NURSE_FIRST[i], "worker_last_name": NURSE_LAST[i],
            "worker_email": f"{wu}@example.org",
        })

    clinic_w = [c[4] for c in CLINICS]
    children_rows, vacc_rows = [], []

    for n in range(1, a.count + 1):
        ref = f"NSK-2026-{n:04d}"
        muslim = rng.random() < 0.08
        gender = "M" if rng.random() < 0.515 else "F"
        fn_pool = (MUSLIM_M if gender == "M" else MUSLIM_F) if muslim else (HINDU_M if gender == "M" else HINDU_F)
        first, last = rng.choice(fn_pool), rng.choice(MUSLIM_SUR if muslim else HINDU_SUR)

        rel = rng.choices(["MOTHER", "FATHER", "GUARDIAN"], weights=[70, 25, 5])[0]
        g_female = rel == "MOTHER" or (rel == "GUARDIAN" and rng.random() < 0.5)
        gpool = (MUSLIM_GF if g_female else MUSLIM_GM) if muslim else (HINDU_GF if g_female else HINDU_GM)
        g_first = rng.choice(gpool)

        clinic = rng.choices(CLINICS, weights=clinic_w, k=1)[0]
        code = clinic[0]
        profile = rng.choices(
            ["POOR", "AVERAGE", "GOOD"],
            weights=[clinic[5], 0.25, 1 - clinic[5] - 0.25])[0]

        dob = dob_start + timedelta(days=rng.randint(0, span))
        reg = min(dob + timedelta(days=rng.randint(0, 10)), REF_DATE)
        username = f"nsk_parent_{n:04d}"

        children_rows.append({
            "child_ref": ref, "first_name": first, "last_name": last,
            "date_of_birth": dob.isoformat(), "gender": gender,
            "blood_group": wchoice(rng, BLOOD), "allergies": wchoice(rng, ALLERGIES),
            "guardian_relationship": rel, "guardian_username": username,
            "guardian_first_name": g_first, "guardian_last_name": last,
            "guardian_email": f"{username}@example.com",
            "guardian_phone": f"+91-{rng.choice(['98', '97', '99', '88', '93', '70', '72', '75', '80', '90'])}{rng.randint(10000000, 99999999)}",
            "clinic_code": code, "locality": clinic[2], "pincode": clinic[3],
            "registration_date": reg.isoformat(), "adherence_profile": profile,
        })

        # ---- simulate vaccination history up to REF_DATE
        last_admin = {}   # vaccine code -> last administered date
        missed_prev = {}  # vaccine code -> previous dose missed?
        for vcode, dno, label, od, om in SCHEDULE:
            due = due_date(dob, od, om)
            if due > REF_DATE:
                continue
            birth_dose = (od == 0 and om == 0)
            p_miss = MISS_P[profile]
            if birth_dose:
                p_miss = 0.04 if profile != "POOR" else 0.15
            if missed_prev.get(vcode):
                p_miss = min(0.9, p_miss * 2 + 0.2)
            if rng.random() < p_miss:
                missed_prev[vcode] = True
                continue
            delay = 0 if (birth_dose and rng.random() < 0.9) else delay_for(rng, profile)
            adm = due + timedelta(days=delay)
            if vcode in last_admin:  # respect 28-day minimum interval
                adm = max(adm, last_admin[vcode] + timedelta(days=28))
            if adm > REF_DATE:
                missed_prev[vcode] = True
                continue
            missed_prev[vcode] = False
            last_admin[vcode] = adm
            fac = code if rng.random() < 0.92 else rng.choice(CLINICS)[0]
            adverse = rng.random() < 0.02 and not birth_dose
            vacc_rows.append({
                "child_ref": ref, "vaccine_code": vcode, "dose_number": dno, "dose_label": label,
                "due_date": due.isoformat(), "administered_date": adm.isoformat(), "delay_days": (adm - due).days,
                "batch_number": f"UIP-NSK-{adm:%Y%m}-{vcode.upper()}-{rng.randint(100, 999)}",
                "facility_code": fac, "administered_by_username": workers[fac],
                "adverse_reaction": "TRUE" if adverse else "FALSE",
                "notes": "Mild fever and local swelling; resolved in 48 hours." if adverse
                         else ("Administered at hospital after delivery." if birth_dose and delay == 0 else "Routine UIP session."),
            })

    def write(name, rows):
        with open(OUT / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    write("nashik_clinics.csv", clinic_rows)
    write("nashik_children_2026.csv", children_rows)
    write("nashik_vaccinations_2026.csv", vacc_rows)
    print(f"Wrote {len(clinic_rows)} clinics, {len(children_rows)} children, {len(vacc_rows)} vaccinations to {OUT}")


if __name__ == "__main__":
    main()
