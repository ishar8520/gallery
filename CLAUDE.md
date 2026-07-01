# gallery

Онлайн-галерея: авторизованные пользователи хранят и просматривают свои фотографии.
Микросервисная архитектура, развёртывание через Docker Compose ([compose.yaml](compose.yaml)).

## Сервисы

| Сервис | Путь | Стек | Статус |
|---|---|---|---|
| auth | `services/auth` | FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Alembic | разобран и поправлен (см. ниже) |
| gallery | `services/gallery` | FastAPI (предположительно, есть Dockerfile + poetry) | не разбирался |
| nginx | `services/nginx` | reverse proxy перед auth/gallery | не разбирался (кроме базового образа, см. ниже) |
| minio | `services/minio` | S3-совместимое хранилище фото | не разбирался (кроме базового образа, см. ниже) |

Разбор и доработка сервисов идёт по очереди. Сейчас приведён в порядок только **auth**
(код, тесты, CI). gallery/nginx/minio по содержимому — следующие в очереди, контекст по
их прикладному коду/конфигу пока не собран.

### Базовые образы — отказ от Bitnami (2026-06-23, смержено: PR #9 `infra/replace-bitnami-images`)

Все четыре инфраструктурных образа были на `bitnami/*` (postgresql, redis, nginx, minio).
После покупки Bitnami Broadcom'ом большинство тегов перестали свободно тянуться с Docker Hub.
Заменено на официальные образы в `compose.yaml` / `services/nginx/Dockerfile` / `services/minio/Dockerfile`:

| Было | Стало | Что изменилось |
|---|---|---|
| `bitnami/postgresql:17` | `postgres:17` | env `POSTGRESQL_USERNAME/PASSWORD/DATABASE` → `POSTGRES_USER/PASSWORD/DB`; volume `/bitnami/postgresql` → `/var/lib/postgresql/data` |
| `bitnami/redis:8.0` | `redis:8.0` | `ALLOW_EMPTY_PASSWORD=yes` убран (без пароля — поведение по умолчанию); `command` теперь `redis-server --maxmemory ...` вместо bitnami-скрипта; volume `/bitnami/redis/data` → `/data` |
| `bitnami/nginx:latest` (build) | `nginx:1.27-alpine` (build) | конфиг копируется в `/etc/nginx/conf.d/` вместо `/opt/bitnami/nginx/conf/server_blocks`; стоковый `default.conf` удаляется в Dockerfile; volume логов `/opt/bitnami/nginx/logs` → `/var/log/nginx` |
| `bitnami/minio:latest` (build) | `minio/minio:latest` (build, официальный от самого MinIO) | добавлен явный `CMD ["server", "/data", "--console-address", ":9001"]` — у официального образа, в отличие от bitnami, нет автозапуска без аргументов |

**Важная особенность nginx:** у официального образа `access.log`/`error.log` по умолчанию —
симлинки на `/dev/stdout`/`/dev/stderr`, а не обычные файлы. Volume `nginx-logs-data` всё ещё
примонтирован на `/var/log/nginx`, но реальные логи теперь смотреть через `docker logs nginx`,
а не через файлы в volume.

Все 4 образа проверены вживую (`docker build` + `docker run`/`docker compose config`) —
тянутся, стартуют, health-check'и (`pg_isready`, `redis-cli ping`, `/minio/health/live`,
`nginx -t`) проходят. `.env.sample` не менялся — это имена переменных в корневом `.env`,
они не привязаны к именам env-переменных самих контейнеров.

**Известный пробел:** для этой замены нет автоматического CI-чека — `.github/workflows/auth-ci.yml`
триггерится только на `services/auth/**` и не покрывает `compose.yaml`/`nginx`/`minio`. Проверка была
только ручной (см. выше). Если правки в эту область будут продолжаться — стоит завести отдельный
workflow с собственным path-фильтром (например `compose.yaml`, `services/nginx/**`, `services/minio/**`),
аналогично `auth-ci.yml`.

## Auth-service

### Стек (актуален, без устаревших библиотек)
Python 3.12, FastAPI 0.115, Pydantic v2, SQLAlchemy 2.0 async + asyncpg, Alembic,
Redis (`redis.asyncio`), `async-fastapi-jwt-auth` (обёртка над PyJWT — **не** `python-jose`),
bcrypt напрямую (без passlib). Зависимости и сборка — Poetry.

Управление пользователем: регистрация, login/logout, access+refresh JWT (cookie + header),
роли USER/ADMIN, бутстрап суперюзера через Alembic-миграцию.
Межсервисный эндпоинт `GET /auth/api/v1/verify` — проверяет подпись JWT и отзыв токена
через Redis (для вызова из gallery-service и других сервисов).

### Сделано в ходе ревью ветки `feature/auth-service` (2026-06-23, смержено: PR #8 `fix/auth-service-review`)

Полный список находок и обоснование — см. историю диалога/PR. Кратко:

**Исправлено:**
- IDOR в `PATCH /user/{user_id}` — эндпоинт позволял любому аутентифицированному
  пользователю менять чужой профиль. Добавлена проверка: меняешь свой профиль —
  ОК, иначе требуется роль ADMIN ([services/auth/src/api/v1/endpoints/user.py](services/auth/src/api/v1/endpoints/user.py)).
- SQL без параметризации в `downgrade()` миграции `192db30b56b4_add_admin.py`
  (ломала синтаксис из-за отсутствия кавычек) — переведено на `sa.text` с bind-параметром.
