"""Circuito completo a través de la capa de servicios (sin interfaz)."""

from datetime import date, datetime, time, timedelta

import pytest

from veterinaria.dominio.clinica.agenda_medica import DiaSemana
from veterinaria.dominio.clinica.atencion import TipoAtencion
from veterinaria.servicios.errores import ErrorNegocio
from veterinaria.servicios.exportador import exportar_csv, exportar_pdf, exportar_comprobante_pdf
from veterinaria.servicios.fachada import Servicios

LUNES = datetime(2026, 11, 2, 9, 0)  # lunes


@pytest.fixture(autouse=True)
def reloj_fijo(monkeypatch):
    """Los turnos no pueden reservarse en el pasado: estas pruebas usan fechas fijas de
    noviembre de 2026, así que el "ahora" del servicio queda fijado antes de esas fechas."""
    monkeypatch.setattr("veterinaria.servicios.clinica_servicio.ahora", lambda: datetime(2026, 11, 1, 0, 0))


@pytest.fixture
def s(tmp_path):
    return Servicios(tmp_path / "vet.db")


@pytest.fixture
def base(s):
    id_cli = s.clinica.crear_cliente("Ana", "Pérez", "30111222", "351", "a@x.com")
    id_mas = s.clinica.crear_mascota(id_cli, "Firulais", "Perro")
    id_cl = s.clinica.crear_clinica("Clínica Centro", "Colón 100")
    id_vet = s.clinica.crear_veterinario(id_cl, "Luis", "Gómez", "MP-1")
    s.clinica.guardar_agenda(id_vet, {DiaSemana.LUNES}, time(8), time(13))
    s.atencion.abrir_historia(id_mas, "Primera visita", date(2026, 11, 2))
    return {"cli": id_cli, "mas": id_mas, "cl": id_cl, "vet": id_vet}


def _atencion_con_orden(s, b):
    id_at = s.atencion.registrar_atencion(b["mas"], b["vet"], LUNES, TipoAtencion.CONSULTA, "Control")
    id_or = s.laboratorio.crear_orden(id_at, "Hemograma", fecha_emision=LUNES)
    id_mu = s.laboratorio.registrar_muestra(id_or, "Sangre", LUNES)
    return id_at, id_or, id_mu


def _despachado(s, b, id_mu, romper=False):
    id_c = s.laboratorio.crear_conservadora("CONS-1")
    id_r = s.laboratorio.crear_remito(b["cl"], id_c, fecha_emision=LUNES)
    s.laboratorio.agregar_muestras_a_remito(id_r, [id_mu], LUNES + timedelta(minutes=10))
    s.laboratorio.asignar_precinto(id_r, "PRE-1")
    id_e = s.laboratorio.despachar_remito(id_r, LUNES + timedelta(minutes=30))
    if romper:
        s.laboratorio.romper_precinto(id_r)
    s.laboratorio.registrar_llegada(id_e, LUNES + timedelta(hours=2))
    return id_r, id_e


def test_mascota_sin_responsable(s):
    with pytest.raises(ErrorNegocio):
        s.clinica.crear_mascota(None, "X", "Perro")
    with pytest.raises(ErrorNegocio):
        s.clinica.crear_mascota(999, "X", "Perro")


def test_turnos_agenda_superposicion_y_cancelado(s, base):
    t = lambda h, m, h2, m2: (LUNES.replace(hour=h, minute=m), LUNES.replace(hour=h2, minute=m2))
    s.clinica.agendar_turno(base["vet"], base["mas"], *t(9, 0, 9, 30))
    s.clinica.agendar_turno(base["vet"], base["mas"], *t(9, 30, 10, 0))      # consecutivo
    with pytest.raises(ErrorNegocio, match="superpone"):
        s.clinica.agendar_turno(base["vet"], base["mas"], *t(9, 15, 9, 45))
    with pytest.raises(ErrorNegocio, match="fuera de la agenda"):
        s.clinica.agendar_turno(base["vet"], base["mas"], *t(13, 0, 13, 30))
    with pytest.raises(ErrorNegocio, match="fuera de la agenda"):            # martes
        s.clinica.agendar_turno(base["vet"], base["mas"], LUNES + timedelta(days=1), LUNES + timedelta(days=1, minutes=30))
    primero = s.clinica.listar_turnos()[0]["id"]
    s.clinica.cambiar_estado_turno(primero, "cancelar")
    s.clinica.agendar_turno(base["vet"], base["mas"], *t(9, 15, 9, 30))      # libera el horario


