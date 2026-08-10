# Definición General del Sistema

**Sistema "Es un 10 pero…" — Videojuego multijugador por turnos**

Documentos base: SRS v1.0 (Especificación de Requisitos de Software) y DDD v1.0 (Documento de Diseño de Software, IEEE 1016-2009).

Códigos de referencia: SRS-ES10P · DDD-ES10P-001

Versión: 1.0 · Estado: Preliminar

---

# 1. El problema

## 1.1 Descripción del problema general

Existe la necesidad de ofrecer una experiencia de entretenimiento social tipo juego de salón, en la que un grupo reducido de jugadores pueda reunirse de forma privada y participar en partidas por turnos de adivinación y puntuación.

El juego se basa en completar una frase según una modalidad seleccionada y asignarle un puntaje secreto (entero entre 1 y 10). El resto de los jugadores intenta adivinar exactamente ese puntaje; el autor gana puntos por cada acierto exacto. Al completarse la ronda, el sistema determina el ganador o declara un empate.

## 1.2 Problemas concretos a resolver

1. Registro e identidad de jugadores: permitir crear cuentas, verificar el correo, autenticarse y gestionar el perfil de forma segura.
2. Reunión privada de jugadores: crear salas privadas identificadas por un código único, permitir el ingreso/abandono y restringir quién puede iniciar la partida.
3. Vida de la partida en tiempo real: iniciar una partida, ordenar a los jugadores, recorrer los turnos de una ronda y sincronizar el estado del juego entre todos los participantes.
4. Secretismo y puntuación: mantener oculto el puntaje secreto y los votos hasta el momento de publicación, y calcular los puntos de forma correcta y consistente.
5. Concurrencia y tiempos: gestionar múltiples partidas simultáneas sin interferencias y controlar tiempos de respuesta por turno (autor y votación).
6. Datos transitorios vs. permanentes: distinguir claramente la información duradera (usuarios, modalidades, frases) de la efímera (salas, partidas, turnos, sesiones) que debe eliminarse al finalizar.
## 1.3 Restricciones y alcance de la solución (v1)

- Partidas privadas entre grupos reducidos (mínimo 2 y máximo 6 jugadores).
- Una única ronda por partida, con tantos turnos como jugadores haya al inicio.
- Mínimo de 2 jugadores para iniciar una partida.
- En esta versión no se incluyen: chat, amigos, rankings, estadísticas históricas, autenticación externa, usuarios administradores ni carga de imágenes de perfil personalizadas.
# 2. Solución planteada (visión general)

Se desarrollará un backend desacoplado que expone una API REST para las operaciones de dominio y un canal WebSocket para la sincronización en tiempo real. La interfaz gráfica es un cliente independiente (web, móvil o escritorio) que consume estos contratos.

El sistema se organiza en ocho módulos funcionales, cada uno con responsabilidad única:

| Módulo | Responsabilidad |
| --- | --- |
| Usuarios | Registro, perfiles, unicidad de nombre/correo, avatar automático. |
| Autenticación | Inicio/cierre de sesión, verificación de correo, recuperación de contraseña, bloqueo por intentos fallidos. |
| Salas | Creación de salas privadas, códigos únicos, ingreso/abandono, modalidad, condiciones para iniciar. |
| Partidas | Ciclo de vida completo de la partida (creada → inicializada → en curso → finalizada/cancelada). |
| Turnos | Rondas, frases, puntaje secreto, votos, control de tiempos, cambio de turno. |
| Puntuación | Cálculo de puntos del autor y marcador acumulado. |
| Comunicación en tiempo real | Emisión y distribución de eventos a los clientes conectados. |
| Persistencia | Almacenamiento y recuperación de datos permanentes. |

Principios rectores: arquitectura cliente-servidor con contratos JSON, lógica de juego exclusivamente en el servidor, modularidad y bajo acoplamiento, y minimización de datos almacenados.

# 3. Reglas de negocio esenciales

- Usuarios: nombre y correo únicos (RN-001, RN-002); toda funcionalidad exige autenticación (RN-003); un usuario no puede estar en más de una sala a la vez (RN-004).
- Salas: todas privadas y por código (RN-006); solo el creador inicia (RN-007) o cancela (RN-010); se necesita mínimo 2 jugadores para iniciar (RN-008); no se admite ingreso tras iniciar (RN-009); la modalidad es fija (RN-011).
- Partida: puntaje secreto y votos enteros 1–10 (RN-012, RN-015); un voto por jugador por turno (RN-014); secreto y votos ocultos hasta publicar (RN-013, RN-016).
- Puntuación: puntos solo al autor (RN-018), un punto por acierto exacto (RN-019), y al cierre del turno se muestra secreto, votos y marcador (RN-020).
- Abandono: el jugador desconectado pierde los turnos restantes; si quedan menos de 2 jugadores activos, la partida finaliza (RN-017, RN-021, RN-022).
- Finalización: ronda única; empate si hay más de un máximo (RN-023); la sala se elimina al finalizar (RN-024).
# 4. Arquitectura del sistema

                  contratos JSON (REST)

