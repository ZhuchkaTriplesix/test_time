# Сервис контроля времени ответа (SLA Response Time Control Service)

Сервис для операционных команд, отслеживающий время первой реакции сотрудников на клиентские обращения, фиксирующий нарушения SLA (пороговые статусы `warning` и `overdue`) и вычисляющий показатели эффективности.

---

## 🏗 Архитектура и структура репозитория

Проект спроектирован по принципу **модульной чистой архитектуры (Vertical Slice / Feature-Driven Architecture)**, обеспечивающей строгое разделение ответственности между HTTP-слоем, бизнес-логикой и доступом к данным.

```
test_time/
├── .agents/                      # Правила и конфигурации для AI-агентов (GitFlow)
├── backend/                      # FastAPI Backend API сервис
│   ├── docker/
│   │   ├── Dockerfile            # Контейнеризация бэкенда
│   │   └── entrypoint.sh         # Скрипт ожидания БД, применения миграций Alembic и запуска
│   ├── src/
│   │   ├── configuration/        # Фабрика приложения FastAPI, CORS, middleware
│   │   ├── database/             # Слой работы с БД (SQLAlchemy 2.0 async + Alembic)
│   │   ├── middlewares/          # HTTP Middlewares (логирование, время обработки)
│   │   ├── routers/              # Доменные модули (root, events, tickets, metrics)
│   │   │   ├── events/           # POST /api/events (ON CONFLICT DO NOTHING)
│   │   │   ├── tickets/          # GET /api/tickets (динамический SLA)
│   │   │   ├── metrics/          # GET /api/metrics (percentile_cont(0.5))
│   │   │   └── root/             # GET /health (Liveness/Readiness probe)
│   │   ├── services/             # Адаптеры нотификаций
│   │   ├── config.py             # Централизованная типизированная конфигурация (.env)
│   │   └── main.py               # Точка входа ASGI
│   ├── tests/                    # Автоматические тесты pytest-asyncio
│   │   ├── test_idempotency.py   # 20 параллельных одинаковых событий (идемпотентность)
│   │   ├── test_concurrency.py   # Неблокирующий Event Loop при задержках
│   │   ├── test_sla.py           # Логика SLA и защита от дубликатов алертов
│   │   ├── test_atomicity.py     # Атомарность транзакций и откат при сбоях
│   │   └── test_metrics.py       # Расчет метрик и медианы (включая пустую выборку)
│   ├── alembic.ini               # Конфигурация миграций
│   └── requirements.txt          # Зависимости
├── worker/                       # Выделенный фоновый воркер
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── src/
│       ├── main.py               # Точка входа воркера
│       ├── outbox_processor.py   # Transactional Outbox (SELECT FOR UPDATE SKIP LOCKED)
│       ├── sla_sweeper.py        # Периодическая проверка SLA порогов (60с / 180с)
│       ├── notifications.py      # Адаптер отправки уведомлений
│       └── models.py
├── frontend/                     # Реактивный веб-интерфейс (React + Vite)
│   ├── docker/
│   │   ├── Dockerfile            # Multi-stage сборка Nginx + Static SPA
│   │   └── nginx.conf            # Проксирование API
│   ├── src/                      # UI компоненты (MetricsPanel, TicketTable, FilterBar)
│   ├── index.html
│   └── package.json
├── scripts/
│   └── seed.py                   # Демонстрационный скрипт сидирования событий
├── .env.example                  # Шаблон переменных окружения
├── .gitignore                    # Игнорируемые файлы (секреты, docs, артефакты)
├── CONTRIBUTING.md               # Руководство по GitFlow и конвенции коммитов
├── DEMO.md                       # Инструкция по проверке обязательных сценариев
├── docker-compose.yml            # Развертывание всех сервисов (PostgreSQL 17, API, Worker, Frontend)
├── Makefile                      # Команды управления, сборки и тестирования
└── ruff.toml                     # Конфигурация линтера и форматтера
```

---

## 📋 Контракты API (Примеры JSON)

### 1. Событие сообщения клиента (`client`)
Создает новое обращение в системе.

```json
{
  "external_event_id": "evt_client_20260814_001",
  "event_type": "client",
  "received_at": "2026-08-14T10:00:00Z",
  "external_client_id": "tg_user_8912",
  "topic": "Техническая поддержка",
  "content": "Не могу зайти в личный кабинет через мобильное приложение.",
  "payload": {
    "channel": "telegram",
    "app_version": "2.4.1"
  }
}
```

### 2. Событие ответа сотрудника (`agent`)
Закрывает обращение и фиксирует итоговое время первой реакции.

```json
{
  "external_event_id": "evt_agent_20260814_002",
  "event_type": "agent",
  "received_at": "2026-08-14T10:01:15Z",
  "ticket_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "content": "Здравствуйте! Ваш профиль разблокирован, проверьте доступ.",
  "payload": {
    "agent_id": "agent_anna_12"
  }
}
```

---

## 🚀 Быстрый старт

### Развертывание в Docker:
```bash
# 1. Скопировать переменные окружения
cp .env.example .env

# 2. Собрать и запустить все сервисы (PostgreSQL, Backend API, Worker, Frontend)
make up
# или: docker compose up --build -d

# 3. Заполнить демонстрационными данными (опционально)
python scripts/seed.py
```

### Адреса сервисов:
- **Веб-интерфейс**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Документация (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Запуск тестов

Тестирование осуществляется с помощью `pytest` в изолированном асинхронном окружении:

```bash
# Запуск внутри контейнера:
make test

# Локальный запуск:
uv run pytest backend/tests -v
```

---

## 📈 Архитектурное развитие для Production (Highload & Интеграции)

При росте нагрузки и подключении десятков внешних систем (CRM, Helpdesk, Telegram, Email, Slack):

1. **Change Data Capture (CDC) вместо polling Outbox**:
   - При тысячах событий в секунду опрос таблицы `outbox_events` через `SKIP LOCKED` увеличит нагрузку на дисковую подсистему и менеджер блокировок.
   - Переход на **Debezium + Apache Kafka**: Debezium читает WAL-лог PostgreSQL и асинхронно передает события в топики Kafka, откуда независимые воркеры отправляют уведомления.
2. **Аналитическое хранилище для метрик (ClickHouse)**:
   - Расчет перцентилей `percentile_cont` на терабайтных объемах данных требует существенных ресурсов CPU на сортировку.
   - Для высоконагруженной аналитики данные реплицируются в **ClickHouse**, обеспечивающий расчет медианы и перцентилей за миллисекунды.
3. **Read Replicas для операционных запросов**:
   - Разделение пула соединений: мастер-нода обрабатывает `INSERT ... ON CONFLICT DO NOTHING`, а асинхронные реплики PostgreSQL обслуживают `GET /api/tickets`.
