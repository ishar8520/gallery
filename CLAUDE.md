# gallery

Онлайн-галерея: авторизованные пользователи хранят и просматривают свои фотографии.
Микросервисная архитектура, развёртывание через Docker Compose ([compose.yaml](compose.yaml)).

## Целевая архитектура

```
Browser / Mobile
       │
   [nginx]  ← единая точка входа, роутит по prefix
       ├── /auth    →  auth-service  (PostgreSQL + Redis)
       ├── /api     →  gallery-service  (PostgreSQL metadata + MinIO files)
       ├── /ugc     →  ugc-service  (ClickHouse analytics)
       ├── /minio/  →  minio:9000  (presigned URL proxy, Host: minio:9000)
       └── /        →  frontend-service

Kafka ──────── async шина событий
  ├── topic: mail-events  ← auth → mail-service
  └── topic: ugc-events   ← auth + gallery → ugc-service

Loki + Grafana ← structured logs от всех сервисов  (не начат)
```

## Сервисы — план и статус

| Сервис | Путь | Стек | Статус |
|---|---|---|---|
| auth | `services/auth` | FastAPI, SQLAlchemy async, PostgreSQL, Redis | ✅ разобран, тесты, CI |
| gallery | `services/gallery` | FastAPI, SQLAlchemy async, PostgreSQL, MinIO | ✅ разобран, тесты, CI |
| nginx | `services/nginx` | nginx 1.27-alpine, reverse proxy | ✅ образ заменён, MinIO proxy добавлен |
| minio | `services/minio` | minio/minio, S3-совместимое хранилище | ✅ образ заменён |
| mail | `services/mail` | FastAPI, aiokafka consumer, aiosmtplib | ✅ email-подтверждение, сброс пароля |
| frontend | `services/frontend` | Vue 3, Vite, Pinia, Vue Router, Axios | ✅ реализован, OAuth, сброс пароля |
| Kafka | — | Apache Kafka 3.9 (KRaft) | ✅ работает в compose |
| ugc | `services/ugc` | FastAPI, aiokafka consumer, clickhouse-connect | ✅ реализован |
| ClickHouse | — | clickhouse/clickhouse-server:24 | ✅ в compose |
| Loki | — | Grafana Loki + Promtail + Grafana | не начат |

**Порядок разработки:** auth ✅ → gallery ✅ → nginx ✅ → Kafka ✅ → frontend ✅ →
mail ✅ → ugc ✅ → Loki.

## Ключевые продуктовые решения (зафиксированы)

**gallery-service — модель данных:**
- Файлы хранятся в MinIO (S3), метаданные — в отдельной PostgreSQL gallery-service.
- Группировка фото = **папки/альбомы**: пользователь создаёт произвольные папки,
  перемещает фото между ними. Никакого автоматического распознавания/тегирования.
- Сортировка: по дате загрузки, дате на фото (EXIF), названию, размеру — на выбор пользователя.
- Авторизация запросов: gallery вызывает `GET /auth/api/v1/verify` с Bearer-токеном пользователя,
  получает `user_id + roles`, далее работает с данными этого пользователя.

**Presigned URLs для фото:**
- gallery-service генерирует presigned URL через MinIO SDK (TTL 1 час), подпись вычисляется
  для хоста `minio:9000` (Docker-internal).
- В URL хост переписывается на `localhost:8000/minio/...` (`MINIO_PUBLIC_HOST` env var).
- nginx проксирует `/minio/` → `minio:9000` с `Host: minio:9000` — подпись остаётся валидной.
- Без этого браузер получал бы URL с `minio:9000`, который недоступен снаружи Docker-сети.

**Kafka:**
- `mail-events` — auth (email-верификация, сброс пароля) → mail-service.
- `ugc-events` — gallery (просмотр, загрузка, удаление фото) → ugc-service (не начат).
- Назначение: если mail-service или ugc-service недоступны, события не теряются.

**Логирование:** Grafana Loki + Promtail (сборщик логов с контейнеров) + Grafana (UI).
Выбрано вместо ELK как более лёгкое решение. Loki не индексирует содержимое логов —
только метки (service, level), поиск по содержимому через grep-подобный LogQL.

**Личный кабинет:** фича фронта, не отдельный сервис. Данные профиля из auth-service,
фото и альбомы из gallery-service.

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

