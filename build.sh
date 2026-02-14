#!/usr/bin/env bash
# DigitalOcean build script

set -o errexit  # Exit on error

echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Build completed successfully!"
