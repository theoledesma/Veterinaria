# Interfaz gráfica

Interfaz de escritorio en **Flet** para el sistema del TP. Se agregó **sin modificar ningún archivo existente**:
el dominio, los patrones, la persistencia y los tests siguen exactamente igual. La interfaz usa esas clases
tal como están.

## Cómo ejecutarla

```bash
python -m pip install -r requirements.txt -r requirements-interfaz.txt
```

```bash
python main.py
```

La primera vez se crea `veterinaria.db` con datos de demostración (está en el `.gitignore`). Si la ventana
no abre, se puede usar el navegador con `python main.py --web`. Para volver a los datos iniciales, borrar
`veterinaria.db`.

## Qué se agregó

| Archivo | Para qué |
|---|---|
| `main.py` | Abre la interfaz desde la raíz del repositorio (agrega `src` al path). |
| `requirements-interfaz.txt` | Dependencia de la interfaz (`flet`), separada de `requirements.txt`. |
| `src/veterinaria/main.py` | Punto de entrada previsto en la estructura del `AGENTS.md`. |
| `src/veterinaria/servicios/sistema.py` | Capa de servicios: coordina cada caso de uso con los DAO y las clases del dominio, dentro de una transacción. |
| `src/veterinaria/interfaz/` | Pantallas en Flet (una por sección). |
| `src/veterinaria/datos_demo.py` | Carga datos de prueba usando la capa de servicios. |
| `tests/test_servicios_interfaz.py` | Pruebas de la capa de servicios. |

## Cómo se conecta con el código del grupo

La capa de servicios no agrega reglas de negocio. Para cada operación:

1. carga los objetos con los DAO;
2. le pide la operación a las clases del dominio, que deciden si se puede (por ejemplo `Recepcion.procesar_recepcion()`
   o `ResultadoAnalisis.registrar_resultado()`, que usan el patrón State de `MuestraBiologica`);
3. guarda el resultado con los DAO y confirma la transacción.

Cuando el dominio devuelve `False`, el servicio averigua el motivo para mostrar un mensaje claro (por ejemplo,
"la muestra fue RECHAZADA porque el precinto llegó roto").

Detalles a tener en cuenta:

- Los DAO piden ids explícitos: el servicio usa el siguiente al mayor existente en cada tabla.
- La conexión se abre con la misma configuración que `persistencia/conexion.py`, pero habilitada para varios
  hilos, porque Flet atiende cada evento en un hilo distinto.
- Al recibir un remito, la conservadora se libera con `ConservadoraIsotermica.liberar()` para poder reutilizarla.
- Los reportes se generan con `GeneradorReportes` y las cuatro estrategias del grupo, y se muestran como tablas.

## Pantallas

| Pantalla | Procesos y reglas |
|---|---|
| Clientes | Alta y edición de clientes. |
| Mascotas | Alta con responsable obligatorio (RN01), historia clínica y vacunas aplicadas. |
| Turnos | Reserva dentro de la agenda (RN02) y sin superposición (RN03); confirmar y cancelar. |
| Atención | Registro de la atención con control de vacunas (RN05), orden de derivación con su muestra (RN06) y comprobante. |
| Laboratorio | Empaquetado (RN07), despacho (RN08, RN09), llegada, recepción con verificación del precinto (RN10 a RN12), resultado (RN13) e historial de estados (RN14, RN15). |
| Reportes | Los cuatro reportes del patrón Strategy. |

## Recorrido de prueba

1. **Mascotas**: Nala figura con vacunas pendientes. En **Atención**, intentar registrarle una atención: el sistema
   no lo permite hasta aplicarle las vacunas (botón de vacunas en Mascotas).
2. **Atención**: registrar una atención de otra mascota y emitir una orden de derivación.
3. **Laboratorio > Empaquetado**: generar el remito con esa muestra.
4. **Envío**: despachar y después registrar la llegada.
5. **Recepción**: destildar "Precinto sanitario intacto" y registrar: la muestra queda RECHAZADA.
6. **Resultados**: intentar cargar el resultado de esa muestra: no se permite.
7. **Trazabilidad**: ver el historial de estados de la muestra.
8. **Reportes**: el reporte de muestras rechazadas la muestra.
