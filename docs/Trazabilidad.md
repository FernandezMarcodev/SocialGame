# Trazabilidad de Requisitos — “Es un 10 pero…”

**Propósito.** Garantizar la alineación completa entre los requisitos (SRS), el diseño
(DDD), los contratos JSON/WebSocket definidos en el Apéndice B del DDD y el código
implementado en `app/`, conforme a RNF-EST-002.

**Alcance.** Rama `develop` (commit `78763be`). Se revisaron los tres documentos base
(`SRS_Es_un_10_pero.md`, `DDD_Es_un_10_pero.md`, `Definicion_General_del_Sistema.md`),
los contratos del Apéndice B del DDD y el 100 % del código de `app/` (33 módulos,
~2.235 líneas).

**Método.** Para cada requisito (RF/RN) se localizó su módulo en el DDD, su contrato
en el Apéndice B y su implementación en `app/`. Los desajustes encontrados se corrigieron
**adaptando los documentos al sistema** (no se modificó el código), registrándose como
requisitos volátiles (RV) en el SRS §7.5.

---

## 1. Estado de la alineación

| Conjunto | Alineación | Observaciones |
| --- | --- | --- |
| SRS ↔ DDD | ✅ Alineados | Tras ajustar rondas (RV-012) y avatar (RV-001). |
| DDD ↔ Contratos JSON (B.1–B.3) | ✅ Alineados | Tras añadir `turn_index`, `total_rounds`, `profile_image_url`. |
| Contratos ↔ Código (`app/`) | ✅ Alineados | Campos de `MatchOut`/`PlayerOut`/`UserOut` coinciden con B.1/B.2.4. |
| WebSocket (B.2.7) ↔ Código | ⚠️ Parcial | Solo emiten `room.updated`, `room.cancelled`, `match.started` (RV-010, documentado). |
| Persistencia (AD-005) ↔ Código | ⚠️ Arquitectura objetivo | Código 100 % en memoria; PostgreSQL pendiente (nota añadida en B.2.8). |

**Resultado:** trazabilidad **exitosa**; las únicas divergencias son las deliberadas y
ya documentadas en el SRS (RV-008 abandono, RV-010 WebSocket parcial).

---

## 2. Matriz de trazabilidad (SRS → DDD → Contrato → Código)

### 2.1 Usuarios (RF-USR-001…007, RN-001…005)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| RF-USR-001 Registro | 4.2 / §B.2.1 | `POST /auth/register` | `auth_service.register` | Implementado |
| RF-USR-002/003 Unicidad | 4.2 | validación `UserStore` | `MemoryUserStore` (índices `[username]/[email]`) | Implementado |
| RF-USR-004 Validación | — | Pydantic `RegisterIn` | `core/security.validate_password_policy` | Implementado |
| RF-USR-005 Avatar automático | B.2.2 | `User.profile_image_url="/avatars/x.svg"` | `domain/avatars.avatar_url` | Implementado (+ RV-001) |
| RF-USR-006 Consultar perfil | B.2.2 | `GET /users/me` | `routers/users.get_me` | Implementado |
| RF-USR-007 Modificar perfil | B.2.2 | `PATCH /users/me` | `users_service.update_profile` | Implementado (+ RV-001) |
| RN-001/002 Unicidad | 4.2 | — | `auth_service.register` | Implementado |
| RN-003 Auth obligatoria | — | `HTTPBearer` | `api/deps.get_current_user` | Implementado |
| RN-004 Una sala a la vez | 4.3 | — | `room_service.create_room/join_room` | Implementado |
| RN-005 Avatar (sin carga → **con carga**) | B.2.2 | `PUT /users/me/avatar` | `users_service.update_avatar` | **Modificado (RV-001)** |

### 2.2 Autenticación (RF-AUT-001…009, RN-003)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| RF-AUT-001 Verificar correo | B.2.1 | `POST /auth/verify-email` | `auth_service.verify_email` | Implementado |
| RF-AUT-002 Reenviar | B.2.1 | `POST /auth/resend-verification` | `auth_service.resend_verification` | Implementado |
| RF-AUT-003/004 Login | B.2.1 | `POST /auth/login` | `auth_service.login` (identifier=user/email) | Implementado |
| RF-AUT-005 Bloqueo | B.2.1 | `ACCOUNT_BLOCKED` | `auth_service.login` (intentos) | Implementado |
| RF-AUT-006 Logout | B.2.1 | `POST /auth/logout` | `auth_service.logout` (revoca hash) | Implementado |
| RF-AUT-007 Cambiar clave | B.2.1 | `POST /auth/change-password` | `auth_service.change_password` | Implementado |
| RF-AUT-008/009 Recuperar | B.2.1 | `forgot/reset-password` | `auth_service.forgot/reset_password` | Implementado |
| AD-002 Token opaco + hash | B.2.1 | `access_token` | `security.hash_token` + `SessionStore` | Implementado |
| AD-006 Argon2id | 4.2 / §AD-006 | — | `security.PasswordHasherArgon2` | Implementado |

