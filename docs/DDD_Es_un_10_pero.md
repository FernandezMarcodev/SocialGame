# DOCUMENTO DE DISEÑO DE SOFTWARE

**Sistema “Es un 10 pero…”**

Videojuego multijugador por turnos — Arquitectura cliente-servidor

Documento DDD · Versión 1.0 · Basado en SRS v1.0 · Estándar IEEE 1016-2009

Referencia: DDD-ES10P-001

---

# 1. Identificación del diseño

El presente documento constituye la descripción del diseño de software (Software Design Description, SDD) del sistema “Es un 10 pero…”, conforme a lo establecido por el estándar IEEE 1016-2009. El diseño se deriva de la Especificación de Requisitos de Software (SRS v1.0) y describe la arquitectura, los componentes, las interfaces, los datos y el comportamiento del sistema considerando los requisitos funcionales y no funcionales allí definidos.

| Dato | Valor |
| --- | --- |
| Identificador del diseño | DDD-ES10P-001 |
| Nombre del sistema | “Es un 10 pero…” — Videojuego multijugador por turnos |
| Documento de requisitos base | SRS v1.0 — Especificación de Requisitos de Software (2026) |
| Estándares aplicados | IEEE 1016-2009 (descripción de diseño de software); IEEE 42010 (Arquitectura); IEEE 830/IEEE 29148 (requisitos) |
| Versión del diseño | 1.0 |
| Estado | Preliminar |
| Alcance | Diseño del backend (API REST + WebSocket + persistencia + despliegue) y contratos de interfaz para clientes. Queda fuera de alcance el diseño de una interfaz gráfica concreta. |
| Stack tecnológico | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL 16 · Docker Compose · WebSocket nativo |

El diseño sigue la descomposición en ocho módulos funcionales definidos en el SRS (usuarios, autenticación, salas, partidas, turnos, puntuación, comunicación en tiempo real y persistencia), garantizando trazabilidad de cada requisito hacia los elementos de diseño (sección 9).

# 2. Interesados y aspectos de interés

## 2.1 Interesados

Se identifican los siguientes interesados (stakeholders) del sistema y su relación con el diseño:

| Interesado | Rol | Aspectos de interés principales |
| --- | --- | --- |
| Jugador (usuario final) | Consume la API mediante un cliente (web, móvil, escritorio). | Usabilidad, tiempos de respuesta, feedback de operaciones, claridad del estado de juego. |
| Cliente consumidor | Aplicación que implementa la interfaz gráfica sobre los contratos definidos. | Contratos REST y WebSocket estables, documentación OpenAPI, consistencia de eventos. |
| Desarrollador backend | Implementa y evoluciona la API y la lógica de negocio. | Modularidad, bajo acoplamiento, mantenibilidad, pruebas automatizadas. |
| Operador / DevOps | Despliega y opera el sistema (Docker, PostgreSQL, entorno). | Portabilidad, configuración por variables de entorno, eficiencia en producción. |
| Administrador de base de datos | Administra el almacenamiento persistente. | Integridad de datos, modelo de datos claro, migraciones controladas. |
| Equipo de calidad (QA) | Verifica el cumplimiento de requisitos. | Trazabilidad requisito-diseño, criterios verificables, estados y excepciones documentados. |
| Dueño del producto | Define prioridades y evolución prevista del sistema. | Extensibilidad a nuevos clientes y modalidades, cumplimiento de reglas de negocio. |

## 2.2 Aspectos de interés (Design Concerns)

Los aspectos de interés (concerns) orientan la selección de puntos de vista. Se vinculan con los requisitos no funcionales del SRS:

| ID | Aspecto de interés | Requisito asociado | Punto(s) de vista que lo abordan |
| --- | --- | --- | --- |
| CA-01 | Separación de responsabilidades y modularidad | RNF-MAN-001, RNF-MAN-002 | Composición, Arquitectónico |
| CA-02 | Rendimiento y tiempos de respuesta de la API | RNF-EFI-001 | Interacción, Despliegue |
| CA-03 | Sincronización en tiempo real de eventos | RNF-EFI-002, RNF-EFI-003 | Interacción, Comportamiento |
| CA-04 | Seguridad (hash de contraseñas, autenticación, validación, cifrado) | RNF-SEG-001 a 004 | Interacción, Información |
| CA-05 | Fiabilidad y consistencia del estado del juego | RNF-FIA-001 a 003 | Comportamiento, Información |
| CA-06 | Usabilidad y claridad del estado | RNF-USA-001, RNF-USA-002 | Interacción |
| CA-07 | Mantenibilidad y pruebas | RNF-MAN-001 a 003 | Composición |
| CA-08 | Portabilidad y despliegue mediante Docker | RNF-POR-001, RNF-POR-002 | Despliegue |
| CA-09 | Interoperabilidad (JSON, HTTP, WebSocket) | RNF-INT-001, RNF-INT-002 | Interacción, Información |
| CA-10 | Eliminación de información temporal | RNF-DAT-001, RNF-DAT-002 | Información, Comportamiento |
| CA-11 | Trazabilidad con la especificación | RNF-EST-002 | Trazabilidad (sección 9) |

# 3. Puntos de vista del diseño

Un punto de vista (viewpoint) define qué se muestra, para quién y con qué notación. Los puntos de vista del SDD de “Es un 10 pero…” derivan de los aspectos de interés de la sección 2.2. Cada punto de vista genera una vista específica en la sección 4.

## 3.1 Punto de vista arquitectónico

Propósito: Mostrar la estructura de alto nivel del sistema: cliente, API, base de datos y canal en tiempo real, y sus relaciones.

Notación: Diagrama de contexto y diagrama de contenedores (estilo C4) representados como diagramas de bloques.

Espectadores: Interesados generales, dueño del producto, desarrolladores backend.

Concerns: CA-01, CA-05, CA-06, CA-09.

## 3.2 Punto de vista de composición

Propósito: Mostrar la descomposición interna del backend en módulos, capas y paquetes, con sus dependencias.

Notación: Diagrama de paquetes / capas y tablas de dependencias.

Espectadores: Desarrolladores backend, QA, DevOps.

Concerns: CA-01, CA-07, CA-05.

## 3.3 Punto de vista de información

Propósito: Mostrar la estructura de datos persistentes y temporales: entidades, atributos, relaciones y estados persistidos.

Notación: Modelo entidad-relación y tablas de atributos.

Espectadores: Desarrolladores backend, DBA, QA.

Concerns: CA-04, CA-05, CA-10, CA-09.

## 3.4 Punto de vista de comportamiento

Propósito: Mostrar los estados de las entidades dinámicas (sala, partida, turno), las transiciones válidas y el flujo de la lógica de juego.

Notación: Máquinas de estados y diagramas de actividad.

Espectadores: Desarrolladores backend, QA, dueño del producto.

Concerns: CA-03, CA-05, CA-10.

## 3.5 Punto de vista de interacción

Propósito: Mostrar cómo se comunican el cliente y el servidor: contratos REST/JSON, eventos WebSocket y secuencias de uso principales.

Notación: Diagramas de secuencia y definición de contratos de mensajes.

Espectadores: Clientes consumidores, backends, QA.

Concerns: CA-02, CA-03, CA-04, CA-06, CA-09.

## 3.6 Punto de vista de despliegue

Propósito: Mostrar el entorno de ejecución: contenedores, servicios, red, puertos y configuración del entorno.

Notación: Diagrama de despliegue.

Espectadores: DevOps, operador, DBA, desarrolladores.

Concerns: CA-02, CA-08.

# 4. Vistas del diseño

Esta sección materializa cada punto de vista en una vista concreta del sistema.

## 4.1 Vista arquitectónica

### 4.1.1 Diagrama de contexto

```
+------------------------+        Contratos JSON        +----------------------+
|      CLIENTE           | --------------------------->  |   API REST          |
| (web / móvil /         |                                |   (FastAPI)         |
|  escritorio)           | <---------------------------  |  Lógica de negocio  |
+------------------------+        Respuestas/eventos     |  Autenticación      |
|                                               |  Salas / Partidas   |
|   Canal WebSocket (tiempo real)               |  Turnos/Puntuación  |
+---------------------------------------------> |  Comunicación RTR   |
+----------+-----------+
|
```

                                                          SQL (async/psycopg)

```
                                                                   |
+---------------v-------------+
|        BASE DE DATOS       |
|  PostgreSQL 16             |
|  (Usuarios, modalidades,   |
|   frases, persistencia)    |
+----------------------------+
```

### 4.1.2 Diagrama de contenedores