- Опечатка `poerty_auth_builder` → `poetry_auth_builder` в Dockerfile.
- Мёртвый код (`AuthService.get_password`), лишний повторный `add_user()` в `RoleService.add_user_role`,
  неверный `PYTHONPATH=/opt/app` в entrypoint.sh (код лежит в `/app`), грамматика в текстах ошибок,
  непоследовательное использование `Roles.ADMIN` vs `Roles.ADMIN.value`.
- Добавлены unit-тесты на pytest: `services/auth/tests/` (см. ниже). Регрессионный тест
  на IDOR-фикс лежит в `tests/unit/test_user_endpoints.py`.

**Сознательно отложено (не блокирует текущий PR, но нужно отдельными тикетами):**
- Восстановление пароля, подтверждение email — отсутствуют полностью.
- Rate limiting / lockout на login — отсутствует (риск брутфорса).
- Валидация сложности пароля — принимается строка любой длины.
- `authjwt_cookie_csrf_protect=False` при использовании cookie-based JWT — стоит включить,
  но это меняет поведение клиента (нужен CSRF-токен в заголовке), требует согласования с фронтом.
- Healthcheck `GET /auth/api/v1/_healthcheck` возвращает `{}` без реальной проверки
  доступности Postgres и Redis — в production стоит добавить пинг обоих.
- Структурного логирования нет вообще.
- README по сервису нет.

### Тесты

Юнит-тесты на pytest + pytest-asyncio лежат в `services/auth/tests/`:
- `tests/unit/test_auth_service.py` — login/logout/check_role
- `tests/unit/test_user_service.py` — регистрация, get/patch user, валидация email
- `tests/unit/test_role_service.py` — добавление/удаление ролей
- `tests/unit/test_user_endpoints.py` — авторизация на уровне эндпоинта (регрессия IDOR-фикса)
- `tests/unit/test_auth_service.py` — в т.ч. `TestVerifyToken`: активный токен / отозванный

Зависимости настроек (`Settings` в `src/core/config.py`) читаются из переменных окружения без
`.env`-файла, поэтому `tests/conftest.py` выставляет дефолтные значения через `os.environ.setdefault(...)`
до импорта `src.*` — реальные Postgres/Redis для юнит-тестов не нужны, все внешние зависимости мокаются.

**Как запустить:**
```bash
cd services/auth
poetry install --with dev
poetry run pytest
poetry run ruff check .
```

**Окружение:** система на Ubuntu 26.04 идёт с Python 3.14 из коробки, а проект целится
в 3.12 (см. `Dockerfile`, `requires-python` в `pyproject.toml`) — под 3.14 у `pydantic-core`
пока нет везде готовых wheel-файлов, сборка из исходников падает. Поэтому локально
поставлен **pyenv** + Python 3.12.13, закреплён файлом `.python-version` в `services/auth/`
(`pyenv local 3.12.13`). pyenv уже инициализирован в `~/.bashrc`. `poetry env use python`
в этой директории подхватывает версию из `.python-version` через shim pyenv автоматически.

`poetry.toml` в `services/auth/` — `virtualenvs.in-project = true`, чтобы venv лежал в
`services/auth/.venv` и его было видно в IDE.

`pyproject.toml` — `package-mode = false` (под `[tool.poetry]`): проект — приложение,
а не библиотека для дистрибуции, отдельного пакета `auth/` с `__init__.py` на верхнем
уровне нет (код в `src/`). Без этой настройки `poetry install` падает с
`No file/folder found for package auth` (та же причина, по которой Dockerfile уже
использовал `poetry install --no-root`).

**Линтер:** добавлен `ruff` (dev-зависимость + конфиг `[tool.ruff]` в `pyproject.toml`,
правила `E, F, W, I, UP`, `line-length = 100`, `target-version = "py312"`). Прогнан с
`--fix` по всей кодовой базе сервиса — поймал лишние пробелы, неотсортированные импорты,
устаревший `Union[..., None]` вместо `... | None`, `datetime.timezone.utc` вместо `UTC`,
`class Roles(str, Enum)` вместо `StrEnum`. Все 26 тестов после этого по-прежнему проходят.

### Переменные окружения

Шаблон в [.env.sample](.env.sample) (корень репозитория). Для auth-service: `POSTGRESQL_*`,
`REDIS_HOST/PORT`, `JWT_*`, `AUTH_SUPERUSER_*`. Конфиг сервиса читает их через `pydantic-settings`
с префиксами (`postgresql_`, `redis_`, `jwt_`, `auth_superuser_`).

## CI

`.github/workflows/auth-ci.yml` — два джоба:
1. `lint-and-test` — Python 3.12, `poetry install --with dev`, `ruff check .`, `pytest`.
2. `docker-build` (зависит от первого) — `docker build services/auth`, без публикации
   образа куда-либо; цель — поймать ошибки в Dockerfile до мерджа (так нашлась бы опечатка
   `poerty_auth_builder`, которую обычные тесты не ловят).

Триггеры: `pull_request` в `main` и `push` в `feature/**`, `fix/**`, `infra/**`,
только при изменениях внутри `services/auth/**` или самого workflow-файла.
При появлении gallery/nginx/minio CI — заводить по аналогии отдельным workflow-файлом
с собственным path-фильтром, не расширять этот.

## Соглашения по работе

- Часть коммитов в истории на русском (например «Хэш паролей», «Валидация email») — это нормально
  для этого репозитория, не нужно навязывать английский.
- Подтверждай находки чтением кода напрямую, не доверяй слепо выводам саб-агентов при ревью —
  в этой сессии один из выводов саб-агента (мнимый async/await баг в `RedisDep`) оказался ложным
  при проверке вручную.
