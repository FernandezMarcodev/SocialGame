# Guía de Pruebas — "Es un 10 pero…

Documento que explica cómo está organizado y cómo se ejecuta el testing del
backend de **"Es un 10 pero…"** (API REST FastAPI), su alcance y su
verificación manual complementaria.

Documentos base: SRS v1.0 (RF/RNF) · DDD v1.0 (apéndice B: contratos front-back).
Version 1.1 · Estado: activo.

---

## 1. Estrategia general

El testing se divide en dos niveles complementarios:

| Nivel | Qué valida | Cómo |
| --- | --- | --- |
| **Pruebas unitarias** | Lógica de dominio/servicio aislada (máquinas de estado, reglas de negocio, tiempos) | Llama a los servicios (`MatchService`, `TurnService`, `ScoringService`, `AuthService`) con stores en memoria y relojes controlados |
| **Pruebas de contrato (HTTP)** | Contratos REST del apéndice B del DDD de punta a punta | `TestClient` (httpx) contra la app FastAPI real, con proveedor de correo en memoria (`outbox`) y almacenes en memoria / SQLite |
| **Pruebas de persistencia** | Comportamiento de repositorios con SQLite aislado | `tests/test_persistence.py` usando `tmp_path` y `sqlite:///<tmp>/app.db` |

Ambos niveles, junto con las pruebas de persistencia, ejercitan los
**códigos de error** del apéndice B.5 junto con los
`HTTP status` correctos (`401`, `403`, `409`, `422`, `423`), de modo que la
superficie pública queda protegida ante cambios de contrato.

Estado actual de la suite: **94 pruebas, todas en verde**.

## 2. Stack de pruebas

- **pytest** 8.3 (runner) — `requirements-dev.txt`
- **httpx** 0.28 → `TestClient` de FastAPI para pruebas de contrato HTTP
- **pydantic-settings** con `Settings(_env_file=None, debug=True)` → app aislada
  de variables de entorno reales
- **Proveedor de email fake**: la app recibe una lista `outbox` y el
  `ConsoleEmailProvider` acumula los correos; las pruebas leen el token de
  verificación/reset desde ahí (no hace falta red ni SMTP)
- **SQLite en `tmp_path`** → pruebas del módulo de persistencia sin depender de
  un PostgreSQL (RF-PER-001 a 005)

## 3. Cómo correr las pruebas

```bash
# entorno (una sola vez)
python3 -m venv .venv
source .venv/bin/activate            # Linux/macOS
pip install -r requirements-dev.txt

# toda la suite
pytest

# por módulo
pytest tests/test_auth.py
pytest tests/test_rooms.py

# filtrar por nombre
pytest -k "turn"
pytest -k "persistence or integration"
```

Resultado esperado:

```
94 passed in ~19s
```

## 4. Organización de la suite

| Archivo | Nº tests | Cobertura |
| --- | --- | --- |
| `tests/test_auth.py` | 18 | Contrato auth: registro, unicidad (RN-001/002), política de contraseña, verificación, bloqueo por intentos (RF-AUT-005), logout/revocación, cambio y reset de contraseña |
| `tests/test_auth_service_unit.py` | 4 | Unitarias de `AuthService` (tokens, verificación, expiración) |
| `tests/test_users.py` | 7 | `GET/PATCH /users/me`, unicidad de username/email, email nuevo revierte `verified` (RF-USR), catálogo de modalidades |
| `tests/test_rooms.py` | 21 | Salas: crear/obtener/unirse/abandonar/cancelar, cupo (RN-009), jugador en una sola sala (RN-004), transferencia de creador, inicio solo por creador (RN-007) y con mínimo de jugadores (RN-008) |
| `tests/test_matches.py` | 15 | Partidas: creación, `turn_order` aleatorio, avance de ronda, finalización (RN-017/021), resultado con ganador y empate (RN-023), restricciones de estado |
| `tests/test_turns.py` | 13 | Turnos por HTTP y unitarias: flujo completo de ronda, autor incorrecto, voto duplicado, autor que no vota, tiempos de autor/votación (RF-TUR-005/008), puntos por acierto exacto |
| `tests/test_scoring.py` | 11 | Marcador (scoreboard) y resultado vía HTTP + puntos acumulados (RN-018/019) |
| `tests/test_persistence.py` | 5 | Persistencia: repositorios (usuarios, modalidades siembra idempotente, frases de turno) y pruebas de integración con **SQLite**: usuarios y frases sobreviven a reinicios de la app |

