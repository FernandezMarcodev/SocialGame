# Resumen del Backend — "Es un 10 pero…"

Documentación generada a partir de la revisión del código en `app/` (rama `develop`,
commit `78763be`). Incluye la evolución histórica, la arquitectura por capas y un
revisión módulo a módulo con observaciones.

## 1. Evolución histórica (cambios por commit)

| Commit | Título | Alcance backend |
|--------|--------|-----------------|
| `2edd94f` | feat: servidor FastAPI base funcionando | `main.py`, `app` factory, health/root. |
| `8ffd832` | feat: módulo de configuración central con pydantic-settings | `core/config.py` (Settings). |
| `efd6ba3` | feat: módulo de autenticación y esqueleto de API REST | `api/errors.py`, `api/schemas.py`, `core/security.py`, `services/auth_service.py`. |
| `f12fc33` | feat(auth): imprimir cuerpo del correo en consola para pruebas | `email/provider.py` (ConsoleEmailProvider). |
| `11b4ac6` | feat: módulo de salas de juego | `services/room_service.py`, `api/routers/rooms.py`, `stores/base.py`. |
| `f327c7c` | fix(modalities): catalogar segunda modalidad | `services/catalog.py`. |
| `563d1bd` | refactor: consolidar módulos de cuentas, salas y catálogo | Reorganización en `app/` (cuentas, salas, catálogo). |
| `fa8ce16` | feat: módulo de partidas | `services/match_service.py`, `api/routers/matches.py`. |
| `6b32cde` | feat: módulo de turnos | `services/turn_service.py`, `api/routers/turns.py`, `domain/entities.py` (Turn, Vote). |
| `ea6a301` | feat: módulo de puntuación | `services/scoring_service.py`, `api/routers/scoring.py`. |
| `c015fae` | feat: tiempo real por WebSocket y entrada a partidas por código | `services/realtime_service.py`, `api/ws.py`, código de sala, `routers/modalities.py`. |
| `925ce55` | feat: foto de perfil por archivo, fix de borrador y trazabilidad | `services/users_service.py`, avatar upload, `profile_image_url` en entidades/schemas. |
| `78763be` | feat: 3 rondas fijas, imagen de perfil y mejoras de UI | `_TOTAL_ROUNDS=3`, `turn_index`/`total_rounds` en `MatchOut`, `profile_image_url` en `PlayerOut`. |

## 2. Arquitectura por capas (DDD + FastAPI)

```
main.py                     → composea todos los servicios (app factory)
  ├─ core/        config.py (Settings), security.py (Argon2, tokens)
  ├─ domain/      entities.py (dataclasses), avatars.py
  ├─ stores/      base.py (Protocols), memory.py (impl. en memoria)
  ├─ services/    auth, users, room, match, turn, scoring, catalog, realtime, emails
  ├─ api/         deps.py, errors.py, schemas.py, routers/*, ws.py
  └─ email/       provider.py (Protocol + ConsoleEmailProvider)
```

Puntos de diseño (decisiones de arquitectura, "AD-xxx" citadas en el código):
- **AD-002**: token opaco (`secrets.token_urlsafe`) almacenado solo como hash SHA-256.
- **AD-003**: persistencia 100% en memoria (`stores/memory.py`), sin PostgreSQL aún.
- **AD-004**: tiempo real con bus de eventos `EventBus` + `ConnectionManager` WebSocket.
- **AD-005**: email desacoplado vía `EmailProvider`; en dev usa `ConsoleEmailProvider`.
- **AD-006**: contraseñas con Argon2id.
- **AD-007**: catálogo de modalidades precargado en código (`catalog.py`).
- **AD-010**: política de contraseñas (≥8, mayúscula, minúscula, dígito y símbolo).

## 3. Revisión por módulo

### 3.1 Configuración — `core/config.py`
Centraliza timeouts (login, verificación, reset), límites de sala (2–6), tiempos de
turno (autor 60s, votación 30s) y límite de avatar (2 MB). Lee de `.env`.

### 3.2 Seguridad — `core/security.py`
- `PasswordHasherArgon2`: Argon2id, `verify` captura `VerifyMismatchError` y cualquier
  excepción devolviendo `False` (evita crashes).
- `validate_password_policy`: exige símbolo (política estricta, ver observación O-3).
- `generate_token` / `hash_token`: token opaco + hash SHA-256.

### 3.3 Autenticación — `services/auth_service.py` (RN-001…004, RF-AUT-001…009)
- `register`: valida política, username/email únicos, hashea, genera avatar por defecto,
  emite verificación.
- `login`: acepta `identifier` = username **o** email; bloqueo por intentos fallidos
  (`max_login_attempts`, `lockout_seconds`); exige `verified`.
- `verify_email` / `resend_verification` / `forgot_password` / `reset_password`: tokens
  con TTL y `used` flag.
- `resolve_access_token`: valida sesión (revocada/expirada).
- Nota menor: `resend_verification` reusa `ForgotPasswordIn` (campo `email`); funciona
  pero el nombre del esquema es confuso (ver O-4).

### 3.4 Usuarios — `services/users_service.py` (RF-USR-005…007)
- `update_profile`: username/email únicos; al cambiar email se des-verifica y re-emite
  verificación.
- `update_avatar`: valida tipo MIME (`ALLOWED_AVATAR_TYPES`), tamaño, elimina avatar
  previo (`glob`) y sirve desde `/uploads/{id}{ext}`.

