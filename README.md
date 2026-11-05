# TP Veterinaria

Trabajo Práctico Integrador 2026 — Desarrollo de Aplicaciones con Objetos.
Sistema para una red de clínicas veterinarias y derivación de muestras a un laboratorio central.

## Estado actual

El MVP está funcionalmente completo para el alcance del TP:

- Dominio clínico, vacunación, laboratorio y transporte implementados en Python.
- State para el ciclo de vida de `MuestraBiologica` y Strategy para cuatro reportes.
- Persistencia P1–P9 terminada: SQLite mediante `sqlite3`, 19 DAO, conexión
  compartida, SQL parametrizado y transacciones controladas por el llamador.
- Integración completa con cierre y reapertura real de SQLite, tanto con precinto
  intacto como roto, y reportes sobre datos recuperados.
- Capa de servicios (`servicios/`) y aplicación de escritorio con Flet (`interfaz/`) de
  cinco secciones, con datos de demostración y exportación de reportes a PDF y CSV. Ver
  [Interfaz gráfica y capa de servicios](#interfaz-gráfica-y-capa-de-servicios).

El total final de casos verificados figura en [Pruebas](#pruebas). El estado de los
diagramas derivados se detalla en [Documentación](#documentación).

## Estructura del proyecto

```text
Veterinaria/
├── src/veterinaria/
│   ├── dominio/
│   │   ├── clinica/
│   │   ├── vacunacion/
│   │   ├── laboratorio/
│   │   └── transporte/
│   ├── patrones/
│   │   ├── state/
│   │   └── strategy/
│   ├── persistencia/
│   ├── servicios/
│   ├── interfaz/
│   └── main.py
├── tests/
│   ├── persistencia/
│   ├── servicios/
│   └── interfaz/
├── docs/
│   ├── der/
│   ├── enunciado/
│   └── uml/
├── requirements.txt
└── pytest.ini
```

| Carpeta | Contenido |
|---|---|
| `dominio/clinica/` | Clientes, mascotas, historias, atenciones, comprobantes, veterinarios, agenda y turnos. |
| `dominio/vacunacion/` | Vacunas y aplicaciones. |
| `dominio/laboratorio/` | Órdenes, muestras, historial y resultados. |
| `dominio/transporte/` | Conservadoras, precintos, remitos, envíos y recepciones. |
| `patrones/state/` | Estados y transiciones de `MuestraBiologica`. |
| `patrones/strategy/` | Generador y estrategias de los cuatro reportes. |
| `persistencia/` | Conexión SQLite, inicialización del esquema y DAO. |
| `servicios/` | Casos de uso: transacciones, IDs, acciones en un paso, reportes, exportación PDF/CSV y datos de demostración. |
| `interfaz/` | Aplicación Flet: ventana principal y cinco secciones con pestañas. |
| `main.py` | Punto de entrada de la aplicación de escritorio. |
| `tests/` | Pruebas de dominio y reportes; `tests/persistencia/` incluye DAO e integración. |
| `docs/` | DER, UML y enunciado del TP. |

Las carpetas `dominio/`, `patrones/` y `persistencia/` pertenecen a
`src/veterinaria/`. Las secciones siguientes describen las reglas y decisiones de
cada módulo sin requerir navegar todos los archivos.

## Preparación y ejecución

El entorno verificado utiliza **Python 3.12.3 y pytest 9.1.1**. Para reproducirlo,
usar Python 3.12 y ejecutar desde la raíz del repositorio:

1. Clonar el proyecto y entrar en su carpeta:

   ```console
   git clone https://github.com/juansarey/Veterinaria.git
   cd Veterinaria
   ```

2. Crear un entorno virtual:

   ```console
   python -m venv .venv
   ```

   Activarlo en PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   En `cmd.exe`, usar `.venv\Scripts\activate.bat`. También se puede trabajar sin
   activar el entorno, reemplazando `python` por `.\.venv\Scripts\python.exe` en
   los comandos siguientes.

3. Instalar las dependencias de pruebas:

   ```console
   python -m pip install -r requirements.txt
   ```

   `requirements.txt` contiene `pytest`, `flet[all]` (interfaz), `reportlab` (PDF) y `matplotlib` (gráficos) sin
   fijar versiones; la interfaz se verificó con Flet 1.0.5 y ReportLab 4.4. El dominio y
   la persistencia usan la biblioteca estándar de Python, incluido `sqlite3`; no
   necesitan instalar un servidor de base de datos.

4. Ejecutar la suite completa:

   ```console
   python -m pytest -p no:cacheprovider
   ```

   Con el entorno activado también puede usarse `pytest -p no:cacheprovider`.
   `pytest.ini` agrega `src` a la ruta de imports. Las pruebas crean bases aisladas
   en memoria o archivos temporales, sin requerir una base preparada manualmente.

## Recorrido de implementación

Los siguientes incrementos ya están implementados; se conservan como historial
de las decisiones que dieron lugar al modelo actual.
Los incrementos P1 a P8 incorporan
almacenamiento para `Cliente`, `Mascota`, `Clinica`, `Veterinario`,
`AgendaMedica`, `Turno`, `HistoriaClinica`, `Atencion`, `Vacuna`,
`AplicacionVacuna`, `OrdenDerivacionLaboratorio`, `MuestraBiologica`,
`HistorialEstadoMuestra`, `ConservadoraIsotermica`, `PrecintoSanitario` y
`RemitoBiologico`, `Envio`, `Recepcion`, `ResultadoAnalisis` y
`ComprobanteAtencion`. El historial de estados se persiste como parte interna de
`MuestraBiologicaDAO`. P9 integra los cuatro reportes con datos persistidos y
verifica el circuito completo cerrando y reabriendo la conexión:

- Primer incremento: `Clinica`, `Veterinario`, `AgendaMedica` y `Turno`.
- Segundo incremento: `Cliente`, `Mascota`, `HistoriaClinica`, `Atencion`,
  `TipoAtencion` y la asociación de cada `Turno` con una `Mascota`.
- Tercer incremento: `Vacuna`, `AplicacionVacuna`, registro de aplicaciones en
  `Mascota` y validación de vacunas obligatorias al registrar una atención.
- Cuarto incremento: `OrdenDerivacionLaboratorio`, `EstadoOrden`,
  `MuestraBiologica`, `HistorialEstadoMuestra` y patrón State para el ciclo de
  vida de las muestras.
- Quinto incremento: `ConservadoraIsotermica`, `EstadoConservadora`,
  `PrecintoSanitario`, `EstadoPrecinto`, `RemitoBiologico`, `EstadoRemito`,
  empaquetado de muestras mediante el remito y consulta de sus condiciones de
  despacho.
- Sexto incremento: `Envio`, `EstadoEnvio`, `Recepcion`, despacho y recepción del
  remito, registro de llegada, verificación del precinto y transición de las muestras
  a `EN_TRANSITO`, `RECIBIDA` o `RECHAZADA`.
- Séptimo incremento: `ResultadoAnalisis`, relación unidireccional con
  `MuestraBiologica`, registro de resultados y transición de muestras recibidas a
  `ANALIZADA`.
- Octavo incremento: `ComprobanteAtencion`, emisión mediante construcción y relación
  unidireccional con `Atencion`.
- Noveno incremento: patrón Strategy mediante `EstrategiaReporte` y
  `GeneradorReportes`, con cuatro estrategias concretas para generar reportes de
  atenciones y derivaciones, muestras rechazadas, vacunas pendientes y tiempos
  promedio de tránsito y procesamiento.

La persistencia utiliza SQLite mediante `sqlite3` y el patrón DAO. Incluye una
conexión compartida con claves foráneas activas, SQL parametrizado y control
externo de las transacciones. Persistencia 1 cubre `Cliente` y `Mascota`;
Persistencia 2 agrega `Clinica`, `Veterinario`, `AgendaMedica` y `Turno`, y
Persistencia 3 incorpora `HistoriaClinica` y `Atencion`; Persistencia 4 agrega
`Vacuna` y `AplicacionVacuna`; Persistencia 5 incorpora
`OrdenDerivacionLaboratorio`, `MuestraBiologica` y su historial de estados; y
Persistencia 6 agrega `ConservadoraIsotermica`, `PrecintoSanitario` y
`RemitoBiologico`; Persistencia 7 agrega `Envio` y `Recepcion`; y Persistencia 8
incorpora `ResultadoAnalisis` y `ComprobanteAtencion`. El total verificado de tests
se informa en la sección Pruebas. Persistencia 9 completa las cargas opcionales
para reportes, protege el responsable de la mascota y prueba ambos caminos de
recepción en un archivo SQLite temporal con conexiones independientes.

Los procesos obligatorios principales del enunciado ya cubren clientes, mascotas e
historias clínicas, atenciones, órdenes de laboratorio, empaquetado, envío, recepción,
rechazo por precinto roto, resultados de análisis y comprobantes de atención.
También están implementados los dos patrones de diseño obligatorios, State y
Strategy, y cuatro reportes no triviales. State y Strategy operan sobre objetos
del dominio; sus algoritmos no necesitan tablas propias.

## Agenda y turnos

- `Clinica` mantiene varios veterinarios. `agregar_veterinario()` devuelve `True`
  cuando agrega una instancia y `False` si esa misma instancia ya estaba registrada.
- Cada veterinario tiene una única agenda semanal, asignada con `asignar_agenda()`.
  Puede crearse sin agenda, pero no registrar turnos hasta asignarle una.
- `AgendaMedica(dias_trabajo, hora_desde, hora_hasta)` selecciona los días laborales
  mediante `DiaSemana`. Un mismo horario se aplica a todos los días seleccionados;
  `hora_hasta` debe ser posterior a `hora_desde`.
- Un turno debe terminar después de comenzar, empezar y terminar en la misma fecha,
  corresponder a un día laboral y quedar completamente dentro del horario, incluidos sus límites.
- Cada veterinario mantiene varios turnos. No pueden superponerse turnos activos
  (para este control, todos los estados excepto `CANCELADO`).
  Los turnos consecutivos son válidos y los cancelados no bloquean el horario.
- La superposición se controla entre turnos, no entre agendas.

Por ejemplo, una agenda con lunes, martes, jueves y viernes de 08:00 a 13:00
permite un turno el lunes de 09:00 a 09:30, pero no el miércoles en ese horario.
Las relaciones almacenadas son unidireccionales: `Clinica -> Veterinario`,
`Veterinario -> AgendaMedica` y `Veterinario -> Turno`.

## Clientes, mascotas e historia clínica

- Toda `Mascota` tiene obligatoriamente un `Cliente` responsable. El constructor
  rechaza `None` y guarda `_responsable`; la propiedad pública `responsable` no
  tiene setter. Intentar asignarle `None` u otro cliente produce `AttributeError`,
  por lo que la API pública conserva el responsable durante la vida del objeto.
- Una mascota puede tener una única `HistoriaClinica`. La primera asignación se
  conserva y no puede reemplazarse con una segunda.
- `HistoriaClinica` almacena sus `Atencion` y evita registrar dos veces la misma
  instancia.
- Cada `Atencion` indica su `TipoAtencion` e identifica al `Veterinario` que la
  realizó.
- `ComprobanteAtencion` conserva una referencia unidireccional a la `Atencion` y una
  fecha de emisión explícita. Su construcción representa la emisión del comprobante;
  no existe un método `emitir()` ni una referencia inversa desde `Atencion`.
- La relación conceptual admite como máximo un comprobante persistido por atención
  porque el DER declara `id_atencion` como único. Esa unicidad global todavía no se
  controla en memoria.
- Cada `Turno` corresponde obligatoriamente a una `Mascota`.

Las relaciones del modelo de objetos son unidireccionales:
`Mascota -> Cliente`, `Mascota -> HistoriaClinica`,
`HistoriaClinica -> Atencion`, `Atencion -> Veterinario` y `Turno -> Mascota`.
No se almacenan referencias inversas.

## Persistencia 1: clientes y mascotas

La persistencia sigue la separación:

```text
Dominio
   ↓ utilizado por
DAO
   ↓
sqlite3
   ↓
SQLite
```

Las entidades no conocen SQLite, conexiones ni DAO, y no contienen SQL. Los DAO
conocen las entidades que persisten y reciben una `sqlite3.Connection` ya abierta.
La conexión se crea a partir de una ruta, admite `:memory:`, activa
`PRAGMA foreign_keys = ON` y configura `sqlite3.Row` para acceder a las columnas
por nombre. No existen conexiones globales.

`ClienteDAO` y `MascotaDAO` implementan exactamente estas operaciones:

- `crear()`;
- `obtener_por_id()`;
- `listar()`;
- `actualizar()`;
- `eliminar()`.

Todos los datos variables se envían mediante parámetros `?`. Los DAO conservan los
IDs explícitos de los objetos y no asignan identificadores mediante `lastrowid`.
Cada `crear()` exige el ID de la entidad y rechaza `None` con `ValueError` antes de
ejecutar SQL. SQLite conserva `AUTOINCREMENT` como mecanismo técnico de sus tablas;
el DAO no lo utiliza para generar IDs del dominio. La excepción es `id_agenda`,
un identificador técnico generado por SQLite que no pertenece a `AgendaMedica`.
Tampoco ejecutan `commit`: el código que coordina una operación decide si confirma
con `conexion.commit()` o revierte con `conexion.rollback()`, por lo que ambos DAO
pueden participar en una misma transacción.

La relación se persiste mediante la clave foránea
`mascota.id_cliente -> cliente.id_cliente`, obtenida de
`mascota.responsable.id_cliente`. Al recuperar una mascota, `MascotaDAO` utiliza
`ClienteDAO` para reconstruir su responsable. El sentido del modelo de objetos se
mantiene como `Mascota -> Cliente`; no se agrega una colección de mascotas en
`Cliente`.

`fecha_nacimiento` se guarda como texto ISO mediante `date.isoformat()` y se
recupera explícitamente con `date.fromisoformat()`. Los valores opcionales se
conservan como `NULL` cuando corresponde. Las restricciones de PK, `UNIQUE`, FK y
`NOT NULL` provienen del DER. Los DAO dejan que `sqlite3.IntegrityError` se propague
ante una violación y no convierten esos errores en un resultado `False`.

Los archivos incorporados son:

```text
src/veterinaria/persistencia/
    conexion.py
    inicializar_bd.py
    cliente_dao.py
    mascota_dao.py

tests/persistencia/
    conftest.py
    test_conexion.py
    test_inicializar_bd.py
    test_cliente_dao.py
    test_mascota_dao.py
```

Persistencia 1 incorporó las tablas `cliente` y `mascota` mediante
`CREATE TABLE IF NOT EXISTS`. Los tests de persistencia utilizan bases aisladas,
principalmente `:memory:`, y no comparten una base real entre ejecuciones.

## Persistencia 2: clínica, profesionales, agenda y turnos

Persistencia 2 continúa con la misma arquitectura: SQLite mediante `sqlite3`,
DAO que reciben una conexión compartida, SQL parametrizado, claves foráneas
activas, IDs explícitos para las entidades y transacciones controladas por el
código que coordina la operación. La inicialización agrega las tablas `clinica`,
`veterinario`, `agenda_medica`, `agenda_medica_dia` y `turno`.

Los DAO implementan estas operaciones:

- `ClinicaDAO`: `crear()`, `obtener_por_id()`, `listar()`, `actualizar()` y
  `eliminar()`. Recupera solamente los datos propios de la clínica y no carga sus
  veterinarios.
- `VeterinarioDAO`: `crear(veterinario, id_clinica)`, `obtener_por_id()`,
  `listar()`, `listar_por_clinica()`, `actualizar(veterinario, id_clinica)` y
  `eliminar()`. `id_clinica` es contexto de persistencia; el objeto recuperado no
  incorpora una referencia a `Clinica`, una agenda ni turnos.
- `AgendaMedicaDAO`: `crear(agenda, id_veterinario)`,
  `obtener_por_veterinario()`, `actualizar(agenda, id_veterinario)` y
  `eliminar_por_veterinario()`. Administra conjuntamente `agenda_medica` y
  `agenda_medica_dia`; no existe un DAO separado para los días.
- `TurnoDAO`: `crear(turno, id_veterinario)`, `obtener_por_id()`, `listar()`,
  `listar_por_veterinario()`, `actualizar(turno, id_veterinario)` y `eliminar()`.
  Obtiene `id_mascota` desde `turno.mascota` y utiliza `MascotaDAO` al reconstruir
  esa asociación. `id_veterinario` permanece como contexto de persistencia y no se
  agrega una referencia desde `Turno` hacia `Veterinario`.

Las relaciones del modelo de objetos continúan siendo unidireccionales:
`Clinica -> Veterinario`, `Veterinario -> AgendaMedica`,
`Veterinario -> Turno`, `Turno -> Mascota` y `Mascota -> Cliente`. La carga de un
objeto por su DAO no reconstruye automáticamente las colecciones o referencias
que pertenecen a otro agregado. No se incorporan las relaciones inversas
`Veterinario -> Clinica`, `AgendaMedica -> Veterinario`,
`Turno -> Veterinario` ni `Mascota -> Turno`.

Las claves foráneas del modelo relacional se resuelven mediante los IDs de las
entidades y los parámetros que reciben los DAO; no representan nuevas relaciones
en el modelo de objetos.

`agenda_medica.id_agenda` es un identificador técnico generado por SQLite y se usa
internamente mediante `lastrowid` para asociar los días. No forma parte de
`AgendaMedica`, cuyas instancias se consultan por `id_veterinario`. Los valores de
`DiaSemana` se guardan mediante `dia.name`, por ejemplo `LUNES`, `MARTES` o
`MIERCOLES`, y se reconstruyen mediante `DiaSemana[nombre]`; no se persisten sus
valores numéricos de 0 a 6.

Los valores `time` y `datetime` se guardan como texto ISO y se recuperan con
`fromisoformat()`, conservando segundos y microsegundos. El estado del turno se
persiste mediante el nombre de `EstadoTurno`: `PENDIENTE`, `CONFIRMADO`, `ATENDIDO`
o `CANCELADO`. El mapper privado lo restaura directamente; la lectura desde la
base no ejecuta una transición de negocio ni llama a `confirmar()`, `cancelar()` o
`marcar_atendido()`.

SQLite garantiza las claves primarias y foráneas, los campos `NOT NULL`, la
matrícula única, una sola agenda por veterinario y los valores permitidos mediante
restricciones `CHECK`. Los DAO dejan que `sqlite3.IntegrityError` se propague. Las
reglas de horario válido, pertenencia a la agenda y superposición de turnos se
validan en el dominio y no se atribuyen a SQLite.

Ningún DAO ejecuta `commit()` ni `rollback()`. La agenda y sus días forman una
unidad lógica que debe confirmarse o revertirse en una misma transacción externa.
Los archivos incorporados en este incremento son:

```text
src/veterinaria/persistencia/
    clinica_dao.py
    veterinario_dao.py
    agenda_medica_dao.py
    turno_dao.py

tests/persistencia/
    test_clinica_dao.py
    test_veterinario_dao.py
    test_agenda_medica_dao.py
    test_turno_dao.py
```

## Persistencia 3: historias clínicas y atenciones

Persistencia 3 mantiene SQLite, `sqlite3`, el patrón DAO, la conexión compartida,
las claves foráneas activas, el SQL parametrizado, los IDs explícitos y el control
externo de las transacciones. La inicialización agrega las tablas
`historia_clinica` y `atencion`.

Los DAO implementan estas operaciones:

- `HistoriaClinicaDAO`: `crear(historia, id_mascota)`, `obtener_por_id()`,
  `obtener_por_mascota()`, `actualizar(historia)` y `eliminar()`. `id_mascota` se
  establece al crear y no se modifica durante una actualización, que cambia
  solamente `fecha_apertura` y `observaciones`. La restricción
  `UNIQUE(id_mascota)` garantiza como máximo una historia por mascota.
- `AtencionDAO`: `crear(atencion, id_historia)`, `obtener_por_id()`, `listar()`,
  `listar_por_historia()`, `actualizar(atencion)` y `eliminar()`. `id_historia` se
  establece al crear y no se modifica durante una actualización. El
  `id_veterinario` se obtiene desde `atencion.veterinario` y sí puede actualizarse
  junto con los demás datos propios de la atención.

Las relaciones del dominio permanecen en un solo sentido:
`Mascota -> HistoriaClinica`, `HistoriaClinica -> Atencion` y
`Atencion -> Veterinario`. Las claves foráneas inversas se resuelven mediante los
parámetros de los DAO; no se agregan referencias `HistoriaClinica -> Mascota`,
`Atencion -> HistoriaClinica` ni `Veterinario -> Atencion`.

`HistoriaClinicaDAO` recupera solamente los datos de la historia y deja su colección
de atenciones vacía. Cuando se necesitan, se consultan con
`AtencionDAO.listar_por_historia()`. `AtencionDAO` reconstruye la atención y utiliza
`VeterinarioDAO` para obtener el profesional básico, sin cargar su clínica, agenda o
turnos. Tampoco carga órdenes de derivación.

La lectura desde SQLite reconstruye hechos existentes y no vuelve a ejecutar las
reglas usadas para registrarlos. En particular, no llama a
`Mascota.registrar_atencion()` ni a `HistoriaClinica._agregar_atencion()`.

`TipoAtencion` se guarda mediante `atencion.tipo.name` y se recupera con
`TipoAtencion[nombre]`. Los valores admitidos son `CONSULTA`, `CONTROL` y
`URGENCIA`, respaldados por una restricción `CHECK`. `fecha_apertura` se almacena
en formato ISO y se recupera con `date.fromisoformat()`; `fecha_hora` usa formato
ISO y `datetime.fromisoformat()`, conservando la precisión disponible.

Los campos opcionales conservan su valor: `None` se almacena como `NULL` y no se
normaliza como una cadena vacía, ni una cadena vacía se convierte en `NULL`.
SQLite garantiza PK, FK, `NOT NULL`, la unicidad de `id_mascota` y el `CHECK` de
`TipoAtencion`. Los DAO propagan `sqlite3.IntegrityError` y no agregan controles de
reglas de negocio ajenos al DER.

Ningún DAO ejecuta `commit()` ni `rollback()`. La conexión compartida permite
confirmar o revertir externamente la creación de una historia y sus atenciones como
parte de una misma transacción. Los archivos incorporados son:

```text
src/veterinaria/persistencia/
    historia_clinica_dao.py
    atencion_dao.py

tests/persistencia/
    test_historia_clinica_dao.py
    test_atencion_dao.py
```

## Persistencia 4: vacunas y aplicaciones

Persistencia 4 continúa con SQLite, `sqlite3`, el patrón DAO, una conexión
compartida, claves foráneas activas, SQL parametrizado, IDs explícitos y
transacciones externas. La inicialización agrega las tablas `vacuna` y
`aplicacion_vacuna`.

Los DAO implementan estas operaciones:

- `VacunaDAO`: `crear()`, `obtener_por_id()`, `listar()`, `actualizar()` y
  `eliminar()`. Conserva `id_vacuna` explícito y actualiza solamente `nombre`,
  `especie` y `obligatoria`.
- `AplicacionVacunaDAO`: `crear(aplicacion, id_mascota)`, `obtener_por_id()`,
  `listar_por_mascota()`, `actualizar(aplicacion)` y `eliminar()`. Conserva
  `id_aplicacion` como identidad explícita del dominio. `id_mascota` se establece
  al crear y `id_vacuna` se obtiene desde `aplicacion.vacuna`.

Una actualización de `AplicacionVacuna` modifica exclusivamente
`fecha_aplicacion` y `fecha_proxima_dosis`; no reasigna `id_mascota` ni
`id_vacuna`. El modelo de objetos mantiene la navegación
`Mascota -> AplicacionVacuna -> Vacuna`, sin referencias inversas desde la
aplicación hacia la mascota ni desde la vacuna hacia aplicaciones o mascotas.

`AplicacionVacunaDAO` utiliza `VacunaDAO` con la misma conexión para reconstruir la
vacuna asociada. La recuperación no llama a
`Mascota.agregar_aplicacion_vacuna()` ni modifica la mascota. `MascotaDAO` continúa
recuperando mascotas básicas con su colección de aplicaciones vacía; cuando se
necesitan aplicaciones se consultan mediante `listar_por_mascota()`.

`fecha_aplicacion` y `fecha_proxima_dosis` se almacenan con `date.isoformat()` y se
recuperan con `date.fromisoformat()`. Una próxima dosis ausente se conserva como
`NULL` en SQLite y `None` en Python. La regla que exige una próxima dosis posterior
a la aplicación continúa en el dominio y no se duplica como restricción SQL.

`obligatoria` se representa como `INTEGER NOT NULL`: `False` corresponde a `0` y
`True` a `1`. Una restricción `CHECK (obligatoria IN (0, 1))` impide otros valores;
no se utilizan cadenas `TRUE` o `FALSE`.

SQLite garantiza PK, FK, `NOT NULL` y el `CHECK` booleano, y los DAO propagan
`sqlite3.IntegrityError`. La base no duplica reglas de vigencia, vencimiento,
especie, vacunas pendientes ni `vacunas_obligatorias_al_dia()`, que permanecen en
el dominio.

No se agregaron cascadas. Una vacuna referenciada o una mascota con aplicaciones
no pueden eliminarse por las FK; una vacuna sin aplicaciones y una aplicación
concreta sí pueden eliminarse. Ningún DAO ejecuta `commit()` ni `rollback()`; el
código coordinador controla la transacción sobre la conexión compartida.

Los archivos incorporados son:

```text
src/veterinaria/persistencia/
    vacuna_dao.py
    aplicacion_vacuna_dao.py

tests/persistencia/
    test_vacuna_dao.py
    test_aplicacion_vacuna_dao.py
```

## Persistencia 5: órdenes, muestras y trazabilidad

Persistencia 5 mantiene SQLite, `sqlite3`, el patrón DAO, la conexión compartida,
el SQL parametrizado, los IDs explícitos y el control externo de las transacciones.
La inicialización agrega las tablas `orden_derivacion_laboratorio`,
`muestra_biologica` e `historial_estado_muestra`.

Los DAO implementan estas operaciones:

- `OrdenDerivacionLaboratorioDAO`: `crear(orden, id_atencion)`,
  `obtener_por_id()`, `listar_por_atencion()`, `actualizar(orden)` y `eliminar()`.
  `id_atencion` se establece al crear y no cambia al actualizar. `EstadoOrden` se
  almacena por nombre. La recuperación restaura el estado sin ejecutar
  `iniciar_proceso()`, `completar()` ni `cancelar()`, y deja vacía la colección de
  muestras.
- `MuestraBiologicaDAO`: `crear(muestra, id_orden)`, `obtener_por_id()`,
  `listar_por_orden()` y `actualizar(muestra)`. `id_orden` se establece al crear y
  no se modifica al actualizar. El DAO no expone una operación de eliminación.

Los estados persistibles de una muestra son `EXTRAIDA`, `EMPAQUETADA`,
`EN_TRANSITO`, `RECIBIDA`, `ANALIZADA` y `RECHAZADA`. El DAO usa un diccionario
explícito para reconstruir la clase State concreta. No serializa objetos State ni
utiliza `pickle`. Las reglas `EXTRAIDA -> EMPAQUETADA`,
`EMPAQUETADA -> EN_TRANSITO`, `EN_TRANSITO -> RECIBIDA / RECHAZADA` y
`RECIBIDA -> ANALIZADA` permanecen exclusivamente en el patrón State; el DAO no
decide ni ejecuta transiciones.

La reconstrucción de una muestra sigue estos pasos:

1. recupera la fila de `muestra_biologica`;
2. consulta el historial en orden estable por `fecha_hora, id_historial`;
3. construye los objetos `HistorialEstadoMuestra`;
4. reconstruye la clase State concreta;
5. utiliza el constructor normal de `MuestraBiologica` para sus datos estructurales;
6. el mapper privado reemplaza controladamente `_estado` y `_historial` con los
   valores persistidos.

Este mecanismo es interno al mapper, no una operación pública del dominio. No
ejecuta transiciones, no inserta registros al leer, no genera un evento persistido
y no duplica el registro inicial `EXTRAIDA`.

`HistorialEstadoMuestra` continúa siendo inmutable y no incorpora un ID al dominio.
`id_historial` es una clave técnica administrada exclusivamente por SQLite. No
existe un `HistorialEstadoMuestraDAO` público: `MuestraBiologicaDAO` inserta y
consulta los registros históricos, pero no los actualiza ni ofrece eliminarlos de
forma individual.

Al recuperar una muestra se valida que el estado actual y todos los estados del
historial sean conocidos, que el historial no esté vacío, que comience en
`EXTRAIDA`, que sus fechas sean no decrecientes y que el último registro coincida
con `estado_actual`. Una inconsistencia produce `ValueError`; no se corrigen datos
históricos silenciosamente.

La actualización conserva la trazabilidad mediante una comparación de prefijo.
Antes de escribir, los registros persistidos deben constituir un prefijo idéntico
del historial del objeto, comparando `nombre_estado`, `fecha_hora` y
`observaciones`. Después se actualizan los datos propios y `estado_actual`, y se
insertan solamente los eventos nuevos. No se borra ni se reconstruye el historial
anterior. Una segunda llamada a `actualizar()` sin transiciones nuevas no agrega
registros duplicados.

En el esquema final para bases nuevas, `muestra_biologica.id_remito` es nullable y
referencia `remito_biologico.id_remito`. Persistencia 6 utiliza esa FK para asociar
las muestras con su remito sin agregar una referencia inversa al dominio.

No se agregaron cascadas. Una orden sin muestras puede eliminarse; una orden con
muestras queda protegida por la FK. `MuestraBiologicaDAO` no expone eliminación y
el historial no ofrece eliminación individual. Ningún DAO ejecuta `commit()` ni
`rollback()`: el llamador puede confirmar o revertir como una unidad tanto la
creación de la muestra con su historial inicial como la actualización del estado
con sus nuevos eventos.

Las relaciones del dominio siguen siendo unidireccionales:
`Atencion -> OrdenDerivacionLaboratorio -> MuestraBiologica`,
`MuestraBiologica -> HistorialEstadoMuestra` y
`MuestraBiologica -> EstadoMuestra`. Las FK no agregan relaciones inversas al
modelo de objetos.

Los archivos incorporados son:

```text
src/veterinaria/persistencia/
    orden_derivacion_laboratorio_dao.py
    muestra_biologica_dao.py

tests/persistencia/
    test_orden_derivacion_laboratorio_dao.py
    test_muestra_biologica_dao.py
```

## Persistencia 6: conservadoras, precintos y remitos

Persistencia 6 agrega las tablas `conservadora_isotermica`, `remito_biologico` y
`precinto_sanitario`. El esquema final de una base nueva también declara la clave
foránea nullable:

```text
muestra_biologica.id_remito
    -> remito_biologico.id_remito
```

La FK acepta `NULL` y remitos existentes, rechaza IDs de remitos inexistentes y no
utiliza `ON DELETE CASCADE`. Es una relación del modelo relacional: cada
`MuestraBiologica` continúa sin conocer al `RemitoBiologico` en el modelo de
objetos.

Los DAO implementados son:

- `ConservadoraIsotermicaDAO`: `crear()`, `obtener_por_id()`, `listar()`,
  `actualizar()` y `eliminar()`. Persiste los estados `DISPONIBLE` y `EN_USO`; el
  código es único. La reconstrucción usa el constructor normal y luego restaura el
  estado persistido sin ejecutar `marcar_en_uso()` ni `liberar()`. No existe una
  liberación automática.
- `PrecintoSanitarioDAO`: `crear(precinto, id_remito)`, `obtener_por_id()`,
  `obtener_por_remito()` y `actualizar()`. Persiste `INTACTO` y `ROTO`; tanto el
  código como `id_remito` son únicos, por lo que cada remito admite como máximo un
  precinto persistido. La actualización modifica código y estado, pero no cambia
  `id_remito`. La reconstrucción no ejecuta `marcar_roto()` y el DAO no expone una
  eliminación pública. Un precinto `ROTO` no rechaza automáticamente las muestras;
  ese procesamiento corresponde a `Recepcion`.
- `RemitoBiologicoDAO`: `crear()`, `obtener_por_id()`, `listar()`, `actualizar()` y
  `guardar_muestra_asociada()`. Persiste clínica de origen, conservadora, fecha de
  emisión, estado y observaciones; al recuperar incorpora el precinto opcional y la
  colección de muestras. Los estados persistibles son `GENERADO`, `DESPACHADO` y
  `RECIBIDO`; este último es final.

Al crear un remito, el DAO persiste también el estado `EN_USO` que la conservadora
ya adquirió en el dominio. La lectura del remito no usa su constructor normal,
porque ese constructor reserva la conservadora y modifica otro objeto. El mapper
privado utiliza exclusivamente:

```python
RemitoBiologico.__new__(RemitoBiologico)
```

Luego restaura identidad, clínica, conservadora, fecha, observaciones, estado,
precinto y muestras. La recuperación no ejecuta el constructor normal,
`agregar_muestra()`, `asignar_precinto()`, `despachar()`, `marcar_recibido()` ni
`conservadora.marcar_en_uso()`.

`MuestraBiologicaDAO.listar_por_remito(id_remito)` consulta
`muestra_biologica.id_remito` y reconstruye las muestras pertenecientes al remito.
La navegación del dominio permanece en un solo sentido:
`RemitoBiologico -> Clinica`, `RemitoBiologico -> ConservadoraIsotermica`,
`RemitoBiologico -> PrecintoSanitario` y
`RemitoBiologico -> MuestraBiologica`. No se agregan referencias inversas desde
esas entidades hacia el remito.

La asociación persistente se realiza después de que el dominio ejecuta
`remito.agregar_muestra()`. Esa operación de dominio empaqueta la muestra, cambia
su State, agrega el historial y la incorpora al remito. Luego
`guardar_muestra_asociada()` actualiza el estado de la muestra, persiste los nuevos
registros históricos y establece `id_remito`. El DAO no vuelve a ejecutar el
empaquetado.

La asociación es idempotente cuando la muestra ya pertenece al mismo remito:
actualiza sus datos sin duplicar historial ni ejecutar nuevamente `empaquetar()`.
La reasignación a otro remito se rechaza; `id_remito` no se trata como una FK
libremente editable.

Ningún DAO ejecuta `commit()` ni `rollback()`. La creación del remito junto con la
persistencia de la conservadora `EN_USO`, la asociación de muestra con su estado e
historial y la creación del precinto pueden participar en una transacción externa
compartida.

No se incorporó infraestructura de migraciones ni versionado de esquema. El
inicializador genera el esquema correcto para bases nuevas y las bases parciales
utilizadas durante el desarrollo pueden recrearse.

Los archivos incorporados son:

```text
src/veterinaria/persistencia/
    conservadora_isotermica_dao.py
    precinto_sanitario_dao.py
    remito_biologico_dao.py

tests/persistencia/
    test_conservadora_isotermica_dao.py
    test_precinto_sanitario_dao.py
    test_remito_biologico_dao.py
```

También se actualizaron `inicializar_bd.py`, `muestra_biologica_dao.py`,
`tests/persistencia/conftest.py`, `test_inicializar_bd.py` y
`test_muestra_biologica_dao.py`. No se agregó ningún `__init__.py`.

## Persistencia 7: envío y recepción

Persistencia 7 agrega las tablas `envio` y `recepcion` con relaciones uno a uno
hacia `remito_biologico` y `envio`, respectivamente. Ambas FK son obligatorias y
únicas, no utilizan `ON DELETE CASCADE` y sus violaciones se propagan como
`sqlite3.IntegrityError`.

`EnvioDAO` ofrece `crear()`, `obtener_por_id()`, `obtener_por_remito()`,
`actualizar()` y `guardar_despacho()`. La actualización modifica únicamente fecha
de salida, fecha de llegada, estado y observaciones; nunca reasigna el remito.
`guardar_despacho()` se ejecuta después de `Envio.iniciar()` y persiste sobre la
conexión compartida el envío, el remito y todas sus muestras. Para cada muestra
delega en `MuestraBiologicaDAO.actualizar()`, por lo que sólo se insertan los nuevos
eventos `EN_TRANSITO` y un segundo guardado no duplica historial.

`RecepcionDAO` ofrece solamente `obtener_por_id()`, `obtener_por_envio()` y
`guardar_recepcion()`. Esta última es la operación de inserción y se ejecuta después
de `Recepcion.procesar_recepcion()`. Persiste coordinadamente la recepción, el envío
`ENTREGADO`, el estado actual del precinto, el remito `RECIBIDO` y las muestras
`RECIBIDA` o `RECHAZADA` con sus nuevos historiales. El DAO no verifica ni rompe el
precinto, no decide el estado de las muestras y no ejecuta operaciones State.

La lectura de un envío usa su constructor normal, recupera el remito mediante
`RemitoBiologicoDAO` y restaura directamente sus fechas y `_estado`. La lectura de
una recepción recupera el envío mediante `EnvioDAO` y usa también el constructor
normal. Ninguna reconstrucción llama `iniciar()`, `registrar_llegada()` o
`procesar_recepcion()`, ni modifica remitos, precintos, muestras o historiales.

Los DAO reciben la misma `sqlite3.Connection` y no ejecutan `commit()` ni
`rollback()`. El llamador puede confirmar o revertir como una unidad el despacho o
la recepción completa, incluso ante una inconsistencia intermedia del historial.
No se exponen operaciones públicas de eliminación para envíos ni recepciones porque
integran la cadena de custodia.

El ciclo definitivo de `RemitoBiologico` es:

```text
GENERADO -> DESPACHADO -> RECIBIDO
```

`RECIBIDO` es final; no existe `CERRADO` ni una operación `cerrar()`.

Los archivos incorporados son:

```text
src/veterinaria/persistencia/
    envio_dao.py
    recepcion_dao.py

tests/persistencia/
    test_envio_dao.py
    test_recepcion_dao.py
```

También se actualizaron `remito_biologico.py`, `inicializar_bd.py`,
`tests/persistencia/conftest.py`, `test_inicializar_bd.py` y este README. No se
agregó ningún `__init__.py`, capa Service, Repository ni UnitOfWork.

## Persistencia 8: resultados de análisis y comprobantes de atención

Persistencia 8 incorpora las tablas `resultado_analisis` y
`comprobante_atencion`. `resultado_analisis.id_muestra` es una FK obligatoria y
única: cada muestra admite como máximo un resultado persistido.
`comprobante_atencion.id_atencion` también es una FK obligatoria y única: cada
atención admite como máximo un comprobante persistido. Ambas fechas son
obligatorias, al igual que el contenido del resultado; el contenido vacío está
permitido y las observaciones del resultado aceptan `NULL`. No se agregan cascadas.

`ResultadoAnalisisDAO` ofrece únicamente `guardar_resultado()`, `obtener_por_id()`
y `obtener_por_muestra()`. El llamador debe ejecutar primero
`resultado.registrar_resultado()` y guardar sólo si devuelve `True`. Esta operación
de dominio delega en la muestra la transición `RECIBIDA -> ANALIZADA` y agrega el
evento histórico correspondiente. `guardar_resultado()` comprueba defensivamente
que la muestra esté `ANALIZADA`, inserta el resultado y delega la persistencia de la
muestra y los eventos nuevos en `MuestraBiologicaDAO.actualizar()`.

El DAO no vuelve a ejecutar `registrar_resultado()`, `analizar()` ni operaciones
State. Tampoco agrega un indicador de registro al dominio. La comprobación de
estado no sustituye el contrato del llamador: sólo éste conoce el retorno de
`registrar_resultado()` para ese resultado. Una muestra `RECHAZADA` no puede
registrar un análisis y el guardado defensivo la rechaza con `ValueError`.

La actualización de una muestra sin nuevas transiciones no duplica historial.
Una segunda inserción de resultado falla por PK o por la FK única `id_muestra` y
propaga `sqlite3.IntegrityError`; no se interpreta como una actualización.

`ComprobanteAtencionDAO` ofrece únicamente `crear()`, `obtener_por_id()` y
`obtener_por_atencion()`. Persiste el comprobante cuya construcción válida ya
representa la emisión. No incorpora estados, pagos ni otra lógica de facturación.
Una segunda inserción para la misma atención también propaga
`sqlite3.IntegrityError`. Ninguno de los dos DAO expone `actualizar()`, `eliminar()`
o `listar()`; el DAO de resultados tampoco expone `crear()`.

Ambos DAO exigen IDs explícitos y rechazan `None` con `ValueError`. Los errores de
PK, FK, `UNIQUE` y `NOT NULL` se propagan como `sqlite3.IntegrityError`. Las fechas
provienen de los objetos y se almacenan mediante `isoformat()`.

La hidratación usa los constructores normales, que sólo validan parámetros y
almacenan referencias. El resultado recupera su muestra mediante
`MuestraBiologicaDAO`; el comprobante recupera su atención y el veterinario básico
mediante `AtencionDAO`. Las fechas se reconstruyen con `datetime.fromisoformat()`.
La lectura no ejecuta transiciones ni inserta historial, y no registra nuevamente
la atención. Las relaciones OO siguen siendo únicamente:

```text
ResultadoAnalisis -> MuestraBiologica
ComprobanteAtencion -> Atencion
```

Todos los DAO utilizan la `sqlite3.Connection` compartida y dejan el `commit()` o
`rollback()` al llamador. Resultado, estado de muestra e historial pueden
confirmarse o revertirse juntos, incluso si falla la validación del historial
después de insertar el resultado. El rollback revierte SQLite, no los objetos
Python; para comprobar o continuar con el estado persistido deben recargarse.

Los archivos incorporados son:

```text
src/veterinaria/persistencia/
    resultado_analisis_dao.py
    comprobante_atencion_dao.py

tests/persistencia/
    test_resultado_analisis_dao.py
    test_comprobante_atencion_dao.py
```

También se actualizaron `inicializar_bd.py`, las fixtures de persistencia, sus tests
de inicialización y este README. El dominio, el DER y el UML no requieren cambios.

## Persistencia 9: integración final y auditoría

P9 cierra la integración de persistencia del MVP. La auditoría comparó las 21 tablas
del DER con SQLite: columnas, tipos adaptados, PK, autoincremento, nulabilidad,
unicidad, claves foráneas y enums coinciden. Se mantiene la arquitectura
`sqlite3 + DAO`, una conexión compartida y el control externo de transacciones.
No se agregan entidades, tablas, columnas ni capas de arquitectura.

El responsable de `Mascota` se expone mediante una propiedad sin setter. El DAO
continúa leyendo `mascota.responsable` tanto al crear como al actualizar. La
persistencia conserva su API de actualización: si se necesita representar otro
estado para una prueba de FK, puede construirse otra mascota con el mismo ID;
no se incorpora una operación de cambio de responsable al dominio.

Las lecturas básicas siguen recuperando objetos parciales por defecto.
`obtener_por_id()` no cambia su comportamiento. Sólo se extienden los listados
necesarios para alimentar las estrategias existentes:

- `AtencionDAO.listar(cargar_ordenes=True)` recupera las órdenes mediante
  `OrdenDerivacionLaboratorioDAO.listar_por_atencion()` y restaura técnicamente
  `_ordenes_derivacion`.
- `MascotaDAO.listar(cargar_aplicaciones=True)` recupera las aplicaciones mediante
  `AplicacionVacunaDAO.listar_por_mascota()` y restaura técnicamente
  `_aplicaciones_vacuna`, incluyendo la vacuna de cada aplicación.

Ambas opciones son keyword-only y su valor por defecto es `False`. La hidratación
no llama `agregar_orden_derivacion()` ni `agregar_aplicacion_vacuna()`, no escribe
en SQLite y no mezcla ni duplica las colecciones de distintas entidades. Los DAO
auxiliares reciben la misma conexión; sus imports no forman ciclos.

La integración con Strategy se realiza componiendo objetos desde el código
llamador, sin SQL específico de reportes ni consultas SQLite dentro de estrategias:

```python
atenciones = atencion_dao.listar(cargar_ordenes=True)
remitos = remito_dao.listar()
mascotas = mascota_dao.listar(cargar_aplicaciones=True)
vacunas = vacuna_dao.listar()

envios = []
for remito in remitos:
    envio = envio_dao.obtener_por_remito(remito.id_remito)
    if envio is not None:
        envios.append(envio)
```

Esas colecciones alimentan, respectivamente, `ReporteAtencionesDerivaciones`,
`ReporteMuestrasRechazadas`, `ReporteVacunasPendientes` (con fecha de referencia
explícita) y `ReporteTiemposTransitoProcesamiento`. Se conserva el alcance actual
de los reportes y no se agrega `EnvioDAO.listar()`.

Los dos escenarios integrales usan `tmp_path / "veterinaria.db"`. Registran
cliente, mascota, historia, clínica, veterinario, agenda, turno, vacunación,
atención, orden y muestra; luego recorren empaquetado, despacho, llegada y
recepción, y emiten un comprobante. Las operaciones de dominio preceden a la
persistencia de sus efectos. Un commit externo confirma el circuito antes de
cerrar la conexión; una conexión nueva y nuevos DAO recuperan las entidades.

Con precinto intacto, el envío termina `ENTREGADO`, el remito `RECIBIDO` y la
muestra `ANALIZADA`, con historial exacto:

```text
EXTRAIDA -> EMPAQUETADA -> EN_TRANSITO -> RECIBIDA -> ANALIZADA
```

Se recuperan tanto el resultado de análisis como el comprobante. Con precinto roto
después del despacho, envío y remito conservan esos estados finales y la muestra
queda `RECHAZADA`, con historial exacto:

```text
EXTRAIDA -> EMPAQUETADA -> EN_TRANSITO -> RECHAZADA
```

`registrar_resultado()` devuelve `False` y no se guarda un resultado; el comprobante
sí se persiste. Ambos escenarios verifican fechas, asociaciones por ID, integridad
referencial y estados tras reabrir. Otros cuatro tests ejecutan las estrategias
sobre datos recuperados, incluyendo una mascota vacunada y otra con pendiente,
y un remito sin envío que se descarta al componer el reporte de tiempos.

Se mantienen estos límites: no hay identity map ni caché; dos consultas pueden
reconstruir instancias distintas del mismo registro y deben compararse por IDs y
valores. El rollback revierte SQLite, no los objetos Python. El llamador debe
ejecutar las operaciones de dominio antes de persistir sus efectos y recargar los
objetos cuando necesite recuperar el estado de la base después de un rollback.

Los archivos nuevos son `tests/persistencia/test_integracion_completa.py` y
`tests/persistencia/test_reportes_persistidos.py`. Se ajustaron `mascota.py`,
`mascota_dao.py`, `atencion_dao.py`, sus tests, las fixtures y este README. El esquema
SQLite, el DBML, el PUML, las estrategias y `AGENTS.md` permanecen sin cambios.

## Vacunación

- `Mascota` mantiene una colección de `AplicacionVacuna`; cada aplicación conoce
  la `Vacuna` correspondiente. Las relaciones se almacenan en un único sentido:
  `Mascota -> AplicacionVacuna -> Vacuna`.
- Una vacuna genera un requisito solamente cuando es obligatoria y su especie
  coincide con la especie de la mascota. La cobertura se compara mediante
  `id_vacuna` y requiere al menos una aplicación vigente.
- Una aplicación anterior puede estar vencida sin impedir que otra aplicación
  vigente de la misma vacuna satisfaga el requisito. Las vacunas opcionales y las
  correspondientes a otras especies no generan pendientes.
- Antes de `fecha_aplicacion`, una aplicación no está vigente ni vencida. Está
  vigente desde su aplicación hasta antes de `fecha_proxima_dosis`, y vencida en
  esa fecha o después. Si no tiene próxima dosis, permanece vigente desde su
  aplicación sin vencimiento definido.
- `Mascota.registrar_atencion(atencion, vacunas)` usa
  `atencion.fecha_hora.date()` como fecha de referencia. Requiere una historia
  clínica y todas las vacunas obligatorias al día. Si la validación falla, devuelve
  `False` sin modificar la historia; si pasa, delega el agregado en
  `HistoriaClinica._agregar_atencion()`.

## Órdenes, muestras y trazabilidad

- Una `Atencion` puede registrar varias `OrdenDerivacionLaboratorio`, y cada orden
  mantiene su colección de `MuestraBiologica`. La navegación es unidireccional:
  `Atencion -> OrdenDerivacionLaboratorio -> MuestraBiologica`.
- Las órdenes comienzan en `PENDIENTE`, pueden pasar a `EN_PROCESO` y finalizar
  como `COMPLETADA` o `CANCELADA`. `completar()` controla solamente el ciclo de
  la orden y no inspecciona el estado de sus muestras.
- Toda muestra comienza en `EXTRAIDA`. Su ciclo de vida se implementa mediante
  State: `EXTRAIDA -> EMPAQUETADA -> EN_TRANSITO -> RECIBIDA -> ANALIZADA`, con
  la alternativa `EN_TRANSITO -> RECHAZADA`.
- `ResultadoAnalisis` mantiene una referencia unidireccional a `MuestraBiologica`.
  `registrar_resultado()` delega en `MuestraBiologica.analizar()` usando la fecha y
  las observaciones del resultado. Una muestra `RECIBIDA` pasa a `ANALIZADA` y
  registra el cambio en su historial sin que el resultado modifique directamente el
  State ni la colección histórica.
- `ANALIZADA` y `RECHAZADA` son estados finales. Una operación inválida devuelve
  `False` sin cambiar el estado ni agregar historial. Como solamente `RECIBIDA`
  admite `analizar()`, una muestra `RECHAZADA` no puede registrar un resultado.
- La muestra mantiene registros inmutables de `HistorialEstadoMuestra`. El primer
  registro corresponde a `EXTRAIDA` y cada transición exitosa agrega uno nuevo.
  Las fechas anteriores al último registro son rechazadas; las iguales o
  posteriores se admiten cuando la transición también es válida.
- Los estados reciben temporalmente la muestra durante una operación, pero no la
  almacenan. Tampoco existen referencias inversas desde orden, muestra o historial.

## Remitos, envío y recepción

- Una `ConservadoraIsotermica` comienza `DISPONIBLE`. Al crear un
  `RemitoBiologico`, la conservadora requerida queda `EN_USO`; mientras esté
  ocupada no puede utilizarse para crear otro remito. `liberar()` está disponible,
  pero todavía no forma parte de un flujo automático del remito.
- El remito conserva referencias unidireccionales hacia la `Clinica` de origen,
  la conservadora, un precinto opcional y sus muestras. Ninguna de esas entidades
  almacena una referencia inversa al remito en el modelo de objetos.
- `agregar_muestra()` evita registrar dos veces la misma instancia y delega en
  `MuestraBiologica.empaquetar()`. La muestra se incorpora solamente si la
  transición `EXTRAIDA -> EMPAQUETADA` tiene éxito; la propia muestra administra
  su State y agrega el registro correspondiente a su historial.
- La primera asignación de un `PrecintoSanitario` devuelve `True`. Asignar `None`
  o intentar reemplazar el precinto devuelve `False`. En el comportamiento actual
  se permite asignar un precinto a un remito sin muestras, asignar uno que ya esté
  roto y agregar muestras después de haberlo asignado.
- Un precinto comienza `INTACTO` y puede pasar una sola vez a `ROTO`. Romperlo no
  modifica inmediatamente las muestras; su estado se verifica al procesar la
  recepción.
- `puede_despacharse()` es una consulta sin efectos laterales. Devuelve `True`
  solamente si el remito sigue `GENERADO`, tiene conservadora, al menos una
  muestra y un precinto intacto. No despacha el remito ni cambia estados.
- `Envio` mantiene una referencia unidireccional al remito. Al iniciar un envío,
  el remito pasa de `GENERADO` a `DESPACHADO`, sus muestras pasan de
  `EMPAQUETADA` a `EN_TRANSITO` y el envío pasa de `PENDIENTE` a `EN_TRANSITO`.
- Registrar la llegada guarda su fecha y cambia el envío a `ENTREGADO`; no procesa
  las muestras ni cambia el remito.
- `Recepcion` mantiene una referencia unidireccional al envío y verifica el precinto
  a través de `Recepcion -> Envio -> RemitoBiologico`. Si está `INTACTO`, las
  muestras pasan de `EN_TRANSITO` a `RECIBIDA`; si está `ROTO`, pasan a
  `RECHAZADA` y no pueden continuar hacia `ANALIZADA`. En ambos casos, el remito
  pasa de `DESPACHADO` a `RECIBIDO`.
- `RemitoBiologico` y `Recepcion` usan `despachar()`, `recibir()` y `rechazar()` de
  `MuestraBiologica`; no modifican directamente su State ni su historial. Antes de
  procesar el lote validan estados y fechas para evitar cambios parciales. El
  historial continúa siendo inmutable.
- La conservadora permanece `EN_USO` después de la recepción. No existe liberación
  automática y todavía no está definido cuándo debe liberarse.

El flujo del remito termina definitivamente en `RECIBIDO`, que es final.

## Reportes y patrón Strategy

- `EstrategiaReporte` define la operación común `generar()`. Las cuatro estrategias
  concretas reciben en su constructor las colecciones que necesitan y devuelven
  listas de diccionarios.
- `GeneradorReportes` conserva una estrategia intercambiable. `generar_reporte()`
  delega exclusivamente en `estrategia.generar()` y no conoce la lógica particular
  de ningún reporte. `establecer_estrategia()` permite cambiarla y devuelve `False`
  si recibe `None`, sin reemplazar la estrategia vigente.
- `ReporteAtencionesDerivaciones(atenciones)` relaciona cada atención con su
  veterinario y sus órdenes obtenidas mediante `obtener_ordenes_derivacion()`,
  agrupa los datos de las derivaciones y calcula su cantidad. Las órdenes canceladas
  también se incluyen.
- `ReporteMuestrasRechazadas(remitos)` recorre las muestras públicas de los remitos
  e incluye únicamente las que se encuentran efectivamente en `RECHAZADA`. Obtiene
  la fecha del historial y agrega el contexto del remito, la clínica y el precinto.
  Un precinto roto por sí solo no incorpora una muestra: debe haberse producido la
  transición `EN_TRANSITO -> RECHAZADA`.
- `ReporteVacunasPendientes(mascotas, vacunas, fecha_referencia)` llama a
  `Mascota.obtener_vacunas_pendientes()` y relaciona cada pendiente con su mascota,
  responsable y fecha de referencia. No vuelve a implementar las reglas de
  obligatoriedad, especie, vigencia o vencimiento.
- `ReporteTiemposTransitoProcesamiento(envios)` devuelve un resumen con cantidad y
  promedio de envíos con tránsito completo, calculado como llegada menos salida, y
  cantidad y promedio de muestras procesadas, calculado entre los registros
  `RECIBIDA` y `ANALIZADA`. Cada envío y cada muestra se cuentan una sola vez. Las
  etapas incompletas y las muestras rechazadas no participan del promedio de
  procesamiento; sin datos suficientes, la cantidad es cero y el promedio es
  `None`. Las duraciones se conservan como `timedelta`.

Los cuatro reportes son consultas en memoria y no modifican entidades, estados ni
historiales. Las entidades del dominio no conocen al generador ni a las estrategias;
los reportes aprovechan exclusivamente las relaciones unidireccionales y las APIs
públicas existentes.

## Interfaz gráfica y capa de servicios

La interfaz sigue la separación de la guía de Flet de la cátedra:

```text
Presentación (interfaz/, Flet)
   ↓ llama a
Negocio / casos de uso (servicios/)
   ↓ usa
Dominio (dominio/, patrones/)  +  DAO (persistencia/)
   ↓
sqlite3 → SQLite
```

### Ejecución

Desde la raíz del repositorio y con el entorno virtual activo:

```console
python -m pip install -r requirements.txt
python src/veterinaria/main.py --demo
```

- `--demo` carga datos de demostración si la base está vacía (2 clínicas, 3 veterinarios con
  agenda, 5 clientes, 6 mascotas, vacunas, atenciones, comprobantes y remitos en distintos
  estados: aceptado y analizado, rechazado por precinto roto, en tránsito y una muestra
  pendiente de empaquetar). Sin `--demo` se parte de una base vacía.
- `--web` abre la aplicación en el navegador (`http://localhost:8550`).
- También puede usarse `flet run src/veterinaria/main.py`.
- La base es `veterinaria.db` en la carpeta desde la que se ejecuta; `VETERINARIA_DB` permite
  indicar otra ruta. Los PDF y CSV van a una carpeta `exportaciones/` junto a la base.

### Cinco secciones

| Sección | Pestañas | Procesos |
|---|---|---|
| **Clientes y mascotas** | Clientes · Mascotas | 1 y 2: altas, edición, bajas con confirmación, búsqueda e historia clínica de cada mascota (atenciones y vacunas). |
| **Turnos** | Agenda de turnos · Veterinarios y agendas | Reserva con control de agenda y superposición; clínicas, veterinarios y agenda semanal. |
| **Atención** | Atenciones · Vacunas | 3 y 7: registro de la atención con control de vacunas, derivación al laboratorio en un paso y comprobante de atención en PDF. |
| **Laboratorio** | Empaquetado · Envío y recepción · Resultados · Seguimiento | 4, 5, 6 y 7: remito y precinto, despacho, recepción con verificación del precinto, resultados con su comprobante en PDF y línea de tiempo de cada muestra. |
| **Reportes** | — | Los cuatro reportes con vista previa y exportación a PDF o CSV. |

Para que sea fácil de usar, varios pasos del circuito se resuelven con una sola acción:
registrar una mascota abre su historia clínica; *Derivar a laboratorio* emite la orden y la
muestra; *Empaquetar y precintar* genera el remito, empaqueta las muestras y coloca el precinto
(con un código automático si no se ingresa uno); *Registrar recepción* anota la llegada y
verifica el precinto. Las fechas se escriben sólo con números (las barras se agregan solas) o se eligen en un
calendario desplegable (con selector de hora cuando el campo incluye la hora), los selectores
admiten búsqueda por escritura, los estados se muestran con etiquetas de color y los cuadros
de formulario ocupan todo el ancho y quedan fijos, y el listado ocupa el resto de la pantalla con su propia
barra de desplazamiento: al crecer, sólo se mueve la tabla y no toda la pantalla (la pestaña
«Veterinarios y agendas», que reúne tres listados, se desplaza completa). El diseño está pensado para
ventanas grandes (pantalla completa).

### Recorrido sugerido para la demostración

1. **Clientes y mascotas** → alta de una mascota sin responsable: no se guarda (RN01).
2. **Turnos** → reservar dos turnos que se pisen: el segundo se rechaza; uno fuera de horario también.
3. **Atención** → registrar una atención de *Toby* o *Mora*: se bloquea por vacunas obligatorias
   pendientes; aplicarlas en **Vacunas** y volver a intentar. Derivar la atención a laboratorio.
4. **Laboratorio › Empaquetado** → elegir la clínica, la conservadora y las muestras: se emite el remito y el precinto.
5. **Envío y recepción** → despachar; recibir con el precinto íntegro (muestras *Recibida*) o
   destildado (muestras *Rechazada*).
6. **Resultados** → cargar el resultado de una muestra recibida; una rechazada no puede analizarse.
7. Al registrar el resultado se emite el **comprobante de resultados** en PDF (se puede volver a emitir desde la
   tabla de resultados). **Seguimiento** → línea de tiempo inmutable de cada muestra. **Atención** →
   comprobante de atención en PDF. **Reportes**.

### Capa de servicios

`Servicios(ruta_bd)` (`servicios/fachada.py`) agrupa `ClinicaServicio`, `AtencionServicio`,
`LaboratorioServicio` y `ReporteServicio`. Cada método público es una unidad de trabajo: abre una
conexión, vuelve a leer los objetos necesarios, ejecuta primero la operación de dominio y luego el
DAO, y hace `commit`; ante cualquier error hace `rollback`. Las acciones en un paso
(`derivar`, `empaquetar`, `recibir_remito`) ocurren en una sola transacción: si algo falla no queda
nada a medias. Las violaciones de reglas se informan como `ErrorNegocio` con un mensaje legible y
los errores de integridad de SQLite (DNI o matrícula repetidos, claves foráneas) se traducen al
mismo tipo. Los IDs explícitos que exigen los DAO los genera el servicio (`MAX(id) + 1`). Las reglas
del negocio siguen en el dominio: la capa usa `Veterinario.agregar_turno()`, `Mascota.registrar_atencion()`,
`RemitoBiologico`, `Envio`, `Recepcion`, `ResultadoAnalisis` y las estrategias existentes, y suma
mensajes que explican por qué una operación fue rechazada. `servicios/datos_demo.py` crea los datos
de demostración a través de esos mismos servicios.

Además, la capa valida los datos que se ingresan (`servicios/base.py`):

- nombre y apellido de clientes y veterinarios: sólo letras (se aceptan tildes, ñ, espacios,
  apóstrofo y guion, como en «María José» o «Pérez-Núñez»);
- DNI: sólo números, de 7 u 8 dígitos (el campo de la pantalla no admite otra cosa);
- fecha de nacimiento de la mascota: no puede ser posterior a hoy;
- turnos: no se reservan en una fecha u hora que ya pasó.

Clínicas y veterinarios se pueden eliminar desde **Turnos › Veterinarios y agendas**, con
confirmación. Un veterinario con turnos o atenciones no se elimina (al eliminarlo se borra también su
agenda), y una clínica sólo se elimina si no tiene veterinarios ni remitos.

Los cuatro reportes se generan con `GeneradorReportes` y las estrategias existentes; el servicio sólo
compone los datos (por ejemplo, agrega mascota y clínica al reporte de atenciones). El CSV usa `;`
como separador y UTF-8 con BOM para abrirse bien en Excel.

El comprobante de resultados es un PDF que se genera a pedido con los datos ya persistidos
(muestra, estudio, mascota, responsable, clínica, remito y precinto, fechas y resultado): no agrega
entidades ni tablas. Registrar una mascota repetida (mismo responsable, nombre y especie) se
rechaza, y una mascota sin atenciones puede eliminarse junto con su historia vacía.

No se modificaron el dominio, los DAO, las estrategias, el DER ni el UML. La facturación y el
resto de los procesos opcionales siguen fuera del alcance.

## Pruebas

Desde la raíz del repositorio, con Python y pytest disponibles:

```console
python -m pytest -p no:cacheprovider
```

La suite completa contiene actualmente 775 casos y finaliza sin fallos.

`pytest.ini` permite resolver los imports desde `src`. Los tests cubren disponibilidad
semanal, límites horarios, superposición, cancelaciones, estados de turnos, registro
de veterinarios, responsables de mascotas, asignación de historias clínicas,
registro de atenciones, tipos de atención, vigencia de aplicaciones y control de
vacunas obligatorias, ciclos de órdenes, State de muestras y trazabilidad temporal.
También cubren estados de conservadoras y precintos, reserva de conservadoras,
empaquetado y despacho de remitos, envíos, registro de llegada, recepción según el
estado del precinto, rechazo de muestras, prevención de cambios parciales y registro
de resultados con transición de muestras recibidas a `ANALIZADA`. También cubren la
construcción y las referencias de los comprobantes de atención. Los tests del
noveno incremento verifican el cambio y la delegación de estrategias, los cuatro
reportes, sus casos vacíos y múltiples, los promedios de tiempos y que las consultas
no modifiquen el dominio. Los tests de Persistencia 1 verifican conexión e
inicialización, ABMC, reconstrucción de responsables, fechas ISO, SQL parametrizado,
restricciones de integridad, claves foráneas y control externo de transacciones.
Los tests de Persistencia 2 verifican la inicialización de sus cinco tablas, el
ABMC de clínicas, veterinarios, agendas y turnos, los filtros por clínica o
veterinario, las conversiones ISO, la restauración de enums, la carga independiente
de asociaciones, las restricciones de integridad y las transacciones externas.
Los tests de Persistencia 3 verifican las tablas de historias y atenciones, sus
operaciones DAO, filtros, orden determinista, conversiones ISO, valores opcionales,
integridad, carga simple, reconstrucción sin ejecutar reglas de registro, FK
hacia mascota e historia sin reasignación y control externo de transacciones.
Los tests de Persistencia 4 verifican las tablas y DAO de vacunas y aplicaciones,
IDs explícitos, orden de listados, mapeo booleano, fechas ISO, valores opcionales,
integridad, reconstrucción de vacunas, carga simple de mascotas, relaciones fijas,
eliminaciones protegidas por FK y transacciones externas.
Los tests de Persistencia 5 verifican sus tres tablas, ambos DAO, todos los
estados de orden y muestra, reconstrucción sin transiciones ni nuevos eventos,
historial inmutable y orden estable, consistencia State/historial, comparación de
prefijo, actualizaciones incrementales sin duplicados, claves foráneas, eliminación
protegida y transacciones externas.
Los tests de Persistencia 6 verifican sus tres tablas y DAO, estados y
restricciones de integridad, la FK final nullable de muestras, reconstrucción sin
operaciones de negocio, carga de clínica, conservadora, precinto y muestras,
asociación idempotente sin duplicar historial, rechazo de reasignaciones y control
externo de transacciones.
Los tests de Persistencia 7 verifican las tablas y DAO de envío y recepción, las
restricciones uno a uno, fechas opcionales, reconstrucción sin operaciones de
dominio, despacho y recepción coordinados, precintos intactos y rotos, historial
incremental sin duplicados, rollback externo, ausencia de commits internos y
relaciones del dominio exclusivamente unidireccionales.
Los tests de Persistencia 8 verifican ambas tablas y DAO, IDs explícitos, fechas
con microsegundos, restricciones de integridad, reconstrucción sin operaciones de
negocio, análisis de muestras recibidas, rechazo de muestras no analizadas,
historial sin duplicados y control externo de transacciones tanto exitosas como
fallidas.
Los tests de Persistencia 9 verifican la protección del responsable, los listados
opcionales sin operaciones de negocio, aislamiento de colecciones, ambos circuitos
integrales con cierre y reapertura y los cuatro reportes con datos persistidos.
El cierre incorpora siete pruebas de rechazo de `id=None` en los DAO antiguos:
comprueban `ValueError`, ausencia de SQL e inserciones y conservación del trabajo
pendiente hasta el rollback explícito del llamador.

Los 28 casos nuevos cubren la capa de servicios (`tests/servicios/`) —circuito completo con
precinto intacto y roto, acciones en un paso, turnos, vacunas obligatorias, datos de demostración,
exportación PDF/CSV, comprobante de resultados y los cuatro reportes— y un recorrido de la interfaz con una página simulada
(`tests/interfaz/`), sin abrir ventanas. Estas pruebas no reemplazan una revisión visual de la
aplicación.

## Documentación

- [UML editable](docs/uml/DG_TP_Veterinaria.puml) y [diagrama SVG](docs/uml/DG_TP_Veterinaria.svg).
- [DER editable](docs/der/BD_TP_Veterinaria.dbml) y [diagrama SVG](docs/der/BD_TP_Veterinaria.svg).

La fuente UML se mantiene como diagrama de dominio, State y Strategy; no incorpora
DAO ni clases de persistencia. Su SVG se regeneró desde el PUML actual con
PlantUML 1.2024.3, disponible en la extensión local de VS Code. `EstadoRemito`
contiene únicamente `GENERADO`, `DESPACHADO` y `RECIBIDO`.
El SVG del DER contiene las tablas y columnas esperadas, pero su correspondencia
completa con las restricciones del DBML no pudo certificarse mediante regeneración:
no se encontró un renderizador DBML local disponible. Ese SVG se conserva sin
modificaciones. No se instalaron ni descargaron herramientas.

Las fuentes editables representan el modelo final del MVP.
El DER conserva `id_agenda` como identificador técnico de persistencia; el objeto
de dominio no lo utiliza. `agenda_medica.id_veterinario` es único y los días
laborales se almacenan en `agenda_medica_dia`, con clave compuesta
`(id_agenda, dia)`. El DER ya representa las relaciones finales entre muestras,
remitos, envíos y recepciones utilizadas por el esquema SQLite para bases nuevas.

## Limitaciones del alcance

Estas decisiones delimitan el MVP y deben tenerse en cuenta al utilizarlo:

- La inicialización crea el esquema para bases nuevas; no migra bases históricas.
- Las lecturas son parciales por defecto. El llamador carga y compone las
  asociaciones necesarias; P9 ofrece cargas opcionales de órdenes y aplicaciones
  para reportes.
- No existe identity map ni caché de entidades: lecturas independientes pueden
  producir objetos distintos para el mismo ID.
- Un rollback revierte SQLite, no los objetos Python ya modificados. Para recuperar
  el estado persistido deben recargarse.
- La liberación automática de `ConservadoraIsotermica` no está definida; existe
  `liberar()`, pero no forma parte del flujo automático de recepción.
- La interfaz es de escritorio (Flet) y de uso local: sin autenticación de usuarios ni
  acceso concurrente de varias instancias a la misma base.
- Los servicios generan los IDs con `MAX(id) + 1`, adecuado para un único usuario.

## Cierre del MVP

El dominio, State, Strategy, los cuatro reportes y Persistencia P1–P9 están
terminados para el alcance actual. La auditoría y el incremento final de cierre
completan la consistencia de IDs explícitos y la documentación de ejecución.
Los circuitos con precinto intacto y roto se verifican tras cerrar y reabrir SQLite.
Queda pendiente certificar el SVG del DER mediante regeneración cuando se disponga
de una herramienta adecuada; su fuente DBML es la referencia vigente.
