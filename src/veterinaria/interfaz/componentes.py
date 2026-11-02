"""Controles reutilizados por todas las pantallas."""
import re
import traceback
from datetime import datetime

import flet as ft

from veterinaria.servicios.sistema import ErrorOperacion

COLOR_PRIMARIO = "#1F5F8B"
# colores de los estados que usan las clases del dominio (State de la muestra, remito, turno, envío)
COLORES_ESTADO = {
    "EXTRAIDA": ft.Colors.BLUE_GREY_400, "EMPAQUETADA": ft.Colors.INDIGO_400, "EN_TRANSITO": ft.Colors.AMBER_700,
    "RECIBIDA": ft.Colors.TEAL_500, "ANALIZADA": ft.Colors.GREEN_600, "RECHAZADA": ft.Colors.RED_600,
    "GENERADO": ft.Colors.BLUE_GREY_400, "DESPACHADO": ft.Colors.AMBER_700, "RECIBIDO": ft.Colors.GREEN_600,
    "PENDIENTE": ft.Colors.BLUE_400, "CONFIRMADO": ft.Colors.INDIGO_400, "ATENDIDO": ft.Colors.GREEN_600,
    "CANCELADO": ft.Colors.GREY_500, "ENTREGADO": ft.Colors.TEAL_500, "INTACTO": ft.Colors.GREEN_600,
    "ROTO": ft.Colors.RED_600,
}


def avisar(page, texto, error=False):
    page.show_dialog(ft.SnackBar(ft.Text(texto, color=ft.Colors.WHITE),
                                 bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700, duration=4500))


def accion_segura(page, funcion):
    """Ejecuta una acción de la interfaz mostrando los errores de negocio como avisos."""
    def manejador(e=None):
        try:
            funcion(e)
        except (ErrorOperacion, ValueError) as ex:      # ValueError: validaciones de las clases del dominio
            avisar(page, str(ex), error=True)
        except Exception as ex:          # errores inesperados: se muestran sin cerrar la aplicación
            traceback.print_exc()
            avisar(page, f"Error inesperado: {ex}", error=True)
        finally:
            # al abrir un aviso Flet no siempre redibuja el resto de la pantalla: lo forzamos
            page.update()
    return manejador


def titulo(texto, subtitulo=""):
    controles = [ft.Text(texto, size=24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO)]
    if subtitulo:
        controles.append(ft.Text(subtitulo, size=13, color=ft.Colors.GREY_700))
    return ft.Column(controles, spacing=2)


def tarjeta(contenido, titulo_tarjeta=None, expand=False):
    controles = []
    if titulo_tarjeta:
        controles.append(ft.Text(titulo_tarjeta, size=16, weight=ft.FontWeight.W_600))
    controles.append(contenido)
    return ft.Container(ft.Column(controles, spacing=10, tight=True), padding=16, border_radius=10,
                        bgcolor=ft.Colors.WHITE, border=ft.Border.all(1, ft.Colors.BLUE_GREY_100), expand=expand)


def chip_estado(estado):
    return ft.Container(ft.Text(estado, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                        bgcolor=COLORES_ESTADO.get(estado, ft.Colors.GREY_600), border_radius=12,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2))


def celda(valor):
    if isinstance(valor, ft.Control):
        return ft.DataCell(valor)
    texto = re.sub(r"<[^>]+>", "", str(valor if valor is not None else ""))   # sin etiquetas HTML de los reportes
    return ft.DataCell(ft.Text(texto, size=12))


def tabla(columnas, filas=None):
    return ft.DataTable(
        columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.W_600, size=12)) for c in columnas],
        rows=[ft.DataRow([celda(v) for v in fila]) for fila in (filas or [])],
        heading_row_color=ft.Colors.BLUE_GREY_50, column_spacing=18, data_row_min_height=36,
        data_row_max_height=52, border=ft.Border.all(1, ft.Colors.BLUE_GREY_100), border_radius=8)


def cargar_filas(data_table, filas):
    data_table.rows = [ft.DataRow([celda(v) for v in fila]) for fila in filas]


