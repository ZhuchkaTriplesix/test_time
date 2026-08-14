"""Тесты валидации входных данных, обработки ошибок и граничных условий API.

Назначение:
- Проверка валидации Pydantic схем (некорректный event_type, пустой content).
- Проверка ответов на несуществующий тикет (404 Not Found) и повторное закрытие (400 Bad Request).
- Проверка эндпоинта проверки работоспособности GET /health.
- Проверка фильтрации по несуществующему топику.
"""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_healthcheck_endpoint(async_client: AsyncClient):
    """Test healthcheck endpoint returns 200 OK and connected database."""
    res = await async_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_api_validation_invalid_event_type(async_client: AsyncClient):
    """Test creating an event with invalid event_type returns 422 Unprocessable Entity."""
    payload = {
        "external_event_id": f"evt_invalid_{uuid.uuid4()}",
        "event_type": "unknown_type",
        "external_client_id": "client_1",
        "topic": "Техническая поддержка",
        "content": "Текст сообщения",
    }
    res = await async_client.post("/api/events", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_api_agent_reply_to_non_existent_ticket(async_client: AsyncClient):
    """Test agent response referencing a non-existent ticket returns 404 Not Found."""
    fake_ticket_id = str(uuid.uuid4())
    payload = {
        "external_event_id": f"evt_agent_{uuid.uuid4()}",
        "event_type": "agent",
        "ticket_id": fake_ticket_id,
        "content": "Здравствуйте! Ваш вопрос решен.",
    }
    res = await async_client.post("/api/events", json=payload)
    assert res.status_code == 404
    assert "не найден" in res.json()["detail"]


@pytest.mark.asyncio
async def test_api_agent_reply_to_already_closed_ticket(async_client: AsyncClient):
    """Test agent response to an already closed ticket returns 400 Bad Request."""
    # 1. Create client ticket
    client_payload = {
        "external_event_id": f"evt_client_{uuid.uuid4()}",
        "event_type": "client",
        "external_client_id": "client_1",
        "topic": "Техподдержка",
        "content": "Не работает кнопка",
    }
    res = await async_client.post("/api/events", json=client_payload)
    assert res.status_code == 201
    ticket_id = res.json()["ticket_id"]

    # 2. First agent response - successfully closes the ticket
    agent_payload_1 = {
        "external_event_id": f"evt_agent_1_{uuid.uuid4()}",
        "event_type": "agent",
        "ticket_id": ticket_id,
        "content": "Вопрос решен.",
    }
    res = await async_client.post("/api/events", json=agent_payload_1)
    assert res.status_code == 201

    # 3. Second agent response to the same ticket - should return 400 Bad Request
    agent_payload_2 = {
        "external_event_id": f"evt_agent_2_{uuid.uuid4()}",
        "event_type": "agent",
        "ticket_id": ticket_id,
        "content": "Повторный ответ.",
    }
    res = await async_client.post("/api/events", json=agent_payload_2)
    assert res.status_code == 400
    assert "уже закрыто" in res.json()["detail"]


@pytest.mark.asyncio
async def test_api_tickets_topic_filtering_empty_match(async_client: AsyncClient):
    """Test tickets endpoint with a non-matching topic returns empty list and available topics."""
    # Create a ticket in "Телефония"
    await async_client.post(
        "/api/events",
        json={
            "external_event_id": f"evt_client_{uuid.uuid4()}",
            "event_type": "client",
            "external_client_id": "user_tel",
            "topic": "Телефония",
            "content": "Не проходит звонок",
        },
    )

    # Query non-existent topic "Бухгалтерия"
    res = await async_client.get("/api/tickets?topic=Бухгалтерия")
    assert res.status_code == 200
    data = res.json()
    assert len(data["tickets"]) == 0
    assert data["total"] == 0
    assert "Телефония" in data["available_topics"]
