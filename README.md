# Findjob

Plataforma de búsqueda y matching de ofertas laborales con scraping, embeddings locales y IA.

## Setup rápido

```bash
# Infraestructura
docker compose up -d

# Dependencias
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Variables de entorno
cp .env.example .env

# Migraciones
alembic upgrade head
```