def contenedor_tabla(data_table, alto=None):
    """Tabla con scroll horizontal y vertical."""
    return ft.Container(
        ft.Column([ft.Row([data_table], scroll=ft.ScrollMode.AUTO)], scroll=ft.ScrollMode.AUTO, expand=True),
        height=alto, expand=alto is None)


def desplegable(etiqueta, opciones, ancho=260, on_select=None):
    """opciones: lista de (clave, texto)."""
    return ft.Dropdown(label=etiqueta, width=ancho, enable_filter=True, editable=True, menu_height=320,
                       options=[ft.DropdownOption(key=str(k), text=t) for k, t in opciones], on_select=on_select)


def recargar_opciones(dropdown, opciones):
    dropdown.options = [ft.DropdownOption(key=str(k), text=t) for k, t in opciones]
    if dropdown.value not in {str(k) for k, _ in opciones}:
        dropdown.value = None


def campo(etiqueta, ancho=220, valor="", **kwargs):
    return ft.TextField(label=etiqueta, width=ancho, value=valor, dense=True, **kwargs)


# posición (cantidad de dígitos) -> separador que va antes del dígito siguiente
_SEPARADORES = {2: "/", 4: "/", 8: " ", 10: ":"}


def formatear_fecha(texto, anterior="", con_hora=False):
    """Máscara DD/MM/AAAA [HH:MM]: el usuario escribe sólo números y las barras se agregan solas.
    Si está borrando no se vuelve a agregar el separador, para que pueda corregir."""
    maximo = 12 if con_hora else 8
    digitos = re.sub(r"\D", "", texto or "")[:maximo]
    resultado = ""
    for i, d in enumerate(digitos):
        if i in _SEPARADORES:
            resultado += _SEPARADORES[i]
        resultado += d
    borrando = len(texto or "") < len(anterior or "")
    if not borrando and len(digitos) in _SEPARADORES and len(digitos) < maximo:
        resultado += _SEPARADORES[len(digitos)]
    return resultado


def campo_fecha(etiqueta="Fecha (DD/MM/AAAA)", ancho=200, valor=None, con_hora=False, **kwargs):
    """valor: date/datetime o None (vacío)."""
    formato = "%d/%m/%Y %H:%M" if con_hora else "%d/%m/%Y"
    texto = valor.strftime(formato) if valor else ""
    control = campo(etiqueta, ancho, texto, input_filter=ft.InputFilter(regex_string=r"[0-9/: ]"),
                    hint_text="DD/MM/AAAA HH:MM" if con_hora else "DD/MM/AAAA", **kwargs)
    control.data = texto       # último valor, para saber si el usuario está borrando

    def al_escribir(e):
        nuevo = formatear_fecha(control.value, control.data, con_hora)
        if nuevo != control.value:
            control.value = nuevo
            control.selection = ft.TextSelection(base_offset=len(nuevo), extent_offset=len(nuevo))
        control.data = nuevo
        control.update()

    control.on_change = al_escribir
    return control


def campo_fecha_hora(etiqueta="Fecha y hora (DD/MM/AAAA HH:MM)", ancho=250):
    return campo_fecha(etiqueta, ancho, datetime.now(), con_hora=True)


def valor_entero(dropdown, nombre):
    if not dropdown.value:
        raise ErrorOperacion(f"Seleccioná {nombre}.")
    return int(dropdown.value)


def boton(texto, icono, on_click, principal=True):
    if principal:
        return ft.FilledButton(texto, icon=icono, on_click=on_click)
    return ft.OutlinedButton(texto, icon=icono, on_click=on_click)


def leer_fecha(texto, nombre="la fecha"):
    try:
        return datetime.strptime((texto or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ErrorOperacion(f"Revisá {nombre}: el formato es DD/MM/AAAA.")


def leer_fecha_hora(texto, nombre="la fecha y hora"):
    try:
        return datetime.strptime((texto or "").strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        raise ErrorOperacion(f"Revisá {nombre}: el formato es DD/MM/AAAA HH:MM.")


def fh(valor):
    """datetime -> texto para mostrar."""
    return valor.strftime("%d/%m/%Y %H:%M") if valor else "-"


def f(valor):
    return valor.strftime("%d/%m/%Y") if valor else "-"
