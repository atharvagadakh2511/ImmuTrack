#!/usr/bin/env bash
set -o errexit

# Install Python dependencies.
pip install -r requirements.txt

# Prepare the production database.
python manage.py migrate --noinput

# Seed the India UIP reference schedule. This command is idempotent.
python manage.py seed_immunization_data

# Import the bundled synthetic Nashik dataset if it has not already been imported.
# The command is safe to run again because it uses get_or_create/update logic.
python manage.py import_nashik_dataset --skip-ml

# Train and persist the ML model into the deploy image, then refresh risk scores.
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