```
+------------------+  ---------------------->  +-------------------------+
|     CLIENTE      |                            |       API BACKEND      |
| (web/movil/      |  <----------------------  |  - Capa de interfaces  |
|  escritorio)     |    respuestas/eventos     |  - Capa de aplicacion  |
+------------------+                            |  - Capa de dominio     |
|                                      |  - Capa de infraestruct.|  |
|   WebSocket (eventos en tiempo real) |  +--------+  +-------+ |
+------------------------------------> |  | Stores |  | Email | |
|  | memoria|  | prov. | |
|  +---+----+  +---+---+ |
|      |            |    |
|      | SQL async  |    |
|      v            |    |
|  PostgreSQL 16    |    |
+----+----------+---+----+
| persistencia
```

                                                    v

                                    (usuarios, modalidades, frases)

- Estado efímero en memoria: salas, partidas, turnos, sesiones y códigos viven en stores en memoria dentro de la API (decisión AD-003).
- Persistencia mínima: solo usuarios, modalidades y frases se guardan en PostgreSQL (RN-024, RNF-DAT-001/002).
- Dependencias: las dependencias fluyen interfaces → aplicación → dominio → infraestructura; el módulo de tiempo real es atravesado para publicar eventos sin que el resto conozca a los clientes.
# 5. Definición tecnológica (el “cómo”)

Esta sección define cada tecnología, su librería o extensión específica, el motivo de su elección y dónde se aplica. En los casos que provienen de decisiones documentadas se indica el ADR correspondiente del DDD.

## 5.1 Mapa general del stack

| Capa / aspecto | Tecnología | Librería / extensión |
| --- | --- | --- |
| Lenguaje | Python 3.12 | — |
| Framework web (REST) | FastAPI | — |
| Tiempo real | WebSocket nativo | starlette / websockets (integrado) |
| Validación / serialización | Pydantic v2 | pydantic, pydantic-settings |
| ORM | SQLAlchemy 2.0 (async) | sqlalchemy[asyncio] |
| Conector async a PostgreSQL | — | asyncpg |
| Migraciones | Alembic | alembic |
| Base de datos | PostgreSQL 16 | — |
| Hash de contraseñas | Argon2id | argon2-cffi |
| Envío de email | Interfaz intercambiable | resend / aiosmtplib / proveedor fake |
| Configuración | Variables de entorno | pydantic-settings + .env |
| Documentación API | OpenAPI / Swagger | autogenerada por FastAPI |
| Pruebas | Unitarias y de contrato | pytest, pytest-asyncio, httpx |
| Contenedores | Docker | Docker Compose |
| Control de versiones | Git | — |

## 5.2 Lenguaje de programación — Python 3.12

Qué es: lenguaje interpretado, de alto nivel y propósito general.

Por qué se elige: es el lenguaje definido por el SRS (sección 2.4) y el ecosistema natural de FastAPI. Su tipado progresivo y su soporte asíncrono (asyncio) se adecuan a un backend de lógica de negocio con eventos en tiempo real.

Dónde se aplica: en la totalidad del backend (app/).

## 5.3 Framework web — FastAPI

Qué es: framework web moderno basado en Starlette y Pydantic para construir APIs REST con soporte asíncrono.

Por qué: elegido por el SRS/DDD (AD-001, AD-004). Aporta enrutado declarativo, validación automática de peticiones, generación automática de documentación OpenAPI/Swagger (cubre RNF-EST-001), compatibilidad total con asyncio, y soporte nativo de WebSocket (cubre RNF-INT-002 y RNF-EFI-002).

Dónde se aplica: capa de interfaces — routers REST en app/api/v1/routes/ y gateway WebSocket en app/api/v1/ws.py.

## 5.4 Validación y configuración — Pydantic v2 y pydantic-settings

Qué es: Pydantic es la librería de validación y serialización de datos con modelos tipados; pydantic-settings es su extensión para leer configuración desde variables de entorno.

Por qué: el requisito de seguridad RNF-SEG-003 exige validar toda entrada recibida; Pydantic es el mecanismo de validación integrado de FastAPI (AD-006) y evita que datos inválidos lleguen a la lógica de dominio. pydantic-settings centraliza la configuración del entorno (AD-008 a AD-010), cumpliendo RNF-POR-002.

Dónde se aplica: esquemas de petición/respuesta en app/api/v1/schemas/ y configuración en app/core/config.py.

