#!/usr/bin/env bash
# Smoke test: health checks plus a register -> login -> refresh round trip.
# Usage: ./infrastructure/scripts/smoke-test.sh https://your-app.vercel.app
# Creates ONE throwaway user (smoke+<timestamp>@example.com) in the target database.
# For Vercel preview URLs behind Deployment Protection set VERCEL_BYPASS_SECRET.
set -euo pipefail

BASE_URL="${1:-${BASE_URL:-}}"
if [ -z "$BASE_URL" ]; then
  echo "usage: $0 <base-url>" >&2
  exit 2
fi
BASE_URL="${BASE_URL%/}"

JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT

EXTRA=()
if [ -n "${VERCEL_BYPASS_SECRET:-}" ]; then
  EXTRA=(-H "x-vercel-protection-bypass: ${VERCEL_BYPASS_SECRET}")
fi

req() { curl -sS --max-time 60 "${EXTRA[@]}" "$@"; }
fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok:   $*"; }

code=$(req -o /dev/null -w '%{http_code}' "$BASE_URL/api/health") || fail "health unreachable"
[ "$code" = "200" ] || fail "/api/health returned $code"
ok "/api/health"

code=$(req -o /dev/null -w '%{http_code}' "$BASE_URL/api/health/ready") || fail "ready unreachable"
[ "$code" = "200" ] || fail "/api/health/ready returned $code (database unreachable or not migrated?)"
ok "/api/health/ready"

EMAIL="smoke+$(date +%s)@example.com"
PASSWORD="Smoke-Test-$(date +%s)a1"

code=$(req -o /dev/null -w '%{http_code}' -c "$JAR" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Smoke Test\"}" \
  "$BASE_URL/api/v1/auth/register")
[ "$code" = "201" ] || fail "register returned $code"
ok "register"

: > "$JAR"
body=$(req -c "$JAR" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" "$BASE_URL/api/v1/auth/login") || fail "login failed"
TOKEN=$(printf '%s' "$body" | sed -n 's/.*"access_token" *: *"\([^"]*\)".*/\1/p')
[ -n "$TOKEN" ] || fail "login returned no access_token"
ok "login"

code=$(req -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/users/me")
[ "$code" = "200" ] || fail "GET /users/me returned $code"
ok "authenticated request"

code=$(req -o /dev/null -w '%{http_code}' -b "$JAR" -c "$JAR" -X POST \
  -H 'X-Requested-With: CareerLens' "$BASE_URL/api/v1/auth/refresh")
[ "$code" = "200" ] || fail "refresh returned $code (cookie not set/sent? check HTTPS and same-origin)"
ok "refresh"

echo "Smoke test passed for $BASE_URL (test user: $EMAIL - delete it via Settings or DELETE /users/me if desired)."
