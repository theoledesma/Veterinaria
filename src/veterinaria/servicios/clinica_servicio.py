"""Procesos 1 y 2 (parte): clientes, mascotas, clínicas, veterinarios, agenda y turnos."""

from veterinaria.dominio.clinica.agenda_medica import AgendaMedica, DiaSemana
import sqlite3
from collections import Counter
from datetime import date

from veterinaria.dominio.clinica.cliente import Cliente
from veterinaria.dominio.clinica.clinica import Clinica
from veterinaria.dominio.clinica.historia_clinica import HistoriaClinica
from veterinaria.dominio.clinica.mascota import Mascota
from veterinaria.dominio.clinica.turno import EstadoTurno, Turno
from veterinaria.dominio.clinica.veterinario import Veterinario
from veterinaria.persistencia.agenda_medica_dao import AgendaMedicaDAO
from veterinaria.persistencia.atencion_dao import AtencionDAO
from veterinaria.persistencia.cliente_dao import ClienteDAO
from veterinaria.persistencia.clinica_dao import ClinicaDAO
from veterinaria.persistencia.historia_clinica_dao import HistoriaClinicaDAO
from veterinaria.persistencia.mascota_dao import MascotaDAO
from veterinaria.persistencia.turno_dao import TurnoDAO
from veterinaria.persistencia.veterinario_dao import VeterinarioDAO
from veterinaria.servicios.base import (ServicioBase, ahora, fmt_fecha_hora, requerir_dni, requerir_nombre,
                                        requerir_texto, validar_fecha_nacimiento)
from veterinaria.servicios.errores import ErrorNegocio