```
+-------------------------------------------------------------------------------+
|                          API BACKEND (un solo contenedor)                     |
|                                                                               |
|  +-----------------------------------------------------------------------+   |
|  |  CAPA DE INTERFACES (API)       routers REST + gateway WebSocket       |   |
|  +------------------------------------------+----------------------------+   |
|  |  CAPA DE APLICACIÓN (servicios)  Auth, Users, Rooms, Matches,          |   |
|  |                                   Turns, Scoring, Realtime, Persist.   |   |
|  +------------------------------------------+----------------------------+   |
|  |  CAPA DE DOMINIO  modelos + máquinas de estado + reglas de negocio RN  |   |
|  +------------------------------------------+----------------------------+   |
|  |  CAPA DE INFRAESTRUCTURA  repositorios, stores en memoria, bus de     |   |
|  |                          eventos, gestor de timers, email, config     |   |
|  +--------------------------------------------------------------------------+  |
+--------+-------------------------------+---------------------------------------+
|                               |
```

      PostgreSQL                       (estado temporal en memoria:

      (persistente)                     sesiones, salas, partidas, turnos)

Regla clave: el estado efímero del juego (salas, partidas, turnos, sesiones, códigos) vive en memoria dentro del proceso de la API (decisión AD-003). Solo persistirán usuarios, modalidades y frases, cumpliendo RN-024 y RNF-DAT-001/002.

## 4.2 Vista de composición

### 4.2.1 Descomposición en capas y paquetes

app/

```
├── main.py                       # Creación de la aplicación, routers, WS, lifespan
├── core/
│   ├── config.py                 # Configuración por variables de entorno (pydantic-settings)
│   ├── security.py               # Argon2id, generación y hashing de tokens
│   ├── database.py               # Motor async, sesión SQLAlchemy, Alembic
│   └── exceptions.py             # Jerarquía de errores de dominio y de aplicación
├── api/
│   ├── deps.py                   # Dependencias FastAPI (autenticación, servicios)
│   ├── v1/
│   │   ├── routes/               # auth.py, users.py, rooms.py, matches.py, modalities.py
│   │   ├── schemas/              # esquemas Pydantic de petición/respuesta
│   │   └── ws.py                 # gateway WebSocket + enrutado de eventos
│   └── errors.py                 # manejo uniforme de errores HTTP / WS
├── application/
│   └── services/                 # auth, users, rooms, matches, turns, scoring, realtime, persistence
├── domain/
│   ├── models/                   # room.py, match.py, turn.py, player.py, vote.py
│   ├── events.py                 # eventos de dominio (publ/sub)
│   └── rules.py                  # reglas de negocio y validaciones (RN-…)
└── infrastructure/
├── repositories/             # users, modalities, phrases (SQLAlchemy)
├── stores/                   # session_store, room_store, match_store, code_store
├── realtime/                 # event_bus.py, connection_manager.py
├── timing/                   # timer_manager.py (expiración de turnos/votaciones)
└── email/                    # provider.py (interfaz), resend.py, smtp.py, fake.py
```

tests/                            # pruebas unitarias y de contrato

### 4.2.2 Dependencias entre módulos

Las dependencias fluyen de interfaces hacia aplicación hacia dominio y hacia infraestructura (regla de dependencia). El módulo de comunicación en tiempo real es atravesado por los demás módulos para publicar eventos, pero ningún módulo importa la interfaz gráfica ni conoce a los clientes.

| Módulo | Depende de | Es dependido por |
| --- | --- | --- |
| Usuarios | Persistencia, Seguridad | Autenticación, Salas |
| Autenticación | Usuarios, Persistencia, Email, Seguridad | — (todos los endpoints protegidos) |
| Salas | Usuarios, Comunicación RTR, Modalidades | Partidas |
| Partidas | Salas, Turnos, Puntuación, Comunicación RTR | — |
| Turnos | Partidas, Puntuación, Comunicación RTR, Temporización | Partidas |
| Puntuación | Turnos, Partidas | Turnos, Partidas |
| Comunicación RTR | Persistencia (roles mínimos) | Salas, Partidas, Turnos, Puntuación |
| Persistencia | Base de datos | Todos los anteriores |

## 4.3 Vista de información

### 4.3.1 Modelo entidad-relación (persistente)

```
+----------------+       +----------------+       +----------------+
|     users      |       |   modalities   |       |    phrases     |
+----------------+       +----------------+       +----------------+
| id (PK, UUID)  |       | id (PK)        |       | id (PK)        |
| username (AK)  |       | code (AK)      |       | text           |
| email (AK)     |       | template       |       | modality_id FK |
| password_hash  |       | is_active      |       | author_id FK -> users
| profile_image  |       | created_at     |       | match_id (ref. ephemeral)
| is_verified    |       +----------------+       | created_at     |
| failed_attempts|                               +----------------+
| locked_until   |
| created_at     |
| updated_at     |
+----------------+
```

                         1                    N                  N

                  modalities ------------------- phrases <------ users

### 4.3.2 Entidades temporales (en memoria)

Estas entidades viven exclusivamente en memoria durante el ciclo de vida de una partida y se descartan al finalizar (RN-024, RF-PER-004).

| Entidad | Atributos principales | Ciclo de vida |
| --- | --- | --- |
| Session | token (opaco), user_id, created_at, expires_at (TTL) | Creada en login; invalidada en logout o al expirar. In-memory. |
| Room | code (6 chars), creator_id, modality_id, state, players[], max_players=6 | Creada en POST /rooms; eliminada al cancelar o al finalizar partida. |
| Match | id, room_id, modality_id, state, order[], scores{}, turn_index | Creada al iniciar; eliminada al finalizar. |
| Turn | id, match_id, author_id, state, phrase, secret_score, votes{}, timer | Creada por el módulo de turnos; desechada al finalizar turno. |
| Vote | turn_id, voter_id, value (1-10) | Emitido durante votación; contenido con los resultados. |
| CodeToken | user_id, tipo (verify/reset), token_hash, expires_at | Creado para verificación/reset; consumido o expirado. |

### 4.3.3 Persistencia e integración de datos

Acceso mediante SQLAlchemy 2.0 async con migraciones Alembic (RNF-FIA-003). Unicidad garantizada por índices únicos en username y email (RN-001, RN-002). Frases se almacenan para futuras extensiones (RF-PER-005). Salas y partidas no se persisten (RNF-DAT-001/002).

## 4.4 Vista de comportamiento

### 4.4.1 Máquina de estados — Sala

```
                 +-----------------+   creador inicia   +-----------+
```

    create ----> |    DISPONIBLE   | -----------------> | EN JUEGO  | ----> (fin partida/RNF)

```
                 |  (esperando)    |                    +-----------+
+-----------------+                          |
| x (cancelación por creador)          | casa / finaliza
```

                       v                                      v

```
                 +-----------------+              +-----------+-----------+
|   CANCELADA     |              |     ELIMINADA          |
+-----------------+              +------------------------+
```

                 transición a eliminada (RN-024)

### 4.4.2 Máquina de estados — Partida

```
        +-----------+     RF-PAR-002      +------------+   primer turno (RF-TUR-001)
```

creada |  CREADA   | -------------------> | INICIALIZADA| ---------------------------+

```
       +-----------+                       +------------+                           |
```

                                                                                     v

```
                                                                        +---------------------+
```

                                  todos los turnos completados          |      EN CURSO       |

                               RF-PAR-006 / RN-021 / RN-022             +---------------------+

```
                                                                                     |
+----------------------------------------------------------------+
|                                                                |
```

< 2 jugadores activos (RN-017)                                              se completó la ronda

```
                     |                                                                |
```

                     v                                                                v

```
         +---------------------+                                  +---------------------+
|     FINALIZADA      | <------------------------------- |    FINALIZADA       |
+---------------------+                                  +---------------------+
|                             resultado: ganador o empate (RN-023, RF-PAR-007)
```

### 4.4.3 Máquina de estados — Turno

```
            +-----------+    frase + secreto (RF-TUR-003)   +-------------+
```

 iniciado ->|  ACTIVO   | ---------------------------------> | EN VOTACIÓN |

 (RF-TUR-01)| (autor)   |                                    |  (votantes) |

```
            +-----------+                                    +-------------+
| tiempo de autor agotado                          |  todos votan o tiempo
| abandono del autor (RN-017)                     |  de votación agotado
```

                 v                                                  v

```
            +-------------+                                   +---------------+
| DESCARTADO  |                                   |  FINALIZADO   |
+-------------+                                   | (resultado)   |
+---------------+
```

### 4.4.4 Diagrama de actividad — Desarrollo de un turno

