"""
Capa de servicios: coordina los casos de uso completos que usa la interfaz.

No agrega reglas de negocio: carga los objetos con los DAO, les pide la
operación a las clases del dominio (que deciden si se puede) y guarda el
resultado en una transacción. Cuando el dominio devuelve False, el servicio
averigua el motivo para poder mostrarle al usuario un mensaje claro.
"""
from contextlib import contextmanager
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
import secrets

from veterinaria.dominio.clinica.agenda_medica import AgendaMedica, DiaSemana
from veterinaria.dominio.clinica.atencion import Atencion, TipoAtencion
from veterinaria.dominio.clinica.cliente import Cliente
from veterinaria.dominio.clinica.clinica import Clinica
from veterinaria.dominio.clinica.comprobante_atencion import ComprobanteAtencion
from veterinaria.dominio.clinica.historia_clinica import HistoriaClinica
from veterinaria.dominio.clinica.mascota import Mascota
from veterinaria.dominio.clinica.turno import EstadoTurno, Turno
from veterinaria.dominio.clinica.veterinario import Veterinario
from veterinaria.dominio.laboratorio.muestra_biologica import MuestraBiologica
from veterinaria.dominio.laboratorio.orden_derivacion_laboratorio import OrdenDerivacionLaboratorio
from veterinaria.dominio.laboratorio.resultado_analisis import ResultadoAnalisis
from veterinaria.dominio.transporte.conservadora_isotermica import ConservadoraIsotermica
from veterinaria.dominio.transporte.envio import Envio, EstadoEnvio
from veterinaria.dominio.transporte.precinto_sanitario import PrecintoSanitario
from veterinaria.dominio.transporte.recepcion import Recepcion
from veterinaria.dominio.transporte.remito_biologico import EstadoRemito, RemitoBiologico
from veterinaria.dominio.vacunacion.aplicacion_vacuna import AplicacionVacuna
from veterinaria.dominio.vacunacion.vacuna import Vacuna
from veterinaria.patrones.strategy.generador_reportes import GeneradorReportes
from veterinaria.patrones.strategy.reporte_atenciones_derivaciones import ReporteAtencionesDerivaciones
from veterinaria.patrones.strategy.reporte_muestras_rechazadas import ReporteMuestrasRechazadas
from veterinaria.patrones.strategy.reporte_tiempos_transito_procesamiento import ReporteTiemposTransitoProcesamiento
from veterinaria.patrones.strategy.reporte_vacunas_pendientes import ReporteVacunasPendientes
from veterinaria.persistencia.agenda_medica_dao import AgendaMedicaDAO
from veterinaria.persistencia.aplicacion_vacuna_dao import AplicacionVacunaDAO
from veterinaria.persistencia.atencion_dao import AtencionDAO
from veterinaria.persistencia.cliente_dao import ClienteDAO
from veterinaria.persistencia.clinica_dao import ClinicaDAO
from veterinaria.persistencia.comprobante_atencion_dao import ComprobanteAtencionDAO
from veterinaria.persistencia.conservadora_isotermica_dao import ConservadoraIsotermicaDAO
from veterinaria.persistencia.envio_dao import EnvioDAO
from veterinaria.persistencia.historia_clinica_dao import HistoriaClinicaDAO
from veterinaria.persistencia.inicializar_bd import inicializar_bd
from veterinaria.persistencia.mascota_dao import MascotaDAO
from veterinaria.persistencia.muestra_biologica_dao import MuestraBiologicaDAO
from veterinaria.persistencia.orden_derivacion_laboratorio_dao import OrdenDerivacionLaboratorioDAO
from veterinaria.persistencia.precinto_sanitario_dao import PrecintoSanitarioDAO
from veterinaria.persistencia.recepcion_dao import RecepcionDAO
from veterinaria.persistencia.remito_biologico_dao import RemitoBiologicoDAO
from veterinaria.persistencia.resultado_analisis_dao import ResultadoAnalisisDAO
from veterinaria.persistencia.turno_dao import TurnoDAO
from veterinaria.persistencia.vacuna_dao import VacunaDAO
from veterinaria.persistencia.veterinario_dao import VeterinarioDAO

