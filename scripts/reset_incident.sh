#!/usr/bin/env bash
echo "Resetting incident environment to clean default flagship scenario..."
curl -s -X POST "http://localhost:8000/api/incidents/reset" | jq . || curl -s -X POST "http://localhost:8000/api/incidents/reset"
echo ""
