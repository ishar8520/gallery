ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS poetry_builder

ENV PYTHONBUFFERED=1

RUN pip install --no-cache-dir poetry==1.7.1
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

FROM python:${PYTHON_VERSION}-slim AS base

COPY --from=poetry_builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=poetry_builder /usr/local/bin /usr/local/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl

COPY ./src ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]