#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install system dependencies
apt-get update && apt-get install -y libzbar0 poppler-utils tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt
