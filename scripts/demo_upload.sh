#!/usr/bin/env bash
# Upload all fixtures and fetch latest report (requires docker compose up)
set -e
ORG=11111111-1111-1111-1111-111111111111
API=http://localhost:8000
KEY=dev-secret

for f in fixtures/*.csv; do
  echo "Uploading $f..."
  curl -s -X POST "$API/v1/ingest/uploads" \
    -H "X-API-Key: $KEY" \
    -H "X-Org-Id: $ORG" \
    -F "files=@$f"
  echo
  sleep 3
done

echo "Waiting for worker..."
sleep 15

echo "Latest report:"
curl -s "$API/v1/reports/latest" \
  -H "X-API-Key: $KEY" \
  -H "X-Org-Id: $ORG" | python3 -m json.tool
