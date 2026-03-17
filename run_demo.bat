@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
cd Flask
python app.py