**Известный пробел:** для этой замены нет автоматического CI-чека — `.github/workflows/auth-ci.yml`
триггерится только на `services/auth/**` и не покрывает `compose.yaml`/`nginx`/`minio`. Проверка была
только ручной. Если правки в эту область будут продолжаться — стоит завести отдельный
workflow с собственным path-фильтром (например `compose.yaml`, `services/nginx/**`, `services/minio/**`),
аналогично `auth-ci.yml`.

## Auth-service

### Стек (актуален, без устаревших библиотек)
Python 3.12, FastAPI 0.115, Pydantic v2, SQLAlchemy 2.0 async + asyncpg, Alembic,
Redis (`redis.asyncio`), `async-fastapi-jwt-auth` (обёртка над PyJWT — **не** `python-jose`),
bcrypt напрямую (без passlib). Зависимости и сборка — Poetry.

Управление пользователем: регистрация с email-подтверждением, login/logout,
access+refresh JWT (cookie + header), роли USER/ADMIN, бутстрап суперюзера через Alembic-миграцию.
Межсервисный эндпоинт `GET /auth/api/v1/verify` — проверяет подпись JWT и отзыв токена
через Redis (для вызова из gallery-service и других сервисов).

### Эндпоинты

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| POST | `/auth/api/v1/registration` | Все | Регистрация (резервирует в Redis, шлёт email через Kafka) |
| GET/POST | `/auth/api/v1/confirm` | Все | Подтверждение email по токену |
| POST | `/auth/api/v1/login` | Все | Вход, возвращает access token |
| POST | `/auth/api/v1/logout` | Auth | Отзыв токена (Redis blacklist) |
| POST | `/auth/api/v1/refresh` | Cookie | Обновление access token |
| GET | `/auth/api/v1/me` | Auth | Профиль текущего пользователя |
| GET | `/auth/api/v1/verify` | Межсервисный | Проверка JWT (для gallery и других) |
| GET | `/auth/api/v1/user/{id}` | Auth | Получить пользователя |
| PATCH | `/auth/api/v1/user/{id}` | Auth/ADMIN | Изменить профиль (только свой или ADMIN) |
| DELETE | `/auth/api/v1/user/{id}` | ADMIN | Удалить пользователя |
| POST | `/auth/api/v1/user/{id}/password` | Auth (только свой) | Сменить пароль |
| GET | `/auth/api/v1/users` | ADMIN | Список всех пользователей с ролями |
| POST | `/auth/api/v1/role/{id}` | ADMIN | Назначить роль |
| DELETE | `/auth/api/v1/role/{id}` | ADMIN | Снять роль |

### Сделано в ходе ревью (2026-06-23, смержено: PR #8 `fix/auth-service-review`)

**Исправлено:**
- IDOR в `PATCH /user/{user_id}` — добавлена проверка владельца/ADMIN.
- SQL без параметризации в `downgrade()` миграции `192db30b56b4_add_admin.py`.
- Опечатка `poerty_auth_builder` → `poetry_auth_builder` в Dockerfile.
- Мёртвый код, неверный PYTHONPATH, грамматика в текстах ошибок.
- Добавлены unit-тесты на pytest: `services/auth/tests/`.

**Добавлено в ветке `infra/frontend`:**
- `GET /auth/api/v1/users` — список всех пользователей (ADMIN only), с eager-load ролей.
- `POST /auth/api/v1/user/{id}/password` — смена пароля (только свой аккаунт).
- Модели `ResponseUserAdmin`, `RequestChangePassword`.
- Регистрация с email-подтверждением через Kafka (было заложено, доведено до рабочего состояния).

**Сознательно отложено:**
- Сброс пароля (`forgot-password` / `reset-password`) — в работе в текущей ветке.
- Rate limiting / lockout на login — отсутствует (риск брутфорса).
- `authjwt_cookie_csrf_protect=False` при cookie-based JWT — требует CSRF-токен на клиенте.
- Healthcheck без реальной проверки Postgres и Redis.
- Структурное логирование.

### Тесты

31 юнит-тест в `services/auth/tests/`:
- `tests/unit/test_auth_service.py` — login/logout/check_role, verify token (активный/отозванный)
- `tests/unit/test_user_service.py` — регистрация, get/patch/delete user, валидация email, смена пароля
- `tests/unit/test_role_service.py` — добавление/удаление ролей
- `tests/unit/test_user_endpoints.py` — авторизация на уровне эндпоинта (регрессия IDOR-фикса)

