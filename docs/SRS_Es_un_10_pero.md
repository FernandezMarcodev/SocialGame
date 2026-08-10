# ESPECIFICACIÓN DE REQUISITOS DE SOFTWARE

**Sistema “Es un 10 pero…”**

Videojuego multijugador por turnos — Arquitectura cliente-servidor

Documento SRS · Versión 1.0 · Estado: Preliminar · Estándar IEEE 830/IEEE 29148

Referencia: SRS-ES10P

---

# 1. Introducción

## 1.1 Objetivo

El presente documento tiene como propósito especificar los requisitos funcionales y no funcionales del sistema “Es un 10 pero…”, un videojuego multijugador por turnos desarrollado bajo una arquitectura cliente-servidor.

El sistema ofrecerá una API REST destinada a administrar usuarios, salas de juego y partidas multijugador sincronizadas en tiempo real. La API será independiente de cualquier interfaz gráfica, permitiendo que distintos clientes (web, móviles o de escritorio) puedan consumir sus servicios mediante contratos previamente definidos.

De esta manera, este documento será la base para las etapas de análisis, diseño, implementación, pruebas y mantenimiento del sistema, garantizando la trazabilidad entre los requisitos especificados y los distintos artefactos generados durante el ciclo de vida del software.

## 1.2 Alcance

El sistema permitirá a los usuarios registrarse, autenticarse y gestionar su perfil para participar en partidas multijugador.

Los usuarios podrán crear salas privadas, unirse mediante un código único e iniciar partidas cuando se cumplan las condiciones establecidas por el sistema.

Durante una partida, los jugadores participarán en una ronda por turnos en la cual deberán completar una frase correspondiente a la modalidad seleccionada y asignarle un puntaje secreto. El resto de los participantes intentará adivinar dicho puntaje, obteniendo el autor puntos por cada coincidencia con otro jugador.

Al finalizar la partida, el sistema calculará automáticamente el puntaje acumulado de cada jugador y determinará el ganador, o declarará un empate cuando corresponda.

Esta versión del sistema no contempla funcionalidades como chat entre jugadores, listas de amigos, rankings, estadísticas históricas, autenticación mediante proveedores externos ni mecanismos de inteligencia artificial integrados.

## 1.3 Definiciones, Acrónimos y Abreviaturas

Los términos técnicos y de dominio, así como los acrónimos utilizados a lo largo del presente documento (RF, RN, RNF, entre otros), se encuentran definidos en el Apéndice A – Glosario de Términos y Acrónimos.

# 2. Descripción General

## 2.1 Perspectiva del producto

El sistema “Es un 10 pero…” es una aplicación multijugador orientada al entretenimiento social, diseñada para permitir partidas entre usuarios. Está compuesto principalmente por una API REST desarrollada como servicio independiente, responsable de gestionar la lógica del negocio del juego, la administración de usuarios, la creación de salas, la sincronización de partidas y la comunicación entre los distintos clientes conectados.

La arquitectura propuesta permitirá desacoplar la lógica de negocio del juego de la interfaz de usuario, posibilitando la incorporación futura de diferentes clientes, como aplicaciones web, móviles o de escritorio, sin modificar el núcleo del sistema.

El sistema utilizará una comunicación basada en contratos definidos previamente, garantizando una interacción consistente entre el backend y los clientes consumidores de la API.

## 2.2 Arquitectura general del sistema

Cliente consumidor

Interfaz encargada de interactuar con los usuarios. Puede ser una aplicación web, móvil o cualquier otro cliente compatible con los contratos definidos.

API del sistema

Servicio encargado de exponer las operaciones disponibles. Implementará la lógica de negocio del juego y gestionará la autenticación, las salas, las partidas y la comunicación entre jugadores.

Base de datos

Responsable de almacenar la información persistente del sistema. Contendrá los datos relacionados con los usuarios y la configuración necesaria para la operación del sistema.

Canal de comunicación en tiempo real

Permitirá mantener sincronizados a los jugadores durante una partida activa. Será utilizado para transmitir eventos relacionados con cambios de estado del juego.

## 2.3 Usuarios del sistema

El sistema contempla como usuario principal al jugador participante de una partida. Los jugadores interactúan con el sistema mediante un cliente externo, sin requerir conocimientos técnicos sobre la infraestructura interna.

En esta primera versión no se contempla un usuario administrador con acceso funcional dentro de la aplicación.

## 2.4 Restricciones generales

El desarrollo del sistema estará condicionado por las siguientes restricciones:

- El backend será implementado utilizando Python 3.12 y el framework FastAPI.
- La persistencia utilizará PostgreSQL como sistema gestor de bases de datos.
- El despliegue será realizado mediante contenedores Docker.
- La comunicación entre componentes deberá realizarse mediante contratos JSON previamente definidos.
- La primera versión estará orientada a partidas privadas entre grupos reducidos de usuarios.
- El sistema no incluirá inicialmente funcionalidades sociales complementarias, como chats, amigos, ranking o estadísticas históricas.
## 2.5 Evolución prevista

La arquitectura propuesta permitirá futuras extensiones del sistema, incluyendo nuevas modalidades de juego, clientes adicionales, funcionalidades sociales y sistemas de seguimiento de actividad.

## 2.6 Componentes del sistema

Con el propósito de favorecer una arquitectura modular, facilitar el mantenimiento del software y garantizar la trazabilidad entre los requisitos y los componentes encargados de implementarlos, el sistema estará organizado en módulos funcionales, cada uno con responsabilidades claramente definidas. Esta organización permitirá separar la lógica de negocio en componentes independientes, reduciendo el acoplamiento entre ellos y facilitando futuras ampliaciones del sistema.

### 2.6.1 Módulo de usuarios

Responsable de la gestión de la información correspondiente a los usuarios registrados en el sistema. Administrará el registro de nuevas cuentas, la consulta de perfiles y la validación de la información asociada a cada jugador. Asimismo, será responsable de asignar una imagen de perfil predeterminada generada automáticamente durante la creación de la cuenta.

### 2.6.2 Módulo de autenticación

Responsable de verificar la identidad de los usuarios y controlar el acceso a las funcionalidades protegidas del sistema. Administrará el proceso de autenticación mediante credenciales y garantizará que únicamente los usuarios autenticados puedan acceder a las operaciones que así lo requieran.

### 2.6.3 Módulo de salas

Responsable de administrar las salas de juego donde los usuarios se reúnen antes del inicio de una partida. Gestionará la creación de salas, la generación de códigos únicos de acceso, el ingreso y abandono de jugadores, la selección de la modalidad de juego y la validación de las condiciones necesarias para iniciar una partida.

### 2.6.4 Módulo de partidas

Responsable de administrar el ciclo de vida completo de una partida, desde su creación hasta su finalización. Controlará el estado general del juego, la selección del jugador inicial, la ejecución de la ronda y la finalización de la sesión de juego.

### 2.6.5 Módulo de turnos

Responsable de gestionar el desarrollo de cada turno durante una partida. Administrará las etapas de redacción de la frase, la asignación del puntaje secreto, la recepción de los votos emitidos por los participantes, el control de los tiempos establecidos y el cambio de turno entre jugadores.

### 2.6.6 Módulo de puntuación

Responsable de aplicar las reglas de puntuación definidas por el sistema. Calculará automáticamente los puntos obtenidos por el autor de cada frase según la coincidencia entre el puntaje secreto y los votos emitidos por los demás jugadores, además de mantener actualizado el marcador durante toda la partida.

### 2.6.7 Módulo de comunicación en tiempo real

Responsable de mantener sincronizados a todos los jugadores durante una partida activa. Administrará el intercambio de eventos relacionados con el estado del juego, permitiendo que todos los clientes reciban en tiempo real las actualizaciones correspondientes al desarrollo de la partida.

### 2.6.8 Módulo de persistencia

Responsable de gestionar el acceso a la información persistente del sistema. Administrará el almacenamiento y la recuperación de los datos de los usuarios y de la configuración necesaria para el funcionamiento de la aplicación, garantizando la integridad de la información almacenada.

# 3. Reglas de Negocio

## 3.1 Gestión de usuarios

RN-001. El nombre de usuario deberá ser único dentro del sistema.

RN-002. El correo electrónico deberá ser único dentro del sistema.

RN-003. Todo usuario deberá autenticarse para acceder a las funcionalidades del juego.

RN-004. Un usuario no podrá participar simultáneamente en más de una sala.

RN-005. Todo usuario dispondrá de una imagen de perfil generada automáticamente por el sistema en base a la inicial de su nombre de usuario. Esta versión del sistema no contempla la carga de una imagen de perfil personalizada.

## 3.2 Gestión de salas

RN-006. Todas las salas serán privadas y solo podrán ser identificadas mediante un código generado por el sistema.

RN-007. Solo el creador de una sala podrá iniciar una partida.

RN-008. Una partida sólo podrá iniciarse cuando la sala cuente con un mínimo de 2 y un máximo de 6 jugadores.

RN-009. Una vez iniciada la partida, no se permitirá el ingreso de nuevos jugadores.

RN-010. El creador de la sala podrá cancelar la partida antes de iniciarla.

RN-011. La modalidad de juego será seleccionada por el creador de la sala antes del inicio de la partida y permanecerá fija durante toda la sesión de juego.

## 3.3 Desarrollo de la partida

A los efectos de esta sección se entiende por “ronda” al ciclo completo de la partida, compuesto por un turno de cada jugador participante. En esta versión del sistema, la partida está compuesta por una única ronda. Se entiende por “turno” al paso individual dentro de la ronda, correspondiente a un jugador determinado: dicho jugador actúa como autor de la frase, mientras el resto de los jugadores activos actúa como votante.

RN-012. El jugador que tenga el turno deberá completar la frase correspondiente a la modalidad seleccionada y asignarle un puntaje secreto entero comprendido entre 1 y 10.

RN-013. El puntaje secreto no será visible para los demás jugadores hasta finalizar la etapa de votación.

