# "Es un 10 pero…" — API

Videojuego multijugador por turnos. Este repositorio contiene el **backend** (API REST) del sistema, siguiendo la especificación definida en los documentos `SRS` y `DDD`.

## Requisitos

- Python 3.12
- (Opcional) Docker + Docker Compose

## Cómo correr el servidor

### 1. Opción local (recomendada para desarrollo)

```bash
# crear entorno virtual
python3 -m venv .venv

# activarlo
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# instalar dependencias
pip install -r requirements.txt

# levantar el servidor de desarrollo
uvicorn app.main:app --reload
```

El servidor queda disponible en `http://localhost:8000`.

### 2. Opción Docker

```bash
docker compose up --build
```

El servidor queda disponible en `http://localhost:8000`.

## Endpoints

| Método | Ruta      | Descripción                          |
| ------ | --------- | ------------------------------------ |
| GET    | `/`       | Información básica de la API         |
| GET    | `/health` | Health check del servidor            |
| GET    | `/docs`   | Documentación interactiva (Swagger)  |

## Estructura del proyecto

```
app/
└── main.py          # Aplicación FastAPI (punto de entrada)
```

El proyecto evolucionará siguiendo la arquitectura por capas definida en el DDD:
`api/`, `application/`, `domain/` e `infrastructure/`.

## Flujo de trabajo con git

- `main`  → versión estable.
- `develop` → integración de funcionalidades.
- `feature/*` → ramas para funcionalidades puntuales, mergeadas en `develop`.