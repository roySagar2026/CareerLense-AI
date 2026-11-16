#!/usr/bin/env bash
# Prints a random 64-character URL-safe secret suitable for JWT_SECRET.
set -euo pipefail
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import secrets;print(secrets.token_urlsafe(48))"
else
  openssl rand -base64 48 | tr '+/' '-_' | tr -d '=\n'; echo
fi