**Как запустить:**
```bash
cd services/auth
poetry install --with dev
poetry run pytest
poetry run ruff check .
```

**Окружение:** система на Ubuntu 26.04 идёт с Python 3.14 из коробки, а проект целится
в 3.12. Поставлен **pyenv** + Python 3.12.13, закреплён файлом `.python-version` в `services/auth/`.
`poetry.toml` — `virtualenvs.in-project = true`.

### Переменные окружения

Шаблон в [.env.sample](.env.sample). Для auth-service: `POSTGRESQL_*`,
`REDIS_HOST/PORT`, `JWT_*`, `AUTH_SUPERUSER_*`. Конфиг читает через `pydantic-settings`
с префиксами (`postgresql_`, `redis_`, `jwt_`, `auth_superuser_`).

## CI

`.github/workflows/auth-ci.yml` — два джоба:
1. `lint-and-test` — Python 3.12, `poetry install --with dev`, `ruff check .`, `pytest`.
2. `docker-build` (зависит от первого) — `docker build services/auth`.

Триггеры: `pull_request` в `main` и `push` в `feature/**`, `fix/**`, `infra/**`,
только при изменениях внутри `services/auth/**` или самого workflow-файла.
При появлении CI для других сервисов — заводить отдельным workflow-файлом с собственным
path-фильтром, не расширять этот.

## Gallery-service

### Стек
Python 3.12, FastAPI 0.115, Pydantic v2, SQLAlchemy 2.0 async + asyncpg, Alembic,
httpx (межсервисный вызов `/auth/api/v1/verify`), minio (официальный SDK, blocking calls
обёрнуты в `asyncio.to_thread`), Pillow (EXIF-дата из JPEG).

Аутентификация: gallery не использует JWT-библиотеку — читает `Authorization` header и
пробрасывает его в auth-service. `CurrentUserDep` вызывает `GET /auth/api/v1/verify`,
получает `user_id + roles`.

### Presigned URLs

`ResponsePhoto` содержит поле `url: str | None` — presigned URL с TTL 1 час.
Генерируется при листинге через `asyncio.gather` (параллельно для всех фото).

Хост в URL переписывается: `minio:9000` → `{MINIO_PUBLIC_HOST}/minio/...`.
nginx проксирует `/minio/` → `minio:9000` с `proxy_set_header Host minio:9000`,
благодаря чему AWS-подпись остаётся валидной. `MINIO_PUBLIC_HOST` по умолчанию `localhost:8000`.

### Текущие допущения (технический долг)

- **httpx AsyncClient и MinioClient** создаются на каждый запрос — правильно singleton через lifespan.
- **Rate limiting на upload** отсутствует.
- **Пагинация** через `limit`/`offset`, cursor-based эффективнее при больших объёмах.
- **NULLS при сортировке по `exif_date`** — нет явного `NULLS LAST/FIRST`.

### Тесты

31 юнит-тест в `services/gallery/tests/`:
- `test_photo_service.py` — EXIF-парсинг, upload, list (пагинация, `no_album` фильтр), presigned URL, move, delete
- `test_album_service.py` — create, get, rename, delete
- `test_auth_dep.py` — missing token, valid token, auth-service error

**Как запустить:**
```bash
cd services/gallery
.venv/bin/pytest
.venv/bin/ruff check .
```

### Переменные окружения

Шаблон в [.env.sample](.env.sample). Для gallery-service: `GALLERY_POSTGRESQL_*`,
`MINIO_HOST/PORT/USER/PASSWORD/PUBLIC_HOST`. Читаются через `pydantic-settings`.

## Mail-service

### Стек
Python 3.12, FastAPI 0.115, aiokafka (consumer), aiosmtplib (SMTP), httpx (link-service).

### Архитектура

FastAPI-приложение с Kafka consumer в фоновой задаче (запускается через lifespan).
Consumer слушает топик `mail-events`, десериализует JSON и делегирует `MailService`.

**Поток email-подтверждения:**
1. auth-service публикует `email_confirmation_requested` → `mail-events`
2. mail-service consumer получает событие
3. `MailService.send_confirmation_email` запрашивает короткую ссылку у link-service
4. При недоступности link-service fallback на полный URL
5. Письмо уходит через aiosmtplib (локально — MailHog на порту 8025)

**Формат события:**
```json
{
  "event_type": "email_confirmation_requested",
  "timestamp": "2026-07-09T...",
  "payload": { "token": "...", "username": "...", "email": "..." }
}
```