def test_atencion_exige_historia_y_vacunas(s, base):
    id_cli = s.clinica.crear_cliente("Bea", "Ruiz", "30999888")
    sin_historia = s.clinica.crear_mascota(id_cli, "Michi", "Gato")
    with pytest.raises(ErrorNegocio, match="historia"):
        s.atencion.registrar_atencion(sin_historia, base["vet"], LUNES, TipoAtencion.CONSULTA, "x")

    id_vac = s.atencion.crear_vacuna("Antirrábica", "Perro", True)
    with pytest.raises(ErrorNegocio, match="Antirrábica"):
        s.atencion.registrar_atencion(base["mas"], base["vet"], LUNES, TipoAtencion.CONSULTA, "x")
    s.atencion.registrar_aplicacion(base["mas"], id_vac, date(2026, 10, 1), date(2027, 10, 1))
    assert s.atencion.vacunas_pendientes(base["mas"], date(2026, 11, 2)) == []
    s.atencion.registrar_atencion(base["mas"], base["vet"], LUNES, TipoAtencion.CONSULTA, "ok")


def test_circuito_precinto_intacto(s, base, tmp_path):
    id_at, id_or, id_mu = _atencion_con_orden(s, base)
    id_r, id_e = _despachado(s, base, id_mu)
    res = s.laboratorio.registrar_recepcion(id_e, LUNES + timedelta(hours=2, minutes=15))
    assert res["resultado"] == "ACEPTADO" and res["muestras"] == [(id_mu, "RECIBIDA")]
    s.laboratorio.registrar_resultado(id_mu, "Normal", fecha_resultado=LUNES + timedelta(hours=4))
    assert [h["estado"] for h in s.laboratorio.historial_muestra(id_mu)] == [
        "EXTRAIDA", "EMPAQUETADA", "EN_TRANSITO", "RECIBIDA", "ANALIZADA"]
    assert s.laboratorio.listar_ordenes()[0]["estado"] == "COMPLETADA"
    assert s.laboratorio.obtener_resultado(id_mu)["resultado"] == "Normal"

    s.atencion.emitir_comprobante(id_at, LUNES + timedelta(hours=5))
    comp = s.atencion.obtener_comprobante(id_at)
    assert comp["mascota"].startswith("Firulais")
    with pytest.raises(ErrorNegocio):
        s.atencion.emitir_comprobante(id_at)

    t = s.reportes.tiempos()["filas"]
    assert t[0]["cantidad"] == 1 and t[1]["cantidad"] == 1
    assert s.reportes.muestras_rechazadas()["filas"] == []
    rep = s.reportes.atenciones_derivaciones()["filas"]
    assert rep[0]["mascota"] == "Firulais" and rep[0]["clinica"] == "Clínica Centro"
    assert rep[0]["derivaciones"] == 1

    exportar_csv(tmp_path / "r.csv", s.reportes.atenciones_derivaciones())
    exportar_pdf(tmp_path / "r.pdf", s.reportes.tiempos())
    exportar_comprobante_pdf(tmp_path / "c.pdf", comp)
    assert (tmp_path / "r.pdf").stat().st_size > 500 and (tmp_path / "c.pdf").stat().st_size > 500


