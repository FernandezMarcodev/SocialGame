#!/bin/sh
# Entrypoint del backend: aplica migraciones y arranca la API.
set -e

if [ -n "$DATABASE_URL" ]; then
  echo "Aplicando migraciones de base de datos..."
  # Reintenta unas veces por si la BD aún no está lista (BD gestionada externa).
  for i in $(seq 1 10); do
    if alembic upgrade head; then
      break
    fi
    echo "Reintentando migración en 3s (intento $i/10)..."
    sleep 3
  done
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