RN-014. Los jugadores solo podrán emitir un voto por turno.

RN-015. Los votos deberán ser números enteros comprendidos entre 1 y 10.

RN-016. Los jugadores no podrán visualizar los votos emitidos por los demás participantes hasta que finalice la votación de turno.

RN-017. Si un jugador abandona una partida iniciada, perderá la posibilidad de participar en los turnos restantes de la ronda. El turno en el que dicho jugador debía actuar como autor, si aún no se había jugado, quedará descartado y no se reasignará a otro jugador. Si como consecuencia del abandono quedan menos de 2 jugadores activos, la partida finalizará automáticamente.

## 3.4 Puntuación

RN-018. Los puntos serán otorgados sólo al autor de la frase.

RN-019. El autor obtendrá un punto por cada jugador que acierte exactamente el puntaje secreto.

RN-020. Al finalizar cada turno, el sistema mostrará el puntaje secreto, los votos emitidos y el puntaje acumulado de todos los jugadores.

## 3.5 Finalización

RN-021. Una partida finalizará cuando se hayan completado todos los turnos que componen la ronda. Se considerará que un jugador participó en la ronda cuando haya actuado como autor en su propio turno y haya emitido su voto en cada uno de los turnos de los demás jugadores activos.

RN-022. La ronda estará compuesta por una cantidad de turnos igual a la cantidad de jugadores presentes al inicio de la partida. Esta cantidad no se recalcula si algún jugador abandona la partida; los turnos correspondientes al jugador que abandonó quedan descartados conforme a lo establecido en RN-017, sin ser reemplazados por turnos adicionales de otros jugadores.

RN-023. Si dos o más jugadores finalizan con el mayor puntaje, el sistema declarará un empate.

## 3.6 Consideraciones

RN-024. Al finalizar la partida, la sala será eliminada automáticamente.

RN-025. La partida estará compuesta por una única ronda, integrada por tantos turnos como jugadores participen al inicio. En cada turno, un jugador distinto actuará como autor de la frase, mientras el resto de los jugadores activos actuará como votante.

RN-026. El sistema permitirá seleccionar únicamente modalidades de juego previamente configuradas.

RN-027. El código de sala deberá ser único mientras la partida se encuentre activa.

# 4. Especificación de Requisitos Funcionales

## 4.1 Módulo de Usuarios

Responsabilidad

El módulo de usuarios será responsable de administrar la información asociada a las cuentas registradas dentro del sistema, incluyendo la creación de nuevos usuarios, la consulta de perfiles y la validación de la información asociada a cada jugador. Asimismo, será responsable de asignar una imagen de perfil predeterminada generada automáticamente durante la creación de la cuenta.

#### RF-USR-001 — Registrar usuario

Descripción

El sistema deberá permitir al usuario registrarse mediante la creación de una nueva cuenta, ingresando la información necesaria para identificarse dentro de la aplicación.

Entradas

- Nombre de usuario.
- Correo electrónico.
- Contraseña.
- Datos adicionales requeridos para la creación de la cuenta.
Proceso

1. El usuario ingresa sus datos de registro.

2. El sistema valida que la información ingresada cumpla con las condiciones establecidas.

3. El sistema verifica la disponibilidad del nombre de usuario y correo electrónico.

4. El sistema almacena la información del nuevo usuario.

5. El sistema genera el perfil inicial asociado a la cuenta.

Salidas

- Usuario registrado correctamente.
- Confirmación de creación de cuenta.
- Identificador del usuario generado por el sistema.
Verificaciones

- El nombre de usuario no debe existir previamente.
- El correo electrónico no debe estar registrado previamente.
- Los campos obligatorios deben encontrarse completos.
- La contraseña debe cumplir las restricciones de seguridad definidas.
Excepciones

- El nombre de usuario ya se encuentra registrado.
- El correo electrónico ya pertenece a una cuenta existente.
- La información ingresada no cumple con las validaciones establecidas.
- Error durante el almacenamiento de los datos.
#### RF-USR-002 — Validar unicidad del nombre de usuario

Descripción

El sistema deberá verificar que el nombre de usuario ingresado durante el registro o modificación del perfil no se encuentre asociado a otro usuario existente.

Entradas

- Nombre de usuario ingresado por el usuario.
Proceso

1. El sistema recibe el nombre de usuario.

2. El sistema consulta la base de datos.

3. El sistema determina si existe otro usuario con el mismo nombre.

4. El sistema permite o rechaza la operación según el resultado obtenido.

Salidas

- Confirmación de disponibilidad del nombre de usuario.
- Mensaje indicando que el nombre ya se encuentra utilizado.
Verificaciones

- La comparación deberá realizarse contra todos los usuarios registrados.
- El nombre de usuario deberá cumplir las restricciones definidas por el sistema.
Excepciones

- Error de conexión con la base de datos.
- Consulta no disponible durante la validación.
#### RF-USR-003 — Validar unicidad del correo electrónico

Descripción

El sistema deberá verificar que el correo electrónico ingresado por el usuario no se encuentre asociado a otra cuenta existente.

Entradas

- Correo electrónico ingresado por el usuario.
Proceso

1. El sistema recibe el correo electrónico.

2. El sistema consulta los registros existentes.

3. El sistema determina si el correo ya fue registrado.

4. El sistema permite continuar con el proceso o informa el conflicto detectado.

Salidas

- Confirmación de disponibilidad del correo electrónico.
- Notificación indicando que el correo ya está registrado.
Verificaciones

- El formato del correo electrónico deberá ser válido.
- El correo no deberá existir previamente en el sistema.
Excepciones

- Correo electrónico con formato incorrecto.
- Error de acceso a la información almacenada.
#### RF-USR-004 — Validar información del registro

Descripción

El sistema deberá validar que la información ingresada durante el registro de usuario sea correcta y cumpla con las reglas definidas.

Entradas

- Datos ingresados durante el registro.
- Nombre de usuario.
- Correo electrónico.
- Contraseña.
Proceso

1. El sistema recibe la información ingresada.

2. El sistema valida formato y restricciones de cada campo.

3. El sistema determina si la información puede ser utilizada para crear la cuenta.

Salidas

- Datos validados correctamente.
- Lista de errores encontrados durante la validación.
Verificaciones

- Campos obligatorios completos.
- Formatos correctos.
- Cumplimiento de restricciones de longitud y seguridad.
Excepciones

- Campos obligatorios vacíos.
- Información con formato inválido.
- Datos que no cumplen las reglas definidas.
#### RF-USR-005 — Generar imagen de perfil predeterminada

Descripción

El sistema deberá generar automáticamente una imagen de perfil predeterminada para cada usuario registrado, utilizando la inicial correspondiente a su nombre de usuario.

Entradas

- Nombre de usuario registrado.
Proceso

1. El sistema obtiene el nombre del usuario.

2. El sistema identifica la inicial correspondiente.

3. El sistema genera la imagen de perfil predeterminada asociada a la cuenta.

4. El sistema almacena la referencia de la imagen de perfil generada.

Salidas

- Imagen de perfil predeterminada asignada al usuario.
Verificaciones

- El usuario debe poseer un nombre válido.
- La generación de la imagen de perfil debe completarse correctamente.
Excepciones

- Nombre de usuario inexistente.
- Error durante la generación o almacenamiento de la imagen de perfil.
#### RF-USR-006 — Consultar perfil de usuario

Descripción

El sistema deberá permitir al usuario consultar la información asociada a su perfil registrado dentro de la aplicación.

Entradas

- Identificador del usuario autenticado.
Proceso

1. El sistema recibe la solicitud de consulta.

2. El sistema identifica al usuario correspondiente.

3. El sistema obtiene la información almacenada.

4. El sistema devuelve los datos disponibles del perfil.

Salidas

- Información del perfil del usuario.
- Datos asociados a la cuenta.
Verificaciones

- El usuario debe encontrarse autenticado.
- El usuario debe existir dentro del sistema.
Excepciones

- Usuario inexistente.
- Usuario no autenticado.
- Error al recuperar información.
#### RF-USR-007 — Modificar información del perfil

Descripción

El sistema deberá permitir al usuario modificar la información editable asociada a su perfil.

Entradas

- Identificador del usuario autenticado.
- Nuevos datos del perfil.
Proceso

1. El usuario solicita modificar su información.

2. El sistema valida los nuevos datos ingresados.

3. El sistema actualiza la información correspondiente.

4. El sistema confirma la modificación realizada.

Salidas

- Perfil actualizado correctamente.
- Información modificada disponible para futuras consultas.
Verificaciones

- El usuario debe estar autenticado.
- Los datos modificados deben cumplir las reglas establecidas.
- Los campos únicos deben continuar siendo válidos.
Excepciones

- Usuario no autenticado.
- Información inválida.
- Intento de utilizar datos pertenecientes a otro usuario.
- Error durante la actualización.
## 4.2 Módulo de Autenticación

Responsabilidad

El módulo de autenticación será responsable de verificar la identidad de los usuarios y controlar el acceso a las funcionalidades protegidas del sistema, administrando el inicio y cierre de sesión, la verificación de cuentas y la recuperación de contraseñas.

#### RF-AUT-001 — Verificar correo electrónico

Descripción

El sistema deberá permitir verificar la dirección de correo electrónico asociada a una cuenta de usuario, confirmando que pertenece al usuario registrado.

Entradas

- Identificador del usuario.
- Código o enlace de verificación enviado al correo electrónico.
Proceso

1. El sistema genera un mecanismo de verificación asociado al registro del usuario.

2. El usuario accede al enlace o ingresa el código recibido.

3. El sistema valida la información proporcionada.

4. El sistema actualiza el estado de verificación de la cuenta.

Salidas

- Confirmación de correo electrónico verificado.
- Actualización del estado de la cuenta.
Verificaciones

- El código o enlace debe corresponder al usuario correcto.
- El código debe encontrarse vigente.
- La cuenta debe existir dentro del sistema.
Excepciones

