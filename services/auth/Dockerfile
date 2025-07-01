FROM python:3.12-slim AS poerty_auth_builder

ENV PYTHONBUFFERED=1

RUN pip install --no-cache-dir poetry==2.1.3

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --only main


FROM python:3.12-slim AS base

COPY --from=poerty_auth_builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=poerty_auth_builder /usr/local/bin /usr/local/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl

COPY ./alembic.ini ./alembic.ini
COPY ./src ./src
COPY ./entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT [ "/usr/bin/bash", "entrypoint.sh" ]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]