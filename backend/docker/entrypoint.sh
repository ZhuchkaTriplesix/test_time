#!/bin/sh
set -e

echo "Waiting for PostgreSQL database connection..."
python -c "
import asyncio, os, sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

url = os.getenv('DATABASE_URL')
if not url:
    user = os.getenv('POSTGRES_USER', 'postgres')
    pw = os.getenv('POSTGRES_PASSWORD', 'postgres')
    host = os.getenv('POSTGRES_HOST', 'db')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'tickets_db')
    url = f'postgresql+asyncpg://{user}:{pw}@{host}:{port}/{db}'

async def check():
    for i in range(30):
        try:
            engine = create_async_engine(url)
            async with engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            await engine.dispose()
            print('PostgreSQL is ready!')
            return
        except Exception as e:
            print(f'Attempt {i+1}/30: DB not ready ({e}). Retrying in 1s...')
            await asyncio.sleep(1)
    print('Failed to connect to DB after 30 attempts.')
    sys.exit(1)

asyncio.run(check())
"

echo "Applying Alembic database migrations..."
alembic upgrade head
echo "Migrations applied successfully."

echo "Starting FastAPI application..."
exec "$@"