- Código de verificación inválido.
- Código expirado.
- Usuario inexistente.
- Error durante la actualización del estado de la cuenta.
#### RF-AUT-002 — Reenviar correo de verificación

Descripción

El sistema deberá permitir al usuario solicitar nuevamente el envío del correo electrónico de verificación cuando la cuenta aún no haya sido validada.

Entradas

- Correo electrónico registrado.
Proceso

1. El usuario solicita reenviar la verificación.

2. El sistema identifica la cuenta asociada al correo ingresado.

3. El sistema genera un nuevo mecanismo de verificación.

4. El sistema envía nuevamente la información necesaria al usuario.

Salidas

- Confirmación del envío del correo de verificación.
Verificaciones

- El correo debe estar asociado a una cuenta existente.
- La cuenta no debe encontrarse previamente verificada.
- Deben cumplirse las restricciones de envío establecidas.
Excepciones

- Correo electrónico inexistente.
- Cuenta ya verificada.
- Error en el servicio de envío de correo.
#### RF-AUT-003 — Iniciar sesión

Descripción

El sistema deberá permitir al usuario autenticarse mediante sus credenciales registradas para acceder a las funcionalidades disponibles de la aplicación.

Entradas

- Correo electrónico o nombre de usuario.
- Contraseña.
Proceso

1. El usuario ingresa sus credenciales.

2. El sistema busca la cuenta asociada.

3. El sistema valida la información ingresada.

4. El sistema genera una sesión válida para el usuario.

Salidas

- Acceso autorizado al sistema.
- Token o identificador de sesión generado.
Verificaciones

- El usuario debe existir dentro del sistema.
- La contraseña debe coincidir con la almacenada.
- La cuenta debe encontrarse habilitada.
Excepciones

- Credenciales incorrectas.
- Usuario inexistente.
- Cuenta bloqueada o no habilitada.
- Error durante la autenticación.
#### RF-AUT-004 — Validar credenciales

Descripción

El sistema deberá validar que las credenciales ingresadas por el usuario coincidan con la información almacenada previamente.

Entradas

- Correo electrónico o nombre de usuario.
- Contraseña ingresada.
Proceso

1. El sistema recibe las credenciales.

2. El sistema consulta la información del usuario.

3. El sistema compara las credenciales ingresadas con los datos almacenados.

4. El sistema determina si la autenticación puede continuar.

Salidas

- Credenciales válidas.
- Rechazo de autenticación por datos incorrectos.
Verificaciones

- El usuario debe encontrarse registrado.
- La contraseña deberá coincidir con la almacenada.
- Los datos ingresados deberán cumplir el formato esperado.
Excepciones

- Usuario inexistente.
- Contraseña incorrecta.
- Error de acceso a la información almacenada.
#### RF-AUT-005 — Controlar intentos fallidos

Descripción

El sistema deberá controlar la cantidad de intentos fallidos de autenticación realizados por un usuario para proteger la cuenta ante accesos no autorizados.

Entradas

- Usuario identificado.
- Resultado del intento de autenticación.
Proceso

1. El sistema registra cada intento de inicio de sesión.

2. El sistema incrementa el contador de intentos fallidos cuando corresponde.

3. El sistema verifica si se alcanzó el límite permitido.

4. El sistema aplica las medidas definidas.

Salidas

- Registro actualizado de intentos.
- Bloqueo temporal de la cuenta cuando corresponda.
Verificaciones

- El contador de intentos debe mantenerse actualizado.
- El límite de intentos debe respetar la configuración del sistema.
Excepciones

- Error al registrar el intento.
- Información inconsistente del usuario.
#### RF-AUT-006 — Cerrar sesión

Descripción

El sistema deberá permitir al usuario finalizar su sesión activa dentro de la aplicación.

Entradas

- Identificador de sesión o token autenticado.
Proceso

1. El usuario solicita cerrar sesión.

2. El sistema valida la sesión activa.

3. El sistema invalida el acceso asociado.

4. El sistema confirma la finalización de la sesión.

Salidas

- Sesión cerrada correctamente.
- Token invalidado.
Verificaciones

- La sesión debe encontrarse activa.
- El usuario debe estar autenticado.
Excepciones

- Sesión inexistente.
- Token inválido.
- Error al invalidar la sesión.
#### RF-AUT-007 — Cambiar contraseña

Descripción

El sistema deberá permitir al usuario modificar su contraseña actual por una nueva contraseña válida.

Entradas

- Usuario autenticado.
- Contraseña actual.
- Nueva contraseña.
Proceso

1. El usuario solicita modificar su contraseña.

2. El sistema valida la contraseña actual.

3. El sistema valida las condiciones de la nueva contraseña.

4. El sistema actualiza la contraseña almacenada.

Salidas

- Confirmación de contraseña actualizada.
Verificaciones

- El usuario debe estar autenticado.
- La contraseña actual debe ser correcta.
- La nueva contraseña debe cumplir las reglas de seguridad.
Excepciones

- Contraseña actual incorrecta.
- Nueva contraseña inválida.
- Error durante la actualización.
#### RF-AUT-008 — Solicitar recuperación de contraseña

Descripción

El sistema deberá permitir al usuario solicitar la recuperación de acceso a su cuenta cuando no recuerde su contraseña.

Entradas

- Correo electrónico registrado.
Proceso

1. El usuario solicita recuperar su contraseña.

2. El sistema identifica la cuenta asociada.

3. El sistema genera un mecanismo de recuperación.

4. El sistema envía las instrucciones correspondientes.

Salidas

- Confirmación de solicitud enviada.
- Información necesaria para recuperar el acceso.
Verificaciones

- El correo debe encontrarse registrado.
- La solicitud debe cumplir las restricciones de seguridad.
Excepciones

- Correo inexistente.
- Solicitud inválida.
- Error en el envío del correo.
#### RF-AUT-009 — Restablecer contraseña

Descripción

El sistema deberá permitir al usuario establecer una nueva contraseña utilizando el mecanismo de recuperación generado previamente.

Entradas

- Código o enlace de recuperación.
- Nueva contraseña.
Proceso

1. El usuario accede al mecanismo de recuperación.

2. El sistema valida la solicitud.

3. El usuario ingresa una nueva contraseña.

4. El sistema actualiza la información de autenticación.

Salidas

- Contraseña actualizada correctamente.
- Confirmación de recuperación completada.
Verificaciones

- El código de recuperación debe ser válido.
- El código debe encontrarse vigente.
- La nueva contraseña debe cumplir las restricciones definidas.
Excepciones

- Código inválido.
- Código expirado.
- Nueva contraseña no válida.
- Error durante la actualización.
## 4.3 Módulo de Salas

Responsabilidad

El módulo de salas será responsable de administrar las salas de juego donde los usuarios se reúnen antes del inicio de una partida. Gestionará la creación de salas, la generación de códigos únicos de acceso, el ingreso y abandono de jugadores, la selección de la modalidad de juego y la validación de las condiciones necesarias para iniciar una partida.

#### RF-SAL-001 — Crear sala

Descripción

El sistema deberá permitir al usuario crear una nueva sala privada de juego, generando un identificador único que permita a otros jugadores ingresar mediante dicho código.

Entradas

- Usuario autenticado creador de la sala.
- Modalidad de juego seleccionada.
Proceso

1. El usuario solicita la creación de una sala.

2. El sistema valida que el usuario pueda crear una nueva sala.

3. El sistema genera un código único de identificación.

4. El sistema registra la nueva sala asociando al usuario creador.

5. El sistema establece la modalidad seleccionada.

Salidas

- Sala creada correctamente.
- Código de acceso generado.
- Información inicial de la sala.
Verificaciones

- El usuario debe encontrarse autenticado.
- El usuario no debe pertenecer a otra sala activa.
- La modalidad seleccionada debe encontrarse disponible.
Excepciones

- Usuario no autenticado.
- Usuario ya perteneciente a una sala.
- Modalidad inexistente.
- Error al almacenar la información de la sala.
#### RF-SAL-002 — Unirse a una sala

Descripción

El sistema deberá permitir al usuario ingresar a una sala existente mediante el código generado previamente.

Entradas

- Usuario autenticado.
- Código de sala.
Proceso

1. El usuario ingresa el código de acceso.

2. El sistema busca la sala asociada.

3. El sistema valida que la sala permita nuevos jugadores.

4. El sistema incorpora al usuario dentro de la sala.

Salidas

- Usuario agregado correctamente a la sala.
- Información actualizada de participantes.
Verificaciones

- La sala debe existir.
- La partida no debe encontrarse iniciada.
- El usuario no debe estar participando en otra sala.
- Debe cumplirse la cantidad máxima de jugadores establecida.
Excepciones

- Código inválido.
- Sala inexistente.
- Partida ya iniciada.
- Usuario perteneciente a otra sala.
#### RF-SAL-003 — Consultar información de una sala

Descripción

El sistema deberá permitir consultar la información correspondiente a una sala activa antes del inicio de una partida.

Entradas

- Identificador de sala.
- Usuario autenticado.
Proceso

1. El usuario solicita información de la sala.

2. El sistema identifica la sala correspondiente.

3. El sistema obtiene los datos asociados.

4. El sistema devuelve la información disponible.

Salidas

- Código de sala.
- Modalidad seleccionada.
- Lista de jugadores participantes.
- Estado actual de la sala.
Verificaciones

- El usuario debe tener permisos para consultar la sala.
- La sala debe encontrarse activa.
Excepciones

- Sala inexistente.
- Usuario no autorizado.
- Error al recuperar información.
#### RF-SAL-004 — Abandonar una sala

Descripción

El sistema deberá permitir que un usuario abandone una sala antes del inicio de una partida.

Entradas

- Usuario autenticado.
- Identificador de sala.
Proceso

1. El usuario solicita abandonar la sala.

2. El sistema valida la pertenencia del usuario.

3. El sistema elimina la asociación entre usuario y sala.

