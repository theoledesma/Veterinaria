"""Pruebas de la capa de servicios que usa la interfaz gráfica."""
from datetime import date, datetime, time, timedelta

import pytest

from veterinaria.dominio.clinica.agenda_medica import DiaSemana
from veterinaria.servicios.sistema import ErrorOperacion, SistemaVeterinaria

LUNES = datetime(2026, 11, 2, 10, 0)      # 2 de noviembre de 2026 es lunes


@pytest.fixture
def sistema(tmp_path):
    s = SistemaVeterinaria(tmp_path / "veterinaria.db")
    yield s
    s.cerrar()


@pytest.fixture
def datos(sistema):
    clinica = sistema.crear_clinica("Clínica Centro", "Av. Colón 1250")
    veterinario = sistema.crear_veterinario(clinica.id_clinica, "Laura", "Gómez", "MP-1", "General",
                                            [DiaSemana.LUNES, DiaSemana.MARTES], time(8, 0), time(12, 0))
    vacuna = sistema.crear_vacuna("Antirrábica", "Perro", True)
    conservadora = sistema.crear_conservadora("CI-01")
    cliente = sistema.registrar_cliente("Lucía", "Pérez", "30111222")
    mascota = sistema.registrar_mascota(cliente.id_cliente, "Luna", "Perro")
    return clinica, veterinario, vacuna, conservadora, mascota


def vacunar(sistema, mascota, vacuna):
    sistema.aplicar_vacuna(mascota.id_mascota, vacuna.id_vacuna, date(2026, 6, 1), date(2027, 6, 1))


def circuito_hasta_llegada(sistema, datos):
    clinica, veterinario, vacuna, conservadora, mascota = datos
    vacunar(sistema, mascota, vacuna)
    atencion = sistema.registrar_atencion(mascota.id_mascota, veterinario.id_veterinario, "CONSULTA", "Decaimiento",
                                          "", LUNES)
    _, muestra = sistema.emitir_orden(atencion.id_atencion, "Hemograma", "Sangre", LUNES + timedelta(minutes=10))
    remito = sistema.empaquetar(clinica.id_clinica, conservadora.id_conservadora, [muestra.id_muestra],
                                LUNES + timedelta(hours=1))
    sistema.despachar(remito.id_remito, LUNES + timedelta(hours=2))
    sistema.registrar_llegada(remito.id_remito, LUNES + timedelta(hours=3))
    return remito, muestra


def test_mascota_sin_responsable(sistema):
    with pytest.raises(ErrorOperacion):
        sistema.registrar_mascota(None, "Sin dueño", "Gato")


def test_turno_fuera_de_agenda_y_superpuesto(sistema, datos):
    _, veterinario, _, _, mascota = datos
    with pytest.raises(ErrorOperacion, match="fuera de la agenda"):
        sistema.reservar_turno(veterinario.id_veterinario, mascota.id_mascota, LUNES.replace(hour=13), 30)
    sistema.reservar_turno(veterinario.id_veterinario, mascota.id_mascota, LUNES, 30)
    with pytest.raises(ErrorOperacion, match="superpone"):
        sistema.reservar_turno(veterinario.id_veterinario, mascota.id_mascota, LUNES + timedelta(minutes=15), 30)
    sistema.reservar_turno(veterinario.id_veterinario, mascota.id_mascota, LUNES + timedelta(minutes=30), 30)


def test_cancelar_turno_libera_el_horario(sistema, datos):
    _, veterinario, _, _, mascota = datos
    turno = sistema.reservar_turno(veterinario.id_veterinario, mascota.id_mascota, LUNES, 30)
    sistema.cambiar_estado_turno(veterinario.id_veterinario, turno.id_turno, "cancelar")
    sistema.reservar_turno(veterinario.id_veterinario, mascota.id_mascota, LUNES, 30)