Ссылка в письме: `{AUTH_PUBLIC_URL}/confirm?token={token}` → Vue-страница `/confirm` →
ConfirmView.vue → `POST /auth/api/v1/confirm`.

### Статус

✅ Реализовано:
- Kafka consumer (`mail-events`)
- `send_confirmation_email` с fallback на full URL
- Тесты: `TestHandleEvent` (3 кейса), `TestMailService` (2 кейса)

🔄 В работе:
- `password_reset_requested` event handling
- `send_reset_password_email`

### Как запустить тесты
```bash
cd services/mail
poetry install --with dev
poetry run pytest
poetry run ruff check .
```

### Переменные окружения
`KAFKA_BOOTSTRAP_SERVERS`, `SMTP_HOST/PORT/FROM_EMAIL`, `LINK_SERVICE_URL`, `AUTH_PUBLIC_URL`.
Все заданы в `compose.yaml`, для локального запуска значения по умолчанию в `src/core/config.py`.

## Frontend-service

### Стек
Vue 3 (Composition API, `<script setup>`), Vite 5, Pinia, Vue Router 4, Axios.
Собирается в статику, раздаётся nginx внутри контейнера (`services/frontend/nginx.conf`).

### Реализованные страницы

| Маршрут | Компонент | Описание |
|---|---|---|
| `/login` | `LoginView.vue` | Вход |
| `/register` | `RegisterView.vue` | Регистрация с валидацией (латиница, спецсимволы) |
| `/confirm` | `ConfirmView.vue` | Подтверждение email по токену из query |
| `/gallery` | `GalleryView.vue` | Основная галерея |
| `/photo/:id` | `PhotoView.vue` | Просмотрщик фото с filmstrip и клавиатурной навигацией |
| `/profile` | `ProfileView.vue` | Профиль пользователя |
| `/change-password` | `ChangePasswordView.vue` | Смена пароля |
| `/admin` | `AdminView.vue` | Панель администратора (только ADMIN) |

### Ключевые решения

**Токен в памяти** — access token хранится в `tokenRef` (не localStorage), не уязвим к XSS.
Refresh token — HttpOnly cookie, не доступен из JS.

**Refresh логика** — axios interceptor при 401 делает один refresh, ставит остальные запросы
в очередь (`refreshQueue`). После успеха все запросы повторяются с новым токеном.
Эндпоинты `/me`, `/refresh`, `/login` исключены из retry (NO_REFRESH) чтобы не зациклиться.

**Групповое выделение** — `selectedIds: ref(new Set())`. Создаётся новый Set при каждом
изменении (для реактивности). Bulk delete/move через `Promise.all`.

**Фотографии** — в ответе `/api/v1/photos` уже содержится `url` (presigned). Отдельного
запроса за URL не нужно. `PhotoCard` использует `photo.url` напрямую.

### Цветовая схема (тёмная тема)
```css
--primary:    #66FCF1  /* бирюзовый акцент, кнопки */
--bg:         #0B0C10  /* фон страницы */
--surface:    #1F2833  /* карточки, сайдбар, модалки */
--text:       #C5C6C7  /* основной текст */
--text-muted: #45A29E  /* второстепенный текст */
--border:     #2e3d4f
--danger:     #fc4545
```

### Как запустить локально
```bash
cd services/frontend
npm install
npm run dev   # http://localhost:5173
```
В production собирается и раздаётся через nginx-контейнер в compose.

## Nginx

Конфиг: [services/nginx/conf/server.conf](services/nginx/conf/server.conf).
Слушает порт 8080, снаружи доступен на 8000.

| Location | Upstream | Примечания |
|---|---|---|
| `/auth` | `auth-service:8000` | — |
| `/api` | `gallery-service:8000` | — |
| `/link`, `/s/` | `link-service:8000` | Короткие ссылки |
| `/minio/` | `minio:9000` | `Host: minio:9000` — обязателен для валидности presigned URL подписи |
| `/` | `frontend:80` | Vue SPA |

## Соглашения по работе

- Часть коммитов в истории на русском — это нормально для этого репозитория.
- Подтверждай находки чтением кода напрямую, не доверяй слепо выводам саб-агентов при ревью.
- Тесты запускать перед PR. Линтер (`ruff check .`) — обязательно.
- node_modules фронтенда попали в diff — добавить `services/frontend/node_modules/` в `.gitignore`.