4. El sistema actualiza la información de participantes.

Salidas

- Usuario eliminado de la sala.
- Estado actualizado de la sala.
Verificaciones

- El usuario debe pertenecer a la sala.
- La partida no debe encontrarse iniciada.
Excepciones

- Usuario no pertenece a la sala.
- Sala inexistente.
- La partida ya fue iniciada.
#### RF-SAL-005 — Iniciar una partida

Descripción

El sistema deberá permitir al creador de una sala iniciar una partida cuando se cumplan las condiciones necesarias definidas por las reglas de negocio.

Entradas

- Usuario creador de la sala.
- Identificador de sala.
Proceso

1. El creador solicita iniciar la partida.

2. El sistema valida que el usuario sea el propietario de la sala.

3. El sistema verifica las condiciones necesarias establecidas en las reglas de negocio (RN-007, RN-008).

4. El sistema solicita al módulo de partidas la creación e inicialización de la partida asociada (ver RF-PAR-001 y RF-PAR-002).

5. El sistema actualiza el estado de la sala indicando que la partida fue iniciada.

Salidas

- Partida creada e inicializada correctamente.
- Sala marcada como iniciada.
- Jugadores notificados del inicio.
Verificaciones

- El usuario debe ser el creador de la sala.
- Debe existir la cantidad mínima de jugadores.
- La sala debe encontrarse en estado disponible.
Excepciones

- Usuario sin permisos.
- Cantidad insuficiente de jugadores.
- Partida ya iniciada.
#### RF-SAL-006 — Cancelar una sala

Descripción

El sistema deberá permitir al creador cancelar una sala antes del inicio de la partida.

Entradas

- Usuario creador.
- Identificador de sala.
Proceso

1. El creador solicita cancelar la sala.

2. El sistema valida los permisos del usuario.

3. El sistema cambia el estado de la sala.

4. El sistema elimina la disponibilidad de acceso.

Salidas

- Sala cancelada correctamente.
- Jugadores notificados de la cancelación.
Verificaciones

- El usuario debe ser creador de la sala.
- La partida no debe haber iniciado.
Excepciones

- Usuario sin permisos.
- Sala inexistente.
- Partida iniciada.
#### RF-SAL-007 — Eliminar automáticamente una sala

Descripción

El sistema deberá eliminar automáticamente una sala cuando finalice su ciclo de vida según las reglas definidas.

Entradas

- Estado de la partida asociada.
- Identificador de sala.
Proceso

1. El sistema detecta que la sala debe ser eliminada.

2. El sistema elimina la información temporal asociada.

3. El sistema libera el código de acceso.

4. El sistema actualiza el estado del sistema.

Salidas

- Sala eliminada correctamente.
- Código disponible para futuras salas.
Verificaciones

- La partida asociada debe haber finalizado o la sala debe encontrarse cancelada.
- No deben existir operaciones activas asociadas.
Excepciones

- Error al eliminar información.
- Sala inexistente.
#### RF-SAL-008 — Validar condiciones de ingreso a una sala

Descripción

El sistema deberá validar que un usuario cumpla las condiciones necesarias para ingresar a una sala determinada.

Entradas

- Usuario autenticado.
- Código de sala.
Proceso

1. El sistema recibe la solicitud de ingreso.

2. El sistema verifica el estado de la sala.

3. El sistema valida las restricciones del usuario.

4. El sistema determina si permite o rechaza el ingreso.

Salidas

- Confirmación de ingreso permitido.
- Rechazo indicando la condición incumplida.
Verificaciones

- La sala debe existir.
- La sala debe permitir nuevos jugadores.
- El usuario no debe encontrarse en otra sala.
- Debe respetarse el límite de jugadores.
Excepciones

- Código incorrecto.
- Sala cerrada.
- Usuario no válido.
- Límite de jugadores alcanzado.
## 4.4 Módulo de Partidas

Responsabilidad

El módulo de partidas será responsable de administrar el ciclo de vida completo de una partida, desde su creación hasta su finalización. Controlará la creación de la partida, el estado general del juego, la selección del jugador inicial, la ejecución de la ronda y la finalización de la sesión de juego.

#### RF-PAR-001 — Crear partida

Descripción

El sistema deberá permitir la creación de una nueva partida a partir de una sala válida, generando la instancia correspondiente del juego y asociando los jugadores participantes.

Entradas

- Identificador de la sala.
- Identificador del usuario creador.
- Lista de jugadores pertenecientes a la sala.
- Modalidad seleccionada.
Proceso

1. El sistema recibe la solicitud de creación de partida, generada por el módulo de salas (ver RF-SAL-005).

2. Verifica que la sala exista y se encuentre disponible.

3. Valida que se cumplan las condiciones necesarias para iniciar una partida.

4. Genera una nueva instancia de partida con estado “Creada”.

5. Asocia los jugadores participantes.

6. Solicita la inicialización de la partida (ver RF-PAR-002).

Salidas

- Identificador único de la partida.
- Estado inicial de la partida (“Creada”).
- Lista de jugadores participantes.
- Confirmación de creación exitosa.
Verificaciones

- La sala debe existir.
- El usuario debe ser el creador de la sala.
- La sala debe encontrarse en estado disponible.
- Debe existir la cantidad mínima de jugadores requerida.
Excepciones

- La sala no existe.
- El usuario no tiene permisos para iniciar la partida.
- La partida ya fue creada previamente.
- No se cumple la cantidad mínima de jugadores.
#### RF-PAR-002 — Inicializar partida

Descripción

El sistema deberá inicializar una partida creada, estableciendo las condiciones iniciales necesarias para comenzar el desarrollo del juego.

Entradas

- Identificador de partida.
- Lista de jugadores participantes.
Proceso

1. El sistema recibe la solicitud de inicialización.

2. Verifica que la partida se encuentre en estado “Creada”.

3. Genera el orden de participación de los jugadores (ver RF-PAR-003).

4. Establece el estado de la partida como “Inicializada”.

5. Solicita al módulo de turnos el inicio del primer turno de la ronda (ver RF-TUR-001), lo que da lugar a la transición de la partida al estado “En curso” (ver RF-PAR-004).

Salidas

- Estado actualizado de la partida (“Inicializada”).
- Confirmación de partida inicializada.
- Información del primer jugador en turno.
Verificaciones

- La partida debe existir.
- La partida debe encontrarse en estado “Creada”.
- Debe contar con jugadores participantes válidos.
Excepciones

- La partida no existe.
- La partida no se encuentra en estado “Creada”.
- No existen jugadores disponibles.
#### RF-PAR-003 — Generar orden de participación

Descripción

El sistema deberá generar automáticamente el orden en el que los jugadores participarán como autores durante el desarrollo de la partida.

Entradas

- Identificador de partida.
- Lista de jugadores participantes.
Proceso

1. El sistema obtiene los jugadores asociados a la partida.

2. Genera un orden aleatorio de participación.

3. Guarda el orden generado.

4. Asigna el primer jugador como participante inicial.

Salidas

- Orden de participación generado.
- Jugador correspondiente al primer turno.
Verificaciones

- Todos los jugadores deben pertenecer a la partida.
- El orden debe contener a todos los jugadores participantes.
- No deben existir jugadores duplicados.
Excepciones

- La partida no existe.
- La lista de jugadores está vacía.
- No se puede generar un orden válido.
#### RF-PAR-004 — Administrar el estado de la partida

Descripción

El sistema deberá gestionar los diferentes estados posibles de una partida durante su ciclo de vida. La transición de “Inicializada” a “En curso” se produce automáticamente al iniciarse el primer turno de la partida (ver RF-TUR-001).

Entradas

- Identificador de partida.
- Evento ocurrido durante el juego.
Proceso

1. El sistema recibe un evento asociado a la partida.

2. Evalúa el estado actual.

3. Determina la transición correspondiente.

4. Actualiza el estado de la partida.

Estados contemplados

- Creada.
- Inicializada.
- En curso.
- Finalizada.
- Cancelada.
Salidas

- Nuevo estado de la partida.
- Evento de actualización generado.
Verificaciones

- La transición solicitada debe ser válida.
- La partida debe existir.
- El evento recibido debe corresponder al estado actual.
Excepciones

- Estado inválido.
- Transición no permitida.
- Partida inexistente.
#### RF-PAR-005 — Controlar el avance de la ronda

Descripción

El sistema deberá controlar el avance de la ronda, verificando la finalización de cada turno y determinando cuándo corresponde avanzar al siguiente jugador.

Entradas

- Identificador de partida.
- Estado actual del turno.
- Jugador actual.
Proceso

1. El sistema recibe la finalización de un turno.

2. Verifica si el turno fue completado correctamente.

3. Actualiza el progreso de la ronda.

4. Determina si existen jugadores pendientes de participar.

5. En caso afirmativo, habilita el siguiente turno.

Salidas

- Estado actualizado de la ronda.
- Identificador del siguiente jugador.
- Notificación del cambio de turno.
Verificaciones

- El turno anterior debe haber finalizado.
- El jugador debe pertenecer a la partida.
- La partida debe encontrarse en curso.
Excepciones

- Turno inexistente.
- Jugador inválido.
- La partida ya finalizó.
#### RF-PAR-006 — Finalizar la partida

Descripción

El sistema deberá finalizar una partida cuando se hayan completado todos los turnos correspondientes o cuando se cumpla una condición de finalización anticipada.

Entradas

- Identificador de partida.
- Estado actual del juego.
- Resultado de los turnos realizados.
Proceso

1. El sistema verifica si se cumplen las condiciones de finalización.

2. Cambia el estado de la partida a “Finalizada”.

3. Calcula la información final necesaria.

4. Genera el evento de finalización.

Salidas

- Estado final de la partida.
- Puntajes acumulados.
- Resultado de la partida.
Verificaciones

- Todos los turnos requeridos deben estar completados.
- La partida debe encontrarse en curso.
- Los puntajes deben estar calculados correctamente.
Excepciones

