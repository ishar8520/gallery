#!/usr/bin/env bash

set -e

exec "$@"

alembic upgrade head