```
[ Iniciar turno (RF-TUR-001, RF-TUR-002) ] -> [ Autor redacta frase y asigna
```

                                                    puntaje secreto 1-10 ]

```
          |  a tiempo                                              | expira (RF-TUR-005)
```

          v                                                        v

      [ Validar frase (3-200) y puntaje (RF-TUR-004) ]        [ Turno DESCARTADO ]

```
          |                                                          |
```

          v   (RF-TUR-003, RF-TUR-006)                               v

      [ Estado EN VOTACIÓN, publicar frase ]              [ avanzar al siguiente turno ]

```
          |                                                        (RF-TUR-011, RF-PAR-005)
```

          v

      [ Votantes emiten voto 1-10 (RF-TUR-007, RN-014/015) ]

```
          |  todos votaron o tiempo de votación (RF-TUR-008)
```

          v

```
      [ Cerrar votación (RF-TUR-009) ] -> [ Calcular puntos del autor (RF-PUN-001)
```

                                             = nº de aciertos exactos del secreto ]

```
          |
```

          v

      [ Publicar resultado: secreto + votos + puntos (RF-TUR-010, RN-020) ]

```
          |
```

          v

```
      [ Actualizar marcador (RF-PUN-002) ] -> [ Fin de turno ]
```

## 4.5 Vista de interacción

### 4.5.1 Secuencia — Registrar, autenticar y crear sala

Cliente                    API                                     BD / Stores

```
  |  POST /auth/register     |                                         |
|------------------------->|   validar unicidad (RF-USR-002/003)     |
|                         |---------------------------------------->|  SELECT username/email
|                         |   hash pwd (RNF-SEG-001), avatar, crear  |
|                         |---------------------------------------->|  INSERT user
|  201 {user}             |                                         |
|<-------------------------|                                         |
|  POST /auth/verify-email |  validar token verify (RF-AUT-001)      |
|------------------------->|---------------------------------------->|  marca verified
|  200                     |                                         |
|<-------------------------|                                         |
|  POST /auth/login        |                                         |
|------------------------->|[ validar credenciales (RF-AUT-004)      |
|                         |  controlar intentos fallidos (RF-AUT-005)|
|                         |  generar sesión opaca ]----------> SessionStore
|  200 {token}             |                                         |
|<-------------------------|                                         |
|  POST /rooms {modality}  |  RN-004 (no en otra sala),              |
|------------------------->|  generar código (RF-SAL-001)------> RoomStore
|  201 {code, room}        |                                         |
|<-------------------------|                                         |
```

### 4.5.2 Secuencia — Ronda y turno con votación

Autor                 Votantes                API                            Realtime (broker WS)

```
 |     POST /rooms/{c}/start (RF-SAL-005)      |   RF-PAR-001/002/003 (orden)       |
|-------------------------------------------->|  validate RN-007/008               |
|                                             |  crear Match -> RoomStore          |
|                                             |-PUBLISH match.started------------>|-> a todos
|  POST /matches/{m}/phrase (RF-TUR-003)      |   validar autor, frase, secreto    |
|-------------------------------------------->|   RN-012/013                       |
|                                             |  turn -> EN VOTACIÓN (RF-TUR-006)  |
|                                             |-PUBLISH turn.phrase + voting------>|-> a votantes
|       POST /matches/{m}/votes (RF-TUR-007)  |  validar votante (RN-014/015/016)  |
|       <--------------------------------------|                                    |
|       [ resto de votantes vota ]            |  todos o timeout (RF-TUR-008)      |
|                                             |  cerrar (RF-TUR-009)               |
|                                             |  puntuar autor (RF-PUN-001)        |
|                                             |-PUBLISH turn.result + scoreboard-->|-> a todos
|                                             |  siguiente turno o fin (RF-PAR-005 |
|                                             |   RF-TUR-011 / RF-PAR-006)         |
```

### 4.5.3 Flujo de abandono y expiración

Desconexión durante la partida se traduce en abandono (RF-COM-002/010, RN-017): el jugador pasa a inactivo, se descartan sus turnos como autor pendientes, y si quedan menos de 2 jugadores activos la partida finaliza. La expiración de tiempos se gestiona con el gestor de timers (RF-TUR-005/008).

## 4.6 Vista de despliegue

```
+---------------------------+   red bridge interna (default)   +---------------------------+
|   Contenedor: api          | <------------------------------> |   Contenedor: db          |
|   imagen: es10p-api        |                              |   imagen: postgres:16       |
|   puertos: 8000 (público)  |                              |   puerto interno: 5432      |
|   variables de entorno     |                              |   volumen: pgdata          |
|   (ver 4.6.1)              |                              |   healthcheck de pg        |
+---------------------------+                              +---------------------------+
|
+---------- clients (REST 8000 / WS 8000/ws)
```

### 4.6.1 Variables de entorno

| Variable | Ejemplo | Uso |
| --- | --- | --- |
| DATABASE_URL | postgresql+asyncpg://es10p:@db:5432/es10p | Cadena de conexión a PostgreSQL |
| SESSION_TTL_HOURS | 8 | Vigencia de sesiones opacas |
| AUTHOR_TIMEOUT_SECONDS | 60 | Tiempo de redacción del autor |
| VOTING_TIMEOUT_SECONDS | 30 | Tiempo de votación |
| MAX_FAILED_ATTEMPTS | 5 | Límite de intentos fallidos de login |
| LOCK_DURATION_MINUTES | 15 | Bloqueo temporal tras intentos fallidos |
| VERIFY_TOKEN_TTL | 24h | Vigencia del código de verificación de email |
| RESET_TOKEN_TTL | 30m | Vigencia del token de recuperación de contraseña |
| EMAIL_PROVIDER | resend \| smtp \| fake | Proveedor de email (fake en desarrollo) |
| SECRET_KEY | … | Semilla para tokens y firmas |

Cumple RNF-POR-001 (arranque con docker-compose up) y RNF-POR-002 (sin credenciales en el código).

# 5. Elementos del diseño

Los elementos del diseño son los componentes, estructuras, datos, comportamientos e interfaces que componen el sistema. Se presentan agrupados según su naturaleza.

## 5.1 Elementos estructurales

Los elementos estructurales corresponden a los componentes físicos y lógicos del sistema, con sus responsabilidades.

| Elemento | Tipo | Responsabilidad |
| --- | --- | --- |
| API REST (FastAPI) | Componente lógico | Exponer operaciones por HTTP/JSON; autenticación; validación. |
| Gateway WebSocket | Componente lógico | Aceptar conexiones persistentes, autenticar y enrutar eventos en tiempo real. |
| Servicios de aplicación | Componente lógico | Orquestar casos de uso (registro, login, salas, partidas, turnos, puntuación). |
| Modelos de dominio | Componente lógico | Encapsular estado y reglas de negocio de Room, Match, Turn, Vote, Player. |
| Repositorios | Componente lógico | Persistir y recuperar usuarios, modalidades y frases (SQLAlchemy). |
| Stores en memoria | Componente lógico | Sesiones, salas, partidas y códigos temporales (lifecycle transitorio). |
| Bus de eventos | Componente lógico | Desacoplar publicación de eventos de su envío por WebSocket. |
| Gestor de timers | Componente lógico | Expiración de tiempos de autor y votación. |
| Proveedor de email | Componente externo | Envío de verificación y recuperación de contraseña. |
| PostgreSQL | Componente externo | Almacenamiento persistente. |

## 5.2 Elementos de comportamiento

Elementos que definen comportamiento dinámico del sistema.

| Elemento | Descripción |
| --- | --- |
| Máquina de estados de Sala | DISPONIBLE → EN JUEGO → ELIMINADA \| CANCELADA → ELIMINADA. |
| Máquina de estados de Partida | CREADA → INICIALIZADA → EN CURSO → FINALIZADA; cancelación anticipada. |
| Máquina de estados de Turno | ACTIVO → EN VOTACIÓN → FINALIZADO \| DESCARTADO. |
| Flujo de registro/verificación | Registro, envío de código, verificación, login con control de intentos. |
| Flujo de una ronda | Inicio de turno, redacción, votación, cierre, puntuación, publicación, siguiente turno. |
| Flujo de abandono | Detección de desconexión, actualización de estado y reglas RN-017/RN-022. |
| Temporizadores | Tiempo de autor (60 s) y de votación (30 s) configurables; acciones de expiración definidas. |

## 5.3 Elementos de datos

### 5.3.1 Tablas persistentes