- La partida no existe.
- La partida ya fue finalizada.
- Información incompleta de resultados.
#### RF-PAR-007 — Determinar el resultado final

Descripción

El sistema deberá determinar automáticamente el resultado final de la partida considerando los puntajes acumulados obtenidos por los jugadores.

Entradas

- Identificador de partida.
- Puntajes acumulados de los jugadores.
Proceso

1. El sistema obtiene los puntajes finales.

2. Compara los valores obtenidos por cada jugador.

3. Identifica al jugador con mayor puntuación.

4. Determina si existe un ganador o empate.

Salidas

- Jugador ganador.
- Resultado de empate si corresponde.
- Resumen final de puntuaciones.
Verificaciones

- Todos los jugadores deben tener puntaje registrado.
- Los puntajes deben ser valores válidos.
- La partida debe encontrarse finalizada.
Excepciones

- No existen puntajes disponibles.
- La partida no finalizó.
- Datos inconsistentes de puntuación.
## 4.5 Módulo de Turnos

Responsabilidad

El módulo de turnos será responsable de gestionar el desarrollo de cada turno durante una partida. Administrará las etapas de redacción de la frase, la asignación del puntaje secreto, la recepción de los votos emitidos por los participantes, el control de los tiempos establecidos y el cambio de turno entre jugadores. Cada turno podrá encontrarse en uno de los siguientes estados: “Activo” (redacción de la frase y asignación del puntaje secreto), “En votación” (recepción de votos de los jugadores participantes) y “Finalizado” (resultado publicado).

#### RF-TUR-001 — Iniciar turno

Descripción

El sistema deberá permitir iniciar un nuevo turno dentro de una partida en curso, asignando al jugador correspondiente como autor de la frase.

Entradas

- Identificador de partida.
- Identificador del jugador asignado al turno.
- Estado actual de la partida.
Proceso

1. El sistema recibe la solicitud de inicio de turno.

2. Verifica que la partida se encuentre en curso.

3. Identifica al jugador correspondiente según el orden de participación.

4. Crea la instancia del turno.

5. Asigna al jugador como autor.

6. Cambia el estado del turno a “Activo”.

Salidas

- Identificador del turno.
- Jugador autor asignado.
- Estado actual del turno.
Verificaciones

- La partida debe existir.
- La partida debe encontrarse en curso.
- El jugador debe pertenecer a la partida.
- El turno no debe haber sido iniciado previamente.
Excepciones

- Partida inexistente.
- Jugador no válido.
- La partida ya finalizó.
- El turno ya se encuentra iniciado.
#### RF-TUR-002 — Notificar inicio de turno

Descripción

El sistema deberá notificar a todos los jugadores conectados el inicio de un nuevo turno y el jugador responsable de completar la frase.

Entradas

- Identificador del turno.
- Identificador del jugador autor.
- Estado del turno.
Proceso

1. El sistema obtiene la información del turno iniciado.

2. Genera el evento correspondiente.

3. Envía la notificación mediante el canal de comunicación en tiempo real.

4. Actualiza el estado visible para los clientes conectados.

Salidas

- Evento de inicio de turno enviado.
- Información del jugador autor.
- Estado actualizado del juego.
Verificaciones

- El turno debe encontrarse en estado “Activo”.
- Los jugadores deben estar conectados a la partida.
- El evento debe corresponder al estado actual.
Excepciones

- Error en la comunicación con los clientes.
- Turno inexistente.
- Partida desconectada.
#### RF-TUR-003 — Registrar frase y puntaje secreto

Descripción

El sistema deberá permitir al jugador autor ingresar la frase completada y asignar un puntaje secreto asociado a dicha frase.

Entradas

- Identificador del turno.
- Identificador del jugador autor.
- Frase ingresada.
- Puntaje secreto.
Proceso

1. El sistema recibe la información enviada por el autor.

2. Valida los datos ingresados.

3. Guarda la frase asociada al turno.

4. Almacena el puntaje secreto sin permitir su visualización a otros jugadores.

5. Cambia el estado del turno a “En votación”.

Salidas

- Confirmación de registro exitoso.
- Estado actualizado del turno.
Verificaciones

- El jugador debe ser el autor del turno.
- La frase debe cumplir las restricciones establecidas.
- El puntaje debe estar entre 1 y 10.
- El turno debe encontrarse en estado “Activo”.
Excepciones

- Jugador no autorizado.
- Frase inválida.
- Puntaje fuera del rango permitido.
- Turno finalizado.
#### RF-TUR-004 — Validar la información ingresada por el autor

Descripción

El sistema deberá validar que la información proporcionada por el autor cumpla con las reglas definidas antes de continuar con la etapa de votación.

Entradas

- Frase ingresada.
- Puntaje secreto.
- Datos del jugador autor.
Proceso

1. El sistema recibe la información ingresada.

2. Verifica la longitud y formato de la frase.

3. Comprueba que el puntaje sea válido.

4. Determina si la información puede ser aceptada.

Salidas

- Confirmación de datos válidos.
- Mensaje de error en caso contrario.
Verificaciones

- La frase debe contener entre 3 y 200 caracteres.
- El puntaje debe ser un número entero.
- El puntaje debe encontrarse entre 1 y 10.
Excepciones

- Datos incompletos.
- Formato incorrecto.
- Valores fuera de rango.
#### RF-TUR-005 — Controlar el tiempo del autor

Descripción

El sistema deberá controlar el tiempo disponible para que el jugador autor complete la frase y asigne el puntaje secreto.

Entradas

- Identificador del turno.
- Tiempo máximo configurado.
- Estado del turno.
Proceso

1. El sistema inicia el contador del turno.

2. Monitorea el tiempo transcurrido.

3. Verifica si el autor completó la acción dentro del tiempo establecido.

4. Ejecuta la acción correspondiente al finalizar el tiempo.

Salidas

- Confirmación de finalización dentro del tiempo.
- Evento de expiración del turno si corresponde.
Verificaciones

- El turno debe encontrarse en estado “Activo”.
- Debe existir un tiempo configurado.
- El contador no debe haber finalizado previamente.
Excepciones

- Turno inexistente.
- Tiempo inválido.
- Error de sincronización.
#### RF-TUR-006 — Iniciar la etapa de votación

Descripción

El sistema deberá iniciar la etapa de votación una vez que el autor haya registrado correctamente la frase y el puntaje secreto.

Entradas

- Identificador del turno.
- Frase registrada.
- Lista de jugadores participantes.
Proceso

1. El sistema verifica que la información del autor sea válida.

2. Cambia el estado del turno a “En votación”.

3. Envía la frase a los jugadores participantes.

4. Habilita la recepción de votos.

Salidas

- Turno en estado “En votación”.
- Frase disponible para los jugadores.
- Confirmación de votación iniciada.
Verificaciones

- El autor debe haber completado la información requerida.
- Los jugadores deben pertenecer a la partida.
- El turno debe encontrarse en estado “Activo”.
Excepciones

- Información incompleta.
- Turno inválido.
- Partida finalizada.
#### RF-TUR-007 — Registrar voto

Descripción

El sistema deberá permitir a los jugadores participantes registrar un voto correspondiente al puntaje que consideran correcto para la frase presentada.

Entradas

- Identificador del turno.
- Identificador del jugador votante.
- Puntaje seleccionado.
Proceso

1. El sistema recibe el voto del jugador.

2. Verifica que el jugador pueda votar.

3. Valida el puntaje ingresado.

4. Guarda el voto asociado al turno.

Salidas

- Confirmación de voto registrado.
- Estado actualizado de votos recibidos.
Verificaciones

- El jugador no debe ser el autor del turno.
- El jugador debe pertenecer a la partida.
- Solo debe existir un voto por jugador.
- El puntaje debe estar entre 1 y 10.
Excepciones

- Jugador no autorizado.
- Voto duplicado.
- Puntaje inválido.
- Turno finalizado.
#### RF-TUR-008 — Controlar el tiempo de votación

Descripción

El sistema deberá controlar el tiempo disponible para que los jugadores emitan sus votos.

Entradas

- Identificador del turno.
- Tiempo máximo de votación.
- Estado del turno.
Proceso

1. El sistema inicia el contador de votación.

2. Controla el tiempo transcurrido.

3. Determina si todos los jugadores votaron o si finalizó el tiempo.

4. Continúa con la finalización de la votación.

Salidas

- Estado actualizado de la votación.
- Evento de finalización por tiempo.
Verificaciones

- El turno debe encontrarse en estado “En votación”.
- El tiempo debe estar correctamente configurado.
Excepciones

- Turno inexistente.
- Error de temporización.
- Votación ya finalizada.
#### RF-TUR-009 — Finalizar la votación

Descripción

El sistema deberá finalizar la etapa de votación cuando todos los jugadores hayan emitido su voto o cuando finalice el tiempo establecido.

Entradas

- Identificador del turno.
- Votos registrados.
- Estado de la votación.
Proceso

1. El sistema verifica las condiciones de finalización.

2. Cierra la recepción de nuevos votos.

3. Envía la información al módulo de puntuación.

4. Cambia el estado del turno a “Finalizado”.

Salidas

- Votación finalizada.
- Datos enviados para cálculo de puntuación.
Verificaciones

- El turno debe encontrarse en estado “En votación”.
- No debe permitir nuevos votos.
- Los datos recibidos deben ser válidos.
Excepciones

- Votación ya finalizada.
- Datos inconsistentes.
- Turno inexistente.
#### RF-TUR-010 — Publicar el resultado del turno

Descripción

El sistema deberá mostrar el resultado del turno una vez finalizada la votación, incluyendo el puntaje secreto, los votos recibidos y los puntos obtenidos por el autor.

Entradas

- Identificador del turno.
- Puntaje secreto.
- Votos registrados.
- Resultado del cálculo de puntuación.
Proceso

1. El sistema obtiene la información final del turno.

2. Envía el resultado a todos los jugadores.