RUTA_BD = Path(__file__).resolve().parents[3] / "veterinaria.db"


NOMBRES_DIAS = {DiaSemana.LUNES: "Lunes", DiaSemana.MARTES: "Martes", DiaSemana.MIERCOLES: "Miércoles",
                DiaSemana.JUEVES: "Jueves", DiaSemana.VIERNES: "Viernes", DiaSemana.SABADO: "Sábado",
                DiaSemana.DOMINGO: "Domingo"}


def describir_agenda(agenda):
    dias = ", ".join(NOMBRES_DIAS[d] for d in sorted(agenda.dias_trabajo, key=lambda d: d.value))
    return f"{dias} de {agenda.hora_desde:%H:%M} a {agenda.hora_hasta:%H:%M}"


class ErrorOperacion(Exception):
    """La operación no se pudo hacer; el mensaje se muestra al usuario."""


class SistemaVeterinaria:
    def __init__(self, ruta=RUTA_BD):
        self.conexion = self._abrir_conexion(ruta)
        inicializar_bd(self.conexion)
        self.conexion.commit()

    @staticmethod
    def _abrir_conexion(ruta):
        """Igual que persistencia.conexion.abrir_conexion, pero usable desde varios hilos:
        la interfaz Flet atiende cada evento en un hilo distinto."""
        conexion = sqlite3.connect(ruta, check_same_thread=False)
        conexion.execute("PRAGMA foreign_keys = ON").close()
        conexion.row_factory = sqlite3.Row
        return conexion

    def cerrar(self):
        self.conexion.close()

    @contextmanager
    def _transaccion(self):
        """Confirma todo junto al final; si algo falla, deshace todo."""
        try:
            yield
            self.conexion.commit()
        except Exception:
            self.conexion.rollback()
            raise

    def _siguiente_id(self, tabla, columna):
        """Los DAO piden el id explícito: se usa el siguiente al mayor existente."""
        fila = self.conexion.execute(f"SELECT COALESCE(MAX({columna}), 0) + 1 FROM {tabla}").fetchone()
        return fila[0]

    # ------------------------------------------------------------ catálogos
    def clinicas(self):
        return ClinicaDAO(self.conexion).listar()

    def crear_clinica(self, nombre, direccion, telefono=""):
        clinica = Clinica(self._siguiente_id("clinica", "id_clinica"), nombre, direccion, telefono)
        with self._transaccion():
            ClinicaDAO(self.conexion).crear(clinica)
        return clinica

    def veterinarios(self, id_clinica=None):
        dao = VeterinarioDAO(self.conexion)
        return dao.listar_por_clinica(id_clinica) if id_clinica else dao.listar()

    def clinica_de_veterinario(self, id_veterinario):
        fila = self.conexion.execute("SELECT id_clinica FROM veterinario WHERE id_veterinario = ?",
                                     (id_veterinario,)).fetchone()
        return ClinicaDAO(self.conexion).obtener_por_id(fila[0]) if fila and fila[0] else None

    def crear_veterinario(self, id_clinica, nombre, apellido, matricula, especialidad, dias, hora_desde, hora_hasta):
        veterinario = Veterinario(self._siguiente_id("veterinario", "id_veterinario"), nombre, apellido,
                                  matricula, especialidad)
        agenda = AgendaMedica(set(dias), hora_desde, hora_hasta)
        veterinario.asignar_agenda(agenda)
        with self._transaccion():
            VeterinarioDAO(self.conexion).crear(veterinario, id_clinica)
            AgendaMedicaDAO(self.conexion).crear(agenda, veterinario.id_veterinario)
        return veterinario

    def agenda_de(self, id_veterinario):
        return AgendaMedicaDAO(self.conexion).obtener_por_veterinario(id_veterinario)

    def vacunas(self):
        return VacunaDAO(self.conexion).listar()

    def crear_vacuna(self, nombre, especie, obligatoria):
        vacuna = Vacuna(self._siguiente_id("vacuna", "id_vacuna"), nombre, especie, obligatoria)
        with self._transaccion():
            VacunaDAO(self.conexion).crear(vacuna)
        return vacuna

    def conservadoras(self):
        return ConservadoraIsotermicaDAO(self.conexion).listar()

    def crear_conservadora(self, codigo):
        conservadora = ConservadoraIsotermica(self._siguiente_id("conservadora_isotermica", "id_conservadora"),
                                              codigo)
        with self._transaccion():
            ConservadoraIsotermicaDAO(self.conexion).crear(conservadora)
        return conservadora

    # ------------------------------------------------------------ clientes y mascotas
    def clientes(self):
        return ClienteDAO(self.conexion).listar()

    def registrar_cliente(self, nombre, apellido, dni, telefono="", email=""):
        if not nombre.strip() or not apellido.strip() or not dni.strip():
            raise ErrorOperacion("Nombre, apellido y DNI son obligatorios.")
        if any(c.dni == dni.strip() for c in self.clientes()):
            raise ErrorOperacion(f"Ya existe un cliente con DNI {dni}.")
        cliente = Cliente(self._siguiente_id("cliente", "id_cliente"), nombre.strip(), apellido.strip(),
                          dni.strip(), telefono.strip(), email.strip())
        with self._transaccion():
            ClienteDAO(self.conexion).crear(cliente)
        return cliente

    def actualizar_cliente(self, id_cliente, nombre, apellido, dni, telefono="", email=""):
        if any(c.dni == dni.strip() and c.id_cliente != id_cliente for c in self.clientes()):
            raise ErrorOperacion(f"El DNI {dni} pertenece a otro cliente.")
        cliente = Cliente(id_cliente, nombre.strip(), apellido.strip(), dni.strip(), telefono.strip(), email.strip())
        with self._transaccion():
            ClienteDAO(self.conexion).actualizar(cliente)
        return cliente

    def mascotas(self):
        """Mascotas con sus vacunas aplicadas (para saber si están al día)."""
        return MascotaDAO(self.conexion).listar(cargar_aplicaciones=True)

    def mascota(self, id_mascota):
        mascota = MascotaDAO(self.conexion).obtener_por_id(id_mascota)
        for aplicacion in AplicacionVacunaDAO(self.conexion).listar_por_mascota(id_mascota):
            mascota.agregar_aplicacion_vacuna(aplicacion)
        historia = HistoriaClinicaDAO(self.conexion).obtener_por_mascota(id_mascota)
        if historia is not None:
            mascota.asignar_historia_clinica(historia)
            for atencion in AtencionDAO(self.conexion).listar_por_historia(historia.id_historia):
                historia._agregar_atencion(atencion)
        return mascota

    def registrar_mascota(self, id_cliente, nombre, especie, raza="", fecha_nacimiento=None, sexo=""):
        if not id_cliente:
            raise ErrorOperacion("Toda mascota debe tener un responsable: elegí un cliente.")
        if not nombre.strip() or not especie.strip():
            raise ErrorOperacion("Nombre y especie son obligatorios.")
        responsable = ClienteDAO(self.conexion).obtener_por_id(id_cliente)
        mascota = Mascota(self._siguiente_id("mascota", "id_mascota"), nombre.strip(), especie.strip(),
                          responsable, raza.strip(), fecha_nacimiento, sexo)
        # cada mascota nueva abre su historia clínica
        historia = HistoriaClinica(self._siguiente_id("historia_clinica", "id_historia"), date.today())
        mascota.asignar_historia_clinica(historia)
        with self._transaccion():
            MascotaDAO(self.conexion).crear(mascota)
            HistoriaClinicaDAO(self.conexion).crear(historia, mascota.id_mascota)
        return mascota

    def vacunas_pendientes(self, mascota, fecha=None):
        return mascota.obtener_vacunas_pendientes(self.vacunas(), fecha or date.today())

    def aplicar_vacuna(self, id_mascota, id_vacuna, fecha_aplicacion, fecha_proxima_dosis=None):
        vacuna = VacunaDAO(self.conexion).obtener_por_id(id_vacuna)
        mascota = self.mascota(id_mascota)
        if vacuna.especie != mascota.especie:
            raise ErrorOperacion(f"La vacuna {vacuna.nombre} es para {vacuna.especie}, no para {mascota.especie}.")
        try:
            aplicacion = AplicacionVacuna(self._siguiente_id("aplicacion_vacuna", "id_aplicacion"), vacuna,
                                          fecha_aplicacion, fecha_proxima_dosis)
        except ValueError as error:
            raise ErrorOperacion(str(error))
        with self._transaccion():
            AplicacionVacunaDAO(self.conexion).crear(aplicacion, id_mascota)
        return aplicacion

    # ------------------------------------------------------------ turnos
    def _veterinario_con_turnos(self, id_veterinario):
        veterinario = VeterinarioDAO(self.conexion).obtener_por_id(id_veterinario)
        agenda = self.agenda_de(id_veterinario)
        if agenda is not None:
            veterinario.asignar_agenda(agenda)
        turnos = TurnoDAO(self.conexion).listar_por_veterinario(id_veterinario)
        # los cancelados primero: así no chocan con los activos al volver a cargarlos
        for turno in sorted(turnos, key=lambda t: t.estado != EstadoTurno.CANCELADO):
            veterinario._turnos.append(turno)
        return veterinario

    def turnos(self, id_veterinario):
        return sorted(TurnoDAO(self.conexion).listar_por_veterinario(id_veterinario),
                      key=lambda t: t.fecha_hora_inicio)

    def reservar_turno(self, id_veterinario, id_mascota, inicio, minutos, motivo=""):
        veterinario = self._veterinario_con_turnos(id_veterinario)
        mascota = MascotaDAO(self.conexion).obtener_por_id(id_mascota)
        turno = Turno(self._siguiente_id("turno", "id_turno"), inicio, inicio + timedelta(minutes=minutos),
                      mascota, motivo)
        if not veterinario.puede_agendar(turno):
            agenda = veterinario.obtener_agenda()
            if agenda is None:
                raise ErrorOperacion("El veterinario no tiene agenda asignada.")
            if not agenda.contiene(turno):
                raise ErrorOperacion(f"El turno está fuera de la agenda del veterinario ({describir_agenda(agenda)}).")
            raise ErrorOperacion("El turno se superpone con otro turno del veterinario.")
        veterinario.agregar_turno(turno)
        with self._transaccion():
            TurnoDAO(self.conexion).crear(turno, id_veterinario)
        return turno

    def cambiar_estado_turno(self, id_veterinario, id_turno, accion):
        """accion: 'confirmar' o 'cancelar' (lo valida el propio Turno)."""
        turno = TurnoDAO(self.conexion).obtener_por_id(id_turno)
        try:
            getattr(turno, accion)()
        except ValueError as error:
            raise ErrorOperacion(str(error))
        with self._transaccion():
            TurnoDAO(self.conexion).actualizar(turno, id_veterinario)
        return turno

    # ------------------------------------------------------------ atenciones
    def atenciones(self):
        """[(atención, mascota)] de todas las historias clínicas, las más recientes primero."""
        resultado = []
        for mascota in MascotaDAO(self.conexion).listar():
            historia = HistoriaClinicaDAO(self.conexion).obtener_por_mascota(mascota.id_mascota)
            if historia is None:
                continue
            for atencion in AtencionDAO(self.conexion).listar_por_historia(historia.id_historia):
                atencion._ordenes_derivacion = OrdenDerivacionLaboratorioDAO(self.conexion).listar_por_atencion(
                    atencion.id_atencion)
                resultado.append((atencion, mascota))
        return sorted(resultado, key=lambda par: par[0].fecha_hora, reverse=True)

    def registrar_atencion(self, id_mascota, id_veterinario, tipo, motivo, diagnostico, fecha_hora,
                           id_turno=None):
        if not motivo.strip():
            raise ErrorOperacion("El motivo de la atención es obligatorio.")
        mascota = self.mascota(id_mascota)
        veterinario = VeterinarioDAO(self.conexion).obtener_por_id(id_veterinario)
        atencion = Atencion(self._siguiente_id("atencion", "id_atencion"), fecha_hora, TipoAtencion(tipo),
                            motivo.strip(), veterinario, diagnostico.strip())
        # RN05: la mascota sólo registra la atención si tiene las vacunas obligatorias al día
        if not mascota.registrar_atencion(atencion, self.vacunas()):
            pendientes = self.vacunas_pendientes(mascota, fecha_hora.date())
            if pendientes:
                raise ErrorOperacion(
                    f"{mascota.nombre} tiene vacunas obligatorias pendientes: "
                    f"{', '.join(v.nombre for v in pendientes)}. Aplicalas primero desde la pantalla Mascotas.")
            raise ErrorOperacion("No se pudo registrar la atención en la historia clínica.")
        turno = TurnoDAO(self.conexion).obtener_por_id(id_turno) if id_turno else None
        if turno is not None:
            if turno.estado == EstadoTurno.PENDIENTE:
                turno.confirmar()
            turno.marcar_atendido()
        with self._transaccion():
            AtencionDAO(self.conexion).crear(atencion, mascota.obtener_historia_clinica().id_historia)
            if turno is not None:
                TurnoDAO(self.conexion).actualizar(turno, id_veterinario)
        return atencion

    def emitir_comprobante(self, id_atencion, fecha_emision):
        dao = ComprobanteAtencionDAO(self.conexion)
        if dao.obtener_por_atencion(id_atencion) is not None:
            raise ErrorOperacion("Esa atención ya tiene un comprobante emitido.")
        atencion = AtencionDAO(self.conexion).obtener_por_id(id_atencion)
        comprobante = ComprobanteAtencion(self._siguiente_id("comprobante_atencion", "id_comprobante"),
                                          atencion, fecha_emision)
        with self._transaccion():
            dao.crear(comprobante)
        return comprobante

    def comprobante_de(self, id_atencion):
        return ComprobanteAtencionDAO(self.conexion).obtener_por_atencion(id_atencion)

    # ------------------------------------------------------------ órdenes y muestras
    def emitir_orden(self, id_atencion, estudio, tipo_muestra, fecha_hora, observaciones=""):
        if not estudio.strip() or not tipo_muestra.strip():
            raise ErrorOperacion("Indicá el estudio solicitado y el tipo de muestra.")
        orden = OrdenDerivacionLaboratorio(self._siguiente_id("orden_derivacion_laboratorio", "id_orden"),
                                           fecha_hora, estudio.strip(), observaciones)
        # RN06: la muestra nace en estado EXTRAIDA
        muestra = MuestraBiologica(self._siguiente_id("muestra_biologica", "id_muestra"), tipo_muestra.strip(),
                                   fecha_hora)
        orden.agregar_muestra(muestra)
        orden.iniciar_proceso()
        with self._transaccion():
            OrdenDerivacionLaboratorioDAO(self.conexion).crear(orden, id_atencion)
            MuestraBiologicaDAO(self.conexion).crear(muestra, orden.id_orden)
        return orden, muestra

    def muestras(self):
        """[(muestra, orden, atención, mascota)] de todas las órdenes."""
        resultado = []
        for atencion, mascota in self.atenciones():
            for orden in atencion.obtener_ordenes_derivacion():
                for muestra in MuestraBiologicaDAO(self.conexion).listar_por_orden(orden.id_orden):
                    resultado.append((muestra, orden, atencion, mascota))
        return sorted(resultado, key=lambda f: f[0].id_muestra, reverse=True)

    def muestras_sin_remito(self):
        ids = {f[0] for f in self.conexion.execute(
            "SELECT id_muestra FROM muestra_biologica WHERE id_remito IS NULL").fetchall()}
        return [f for f in self.muestras() if f[0].id_muestra in ids and f[0].estado.obtener_nombre() == "EXTRAIDA"]

    def muestra(self, id_muestra):
        return MuestraBiologicaDAO(self.conexion).obtener_por_id(id_muestra)

    def resultado_de(self, id_muestra):
        return ResultadoAnalisisDAO(self.conexion).obtener_por_muestra(id_muestra)

    # ------------------------------------------------------------ remitos, envíos y recepción
    def remitos(self):
        return sorted(RemitoBiologicoDAO(self.conexion).listar(), key=lambda r: r.id_remito, reverse=True)

    def envio_de(self, id_remito):
        return EnvioDAO(self.conexion).obtener_por_remito(id_remito)

    def empaquetar(self, id_clinica, id_conservadora, ids_muestras, fecha_hora, observaciones=""):
        if not ids_muestras:
            raise ErrorOperacion("Elegí al menos una muestra para empaquetar.")
        clinica = ClinicaDAO(self.conexion).obtener_por_id(id_clinica)
        conservadora = ConservadoraIsotermicaDAO(self.conexion).obtener_por_id(id_conservadora)
        if not conservadora.esta_disponible():
            raise ErrorOperacion(f"La conservadora {conservadora.codigo} está en uso.")
        remito = RemitoBiologico(self._siguiente_id("remito_biologico", "id_remito"), clinica, conservadora,
                                 fecha_hora, observaciones)
        remito_dao = RemitoBiologicoDAO(self.conexion)
        with self._transaccion():
            remito_dao.crear(remito)
            for id_muestra in ids_muestras:
                muestra = MuestraBiologicaDAO(self.conexion).obtener_por_id(id_muestra)
                # RN07: al agregarla al remito, la muestra pasa a EMPAQUETADA (lo decide su State)
                if not remito.agregar_muestra(muestra, fecha_hora, "Empaquetada en el remito"):
                    raise ErrorOperacion(f"La muestra {id_muestra} no se puede empaquetar "
                                         f"(está {muestra.estado.obtener_nombre()} o la fecha es anterior a la extracción).")
                remito_dao.guardar_muestra_asociada(remito, muestra)
            precinto = PrecintoSanitario(self._siguiente_id("precinto_sanitario", "id_precinto"),
                                         f"PS-{secrets.token_hex(3).upper()}")
            remito.asignar_precinto(precinto)
            PrecintoSanitarioDAO(self.conexion).crear(precinto, remito.id_remito)
        return remito

    def despachar(self, id_remito, fecha_hora, observaciones=""):
        remito = RemitoBiologicoDAO(self.conexion).obtener_por_id(id_remito)
        if EnvioDAO(self.conexion).obtener_por_remito(id_remito) is not None:
            raise ErrorOperacion("Ese remito ya fue despachado.")
        envio = Envio(self._siguiente_id("envio", "id_envio"), remito, observaciones)
        envio_dao = EnvioDAO(self.conexion)
        with self._transaccion():
            envio_dao.crear(envio)
            # RN08/RN09: el remito valida conservadora, precinto y muestras; las muestras pasan a EN_TRANSITO
            if not envio.iniciar(fecha_hora):
                raise ErrorOperacion("El remito no se puede despachar: necesita conservadora, precinto intacto y "
                                     "al menos una muestra, y la fecha no puede ser anterior al empaquetado.")
            envio_dao.guardar_despacho(envio)
        return envio

    def registrar_llegada(self, id_remito, fecha_hora):
        envio = EnvioDAO(self.conexion).obtener_por_remito(id_remito)
        if envio is None:
            raise ErrorOperacion("Ese remito todavía no fue despachado.")
        if not envio.registrar_llegada(fecha_hora):
            raise ErrorOperacion("No se pudo registrar la llegada: el envío no está en tránsito o la fecha es "
                                 "anterior a la salida.")
        with self._transaccion():
            EnvioDAO(self.conexion).actualizar(envio)
        return envio

    def recibir(self, id_remito, fecha_hora, precinto_intacto, observaciones=""):
        envio = EnvioDAO(self.conexion).obtener_por_remito(id_remito)
        if envio is None or envio.estado != EstadoEnvio.ENTREGADO:
            raise ErrorOperacion("Primero registrá la llegada del envío al laboratorio.")
        if RecepcionDAO(self.conexion).obtener_por_envio(envio.id_envio) is not None:
            raise ErrorOperacion("Ese remito ya fue recibido.")
        remito = envio.remito
        if not precinto_intacto:
            remito.obtener_precinto().marcar_roto()
        recepcion = Recepcion(self._siguiente_id("recepcion", "id_recepcion"), envio, fecha_hora, observaciones)
        # RN10-RN12: la recepción verifica el precinto; intacto -> RECIBIDA, roto -> RECHAZADA
        if not recepcion.procesar_recepcion():
            raise ErrorOperacion("No se pudo procesar la recepción: la fecha no puede ser anterior a la llegada.")
        with self._transaccion():
            RecepcionDAO(self.conexion).guardar_recepcion(recepcion)
            # la conservadora vuelve a estar disponible para otro remito
            if remito.conservadora.liberar():
                ConservadoraIsotermicaDAO(self.conexion).actualizar(remito.conservadora)
        return recepcion

    def registrar_resultado(self, id_muestra, fecha_hora, texto, observaciones=""):
        if not texto.strip():
            raise ErrorOperacion("Escribí el resultado del análisis.")
        muestra = MuestraBiologicaDAO(self.conexion).obtener_por_id(id_muestra)
        resultado = ResultadoAnalisis(self._siguiente_id("resultado_analisis", "id_resultado"), muestra,
                                      fecha_hora, texto.strip(), observaciones)
        # RN12/RN13: sólo una muestra RECIBIDA pasa a ANALIZADA; una RECHAZADA no se puede procesar
        if not resultado.registrar_resultado():
            estado = muestra.estado.obtener_nombre()
            if estado == "RECHAZADA":
                raise ErrorOperacion("La muestra fue RECHAZADA porque el precinto llegó roto: no puede analizarse.")
            if estado != "RECIBIDA":
                raise ErrorOperacion(f"La muestra está {estado}: sólo se analizan muestras RECIBIDAS.")
            raise ErrorOperacion("La fecha del resultado no puede ser anterior a la recepción.")
        with self._transaccion():
            ResultadoAnalisisDAO(self.conexion).guardar_resultado(resultado)
            orden = self._orden_de_muestra(id_muestra)
            if orden is not None and all(m.estado.obtener_nombre() == "ANALIZADA"
                                         for m in MuestraBiologicaDAO(self.conexion).listar_por_orden(orden.id_orden)):
                orden.completar()
                OrdenDerivacionLaboratorioDAO(self.conexion).actualizar(orden)
        return resultado

    def _orden_de_muestra(self, id_muestra):
        fila = self.conexion.execute("SELECT id_orden FROM muestra_biologica WHERE id_muestra = ?",
                                     (id_muestra,)).fetchone()
        return OrdenDerivacionLaboratorioDAO(self.conexion).obtener_por_id(fila[0]) if fila else None

    # ------------------------------------------------------------ reportes (patrón Strategy del grupo)
    def reporte(self, clave, fecha_referencia=None):
        if clave == "atenciones":
            atenciones = AtencionDAO(self.conexion).listar(cargar_ordenes=True)
            estrategia = ReporteAtencionesDerivaciones(atenciones)
        elif clave == "rechazadas":
            estrategia = ReporteMuestrasRechazadas(RemitoBiologicoDAO(self.conexion).listar())
        elif clave == "vacunas":
            estrategia = ReporteVacunasPendientes(self.mascotas(), self.vacunas(), fecha_referencia or date.today())
        elif clave == "tiempos":
            envios = [e for e in (self.envio_de(r.id_remito) for r in RemitoBiologicoDAO(self.conexion).listar())
                      if e is not None]
            estrategia = ReporteTiemposTransitoProcesamiento(envios)
        else:
            raise ErrorOperacion(f"Reporte desconocido: {clave}")
        return GeneradorReportes(estrategia).generar_reporte()

