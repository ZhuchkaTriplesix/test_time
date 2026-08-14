# Сервис контроля времени ответа (SLA Response Time Control Service)

Высоконагруженный сервис для операционных команд и клиентской поддержки, отслеживающий время первой реакции сотрудников на клиентские обращения, непрерывно контролирующий соблюдение SLA (пороговые уровни `normal`, `warning`, `overdue`), генерирующий гарантированные алерты через Transactional Outbox и рассчитывающий P50-медиану времени ответа непосредственно в СУБД.

---

## 📌 Основные возможности

* **Атомарный и идемпотентный прием событий (`POST /api/events`)**:
  * Защита от дубликатов на уровне ядра PostgreSQL через `ON CONFLICT (external_event_id) DO NOTHING`.
  * Создание обращений по клиентским событиям (`client`) и закрытие тикетов с фиксацией времени первого ответа при ответах сотрудников (`agent`).
* **Контроль порогов SLA**:
  * `NORMAL` (время ожидания $\le$ 60 секунд) — штатный режим.
  * `WARNING` (время ожидания > 60 секунд) — предварительное предупреждение.
  * `OVERDUE` (время ожидания > 180 секунд) — критическое нарушение SLA.
* **Надежная доставка алертов (Transactional Outbox & SKIP LOCKED)**:
  * Изменение статуса тикета и создание записи в `outbox_events` выполняются в **единой транзакции БД**.
  * Фоновый воркер забирает события через `SELECT ... FOR UPDATE SKIP LOCKED`, обеспечивая бесконфликтное горизонтальное масштабирование реплик воркера.
  * Экспоненциальный бэкофф (`2 ** attempts`) при сбоях внешней системы доставки и Dead-Letter статус (`failed`) при превышении лимита попыток.
* **Аналитические метрики в СУБД (`GET /api/metrics`)**:
  * Точный расчет медианы времени первого ответа (P50 / TTFR) через `func.percentile_cont(0.5)` в PostgreSQL без передачи строк в память приложения.
* **Операционный веб-интерфейс (React + Vite + Nginx)**:
  * Живой мониторинг очереди обращений с таймерами ожидания в реальном времени.
  * Фильтрация по направлениям (Topic) со счетчиками.
  * Быстрый и удобный интерфейс ответа оператора с готовыми шаблонами (Canned Responses), поддержкой горячих клавиш (`Ctrl + Enter` / `⌘ + Enter`) и всплывающими уведомлениями (Toasts).
  * Фоновый опрос каждые 10 секунд с возможностью ручной паузы и принудительного обновления.

---

## 🏗 Архитектура и структура репозитория

Проект спроектирован по принципу **модульной чистой архитектуры (Vertical Slice / Feature-Driven Architecture)**, обеспечивающей строгое разделение ответственности между HTTP-слоем, бизнес-логикой и доступом к данным.