def test_atencion_bloqueada_si_faltan_vacunas_obligatorias(sistema, datos):
    _, veterinario, vacuna, _, mascota = datos
    with pytest.raises(ErrorOperacion, match="Antirrábica"):
        sistema.registrar_atencion(mascota.id_mascota, veterinario.id_veterinario, "CONSULTA", "Control", "", LUNES)
    vacunar(sistema, mascota, vacuna)
    atencion = sistema.registrar_atencion(mascota.id_mascota, veterinario.id_veterinario, "CONSULTA", "Control",
                                          "", LUNES)
    assert [a.id_atencion for a, _ in sistema.atenciones()] == [atencion.id_atencion]


def test_circuito_completo_con_precinto_intacto(sistema, datos):
    remito, muestra = circuito_hasta_llegada(sistema, datos)
    sistema.recibir(remito.id_remito, LUNES + timedelta(hours=3, minutes=10), True)
    sistema.registrar_resultado(muestra.id_muestra, LUNES + timedelta(hours=5), "Normal")
    estados = [h.nombre_estado for h in sistema.muestra(muestra.id_muestra).obtener_historial()]
    assert estados == ["EXTRAIDA", "EMPAQUETADA", "EN_TRANSITO", "RECIBIDA", "ANALIZADA"]
    assert sistema.conservadoras()[0].esta_disponible()          # se libera al recibir


def test_precinto_roto_rechaza_y_no_deja_analizar(sistema, datos):
    remito, muestra = circuito_hasta_llegada(sistema, datos)
    sistema.recibir(remito.id_remito, LUNES + timedelta(hours=3, minutes=10), False)
    assert sistema.muestra(muestra.id_muestra).estado.obtener_nombre() == "RECHAZADA"
    with pytest.raises(ErrorOperacion, match="RECHAZADA"):
        sistema.registrar_resultado(muestra.id_muestra, LUNES + timedelta(hours=5), "No debe registrarse")
    assert sistema.resultado_de(muestra.id_muestra) is None
    assert [f["id_muestra"] for f in sistema.reporte("rechazadas")] == [muestra.id_muestra]


def test_no_se_recibe_sin_registrar_la_llegada(sistema, datos):
    clinica, veterinario, vacuna, conservadora, mascota = datos
    vacunar(sistema, mascota, vacuna)
    atencion = sistema.registrar_atencion(mascota.id_mascota, veterinario.id_veterinario, "CONSULTA", "x", "", LUNES)
    _, muestra = sistema.emitir_orden(atencion.id_atencion, "Hemograma", "Sangre", LUNES)
    remito = sistema.empaquetar(clinica.id_clinica, conservadora.id_conservadora, [muestra.id_muestra],
                                LUNES + timedelta(hours=1))
    sistema.despachar(remito.id_remito, LUNES + timedelta(hours=2))
    with pytest.raises(ErrorOperacion, match="llegada"):
        sistema.recibir(remito.id_remito, LUNES + timedelta(hours=3), True)


def test_comprobante_unico_por_atencion(sistema, datos):
    _, veterinario, vacuna, _, mascota = datos
    vacunar(sistema, mascota, vacuna)
    atencion = sistema.registrar_atencion(mascota.id_mascota, veterinario.id_veterinario, "CONTROL", "x", "", LUNES)
    sistema.emitir_comprobante(atencion.id_atencion, LUNES + timedelta(minutes=30))
    with pytest.raises(ErrorOperacion):
        sistema.emitir_comprobante(atencion.id_atencion, LUNES + timedelta(minutes=40))


def test_los_cuatro_reportes(sistema, datos):
    remito, muestra = circuito_hasta_llegada(sistema, datos)
    sistema.recibir(remito.id_remito, LUNES + timedelta(hours=3, minutes=10), True)
    sistema.registrar_resultado(muestra.id_muestra, LUNES + timedelta(hours=4), "Normal")
    assert len(sistema.reporte("atenciones")) == 1
    assert sistema.reporte("rechazadas") == []
    assert sistema.reporte("vacunas", date(2026, 11, 2)) == []
    tiempos = sistema.reporte("tiempos")[0]
    assert tiempos["tiempo_promedio_transito"] == timedelta(hours=1)