def test_circuito_precinto_roto_rechaza(s, base):
    _, _, id_mu = _atencion_con_orden(s, base)
    id_r, id_e = _despachado(s, base, id_mu, romper=True)
    res = s.laboratorio.registrar_recepcion(id_e, LUNES + timedelta(hours=3))
    assert res["resultado"] == "RECHAZADO" and res["muestras"] == [(id_mu, "RECHAZADA")]
    with pytest.raises(ErrorNegocio, match="RECHAZADA"):
        s.laboratorio.registrar_resultado(id_mu, "x")
    assert [h["estado"] for h in s.laboratorio.historial_muestra(id_mu)][-1] == "RECHAZADA"
    fila = s.reportes.muestras_rechazadas()["filas"][0]
    assert fila["estado_precinto"] == "ROTO" and fila["id_remito"] == id_r
    assert s.reportes.tiempos()["filas"][1]["cantidad"] == 0


def test_no_despacha_sin_condiciones(s, base):
    _, _, id_mu = _atencion_con_orden(s, base)
    id_c = s.laboratorio.crear_conservadora("CONS-2")
    id_r = s.laboratorio.crear_remito(base["cl"], id_c)
    with pytest.raises(ErrorNegocio, match="muestras"):
        s.laboratorio.despachar_remito(id_r)
    s.laboratorio.agregar_muestras_a_remito(id_r, [id_mu], LUNES + timedelta(minutes=1))
    with pytest.raises(ErrorNegocio, match="precinto"):
        s.laboratorio.despachar_remito(id_r)
    with pytest.raises(ErrorNegocio, match="no está disponible"):
        s.laboratorio.crear_remito(base["cl"], id_c)


def test_vacunas_pendientes_reporte(s, base):
    s.atencion.crear_vacuna("Antirrábica", "Perro", True)
    filas = s.reportes.vacunas_pendientes(date(2026, 11, 2))["filas"]
    assert filas[0]["mascota"] == "Firulais" and filas[0]["vacuna"] == "Antirrábica"


# ---------------------------------------------------------- acciones en un solo paso
def test_mascota_con_historia_automatica(s, base):
    id_mas = s.clinica.crear_mascota(base["cli"], "Nina", "Gato", abrir_historia=True)
    assert s.atencion.obtener_historia(id_mas) is not None
    s.atencion.registrar_atencion(id_mas, base["vet"], LUNES, TipoAtencion.CONSULTA, "Control")


def test_derivar_empaquetar_y_recibir_en_un_paso(s, base):
    id_at = s.atencion.registrar_atencion(base["mas"], base["vet"], LUNES, TipoAtencion.CONSULTA, "x")
    r = s.laboratorio.derivar(id_at, "Hemograma", "Sangre", LUNES)
    id_c = s.laboratorio.crear_conservadora("CONS-9")
    emp = s.laboratorio.empaquetar(base["cl"], id_c, [r["id_muestra"]], "", LUNES + timedelta(hours=1))
    assert emp["precinto"].startswith("PRE-")
    id_e = s.laboratorio.despachar_remito(emp["id_remito"], LUNES + timedelta(hours=2))
    res = s.laboratorio.recibir_remito(id_e, True, LUNES + timedelta(hours=4))
    assert res["resultado"] == "ACEPTADO"
    # sin muestras no se crea nada: la operación es atómica
    id_c2 = s.laboratorio.crear_conservadora("CONS-10")
    with pytest.raises(ErrorNegocio):
        s.laboratorio.empaquetar(base["cl"], id_c2, [], "", LUNES)
    assert [c["estado"] for c in s.laboratorio.listar_conservadoras() if c["id"] == id_c2] == ["DISPONIBLE"]


