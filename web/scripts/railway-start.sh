#!/bin/sh
set -e
export HOSTNAME="${HOSTNAME:-0.0.0.0}"
export PORT="${PORT:-3000}"
echo "ribet-web starting on ${HOSTNAME}:${PORT}"
exec node server.js
