
#!/usr/bin/env bash
set -o errexit

# Install Python dependencies.
pip install -r requirements.txt

# Prepare the production database.
python manage.py migrate --noinput

# Configure initial administrator.
python manage.py shell <<'PY'
import os
from django.contrib.auth.models import User
from accounts.models import Role

username = os.environ.get("INITIAL_ADMIN_USERNAME")
password = os.environ.get("INITIAL_ADMIN_PASSWORD")
email = os.environ.get("INITIAL_ADMIN_EMAIL", "")

if username and password:
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={"email": email}
    )
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    user.profile.role = Role.ADMIN
    user.profile.save()
    print("Initial administrator configured.")
else:
    print("Admin creation skipped: environment variables not configured.")
PY

# Seed the India UIP reference schedule.
python manage.py seed_immunization_data

# Import the bundled synthetic Nashik dataset.
python manage.py import_nashik_dataset --skip-ml

# Import Maharashtra hospitals and vaccination centres.
python manage.py import_facilities

# Train and persist the ML model.
python manage.py shell <<'PY'
from analytics.ml.pipeline import DefaulterRiskPipeline
from analytics.models import ChildRiskAssessment, MLModelMetadata
from children.models import Child

metrics = DefaulterRiskPipeline.train_and_persist()
meta = MLModelMetadata.objects.create(
    model_name="Baseline Random Forest Adherence Predictor (Render deployment)",
    version="1.0.0",
    accuracy=metrics["accuracy"],
    precision=metrics["precision"],
    recall=metrics["recall"],
    f1_score=metrics["f1_score"],
    features_used=", ".join(metrics["features"]),
)

for child in Child.objects.all():
    prediction = DefaulterRiskPipeline.predict_risk(child)
    ChildRiskAssessment.objects.update_or_create(
        child=child,
        defaults={
            "model_version": meta,
            "risk_level": prediction["level"],
            "probability": prediction["probability"],
            "top_risk_factor": prediction["factor"],
        },
    )
print("ML model trained and risk assessments initialized.")
PY

# Collect static assets for WhiteNoise.
python manage.py collectstatic --noinput
