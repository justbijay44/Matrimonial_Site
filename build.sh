#!/bin/bash

# Activate virtual environment
source /opt/venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Build Tailwind CSS
cd theme
npm install
npm run build
cd ..

# Collect static files
python manage.py tailwind build
python manage.py collectstatic --noinput

# Run migrations and start the server
python manage.py migrate
daphne -b 0.0.0.0 -p $PORT marital_website.asgi:application 