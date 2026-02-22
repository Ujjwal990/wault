#!/bin/bash
# Run this on PythonAnywhere any time you update the code.
# Usage: bash ~/wault/deploy/pa_update.sh

set -e
cd ~/wault

echo "→ Pulling latest code..."
git pull

echo "→ Installing dependencies..."
.venv/bin/pip install -r requirements.txt -q

echo "→ Running migrations..."
.venv/bin/python manage.py migrate --no-input

echo "→ Collecting static files..."
.venv/bin/python manage.py collectstatic --no-input

echo "→ Reloading web app..."
touch /var/www/slingshot_pythonanywhere_com_wsgi.py

echo ""
echo "✅ Done! https://slingshot.pythonanywhere.com is updated."
