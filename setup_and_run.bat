@echo off
REM ImmuTrack one-click setup (Windows). Double-click or run from the project folder.
if not exist venv (
    python -m venv venv || (echo Python not found. Install Python 3.9+ and tick "Add to PATH". & pause & exit /b 1)
)
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo Dependency install failed & pause & exit /b 1)
python manage.py makemigrations accounts children vaccination notifications analytics
python manage.py migrate
python manage.py seed_demo_system
python manage.py import_nashik_dataset
echo.
echo Starting server at http://127.0.0.1:8000/
python manage.py runserver
