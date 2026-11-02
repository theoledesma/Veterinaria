"""
Interfaz gráfica del sistema (Flet).

    python main.py          -> aplicación de escritorio (desde la raíz del repositorio)
    python main.py --web    -> se abre en el navegador

Si veterinaria.db no existe, se crea con datos de demostración.
"""
import sys

import flet as ft

from veterinaria import datos_demo
from veterinaria.interfaz.app import AppVeterinaria
from veterinaria.servicios.sistema import RUTA_BD, SistemaVeterinaria


def iniciar(page: ft.Page):
    page.add(AppVeterinaria(page, SistemaVeterinaria()).build())


def main():
    if not RUTA_BD.exists():
        print("Creando base de datos con datos de demostración...")
        datos_demo.cargar()
    if "--web" in sys.argv:
        ft.run(iniciar, view=ft.AppView.WEB_BROWSER, port=8551, no_cdn=True)
    else:
        ft.run(iniciar)


if __name__ == "__main__":
    main()
