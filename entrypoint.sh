#!/bin/sh
set -e

if [ -n "$ALEMBIC_CONFIG" ]; then
  alembic -c "$ALEMBIC_CONFIG" upgrade head
else
  alembic upgrade head
fi

exec "$@"

