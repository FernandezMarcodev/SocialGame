# Guía completa de implementación y estudio — "Es un 10 pero…"

> Documento didáctico integral. Explica cómo está construido el proyecto, en
> qué orden se hizo, qué hace cada dependencia, cómo se arma el contenedor y
> cómo se conecta y hostea la base de datos. Pensado para leer y estudiar.

---

## Índice

1. [Visión general del proyecto](#1-visión-general-del-proyecto)
2. [Arquitectura por capas](#2-arquitectura-por-capas)
3. [Orden en que se construyó (y en que orden debería hacerse)](#3-orden-de-construcción)
4. [Dependencias: qué son y para qué sirven](#4-dependencias)
5. [Cómo se "instala" todo dentro del contenedor](#5-instalación-dentro-del-contenedor)
6. [FastAPI: cómo arranca la app](#6-fastapi-cómo-arranca-la-app)
7. [Configuración (`config.py`)](#7-configuración)
8. [La capa de datos: entidades, stores y base de datos](#8-capa-de-datos)
9. [SQLAlchemy y los modelos](#9-sqlalchemy-y-los-modelos)
10. [Alembic: migraciones](#10-alembic-migraciones)
11. [Email: console vs SMTP](#11-email)
12. [Docker: Dockerfile, entrypoint y compose](#12-docker)
13. [Cómo probar el sistema](#13-cómo-probar-el-sistema)
14. [Deploy en Render (Managed Postgres)](#14-deploy-en-render)
15. [Preguntas frecuentes / decisiones](#15-notas-y-decisiones)

---

## 1. Visión general del proyecto

"Es un 10 pero…" es un **videojuego multijugador por turnos**. Tiene dos partes:

- **Backend** (`app/`): API REST en **FastAPI** (Python) que maneja
  autenticación, salas, partidas, turnos y puntajes.
- **Frontend** (`frontend/`): una SPA en **Vite + vanilla JS** que consume la API.

No hay bots: todo juega contra la API real. El flujo típico: un jugador crea
una sala (obtiene un código), otros se unen con ese código, el creador inicia
la partida y juegan rondas escribiendo frases y votando puntajes.

---

## 2. Arquitectura por capas

El backend está organizado de "adentro hacia afuera". Cada capa no conoce los
detalles de la de abajo:

```
HTTP (routers)          app/api/routers/   → recibe requests, devuelve JSON
   ↓
Services                app/services/      → reglas de negocio (auth, salas, etc.)
   ↓
Stores / Repositorios   app/stores/        → guardan y leen datos
   ↓
Entities (dataclasses)  app/domain/        → modelo del dominio (User, Room…)
```

Gracias a esto pudimos cambiar "memoria" por "Postgres" **sin tocar la lógica
del juego**: solo reemplazamos la capa de stores.

Archivos principales:

```
app/
  main.py                 # crea la app FastAPI y conecta todo
  core/
    config.py             # settings desde variables de entorno
    security.py           # hashing de passwords (argon2), tokens
  domain/
    entities.py           # User, Room, Match, Turn, Vote, etc. (dataclasses)
  stores/
    base.py               # interfaces (Protocol) de los stores
    memory.py             # implementación en memoria
    database.py           # implementación en PostgreSQL (SQLAlchemy)
  services/
    auth_service.py       # registro, login, verificación, reset
    users_service.py      # perfil y avatar
    room_service.py       # crear/unir/salir/iniciar sala
    match_service.py      # ciclo de vida de la partida
    turn_service.py       # frases, votos, timeouts
    scoring_service.py    # puntajes
    realtime_service.py   # WebSockets
  api/
    routers/              # endpoints HTTP bajo /api/v1
    errors.py             # formato de error estándar
    schemas.py            # modelos de request/response (pydantic)
  email/
    provider.py           # ConsoleEmailProvider / SmtpEmailProvider
```

---

## 3. Orden de construcción

### 3.1 El orden que usamos (protoype → producción)

1. Dominio y documentos DDD (entidades, reglas).
2. Stores **en memoria** (rápido para prototipar y testear lógica).
3. Services con la lógica del juego.
4. API routers (HTTP).
5. Seguridad básica (argon2, verificación).
6. **Más tarde**: base de datos real (Postgres + SQLAlchemy + Alembic),
   proveedor de email SMTP y ajuste de los tests a 3 rondas.

### 3.2 El orden "correcto" en un proyecto real con autenticación

Para un sistema con usuarios, la persistencia es central. Lo ideal:

1. Definir el dominio (docs DDD).
2. **Elegir la DB desde el día 1** (Postgres) y crear la 1ª migración.
3. Entorno: `venv`, `requirements.txt`, `config.py` con `DATABASE_URL`.
4. Entities → Stores (con la DB real).
5. Services.
6. API routers.
7. Seguridad (argon2, email SMTP de verdad).
8. Tests (con la DB real o memoria para unitarios).
9. Dockerizar + `docker-compose` con `db`.
10. Deploy (Render): env vars, migraciones, frontend estático.

> **Lección:** empezar con memoria estuvo bien para aprender, pero para auth
> deberíamos haber puesto Postgres desde el inicio. Lo que tenemos ahora ya
> es esa versión correcta.

---

## 4. Dependencias

Todo vive en `requirements.txt` (backend). Cada línea tiene un trabajo:

| Dependencia | Qué es | Para qué se usa |
|---|---|---|
| `fastapi==0.115.6` | Framework web HTTP/JSON | Define los endpoints y genera `/docs` |
| `uvicorn[standard]==0.34.0` | Servidor ASGI | Corre la app: `uvicorn app.main:app` |
| `pydantic-settings==2.7.1` | Config desde env vars | `config.py` lee `DATABASE_URL`, `EMAIL_PROVIDER`, etc. |
| `argon2-cffi==25.1.0` | Hash de contraseñas | `security.py` guarda passwords hasheadas |
| `email-validator==2.2.0` | Valida emails | Al registrar usuario |
| `python-multipart==0.0.20` | Parser de formularios/archivos | Subida de avatares |
| `sqlalchemy==2.0.36` | ORM (objetos ⇄ tablas SQL) | `app/stores/database.py` |
| `psycopg2-binary==2.9.10` | Driver de Postgres | Lo que SQLAlchemy usa para hablar con Postgres |
| `alembic==1.14.1` | Versionado del esquema | `migrations/` crea/evoluciona tablas |

El **frontend** tiene sus propias dependencias en `frontend/package.json`
(Vite, etc.) y se construye aparte.

---

## 5. Instalación dentro del contenedor

El backend corre en un contenedor Docker definido por `Dockerfile`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # ← aquí se instala FastAPI, SQLAlchemy, etc.

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["sh", "./entrypoint.sh"]
```

**¿Cómo se instaló FastAPI y el resto?** Cuando Render (o `docker build`)
construye la imagen, el paso `pip install -r requirements.txt` baja e instala
todas las librerías listadas arriba dentro del contenedor. Vos no instalás
nada a mano: el `Dockerfile` lo automatiza.

La **base de datos** no se instala con pip: es un contenedor separado
(`postgres:16-alpine`) definido en `docker-compose.yml`.

---

## 6. FastAPI: cómo arranca la app

`app/main.py` tiene una función `create_app()` que ensambla todo:

```python
def create_app(settings=None, outbox=None):
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    # 1) Elegir stores según si hay DATABASE_URL
    if settings.database_url:
        from app.stores.database import (Database, DatabaseUserStore, ...)
        db = Database(settings.database_url)
        user_store = DatabaseUserStore(db)
        ...
        email_provider = SmtpEmailProvider(...) if settings.email_provider=="smtp" else ConsoleEmailProvider(outbox)
    else:
        user_store = MemoryUserStore()   # modo dev / tests
        ...

    # 2) Crear services con los stores
    auth_service = AuthService(settings=settings, users=user_store, ...)
    ...

    # 3) Registrar routers bajo /api/v1
    api = APIRouter(prefix="/api/v1")
    api.include_router(auth.router)
    ...

    return app
```

Al final del archivo: `app = create_app()` para que Uvicorn pueda hacer
`uvicorn app.main:app`.

El `entrypoint.sh` es el que de verdad arranca Uvicorn:

```sh
#!/bin/sh
set -e
if [ -n "$DATABASE_URL" ]; then
  echo "Aplicando migraciones de base de datos..."
  alembic upgrade head
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

---

## 7. Configuración

`app/core/config.py` usa `pydantic-settings`. Lee variables de entorno (y un
`.env`). Campos relevantes:

```python
class Settings(BaseSettings):
    app_name: str = "Es un 10 pero…"
    debug: bool = False

    database_url: str = ""          # si está vacío → usa memoria

    email_provider: str = "console" # "console" o "smtp"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    room_min_players: int = 2
    room_max_players: int = 6
    author_timeout_seconds: int = 60
    voting_timeout_seconds: int = 30
    # ...tokens, locks, etc.
```

---

## 8. La capa de datos

### 8.1 Entities (`app/domain/entities.py`)

Son `dataclasses` puras, sin lógica de persistencia:

```python
@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    verified: bool = False
    # ...
```

### 8.2 Stores (Repository pattern)

`base.py` define las **interfaces** (qué métodos debe tener un store).
Luego hay dos implementaciones:

- `memory.py` → guarda en diccionarios de Python (se pierde al reiniciar).
- `database.py` → guarda en Postgres vía SQLAlchemy.

Como ambas cumplen la misma interfaz, los services funcionan con cualquiera.

### 8.3 ¿Por qué había datos "en memoria"?

Al principio `memory.py` era el único store. Los datos vivían en RAM. Por eso
al reiniciar se perdían los usuarios. Lo reemplazamos por `database.py`.

---

## 9. SQLAlchemy y los modelos

`app/stores/database.py` define un modelo ORM por tabla. Ejemplo reducido:

```python
class UserModel(Base):
    __tablename__ = "users"
    id = mapped_column(String, primary_key=True)
    username = mapped_column(String, unique=True, nullable=False, index=True)
    email = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash = mapped_column(String, nullable=False)
    verified = mapped_column(Boolean, default=False)
    # ...
```

**Detalle importante — columnas JSONB:** estructuras anidadas como la lista de
jugadores, el orden de turnos, los puntajes y los votos se guardan en columnas
`JSONB`. Así conservamos la forma exacta del dominio sin crear 10 tablas
relacionales:

```python
class MatchModel(Base):
    __tablename__ = "matches"
    match_id = mapped_column(String, primary_key=True)
    room_code = mapped_column(String, unique=True, nullable=False, index=True)
    players = mapped_column(JSONB, nullable=False, default=list)
    turn_order = mapped_column(JSONB, nullable=False, default=list)
    scores = mapped_column(JSONB, nullable=False, default=dict)
    # ...
```

Cada store tiene métodos que convierten entidad ⇄ fila (ej.
`UserModel.from_entity` / `to_entity`).

`Database` crea el engine y un `sessionmaker`:

```python
class Database:
    def __init__(self, database_url: str):
        self._engine = create_engine(_normalize_url(database_url), pool_pre_ping=True, future=True)
        self._Session = sessionmaker(bind=self._engine, expire_on_commit=False, future=True)
```

> Nota: `_normalize_url` convierte `postgres://` (que da Render) en
> `postgresql://` (que esperan los drivers).

---

## 10. Alembic: migraciones

Las tablas **no se crean solas**: las crea Alembic corriendo la migración
inicial. Archivos:

- `alembic.ini` → configuración (apunta a `migrations/`).
- `migrations/env.py` → conecta con `DATABASE_URL` y usa los modelos de
  `app.stores.database.Base`.
- `migrations/script.py.mako` → plantilla de migraciones.
- `migrations/versions/0001_initial.py` → crea las 6 tablas (+ `alembic_version`):

```python
def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)   # crea users, rooms, matches, turns, sessions, verification_tokens

def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
```

**¿Cuándo corre?** En el `entrypoint.sh`, antes de arrancar Uvicorn:
`alembic upgrade head`. También podés correrlo manualmente con
`alembic upgrade head` (necesitás la env `DATABASE_URL`).

---

## 11. Email

`app/email/provider.py` usa el patrón Strategy:

- `ConsoleEmailProvider` → imprime el correo (token de verificación) en los
  logs. Se usa en dev (`EMAIL_PROVIDER=console`).
- `SmtpEmailProvider` → envía por SMTP real (producción).

En `main.py` se elige según `settings.email_provider`:

```python
if settings.email_provider == "smtp" and settings.smtp_host:
    email_provider = SmtpEmailProvider(host=..., port=..., ...)
else:
    email_provider = ConsoleEmailProvider(outbox)
```

Para producción, las variables son `EMAIL_PROVIDER=smtp`, `SMTP_HOST`,
`SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`.

---

## 12. Docker

### 12.1 `docker-compose.yml`

Tres servicios:

```yaml
services:
  db:                       # base de datos
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: es10p
      POSTGRES_PASSWORD: es10p
      POSTGRES_DB: es10p
    volumes:
      - es10p_db_data:/var/lib/postgresql/data   # persistencia
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U es10p -d es10p"]
      ...

  es10p-api:                # backend
    build: .
    environment:
      DATABASE_URL: postgresql://es10p:es10p@db:5432/es10p
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"

  frontend:                 # SPA + nginx
    build:
      context: ./frontend
    ports:
      - "5173:80"
    depends_on:
      - es10p-api
```

El nombre `es10p-api` es clave: el `nginx.conf` del frontend hace proxy de
`/api` a `http://es10p-api:8000`.

### 12.2 Volúmenes

`es10p_db_data` hace que los datos de Postgres **persistan** aunque reinicies
el contenedor `db`. Sin volumen, se perderían al borrar el contenedor.

---

## 13. Cómo probar el sistema

Levantar todo:

```bash
docker compose up --build
```

- App: http://localhost:5173
- API docs: http://localhost:8000/docs

**Probar la persistencia (la parte importante):**
1. Registrate en la app.
2. El código de verificación se imprime en los logs del backend:
   ```bash
   docker compose logs es10p-api | grep -A3 "Verificación"
   ```
3. Verificá la cuenta y jugá.
4. Para comprobar que los datos van a Postgres (no a memoria): reiniciá
   `docker compose restart es10p-api` y volvete a loguear. Si entra, el
   usuario está en la base.

**Ver las tablas directamente:**

```bash
docker compose exec db psql -U es10p -d es10p -c "\dt"
docker compose exec db psql -U es10p -d es10p -c "SELECT count(*) FROM users;"
```

---

## 14. Deploy en Render (Managed Postgres)

1. Creá la base en Render: **PostgreSQL** (Managed). Render la crea vacía y te
   da una `DATABASE_URL`.
2. En tu **Web Service** (backend), **adjuntá** la base de datos. Render
   inyecta `DATABASE_URL` automáticamente (o la seteás manual como variable de
   entorno).
3. El `Dockerfile` + `entrypoint.sh` ya corre `alembic upgrade head` al
   iniciar → crea las tablas solas.
4. Seteá además (si usás email real):
   - `EMAIL_PROVIDER=smtp`
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`,
     `SMTP_USE_TLS`
5. El frontend podés servirlo como **Static Site** (build `npm run build`,
   publish `dist/`) o como otro Web Service con nginx.

**Si no usás nuestra imagen Docker** (p.ej. Buildpack de Python), poné en
**Release Command**: `alembic upgrade head`.

> La base "vacía" al crearla es **normal**. Las tablas las crea Alembic y los
> datos (usuarios, partidas) los crea la app cuando la usan. Vos no insertás
> nada manualmente.

---

## 15. Notas y decisiones

- **3 rondas por partida** (`_TOTAL_ROUNDS = 3`, RN-002). Los tests que
  asumían 1 ronda se ajustaron para jugar las 3 rondas completas.
- **Stores en memoria vs DB**: la app usa DB si `DATABASE_URL` está seteado;
  si no, memoria (modo dev/tests). Esto permite testear sin Postgres.
- **API usa `$PORT`** en el entrypoint (`${PORT:-8000}`) para compatibilidad
  con Render y con `docker-compose`.
- **Tablas**: `users`, `sessions`, `verification_tokens`, `rooms`, `matches`,
  `turns` (más `alembic_version`).
- **Seguridad**: contraseñas con argon2; tokens de verificación/reset
  hasheados; sesiones con expiración.

---

### Resumen para estudiar

1. El backend es FastAPI con capas (routers → services → stores → entities).
2. Las dependencias se instalan dentro del contenedor vía
   `pip install -r requirements.txt`.
3. La persistencia real la da SQLAlchemy + Postgres; las tablas las crea
   Alembic (`alembic upgrade head`).
4. Docker empaqueta backend + base + frontend; el volumen hace persistente la DB.
5. En hosting solo conectás la `DATABASE_URL`; el resto lo hace el código.