| Tabla | Atributos clave | Restricciones |
| --- | --- | --- |
| users | id (UUID PK), username, email, password_hash, profile_image, is_verified, failed_attempts, locked_until, created_at, updated_at | username y email ÚNICOS (RN-001, RN-002); password_hash con Argon2id (RNF-SEG-001) |
| modalities | id (PK), code (único), template, is_active, created_at | Códigos únicos; seed inicial: “es-un-10-pero” y “es-un-1-pero” |
| phrases | id (PK), text, modality_id (FK), author_id (FK users), match_id (ref. efímera), created_at | text entre 3 y 200 caracteres (RF-TUR-004) |

### 5.3.2 Estructuras temporales

| Estructura | Campos | Ubicación |
| --- | --- | --- |
| Session | token, user_id, created_at, expires_at | SessionStore (memoria) |
| Room | code, creator_id, modality_id, state, players[], max_players=6 | RoomStore (memoria) |
| Match | id, room_id, modality_id, state, order[], scores{}, turn_index | MatchStore (memoria) |
| Turn | id, match_id, author_id, state, phrase, secret_score, votes[], expires_at | MatchStore (memoria) |
| CodeToken | user_id, kind (verify\|reset), token_hash, expires_at | CodeStore (memoria) |

## 5.4 Interfaces

Contratos formales entre el cliente y el sistema, y entre módulos internos. El detalle completo de mensajes y códigos de error se encuentra en el Apéndice B.

