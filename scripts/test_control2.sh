#!/usr/bin/env bash
set -e
BASE="http://localhost:8080"
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -d "username=admin@cloudcrm.dev&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"

echo "=== LB now spreads across 4 instances (40 reqs) ==="
for i in $(seq 1 40); do
  curl -s "$BASE/api/infrastructure/ping" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['served_by'])"
done | sort | uniq -c

echo "=== Scale to max (6) ==="
curl -s -X POST "$BASE/api/control/scale" -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"target":6}'
echo ""

echo "=== Try to exceed max (should 400) ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/api/control/scale/up" -H "$AUTH"

echo "=== Try to scale beyond max via /scale (should 400) ==="
curl -s -X POST "$BASE/api/control/scale" -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"target":10}'
echo ""

echo "=== Scale down to 2 ==="
curl -s -X POST "$BASE/api/control/scale" -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"target":2}'
echo ""
sleep 5
docker ps --filter "label=com.docker.compose.service=api" --format "{{.Names}}" | sort

echo "=== Unauthenticated scale attempt (should 401) ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/api/control/scale/up"
