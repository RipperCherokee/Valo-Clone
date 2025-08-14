#!/bin/sh

# Exit if any command fails
set -e

# 1. Run the database initialization
echo "--- Initializing database... ---"
flask init-db

# 2. Start the Gunicorn server on the correct port for Render
echo "--- Starting server on port 10000... ---"
exec gunicorn --bind 0.0.0.0:10000 app:app