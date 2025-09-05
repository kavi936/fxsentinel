# Railway Procfile for Main App (Web Application)
# This should be used for the main Flask web application deployment
web: cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2
