# GitFlow & Commit Conventions

## Branching Strategy (GitFlow)

1. **`master` (или `main`)**:
   - Хранит стабильный production-ready код.
   - Прямые коммиты в `master` запрещены (только релизные мержи и хотфиксы).

2. **`develop`**:
   - Основная ветка разработки и интеграции фичей.
   - Все функциональные ветки стартуют от `develop` и вливаются обратно в `develop`.

3. **`feature/<feature-name>`**:
   - Ветка для разработки конкретной фичи или задачи (например: `feature/backend-api`, `feature/worker-outbox`, `feature/frontend-ui`).
   - Ответвляется от: `develop`.
   - Вливается в: `develop`.

4. **`release/<version>`**:
   - Подготовка релиза (например: `release/v1.0.0`).
   - Ответвляется от: `develop`.
   - Вливается в: `master` (создается git tag `vX.Y.Z`) и обратно в `develop`.

5. **`hotfix/<issue-name>`**:
   - Срочные исправления критических багов на проде.
   - Ответвляется от: `master`.
   - Вливается в: `master` (с тегом) и `develop`.

---

## Commit Guidelines (Conventional Commits)

Формат сообщений коммитов:
`<type>(<scope>): <short description>`

### Types:
- `feat`: новая функциональность
- `fix`: исправление ошибки
- `refactor`: рефакторинг кода без изменения поведения
- `test`: добавление или изменение тестов
- `docs`: изменения в документации
- `chore`: сопутствующие задачи, зависимости, конфиги
- `ci`: изменения в CI/CD пайплайнах
- `perf`: улучшение производительности

### Scopes:
- `backend`, `worker`, `frontend`, `db`, `infra`, `api`, `sla`, `outbox`

### Примеры:
- `feat(backend): implement event ingestion endpoint POST /api/events`
- `feat(worker): implement transactional outbox processor with SKIP LOCKED`
- `feat(frontend): create reactive SLA metrics dashboard`
- `test(backend): add idempotency concurrency test with 20 parallel events`
- `docs(readme): add setup and execution instructions`