```
test_time/
├── .agents/                      # Правила и регламенты разработки для AI-агентов (GitFlow)
├── .github/                      # CI/CD пайплайны GitHub Actions
│   └── workflows/
│       └── ci.yaml               # Проверка Ruff lint, автотесты PostgreSQL 17, сборка Vite и Compose
├── backend/                      # FastAPI Backend API сервис
│   ├── docker/
│   │   ├── Dockerfile            # Контейнеризация бэкенда (Python 3.11-slim)
│   │   └── entrypoint.sh         # Скрипт ожидания БД, применения миграций Alembic и запуска Uvicorn
│   ├── src/
│   │   ├── configuration/        # Фабрика приложения FastAPI, CORS, обработчики ошибок
│   │   ├── database/             # Слой работы с БД (SQLAlchemy 2.0 async + asyncpg + Alembic)
│   │   ├── middlewares/          # HTTP Middlewares (замер времени обработки, логирование)
│   │   ├── routers/              # Доменные модули (Vertical Slices)
│   │   │   ├── events/           # POST /api/events (идемпотентный инжест событий)
│   │   │   ├── tickets/          # GET /api/tickets (очередь с динамическим SLA)
│   │   │   ├── metrics/          # GET /api/metrics (P50-медиана и счетчики)
│   │   │   ├── outbox/           # Модели и статусы Transactional Outbox
│   │   │   └── root/             # GET /health (Liveness/Readiness probe)
│   │   ├── services/             # Сервисные адаптеры нотификаций
│   │   ├── config.py             # Централизованная типизированная конфигурация (.env)
│   │   └── main.py               # Точка входа ASGI приложения
│   ├── tests/                    # Полный набор автотестов pytest-asyncio (13 тестов)
│   │   ├── test_idempotency.py   # 20 параллельных одинаковых событий (дедупликация)
│   │   ├── test_concurrency.py   # Неблокирующий Event Loop при задержках алертов
│   │   ├── test_sla.py           # Логика порогов SLA и защита от дубликатов
│   │   ├── test_atomicity.py     # Атомарность транзакций и откат при сбоях
│   │   ├── test_metrics.py       # Расчет метрик и P50 медианы (пустая и заполненная БД)
│   │   ├── test_outbox_worker.py # Фоновая доставка Outbox, retry и failure handling
│   │   └── test_api_validation_and_errors.py # Валидация схем, 404/400 ошибки, healthcheck
│   ├── alembic.ini               # Конфигурация миграций БД
│   └── requirements.txt          # Зависимости проекта
├── worker/                       # Выделенный сервис фонового воркера
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── src/
│       ├── main.py               # Точка входа воркера (Graceful Shutdown)
│       ├── outbox_processor.py   # Обработчик Outbox (SELECT FOR UPDATE SKIP LOCKED)
│       ├── sla_sweeper.py        # Периодический сканер SLA порогов (60с / 180с)
│       ├── notifications.py      # Адаптер отправки уведомлений
│       └── models.py             # ORM-модели воркера
├── frontend/                     # Реактивный веб-интерфейс (React + Vite)
│   ├── docker/
│   │   ├── Dockerfile            # Multi-stage сборка (Node 20 -> Nginx Alpine)
│   │   └── nginx.conf            # Конфигурация проксирования API и раздачи статики
│   ├── src/                      # UI компоненты (MetricsPanel, TicketTable, FilterBar, Modals, Toast)
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
├── scripts/
│   └── seed.py                   # Демонстрационный скрипт генерации тестовых событий
├── .env.example                  # Шаблон переменных окружения
├── .gitignore                    # Игнорируемые файлы (секреты, docs, артефакты)
├── CONTRIBUTING.md               # Руководство по GitFlow и конвенции коммитов
├── DEMO.md                       # Пошаговая инструкция по проверке обязательных сценариев ТЗ
├── docker-compose.yml            # Развертывание всех 4 сервисов (PostgreSQL 17, API, Worker, Frontend)
├── Makefile                      # Команды управления, сборки, линтинга и тестирования
└── ruff.toml                     # Конфигурация линтера и форматтера Ruff
```

---

## 📋 Спецификация API и контракты данных

### 1. `POST /api/events` — Прием входящего события

Принимает события от клиентов или сотрудников. Идемпотентность гарантируется по `external_event_id`.

#### Пример 1: Клиентское сообщение (`event_type = "client"`)
*Создает новое обращение в статусе `open` и `sla_status = "normal"`.*

```json
{
  "external_event_id": "evt_client_20260814_001",
  "event_type": "client",
  "received_at": "2026-08-14T10:00:00Z",
  "external_client_id": "tg_user_ivan_45",
  "topic": "Техническая поддержка",
  "content": "Не могу зайти в личный кабинет через мобильное приложение.",
  "payload": {
    "channel": "telegram",
    "app_version": "2.4.1"
  }
}
```

**Ответ (`201 Created` для нового события / `200 OK` для дубликата):**
```json
{
  "status": "created",
  "external_event_id": "evt_client_20260814_001",
  "ticket_id": "e386d251-a88c-4c7d-8a9a-2411868b8308",
  "event_type": "client",
  "message": "Event ingested successfully"
}
```

#### Пример 2: Ответ оператора (`event_type = "agent"`)
*Закрывает обращение, переводит статус в `closed` и фиксирует `first_response_time`.*

```json
{
  "external_event_id": "evt_agent_20260814_002",
  "event_type": "agent",
  "received_at": "2026-08-14T10:01:15Z",
  "ticket_id": "e386d251-a88c-4c7d-8a9a-2411868b8308",
  "content": "Здравствуйте! Ваш профиль успешно разблокирован, проверьте доступ.",
  "payload": {
    "agent_id": "ops_agent_anna"
  }
}
```

---

### 2. `GET /api/tickets` — Список открытых обращений