| Interfaz | Descripción | Detalle |
| --- | --- | --- |
| REST /api/v1/* | Operaciones CRUD y de dominio por HTTP/JSON | Apéndice B.3 — catálogo de endpoints |
| WebSocket /api/v1/ws | Eventos de tiempo real push al cliente | Apéndice B.4 — catálogo de eventos |
| Interfaz interna de servicios | Llamadas entre servicios de aplicación | Sección 4.2.2 (dependencias) |
| Interfaz de repositorios | Acceso a datos (SQLAlchemy) | Sección 4.3 |
| Interfaz de email | Proveedor intercambiable (fake/smtp/resend) | Sección 5.5 |

## 5.5 Componentes

| Componente | Entradas | Salidas | Dependencias |
| --- | --- | --- | --- |
| AuthService | Credenciales, tokens | Sesión/token, verificación de email | UserRepository, security, EmailProvider, SessionStore |
| UserService | Datos de registro/perfil | Usuario validado y persistido | UserRepository, security, PersistenceService |
| RoomService | Acciones de sala | Salas creadas/actualizadas, eventos | RoomStore, UserService, ModalidadRepository |
| MatchService | Inicio/finalización de partida | Instancias de partida, resultado | MatchStore, TurnService, ScoringService |
| TurnService | Frase, puntaje secreto, votos | Turnos avanzados, resultados de turno | MatchStore, ScoringService, TimerManager, EventBus |
| ScoringService | Secreto + votos | Puntos del autor, marcador | MatchStore |
| RealtimeService | Eventos de dominio | Mensajes WS a clientes | EventBus, ConnectionManager |
| PersistenceService | Datos a almacenar/consultar | Registros persistentes | Repositories, database |
| EventBus | Eventos publicados | Suscripciones notificadas | — |
| ConnectionManager | Conexiones WS autenticadas | Envío de mensajes a destinatarios | SessionStore |
| TimerManager | Configuración de tiempos | Eventos de expiración | — |

# 6. Justificación del diseño

## 6.1 Decisiones

Las decisiones principales del diseño, identificadas como AD-001 a AD-010, se listan de forma resumida aquí y se formalizan como Registros de Decisión Arquitectónica (ADR) en el Apéndice A.

| ID | Decisión | Resumen |
| --- | --- | --- |
| AD-001 | Monolito modular en una sola API FastAPI | Backend único y desplegable en un contenedor, organizado en capas y módulos (RNF-MAN-001/002, RNF-IMP-001). |
| AD-002 | Tokens de sesión opacos en servidor | Sesión en memoria con TTL; permite invalidación inmediata (logout) y bloqueo por intentos fallidos (RF-AUT-005/006, RNF-SEG-002). |
| AD-003 | Estado de juego en memoria | Salas, partidas y turnos transitorios en memoria; se eliminan al finalizar (RN-024, RNF-DAT-001/002). Permite bajo retardo y consistencia (RNF-EFI-001/003, RNF-FIA-002). |
| AD-004 | WebSocket nativo + bus de eventos en proceso | Comunicación RTR sin dependencias externas adicionales; cumple RNF-EFI-002 e RNF-INT-002. |
| AD-005 | SQLAlchemy 2.0 async + Alembic + PostgreSQL | Persistencia asíncrona y migraciones versionadas (RNF-FIA-003, RNF-EST-002). |
| AD-006 | Autenticación con hash Argon2id y validación Pydantic | Cumple RNF-SEG-001 y RNF-SEG-003. |
| AD-007 | Proveedor de email intercambiable | fake en desarrollo, smtp/resend en producción; configuración por entorno (RNF-POR-002). |
| AD-008 | Timers configurables (autor 60 s, votación 30 s) | Definidos por entorno; expiración de autor descarta el turno; de votación cierra votación (RF-TUR-005/008). |
| AD-009 | Sala de 2 a 6 jugadores y modalidades en catálogo | Límites configurables; modalidades precargadas como plantillas de frase (RN-008, RN-026). |
| AD-010 | Política de contraseña: mín. 8 caracteres y complejidad | Al menos una mayúscula, minúscula, número y carácter especial (RNF-SEG-001). |

## 6.2 Alternativas consideradas

| Decisión | Alternativas evaluadas | Motivo del rechazo |
| --- | --- | --- |
| AD-001 | Microservicios por módulo | Sobrecostos de operación y latencia; sin necesidad de escalado independiente en v1. |
| AD-002 | JWT stateless | No permite invalidar sesiones de forma simple (RF-AUT-006) ni bloquear por intentos fallidos sin lógica adicional. |
| AD-003 | Persistir salas/partidas/turnos en BD | Contradice la naturaleza transitoria (RN-024) y agrega latencia a cada transición de turno. |
| AD-004 | Redis Pub/Sub, socket.io | Requieren infraestructura adicional; innecesarias para una sola instancia con bus en memoria. |
| AD-005 | Tortoise ORM / SQL puro / SQLModel | SQLAlchemy 2.0 es el estándar de FastAPI con migraciones maduras y soporte async completo. |
| AD-007 | Proveedor de email único (solo SMTP) | Dificulta pruebas locales y desarrollo; la abstracción permite fake en desarrollo. |
| AD-009 | Sin límite de jugadores / modalidades fijas en código | Se exige control del límite y configuración previa de modalidades (RN-026, RF-SAL-008). |

## 6.3 Justificación

El diseño cumple con los requisitos no funcionales de la siguiente manera:

| Requisito | Cómo lo satisface el diseño |
| --- | --- |
| RNF-EFI-001 | Estado en memoria + SQL async; consultas con índices únicos. |
| RNF-EFI-002/003 | WebSocket con envío push; cada partida aislada en MatchStore. |
| RNF-SEG-001 | Argon2id para contraseñas; tokens con hash en CodeStore. |
| RNF-SEG-002/003 | Sesiones opacas verificadas en cada endpoint; validación Pydantic de toda entrada. |
| RNF-FIA-001 | Jerarquía de excepciones con respuestas controladas y códigos de error. |
| RNF-FIA-002 | Toda mutación de estado se realiza solo mediante servicios del servidor. |
| RNF-FIA-003 | Transacciones SQLAlchemy + migraciones Alembic. |
| RNF-USA-001/002 | Respuestas siempre informativas; eventos RTR comunican el estado y el jugador activo. |
| RNF-MAN-001/002 | Arquitectura por capas y módulos con baja dependencia. |
| RNF-MAN-003 | Estructura de pruebas por módulo (unitarias) y de contrato (HTTP/WS). |
| RNF-POR-001/002 | Docker Compose y configuración por variables de entorno. |
| RNF-INT-001/002 | JSON en REST y WebSocket; HTTP y WebSocket como protocolos. |
| RNF-DAT-001/002 | Solo usuarios, modalidades y frases persistidas; salas/partidas efímeras eliminadas al finalizar. |
| RNF-EST-001 | OpenAPI generada automáticamente por FastAPI. |

# 7. Restricciones del diseño

Restricciones técnicas, de negocio y de estándares que condicionan el diseño.

## 7.1 Restricciones técnicas y de plataforma

- Backend implementado en Python 3.12 con FastAPI (SRS 2.4).
- Persistencia en PostgreSQL mediante SQLAlchemy 2.0 async y migraciones Alembic.
- Despliegue mediante contenedores Docker (Docker Compose).
- Comunicación con JSON; REST sobre HTTP y tiempo real sobre WebSocket (RNF-INT-001/002).
- API documentada con OpenAPI (RNF-EST-001); proyecto bajo Git (RNF-EST-002).
- Se asume una única instancia de la API (el estado en memoria requiere replicación adicional si se escala — decisión AD-003).
## 7.2 Restricciones de negocio y funcionales

- Partidas privadas entre grupos reducidos; todas las salas requieren código único (RN-006, RN-027).
- Cantidad de jugadores por sala: mínimo 2 y máximo 6 (RN-008).
- Partida compuesta por una única ronda con tantos turnos como jugadores al inicio (RN-022, RN-025).
- Puntaje secreto y votos: enteros entre 1 y 10 (RN-012, RN-015); un voto por jugador y por turno (RN-014).
- Sin chat, amigos, rankings, estadísticas ni autenticación externa en v1 (SRS 1.2).
- Sin usuario administrador funcional (SRS 2.3).
- Todas las salas privadas; solo el creador inicia o cancela (RN-007, RN-010).
- Política de contraseña: mín. 8 caracteres con mayúscula, minúscula, dígito y carácter especial (AD-010).
- Tiempos configurables: autor 60 s, votación 30 s (AD-008).
# 8. Decisiones de diseño

Este capítulo consolida las decisiones de diseño y sus registros formales (ADR). Las decisiones se clasifican según el aspecto del diseño que afectan.

| Aspecto | Decisiones | Referencia ADR |
| --- | --- | --- |
| Arquitectura | Monolito modular, estado en memoria, una instancia | AD-001, AD-003 |
| Tiempo real | WebSocket nativo + bus de eventos en proceso | AD-004 |
| Autenticación | Sesiones opacas con TTL; bloqueo por intentos fallidos | AD-002, AD-006 |
| Persistencia | SQLAlchemy async + Alembic; modelo mínimo de datos | AD-005 |
| Seguridad | Argon2id, tokens con hash, validación Pydantic | AD-006 |
| Correo | Proveedor intercambiable (fake/smtp/resend) | AD-007 |
| Configuración | Variables de entorno para tiempos, límites y credenciales | AD-008, AD-009, AD-010 |

Los ADR completos (contexto, decisión, consecuencias, estado) figuran en el Apéndice A.

# 9. Trazabilidad

La trazabilidad garantiza que cada requisito del SRS se corresponde con uno o más elementos del diseño y que cada elemento del diseño responde a requisitos, conforme a IEEE 1016 y RNF-EST-002.

## 9.1 Requisitos → elementos de diseño

Trazabilidad de requisitos funcionales (RF) hacia componentes del diseño:

| Requisito | Elemento(s) de diseño |
| --- | --- |
| RF-USR-001 a 007 | UserService, UserRepository, AvatarGenerator (Módulo Usuarios), tabla users |
| RF-AUT-001 a 009 | AuthService, SessionStore, CodeStore, EmailProvider (Módulo Autenticación) |
| RF-SAL-001 a 008 | RoomService, RoomStore, RealtimeService (Módulo Salas) |
| RF-PAR-001 a 007 | MatchService, MatchStore, TurnService (Módulo Partidas) |
| RF-TUR-001 a 011 | TurnService, TimerManager, ScoringService, EventBus (Módulo Turnos) |
| RF-PUN-001 a 004 | ScoringService, MatchStore (Módulo Puntuación) |
| RF-COM-001 a 010 | RealtimeService, EventBus, ConnectionManager, Gateway WS (Módulo Comunicación RTR) |
| RF-PER-001 a 005 | PersistenceService, Repositories, database (Módulo Persistencia) |

Trazabilidad de reglas de negocio (RN):

| Reglas | Elemento(s) de diseño |
| --- | --- |
| RN-001 a 005 | UserService, tabla users (unicidad), AuthService (acceso), Módulo Usuarios |
| RN-006 a 011 | RoomService, RoomStore (estados, permisos de creador, modalidad) |
| RN-012 a 017 | TurnService, modelo Turn (secreto, votos, abandonos, ronda única) |
| RN-018 a 020 | ScoringService (puntos solo al autor por acierto exacto) |
| RN-021 a 023 | MatchService, MatchStore (fin de ronda, turnos fijos, empate) |
| RN-024 a 027 | PersistenceService + RoomStore (eliminación), catálogo de modalidades, unicidad de código |

## 9.2 Requisitos → vistas

| Requisito | Vistas que lo abordan |
| --- | --- |
| RNF-MAN-001/002, RNF-IMP-001 | 4.1 Arquitectónica, 4.2 Composición |
| RNF-EFI-001, RNF-INT-001/002, RNF-SEG-002/003 | 4.5 Interacción, 4.3 Información |
| RNF-EFI-002/003, RNF-FIA-002, RN-012 a 023 | 4.4 Comportamiento |
| RNF-SEG-001, RNF-FIA-003, RNF-DAT-001/002, RF-PER-* | 4.3 Información |
| RNF-POR-001/002, RNF-EFI-001 | 4.6 Despliegue |
| RNF-USA-001/002, RNF-FIA-001 | 4.5 Interacción, 4.4 Comportamiento |
| RF-COM-*, RF-TUR-* | 4.5 Interacción, 4.4 Comportamiento |

## 9.3 Diseño → implementación

Mapeo entre los elementos del diseño y los artefactos reales del código (estructura verificada en la rama `develop`). Las rutas difieren de la estructura de paquetes prevista en 4.2.1; esta tabla es la fuente de verdad vigente.

| Elemento de diseño | Artefacto de implementación |
| --- | --- |
| API REST | `app/api/routers/*.py` (`auth.py`, `users.py`, `modalities.py`, `rooms.py`, `matches.py`, `turns.py`, `scoring.py`) |
| Gateway WebSocket | `app/api/ws.py` (endpoint `/api/v1/ws`) |
| Inyección de dependencias | `app/api/deps.py` (`get_event_bus`, `get_current_user`, sesiones, stores) |
| Esquemas y contratos | `app/api/schemas.py` |
| Mapa de errores HTTP | `app/api/errors.py` (formato B.5) |
| Servicios de aplicación | `app/services/*.py` (`auth_service`, `users_service`, `room_service`, `match_service`, `turn_service`, `scoring_service`, `emails`, `catalog`, `realtime_service`) |
| Modelos de dominio | `app/domain/entities.py` (`Room`, `Match`, `Turn`, `User`), `app/domain/avatars.py` |
| Contratos de repositorios | `app/stores/base.py` (interfaces `UserStore`, `RoomStore`, etc.) |
| Stores en memoria | `app/stores/memory.py` (implementación actual; sin base de datos) |
| Bus de eventos, ConnectionManager y servicio realtime | `app/services/realtime_service.py` (EventBus tolerante a handlers síncronos/async, ConnectionManager, RealtimeService) |
| Gestor de timers | `app/services/turn_service.py` (tiempos de autor/votación desde `app/core/config.py`) |
| Proveedor de email | `app/email/provider.py` |
| Configuración y seguridad | `app/core/config.py` (pydantic-settings), `app/core/security.py` (argon2, tokens, verificaciones) |
| Archivos estáticos de avatares | `app/main.py` (mount de `/uploads` sobre el volumen `./uploads`) |
| Migraciones | pendiente (no hay base de datos aún; ver RF-PER en SRS §7.1) |
| Cliente web (SPA Vite) | `frontend/src/*` (`main.js`, `router.js`, `store.js`, `events.js`, `realtime.js`, `api.js`, `screens/*`) |
| Pruebas | `tests/` (unitarias y de contrato HTTP/WS; incluye `tests/test_realtime.py`) |
| Despliegue | `Dockerfile` (api), `docker-compose.yml`, `frontend/Dockerfile` + `frontend/nginx.conf` (proxy WS y `/uploads`) |

# Apéndice A — Registros de Decisión Arquitectónica (ADR)

## AD-001 — Monolito modular

Contexto: el SRS exige separación por módulos y bajo acoplamiento (RNF-MAN-001/002). Decisión: un único backend FastAPI organizado en capas y módulos. Consecuencias: despliegue simple, un solo ciclo de vida; se renuncia al escalado independiente por módulo. Estado: Aceptada.

## AD-002 — Sesiones opacas en servidor

Contexto: RF-AUT-006 exige cierre de sesión que invalide el acceso y RF-AUT-005 bloqueo temporal. Decisión: token opaco aleatorio con hash almacenado en SessionStore con TTL; se invalida al hacer logout o al expirar. Consecuencias: sin tokens de larga duración; estado de sesión en memoria. Estado: Aceptada.

## AD-003 — Estado de juego en memoria

Contexto: salas, partidas y turnos son transitorios (RN-024, RNF-DAT-002). Decisión: alojarlos en stores en memoria dentro de la API. Consecuencias: baja latencia y consistencia fuerte por proceso; si se escala a varias instancias, se requerirá Redis u otro mecanismo compartido. Estado: Aceptada.

## AD-004 — WebSocket nativo + bus en proceso

Contexto: RNF-EFI-002 exige eventos en tiempo real sin polling. Decisión: gateway WebSocket de FastAPI + EventBus asyncio interno. Consecuencias: sin dependencia de infraestructura adicional; single-instance. Estado: Aceptada.

## AD-005 — SQLAlchemy 2.0 async + Alembic

Contexto: persistencia en PostgreSQL (RNF-FIA-003). Decisión: SQLAlchemy async con psycopg async y migraciones Alembic. Consecuencias: esquema versionable, consultas no bloqueantes. Estado: Aceptada.

## AD-006 — Argon2id + Pydantic

Contexto: RNF-SEG-001 y RNF-SEG-003. Decisión: hash de contraseñas con Argon2id y validación estricta de entrada mediante Pydantic. Consecuencias: mayor coste computacional por hash (adecuado), entradas validadas antes del dominio. Estado: Aceptada.

## AD-007 — Proveedor de email intercambiable

Contexto: RF-AUT-001/002/008 requieren envío de correos; en desarrollo no debe depender de servicios externos. Decisión: interfaz EmailProvider con implementaciones fake (dev), smtp y resend seleccionable por entorno. Consecuencias: portabilidad y testabilidad; sin acoplamiento a un proveedor concreto. Estado: Aceptada.

## AD-008 — Timers configurables

Contexto: RF-TUR-005/008 exigen control de tiempo sin valores fijos. Decisión: AUTHOR_TIMEOUT_SECONDS=60 y VOTING_TIMEOUT_SECONDS=30 por entorno; expiración de autor descarta el turno y la de votación cierra votación. Consecuencias: comportamiento determinista ante inactividad. Estado: Aceptada.

## AD-009 — Límites y modalidades configurables

Contexto: RN-008 (mínimo 2 jugadores) y RF-SAL-008 (límite máximo). Decisión: mínimo 2 y máximo 6 jugadores por sala, configurables; modalidades en catálogo precargado como plantillas de frase. Consecuencias: flexibilidad sin tocar código. Estado: Aceptada.

## AD-010 — Política de contraseñas

Contexto: RNF-SEG-001 sin política explícita. Decisión: mínimo 8 caracteres y al menos una mayúscula, minúscula, dígito y símbolo. Consecuencias: criterios verificables en registro y cambio de contraseña. Estado: Aceptada.

# Apéndice B — Contratos de interfaz front-back

Este apéndice define, por módulo, los contratos que los clientes (frontend web, apps móviles y de escritorio) consumen del backend. Todo intercambio usa JSON (RNF-INT-001); salvo el canal WebSocket de la sección B.2.7, cada operación de dominio se expone como endpoint REST y el feedback en tiempo real se entrega mediante eventos push.

## B.1 Convenciones generales

- **Base URL**: `/api/v1`. HTTPS en producción.
- **Representación**: `application/json; charset=utf-8`.
- **Autenticación REST**: cabecera `Authorization: Bearer <access_token>`.
- **Autenticación WebSocket**: `wss://host/api/v1/ws?token=<access_token>` (RF-COM-001).
- **Identificadores**:
  - `id` / `player_id` / `user_id`: `usr-` + 10 hex (ej. `usr-3f2a91c4d8`).
  - `room_code`: 6 caracteres `[0-9A-Z]`, sin dígitos/de letras ambiguos (ej. `AB12CD`).
  - `match_id`: `m-` + 10 hex (ej. `m-8b1e42f9c7`).
  - `turn_id`: `t-` + 10 hex (ej. `t-57a30c9d11`).
- **Instantes de tiempo**: epoch en milisegundos (ms, UTC).
- **Estados (máquinas de 4.4)** — valores de máquina (inglés) y su equivalente en el DDD:

  | Entidad | Valores | Correspondencia DDD |
  | --- | --- | --- |
  | `room.state` | `available` · `in_match` · `cancelled` · `deleted` | DISPONIBLE · EN JUEGO · CANCELADA · ELIMINADA |
  | `match.state` | `created` · `initialized` · `in_progress` · `finished` | CREADA · INICIALIZADA · EN CURSO · FINALIZADA |
  | `turn.state` | `active` · `voting` · `finished` · `discarded` | ACTIVO · EN VOTACIÓN · FINALIZADO · DESCARTADO |

- **Envoltura de eventos WS** (B.2.7): `{ "type": <string>, "timestamp": <ms>, "data": <objeto> }`.
- **Errores**: formato unificado B.5; códigos específicos por módulo en cada sección.

**Objetos reutilizados**

`User`:
```json
{
  "id": "usr-3f2a91c4d8",
  "username": "ken2000",
  "email": "ken2000@example.com",
  "verified": true,
  "profile_image_url": "/avatars/k.svg",
  "created_at": 1760000000000
}
```

`Modality`:
```json
{ "id": 1, "name": "Es un 10 pero...", "template": "Es un 10 pero ..." }
```

`Player`:
```json
{ "id": "usr-3f2a91c4d8", "username": "ken2000", "joined_at": 1760000000001 }
```

## B.2 Contratos por módulo

### B.2.1 Módulo de autenticación (RF-AUT-001 a 009)

| Método | Ruta | Auth | Request | Response 2xx | Errores específicos |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | No | `{username, email, password}` | `201` → `User` (sin sesión) | `USERNAME_TAKEN` · `EMAIL_TAKEN` · `VALIDATION_ERROR` |
| POST | `/api/v1/auth/verify-email` | No | `{token}` | `200` → `{}` | `TOKEN_INVALID` · `TOKEN_EXPIRED` · `ALREADY_VERIFIED` |
| POST | `/api/v1/auth/resend-verification` | No | `{email}` | `200` → `{}` | `ALREADY_VERIFIED` · `EMAIL_SEND_FAILED` |
| POST | `/api/v1/auth/login` | No | `{identifier, password}` | `200` → `{access_token, token_type: "bearer", expires_at, user}` | `INVALID_CREDENTIALS` · `ACCOUNT_BLOCKED` · `EMAIL_NOT_VERIFIED` |
| POST | `/api/v1/auth/logout` | Sí | `—` | `204` | `TOKEN_INVALID` |
| POST | `/api/v1/auth/change-password` | Sí | `{current_password, new_password}` | `200` → `{}` | `INVALID_CREDENTIALS` · `PASSWORD_POLICY` |
| POST | `/api/v1/auth/forgot-password` | No | `{email}` | `200` → `{}` | `PASSWORD_POLICY` (respuesta genérica, RF-AUT-008) |
| POST | `/api/v1/auth/reset-password` | No | `{token, new_password}` | `200` → `{}` | `TOKEN_INVALID` · `TOKEN_EXPIRED` · `PASSWORD_POLICY` |

Reglas de negocio no negociables:
- `username`: 3–20 caracteres, único insensible a mayúsculas (RN-001). `email`: único, normalizado (RN-002).
- `password`: mínimo 8 caracteres con mayúscula, minúscula, dígito y símbolo (AD-008).
- La cuenta debe estar verificada (`verified=true`) antes del primer `login` (RF-AUT-001). Un cambio de email en `PATCH /users/me` revierte `verified=false`.
- Tras 5 intentos fallidos consecutivos la cuenta se bloquea temporalmente (RF-AUT-005): `ACCOUNT_BLOCKED` con `details.retry_after`.
- El `access_token` es opaco, con hash almacenado en `SessionStore` y TTL (AD-002); `logout` o expiración lo invalidan.
- Eventos WS: ninguno.

### B.2.2 Módulo de usuarios (RF-USR-001 a 007)

| Método | Ruta | Auth | Request | Response 2xx | Errores específicos |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/users/me` | Sí | `—` | `200` → `User` | `TOKEN_INVALID` |
| PATCH | `/api/v1/users/me` | Sí | `{username?, email?}` (opcionales) | `200` → `User` | `USERNAME_TAKEN` · `EMAIL_TAKEN` · `VALIDATION_ERROR` |
| GET | `/api/v1/modalities` | Sí | `—` | `200` → `{items: [Modality], total}` | `—` |

- `profile_image_url` es generada por el servidor a partir de la inicial del username (RF-USR-005); no acepta subida de imagen (RN-005).
- La lista de modalidades es el catálogo precargado de plantillas de frase (AD-007); es la única fuente de `modality_id` para crear salas.

### B.2.3 Módulo de salas (RF-SAL-001 a 008)

| Método | Ruta | Auth | Request | Response 2xx | Errores específicos |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/rooms` | Sí | `{modality_id}` | `201` → `Room` | `MODALITY_NOT_FOUND` · `PLAYER_ALREADY_IN_SESSION` |
| GET | `/api/v1/rooms/{code}` | Sí | `—` | `200` → `Room` | `ROOM_NOT_FOUND` |
| POST | `/api/v1/rooms/{code}/join` | Sí | `—` | `200` → `Room` | `ROOM_NOT_FOUND` · `ROOM_FULL` · `ROOM_NOT_AVAILABLE` · `PLAYER_ALREADY_IN_SESSION` |
| POST | `/api/v1/rooms/{code}/leave` | Sí | `—` | `200` → `Room` | `ROOM_NOT_FOUND` · `NOT_IN_ROOM` |
| POST | `/api/v1/rooms/{code}/start` | Sí | `—` | `200` → `{match_id}` | `NOT_CREATOR` · `MIN_PLAYERS_NOT_REACHED` · `ROOM_NOT_AVAILABLE` |
| DELETE | `/api/v1/rooms/{code}` | Sí | `—` | `204` | `NOT_CREATOR` · `ROOM_IN_MATCH` |

`Room`:
```json
{
  "code": "AB12CD",
  "state": "available",
  "creator_id": "usr-3f2a91c4d8",
  "modality": {"id": 1, "name": "Es un 10 pero...", "template": "Es un 10 pero ..."},
  "players": [{"id": "usr-3f2a91c4d8", "username": "ken2000", "joined_at": 1760000000001}],
  "min_players": 2,
  "max_players": 6,
  "created_at": 1760000000000
}
```

- Condiciones de ingreso (RF-SAL-008, RN-006 a 009): la sala es privada, se localiza solo por `code`; sólo admite usuarios que no estén en otra sala y mientras `state=available` y haya cupo.
- Transiciones (4.4.1): `available` → `in_match` al iniciar (deja de admitir jugadores, RN-009); `available` → `cancelled` por `DELETE` del creador; cualquier estado → `deleted` al finalizar la partida (RN-024).
- Eventos WS: `room.updated` (RF-COM-004) · `room.cancelled` (RF-SAL-006).

### B.2.4 Módulo de partidas (RF-PAR-001 a 007)

| Método | Ruta | Auth | Request | Response 2xx | Errores específicos |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/matches/{match_id}` | Sí | `—` | `200` → `Match` | `MATCH_NOT_FOUND` |

`Match`:
```json
{
  "match_id": "m-8b1e42f9c7",
  "room_code": "AB12CD",
  "state": "in_progress",
  "players": [{"id": "usr-3f2a91c4d8", "username": "ken2000", "joined_at": 1760000000001}],
  "turn_order": ["usr-3f2a91c4d8", "usr-a91c4d8f3", "usr-f3a91c4d82"],
  "current_turn": "t-57a30c9d11",
  "scores": {"usr-3f2a91c4d8": 1},
  "created_at": 1760000000000
}
```

- `turn_order` se genera aleatoriamente al inicializar (RF-PAR-003) y no se recalcula si un jugador abandona (RN-017/RN-022).
- `scores` se actualiza tras cada `turn.result` (RF-PUN-002).
- Transiciones (4.4.2): `created` → `initialized` (RF-PAR-002) → `in_progress` (primer turno) → `finished` (RF-PAR-006; también si quedan menos de 2 activos, RN-017).
- Eventos WS: `match.started` (RF-COM-005) · `match.finished` (RF-COM-009).

### B.2.5 Módulo de turnos (RF-TUR-001 a 011)

| Método | Ruta | Auth | Request | Response 2xx | Errores específicos |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/matches/{match_id}/phrase` | Sí | `{phrase, secret_score}` | `200` → `{turn_id}` | `NOT_AUTHOR` · `NOT_ACTIVE` · `PHRASE_INVALID` · `SCORE_INVALID` · `ALREADY_SUBMITTED` · `TURN_FINISHED` · `TURN_EXPIRED` |
| POST | `/api/v1/matches/{match_id}/votes` | Sí | `{score}` | `200` → `{turn_id}` | `NOT_VOTING` · `ALREADY_VOTED` · `SCORE_INVALID` · `NOT_IN_MATCH` · `TURN_FINISHED` |
| GET | `/api/v1/matches/{match_id}/turns/{turn_id}` | Sí | `—` | `200` → `Turn` | `MATCH_NOT_FOUND` · `TURN_NOT_FOUND` · `NOT_IN_MATCH` |

`Turn`:
```json
{
  "turn_id": "t-57a30c9d11",
  "match_id": "m-8b1e42f9c7",
  "author_id": "usr-3f2a91c4d8",
  "state": "active",
  "phrase": null,
  "secret_score": null,
  "expires_at": 1760000030000,
  "votes": [],
  "votes_count": 0
}
```

- Restricciones de entrada: `phrase` de 3 a 200 caracteres (RF-TUR-004); `secret_score` y `score` enteros entre 1 y 10 (RN-012, RN-015).
- Tiempos configurables (AD-006): autor `AUTHOR_TIMEOUT_SECONDS=60`, votación `VOTING_TIMEOUT_SECONDS=30`. Los vencimientos vienen en `expires_at` (epoch ms) dentro de `turn.started` y `turn.voting.started`.
- Transiciones (4.4.3): `active` → `voting` (frase+secreto registrados) o `discarded` (expira autor / abandona autor, RN-017); `voting` → `finished` (todos votan o expira votación) o `discarded`.
- Eventos WS: `turn.started` · `turn.phrase.submitted` · `turn.voting.started` · `vote.received` · `turn.voting.stopped` · `turn.result` (RF-COM-006, RF-TUR-010).

### B.2.6 Módulo de puntuación (RF-PUN-001 a 004)

| Método | Ruta | Auth | Request | Response 2xx | Errores específicos |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/matches/{match_id}/scoreboard` | Sí | `—` | `200` → `{round, scores}` | `MATCH_NOT_FOUND` |
| GET | `/api/v1/matches/{match_id}/result` | Sí | `—` | `200` → `{winner_id: string \| null, tied: bool, scores}` | `MATCH_NOT_FOUND` · `MATCH_NOT_FINISHED` |

- Sistema de puntos (RF-PUN-001, RN-018/RN-019): el autor obtiene 1 punto por cada voto que acierte exactamente el `secret_score`. Solo el autor suma puntos.
- Empate: si dos o más jugadores terminan con el mayor puntaje, `winner_id=null` y `tied=true` (RN-023). El resultado final sólo es consultable con `match.state=finished` (RF-PAR-007).
- Eventos WS: `scoreboard.updated` (RF-COM-008).

### B.2.7 Módulo de comunicación en tiempo real (RF-COM-001 a 010)

- **Handshake**: `wss://host/api/v1/ws?token=<access_token>`. La sesión se asocia al `user_id` del token; una misma cuenta sólo mantiene una conexión activa (RF-COM-002).
- **Protocolo**: mensajes del servidor al cliente con envoltura única `{event, data}` (la versión inicial `{type, timestamp, data}` se actualizó a la forma implementada; ver RV-009 en SRS §7.5). Los mensajes cliente → servidor van por REST; el canal WS es de *push* unidireccional del servidor (decisión AD-004).
- **Heartbeat**: el servidor responde `server.pong` a `client.ping` enviado por el cliente cada 30 s; ante dos pings sin respuesta se aplica el flujo de desconexión de RF-COM-010. (Pendiente: el cliente web implementa reconexión con backoff en lugar del ping de 30 s.)
- **Catálogo completo de eventos**:

  | Evento | data | Emitido cuando |
  | --- | --- | --- |
  | `room.updated` | `{code, state, modality, players[]}` | Cambia el roster o el estado de una sala (RF-COM-004) |
  | `room.cancelled` | `{code}` | El creador cancela la sala antes de iniciar (RF-SAL-006) |
  | `match.started` | `{match_id, room_code, order[], first_author}` | Inicia la partida; reparte `turn_order` (RF-COM-005, RF-PAR-003) |
  | `turn.started` | `{turn_id, author_id, expires_at}` | Comienza un turno; solo el autor puede operar (RF-TUR-002) |
  | `turn.phrase.submitted` | `{turn_id, phrase}` | El autor registra frase y secreto y se abre la votación (RF-COM-006) |
  | `turn.voting.started` | `{turn_id, expires_at}` | Etapa de votación; los votantes emiten `score` (RF-TUR-006) |
  | `vote.received` | `{turn_id, votes_count}` | Cada voto válido registrado; oculta su valor (RN-016) |
  | `turn.voting.stopped` | `{turn_id}` | Todos votaron o expiró el tiempo de votación (RF-TUR-009) |
  | `turn.result` | `{turn_id, author_id, secret_score, votes[{voter, value}], points}` | Publica el secreto y el detalle de votos del turno (RF-TUR-010) |
  | `scoreboard.updated` | `{scores}` | Puntos recalculados tras un turno (RF-COM-008, RF-PUN-002) |
  | `match.finished` | `{winner_id: string \| null, tied, scores}` | La ronda completa o quedan menos de 2 activos (RF-COM-009, RN-023) |
  | `player.disconnected` | `{player_id, reason: "timeout" \| "leave"}` | Desconexión definitiva de un jugador (RF-COM-010) |
  | `error` | `{code, message, details}` | Cualquier condición de error de negocio en el canal (B.5) |

> **Estado de implementación (RV-010, SRS §7.5):** por el momento el canal WS emite únicamente `room.updated`, `room.cancelled` y `match.started`. Los eventos de turno, marcador y finalización (`turn.*`, `scoreboard.updated`, `match.finished`, `player.disconnected`) son el diseño objetivo; hoy el frontend los obtiene por polling REST sobre los endpoints de B.3.

### B.2.8 Módulo de persistencia (RF-PER-001 a 005)

No expone contratos front-back: su superficie es interna (almacén PostgreSQL, DDD cap. 3). Los módulos anteriores persisten a través de él (usuarios, modalidades y frase completa de cada turno, RF-PER-005); el resto del estado de juego es efímero en memoria (AD-003, RN-024).

## B.3 Catálogo consolidado de endpoints REST

| Método | Ruta | Autenticación | Descripción | Entrada → Salida |
| --- | --- | --- | --- | --- |
| POST | /api/v1/auth/register | No | Registrar usuario | username, email, password → 201 user |
| POST | /api/v1/auth/verify-email | No | Verificar correo | token → 200 |
| POST | /api/v1/auth/resend-verification | No | Reenviar verificación | email → 200 |
| POST | /api/v1/auth/login | No | Iniciar sesión | identifier, password → 200 {token, user} |
| POST | /api/v1/auth/logout | Sí | Cerrar sesión | — → 204 |
| POST | /api/v1/auth/change-password | Sí | Cambiar contraseña | current_password, new_password → 200 |
| POST | /api/v1/auth/forgot-password | No | Solicitar recuperación | email → 200 |
| POST | /api/v1/auth/reset-password | No | Restablecer contraseña | token, new_password → 200 |
| GET | /api/v1/users/me | Sí | Consultar perfil propio | — → 200 user |
| PATCH | /api/v1/users/me | Sí | Modificar perfil | username/email opcionales → 200 user |
| PUT | /api/v1/users/me/avatar | Sí | Cargar foto de perfil (RV-001) | multipart `file` (JPG/PNG/WEBP/GIF, ≤ 2 MB) → 200 user · 415 tipo inválido |
| GET | /api/v1/modalities | Sí | Listar modalidades | — → 200 list |
| POST | /api/v1/rooms | Sí | Crear sala | modality_id → 201 room |
| GET | /api/v1/rooms/{code} | Sí | Consultar sala | — → 200 room |
| POST | /api/v1/rooms/{code}/join | Sí | Unirse a sala | — → 200 room |
| POST | /api/v1/rooms/{code}/leave | Sí | Abandonar sala | — → 200 |
| POST | /api/v1/rooms/{code}/start | Sí | Iniciar partida (creador) | — → 200 {match_id} |
| DELETE | /api/v1/rooms/{code} | Sí | Cancelar sala (creador) | — → 204 |
| GET | /api/v1/matches/{match_id} | Sí | Estado de partida | — → 200 match |
| GET | /api/v1/matches/by-room/{code} | Sí | Partida asociada a una sala (respaldo de entrada, RV-002) | — → 200 match |
| GET | /api/v1/matches/{match_id}/turns/{turn_id} | Sí | Detalle de turno | — → 200 turn |
| POST | /api/v1/matches/{match_id}/phrase | Sí | Registrar frase y secreto (autor) | phrase, secret_score → 200 |
| POST | /api/v1/matches/{match_id}/votes | Sí | Emitir voto (votante) | score → 200 |
| GET | /api/v1/matches/{match_id}/scoreboard | Sí | Consultar marcador | — → 200 scores |
| GET | /api/v1/matches/{match_id}/result | Sí | Resultado final | — → 200 {winner\|tie, scores} |

## B.4 Catálogo consolidado de eventos WebSocket (push)

| Evento | Dirección | Contenido (data) |
| --- | --- | --- |
| room.updated | server → client | code, players[], state, modality |
| room.cancelled | server → client | code |
| match.started | server → client | match_id, order[], first_author |
| turn.started | server → client | turn_id, author_id, expires_at |
| turn.phrase.submitted | server → client | phrase |
| turn.voting.started | server → client | turn_id, expires_at |
| vote.received | server → client | turn_id, votes_count |
| turn.voting.stopped | server → client | turn_id |
| turn.result | server → client | secret_score, votes[], points |
| scoreboard.updated | server → client | scores{} |
| match.finished | server → client | winner_id \| tie, final scores |
| player.disconnected | server → client | player_id, reason |
| error | server → client | code, message |

## B.5 Formato de error estándar

```json
{
  "error": {
    "code": "USERNAME_TAKEN",
    "message": "El nombre de usuario ya se encuentra registrado.",
    "details": {}
  }
}
```

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `code` | string | Código máquina estable, agrupable por frontend para i18n (ej. `ROOM_FULL`). |
| `message` | string | Descripción legible en el idioma de la respuesta. |
| `details` | object | Contexto adicional: `{field: "error"}` en validaciones, `retry_after` en bloqueos, etc. |

Códigos transversales:

| Código | HTTP | Uso |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | Formato/campos inválidos; `details` lista cada campo con su error. |
| `TOKEN_INVALID` | 401 | Token ausente, malformado o revocado. |
| `TOKEN_EXPIRED` | 401 | Sesión vencida. |
| `FORBIDDEN` | 403 | El actor no tiene el rol exigido (ej. no es el creador). |
| `RATE_LIMITED` | 429 | Supera el límite de solicitudes por ventana. |
| `INTERNAL_ERROR` | 500 | Fallo no controlado; no se detalla internamente. |

## B.6 Ejemplo de contrato de sala y de turno

Sala (respuesta de creación):

```json
{
  "code": "AB12CD",
  "creator": "usuario-1",
  "modality": {"id": 1, "template": "Es un 10 pero..."},
  "state": "available",
  "players": [{"id": "usuario-1", "username": "ken2000"}],
  "max_players": 6
}
```

Evento de resultado de turno:

```json
{
  "type": "turn.result",
  "timestamp": 1760000040000,
  "data": {
    "turn_id": "t-42",
    "author_id": "usuario-3",
    "secret_score": 8,
    "votes": [{"voter": "usuario-1", "value": 8}, {"voter": "usuario-2", "value": 5}],
    "points": 1
  }
}
```

Secuencia de un turno completo (REST en cursiva, WS en negrita):

1. _`POST /rooms/{code}/start`_ → `{match_id}` (RF-SAL-005).
2. **`match.started`** reparte `order[]` y `first_author` (RF-COM-005).
3. **`turn.started`** `{turn_id, author_id, expires_at}` (RF-COM-006).
4. _`POST /matches/{match_id}/phrase`_ `{phrase, secret_score}` (solo autor) → `{turn_id}`.
5. **`turn.phrase.submitted`** muestra la frase → **`turn.voting.started`** `{expires_at}` (RF-TUR-006).
6. _`POST /matches/{match_id}/votes`_ `{score}` (cada votante); **`vote.received`** informa el conteo sin revelar valores (RN-016).
7. **`turn.voting.stopped`** → **`turn.result`** revela secreto, votos y puntos (RF-TUR-010).
8. **`scoreboard.updated`** actualiza el marcador (RF-COM-008).
9. Al completarse la ronda, **`match.finished`** con `winner_id`/`tied` y puntajes finales (RF-COM-009).