class ClinicaServicio(ServicioBase):
    # ------------------------------------------------------------- clientes
    def crear_cliente(self, nombre, apellido, dni, telefono="", email="") -> int:
        nombre = requerir_nombre(nombre, "Nombre")
        apellido = requerir_nombre(apellido, "Apellido")
        dni = requerir_dni(dni)
        with self._tx() as con:
            id_cliente = self._siguiente_id(con, "cliente")
            ClienteDAO(con).crear(
                Cliente(id_cliente, nombre, apellido, dni,
                        (telefono or "").strip(), (email or "").strip())
            )
        return id_cliente

    def modificar_cliente(self, id_cliente, nombre, apellido, dni, telefono="", email=""):
        with self._tx() as con:
            dao = ClienteDAO(con)
            cliente = dao.obtener_por_id(id_cliente)
            if cliente is None:
                raise ErrorNegocio("El cliente no existe.")
            cliente.nombre = requerir_nombre(nombre, "Nombre")
            cliente.apellido = requerir_nombre(apellido, "Apellido")
            cliente.dni = requerir_dni(dni)
            cliente.telefono = (telefono or "").strip()
            cliente.email = (email or "").strip()
            dao.actualizar(cliente)

    def eliminar_cliente(self, id_cliente):
        with self._tx() as con:
            if not ClienteDAO(con).eliminar(id_cliente):
                raise ErrorNegocio("El cliente no existe.")

    def listar_clientes(self) -> list[dict]:
        with self._lectura() as con:
            return [
                {"id": c.id_cliente, "nombre": c.nombre, "apellido": c.apellido,
                 "dni": c.dni, "telefono": c.telefono, "email": c.email,
                 "etiqueta": f"{c.apellido}, {c.nombre} ({c.dni})"}
                for c in ClienteDAO(con).listar()
            ]

    # ------------------------------------------------------------- mascotas
    def crear_mascota(self, id_cliente, nombre, especie, raza="",
                      fecha_nacimiento=None, sexo="", abrir_historia=False) -> int:
        """RN01: toda mascota necesita un responsable existente.

        Con ``abrir_historia=True`` se abre su historia clínica en la misma operación."""
        if id_cliente is None:
            raise ErrorNegocio("Toda mascota debe tener un responsable (cliente).")
        nombre = requerir_texto(nombre, "Nombre")
        especie = requerir_texto(especie, "Especie")
        validar_fecha_nacimiento(fecha_nacimiento)
        with self._tx() as con:
            responsable = ClienteDAO(con).obtener_por_id(id_cliente)
            if responsable is None:
                raise ErrorNegocio("El responsable seleccionado no existe.")
            for existente in MascotaDAO(con).listar():
                if (existente.responsable.id_cliente == id_cliente
                        and existente.nombre.strip().lower() == nombre.lower()
                        and existente.especie.strip().lower() == especie.lower()):
                    raise ErrorNegocio(
                        f"{responsable.nombre} {responsable.apellido} ya tiene registrada una mascota "
                        f"«{nombre}» ({especie}).")
            id_mascota = self._siguiente_id(con, "mascota")
            mascota = Mascota(id_mascota, nombre, especie, responsable,
                              (raza or "").strip(), fecha_nacimiento, (sexo or "").strip())
            MascotaDAO(con).crear(mascota)
            if abrir_historia:
                historia = HistoriaClinica(self._siguiente_id(con, "historia_clinica"),
                                           date.today(), "")
                mascota.asignar_historia_clinica(historia)
                HistoriaClinicaDAO(con).crear(historia, id_mascota)
        return id_mascota

    def modificar_mascota(self, id_mascota, nombre, especie, raza="",
                          fecha_nacimiento=None, sexo=""):
        """El responsable no cambia: la entidad no expone setter."""
        with self._tx() as con:
            dao = MascotaDAO(con)
            actual = dao.obtener_por_id(id_mascota)
            if actual is None:
                raise ErrorNegocio("La mascota no existe.")
            validar_fecha_nacimiento(fecha_nacimiento)
            nueva = Mascota(id_mascota, requerir_texto(nombre, "Nombre"),
                            requerir_texto(especie, "Especie"), actual.responsable,
                            (raza or "").strip(), fecha_nacimiento, (sexo or "").strip())
            dao.actualizar(nueva)

    def eliminar_mascota(self, id_mascota):
        """Elimina la mascota y su historia clínica si está vacía (sin atenciones)."""
        with self._tx() as con:
            historia_dao = HistoriaClinicaDAO(con)
            historia = historia_dao.obtener_por_mascota(id_mascota)
            try:
                if historia is not None and not AtencionDAO(con).listar_por_historia(historia.id_historia):
                    historia_dao.eliminar(historia.id_historia)
                if not MascotaDAO(con).eliminar(id_mascota):
                    raise ErrorNegocio("La mascota no existe.")
            except sqlite3.IntegrityError:
                raise ErrorNegocio("La mascota tiene turnos, vacunas o atenciones registradas y "
                                   "no puede eliminarse.") from None

    def listar_mascotas(self) -> list[dict]:
        with self._lectura() as con:
            filas = []
            for m in MascotaDAO(con).listar():
                r = m.responsable
                filas.append({
                    "id": m.id_mascota, "nombre": m.nombre, "especie": m.especie,
                    "raza": m.raza, "sexo": m.sexo,
                    "fecha_nacimiento": fmt_fecha_hora(m.fecha_nacimiento),
                    "id_responsable": r.id_cliente,
                    "responsable": f"{r.apellido}, {r.nombre}",
                    "etiqueta": f"{m.nombre} ({m.especie}) - {r.apellido}",
                })
            repetidas = Counter(f["etiqueta"] for f in filas)
            for f in filas:                       # distingue mascotas con igual nombre y responsable
                if repetidas[f["etiqueta"]] > 1:
                    f["etiqueta"] += f" [#{f['id']}]"
            return filas

    # ------------------------------------------------------------- clínicas
    def crear_clinica(self, nombre, direccion, telefono="") -> int:
        nombre = requerir_texto(nombre, "Nombre")
        direccion = requerir_texto(direccion, "Dirección")
        with self._tx() as con:
            id_clinica = self._siguiente_id(con, "clinica")
            ClinicaDAO(con).crear(Clinica(id_clinica, nombre, direccion, (telefono or "").strip()))
        return id_clinica

    def eliminar_clinica(self, id_clinica):
        """Sólo se elimina una clínica sin veterinarios ni remitos asociados."""
        with self._tx() as con:
            if ClinicaDAO(con).obtener_por_id(id_clinica) is None:
                raise ErrorNegocio("La clínica no existe.")
            if VeterinarioDAO(con).listar_por_clinica(id_clinica):
                raise ErrorNegocio("La clínica tiene veterinarios: elimínelos antes de eliminar la clínica.")
            try:
                ClinicaDAO(con).eliminar(id_clinica)
            except sqlite3.IntegrityError:
                raise ErrorNegocio("La clínica tiene remitos biológicos registrados y no puede "
                                   "eliminarse.") from None

    def listar_clinicas(self) -> list[dict]:
        with self._lectura() as con:
            return [
                {"id": c.id_clinica, "nombre": c.nombre, "direccion": c.direccion,
                 "telefono": c.telefono, "etiqueta": c.nombre}
                for c in ClinicaDAO(con).listar()
            ]

    # ---------------------------------------------------------- veterinarios
    def crear_veterinario(self, id_clinica, nombre, apellido, matricula, especialidad="") -> int:
        if id_clinica is None:
            raise ErrorNegocio("Seleccione la clínica del veterinario.")
        nombre = requerir_nombre(nombre, "Nombre")
        apellido = requerir_nombre(apellido, "Apellido")
        matricula = requerir_texto(matricula, "Matrícula")
        with self._tx() as con:
            clinica = ClinicaDAO(con).obtener_por_id(id_clinica)
            if clinica is None:
                raise ErrorNegocio("La clínica seleccionada no existe.")
            id_vet = self._siguiente_id(con, "veterinario")
            vet = Veterinario(id_vet, nombre, apellido, matricula, (especialidad or "").strip())
            clinica.agregar_veterinario(vet)
            VeterinarioDAO(con).crear(vet, id_clinica)
        return id_vet

    def eliminar_veterinario(self, id_veterinario):
        """Elimina al veterinario y su agenda si no tiene turnos ni atenciones registradas."""
        with self._tx() as con:
            if VeterinarioDAO(con).obtener_por_id(id_veterinario) is None:
                raise ErrorNegocio("El veterinario no existe.")
            if TurnoDAO(con).listar_por_veterinario(id_veterinario):
                raise ErrorNegocio("El veterinario tiene turnos registrados y no puede eliminarse.")
            AgendaMedicaDAO(con).eliminar_por_veterinario(id_veterinario)
            try:
                VeterinarioDAO(con).eliminar(id_veterinario)
            except sqlite3.IntegrityError:
                raise ErrorNegocio("El veterinario tiene atenciones registradas y no puede "
                                   "eliminarse.") from None

    def listar_veterinarios(self) -> list[dict]:
        with self._lectura() as con:
            filas = []
            for clinica in ClinicaDAO(con).listar():
                for v in VeterinarioDAO(con).listar_por_clinica(clinica.id_clinica):
                    filas.append({
                        "id": v.id_veterinario, "nombre": v.nombre, "apellido": v.apellido,
                        "matricula": v.matricula, "especialidad": v.especialidad,
                        "id_clinica": clinica.id_clinica, "clinica": clinica.nombre,
                        "etiqueta": f"{v.apellido}, {v.nombre} ({clinica.nombre})",
                    })
            return filas

    # --------------------------------------------------------------- agenda
    def guardar_agenda(self, id_veterinario, dias: set[DiaSemana], hora_desde, hora_hasta):
        """RN04: hora_hasta > hora_desde; una agenda semanal por veterinario."""
        if not dias:
            raise ErrorNegocio("Seleccione al menos un día de trabajo.")
        with self._tx() as con:
            if VeterinarioDAO(con).obtener_por_id(id_veterinario) is None:
                raise ErrorNegocio("El veterinario no existe.")
            agenda = AgendaMedica(set(dias), hora_desde, hora_hasta)
            dao = AgendaMedicaDAO(con)
            if dao.obtener_por_veterinario(id_veterinario) is None:
                dao.crear(agenda, id_veterinario)
            else:
                dao.actualizar(agenda, id_veterinario)

    def obtener_agenda(self, id_veterinario) -> dict | None:
        with self._lectura() as con:
            agenda = AgendaMedicaDAO(con).obtener_por_veterinario(id_veterinario)
            if agenda is None:
                return None
            return {"dias": sorted(agenda.dias_trabajo, key=lambda d: d.value),
                    "desde": agenda.hora_desde, "hasta": agenda.hora_hasta}

    # ---------------------------------------------------------------- turnos
    def agendar_turno(self, id_veterinario, id_mascota, inicio, fin, motivo="") -> int:
        """RN02/RN03: dentro de la agenda y sin superposición con turnos activos."""
        if inicio < ahora():
            raise ErrorNegocio("No se puede reservar un turno en una fecha u hora que ya pasó.")
        with self._tx() as con:
            vet = VeterinarioDAO(con).obtener_por_id(id_veterinario)
            if vet is None:
                raise ErrorNegocio("El veterinario no existe.")
            mascota = MascotaDAO(con).obtener_por_id(id_mascota)
            if mascota is None:
                raise ErrorNegocio("La mascota no existe.")
            agenda = AgendaMedicaDAO(con).obtener_por_veterinario(id_veterinario)
            existentes = TurnoDAO(con).listar_por_veterinario(id_veterinario)

            nuevo = Turno(self._siguiente_id(con, "turno"), inicio, fin, mascota,
                          (motivo or "").strip())
            motivo_rechazo = self._motivo_rechazo(agenda, existentes, nuevo)
            if motivo_rechazo:
                raise ErrorNegocio(motivo_rechazo)

            vet.asignar_agenda(agenda)
            for turno in existentes:           # reconstruye el estado en memoria
                try:
                    vet.agregar_turno(turno)
                except ValueError:
                    pass                        # turno histórico fuera de la agenda actual
            if not vet.puede_agendar(nuevo):
                raise ErrorNegocio("El turno no puede agendarse en ese horario.")
            vet.agregar_turno(nuevo)
            TurnoDAO(con).crear(nuevo, id_veterinario)
            return nuevo.id_turno

    @staticmethod
    def _motivo_rechazo(agenda, existentes, nuevo) -> str | None:
        if agenda is None:
            return "El veterinario no tiene agenda médica asignada."
        if not agenda.contiene(nuevo):
            return "El turno queda fuera de la agenda del veterinario (día u horario no laborable)."
        for otro in existentes:
            if otro.estado != EstadoTurno.CANCELADO and nuevo.se_superpone_con(otro):
                return (
                    "El turno se superpone con otro turno activo "
                    f"({fmt_fecha_hora(otro.fecha_hora_inicio)} - "
                    f"{otro.fecha_hora_fin.strftime('%H:%M')})."
                )
        return None

    def cambiar_estado_turno(self, id_turno, accion: str):
        """accion: 'confirmar', 'cancelar' o 'atender'."""
        acciones = {"confirmar": "confirmar", "cancelar": "cancelar",
                    "atender": "marcar_atendido"}
        if accion not in acciones:
            raise ErrorNegocio("Acción de turno desconocida.")
        with self._tx() as con:
            turno_dao = TurnoDAO(con)
            turno, id_vet = None, None
            for v in VeterinarioDAO(con).listar():
                for t in turno_dao.listar_por_veterinario(v.id_veterinario):
                    if t.id_turno == id_turno:
                        turno, id_vet = t, v.id_veterinario
            if turno is None:
                raise ErrorNegocio("El turno no existe.")
            getattr(turno, acciones[accion])()
            turno_dao.actualizar(turno, id_vet)

    def listar_turnos(self, solo_activos=False) -> list[dict]:
        with self._lectura() as con:
            turno_dao = TurnoDAO(con)
            filas = []
            for v in VeterinarioDAO(con).listar():
                for t in turno_dao.listar_por_veterinario(v.id_veterinario):
                    if solo_activos and t.estado == EstadoTurno.CANCELADO:
                        continue
                    filas.append({
                        "id": t.id_turno, "id_veterinario": v.id_veterinario,
                        "id_mascota": t.mascota.id_mascota, "fecha": t.fecha_hora_inicio.date(),
                        "veterinario": f"{v.apellido}, {v.nombre}",
                        "mascota": t.mascota.nombre,
                        "inicio": t.fecha_hora_inicio, "fin": t.fecha_hora_fin,
                        "inicio_txt": fmt_fecha_hora(t.fecha_hora_inicio),
                        "fin_txt": t.fecha_hora_fin.strftime("%H:%M"),
                        "estado": t.estado.name, "motivo": t.motivo,
                    })
            return sorted(filas, key=lambda f: f["inicio"])
