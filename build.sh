#!/usr/bin/env bash
set -o errexit

apt-get update && apt-get install -y openjdk-17-jre poppler-utils tesseract-ocr

pip install -r requirements.txt