def test_recibir_remito_con_precinto_roto(s, base):
    id_at = s.atencion.registrar_atencion(base["mas"], base["vet"], LUNES, TipoAtencion.CONSULTA, "x")
    id_mu = s.laboratorio.derivar(id_at, "Urianálisis", "Orina", LUNES)["id_muestra"]
    id_c = s.laboratorio.crear_conservadora("CONS-1")
    emp = s.laboratorio.empaquetar(base["cl"], id_c, [id_mu], "PRE-X", LUNES + timedelta(hours=1))
    id_e = s.laboratorio.despachar_remito(emp["id_remito"], LUNES + timedelta(hours=2))
    res = s.laboratorio.recibir_remito(id_e, False, LUNES + timedelta(hours=3))
    assert res["resultado"] == "RECHAZADO" and res["muestras"] == [(id_mu, "RECHAZADA")]
    with pytest.raises(ErrorNegocio, match="RECHAZADA"):
        s.laboratorio.registrar_resultado(id_mu, "x")
    # liberar manualmente la conservadora tras la recepción
    s.laboratorio.liberar_conservadora(id_c)


def test_empaquetar_con_fecha_anterior_a_la_extraccion(s, base):
    id_at = s.atencion.registrar_atencion(base["mas"], base["vet"], LUNES, TipoAtencion.CONSULTA, "x")
    id_mu = s.laboratorio.derivar(id_at, "Hemograma", "Sangre", LUNES)["id_muestra"]
    id_c = s.laboratorio.crear_conservadora("CONS-1")
    with pytest.raises(ErrorNegocio, match="anterior a la extracción"):
        s.laboratorio.empaquetar(base["cl"], id_c, [id_mu], "", LUNES - timedelta(hours=1))


def test_no_empaqueta_muestra_de_otra_clinica_ni_altera_el_lote(s, base):
    _, _, muestra_a = _atencion_con_orden(s, base)
    clinica_b = s.clinica.crear_clinica("Clínica Norte", "Norte 100")
    vet_b = s.clinica.crear_veterinario(clinica_b, "Eva", "López", "MP-2")
    atencion_b = s.atencion.registrar_atencion(
        base["mas"], vet_b, LUNES, TipoAtencion.CONSULTA, "Control")
    muestra_b = s.laboratorio.derivar(
        atencion_b, "Urianálisis", "Orina", LUNES)["id_muestra"]
    conservadora = s.laboratorio.crear_conservadora("CONS-OTRA")

    with pytest.raises(ErrorNegocio, match="otra clínica"):
        s.laboratorio.empaquetar(
            clinica_b, conservadora, [muestra_b, muestra_a], fecha=LUNES + timedelta(hours=1))
    assert s.laboratorio.listar_remitos() == []
    assert [c["estado"] for c in s.laboratorio.listar_conservadoras()
            if c["id"] == conservadora] == ["DISPONIBLE"]
    for id_muestra in (muestra_a, muestra_b):
        muestra = next(m for m in s.laboratorio.listar_muestras() if m["id"] == id_muestra)
        assert muestra["estado"] == "EXTRAIDA" and muestra["id_remito"] is None
        assert [h["estado"] for h in s.laboratorio.historial_muestra(id_muestra)] == ["EXTRAIDA"]

    remito = s.laboratorio.crear_remito(clinica_b, conservadora, fecha_emision=LUNES)
    with pytest.raises(ErrorNegocio, match="otra clínica"):
        s.laboratorio.agregar_muestras_a_remito(
            remito, [muestra_b, muestra_a], LUNES + timedelta(hours=1))
    assert next(r for r in s.laboratorio.listar_remitos() if r["id"] == remito)["muestras"] == 0
    for id_muestra in (muestra_a, muestra_b):
        muestra = next(m for m in s.laboratorio.listar_muestras() if m["id"] == id_muestra)
        assert muestra["estado"] == "EXTRAIDA" and muestra["id_remito"] is None
        assert [h["estado"] for h in s.laboratorio.historial_muestra(id_muestra)] == ["EXTRAIDA"]


