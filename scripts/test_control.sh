#!/usr/bin/env bash
set -e
BASE="http://localhost:8080"

TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -d "username=admin@cloudcrm.dev&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "=== controller health ==="
curl -s "$BASE/api/control/health"
echo ""

echo "=== status (before) ==="
curl -s "$BASE/api/control/status" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('count:', d['count'], '| limits:', d['limits'])"

echo "=== scale up ==="
curl -s -X POST "$BASE/api/control/scale/up" -H "Authorization: Bearer $TOKEN"
echo ""

sleep 6
echo "=== containers after scale up ==="
docker ps --filter "label=com.docker.compose.service=api" --format "{{.Names}} {{.Status}}" | sort
