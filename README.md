# "Es un 10 pero…"

Videojuego multijugador por turnos. El repositorio contiene el **backend** (API REST en FastAPI) y el **frontend** (SPA en Vite). No hay modo demo ni bots: todo juega contra la API real.

## Requisitos

- Python 3.12
- Node.js 20+ (para el frontend)
- (Opcional) Docker + Docker Compose

## Cómo correr en desarrollo

### 1. Backend (puerto 8000)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Linux / macOS
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Queda en `http://localhost:8000` (Swagger en `/docs`).

> **Verificación de correo:** en desarrollo el proveedor de correo es `console` (config `EMAIL_PROVIDER`). Al registrarte, el código de verificación se imprime en la salida del servidor. En producción configurá un proveedor real (SMTP/API) por variable de entorno.

### 2. Frontend (puerto 5173)

```bash
cd frontend
npm install
npm run dev
```

Abrí `http://localhost:5173`. Vite reenvía `/api` al backend de `localhost:8000`.

### 3. Tests y E2E

```bash
# tests del backend (pytest)
pytest

# E2E con Playwright: levanta su propio backend en :8000 y juega una partida
# real de dos jugadores. Requiere `npm run dev` corriendo y puerto 8000 libre.
cd frontend && npm run test:e2e
```

## Cómo hostear

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Frontend (nginx, sirve los estáticos y proxya `/api`): `http://localhost:5173`

## Endpoints principales (todos bajo `/api/v1`)

| Área   | Endpoints |
| ------ | --------- |
| Auth   | `POST /auth/register`, `/verify-email`, `/resend-verification`, `/login`, `/logout`, `/change-password`, `/forgot-password`, `/reset-password` |
| Usuarios | `GET|PATCH /users/me` |
| Modalidades | `GET /modalities` |
| Salas  | `POST /rooms`, `GET /rooms/{code}`, `POST /rooms/{code}/join|leave|start`, `DELETE /rooms/{code}` |
| Partidas | `GET /matches/{id}`, `GET /matches/by-room/{code}`, `POST /matches/{id}/phrase`, `/matches/{id}/votes`, `GET /matches/{id}/turns/{turn_id}`, `/matches/{id}/scoreboard`, `/matches/{id}/result` |

Los jugadores entran a una sala con su **código** (único identificador compartido). Al iniciar la partida, el frontend obtiene la partida de esa sala con `GET /matches/by-room/{code}` y todos entran automáticamente: no se comparte ningún enlace ni identificador adicional.

Detalle completo y contrato de errores (`{error:{code,message,details}}`) en la especificación del DDD (`docs/`).

## Estructura

```
app/        # Backend FastAPI (api/, services/, domain/, stores/, email/)
frontend/   # SPA en Vite (src/screens, src/ui, src/api.js, src/store.js)
tests/      # Tests del backend (pytest)
```

## Flujo de trabajo con git

- `main`    → versión estable.
- `develop` → integración de funcionalidades.
- `feature/*` → ramas para funcionalidades puntuales, mergeadas en `develop`.
