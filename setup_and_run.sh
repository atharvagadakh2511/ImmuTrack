#!/usr/bin/env bash
# ImmuTrack one-command setup (macOS / Linux). Run:  bash setup_and_run.sh
set -e
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations accounts children vaccination notifications analytics
python manage.py migrate
python manage.py seed_demo_system
python manage.py import_nashik_dataset
echo "Starting server at http://127.0.0.1:8000/"
python manage.py runserver
