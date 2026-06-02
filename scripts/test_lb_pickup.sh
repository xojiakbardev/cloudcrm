#!/usr/bin/env bash
set -e
BASE="http://localhost:8080"
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -d "username=admin@cloudcrm.dev&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"

echo "=== current count ==="
curl -s "$BASE/api/control/status" -H "$AUTH" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['count'])"

echo "=== scale to 4 ==="
curl -s -X POST "$BASE/api/control/scale" -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"target":4}' ; echo ""

echo "waiting 10s for new instances to be healthy + DNS refresh..."
sleep 10

echo "=== 60 requests through LB ==="
for i in $(seq 1 60); do
  curl -s "$BASE/api/infrastructure/ping" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['served_by'])"
done | sort | uniq -c