## 5.5 ORM — SQLAlchemy 2.0 asíncrono

Qué es: una de las librerías ORM (Object-Relational Mapping) más maduras de Python; la versión 2.0 añade soporte asíncrono de primera clase.

Por qué: decisión AD-005. Se elige sobre alternativas (Tortoise ORM, SQLModel o SQL puro) porque es el estándar de facto en proyectos FastAPI, tiene soporte async completo con consultas no bloqueantes, tipado de modelos al estilo Mapped[] y se integra de forma nativa con Alembic para migraciones versionadas (RNF-FIA-003).

Dónde se aplica: repositorios de infraestructura en app/infrastructure/repositories/, motor en app/core/database.py.

## 5.6 Conector de base de datos — asyncpg

Qué es: driver nativo y asíncrono de PostgreSQL para Python.

Por qué: un ORM asíncrono requiere un driver asíncrono; asyncpg es el más rápido y el recomendado junto con SQLAlchemy async. La cadena de conexión lo referencia directamente (postgresql+asyncpg://… en DATABASE_URL según el DDD).

Dónde se aplica: transporte entre la API y PostgreSQL.

## 5.7 Migraciones — Alembic

Qué es: herramienta de migraciones de esquema de base de datos, integrada con SQLAlchemy.

Por qué: AD-005; permite versionar los cambios de esquema en archivos controlados (alembic/versions/), reproducir el esquema en cualquier entorno y garantizar integridad (RNF-FIA-003, RNF-EST-002).

Dónde se aplica: gestión del esquema persistente (usuarios, modalidades, frases).

## 5.8 Base de datos — PostgreSQL 16

Qué es: sistema gestor de bases de datos relacional.

Por qué: fijado por el SRS (sección 2.4). Modela bien la información persistente (unicidad de username y email, claves foráneas entre frases, modalidades y usuarios), ofrece índices únicos para RN-001/RN-002 y transacciones ACID para RNF-FIA-003.

Dónde se aplica: contenedor db con imagen postgres:16, volumen pgdata y healthcheck.

## 5.9 Seguridad y hashing de contraseñas — Argon2id

Qué es: algoritmo de derivación de claves (hash) ganador del concurso de hashing de contraseñas, resistente a ataques. La variante 2id combina resistencia a ataques por GPU y por circuito dedicado. Se usa mediante la librería argon2-cffi.

Por qué: decisión AD-006 para cumplir RNF-SEG-001 (nunca almacenar contraseñas en texto plano); se utiliza hash criptográfico con salt propio. Se elige sobre SHA o bcrypt por ser el estándar moderno recomendado.

Tema relacionado: los tokens de verificación de correo y recuperación de contraseña también se guardan con hash en CodeStore (nunca en claro).

## 5.10 Autenticación y sesiones — tokens opacos

Qué es: en lugar de JWT stateless, se usan tokens opacos (cadenas aleatorias) cuya versión con hash se almacena en un SessionStore en memoria con tiempo de expiración (TTL).

Por qué: decisión AD-002. Permite invalidar sesiones de forma inmediata (logout, RF-AUT-006) y bloquear cuentas por intentos fallidos (RF-AUT-005), lo que no es viable con JWT sin lógica adicional.

Parámetros: SESSION_TTL_HOURS=8, MAX_FAILED_ATTEMPTS=5, LOCK_DURATION_MINUTES=15 (configurables).

## 5.11 Comunicación en tiempo real — WebSocket nativo + bus de eventos asyncio

Qué es: el gateway WebSocket de FastAPI maneja las conexiones persistentes, y un EventBus interno (basado en asyncio) desacopla la publicación de eventos de su envío por WebSocket.

Por qué: decisión AD-004. Los eventos del juego se transmiten en tiempo real sin polling (RNF-EFI-002), sin añadir infraestructura externa (Redis Pub/Sub o socket.io se descartan por innecesarios en una única instancia). El ConnectionManager asocia cada conexión autenticada a su usuario.

Dónde se aplica: app/infrastructure/realtime/ (event_bus, connection_manager) y app/api/v1/ws.py. Catálogo de eventos en el apéndice B.2 del DDD (match.started, turn.started, turn.result, match.finished, etc.).

## 5.12 Control de tiempos — gestor de timers

Qué es: componente TimerManager que programa la expiración de turnos mediante tareas asíncronas.

Por qué: RF-TUR-005 y RF-TUR-008 exigen control de tiempo del autor y de votación con valores configurables (AD-008): autor 60 s y votación 30 s. La expiración del autor descarta el turno; la de votación cierra la votación y calcula los puntos.

Dónde se aplica: app/infrastructure/timing/timer_manager.py.

## 5.13 Envío de correo — proveedor intercambiable

Qué es: interfaz EmailProvider con implementaciones intercambiables.

Por qué: decisión AD-007. Se usan tres proveedores según entorno: fake (desarrollo, sin dependencias externas), SMTP (aiosmtplib, infraestructura de correo tradicional) y Resend (SaaS en la nube, librería oficial resend). Cubre RF-AUT-001/002/008 (verificación y recuperación) y RNF-POR-002.

Configuración: variable EMAIL_PROVIDER (fake en desarrollo) y credenciales solo por entorno.

## 5.14 Configuración — variables de entorno

Qué es: todos los parámetros sensibles y de operación se leen desde variables de entorno (.env), nunca desde código fuente.

Por qué: RNF-POR-002. Ejemplos: DATABASE_URL, SESSION_TTL_HOURS, AUTHOR_TIMEOUT_SECONDS, VOTING_TIMEOUT_SECONDS, SECRET_KEY, EMAIL_PROVIDER.

## 5.15 Despliegue — Docker y Docker Compose

Qué es: los servicios se empaquetan en contenedores; Compose orquesta api (imagen es10p-api, puerto 8000) y db (PostgreSQL 16) en una red interna.

Por qué: RNF-POR-001 exige arranque en un entorno nuevo con docker-compose up.

Dónde se aplica: Dockerfile, docker-compose.yml y .env.

## 5.16 Documentación de la API — OpenAPI / Swagger

Qué es: FastAPI genera automáticamente una especificación OpenAPI 3 junto con una interfaz Swagger interactiva.

Por qué: RNF-EST-001 exige que todos los endpoints públicos estén documentados mediante OpenAPI, sin escribir la documentación a mano.

## 5.17 Pruebas — pytest

Qué es: framework de pruebas de Python.

Por qué: RNF-MAN-003 exige pruebas automatizadas de los componentes críticos. Se planifican pruebas unitarias por módulo y de contrato sobre HTTP/WebSocket, usando pytest con la extensión pytest-asyncio (para código async), httpx (para probar la aplicación ASGI de FastAPI) y el proveedor fake de email.

Dónde se aplica: directorio tests/.

## 5.18 Control de versiones — Git

Qué es: sistema de control de versiones distribuido.

Por qué: RNF-EST-002; todo el proyecto y la trazabilidad se gestionan en un repositorio Git.

# 6. Decisiones de diseño que condicionan la tecnología

| ID | Decisión | Impacto tecnológico |
| --- | --- | --- |
| AD-001 | Monolito modular (una sola API FastAPI) | Un único contenedor; capas y módulos en app/. |
| AD-002 | Sesiones opacas con TTL en servidor | SessionStore en memoria; sin dependencia de tokens JWT. |
| AD-003 | Estado de juego en memoria | RoomStore, MatchStore y CodeStore viven en el proceso de la API. |
| AD-004 | WebSocket nativo + EventBus asyncio | Sin Redis ni socket.io; single-instance. |
| AD-005 | SQLAlchemy 2.0 async + Alembic | Conector asyncpg; migraciones versionadas. |
| AD-006 | Argon2id + validación Pydantic | argon2-cffi; esquemas estrictos de entrada. |
| AD-007 | Proveedor de email intercambiable | fake / SMTP / Resend según entorno. |
| AD-008 | Timers configurables (autor 60 s, votación 30 s) | Variables de entorno + TimerManager. |
| AD-009 | Sala de 2 a 6 jugadores; modalidades en catálogo | Límites configurables; seed de modalidades. |
| AD-010 | Política de contraseñas (mín. 8 caracteres y complejidad) | Validación en registro y cambio de contraseña. |

# 7. Trazabilidad resumida

- Definición del problema y reglas de negocio → SRS v1.0 (secciones 2 y 3).
- Arquitectura y decisiones tecnológicas → DDD v1.0 (secciones 4 a 8 y apéndice A).
- Requisitos funcionales (RF-USR a RF-PER) y no funcionales (RNF) → trazados a elementos de diseño en las tablas 16 a 19 del DDD.
- Contratos REST y eventos WebSocket → apéndice B del DDD.
# 8. Glosario rápido

| Término | Definición |
| --- | --- |
| SRS / DDD | Especificación de Requisitos de Software / Descripción de Diseño de Software. |
| RF / RN / RNF | Requisito Funcional / Regla de Negocio / Requisito No Funcional. |
| ADR | Registro de Decisión Arquitectónica (Architecture Decision Record). |
| Sala | Espacio privado identificado por código donde los jugadores se reúnen antes de jugar. |
| Partida | Instancia de juego iniciada a partir de una sala. |
| Turno / Ronda | Paso individual de un autor / ciclo completo de turnos de todos los jugadores. |
| Puntaje secreto / Voto | Enteros entre 1 y 10 asignados por el autor / emitidos por los votantes. |
