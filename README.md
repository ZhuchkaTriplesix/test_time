# Сервис контроля времени ответа (SLA Service)

Сервис для отслеживания времени первой реакции сотрудников на клиентские обращения, мониторинга нарушений SLA (пороговые статусы `warning` и `overdue`) и вычисления операционных метрик.

---

## 🏗 Структура проекта и архитектура

Проект спроектирован по принципу **модульной чистой архитектуры (Vertical Slice / Feature-Driven Architecture)**, обеспечивающей строгое разделение ответственности между HTTP-слоем, бизнес-логикой и доступом к данным.

```
test_time/
├── .agents/                      # Правила и конфигурации для AI-агентов
│   └── rules/
│       └── gitflow.md            # Стандарты ветвления GitFlow и правила коммитов
├── backend/                      # FastAPI Backend API сервис
│   ├── docker/
│   │   ├── Dockerfile            # Контейнеризация бэкенда
│   │   └── entrypoint.sh         # Скрипт ожидания БД, применения миграций Alembic и запуска
│   ├── src/
│   │   ├── configuration/        # Фабрика приложения FastAPI, CORS, middleware
│   │   │   ├── __init__.py
│   │   │   └── app.py
│   │   ├── database/             # Слой работы с БД (SQLAlchemy 2.0 async + Alembic)
│   │   │   ├── alembic/          # Миграции схемы базы данных
│   │   │   │   ├── versions/
│   │   │   │   └── env.py
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Базовый декларативный класс ORM
│   │   │   ├── core.py           # Инициализация AsyncEngine и пула соединений
│   │   │   └── dependencies.py   # FastAPI Dependency Injection для сессий AsyncSession
│   │   ├── middlewares/          # HTTP Middlewares (управление сессиями, логирование)
│   │   │   ├── __init__.py
│   │   │   └── database.py
│   │   ├── routers/              # Модульные доменные роутеры (Feature-driven)
│   │   │   ├── __init__.py       # Регистрация всех роутеров в приложении
│   │   │   ├── root/             # Системные маршруты и Health Check (/health)
│   │   │   │   ├── actions.py    # Логика проверки готовности сервисов
│   │   │   │   ├── router.py     # Эндпоинты проверки здоровья
│   │   │   │   └── schemas.py    # DTO схемы ответа
│   │   │   ├── events/           # Фича приёма внешних событий (/api/events)
│   │   │   │   ├── actions.py    # Бизнес-сценарий идемпотентного приёма сообщений
│   │   │   │   ├── dal.py        # Запросы INSERT ... ON CONFLICT DO NOTHING
│   │   │   │   ├── models.py     # Модель Event
│   │   │   │   ├── router.py     # Контроллер POST /api/events
│   │   │   │   └── schemas.py    # DTO входящих событий
│   │   │   ├── tickets/          # Фича открытых обращений (/api/tickets)
│   │   │   │   ├── actions.py    # Бизнес-логика списка и фильтрации тикетов
│   │   │   │   ├── dal.py        # Выборка обращений с вычислением времени ожидания
│   │   │   │   ├── models.py     # Модель Ticket
│   │   │   │   ├── router.py     # Контроллер GET /api/tickets
│   │   │   │   └── schemas.py    # DTO обращений и SLA статусов
│   │   │   └── metrics/          # Фича аналитики и метрик (/api/metrics)
│   │   │       ├── actions.py    # Бизнес-логика агрегации
│   │   │       ├── dal.py        # Аналитические SQL-запросы (percentile_cont(0.5))
│   │   │       ├── router.py     # Контроллер GET /api/metrics
│   │   │       └── schemas.py    # DTO аналитических показателей
│   │   ├── services/             # Интеграционные адаптеры (уведомления, шины)
│   │   │   ├── __init__.py
│   │   │   └── notifications.py  # Адаптер отправки алертов
│   │   ├── config.py             # Централизованная типизированная конфигурация (.env)
│   │   ├── dependencies.py       # Глобальные зависимости FastAPI
│   │   ├── main.py               # Точка входа ASGI (Uvicorn / Granian)
│   │   └── schemas.py            # Общие Pydantic DTO
│   ├── tests/                    # Набор автоматических тестов (pytest, pytest-asyncio)
│   │   ├── conftest.py           # Фикстуры тестовой БД и асинхронного HTTP клиента
│   │   ├── test_idempotency.py   # Тест параллельной дедупликации (20 запросов)
│   │   ├── test_concurrency.py   # Тест неблокирующего Event Loop
│   │   ├── test_sla.py           # Тест логики SLA и защиты от повторных алертов
│   │   ├── test_atomicity.py     # Тест атомарности при сбоях
│   │   └── test_metrics.py       # Тест расчета медианы и метрик на пустых/заполненных данных
│   ├── alembic.ini               # Конфигурация миграций Alembic
│   ├── pyproject.toml / requirements.txt # Зависимости бэкенда
│   └── ruff.toml                 # Настройки линтера
├── worker/                       # Выделенный фоновый воркер (Background Processor)
│   ├── docker/
│   │   └── Dockerfile            # Контейнеризация воркера
│   └── src/
│       ├── __init__.py
│       ├── main.py               # Точка входа воркера
│       ├── outbox_processor.py   # Обработка outbox (SELECT FOR UPDATE SKIP LOCKED)
│       └── sla_sweeper.py        # Периодическая проверка SLA порогов (60с / 180с)
├── frontend/                     # Реактивный веб-интерфейс (React + Vite)
│   ├── docker/
│   │   ├── Dockerfile            # Multi-stage сборка Nginx + Static SPA
│   │   └── nginx.conf            # Конфигурация Nginx и проксирование API
│   ├── src/                      # Исходный код SPA интерфейса
│   │   ├── components/           # UI-компоненты (MetricsPanel, TicketTable, FilterBar)
│   │   ├── App.jsx               # Корневой компонент с поллингом 10-15 сек
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .env.example                  # Шаблон переменных окружения
├── .gitignore                    # Игнорируемые файлы (секреты, docs, артефакты)
├── CONTRIBUTING.md               # Руководство по GitFlow и конвенции коммитов
├── docker-compose.yml            # Локальное развертывание всех сервисов
├── Makefile                      # Команды сборки, запуска и тестирования
└── README.md                     # Документация проекта
```