### Helpers compartidos (`tests/conftest.py` y utilidades)

- Fixtures `settings`, `outbox`, `app`, `client` → cada test levanta una API
  limpia con memoria/outbox propios, sin estado compartido.
- `tests/test_auth.py` → `extract_token(...)` extrae el token del cuerpo del
  correo (verificación/reset).
- `tests/test_turns.py` → `match_and_turn(...)` monta una sala + partida + turno
  con N jugadores, lista para operar (usada también por persistencia).

## 5. Módulo de persistencia (RF-PER) y migraciones

La persistencia es **opt-in**: si `DATABASE_URL` está configurada en el entorno,
la API usa PostgreSQL vía SQLAlchemy; si no, opera con almacenes en memoria
(AD-003). Este modo opt-in permite probar los repositorios contra SQLite sin
necesitar una base de datos externa.

Incluye:

- Modelos y motor: `app/infra/db.py` (`users`, `modalities`, `turn_phrases`).
- Repositorios y orquestación: `app/infra/repositories.py`, `app/infra/persistence.py`.
- Migraciones versionadas con **Alembic** (`alembic/versions/0001_initial.py`).

### 5.1 Correr las migraciones contra PostgreSQL

```bash
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/dbname"
alembic upgrade head        # aplicar
alembic revision --autogenerate -m "descripcion"   # nueva migración
```

### 5.2 Pruebas de persistencia con SQLite

Las pruebas del módulo `tests/test_persistence.py` usan SQLite (`sqlite:///<tmp>/app.db`),
que respeta las mismas restricciones de unicidad de `users.username` y
`users.email` (RN-001/RN-002). Estas pruebas se ejecutan siempre, independientemente
de si `DATABASE_URL` está configurado.

## 6. Verificación manual complementaria

Además de la suite automatizada se verifica el comportamiento real:

### 6.1 Swagger / OpenAPI
Levantando la API (`uvicorn app.main:app --reload`) queda disponible
`http://localhost:8000/docs` con todos los contratos del apéndice B para
probar a mano cada endpoint.

### 6.2 Prueba funcional de punta a punta (multijugador)
En las iteraciones de desarrollo se validó el flujo completo de una partida con
un **cliente de prueba descartable** (HTML/JS sobre los contratos REST, con el
registro → verificación → login → sala → inicio → 3 turnos → resultado) corriendo
junto a la API vía un mini-proxy local. Se validó:

- Registro con política de contraseña y verificación de correo por consola
  (el token lo imprime el `ConsoleEmailProvider`).
- Sala privada con código, ingreso de 3 jugadores e inicio por el creador.
- Turnos: frase + puntaje secreto oculto hasta publicar, votos 1–10, avance
  automático y puntaje por acierto exacto.
- Finalización de ronda, resultado (ganador o empate) y eliminación de la sala.

Ese cliente fue **eliminado del repositorio** para conservar el backend solo;
esta guía documenta la experiencia para poder replicar la prueba manualmente
con `curl` o Swagger cuando se requiera.

### 6.3 Códigos de error a validar
Al probar a mano conviene confirmar los códigos documentados (apéndice B.5):
`TOKEN_INVALID`, `INVALID_CREDENTIALS`, `EMAIL_NOT_VERIFIED`,
`ACCOUNT_BLOCKED` (con `details.retry_after`), `USERNAME_TAKEN`, `EMAIL_TAKEN`,
`ROOM_NOT_FOUND`/`ROOM_FULL`/`ROOM_NOT_AVAILABLE`, `NOT_CREATOR`,
`MIN_PLAYERS_NOT_REACHED`, `NOT_AUTHOR`, `NOT_VOTING`, `ALREADY_VOTED`,
`TURN_FINISHED`/`TURN_EXPIRED`, `MATCH_NOT_FINISHED`, entre otros.

## 7. Buenas prácticas dentro del repo

- Un archivo de tests por módulo (`test_<modulo>.py`), con casos de contrato y
  unitarios claramente separados por clase cuando corresponde.
- Toda regla de negocio (RN) y requisito funcional (RF) del SRS tiene al menos
  un caso en la suite y queda citado en el docstring del test.
- Los tests crean su propio estado (fixtures), nunca dependen del orden de
  ejecución ni de datos previos.
- Antes de cada merge a `develop` se espera `pytest` en verde y sin warnings de
  la suite.
- Cuando `DATABASE_URL` esté configurado, verificar que las migraciones de
  Alembic estén al día antes de correr la suite completa.