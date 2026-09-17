#!/usr/bin/env bash
SCENARIO=${1:-"multi_source"}

echo "Triggering incident scenario: $SCENARIO"
curl -s -X POST "http://localhost:8000/api/incidents/$SCENARIO/trigger" | jq . || curl -s -X POST "http://localhost:8000/api/incidents/$SCENARIO/trigger"
echo ""