Возвращает активные обращения с динамически вычисленным временем ожидания и SLA-статусом.

* **Query-параметры**:
  * `topic` (опционально) — фильтрация по направлению (например, `GET /api/tickets?topic=Платежи%20и%20биллинг`).

**Пример ответа (`200 OK`):**
```json
{
  "tickets": [
    {
      "id": "e8ca3849-8fd0-4302-a7f1-91901fd34d20",
      "external_client_id": "crm_client_elena_88",
      "topic": "Платежи и биллинг",
      "content": "Двойное списание средств по подписке Premium за август.",
      "status": "open",
      "sla_status": "warning",
      "created_at": "2026-08-14T08:22:24.708570Z",
      "closed_at": null,
      "wait_time_seconds": 68.5,
      "first_response_time_seconds": null
    }
  ],
  "total": 1,
  "available_topics": [
    "Общие вопросы",
    "Платежи и биллинг",
    "Техническая поддержка"
  ]
}
```

---

### 3. `GET /api/metrics` — Аналитические показатели и медиана

Возвращает агрегированные операционные метрики и P50 медиану времени первого ответа.

* **Query-параметры**:
  * `date_from` (опционально, ISO 8601) — начало периода.
  * `date_to` (опционально, ISO 8601) — конец периода.

**Пример ответа (`200 OK`):**
```json
{
  "total_created": 15,
  "total_answered": 4,
  "total_overdue": 2,
  "median_first_response_time_seconds": 34.5,
  "period_from": null,
  "period_to": null
}
```

---

### 4. `GET /health` — Liveness & Readiness Проверка

```json
{
  "status": "ok",
  "database": "connected",
  "version": "1.0.0"
}
```

---

## 🚀 Быстрый старт и развертывание

### 1. Запуск всех сервисов в Docker
```bash
# 1. Скопировать шаблон конфигурации
cp .env.example .env

# 2. Собрать и запустить контейнеры (PostgreSQL 17, Backend API, Worker, Frontend)
make up
# или: docker compose up -d --build

# 3. Заполнить базу демонстрационными данными
python3 scripts/seed.py --host http://localhost:3000
```

### 2. Точки доступа к сервисам:
* 🌐 **Веб-интерфейс дашборда**: [http://localhost:3000](http://localhost:3000)
* 📖 **Интерактивная документация Swagger/OpenAPI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 🩺 **Health Check эндпоинт**: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Подключение к PostgreSQL через DBeaver / GUI-клиенты:
* **Host**: `localhost` (или `127.0.0.1`)
* **Port**: `5432`
* **Database**: `tickets_db`
* **Username**: `postgres`
* **Password**: `postgres`

---

## 🧪 Запуск автотестов и линтинга

```bash
# Запуск полного набора автотестов (13 тестов) внутри контейнера API:
make test

# Проверка кода линтером Ruff:
make lint

# Проверка форматирования:
make check

# Автоматическое форматирование кода:
make format
```

---

## 📈 Архитектурное развитие для Production (Highload & Scale)

При росте нагрузки до десятков тысяч RPS и интеграции с распределенными каналами связи (Telegram, WhatsApp, CRM, Web-чаты, Email, Slack):

1. **Change Data Capture (CDC) вместо периодического polling Outbox**:
   * При сверхвысоком потоке событий постоянный опрос таблицы `outbox_events` увеличивает нагрузку на WAL и дисковую подсистему.
   * **Решение**: Внедрение **Debezium + Apache Kafka**. Debezium читает WAL-логи PostgreSQL в реальном времени и передает сообщения в брокер Kafka, откуда независимые консьюмеры рассылают алерты.
2. **Аналитическое хранилище для тяжелых метрик (ClickHouse)**:
   * Расчет перцентилей `percentile_cont` на терабайтных массивах исторических данных требует ресурсов CPU.
   * **Решение**: Репликация закрытых тикетов в **ClickHouse** (MergeTree движок), обеспечивающий расчет перцентилей P50/P95/P99 за доли миллисекунды.
3. **Read Replicas и партиционирование таблиц**:
   * Разделение пулов соединений: мастер-нода PostgreSQL принимает `POST /api/events`, а горизонтально масштабируемые асинхронные Read Replicas обслуживают дашборды `GET /api/tickets`.
   * Партиционирование таблиц `events` и `tickets` по месяцам/кварталам (`RANGE (created_at)`).
