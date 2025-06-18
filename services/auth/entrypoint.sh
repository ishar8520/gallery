#!/usr/bin/env bash

set -e

alembic upgrade head

export PYTHONPATH=/opt/app:$PYTHONPATH

exec "$@"