### 2.3 Salas (RF-SAL-001…008, RN-006…011)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| RF-SAL-001 Crear | B.2.3 | `POST /rooms` | `room_service.create_room` | Implementado |
| RF-SAL-002 Unir (solo código) | B.2.3 | `POST /rooms/{code}/join` | `room_service.join_room` | Implementado (RV-002) |
| RF-SAL-003 Consultar | B.2.3 | `GET /rooms/{code}` | `room_service.get_room` | Implementado |
| RF-SAL-004 Abandonar (pre-inicio) | B.2.3 | `POST /rooms/{code}/leave` | `room_service.leave_room` | Implementado |
| RF-SAL-005 Iniciar | B.2.3 | `POST /rooms/{code}/start` | `room_service.start_match` | Implementado |
| RF-SAL-006 Cancelar | B.2.3 | `DELETE /rooms/{code}` | `room_service.cancel_room` | Implementado |
| RF-SAL-007 Eliminar al finalizar | B.2.3 | evento `room.cancelled` | `match_service._finish` (elimina sala) | Implementado |
| RF-SAL-008 Condiciones ingreso | B.2.3 | errores `ROOM_FULL`… | `room_service.join_room` | Implementado |
| RN-006/007/008/009/010/011 | 4.3 | — | `room_service.*` | Implementado |
| GET `/matches/by-room/{code}` | B.3 | respaldo ingreso | `routers/matches.get_match_by_room` | Implementado (RV-002) |

### 2.4 Partidas (RF-PAR-001…007, RN-021…025)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| RF-PAR-001 Crear | B.2.4 | implícito en `start` | `match_service.create_match` | Implementado |
| RF-PAR-002 Inicializar | B.2.4 | — | `match_service.initialize_match` | Implementado |
| RF-PAR-003 Orden participación | B.2.4 | `turn_order[]` | `initialize_match` (3 permutaciones) | Implementado (**RV-012**) |
| RF-PAR-004 Estados | 4.4.2 | `match.state` | `Match.state` | Implementado |
| RF-PAR-005 Avance de ronda | 4.4.2 | — | `match_service.advance_round` | Implementado (**RV-012**) |
| RF-PAR-006 Finalizar | B.2.4 | — | `match_service._finish` | Implementado |
| RF-PAR-007 Resultado | B.2.4 / B.2.6 | `GET /matches/{id}/result` | `match_service._result_of` | Implementado |
| RN-021…025 (3 rondas) | 4.4.2 / B.2.4 | `total_rounds`, `turn_index` | `MatchService._TOTAL_ROUNDS=3` | **Modificado (RV-012)** |

### 2.5 Turnos (RF-TUR-001…011, RN-012…017,020)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| RF-TUR-001 Iniciar turno | B.2.5 | `POST .../phrase` (arranque) | `turn_service._create_turn` | Implementado |
| RF-TUR-002 Notificar inicio | B.2.7 | `turn.started` (WS) | — (polling REST) | **Parcial (RV-010)** |
| RF-TUR-003 Frase + secreto | B.2.5 | `POST .../phrase` | `turn_service.submit_phrase` | Implementado |
| RF-TUR-004 Validar | B.2.5 | `PHRASE_INVALID`/`SCORE_INVALID` | `submit_phrase` (3–200, 1–10) | Implementado |
| RF-TUR-005 Tiempo autor | AD-008 | `expires_at` | `turn_service.settle_expired` (diferido) | Implementado |
| RF-TUR-006 Votación | B.2.5 | `POST .../votes` | `turn_service.submit_vote` | Implementado |
| RF-TUR-007 Voto | B.2.5 | `POST .../votes` | `turn_service.submit_vote` | Implementado |
| RF-TUR-008 Tiempo votación | AD-008 | `voting_ends_at` | `turn_service.settle_expired` | Implementado |
| RF-TUR-009 Cerrar votación | B.2.5 | `turn.voting.stopped` (WS) | `turn_service._finalize` | Implementado (WS RV-010) |
| RF-TUR-010 Publicar resultado | B.2.5 | `turn.result` (WS) | `turn_service.serialize_turn` | Implementado (WS RV-010) |
| RF-TUR-011 Siguiente jugador | B.2.5 | — | `turn_service._advance` | Implementado |
| RN-012/013/014/015/016 | B.2.5 | `secret_score` oculto | `serialize_turn` (solo en `finished`) | Implementado |
| RN-017 Abandono en partida | 4.4.3 | — | `leave_room` **bloquea** (no abandona) | **Divergencia (RV-008)** |
| RN-020 Publicar tras turno | B.2.5 | `turn.result` | `serialize_turn` | Implementado (WS RV-010) |

### 2.6 Puntuación (RF-PUN-001…004, RN-018/019/023)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| RF-PUN-001 Puntos turno | B.2.6 | `turn.result.points` | `scoring_service.turn_points` | Implementado |
| RF-PUN-002 Marcador | B.2.6 | `scoreboard.updated` (WS) | `scoring_service.apply_turn` | Implementado (WS RV-010) |
| RF-PUN-003 Consultar | B.2.6 | `GET .../scoreboard` | `scoring_service.scoreboard` | Implementado |
| RF-PUN-004 Resultado final | B.2.6 | `GET .../result` | `scoring_service.result` | Implementado |
| RN-018/019 1 pt por acierto exacto | B.2.6 | — | `scoring_service.turn_points` | Implementado |
| RN-023 Empate | B.2.6 | `winner_id=null, tied=true` | `match_service._result_of` | Implementado |

