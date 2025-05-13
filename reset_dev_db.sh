#!/bin/bash

echo "Resetting development database..."

# Set environment
export FLASK_APP=solaranalytics.py
export FLASK_ENV=development

# Step 1: Delete existing SQLite DB
if [ -f "app.db" ]; then
    echo "Removing existing app.db"
    rm app.db
fi

# Step 2: Delete existing migrations folder
if [ -d "migrations" ]; then
    echo "Removing existing migrations folder"
    rm -rf migrations
fi

# Step 3: Re-initialize migrations
echo "Initializing migrations..."
flask db init

# Step 4: Generate new migration scripts
echo "Generating migration scripts..."
flask db migrate -m "Reset DB"

# Step 5: Apply migrations to create fresh DB schema
echo "Applying migrations..."
flask db upgrade

echo "Development database reset complete."
