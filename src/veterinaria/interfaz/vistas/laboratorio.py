"""Empaquetado, envío, recepción, resultados y trazabilidad de las muestras."""
import flet as ft

from veterinaria.interfaz.componentes import (accion_segura, avisar, titulo, tarjeta, tabla, cargar_filas,
                                              contenedor_tabla, desplegable, recargar_opciones, campo,
                                              campo_fecha_hora, valor_entero, boton, chip_estado, leer_fecha_hora,
                                              fh, COLOR_PRIMARIO)


class VistaLaboratorio:
    def __init__(self, page, sistema):
        self.page, self.sistema = page, sistema
        # empaquetado
        self.emp_clinica = desplegable("Clínica de origen", [(c.id_clinica, c.nombre) for c in sistema.clinicas()], 240)
        self.emp_conservadora = desplegable("Conservadora disponible", [], 220)
        self.emp_fecha = campo_fecha_hora()
        self.emp_muestras = ft.Column(spacing=0)
        # envío
        self.env_remito = desplegable("Remito", [], 380)
        self.env_fecha = campo_fecha_hora()
        self.env_obs = campo("Transporte / observaciones", 280)
        self.tabla_remitos = tabla(["Remito", "Clínica", "Conservadora", "Precinto", "Muestras", "Estado", "Envío",
                                    "Salida", "Llegada"])
        # recepción
        self.rec_remito = desplegable("Remito entregado", [], 380)
        self.rec_fecha = campo_fecha_hora()
        self.rec_intacto = ft.Checkbox(label="Precinto sanitario intacto", value=True)
        self.rec_obs = campo("Observaciones", 300)
        # resultados
        self.res_muestra = desplegable("Muestra", [], 460)
        self.res_fecha = campo_fecha_hora()
        self.res_texto = ft.TextField(label="Resultado", multiline=True, min_lines=2, width=520)
        self.res_obs = campo("Observaciones", 300)
        # trazabilidad
        self.tabla_muestras = tabla(["Muestra", "Tipo", "Estudio", "Mascota", "Extracción", "Estado", ""])

    def build(self):
        pestanias = [
            ("Empaquetado", ft.Icons.INVENTORY_2, self._tab(
                tarjeta(ft.Column([
                    ft.Text("Las muestras pasan a EMPAQUETADA y se genera el precinto sanitario del remito.",
                            size=12, color=ft.Colors.GREY_700),
                    ft.Row([self.emp_clinica, self.emp_conservadora, self.emp_fecha], wrap=True),
                    ft.Text("Muestras extraídas sin remito:", weight=ft.FontWeight.W_500), self.emp_muestras,
                    boton("Generar remito", ft.Icons.INVENTORY_2, accion_segura(self.page, self.empaquetar)),
                ]), "Empaquetar muestras"))),
            ("Envío", ft.Icons.LOCAL_SHIPPING, self._tab(
                tarjeta(ft.Column([
                    ft.Row([self.env_remito, self.env_fecha, self.env_obs], wrap=True),
                    ft.Row([boton("Despachar", ft.Icons.LOCAL_SHIPPING, accion_segura(self.page, self.despachar)),
                            boton("Registrar llegada al laboratorio", ft.Icons.PIN_DROP,
                                  accion_segura(self.page, self.registrar_llegada), principal=False)], wrap=True),
                ]), "Cadena de envío"),
                tarjeta(contenedor_tabla(self.tabla_remitos, 300), "Remitos biológicos"))),
            ("Recepción", ft.Icons.FACT_CHECK, self._tab(
                tarjeta(ft.Column([
                    ft.Text("Si el precinto llega roto, las muestras pasan a RECHAZADA y no pueden analizarse.",
                            size=12, color=ft.Colors.GREY_700),
                    ft.Row([self.rec_remito, self.rec_fecha], wrap=True),
                    self.rec_intacto, self.rec_obs,
                    boton("Registrar recepción", ft.Icons.FACT_CHECK, accion_segura(self.page, self.recibir)),
                ]), "Recepción en el laboratorio central"))),
            ("Resultados", ft.Icons.ASSIGNMENT_TURNED_IN, self._tab(
                tarjeta(ft.Column([
                    ft.Row([self.res_muestra, self.res_fecha], wrap=True), self.res_texto, self.res_obs,
                    boton("Registrar resultado", ft.Icons.ASSIGNMENT_TURNED_IN,
                          accion_segura(self.page, self.registrar_resultado)),
                ]), "Resultado del análisis"))),
            ("Trazabilidad", ft.Icons.TIMELINE, self._tab(tarjeta(contenedor_tabla(self.tabla_muestras, 460),
                                                                  "Muestras biológicas"))),
        ]
        self.refrescar()
        return ft.Column([
            titulo("Laboratorio", "Ciclo de vida de la muestra: EXTRAIDA > EMPAQUETADA > EN_TRANSITO > RECIBIDA > ANALIZADA"),
            ft.Tabs(length=len(pestanias), selected_index=0, expand=True, content=ft.Column([
                ft.TabBar(tabs=[ft.Tab(label=n, icon=i) for n, i, _ in pestanias], scrollable=False),
                ft.TabBarView(controls=[ft.Container(c, padding=ft.Padding.only(top=12)) for _, _, c in pestanias],
                              expand=True),
            ], expand=True)),
        ], expand=True)

    @staticmethod
    def _tab(*tarjetas):
        return ft.Column(list(tarjetas), spacing=12, scroll=ft.ScrollMode.AUTO)

    # ------------------------------------------------------------ datos
    def refrescar(self):
        recargar_opciones(self.emp_conservadora, [(c.id_conservadora, c.codigo) for c in self.sistema.conservadoras()
                                                  if c.esta_disponible()])
        self.emp_muestras.controls = [
            ft.Checkbox(label=f"#{m.id_muestra} · {m.tipo_muestra} · {o.estudio_solicitado} · {mascota.nombre} · "
                              f"extraída {fh(m.fecha_extraccion)}", data=m.id_muestra, value=True)
            for m, o, _, mascota in self.sistema.muestras_sin_remito()
        ] or [ft.Text("No hay muestras pendientes de empaquetar.", italic=True, size=12)]

        remitos, filas, para_envio, para_recepcion = self.sistema.remitos(), [], [], []
        for r in remitos:
            envio = self.sistema.envio_de(r.id_remito)
            precinto = r.obtener_precinto()
            estado_envio = envio.estado.name if envio else "SIN ENVIO"
            texto = f"Remito #{r.id_remito} · {r.clinica_origen.nombre} · {len(r.obtener_muestras())} muestra(s)"
            if envio is None or estado_envio == "EN_TRANSITO":
                para_envio.append((r.id_remito, f"{texto} · {estado_envio}"))
            if estado_envio == "ENTREGADO" and r.estado.name == "DESPACHADO":
                para_recepcion.append((r.id_remito, texto))
            filas.append([f"#{r.id_remito}", r.clinica_origen.nombre, r.conservadora.codigo,
                          chip_estado(precinto.estado.name) if precinto else "-", len(r.obtener_muestras()),
                          chip_estado(r.estado.name), chip_estado(estado_envio),
                          fh(envio.fecha_hora_salida) if envio else "-", fh(envio.fecha_hora_llegada) if envio else "-"])
        cargar_filas(self.tabla_remitos, filas)
        recargar_opciones(self.env_remito, para_envio)
        recargar_opciones(self.rec_remito, para_recepcion)

        muestras = self.sistema.muestras()
        recargar_opciones(self.res_muestra, [
            (m.id_muestra, f"#{m.id_muestra} · {o.estudio_solicitado} · {mascota.nombre} · {m.estado.obtener_nombre()}")
            for m, o, _, mascota in muestras if m.estado.obtener_nombre() in ("RECIBIDA", "RECHAZADA")])
        filas = []
        for m, o, _, mascota in muestras:
            ver = ft.IconButton(ft.Icons.TIMELINE, tooltip="Ver historial de estados", icon_color=COLOR_PRIMARIO,
                                on_click=accion_segura(self.page, lambda e, m=m: self.ver_historial(m.id_muestra)))
            filas.append([f"#{m.id_muestra}", m.tipo_muestra, o.estudio_solicitado, mascota.nombre,
                          fh(m.fecha_extraccion), chip_estado(m.estado.obtener_nombre()), ver])
        cargar_filas(self.tabla_muestras, filas)

    # ------------------------------------------------------------ acciones
    def empaquetar(self, e):
        seleccion = [c.data for c in self.emp_muestras.controls if isinstance(c, ft.Checkbox) and c.value]
        remito = self.sistema.empaquetar(valor_entero(self.emp_clinica, "la clínica"),
                                         valor_entero(self.emp_conservadora, "la conservadora"), seleccion,
                                         leer_fecha_hora(self.emp_fecha.value))
        self.refrescar()
        avisar(self.page, f"Remito #{remito.id_remito} generado con precinto {remito.obtener_precinto().codigo}.")

    def despachar(self, e):
        envio = self.sistema.despachar(valor_entero(self.env_remito, "el remito"), leer_fecha_hora(self.env_fecha.value),
                                       self.env_obs.value or "")
        avisar(self.page, f"Remito despachado: {len(envio.remito.obtener_muestras())} muestra(s) EN_TRANSITO.")
        self.refrescar()

    def registrar_llegada(self, e):
        self.sistema.registrar_llegada(valor_entero(self.env_remito, "el remito"), leer_fecha_hora(self.env_fecha.value))
        avisar(self.page, "Llegada registrada. Ya se puede hacer la recepción.")
        self.refrescar()

    def recibir(self, e):
        intacto = self.rec_intacto.value
        recepcion = self.sistema.recibir(valor_entero(self.rec_remito, "el remito"), leer_fecha_hora(self.rec_fecha.value),
                                         intacto, self.rec_obs.value or "")
        muestras = recepcion.envio.remito.obtener_muestras()
        self.refrescar()
        if intacto:
            texto, icono, color = f"Remito aceptado: {len(muestras)} muestra(s) RECIBIDA(s).", ft.Icons.CHECK_CIRCLE, \
                ft.Colors.GREEN_600
        else:
            texto, icono, color = f"Precinto roto: {len(muestras)} muestra(s) RECHAZADA(s). No podrán analizarse.", \
                ft.Icons.CANCEL, ft.Colors.RED_600
        self.page.show_dialog(ft.AlertDialog(icon=ft.Icon(icono, color=color, size=40), title=ft.Text("Recepción registrada"),
                                             content=ft.Text(texto),
                                             actions=[ft.TextButton("Aceptar", on_click=lambda e: self.page.pop_dialog())]))
        self.rec_intacto.value = True

    def registrar_resultado(self, e):
        resultado = self.sistema.registrar_resultado(valor_entero(self.res_muestra, "la muestra"),
                                                     leer_fecha_hora(self.res_fecha.value), self.res_texto.value or "",
                                                     self.res_obs.value or "")
        avisar(self.page, f"Resultado registrado: la muestra #{resultado.muestra.id_muestra} quedó ANALIZADA.")
        self.res_texto.value = self.res_obs.value = ""
        self.refrescar()

    def ver_historial(self, id_muestra):
        muestra = self.sistema.muestra(id_muestra)
        resultado = self.sistema.resultado_de(id_muestra)
        lineas = []
        for registro in muestra.obtener_historial():
            lineas.append(ft.Row([chip_estado(registro.nombre_estado),
                                  ft.Text(fh(registro.fecha_hora), weight=ft.FontWeight.W_500, size=12),
                                  ft.Text(registro.observaciones or "", size=12, color=ft.Colors.GREY_700)]))
        if resultado:
            lineas += [ft.Divider(), ft.Text(f"Resultado: {resultado.resultado}", size=12)]
        lineas.append(ft.Text("El historial es inmutable: cada cambio de estado agrega un registro (RN14, RN15).",
                              size=11, italic=True, color=ft.Colors.GREY_600))
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"Historial de la muestra #{id_muestra} ({muestra.tipo_muestra})"),
            content=ft.Container(ft.Column(lineas, tight=True), width=560),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.pop_dialog())]))
