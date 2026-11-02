"""
Crea veterinaria.db con datos de demostración para probar la interfaz.

Todo se carga a través de SistemaVeterinaria, así que pasa por las mismas
reglas del dominio que usa la interfaz. Uso:  python -m veterinaria.datos_demo
(o lo hace main.py automáticamente si la base no existe).
"""
from datetime import date, datetime, time, timedelta

from veterinaria.dominio.clinica.agenda_medica import DiaSemana
from veterinaria.servicios.sistema import RUTA_BD, SistemaVeterinaria

LUNES_A_VIERNES = [DiaSemana.LUNES, DiaSemana.MARTES, DiaSemana.MIERCOLES, DiaSemana.JUEVES, DiaSemana.VIERNES]


def dias_habiles_hacia_atras(cantidad, desde):
    dias, dia = [], desde
    while len(dias) < cantidad:
        dia -= timedelta(days=1)
        if dia.weekday() < 5:
            dias.append(dia)
    return list(reversed(dias))


def cargar(ruta=RUTA_BD):
    if ruta.exists():
        ruta.unlink()
    s = SistemaVeterinaria(ruta)
    hoy = date.today()

    centro = s.crear_clinica("Clínica Centro", "Av. Colón 1250, Córdoba", "351-4220011")
    nueva_cba = s.crear_clinica("Clínica Nueva Córdoba", "Bv. Illia 480, Córdoba", "351-4680022")
    gomez = s.crear_veterinario(centro.id_clinica, "Laura", "Gómez", "MP-1021", "Clínica general",
                                LUNES_A_VIERNES, time(8, 0), time(18, 0))
    pereyra = s.crear_veterinario(centro.id_clinica, "Martín", "Pereyra", "MP-1187", "Cirugía",
                                  [DiaSemana.LUNES, DiaSemana.MIERCOLES, DiaSemana.VIERNES], time(9, 0), time(13, 0))
    ledesma = s.crear_veterinario(nueva_cba.id_clinica, "Sofía", "Ledesma", "MP-1302", "Dermatología",
                                  LUNES_A_VIERNES, time(8, 0), time(18, 0))

    sextuple = s.crear_vacuna("Séxtuple canina", "Perro", True)
    rabia_perro = s.crear_vacuna("Antirrábica", "Perro", True)
    s.crear_vacuna("Tos de las perreras", "Perro", False)
    triple = s.crear_vacuna("Triple felina", "Gato", True)
    rabia_gato = s.crear_vacuna("Antirrábica", "Gato", True)
    for codigo in ("CI-01", "CI-02", "CI-03", "CI-04"):
        s.crear_conservadora(codigo)

    clientes = [
        s.registrar_cliente("Lucía", "Fernández", "30111222", "351-5551001", "lucia@mail.com"),
        s.registrar_cliente("Javier", "Moreno", "28999333", "351-5551002", "jmoreno@mail.com"),
        s.registrar_cliente("Camila", "Suárez", "35444777", "351-5551003", "camila@mail.com"),
        s.registrar_cliente("Ricardo", "Bustos", "27666555", "351-5551004", ""),
        s.registrar_cliente("Agustina", "Paz", "40123456", "351-5551005", "agus@mail.com"),
    ]
    datos_mascotas = [  # nombre, especie, raza, sexo, años, cliente, vacunada
        ("Luna", "Perro", "Labrador", "Hembra", 4, 0, True), ("Simón", "Gato", "Siamés", "Macho", 3, 0, True),
        ("Rocco", "Perro", "Bulldog francés", "Macho", 2, 1, True), ("Mora", "Gato", "Común europeo", "Hembra", 6, 2, True),
        ("Thor", "Perro", "Ovejero alemán", "Macho", 8, 3, True), ("Kira", "Perro", "Border collie", "Hembra", 3, 4, True),
        ("Nala", "Perro", "Mestiza", "Hembra", 1, 4, False), ("Milo", "Gato", "Persa", "Macho", 2, 2, False),
    ]
    mascotas = []
    for nombre, especie, raza, sexo, anios, ic, vacunada in datos_mascotas:
        m = s.registrar_mascota(clientes[ic].id_cliente, nombre, especie, raza,
                                hoy - timedelta(days=365 * anios), sexo)
        if vacunada:
            aplicada = hoy - timedelta(days=200)
            for vacuna in ((sextuple, rabia_perro) if especie == "Perro" else (triple, rabia_gato)):
                s.aplicar_vacuna(m.id_mascota, vacuna.id_vacuna, aplicada, aplicada + timedelta(days=365))
        mascotas.append(m)
    vacunadas = mascotas[:6]

    # --- atenciones en los últimos 12 días hábiles (con turno las de Gómez)
    motivos = [("CONSULTA", "Vómitos y decaimiento", "Gastroenteritis"), ("CONTROL", "Control anual", "Sano"),
               ("URGENCIA", "Traumatismo por caída", "Contusiones"), ("CONSULTA", "Pérdida de pelo", "Dermatitis"),
               ("CONSULTA", "Tos persistente", "Traqueobronquitis"), ("CONTROL", "Control post tratamiento", "Mejoría")]
    atenciones = []
    for i, dia in enumerate(dias_habiles_hacia_atras(12, hoy)):
        veterinario = ledesma if i % 3 == 2 else gomez
        mascota = vacunadas[i % len(vacunadas)]
        tipo, motivo, diagnostico = motivos[i % len(motivos)]
        inicio = datetime.combine(dia, time(9 + i % 6, 0))
        turno = s.reservar_turno(veterinario.id_veterinario, mascota.id_mascota, inicio, 30, motivo)
        s.cambiar_estado_turno(veterinario.id_veterinario, turno.id_turno, "confirmar")
        atenciones.append(s.registrar_atencion(mascota.id_mascota, veterinario.id_veterinario, tipo, motivo,
                                               diagnostico, inicio, turno.id_turno))

    # --- derivaciones: una muestra por orden
    estudios = [("Hemograma completo", "Sangre"), ("Urianálisis", "Orina"), ("Coproparasitológico", "Heces"),
                ("Perfil bioquímico", "Sangre")]
    muestras = []
    for i, atencion in enumerate(atenciones):
        if i % 4 == 1:
            continue
        estudio, tipo_muestra = estudios[i % len(estudios)]
        _, muestra = s.emitir_orden(atencion.id_atencion, estudio, tipo_muestra,
                                    atencion.fecha_hora + timedelta(minutes=20))
        muestras.append((muestra, atencion))

    # --- remitos de a dos muestras: recorren todo el circuito (el segundo llega con el precinto roto)
    conservadoras = s.conservadoras()
    lotes = [muestras[i:i + 2] for i in range(0, len(muestras) - 1, 2)]
    for n, lote in enumerate(lotes):
        ultima = max(m.fecha_extraccion for m, _ in lote)
        clinica = s.clinica_de_veterinario(lote[0][1].veterinario.id_veterinario)
        if n == len(lotes) - 1:
            break    # el último lote queda sin empaquetar para probar desde la interfaz
        remito = s.empaquetar(clinica.id_clinica, conservadoras[n % len(conservadoras)].id_conservadora,
                              [m.id_muestra for m, _ in lote], ultima + timedelta(hours=1))
        salida = ultima + timedelta(hours=2)
        s.despachar(remito.id_remito, salida, "Moto Express Salud")
        if n == len(lotes) - 2:
            continue    # este remito queda en tránsito
        llegada = salida + timedelta(hours=1, minutes=30)
        s.registrar_llegada(remito.id_remito, llegada)
        s.recibir(remito.id_remito, llegada + timedelta(minutes=15), precinto_intacto=(n != 1),
                  observaciones="Control de ingreso")
        for k, (muestra, _) in enumerate(lote):
            if n != 1 and not (n == 0 and k == 1):
                s.registrar_resultado(muestra.id_muestra, llegada + timedelta(hours=3 + k),
                                      "Valores dentro de parámetros de referencia", "Validado por laboratorio")

    # --- comprobantes
    for atencion in atenciones[:-3]:
        s.emitir_comprobante(atencion.id_atencion, atencion.fecha_hora + timedelta(minutes=40))

    # --- turnos de mañana para la agenda
    manana = hoy + timedelta(days=1)
    while manana.weekday() >= 5:
        manana += timedelta(days=1)
    for k, mascota in enumerate(vacunadas[:3]):
        s.reservar_turno(gomez.id_veterinario, mascota.id_mascota, datetime.combine(manana, time(10 + k, 0)), 30,
                         "Control programado")
    s.cerrar()
    print(f"Base de demostración creada en {ruta}")


if __name__ == "__main__":
    cargar()
