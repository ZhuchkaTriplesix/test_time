"""Главная точка входа ASGI-приложения FastAPI.

Назначение:
- Инициализирует инстанс приложения через фабрику App.
- Предоставляет ASGI-объект `app` для запуска через серверы Uvicorn / Gunicorn.
- Поддерживает прямой запуск через `python src/main.py`.
"""

import logging

import uvicorn

from src.config import get_settings
from src.configuration.app import App

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = App().app

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=False,
    )