3. Actualiza el estado del turno como “Finalizado”.

Salidas

- Puntaje secreto revelado.
- Votos emitidos.
- Puntos obtenidos.
- Estado final del turno.
Verificaciones

- La votación debe haber finalizado.
- El cálculo de puntuación debe estar disponible.
- El turno debe pertenecer a una partida en curso.
Excepciones

- Datos de resultado incompletos.
- Turno inexistente.
- Error de comunicación.
#### RF-TUR-011 — Seleccionar el siguiente jugador

Descripción

El sistema deberá determinar automáticamente el siguiente jugador que participará como autor del próximo turno según el orden establecido en la partida.

Entradas

- Identificador de partida.
- Orden de participación.
- Estado actual del turno.
Proceso

1. El sistema verifica la finalización del turno actual.

2. Consulta el orden de participación establecido.

3. Selecciona el siguiente jugador disponible.

4. Genera el nuevo turno.

Salidas

- Identificador del siguiente jugador.
- Nuevo turno creado.
- Notificación de cambio de turno.
Verificaciones

- El turno anterior debe haber finalizado.
- El jugador seleccionado debe pertenecer a la partida.
- Deben existir jugadores pendientes de participar.
Excepciones

- No existen jugadores disponibles.
- La partida finalizó.
- Orden de participación inválido.
## 4.6 Módulo de Puntuación

Responsabilidad

El módulo de puntuación será responsable de calcular y administrar los puntos obtenidos durante una partida en curso, aplicando las reglas definidas por el sistema. Será el encargado de determinar los puntos obtenidos por el autor de cada frase, actualizar el marcador temporal de los jugadores y proporcionar la información necesaria para mostrar los resultados durante el desarrollo de la partida.

#### RF-PUN-001 — Calcular puntos del turno

Descripción

El sistema deberá calcular automáticamente los puntos obtenidos por el autor de una frase al finalizar la etapa de votación, considerando la coincidencia entre el puntaje secreto asignado y los votos realizados por los demás jugadores.

Entradas

- Identificador del turno.
- Puntaje secreto asignado por el autor.
- Lista de votos registrados.
Proceso

1. El sistema recibe la información final del turno.

2. Obtiene el puntaje secreto definido por el autor.

3. Compara el puntaje secreto con cada voto recibido.

4. Cuenta la cantidad de jugadores que acertaron exactamente el valor.

5. Asigna al autor la cantidad de puntos correspondiente.

Salidas

- Cantidad de puntos obtenidos por el autor.
- Resultado del cálculo de puntuación.
Verificaciones

- El turno debe haber finalizado la etapa de votación.
- El puntaje secreto debe encontrarse disponible.
- Los votos deben encontrarse registrados correctamente.
Excepciones

- Turno inexistente.
- Información incompleta del turno.
- Votos inválidos.
- Error durante el cálculo.
#### RF-PUN-002 — Actualizar marcador de jugadores

Descripción

El sistema deberá actualizar el puntaje acumulado de los jugadores durante una partida en curso luego de finalizar cada turno.

Entradas

- Identificador de partida.
- Identificador del jugador autor.
- Puntos obtenidos durante el turno.
Proceso

1. El sistema recibe el resultado del cálculo del turno.

2. Identifica al jugador autor.

3. Suma los puntos obtenidos al marcador actual.

4. Actualiza el estado temporal de la partida.

Salidas

- Marcador actualizado de todos los jugadores.
- Puntaje acumulado disponible.
Verificaciones

- El jugador debe pertenecer a la partida.
- La partida debe encontrarse en curso.
- Los puntos deben ser valores válidos.
Excepciones

- Jugador inexistente.
- Partida finalizada.
- Error al actualizar el marcador.
#### RF-PUN-003 — Consultar marcador actual

Descripción

El sistema deberá permitir consultar el puntaje acumulado de todos los jugadores durante una partida en curso.

Entradas

- Identificador de partida.
Proceso

1. El sistema recibe la solicitud de consulta.

2. Obtiene la información temporal de puntuación.

3. Genera la información correspondiente para los jugadores.

Salidas

- Lista de jugadores.
- Puntaje acumulado de cada jugador.
Verificaciones

- La partida debe existir.
- Los jugadores deben pertenecer a la partida.
Excepciones

- Partida inexistente.
- Información de puntuación no disponible.
#### RF-PUN-004 — Generar resultado final de puntuación

Descripción

El sistema deberá proporcionar la información necesaria para determinar el resultado final de la partida considerando los puntajes acumulados obtenidos por los jugadores.

Entradas

- Identificador de partida.
- Puntajes acumulados.
Proceso

1. El sistema obtiene los puntajes finales.

2. Compara los valores obtenidos.

3. Identifica el mayor puntaje.

4. Determina ganador o empate.

Salidas

- Resultado final de la partida.
- Jugador ganador o empate.
Verificaciones

- La partida debe haber finalizado.
- Todos los jugadores deben poseer puntaje registrado.
Excepciones

- Datos incompletos.
- Partida inexistente.
- Puntajes inválidos.
## 4.7 Módulo de Comunicación en Tiempo Real

Responsabilidad

El módulo de comunicación en tiempo real será responsable de mantener sincronizados a los jugadores conectados mediante un canal de comunicación bidireccional entre clientes y servidor. Este módulo permitirá transmitir eventos relacionados con cambios de estado del sistema, incluyendo la creación y actualización de salas, el inicio y desarrollo de partidas, los cambios de turno, las etapas de votación, la actualización de puntuaciones y la finalización del juego. El servidor será responsable de controlar el flujo de comunicación y de notificar automáticamente a los clientes conectados cuando ocurra un evento relevante.

#### RF-COM-001 — Establecer conexión en tiempo real

Descripción

El sistema deberá permitir establecer una conexión persistente entre el cliente y el servidor para habilitar la comunicación en tiempo real durante la interacción del usuario con salas y partidas.

Entradas

- Identificador del usuario autenticado.
- Identificador de sala o partida cuando corresponda.
Proceso

1. El cliente solicita establecer una conexión con el servidor.

2. El sistema valida la identidad del usuario.

3. El sistema verifica que el usuario pueda establecer la conexión.

4. El servidor crea el canal de comunicación correspondiente.

5. El cliente queda conectado para recibir eventos.

Salidas

- Conexión establecida correctamente.
- Usuario asociado al canal de comunicación.
Verificaciones

- El usuario debe encontrarse autenticado.
- La conexión debe pertenecer a un usuario válido.
- La sala o partida asociada debe existir cuando corresponda.
Excepciones

- Usuario no autenticado.
- Error al establecer la conexión.
- Sala o partida inexistente.
#### RF-COM-002 — Gestionar conexión de jugadores

Descripción

El sistema deberá administrar el estado de conexión de los jugadores dentro de una sala o partida activa.

Entradas

- Usuario conectado.
- Estado de conexión del cliente.
Proceso

1. El sistema detecta la conexión o desconexión de un jugador.

2. Actualiza el estado de conexión asociado al usuario.

3. Notifica el evento correspondiente a los demás participantes.

4. Aplica las reglas definidas para desconexiones.

Salidas

- Estado actualizado de conexión.
- Notificación enviada a los jugadores.
Verificaciones

- El usuario debe pertenecer a la sala o partida correspondiente.
- El evento recibido debe ser válido.
Excepciones

- Usuario inexistente.
- Conexión inválida.
- Error durante la actualización del estado.
#### RF-COM-003 — Notificar creación de sala

Descripción

El sistema deberá notificar automáticamente a los jugadores conectados cuando una nueva sala sea creada.

Entradas

- Identificador de sala.
- Usuario creador.
- Modalidad seleccionada.
Proceso

1. El sistema detecta la creación de una nueva sala.

2. Genera el evento correspondiente.

3. Envía la información mediante el canal de comunicación en tiempo real.

Salidas

- Evento de sala creada enviado.
- Información actualizada de la sala.
Verificaciones

- La sala debe haber sido creada correctamente.
- El evento debe corresponder a una acción válida.
Excepciones

- Sala inexistente.
- Error de comunicación.
#### RF-COM-004 — Notificar cambios en sala

Descripción

El sistema deberá informar automáticamente a los jugadores conectados sobre modificaciones realizadas dentro de una sala antes del inicio de una partida.

Entradas

- Evento generado dentro de la sala.
- Información actualizada de la sala.
Proceso

1. El sistema detecta un cambio dentro de la sala.

2. Identifica los usuarios afectados.

3. Envía la actualización correspondiente.

Eventos contemplados

- Jugador ingresó a la sala.
- Jugador abandonó la sala.
- Modalidad modificada.
- Partida iniciada.
- Sala cancelada.
Salidas

- Información actualizada para todos los participantes.
Verificaciones

- Los jugadores deben pertenecer a la sala.
- La sala debe encontrarse activa.
Excepciones

- Sala inexistente.
- Error al enviar actualización.
#### RF-COM-005 — Notificar inicio de partida

Descripción

El sistema deberá notificar automáticamente a todos los jugadores conectados cuando una partida comience.

Entradas

- Identificador de partida.
- Lista de jugadores participantes.
Proceso

1. El sistema detecta el inicio de la partida.

2. Genera el evento de comienzo.

3. Envía la información a todos los jugadores conectados.

Salidas

- Evento de partida iniciada.
- Estado inicial del juego.
Verificaciones

- La partida debe encontrarse correctamente creada.
- Todos los jugadores deben pertenecer a la partida.
Excepciones

- Partida inexistente.
- Error de comunicación.
#### RF-COM-006 — Transmitir eventos del turno

Descripción

El sistema deberá comunicar automáticamente los cambios relacionados con el desarrollo de los turnos durante una partida.

Entradas

- Evento generado por el módulo de turnos.
- Identificador de partida.
Proceso

1. El módulo de turnos genera un cambio de estado.

2. El módulo de comunicación recibe el evento.

3. El sistema transmite la actualización a los jugadores.

