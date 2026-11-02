"""Los cuatro reportes del grupo (patrón Strategy), mostrados en pantalla."""
from datetime import date, datetime, timedelta

import flet as ft

from veterinaria.interfaz.componentes import (accion_segura, titulo, tarjeta, tabla, desplegable, campo_fecha,
                                              boton, leer_fecha, fh)

REPORTES = [
    ("atenciones", "Atenciones y derivaciones"),
    ("rechazadas", "Muestras rechazadas"),
    ("vacunas", "Vacunas pendientes"),
    ("tiempos", "Tiempos de tránsito y procesamiento"),
]

# columnas a mostrar de cada reporte: (clave del diccionario que devuelve la estrategia, título)
COLUMNAS = {
    "atenciones": [("id_atencion", "Atención"), ("fecha_hora", "Fecha"), ("tipo", "Tipo"),
                   ("veterinario", "Veterinario"), ("cantidad_derivaciones", "Derivaciones"),
                   ("derivaciones", "Estudios solicitados")],
    "rechazadas": [("id_muestra", "Muestra"), ("tipo_muestra", "Tipo"), ("fecha_rechazo", "Fecha de rechazo"),
                   ("id_remito", "Remito"), ("clinica_origen", "Clínica de origen"), ("estado_precinto", "Precinto")],
    "vacunas": [("mascota", "Mascota"), ("especie", "Especie"), ("responsable", "Responsable"), ("vacuna", "Vacuna"),
                ("fecha_referencia", "Fecha de referencia")],
    "tiempos": [("cantidad_envios_con_transito", "Envíos con tránsito"), ("tiempo_promedio_transito", "Tránsito promedio"),
                ("cantidad_muestras_procesadas", "Muestras procesadas"),
                ("tiempo_promedio_procesamiento", "Procesamiento promedio")],
}


def mostrar(valor):
    if isinstance(valor, datetime):
        return fh(valor)
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, timedelta):
        minutos = int(valor.total_seconds() // 60)
        return f"{minutos // 60} h {minutos % 60:02d} min"
    if isinstance(valor, list):       # derivaciones de una atención
        return ", ".join(f"{d['estudio_solicitado']} ({d['estado']})" for d in valor) or "-"
    return "-" if valor is None else valor


class VistaReportes:
    def __init__(self, page, sistema):
        self.page, self.sistema = page, sistema
        self.tipo = desplegable("Reporte", REPORTES, 360)
        self.tipo.value = "atenciones"
        self.fecha = campo_fecha("Fecha de referencia (vacunas)", 240, date.today())
        self.resultado = ft.Column(spacing=14)

    def build(self):
        return ft.Column([
            titulo("Reportes", "Generados con GeneradorReportes y las estrategias del patrón Strategy"),
            tarjeta(ft.Column([
                ft.Row([self.tipo, self.fecha], wrap=True),
                boton("Generar reporte", ft.Icons.TABLE_VIEW, accion_segura(self.page, self.generar)),
            ]), "Parámetros"),
            self.resultado,
        ], spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    def generar(self, e):
        clave = self.tipo.value or "atenciones"
        filas = self.sistema.reporte(clave, leer_fecha(self.fecha.value) if clave == "vacunas" else None)
        columnas = COLUMNAS[clave]
        nombre = dict(REPORTES)[clave]
        if not filas:
            self.resultado.controls = [tarjeta(ft.Text("El reporte no tiene datos.", italic=True), nombre)]
            return
        datos = tabla([t for _, t in columnas], [[mostrar(fila.get(c)) for c, _ in columnas] for fila in filas])
        self.resultado.controls = [tarjeta(ft.Column([ft.Text(f"{len(filas)} fila(s)", size=12),
                                                      ft.Row([datos], scroll=ft.ScrollMode.AUTO)]), nombre)]
