#!/bin/bash
# Production Deployment Script for Trading Bot
set -e
echo "========================================="
echo "Trading Bot Production Deployment"
echo "========================================="
# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi
# Create directories
mkdir -p data logs monitoring/grafana/dashboards monitoring/grafana/datasources
# Build and start
docker-compose build
docker-compose up -d
echo "Deployment Complete!"
echo "Dashboard: http://localhost:5000"
