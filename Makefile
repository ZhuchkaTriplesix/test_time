.PHONY: up down build logs test lint format check clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	docker compose exec api pytest -v

lint:
	ruff check .

format:
	ruff format .

check: lint
	ruff format --check .

clean:
	docker compose down -v
