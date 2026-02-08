#!/bin/bash
# Backup Script for Trading Bot Data
set -e
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_FILE data/ logs/ config.yaml .env 2>/dev/null || true
echo "Backup created: $BACKUP_FILE"