@pytest.mark.parametrize("precinto_integro", [True, False])
def test_conservadora_solo_se_libera_tras_recepcion_completa(s, base, precinto_integro):
    _, _, id_muestra = _atencion_con_orden(s, base)
    conservadora = s.laboratorio.crear_conservadora("CONS-CUSTODIA")
    remito = s.laboratorio.crear_remito(base["cl"], conservadora, fecha_emision=LUNES)
    with pytest.raises(ErrorNegocio, match="pendiente de recepción"):
        s.laboratorio.liberar_conservadora(conservadora)

    s.laboratorio.agregar_muestras_a_remito(remito, [id_muestra], LUNES + timedelta(minutes=10))
    s.laboratorio.asignar_precinto(remito, "PRE-CUSTODIA")
    envio = s.laboratorio.despachar_remito(remito, LUNES + timedelta(minutes=30))
    with pytest.raises(ErrorNegocio, match="pendiente de recepción"):
        s.laboratorio.liberar_conservadora(conservadora)
    s.laboratorio.registrar_llegada(envio, LUNES + timedelta(hours=2))
    with pytest.raises(ErrorNegocio, match="pendiente de recepción"):
        s.laboratorio.liberar_conservadora(conservadora)
    assert next(c for c in s.laboratorio.listar_conservadoras()
                if c["id"] == conservadora)["estado"] == "EN_USO"

    resultado = s.laboratorio.recibir_remito(
        envio, precinto_integro, LUNES + timedelta(hours=3))
    estado = "RECIBIDA" if precinto_integro else "RECHAZADA"
    assert resultado["muestras"] == [(id_muestra, estado)]
    assert s.laboratorio.historial_muestra(id_muestra)[-1]["estado"] == estado
    s.laboratorio.liberar_conservadora(conservadora)
    assert next(c for c in s.laboratorio.listar_conservadoras()
                if c["id"] == conservadora)["estado"] == "DISPONIBLE"

    # Un remito anterior recibido no debe ocultar un nuevo uso todavía activo.
    s.laboratorio.crear_remito(base["cl"], conservadora, fecha_emision=LUNES + timedelta(hours=4))
    with pytest.raises(ErrorNegocio, match="pendiente de recepción"):
        s.laboratorio.liberar_conservadora(conservadora)


def test_datos_demo(tmp_path):
    from veterinaria.servicios.datos_demo import cargar_demo, hay_datos
    s = Servicios(tmp_path / "demo.db")
    assert not hay_datos(s)
    cargar_demo(s)
    assert hay_datos(s)
    estados = {m["estado"] for m in s.laboratorio.listar_muestras()}
    assert {"ANALIZADA", "RECHAZADA", "EN_TRANSITO", "EXTRAIDA"} <= estados
    reportes = s.reportes.todos()
    assert len(reportes["rechazadas"]["filas"]) == 2 and reportes["vacunas"]["filas"]
    assert reportes["tiempos"]["filas"][0]["cantidad"] >= 1
    with pytest.raises(ErrorNegocio, match="pendientes"):        # Toby tiene vacunas pendientes
        toby = next(m for m in s.clinica.listar_mascotas() if m["nombre"] == "Toby")["id"]
        vet = s.clinica.listar_veterinarios()[0]["id"]
        s.atencion.registrar_atencion(toby, vet, datetime.now(), TipoAtencion.CONSULTA, "x")


# ----------------------------------------------- duplicados, bajas y comprobante de resultados
def test_mascota_duplicada_y_etiquetas_unicas(s, base):
    with pytest.raises(ErrorNegocio, match="ya tiene registrada"):
        s.clinica.crear_mascota(base["cli"], " firulais ", "perro")
    otro = s.clinica.crear_cliente("Raúl", "Pérez", "30777666")          # mismo apellido
    s.clinica.crear_mascota(otro, "Firulais", "Perro")
    etiquetas = [m["etiqueta"] for m in s.clinica.listar_mascotas()]
    assert len(set(etiquetas)) == 2 and all("[#" in e for e in etiquetas)