Eventos contemplados

- Inicio de turno.
- Frase enviada a votación.
- Inicio de votación.
- Finalización de votación.
- Resultado del turno.
- Cambio al siguiente jugador.
Salidas

- Evento recibido por todos los clientes conectados.
Verificaciones

- La partida debe encontrarse en curso.
- El evento debe pertenecer a la partida correspondiente.
Excepciones

- Evento inválido.
- Partida finalizada.
- Error en la transmisión.
#### RF-COM-007 — Actualizar estado del juego

Descripción

El sistema deberá mantener sincronizado el estado actual de una partida entre todos los jugadores conectados.

Entradas

- Estado actual de la partida.
- Evento generado por el servidor.
Proceso

1. El servidor actualiza el estado interno del juego.

2. Genera la información correspondiente.

3. Envía la actualización a todos los clientes conectados.

Salidas

- Estado actualizado del juego visible para los jugadores.
Verificaciones

- El estado recibido debe ser válido.
- La partida debe existir.
Excepciones

- Estado inconsistente.
- Error de sincronización.
#### RF-COM-008 — Notificar actualización de puntuación

Descripción

El sistema deberá informar automáticamente a todos los jugadores cuando se actualice el marcador durante una partida.

Entradas

- Nuevo puntaje de los jugadores.
- Identificador de partida.
Proceso

1. El módulo de puntuación genera la actualización.

2. El módulo de comunicación recibe el resultado.

3. El sistema envía el nuevo marcador a los participantes.

Salidas

- Marcador actualizado visible para todos los jugadores.
Verificaciones

- Los puntajes deben haber sido calculados correctamente.
- La partida debe encontrarse en curso.
Excepciones

- Datos de puntuación inválidos.
- Error de comunicación.
#### RF-COM-009 — Notificar finalización de partida

Descripción

El sistema deberá comunicar automáticamente la finalización de una partida y el resultado obtenido por los jugadores.

Entradas

- Resultado final de la partida.
- Identificador de partida.
Proceso

1. El sistema detecta la finalización del juego.

2. Obtiene la información final.

3. Envía el evento de finalización a los jugadores conectados.

Salidas

- Resultado final mostrado a los participantes.
- Confirmación de partida finalizada.
Verificaciones

- La partida debe encontrarse finalizada.
- El resultado debe estar calculado.
Excepciones

- Resultado incompleto.
- Partida inexistente.
- Error de comunicación.
#### RF-COM-010 — Gestionar desconexión definitiva de jugadores

Descripción

El sistema deberá gestionar la desconexión de un jugador durante una partida aplicando las reglas establecidas para abandono del juego.

Entradas

- Identificador del jugador.
- Identificador de partida.
- Evento de desconexión.
Proceso

1. El sistema detecta la pérdida de conexión.

2. Actualiza el estado del jugador.

3. Notifica la desconexión al resto de participantes.

4. Aplica la regla correspondiente según el estado de la partida.

Salidas

- Jugador marcado como desconectado.
- Estado actualizado de la partida.
Verificaciones

- El jugador debe pertenecer a la partida.
- La desconexión debe corresponder a una conexión activa.
Excepciones

- Jugador inexistente.
- Partida inexistente.
- Error al actualizar estado.
## 4.8 Módulo de Persistencia

Responsabilidad

El módulo de persistencia será responsable de administrar el almacenamiento y recuperación de la información permanente necesaria para el funcionamiento del sistema. Su función principal será gestionar la información de los usuarios registrados y los datos necesarios para la operación actual del juego, manteniendo una estructura preparada para futuras extensiones como estadísticas o funcionalidades sociales.

#### RF-PER-001 — Registrar información de usuario

Descripción

El sistema deberá permitir almacenar la información correspondiente a los usuarios registrados dentro de la aplicación.

Entradas

- Nombre de usuario.
- Correo electrónico.
- Contraseña almacenada mediante hash.
- Imagen de perfil predeterminada.
- Fecha de creación.
Proceso

1. El sistema recibe la información validada del usuario.

2. Genera el registro correspondiente.

3. Almacena la información en la base de datos.

4. Confirma la creación del registro.

Salidas

- Usuario almacenado correctamente.
- Identificador generado para el usuario.
Verificaciones

- Los datos obligatorios deben encontrarse completos.
- El usuario no debe existir previamente.
- La información debe cumplir las restricciones definidas.
Excepciones

- Usuario duplicado.
- Error de almacenamiento.
- Datos inválidos.
#### RF-PER-002 — Consultar información persistente

Descripción

El sistema deberá permitir recuperar información almacenada necesaria para la operación de los distintos módulos.

Entradas

- Identificador de usuario.
- Parámetros de consulta requeridos.
Proceso

1. El sistema recibe una solicitud de información.

2. Consulta los registros almacenados.

3. Recupera la información correspondiente.

4. Devuelve los datos solicitados.

Salidas

- Información recuperada correctamente.
Verificaciones

- El registro solicitado debe existir.
- El usuario debe tener permisos para acceder a la información.
Excepciones

- Registro inexistente.
- Error de conexión con la base de datos.
- Error durante la consulta.
#### RF-PER-003 — Actualizar información persistente

Descripción

El sistema deberá permitir modificar información almacenada cuando un usuario actualice datos correspondientes a su cuenta.

Entradas

- Identificador del usuario.
- Nuevos datos modificados.
Proceso

1. El sistema recibe la solicitud de actualización.

2. Valida los nuevos datos.

3. Actualiza la información correspondiente.

4. Guarda los cambios realizados.

Salidas

- Información actualizada correctamente.
Verificaciones

- El usuario debe existir.
- Los datos modificados deben cumplir las reglas establecidas.
Excepciones

- Usuario inexistente.
- Datos inválidos.
- Error durante la actualización.
#### RF-PER-004 — Administrar eliminación de información temporal

Descripción

El sistema deberá eliminar automáticamente la información temporal asociada a salas y partidas una vez finalizado su ciclo de vida.

Entradas

- Identificador de sala.
- Identificador de partida.
- Evento de finalización.
Proceso

1. El sistema detecta la finalización de una partida.

2. Identifica la información temporal asociada.

3. Elimina los registros correspondientes.

4. Libera los recursos utilizados.

Salidas

- Sala y partida eliminadas correctamente.
- Recursos disponibles nuevamente.
Verificaciones

- La partida debe haber finalizado.
- La información no debe encontrarse en uso.
Excepciones

- Información inexistente.
- Error durante la eliminación.
- Fallo en la conexión con la base de datos.
#### RF-PER-005 — Almacenar frases utilizadas

Descripción

El sistema deberá permitir almacenar las frases utilizadas durante las partidas para permitir futuras funcionalidades relacionadas con estadísticas o análisis del uso del contenido.

Entradas

- Frase utilizada.
- Modalidad asociada.
- Información relacionada con su utilización.
Proceso

1. El sistema recibe la frase utilizada durante un turno.

2. Verifica que la información sea válida.

3. Almacena la frase en la base de datos.

4. Mantiene la información disponible para futuras extensiones.

Salidas

- Frase almacenada correctamente.
Verificaciones

- La frase debe cumplir las restricciones definidas.
- La información asociada debe ser válida.
Excepciones

- Frase inválida.
- Error de almacenamiento.
- Información incompleta.
# 5. Especificación de Requisitos No Funcionales

Los requisitos no funcionales establecen las restricciones de calidad, rendimiento, seguridad y características generales que deberá cumplir el sistema “Es un 10 pero…”, independientemente de las funcionalidades específicas implementadas.

Estos requisitos están basados en la clasificación propuesta por Sommerville, agrupando las restricciones según su naturaleza.

## 5.1 Requisitos de Producto

Los requisitos de producto definen características relacionadas con la calidad interna y externa del sistema, incluyendo eficiencia, seguridad, fiabilidad, usabilidad, mantenibilidad y portabilidad.

### 5.1.1 Eficiencia

Los requisitos de eficiencia establecen las condiciones relacionadas con el rendimiento del sistema y el uso adecuado de los recursos disponibles.

#### RNF-EFI-001 — Tiempo de respuesta de la API

Descripción

El sistema deberá responder las solicitudes realizadas mediante la API REST dentro de tiempos adecuados para garantizar una interacción fluida con los clientes consumidores.

Criterio verificable

Las operaciones de consulta y modificación de información deberán responder en un tiempo máximo de 2 segundos bajo condiciones normales de operación.

#### RNF-EFI-002 — Actualización de eventos en tiempo real

Descripción

El sistema deberá transmitir los eventos generados durante una sala o partida mediante el canal de comunicación en tiempo real.

Criterio verificable

Los eventos enviados mediante WebSocket deberán ser recibidos por los clientes conectados sin requerir solicitudes periódicas adicionales.

#### RNF-EFI-003 — Manejo de múltiples partidas simultáneas

Descripción

El sistema deberá permitir la ejecución independiente de múltiples partidas activas al mismo tiempo.

Criterio verificable

Cada partida deberá mantener su propio estado de juego sin afectar la información perteneciente a otras partidas activas.

### 5.1.2 Seguridad

Los requisitos de seguridad establecen las medidas necesarias para proteger la información del usuario y restringir accesos no autorizados.

#### RNF-SEG-001 — Protección de contraseñas

Descripción

El sistema deberá almacenar las contraseñas de los usuarios utilizando mecanismos criptográficos seguros.

Criterio verificable

Las contraseñas almacenadas en la base de datos deberán encontrarse protegidas mediante un algoritmo de hash seguro y no deberán almacenarse en texto plano.

#### RNF-SEG-002 — Autenticación de usuarios

Descripción

El sistema deberá verificar la identidad de los usuarios antes de permitir acceso a funcionalidades protegidas.

Criterio verificable

Todas las operaciones que requieran autenticación deberán validar la existencia de un token de acceso válido antes de ejecutarse.

#### RNF-SEG-003 — Validación de información recibida

Descripción

