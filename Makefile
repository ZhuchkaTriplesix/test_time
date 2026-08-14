.PHONY: up down build logs test lint clean

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

clean:
	docker compose down -v