def test_baja_de_mascota_con_historia_vacia_y_con_atenciones(s, base):
    nueva = s.clinica.crear_mascota(base["cli"], "Nina", "Gato", abrir_historia=True)
    s.clinica.eliminar_mascota(nueva)                                    # historia vacía: se elimina
    assert all(m["id"] != nueva for m in s.clinica.listar_mascotas())
    s.atencion.registrar_atencion(base["mas"], base["vet"], LUNES, TipoAtencion.CONSULTA, "x")
    with pytest.raises(ErrorNegocio, match="no puede eliminarse"):
        s.clinica.eliminar_mascota(base["mas"])
    assert s.atencion.obtener_historia(base["mas"]) is not None          # rollback: nada se perdió


def test_comprobante_de_resultados(s, base, tmp_path):
    _, _, id_mu = _atencion_con_orden(s, base)
    with pytest.raises(ErrorNegocio, match="todavía no tiene"):
        s.laboratorio.obtener_comprobante_resultado(id_mu)
    id_r, id_e = _despachado(s, base, id_mu)
    s.laboratorio.registrar_recepcion(id_e, LUNES + timedelta(hours=2, minutes=15))
    s.laboratorio.registrar_resultado(id_mu, "Normal\nsin hallazgos", "ok",
                                      LUNES + timedelta(hours=4))
    comp = s.laboratorio.obtener_comprobante_resultado(id_mu)
    assert comp["mascota"] == "Firulais (Perro) - Pérez" and comp["clinica"] == "Clínica Centro"
    assert comp["veterinario"].startswith("Gómez") and comp["precinto"].startswith("PRE-1")
    assert comp["recepcion"] and comp["resultado"].startswith("Normal")
    from veterinaria.servicios.exportador import exportar_comprobante_resultado_pdf
    exportar_comprobante_resultado_pdf(tmp_path / "res.pdf", comp)
    assert (tmp_path / "res.pdf").stat().st_size > 800
    assert [f["id_txt"] for f in s.laboratorio.listar_resultados()] == [f"M-{id_mu:04d}"]


# ---------------------------------------------------------- vacunas y gráficos de reportes
def test_no_se_aplica_una_vacuna_de_otra_especie(s, base):
    id_felina = s.atencion.crear_vacuna("Triple felina", "Gato", True)
    with pytest.raises(ErrorNegocio, match="Gato"):
        s.atencion.registrar_aplicacion(base["mas"], id_felina, date(2026, 6, 1))
    assert s.atencion.listar_aplicaciones(base["mas"]) == []


def test_reportes_traen_datos_para_el_grafico(s, base):
    _, _, id_mu = _atencion_con_orden(s, base)
    s.atencion.crear_vacuna("Antirrábica", "Perro", True)   # después de la atención: si no, la bloquea
    _, id_e = _despachado(s, base, id_mu, romper=True)
    s.laboratorio.registrar_recepcion(id_e, LUNES + timedelta(hours=3))
    reportes = s.reportes.todos(date(2026, 11, 2))
    assert reportes["rechazadas"]["grafico"]["datos"] == {"Clínica Centro": 1}
    assert reportes["vacunas"]["grafico"]["datos"] == {"Antirrábica (Perro)": 1}
    assert reportes["tiempos"]["grafico"]["datos"]["Tránsito"] == 1.5


def test_pdf_de_reporte_incluye_el_grafico(s, base, tmp_path):
    s.atencion.registrar_atencion(base["mas"], base["vet"], LUNES, TipoAtencion.CONSULTA, "Control")
    ruta = tmp_path / "atenciones.pdf"
    exportar_pdf(ruta, s.reportes.atenciones_derivaciones())
    assert b"/Subtype /Image" in ruta.read_bytes()


# ------------------------------------------------- validaciones de datos y bajas de profesionales
@pytest.mark.parametrize("nombre", ["Ana2", "Ana!", "J.", "123"])
def test_nombre_y_apellido_solo_letras(s, nombre):
    with pytest.raises(ErrorNegocio, match="sólo admite letras"):
        s.clinica.crear_cliente(nombre, "Pérez", "30111223")
    with pytest.raises(ErrorNegocio, match="sólo admite letras"):
        s.clinica.crear_cliente("Ana", nombre, "30111223")


