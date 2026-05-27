#!/usr/bin/env bash
# Verify Ribet Railway deploy before running the new-user walkthrough.
#
# Usage:
#   export WEB_URL="https://your-web.up.railway.app"
#   export API_URL="https://your-api.up.railway.app"
#   ./scripts/verify-railway-deploy.sh

set -euo pipefail

WEB_URL="${WEB_URL:-}"
API_URL="${API_URL:-}"

if [[ -z "$WEB_URL" || -z "$API_URL" ]]; then
  echo "Set WEB_URL and API_URL to your public Railway domains."
  echo ""
  echo "  export WEB_URL=\"https://your-web.up.railway.app\""
  echo "  export API_URL=\"https://your-api.up.railway.app\""
  exit 1
fi

WEB_URL="${WEB_URL%/}"
API_URL="${API_URL%/}"

pass() { echo "  OK   $1"; }
fail() { echo "  FAIL $1"; FAILED=1; }

FAILED=0

echo "=== Ribet deploy verification ==="
echo "WEB_URL=$WEB_URL"
echo "API_URL=$API_URL"
echo ""

check_json() {
  local label="$1" url="$2" expect="$3"
  if body=$(curl -sf --max-time 15 "$url" 2>/dev/null); then
    if echo "$body" | grep -q "$expect"; then
      pass "$label"
      echo "       $body" | head -c 200
      echo ""
    else
      fail "$label (unexpected body: ${body:0:120})"
    fi
  else
    rc=$?
    if [[ "$rc" -eq 60 ]]; then
      fail "$label (TLS cert mismatch — verify Railway custom domain + HTTPS cert provisioning)"
    else
      fail "$label (no response or HTTP error)"
    fi
  fi
}

echo "API"
check_json "GET /health" "$API_URL/health" '"ok"'
check_json "GET /health/ready" "$API_URL/health/ready" '"ok"'

echo ""
echo "Web BFF"
check_json "GET /api/health" "$WEB_URL/api/health" '"ok"'

echo ""
echo "Worker (via BFF → API)"
if body=$(curl -sf --max-time 15 "$WEB_URL/api/health/worker" 2>/dev/null); then
  echo "       $body"
  if echo "$body" | grep -q '"worker_alive":true'; then
    pass "worker_alive is true"
  else
    fail "worker_alive is false — check worker env + deploy logs"
  fi
  pending=$(echo "$body" | grep -o '"pending_jobs":[0-9]*' || true)
  processing=$(echo "$body" | grep -o '"processing_jobs":[0-9]*' || true)
  echo "       $pending $processing"
else
  rc=$?
  if [[ "$rc" -eq 60 ]]; then
    fail "GET /api/health/worker (TLS cert mismatch — verify Railway custom domain + HTTPS cert provisioning)"
  else
    fail "GET /api/health/worker (is FASTAPI_URL set on web?)"
  fi
fi

echo ""
if [[ "${FAILED:-0}" -eq 0 ]]; then
  echo "All checks passed. Run the walkthrough:"
  echo "  docs/railway-new-user-walkthrough.md"
  echo "  $WEB_URL"
else
  echo "Some checks failed. See docs/railway-env-setup.md"
  exit 1
fi