---

## 🏛 Разделение ответственности слоёв (Feature Module)

Каждый функциональный модуль внутри `src/routers/<feature>/` содержит:

1. **`router.py` (Transport / HTTP Layer)**:
   - Прием HTTP-запроса, валидация входных данных через Pydantic.
   - Вызов прикладного действия из `actions.py`.
   - Формирование корректного HTTP-ответа и статус-кода (`201 Created`, `200 OK`, `400 Bad Request`).
   - *Прямой доступ к SQL и сложная бизнес-логика здесь запрещены.*

2. **`actions.py` (Business Logic / Use Case Layer)**:
   - Реализация доменных сценариев и бизнес-правил (создание обращения, закрытие ответа сотрудника, перевод статуса SLA).
   - Управление транзакционными границами (`async with session.begin()`).
   - Оркестрация вызовов DAL и адаптеров уведомлений.

3. **`dal.py` (Data Access Layer)**:
   - Прямое взаимодействие с базой данных через SQLAlchemy 2.0.
   - Оптимизированные запросы:
     - `INSERT INTO events ... ON CONFLICT (external_event_id) DO NOTHING` для идемпотентности.
     - `SELECT ... FOR UPDATE SKIP LOCKED` для безопасной фоновой выборки Outbox.
     - `func.percentile_cont(0.5).within_group(...)` для вычисления медианы на уровне СУБД.

4. **`models.py` (Persistence Model)**:
   - Описание реляционной схемы таблиц базы данных (SQLAlchemy Declarative Models).

5. **`schemas.py` (DTO Data Transfer Objects)**:
   - Контракты данных запросов и ответов (Pydantic models).

---

## 🚀 Быстрый старт

### 1. Требования
- Docker & Docker Compose
- Make (опционально)

### 2. Запуск проекта одной командой
```bash
# Скопировать переменные окружения
cp .env.example .env

# Собрать и запустить все сервисы (PostgreSQL, Backend API, Worker, Frontend)
make up
# или
docker compose up --build -d
```

Сервисы будут доступны по адресам:
- **Веб-интерфейс**: [http://localhost:3000](http://localhost:3000)
- **API документация (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Запуск тестов

Тестирование осуществляется с помощью `pytest` в изолированном асинхронном окружении:

```bash
# Запуск тестов внутри Docker контейнера
make test
# или локально:
pytest -v
```

---

## ⚙️ Конфигурация (.env)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `POSTGRES_VERSION` | Версия образа PostgreSQL | `17-alpine` |
| `POSTGRES_USER` | Пользователь БД | `postgres` |
| `POSTGRES_PASSWORD` | Пароль БД | `postgres` |
| `POSTGRES_DB` | Имя базы данных | `tickets_db` |
| `DATABASE_URL` | Async URL подключения к БД | `postgresql+asyncpg://postgres:postgres@db:5432/tickets_db` |
| `SLA_WARNING_SECONDS` | Порог SLA для статуса Warning | `60` |
| `SLA_OVERDUE_SECONDS` | Порог SLA для статуса Overdue | `180` |
| `API_PORT` | Порт API сервиса | `8000` |
| `FRONTEND_PORT` | Порт веб-интерфейса | `3000` |
| `WORKER_POLL_INTERVAL_SECONDS` | Интервал выборки Outbox воркером | `2` |
| `SLA_SWEEPER_INTERVAL_SECONDS` | Интервал проверки SLA сборщиком | `5` |
