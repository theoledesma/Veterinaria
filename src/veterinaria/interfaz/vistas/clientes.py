"""Clientes, mascotas, historia clínica y vacunas."""
from datetime import date, timedelta

import flet as ft

from veterinaria.interfaz.componentes import (accion_segura, avisar, titulo, tarjeta, tabla, cargar_filas,
                                              contenedor_tabla, desplegable, recargar_opciones, campo, campo_fecha,
                                              valor_entero, boton, leer_fecha, f, fh, COLOR_PRIMARIO)

ESPECIES = ["Perro", "Gato"]


class VistaClientes:
    def __init__(self, page, sistema):
        self.page, self.sistema = page, sistema
        self.id_edicion = None
        self.nombre = campo("Nombre")
        self.apellido = campo("Apellido")
        self.dni = campo("DNI", 140)
        self.telefono = campo("Teléfono", 160)
        self.email = campo("Email", 240)
        self.estado_form = ft.Text("Nuevo cliente", italic=True, color=ft.Colors.GREY_700)
        self.tabla = tabla(["DNI", "Apellido y nombre", "Teléfono", "Email", ""])

    def build(self):
        self.refrescar()
        return ft.Column([
            titulo("Clientes", "Responsables de las mascotas"),
            tarjeta(ft.Column([
                self.estado_form,
                ft.Row([self.nombre, self.apellido, self.dni], wrap=True),
                ft.Row([self.telefono, self.email], wrap=True),
                ft.Row([boton("Guardar", ft.Icons.SAVE, accion_segura(self.page, self.guardar)),
                        boton("Limpiar", ft.Icons.CLEAR, accion_segura(self.page, lambda e: self.limpiar()),
                              principal=False)]),
            ]), "Datos del cliente"),
            tarjeta(contenedor_tabla(self.tabla, 400), "Clientes registrados"),
        ], spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    def refrescar(self):
        filas = []
        for c in sorted(self.sistema.clientes(), key=lambda c: (c.apellido, c.nombre)):
            editar = ft.IconButton(ft.Icons.EDIT, tooltip="Editar",
                                   on_click=accion_segura(self.page, lambda e, c=c: self.editar(c)))
            filas.append([c.dni, f"{c.apellido}, {c.nombre}", c.telefono, c.email, editar])
        cargar_filas(self.tabla, filas)

    def guardar(self, e):
        datos = (self.nombre.value or "", self.apellido.value or "", self.dni.value or "",
                 self.telefono.value or "", self.email.value or "")
        if self.id_edicion:
            self.sistema.actualizar_cliente(self.id_edicion, *datos)
            avisar(self.page, "Cliente actualizado.")
        else:
            cliente = self.sistema.registrar_cliente(*datos)
            avisar(self.page, f"Cliente {cliente.apellido}, {cliente.nombre} registrado.")
        self.limpiar()

    def editar(self, c):
        self.id_edicion = c.id_cliente
        self.nombre.value, self.apellido.value, self.dni.value = c.nombre, c.apellido, c.dni
        self.telefono.value, self.email.value = c.telefono, c.email
        self.estado_form.value = f"Editando a {c.apellido}, {c.nombre}"

    def limpiar(self):
        self.id_edicion = None
        for control in (self.nombre, self.apellido, self.dni, self.telefono, self.email):
            control.value = ""
        self.estado_form.value = "Nuevo cliente"
        self.refrescar()


class VistaMascotas:
    def __init__(self, page, sistema):
        self.page, self.sistema = page, sistema
        self.nombre = campo("Nombre", 180)
        self.especie = desplegable("Especie", [(e, e) for e in ESPECIES], 150)
        self.raza = campo("Raza", 180)
        self.sexo = desplegable("Sexo", [("Macho", "Macho"), ("Hembra", "Hembra")], 130)
        self.nacimiento = campo_fecha("Fecha de nacimiento", 220)
        self.responsable = desplegable("Responsable *", [], 320)
        self.tabla = tabla(["Nombre", "Especie", "Raza", "Responsable", "Vacunas obligatorias", ""])

    def build(self):
        self.refrescar()
        return ft.Column([
            titulo("Mascotas", "Toda mascota tiene un cliente responsable (RN01) y abre su historia clínica"),
            tarjeta(ft.Column([
                ft.Row([self.nombre, self.especie, self.raza, self.sexo], wrap=True),
                ft.Row([self.nacimiento, self.responsable], wrap=True),
                boton("Registrar mascota", ft.Icons.SAVE, accion_segura(self.page, self.guardar)),
            ]), "Nueva mascota"),
            tarjeta(contenedor_tabla(self.tabla, 420), "Pacientes"),
        ], spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    def refrescar(self):
        recargar_opciones(self.responsable, [(c.id_cliente, f"{c.apellido}, {c.nombre} (DNI {c.dni})")
                                             for c in self.sistema.clientes()])
        filas = []
        for m in self.sistema.mascotas():
            pendientes = self.sistema.vacunas_pendientes(m)
            vacunas = ft.Text("Al día", color=ft.Colors.GREEN_700, size=12) if not pendientes else ft.Text(
                "Pendientes: " + ", ".join(v.nombre for v in pendientes), color=ft.Colors.RED_600, size=12)
            acciones = ft.Row([
                ft.IconButton(ft.Icons.VACCINES, tooltip="Vacunas", icon_color=COLOR_PRIMARIO,
                              on_click=accion_segura(self.page, lambda e, m=m: self.ver_vacunas(m.id_mascota))),
                ft.IconButton(ft.Icons.MEDICAL_INFORMATION, tooltip="Historia clínica", icon_color=COLOR_PRIMARIO,
                              on_click=accion_segura(self.page, lambda e, m=m: self.ver_historia(m.id_mascota))),
            ], spacing=0)
            r = m.responsable
            filas.append([m.nombre, m.especie, m.raza, f"{r.apellido}, {r.nombre}", vacunas, acciones])
        cargar_filas(self.tabla, filas)

    def guardar(self, e):
        id_cliente = int(self.responsable.value) if self.responsable.value else None
        nacimiento = leer_fecha(self.nacimiento.value, "la fecha de nacimiento") if self.nacimiento.value else None
        mascota = self.sistema.registrar_mascota(id_cliente, self.nombre.value or "", self.especie.value or "",
                                                 self.raza.value or "", nacimiento, self.sexo.value or "")
        avisar(self.page, f"{mascota.nombre} registrada, con su historia clínica abierta.")
        self.nombre.value = self.raza.value = self.nacimiento.value = self.nacimiento.data = ""
        self.especie.value = self.sexo.value = self.responsable.value = None
        self.refrescar()

    def ver_historia(self, id_mascota):
        mascota = self.sistema.mascota(id_mascota)
        historia = mascota.obtener_historia_clinica()
        filas = [[fh(a.fecha_hora), a.tipo.value, a.motivo, a.diagnostico,
                  f"{a.veterinario.apellido}, {a.veterinario.nombre}"]
                 for a in sorted(historia.obtener_atenciones(), key=lambda a: a.fecha_hora)] if historia else []
        contenido = [ft.Text(f"Responsable: {mascota.responsable.apellido}, {mascota.responsable.nombre}", size=12),
                     ft.Text(f"Historia abierta el {f(historia.fecha_apertura)}" if historia else "Sin historia", size=12)]
        contenido.append(ft.Row([tabla(["Fecha", "Tipo", "Motivo", "Diagnóstico", "Veterinario"], filas)],
                                scroll=ft.ScrollMode.AUTO) if filas else ft.Text("Sin atenciones todavía.", italic=True))
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"Historia clínica de {mascota.nombre}"),
            content=ft.Container(ft.Column(contenido, tight=True, scroll=ft.ScrollMode.AUTO), width=720),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.pop_dialog())]))

    def ver_vacunas(self, id_mascota):
        mascota = self.sistema.mascota(id_mascota)
        vacunas = [v for v in self.sistema.vacunas() if v.especie == mascota.especie]
        aplicadas = tabla(["Vacuna", "Aplicada", "Próxima dosis", "Vigente"],
                          [[a.vacuna.nombre, f(a.fecha_aplicacion), f(a.fecha_proxima_dosis),
                            "Sí" if a.esta_vigente(date.today()) else "No"]
                           for a in mascota.obtener_aplicaciones_vacuna()])
        vacuna = desplegable("Vacuna", [(v.id_vacuna, f"{v.nombre}{' (obligatoria)' if v.obligatoria else ''}")
                                        for v in vacunas], 280)
        aplicada = campo_fecha("Fecha de aplicación", 200, date.today())
        proxima = campo_fecha("Próxima dosis", 200, date.today() + timedelta(days=365))

        def aplicar(e):
            self.sistema.aplicar_vacuna(id_mascota, valor_entero(vacuna, "la vacuna"),
                                        leer_fecha(aplicada.value, "la fecha de aplicación"),
                                        leer_fecha(proxima.value, "la próxima dosis") if proxima.value else None)
            avisar(self.page, "Vacuna registrada.")
            self.page.pop_dialog()
            self.refrescar()

        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"Vacunas de {mascota.nombre}"),
            content=ft.Container(ft.Column([
                ft.Row([aplicadas], scroll=ft.ScrollMode.AUTO) if aplicadas.rows else ft.Text("Sin vacunas aplicadas.",
                                                                                            italic=True),
                ft.Divider(), ft.Text("Registrar aplicación", weight=ft.FontWeight.W_500),
                vacuna, ft.Row([aplicada, proxima], wrap=True),
            ], tight=True, scroll=ft.ScrollMode.AUTO), width=640),
            actions=[ft.FilledButton("Aplicar", icon=ft.Icons.VACCINES, on_click=accion_segura(self.page, aplicar)),
                     ft.TextButton("Cerrar", on_click=lambda e: self.page.pop_dialog())]))
