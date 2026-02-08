#!/bin/bash
# Health Check Script
set -e
echo "Trading Bot Health Check"
echo "========================"
docker-compose ps
curl -f -s http://localhost:5000/api/health && echo "✓ Bot healthy" || echo "✗ Bot unhealthy"
curl -f -s http://localhost:9090/-/healthy && echo "✓ Prometheus healthy" || echo "✗ Prometheus unhealthy"
echo "Health check complete"
