ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS poetry_gallery_builder

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir "poetry>=2.0,<3.0"
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

FROM python:${PYTHON_VERSION}-slim AS base

COPY --from=poetry_gallery_builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=poetry_gallery_builder /usr/local/bin /usr/local/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./alembic.ini ./alembic.ini
COPY ./src ./src
COPY ./entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/bin/bash", "entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
