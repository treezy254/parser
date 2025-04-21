#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Create main folders and files
mkdir -p src .github/workflows docs web tests

# Initialize git
git init

# Create top-level files
touch Dockerfile README.md setup.sh req.txt

# Create files inside src
touch src/main.py src/app.py src/repositories.py src/models.py src/services.py src/config.py src/security.py

# Optional: Make setup.sh executable
chmod +x setup.sh

# Echo what was done
echo "Project structure created successfully!"