"""Ventana principal: menú lateral y área de contenido."""
import flet as ft

from veterinaria.interfaz.componentes import COLOR_PRIMARIO
from veterinaria.interfaz.vistas.atencion import VistaAtencion
from veterinaria.interfaz.vistas.clientes import VistaClientes, VistaMascotas
from veterinaria.interfaz.vistas.laboratorio import VistaLaboratorio
from veterinaria.interfaz.vistas.reportes import VistaReportes
from veterinaria.interfaz.vistas.turnos import VistaTurnos
from veterinaria.servicios.sistema import SistemaVeterinaria


class AppVeterinaria:
    SECCIONES = [
        ("Clientes", ft.Icons.PEOPLE_OUTLINE, ft.Icons.PEOPLE, VistaClientes),
        ("Mascotas", ft.Icons.PETS_OUTLINED, ft.Icons.PETS, VistaMascotas),
        ("Turnos", ft.Icons.EVENT_OUTLINED, ft.Icons.EVENT, VistaTurnos),
        ("Atención", ft.Icons.MEDICAL_SERVICES_OUTLINED, ft.Icons.MEDICAL_SERVICES, VistaAtencion),
        ("Laboratorio", ft.Icons.BIOTECH_OUTLINED, ft.Icons.BIOTECH, VistaLaboratorio),
        ("Reportes", ft.Icons.BAR_CHART_OUTLINED, ft.Icons.BAR_CHART, VistaReportes),
    ]

    def __init__(self, page: ft.Page, sistema: SistemaVeterinaria):
        self.page = page
        self.sistema = sistema
        page.title = "Veterinaria — Red de clínicas y laboratorio central"
        page.theme = ft.Theme(color_scheme_seed=COLOR_PRIMARIO)
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = "#F4F7FA"
        page.padding = 0
        page.window.width = 1360
        page.window.height = 860
        self.contenido = ft.Container(expand=True, padding=20)
        self.menu = ft.NavigationRail(
            selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=96,
            leading=ft.Container(ft.Column([ft.Icon(ft.Icons.PETS, size=34, color=COLOR_PRIMARIO),
                                            ft.Text("Veterinaria", weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO)],
                                           horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                 padding=ft.Padding.only(top=16, bottom=12)),
            destinations=[ft.NavigationRailDestination(icon=i, selected_icon=s, label=n)
                          for n, i, s, _ in self.SECCIONES],
            on_change=lambda e: self.mostrar(e.control.selected_index), bgcolor=ft.Colors.WHITE)

    def build(self):
        self.mostrar(0)
        return ft.Row([self.menu, ft.VerticalDivider(width=1), self.contenido], expand=True, spacing=0)

    def mostrar(self, indice):
        vista = self.SECCIONES[indice][3](self.page, self.sistema)    # cada vez con datos frescos
        self.contenido.content = vista.build()