### 3.5 Salas — `services/room_service.py` (RF-SAL-001…008, RN-004,006…011)
- Código de 6 chars (`_ROOM_ALPHABET` sin caracteres ambiguos), único por colisión.
- Un jugador solo en una sala (`get_room_by_player`), estados `available → in_match →
  deleted/cancelled`.
- `start_match`: valida creador, mínimo de jugadores, crea partida, la inicializa,
  arranca turnos y publica `match.started`.

### 3.6 Partidas — `services/match_service.py` (RF-PAR-001…007, RN-017,021…023)
- Ciclo: `created → initialized → in_progress → finished`.
- `initialize_match`: genera `turn_order` como 3 permutaciones independientes
  (`_TOTAL_ROUNDS = 3`, RN-002) → cada partida son exactamente 3 rondas.
- `advance_round` / `finish_round` / `_finish` (elimina la sala al terminar).
- `result` / `_result_of`: empate si hay ≥2 líderes (`winner_id=None`, `tied=True`).

### 3.7 Turnos — `services/turn_service.py` (RF-TUR-001…011, RN-012…017,020)
- Ciclo de turno: `active → voting → finished | discarded`.
- **Expiración diferida** (`settle_expired`): se evalúa al consultar/actuar, cierra
  turnos vencidos antes de continuar (buen patrón, evita tarea de fondo).
- `submit_phrase`: frase 3–200 chars, `secret_score` 1–10, abre votación.
- `submit_vote`: el autor no vota su frase; 1–10; al completar todos los votos
  (`len(players)-1`) finaliza y avanza.
- `_finalize` delega el puntaje a `ScoringService`.

### 3.8 Puntuación — `services/scoring_service.py` (RF-PUN-001…004, RN-018,019)
- `turn_points`: 1 punto por cada voto **exacto** al `secret_score` (RN-019).
- `apply_turn`: suma al marcador del **autor** (RN-018, solo el autor puntúa).
- `scoreboard` / `result`: marcador ordenado y resultado final.

### 3.9 Tiempo real — `services/realtime_service.py` + `api/ws.py` (RF-COM-001…010)
- `ConnectionManager`: conexiones por `user_id` (puede haber varias por usuario).
- `EventBus`: pub/sub en proceso; `RealtimeService` suscrito a `room.updated`,
  `room.cancelled`, `match.started`.
- `ws.py`: `/api/v1/ws?token=...`, autentica con el token, acepta y mantiene viva la
  conexión leyendo mensajes entrantes (no se procesan, solo keep-alive).

### 3.10 API — `api/routers/*`, `api/deps.py`, `api/schemas.py`, `api/errors.py`
- Rutas bajo `/api/v1`: `auth`, `users`, `modalities`, `rooms`, `matches`, `turns`,
  `scoring`, `ws`.
- `deps.py`: inyección vía `app.state.*`; `get_current_user` resuelve el token.
- `errors.py`: `ApiError` con `code` estable + HTTP status; handlers para validación y
  errores no controlados (en prod).
- `schemas.py`: Pydantic con `UserOut.from_attributes`, `MatchOut` con `turn_index` y
  `total_rounds`.

### 3.11 Stores — `stores/base.py` (Protocols) + `stores/memory.py`
Interfaces explícitas (`UserStore`, `SessionStore`, `VerificationStore`, `RoomStore`,
`MatchStore`, `TurnStore`) → fácil migrar a PostgreSQL implementando los Protocols.

## 4. Hallazgos de la revisión (code review)

- **O-1 (medio) — Avatares por defecto inexistentes:** `domain/avatars.py` devuelve
  `/avatars/{initial}.svg`, pero `main.py` solo monta `/uploads`. Los usuarios sin foto
  subida reciben un 404 en su `profile_image_url`. Solución: montar `/avatars` con SVGs
  generados o cambiar la URL por defecto a un placeholder real.
- **O-2 (bajo) — Persistencia en memoria:** todo se pierde al reiniciar el proceso
  (AD-003). Es correcto para el estado actual, pero hay que migrar a PostgreSQL antes de
  producción; los Protocols de `stores/base.py` ya lo habilitan.
- **O-3 (bajo) — Política de contraseñas estricta:** exige símbolo; puede frustrar
  usuarios. Evaluar si se mantiene.
- **O-4 (bajo) — Nombre de esquema:** `resend_verification` usa `ForgotPasswordIn`
  (campo email). Funciona, pero el nombre induce a error.
- **O-5 (bajo) — Concurrencia:** los stores en memoria no usan locks; para una sola
  instancia single-threaded por request está bien, pero con WebSocket concurrente
  (async) podría haber condiciones de carrera en `room.players` / `match.scores`.
- **O-6 (info) — `room.updated` incluye `RoomOut` completo:** el evento WS publica el
  `model_dump()` de la sala; cuidar no filtrar datos sensibles (actualmente solo ids,
  usernames, avatar).

## 5. Cobertura de requisitos (rastreo rápido)
- Cuentas/auth: `auth_service.py` + `routers/auth.py`.
- Salas: `room_service.py` + `routers/rooms.py` + `catalog.py`.
- Partidas/turnos/puntos: `match_/turn_/scoring_service.py` + `routers/{matches,turns,scoring}.py`.
- Tiempo real: `realtime_service.py` + `ws.py`.
- Tests: `tests/test_matches.py` (verificar cobertura de los demás módulos).