def test_nombres_compuestos_con_tilde_y_guion_son_validos(s):
    id_cli = s.clinica.crear_cliente("María José", "Pérez-Núñez", "30111223")
    assert s.clinica.listar_clientes()[0]["apellido"] == "Pérez-Núñez" and id_cli == 1


@pytest.mark.parametrize("dni", ["123", "123456789", "30a11222", "30 111 22"])
def test_dni_solo_numeros_de_7_u_8_digitos(s, dni):
    with pytest.raises(ErrorNegocio, match="DNI"):
        s.clinica.crear_cliente("Ana", "Pérez", dni)


def test_modificar_cliente_tambien_valida(s, base):
    with pytest.raises(ErrorNegocio, match="DNI"):
        s.clinica.modificar_cliente(base["cli"], "Ana", "Pérez", "12")
    with pytest.raises(ErrorNegocio, match="letras"):
        s.clinica.modificar_cliente(base["cli"], "Ana3", "Pérez", "30111222")


def test_veterinario_con_nombre_invalido(s, base):
    with pytest.raises(ErrorNegocio, match="letras"):
        s.clinica.crear_veterinario(base["cl"], "Luis1", "Gómez", "MP-9")


def test_fecha_de_nacimiento_futura(s, base):
    manana = date.today() + timedelta(days=1)
    with pytest.raises(ErrorNegocio, match="nacimiento"):
        s.clinica.crear_mascota(base["cli"], "Toby", "Perro", fecha_nacimiento=manana)
    with pytest.raises(ErrorNegocio, match="nacimiento"):
        s.clinica.modificar_mascota(base["mas"], "Firulais", "Perro", fecha_nacimiento=manana)
    s.clinica.crear_mascota(base["cli"], "Toby", "Perro", fecha_nacimiento=date.today())


def test_turno_en_el_pasado(s, base):
    # el "ahora" fijado es 01/11/2026 00:00: un turno del lunes 26/10 ya pasó
    pasado = LUNES - timedelta(days=7)
    with pytest.raises(ErrorNegocio, match="ya pasó"):
        s.clinica.agendar_turno(base["vet"], base["mas"], pasado, pasado + timedelta(minutes=30))


def test_eliminar_veterinario_sin_turnos_borra_tambien_su_agenda(s, base):
    s.clinica.eliminar_veterinario(base["vet"])
    assert s.clinica.listar_veterinarios() == []
    assert s.clinica.obtener_agenda(base["vet"]) is None


def test_no_se_elimina_veterinario_con_turnos_o_atenciones(s, base):
    s.clinica.agendar_turno(base["vet"], base["mas"], LUNES, LUNES + timedelta(minutes=30))
    with pytest.raises(ErrorNegocio, match="turnos"):
        s.clinica.eliminar_veterinario(base["vet"])
    otro = s.clinica.crear_veterinario(base["cl"], "Marta", "Ruiz", "MP-2")
    s.atencion.registrar_atencion(base["mas"], otro, LUNES, TipoAtencion.CONSULTA, "Control")
    with pytest.raises(ErrorNegocio, match="atenciones"):
        s.clinica.eliminar_veterinario(otro)


def test_eliminar_clinica(s, base):
    vacia = s.clinica.crear_clinica("Clínica Norte", "Av. Norte 1")
    s.clinica.eliminar_clinica(vacia)
    assert [c["nombre"] for c in s.clinica.listar_clinicas()] == ["Clínica Centro"]
    with pytest.raises(ErrorNegocio, match="veterinarios"):
        s.clinica.eliminar_clinica(base["cl"])


def test_no_se_elimina_clinica_con_remitos(s, base):
    norte = s.clinica.crear_clinica("Clínica Norte", "Av. Norte 1")         # sin veterinarios
    s.laboratorio.crear_remito(norte, s.laboratorio.crear_conservadora("CONS-9"), fecha_emision=LUNES)
    with pytest.raises(ErrorNegocio, match="remitos"):
        s.clinica.eliminar_clinica(norte)
