"""Atenciones, órdenes de derivación y comprobantes."""
from datetime import datetime

import flet as ft

from veterinaria.dominio.clinica.atencion import TipoAtencion
from veterinaria.interfaz.componentes import (accion_segura, avisar, titulo, tarjeta, tabla, cargar_filas,
                                              contenedor_tabla, desplegable, recargar_opciones, campo,
                                              campo_fecha_hora, valor_entero, boton, leer_fecha_hora, fh)

TIPOS_MUESTRA = ["Sangre", "Orina", "Heces", "Hisopado", "Tejido"]


class VistaAtencion:
    def __init__(self, page, sistema):
        self.page, self.sistema = page, sistema
        self.mascota = desplegable("Mascota", [(m.id_mascota, f"{m.nombre} ({m.especie}) · {m.responsable.apellido}")
                                               for m in sistema.mascotas()], 340,
                                   on_select=accion_segura(page, self.cargar_turnos))
        self.veterinario = desplegable("Veterinario", [(v.id_veterinario, f"{v.apellido}, {v.nombre}")
                                                       for v in sistema.veterinarios()], 260,
                                       on_select=accion_segura(page, self.cargar_turnos))
        self.turno = desplegable("Turno (opcional)", [], 260)
        self.tipo = desplegable("Tipo", [(t.value, t.value.capitalize()) for t in TipoAtencion], 160)
        self.tipo.value = TipoAtencion.CONSULTA.value
        self.fecha_hora = campo_fecha_hora()
        self.motivo = campo("Motivo", 340)
        self.diagnostico = campo("Diagnóstico", 340)
        # orden de derivación
        self.atencion_orden = desplegable("Atención", [], 480)
        self.estudio = campo("Estudio solicitado", 260)
        self.tipo_muestra = desplegable("Tipo de muestra", [(t, t) for t in TIPOS_MUESTRA], 180)
        self.obs_orden = campo("Observaciones", 300)
        # comprobante
        self.atencion_comprobante = desplegable("Atención sin comprobante", [], 480)
        self.tabla = tabla(["Fecha", "Mascota", "Tipo", "Motivo", "Diagnóstico", "Veterinario", "Derivaciones",
                            "Comprobante"])

    def build(self):
        self.refrescar()
        return ft.Column([
            titulo("Atención clínica", "La atención sólo se registra si la mascota tiene las vacunas obligatorias al día"),
            tarjeta(ft.Column([
                ft.Row([self.mascota, self.veterinario, self.turno], wrap=True),
                ft.Row([self.tipo, self.fecha_hora], wrap=True),
                ft.Row([self.motivo, self.diagnostico], wrap=True),
                boton("Registrar atención", ft.Icons.SAVE, accion_segura(self.page, self.registrar)),
            ]), "Nueva atención"),
            tarjeta(ft.Column([
                self.atencion_orden,
                ft.Row([self.estudio, self.tipo_muestra, self.obs_orden], wrap=True),
                boton("Emitir orden y registrar la muestra", ft.Icons.SCIENCE,
                      accion_segura(self.page, self.emitir_orden)),
            ]), "Orden de derivación al laboratorio"),
            tarjeta(ft.Column([
                self.atencion_comprobante,
                boton("Emitir comprobante", ft.Icons.RECEIPT_LONG, accion_segura(self.page, self.emitir_comprobante)),
            ]), "Comprobante de atención"),
            tarjeta(contenedor_tabla(self.tabla, 360), "Atenciones registradas"),
        ], spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    def refrescar(self):
        atenciones = self.sistema.atenciones()
        opciones = [(a.id_atencion, f"#{a.id_atencion} · {fh(a.fecha_hora)} · {m.nombre} · {a.motivo}")
                    for a, m in atenciones]
        recargar_opciones(self.atencion_orden, opciones)
        con_comprobante = {a.id_atencion for a, _ in atenciones if self.sistema.comprobante_de(a.id_atencion)}
        recargar_opciones(self.atencion_comprobante, [o for o in opciones if o[0] not in con_comprobante])
        cargar_filas(self.tabla, [[fh(a.fecha_hora), m.nombre, a.tipo.value, a.motivo, a.diagnostico,
                                   f"{a.veterinario.apellido}", len(a.obtener_ordenes_derivacion()),
                                   "Emitido" if a.id_atencion in con_comprobante else "-"] for a, m in atenciones])

    def cargar_turnos(self, e):
        if not (self.mascota.value and self.veterinario.value):
            return
        turnos = [t for t in self.sistema.turnos(int(self.veterinario.value))
                  if t.mascota.id_mascota == int(self.mascota.value) and t.estado.name in ("PENDIENTE", "CONFIRMADO")]
        recargar_opciones(self.turno, [("", "Sin turno")] + [(t.id_turno, fh(t.fecha_hora_inicio)) for t in turnos])

    def registrar(self, e):
        atencion = self.sistema.registrar_atencion(
            valor_entero(self.mascota, "la mascota"), valor_entero(self.veterinario, "el veterinario"),
            self.tipo.value, self.motivo.value or "", self.diagnostico.value or "",
            leer_fecha_hora(self.fecha_hora.value), int(self.turno.value) if self.turno.value else None)
        avisar(self.page, f"Atención #{atencion.id_atencion} registrada en la historia clínica.")
        self.motivo.value = self.diagnostico.value = ""
        self.refrescar()
        self.atencion_orden.value = self.atencion_comprobante.value = str(atencion.id_atencion)
        self.cargar_turnos(None)

    def emitir_orden(self, e):
        if not self.tipo_muestra.value:
            avisar(self.page, "Elegí el tipo de muestra.", error=True)
            return
        orden, muestra = self.sistema.emitir_orden(valor_entero(self.atencion_orden, "la atención"),
                                                   self.estudio.value or "", self.tipo_muestra.value,
                                                   datetime.now().replace(second=0, microsecond=0),
                                                   self.obs_orden.value or "")
        avisar(self.page, f"Orden #{orden.id_orden} emitida. Muestra #{muestra.id_muestra} en estado "
                          f"{muestra.estado.obtener_nombre()}.")
        self.estudio.value = self.obs_orden.value = ""
        self.refrescar()

    def emitir_comprobante(self, e):
        comprobante = self.sistema.emitir_comprobante(valor_entero(self.atencion_comprobante, "la atención"),
                                                      datetime.now().replace(second=0, microsecond=0))
        avisar(self.page, f"Comprobante #{comprobante.id_comprobante} emitido.")
        self.refrescar()
