# Руководство по разработке и GitFlow

## Структура веток (GitFlow)

В проекте используется классическая модель ветвления **GitFlow**:

| Ветка | Назначение | Источник | Куда мержится |
|---|---|---|---|
| `master` | Стабильный релизный код | — | — |
| `develop` | Основная ветка разработки | `master` | `master` (через `release/`) |
| `feature/*` | Разработка новой функциональности | `develop` | `develop` |
| `release/*` | Подготовка и стабилизация релиза | `develop` | `master` и `develop` |
| `hotfix/*` | Срочные исправления бага в проде | `master` | `master` и `develop` |

### Жизненный цикл фичи:
1. Создать ветку от `develop`: `git checkout develop && git checkout -b feature/<name>`
2. Реализовать изменения, соблюдая Conventional Commits.
3. Прогнать тесты и линтеры.
4. Влить в `develop`: `git checkout develop && git merge --no-ff feature/<name>` (или через Pull Request).

---

## Формат коммитов (Conventional Commits)

```
<type>(<scope>): <описание>
```

- **`feat`**: Новая функциональность (API, модели, воркер, UI)
- **`fix`**: Исправление багов
- **`test`**: Добавление или обновление тестов
- **`refactor`**: Изменение структуры кода без изменения бизнес-логики
- **`docs`**: Обновление документации (README, DEMO.md)
- **`chore`**: Обновление зависимостей, docker, Makefile
- **`ci`**: Настройка GitHub Actions / CI
