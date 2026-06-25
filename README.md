# Sandbox Connection Pool API

FastAPI-сервис для экспериментов с пулом соединений PostgreSQL.
Проект помогает сравнивать разные шаблоны запросов (последовательные и параллельные, с транзакцией и без) и наблюдать поведение SQLAlchemy + PgBouncer под нагрузкой.

## Основные возможности

- **Полигон для пула соединений**: API-эндпоинты для моделирования различных сценариев работы с БД.
- **Транзакционные сценарии**: сравнение режимов с транзакцией и без транзакции.
- **Режимы сессий**: тесты в вариантах `in-session` и `out-session`.
- **Автозаполнение и очистка данных**: создание и удаление тестовых авторов/книг для повторяемых экспериментов.
- **Утилиты здоровья сервиса**: базовые health-check эндпоинты приложения и базы данных.

---

## Запуск проекта через Docker Compose

### Быстрый старт

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/yooshark/sandbox-connection-pool.git
   cd sandbox-connection-pool
   ```

2. **Создайте файл `.env`** в корне проекта.

3. **Поднимите PostgreSQL + PgBouncer**:
   ```bash
   docker compose up -d
   ```

4. **Установите Python-зависимости**:
   ```bash
   poetry install
   ```

5. **Примените миграции**:
   ```bash
   alembic upgrade head
   ```

6. **Запустите API**:
   ```bash
   python src/run.py
   ```

---

## Локальная разработка (без Docker)

Если хотите запускать инфраструктуру и приложение полностью локально:

1. **Создайте и активируйте виртуальное окружение** (опционально, если используете окружение Poetry):
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

2. **Установите зависимости**:
   ```bash
   poetry install
   ```

3. **Настройте окружение**:
   Создайте `.env` и укажите параметры подключения к PostgreSQL.

4. **Примените миграции**:
   ```bash
   alembic upgrade head
   ```

5. **Запустите сервер**:
   ```bash
   python src/run.py
   ```

---

## Переменные окружения

Минимальный пример `.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sandbox-connection-pool
DB_USER=postgres
DB_PASSWORD=postgres
DB_DRIVER=psycopg
DB_ECHO=False
DB_TIMEOUT=5

# SQLAlchemy connection pool
CONN_POLL_POOL_SIZE=40
CONN_POLL_MAX_OVERFLOW=0
CONN_POLL_POOL_TIMEOUT=30
CONN_POLL_POOL_RECYCLE=3600

# App
APP_DEBUG=True
APP_LOG_LEVEL=INFO
APP_USE_PGBOUNCER_CONN_POOL=False
APP_PAYMENT_FAILURE_RATE=0.1
APP_DOMESTIC_FAILURE_RATE=0.01
APP_SESSION_NUMBERS=[2,3,4]
APP_PAYMENT_DELAYS=[2,3,5,9,10]
APP_DOMESTIC_DELAYS=[2,3,5,9,10]
APP_DEFAULT_PROCESS_DELAYS=[2,3,5,9,10]
```

> Если используете PgBouncer из `docker-compose.yml`, укажите для приложения `DB_PORT=6432`, чтобы подключение шло через PgBouncer.

---

## Обзор API

Базовый URL: `http://localhost:8000`

- **Документация**: `http://localhost:8000/api/docs` (доступна при `APP_DEBUG=true`)
- **Проверка сервиса**: `GET /api/utils/health-check/`
- **Проверка БД**: `GET /api/utils/health-check/test-db`
- **Авторы**: `GET /api/authors/`, `POST /api/authors/`
- **Книги**: `GET /api/books/`, `POST /api/books/`
- **Book Payments**: маршруты `/api/book-payments/...` для seed и нагрузочных сценариев

### Группы сценариев Book Payment

- `in-session/transaction`
- `in-session/no-transaction`
- `out-session/transaction`
- `out-session/no-transaction`

В каждой группе доступны:

- `GET /` (одиночный запуск)
- `POST /sequential`
- `POST /parallel`

---

## Заполнение тестовыми данными

Создать авторов и книги:

```bash
curl -X POST "http://localhost:8000/api/book-payments/seed/" \
  -H "Content-Type: application/json" \
  -d '{"authors_count": 100, "books_per_author": 10}'
```

Очистить seeded-данные:

```bash
curl -X DELETE "http://localhost:8000/api/book-payments/seed/"
```

---

## Полезные команды

```bash
# Поднять только инфраструктуру
docker compose up -d

# Посмотреть логи
docker compose logs -f postgres
docker compose logs -f pgbouncer

# Остановить инфраструктуру
docker compose down

# Остановить и удалить volumes (полная очистка БД)
docker compose down -v

# Запуск приложения напрямую через uvicorn
uvicorn src.main.web:create_app --host localhost --port 8000 --factory
```

---

## Структура проекта

```text
src/
  infra/postgres/        # SQLAlchemy-модели, DB engine, миграции, storage
  main/                  # Конфигурация приложения, FastAPI factory, инициализация роутеров
  modules/               # Доменные роутеры/контроллеры (authors, books, book_payment, utils)
  run.py                 # Точка входа для локального запуска
```

---

## Примечания

- По умолчанию `src/run.py` запускает Uvicorn с `workers=2`.
- В `docker-compose.yml` PgBouncer настроен в режиме `transaction`.
- Репозиторий предназначен как sandbox для экспериментов и тюнинга пула соединений.