### 2.7 Tiempo real (RF-COM-001…010)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| RF-COM-001 Handshake WS | B.2.7 | `/api/v1/ws?token=` | `api/ws.websocket_endpoint` | Implementado |
| RF-COM-002 Gestión conexión | B.2.7 | `ConnectionManager` | `realtime_service.ConnectionManager` | Implementado |
| RF-COM-004 Cambios de sala | B.2.7 | `room.updated` | `routers/rooms` + `bus.publish` | Implementado |
| RF-COM-005 Inicio partida | B.2.7 | `match.started` | `routers/rooms.start_match` | Implementado |
| RF-COM-006/007/008/009 Eventos turno/score/fin | B.2.7 | `turn.*`/`scoreboard.updated`/`match.finished` | — (no emitidos) | **Pendiente (RV-010)** |

### 2.8 Persistencia (RF-PER-001…005, AD-003/AD-005)

| Requisito | DDD | Contrato | Código | Estado |
| --- | --- | --- | --- | --- |
| AD-003 Estado en memoria | 4.3 / B.2.8 | — | `stores/memory.py` | Implementado |
| AD-005 PostgreSQL (objetivo) | B.2.8 | — | *no implementado aún* | **Pendiente** |
| RN-024 Eliminar sala al finalizar | B.2.3 | — | `match_service._finish` | Implementado |

---

## 3. Alineación de contratos JSON ↔ código

| Objeto/Contrato (DDD) | Campos en código (`app/api/schemas.py`) | Alineado |
| --- | --- | --- |
| `User` (B.1) | `id, username, email, verified, profile_image_url, created_at` | ✅ |
| `Player` (B.1) | `id, username, joined_at, profile_image_url` | ✅ (añadido `profile_image_url`) |
| `Modality` (B.1) | `id, name, template` | ✅ |
| `Room` (B.2.3) | `code, state, creator_id, modality, players[], min/max_players, created_at` | ✅ |
| `Match` (B.2.4) | `match_id, room_code, state, players[], turn_order, current_turn, scores, created_at, turn_index, total_rounds` | ✅ (añadidos `turn_index`, `total_rounds`) |
| `Turn` (B.2.5) | `turn_id, match_id, author_id, state, phrase, secret_score, created_at, expires_at, voting_ends_at, votes[], votes_count, points` | ✅ |
| `Scoreboard` (B.2.6) | `round, scores` | ✅ |
| `Result` (B.2.6) | `winner_id, tied, scores` | ✅ |
| Eventos WS (B.2.7) | emitidos: `room.updated`, `room.cancelled`, `match.started` | ⚠️ RV-010 |

---

## 4. Ajustes aplicados a los documentos (trazabilidad exitosa)

Para lograr la alineación **sin tocar el código**, se adaptaron los documentos:

1. **RV-012 (nuevo en SRS §7.5).** El sistema fija **3 rondas** (`MatchService._TOTAL_ROUNDS=3`),
   no la “única ronda” original. Se actualizaron:
   - `SRS`: RN-021, RN-022, RN-025 y el glosario → “3 rondas”.
   - `Definicion_General`: §1.3 y §3 (RN-023) → “3 rondas”.
   - `DDD`: §4.4 (línea “una única ronda”), B.2.4 (`turn_order` = 3 bloques).
2. **Avatar personalizado (RV-001 ya existente).** Se corrigió el texto obsoleto:
   - `SRS` RN-005 → permite carga (`PUT /users/me/avatar`).
   - `Definicion_General` §1.3 → se retiró la exclusión de carga de imagen.
   - `DDD` B.2.2 → “puede reemplazarse por imagen propia”.
3. **Campos de contrato faltantes.** Añadidos en `DDD` B.1/B.2.4:
   - `Player.profile_image_url`.
   - `Match.turn_index`, `Match.total_rounds`.
4. **Persistencia (AD-005 / B.2.8).** Se aclaró que PostgreSQL es arquitectura objetivo
   **no implementada**; el build actual es 100 % en memoria (`stores/memory.py`),
   coherente con AD-003. Esto alinea el DDD con el código real.

## 5. Divergencias deliberadas (ya documentadas en SRS §7.5)

- **RV-008** — RN-017 (abandono durante partida): el sistema **bloquea** el abandono
  (`leave_room` lanza `ROOM_NOT_AVAILABLE`); el descarte de turnos aplica solo a timeouts.
- **RV-010** — Eventos de turno/marcador/finalización no se emiten por WS; el frontend
  los obtiene por polling REST. El canal WS cubre por ahora sala + inicio de partida.

Ambas figuran como “Pendiente de confirmación” / “Pendiente” en el SRS, manteniendo la
trazabilidad completa y explícita.
