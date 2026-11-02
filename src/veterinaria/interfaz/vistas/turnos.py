"""Agenda médica y turnos (RN02 y RN03 los valida la clase Veterinario)."""
from datetime import date, datetime

import flet as ft

from veterinaria.interfaz.componentes import (accion_segura, avisar, titulo, tarjeta, tabla, cargar_filas,
                                              contenedor_tabla, desplegable, campo, campo_fecha, valor_entero, boton,
                                              chip_estado, leer_fecha, fh)
from veterinaria.servicios.sistema import describir_agenda


class VistaTurnos:
    def __init__(self, page, sistema):
        self.page, self.sistema = page, sistema
        self.veterinario = desplegable(
            "Veterinario", [(v.id_veterinario, f"{v.apellido}, {v.nombre} · {v.especialidad}")
                            for v in sistema.veterinarios()], 340, on_select=accion_segura(page, lambda e: self.refrescar()))
        self.agenda = ft.Text("", size=12, color=ft.Colors.GREY_700)
        self.mascota = desplegable("Mascota", [(m.id_mascota, f"{m.nombre} ({m.especie}) · "
                                                f"{m.responsable.apellido}") for m in sistema.mascotas()], 320)
        self.fecha = campo_fecha("Fecha", 170, date.today())
        self.hora = campo("Hora (HH:MM)", 130, "10:00")
        self.duracion = desplegable("Duración", [(m, f"{m} min") for m in (15, 30, 45, 60)], 130)
        self.duracion.value = "30"
        self.motivo = campo("Motivo", 260)
        self.tabla = tabla(["Inicio", "Fin", "Mascota", "Motivo", "Estado", ""])

    def build(self):
        return ft.Column([
            titulo("Turnos", "El turno debe caer dentro de la agenda del veterinario y no superponerse"),
            tarjeta(ft.Column([
                ft.Row([self.veterinario, self.agenda], wrap=True),
                ft.Row([self.mascota, self.fecha, self.hora, self.duracion], wrap=True),
                self.motivo,
                boton("Reservar turno", ft.Icons.EVENT_AVAILABLE, accion_segura(self.page, self.reservar)),
            ]), "Nuevo turno"),
            tarjeta(contenedor_tabla(self.tabla, 400), "Turnos del veterinario"),
        ], spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    def refrescar(self):
        if not self.veterinario.value:
            return
        id_vet = int(self.veterinario.value)
        agenda = self.sistema.agenda_de(id_vet)
        if agenda:
            self.agenda.value = f"Agenda: {describir_agenda(agenda)}"
        else:
            self.agenda.value = "Sin agenda asignada"
        filas = []
        for t in self.sistema.turnos(id_vet):
            acciones = ft.Row([
                ft.IconButton(ft.Icons.CHECK, tooltip="Confirmar", icon_color=ft.Colors.GREEN_600,
                              visible=t.estado.name == "PENDIENTE",
                              on_click=accion_segura(self.page, lambda e, t=t: self.cambiar(t, "confirmar"))),
                ft.IconButton(ft.Icons.EVENT_BUSY, tooltip="Cancelar", icon_color=ft.Colors.RED_400,
                              visible=t.estado.name in ("PENDIENTE", "CONFIRMADO"),
                              on_click=accion_segura(self.page, lambda e, t=t: self.cambiar(t, "cancelar"))),
            ], spacing=0)
            filas.append([fh(t.fecha_hora_inicio), f"{t.fecha_hora_fin:%H:%M}", t.mascota.nombre, t.motivo,
                          chip_estado(t.estado.name), acciones])
        cargar_filas(self.tabla, filas)

    def reservar(self, e):
        try:
            hora = datetime.strptime((self.hora.value or "").strip(), "%H:%M").time()
        except ValueError:
            avisar(self.page, "La hora debe tener el formato HH:MM.", error=True)
            return
        inicio = datetime.combine(leer_fecha(self.fecha.value), hora)
        turno = self.sistema.reservar_turno(valor_entero(self.veterinario, "el veterinario"),
                                            valor_entero(self.mascota, "la mascota"), inicio,
                                            int(self.duracion.value or 30), self.motivo.value or "")
        avisar(self.page, f"Turno reservado para el {fh(turno.fecha_hora_inicio)}.")
        self.motivo.value = ""
        self.refrescar()

    def cambiar(self, turno, accion):
        self.sistema.cambiar_estado_turno(int(self.veterinario.value), turno.id_turno, accion)
        avisar(self.page, "Turno confirmado." if accion == "confirmar" else "Turno cancelado.")
        self.refrescar()
