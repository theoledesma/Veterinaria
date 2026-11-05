"""Infraestructura común de los servicios: conexión, transacciones e IDs."""

import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

from veterinaria.persistencia.conexion import abrir_conexion
from veterinaria.persistencia.inicializar_bd import inicializar_bd
from veterinaria.servicios.errores import ErrorNegocio

# Nombres fijos de tabla/columna; nunca provienen del usuario.
_TABLAS_ID = {
    "cliente": "id_cliente",
    "mascota": "id_mascota",
    "clinica": "id_clinica",
    "veterinario": "id_veterinario",
    "turno": "id_turno",
    "historia_clinica": "id_historia",
    "atencion": "id_atencion",
    "vacuna": "id_vacuna",
    "aplicacion_vacuna": "id_aplicacion",
    "orden_derivacion_laboratorio": "id_orden",
    "muestra_biologica": "id_muestra",
    "conservadora_isotermica": "id_conservadora",
    "precinto_sanitario": "id_precinto",
    "remito_biologico": "id_remito",
    "envio": "id_envio",
    "recepcion": "id_recepcion",
    "resultado_analisis": "id_resultado",
    "comprobante_atencion": "id_comprobante",
}


class ServicioBase:
    """Abre la conexión, confirma o revierte cada operación y genera IDs.

    Cada método público de un servicio es una unidad de trabajo: abre una
    conexión, ejecuta dominio + DAO y hace commit; ante cualquier error hace
    rollback y lo informa como ``ErrorNegocio``. Los objetos de dominio se
    vuelven a leer en cada operación, por lo que un rollback nunca deja
    objetos Python inconsistentes.
    """

    def __init__(self, ruta_bd):
        self._ruta = str(ruta_bd)
        if self._ruta == ":memory:":
            raise ValueError("Los servicios requieren una base en archivo.")
        con = abrir_conexion(self._ruta)
        try:
            inicializar_bd(con)
            con.commit()
        finally:
            con.close()

    @contextmanager
    def _tx(self):
        con = abrir_conexion(self._ruta)
        try:
            yield con
            con.commit()
        except ErrorNegocio:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise ErrorNegocio(_traducir_integridad(exc)) from exc
        except ValueError as exc:
            con.rollback()
            raise ErrorNegocio(str(exc)) from exc
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    @contextmanager
    def _lectura(self):
        con = abrir_conexion(self._ruta)
        try:
            yield con
        finally:
            con.close()

    @staticmethod
    def _siguiente_id(con, tabla: str) -> int:
        columna = _TABLAS_ID[tabla]
        fila = con.execute(
            f"SELECT COALESCE(MAX({columna}), 0) + 1 FROM {tabla}"
        ).fetchone()
        return int(fila[0])


def _traducir_integridad(exc: sqlite3.IntegrityError) -> str:
    texto = str(exc)
    if "UNIQUE" in texto:
        return "Ya existe un registro con ese valor único (por ejemplo DNI, matrícula o código)."
    if "FOREIGN KEY" in texto:
        return "El registro está relacionado con otros datos y no puede modificarse o eliminarse así."
    if "NOT NULL" in texto:
        return "Falta completar un dato obligatorio."
    return f"No se pudo guardar por una restricción de integridad: {texto}"


def requerir_texto(valor, campo: str) -> str:
    texto = (valor or "").strip()
    if not texto:
        raise ErrorNegocio(f"El campo «{campo}» es obligatorio.")
    return texto


# letras (con tildes, ü y ñ) separadas por un espacio, apóstrofo o guion: «María José», «O'Connor»
_PATRON_NOMBRE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*")
DNI_MIN, DNI_MAX = 7, 8


def requerir_nombre(valor, campo: str) -> str:
    """Nombre o apellido de una persona: sólo letras."""
    texto = " ".join(requerir_texto(valor, campo).split())
    if not _PATRON_NOMBRE.fullmatch(texto):
        raise ErrorNegocio(f"El campo «{campo}» sólo admite letras.")
    return texto


def requerir_dni(valor) -> str:
    """DNI: sólo números, entre 7 y 8 dígitos."""
    dni = requerir_texto(valor, "DNI").replace(".", "")
    if not dni.isdigit() or not DNI_MIN <= len(dni) <= DNI_MAX:
        raise ErrorNegocio(f"El DNI debe tener sólo números, entre {DNI_MIN} y {DNI_MAX} dígitos.")
    return dni


def validar_fecha_nacimiento(fecha) -> None:
    if fecha is not None and fecha > date.today():
        raise ErrorNegocio("La fecha de nacimiento no puede ser posterior a hoy.")


def fmt_fecha_hora(valor) -> str:
    return valor.strftime("%d/%m/%Y %H:%M") if isinstance(valor, datetime) else (
        valor.strftime("%d/%m/%Y") if valor is not None else ""
    )


def ahora() -> datetime:
    """Fecha y hora actuales al minuto, igual que las que se ingresan en la interfaz."""
    return datetime.now().replace(second=0, microsecond=0)
