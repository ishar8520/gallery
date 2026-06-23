#!/usr/bin/env bash

set -e

alembic upgrade head

export PYTHONPATH=/app:$PYTHONPATH

exec "$@"