El sistema deberá validar todos los datos recibidos desde clientes externos antes de procesarlos.

Criterio verificable

Toda información ingresada por usuarios deberá ser validada antes de almacenarse o utilizarse dentro de la lógica del sistema.

#### RNF-SEG-004 — Protección de información sensible

Descripción

El sistema deberá evitar la exposición de información sensible durante la comunicación entre componentes.

Criterio verificable

Las comunicaciones entre cliente y servidor deberán utilizar canales cifrados cuando se transmitan datos sensibles.

### 5.1.3 Fiabilidad

Los requisitos de fiabilidad establecen las condiciones necesarias para mantener un funcionamiento correcto del sistema.

#### RNF-FIA-001 — Manejo controlado de errores

Descripción

El sistema deberá controlar los errores producidos durante la ejecución evitando interrupciones inesperadas.

Criterio verificable

Los errores generados por la aplicación deberán devolver respuestas controladas con información suficiente para identificar el problema ocurrido.

#### RNF-FIA-002 — Consistencia del estado del juego

Descripción

El sistema deberá garantizar la consistencia del estado de salas y partidas durante toda la ejecución.

Criterio verificable

Las modificaciones del estado del juego deberán realizarse únicamente mediante la lógica del servidor.

#### RNF-FIA-003 — Integridad de información persistente

Descripción

El sistema deberá garantizar que la información almacenada mantenga consistencia durante las operaciones realizadas.

Criterio verificable

Las operaciones sobre la base de datos deberán ejecutarse utilizando mecanismos que eviten registros incompletos o inconsistentes.

### 5.1.4 Usabilidad

Los requisitos de usabilidad establecen condiciones relacionadas con la facilidad de interacción del usuario con el sistema.

#### RNF-USA-001 — Retroalimentación de operaciones

Descripción

El sistema deberá informar al usuario el resultado de las operaciones realizadas.

Criterio verificable

Cada operación ejecutada por un usuario deberá generar una respuesta indicando si fue realizada correctamente o si ocurrió un error.

#### RNF-USA-002 — Claridad del estado de juego

Descripción

El sistema deberá proporcionar información clara sobre el estado actual de una sala o partida.

Criterio verificable

Los jugadores deberán poder identificar el estado actual de la partida, el jugador activo y las acciones disponibles mediante la información proporcionada por el sistema.

### 5.1.5 Mantenibilidad

Los requisitos de mantenibilidad establecen condiciones que facilitan la evolución y modificación del sistema.

#### RNF-MAN-001 — Separación de responsabilidades

Descripción

El sistema deberá mantener una arquitectura modular donde cada componente posea responsabilidades claramente definidas.

Criterio verificable

Los módulos definidos en la arquitectura deberán encontrarse separados y no deberán contener lógica perteneciente a otros módulos.

#### RNF-MAN-002 — Bajo acoplamiento entre componentes

Descripción

El sistema deberá reducir la dependencia directa entre los distintos componentes internos.

Criterio verificable

Los cambios realizados sobre un módulo no deberán requerir modificaciones innecesarias en módulos independientes.

#### RNF-MAN-003 — Pruebas automatizadas

Descripción

El sistema deberá contar con pruebas automatizadas para validar el comportamiento de sus componentes principales.

Criterio verificable

Los módulos críticos deberán disponer de pruebas automatizadas que validen sus escenarios principales de funcionamiento.

### 5.1.6 Portabilidad

Los requisitos de portabilidad establecen las condiciones necesarias para facilitar la ejecución del sistema en distintos entornos.

#### RNF-POR-001 — Ejecución mediante Docker

Descripción

El sistema deberá permitir su ejecución mediante contenedores Docker.

Criterio verificable

La aplicación deberá poder iniciarse en un entorno nuevo utilizando la configuración Docker definida en el proyecto.

#### RNF-POR-002 — Configuración mediante variables de entorno

Descripción

El sistema deberá permitir configurar parámetros sensibles y dependencias externas mediante variables de entorno.

Criterio verificable

Los datos de configuración sensibles no deberán encontrarse escritos directamente dentro del código fuente.

## 5.2 Requisitos Organizacionales

Los requisitos organizacionales establecen restricciones relacionadas con estándares y procesos utilizados durante el desarrollo.

### 5.2.1 Estándares

#### RNF-EST-001 — Documentación de API

Descripción

El sistema deberá contar con documentación de los servicios expuestos mediante la API.

Criterio verificable

Todos los endpoints públicos deberán encontrarse documentados mediante una especificación OpenAPI.

#### RNF-EST-002 — Control de versiones

Descripción

El código fuente deberá mantenerse utilizando un sistema de control de versiones.

Criterio verificable

El proyecto deberá encontrarse almacenado en un repositorio Git con historial de cambios.

### 5.2.2 Implementación

#### RNF-IMP-001 — Arquitectura basada en servicios

Descripción

El sistema deberá implementarse utilizando una arquitectura que permita separar la lógica de negocio, la persistencia y la comunicación.

Criterio verificable

La aplicación deberá encontrarse organizada en capas o módulos independientes según la responsabilidad asignada.

## 5.3 Requisitos Externos

Los requisitos externos establecen restricciones relacionadas con la comunicación e integración del sistema con otros componentes.

### 5.3.1 Interoperabilidad

#### RNF-INT-001 — Comunicación mediante JSON

Descripción

El sistema deberá utilizar JSON como formato estándar para el intercambio de información entre componentes.

Criterio verificable

Todas las comunicaciones realizadas mediante la API deberán utilizar estructuras JSON definidas previamente.

#### RNF-INT-002 — Uso de protocolos estándar

Descripción

El sistema deberá utilizar protocolos de comunicación ampliamente utilizados.

Criterio verificable

La comunicación REST deberá utilizar HTTP y la comunicación en tiempo real deberá utilizar WebSocket.

### 5.3.2 Protección de datos

#### RNF-DAT-001 — Minimización de información almacenada

Descripción

El sistema deberá almacenar únicamente información necesaria para el funcionamiento actual de la aplicación.

Criterio verificable

La base de datos deberá contener únicamente atributos definidos en el modelo de datos aprobado.

#### RNF-DAT-002 — Eliminación de información temporal

Descripción

El sistema deberá eliminar automáticamente información temporal generada durante la ejecución de partidas.

Criterio verificable

Las salas y partidas deberán eliminarse automáticamente una vez finalizado su ciclo de vida.

# 6. Información de Apoyo

Esta sección reúne la información complementaria que da soporte a la comprensión del presente documento. El detalle correspondiente se encuentra desarrollado en el Apéndice A – Glosario de Términos y Acrónimos, donde se listan las definiciones de los términos técnicos y de dominio, así como los acrónimos utilizados a lo largo de la especificación (RF, RN, RNF, entre otros).

# Apéndice A – Glosario de Términos y Acrónimos

A continuación, se presenta el glosario de términos técnicos, de dominio y acrónimos utilizados a lo largo del presente documento, ordenados alfabéticamente.

| Término | Definición |
| --- | --- |
| API | Conjunto de definiciones y protocolos que permite la comunicación entre distintos componentes de software. |
| API REST | Estilo arquitectónico para el diseño de servicios web basado en el protocolo HTTP y en operaciones sobre recursos. |
| Backend | Componente del sistema responsable de la lógica de negocio, la persistencia de datos y la exposición de servicios hacia los clientes. |
| Cliente | Aplicación web, móvil o de escritorio que consume los servicios expuestos por la API del sistema. |
| Docker | Plataforma de contenedores utilizada para empaquetar y desplegar la aplicación de forma portable. |
| FastAPI | Framework de Python utilizado para el desarrollo del backend y la exposición de la API REST. |
| Hash | Función criptográfica utilizada para almacenar contraseñas de forma segura, sin conservar el valor original. |
| HTTP | Protocolo de comunicación utilizado para las solicitudes realizadas a la API REST. |
| Imagen de perfil | Representación visual predeterminada asociada a la cuenta de un usuario, generada automáticamente por el sistema a partir de la inicial de su nombre de usuario. |
| JSON | Formato estándar (JavaScript Object Notation) utilizado para el intercambio de información entre los distintos componentes del sistema. |
| Modalidad de juego | Configuración predefinida que determina el tipo de frase a completar durante una partida. |
| Partida | Instancia de juego iniciada a partir de una sala, compuesta por una ronda de turnos entre los jugadores participantes. |
| Puntaje secreto | Valor numérico entero, comprendido entre 1 y 10, asignado por el autor de una frase y utilizado como referencia para el cálculo de puntos. |
| PostgreSQL | Sistema gestor de bases de datos relacional utilizado para la persistencia de la información del sistema. |
| RF | Prefijo utilizado para identificar un Requisito Funcional dentro del presente documento (por ejemplo, RF-USR-001). |
| RN | Prefijo utilizado para identificar una Regla de Negocio dentro del presente documento (por ejemplo, RN-001). |
| RNF | Prefijo utilizado para identificar un Requisito No Funcional dentro del presente documento (por ejemplo, RNF-SEG-001). |
| Ronda | Ciclo completo de una partida, compuesto por un turno de cada jugador participante. |
| Sala | Espacio virtual privado, identificado mediante un código único, en el cual los jugadores se reúnen antes del inicio de una partida. |
| SRS | Sigla de Software Requirements Specification: Documento de Especificación de Requisitos de Software. |
| Token | Credencial generada por el sistema tras un inicio de sesión exitoso, utilizada para autenticar las solicitudes posteriores del usuario. |
| Turno | Paso individual dentro de una ronda, correspondiente a un jugador que actúa como autor de una frase, mientras el resto de los jugadores activos actúa como votante. |
| Voto | Valor numérico entero, comprendido entre 1 y 10, emitido por un jugador para intentar acertar el puntaje secreto asignado por el autor de la frase. |
| WebSocket | Protocolo de comunicación bidireccional utilizado para la transmisión de eventos en tiempo real entre el servidor y los clientes conectados. |
