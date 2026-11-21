# Caso 13 - Extensión de la vida útil de computadoras (Grupo 13)
# Prototipo de diagnóstico lógico. Usa datos ingresados por teclado (simulados).
# No escanea el hardware ni accede a archivos del usuario. Solo biblioteca estándar.


import json
import math
import re
from datetime import datetime
from pathlib import Path


# ---------- Umbrales preliminares del proyecto (reglas académicas, no pruebas de falla) ----------
UMBRAL_CPU = 85          # % de uso de CPU
UMBRAL_RAM = 80          # % de uso de RAM
UMBRAL_LIBRE = 15        # % mínimo de espacio libre
MIN_CPU_SOSTENIDO = 10   # minutos con CPU > UMBRAL_CPU para considerarlo sostenido
NOMBRE_CARPETA = "Diagnostico_PC"


def carpeta_datos():
    """Carpeta donde se guardan fichas, reportes y resultados: Documentos/Diagnostico_PC.
    Si no se puede crear, usa la carpeta actual. Siempre devuelve una ruta existente."""
    try:
        carpeta = Path.home() / "Documents" / NOMBRE_CARPETA
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    except OSError:
        return Path.cwd()


ARCHIVO_FICHAS = carpeta_datos() / "fichas_equipos.json"
TIPOS_RAM = ("DDR3", "DDR4", "DDR5")
INTERFACES = ("SATA", "M.2", "IDE")


# Equipos de referencia de la Tabla 2 del informe (valores simulados). Los minutos de CPU alta,
# el tipo/máximo de RAM, las ranuras y la interfaz son supuestos del prototipo (no figuran en la Tabla 2).
EQUIPOS_REFERENCIA = {
    "PC-01": {"ficha": {"id": "PC-01", "cpu_modelo": "Intel Core i3 (4.ª gen)", "ram_gb": 4, "tipo_ram": "DDR3",
                        "ram_max_gb": 8, "ranuras_libres": 0, "disco": "HDD", "interfaz": "SATA"},
              "metricas": {"cpu": 90, "minutos": 15, "ram": 95, "libre": 40}},
    "PC-02": {"ficha": {"id": "PC-02", "cpu_modelo": "Intel Core i5 (6.ª gen)", "ram_gb": 8, "tipo_ram": "DDR4",
                        "ram_max_gb": 16, "ranuras_libres": 1, "disco": "HDD", "interfaz": "SATA"},
              "metricas": {"cpu": 65, "minutos": 0, "ram": 85, "libre": 60}},
    "PC-03": {"ficha": {"id": "PC-03", "cpu_modelo": "AMD A8", "ram_gb": 4, "tipo_ram": "DDR3",
                        "ram_max_gb": 16, "ranuras_libres": 1, "disco": "HDD", "interfaz": "SATA"},


              "metricas": {"cpu": 88, "minutos": 15, "ram": 98, "libre": 30}},
}


# ---------- Validación de entradas ----------
def validar_porcentaje(texto, nombre):
    """Devuelve un float entre 0 y 100 o lanza ValueError con un mensaje claro."""
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"{nombre}: '{texto}' no es un número.")
    if not 0 <= valor <= 100:
        raise ValueError(f"{nombre}: {valor:g} fuera de rango (debe estar entre 0 y 100).")
    return valor


def validar_minutos(texto):
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"Minutos: '{texto}' no es un número.")
    if not math.isfinite(valor):
        raise ValueError(f"Minutos: '{texto}' no es un número finito.")
    if valor < 0:
        raise ValueError("Minutos: no puede ser negativo.")
    return valor


def validar_entero(texto, nombre, minimo=0):
    try:
        valor = int(str(texto).strip())
    except ValueError:
        raise ValueError(f"{nombre}: '{texto}' no es un número entero.")
    if valor < minimo:
        raise ValueError(f"{nombre}: debe ser mayor o igual a {minimo}.")
    return valor


def validar_texto(texto, nombre):
    """El campo no puede estar vacío."""
    valor = str(texto).strip()
    if not valor:
        raise ValueError(f"{nombre}: no puede estar vacío.")
    return valor


def validar_ram_maxima(texto, instalada):
    """La RAM máxima de la placa no puede ser menor que la RAM instalada."""
    valor = validar_entero(texto, "RAM máxima", 1)
    if valor < instalada:
        raise ValueError(f"RAM máxima: {valor} GB es menor que la RAM instalada ({instalada} GB).")
    return valor


def validar_opcion(texto, nombre, opciones):
    valor = str(texto).strip().upper()
    if valor not in opciones:
        raise ValueError(f"{nombre}: '{texto}' no válido (use: {', '.join(opciones)}).")
    return valor


def pedir(mensaje, validador, *args):
    """Repite la pregunta hasta que el dato sea válido (manejo de entradas inválidas)."""
    while True:
        try:
            return validador(input(mensaje), *args)
        except ValueError as error:
            print(" [ENTRADA INVÁLIDA]", error)


# ---------- F01: registro de hardware (ficha del equipo) ----------
def cargar_fichas(ruta=ARCHIVO_FICHAS):
    if not Path(ruta).exists():
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (json.JSONDecodeError, OSError):
        copia = Path(ruta).with_suffix(".bak")


        try:
            Path(ruta).replace(copia)
            print(f" [AVISO] El archivo de fichas estaba dañado; se guardó una copia en {copia}.")
        except OSError:
            print(" [AVISO] No se pudo leer el archivo de fichas; se usará una lista vacía.")
        return {}


def guardar_ficha(ficha, ruta=ARCHIVO_FICHAS):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    fichas = cargar_fichas(ruta)
    fichas[ficha["id"]] = ficha
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(fichas, archivo, ensure_ascii=False, indent=2)


def registrar_equipo(ruta=ARCHIVO_FICHAS):
    print("\n--- F01: REGISTRO DE HARDWARE ---")
    ficha = {"id": pedir("ID del equipo (ej. PC-01): ", validar_texto, "ID").upper()}
    ficha["cpu_modelo"] = pedir("Modelo de CPU: ", validar_texto, "Modelo de CPU")
    ficha["ram_gb"] = pedir("RAM instalada (GB): ", validar_entero, "RAM instalada", 1)
    ficha["tipo_ram"] = pedir("Tipo de RAM (DDR3/DDR4/DDR5): ", validar_opcion, "Tipo de RAM", TIPOS_RAM)
    ficha["ram_max_gb"] = pedir("RAM máxima soportada por la placa (GB): ", validar_ram_maxima, ficha["ram_gb"])
    ficha["ranuras_libres"] = pedir("Ranuras de RAM libres: ", validar_entero, "Ranuras libres", 0)
    ficha["disco"] = pedir("Tipo de disco (HDD/SSD): ", validar_opcion, "Disco", ("HDD", "SSD"))
    ficha["interfaz"] = pedir("Interfaz de almacenamiento (SATA/M.2/IDE): ", validar_opcion,
                               "Interfaz", INTERFACES)
    guardar_ficha(ficha, ruta)
    print(f" Ficha de {ficha['id']} guardada en: {ruta}")
    return ficha


def cargar_referencias(ruta=ARCHIVO_FICHAS):
    """Guarda como fichas F01 los equipos PC-01, PC-02 y PC-03 de la Tabla 2 del informe."""
    for datos in EQUIPOS_REFERENCIA.values():
        guardar_ficha(dict(datos["ficha"]), ruta)
    print(f" Equipos de referencia cargados ({', '.join(EQUIPOS_REFERENCIA)}) en: {ruta}")


# ---------- F02 y F03: evaluación de métricas e identificación de señales de limitación ----------
def evaluar(cpu, minutos_cpu, ram, disco, libre):
    """Aplica la jerarquía de decisión. Devuelve (estado, hallazgos, oportunidades)."""
    hallazgos, oportunidades = [], []
    cpu_sostenida = cpu > UMBRAL_CPU and minutos_cpu >= MIN_CPU_SOSTENIDO
    cpu_pico = cpu > UMBRAL_CPU and minutos_cpu < MIN_CPU_SOSTENIDO
    ram_alta = ram > UMBRAL_RAM
    poco_espacio = libre < UMBRAL_LIBRE


    # Jerarquía: R1/R2 -> CRÍTICO; si no, R3/R4 -> ADVERTENCIA; si no, NORMAL.
    if cpu_sostenida or ram_alta:
        estado = "CRÍTICO"
    elif poco_espacio or cpu_pico:
        estado = "ADVERTENCIA"
    else:
        estado = "NORMAL"


    if cpu_sostenida:
        hallazgos.append(f"CPU > {UMBRAL_CPU} % de forma sostenida ({minutos_cpu:g} min). "
                         "Señal preliminar: reevaluar con una carga representativa.")
    if cpu_pico:
        hallazgos.append(f"CPU > {UMBRAL_CPU} % solo {minutos_cpu:g} min (< {MIN_CPU_SOSTENIDO} min): "
                         "posible pico transitorio; volver a medir.")
    if ram_alta:
        hallazgos.append(f"RAM > {UMBRAL_RAM} %: posible presión de memoria. El uso efectivo de "
                         "paginación requiere indicadores adicionales.")
    if poco_espacio:
        hallazgos.append(f"Espacio libre < {UMBRAL_LIBRE} %: liberar espacio de almacenamiento.")
    if disco == "HDD":
        oportunidades.append("OPORTUNIDAD DE MEJORA: el equipo usa HDD; evaluar migración a SSD "
                             "(no cambia el estado por sí sola).")
    if not hallazgos and not oportunidades:
        hallazgos.append("Equipo en buen estado según las reglas preliminares.")
    return estado, hallazgos, oportunidades


# ---------- F04: recomendaciones con verificación de compatibilidad ----------
def recomendar(cpu, minutos_cpu, ram, disco, libre, ficha=None):
    """Devuelve la lista de recomendaciones (preliminares, sujetas a validación técnica)."""
    recs = []
    cpu_sostenida = cpu > UMBRAL_CPU and minutos_cpu >= MIN_CPU_SOSTENIDO
    cpu_pico = cpu > UMBRAL_CPU and minutos_cpu < MIN_CPU_SOSTENIDO
    if ram > UMBRAL_RAM:


        if ficha is None:
            recs.append("RAM: evaluar ampliación (recomendación preliminar). Sin ficha F01, la "
                        "compatibilidad (tipo de memoria, ranuras, máximo de la placa) debe "
                        "validarse técnicamente.")
        elif ficha["ram_gb"] >= ficha["ram_max_gb"]:
            recs.append(f"RAM: la placa admite como máximo {ficha['ram_max_gb']} GB y ya hay "
                        f"{ficha['ram_gb']} GB; no es posible ampliar. Revisar la carga de aplicaciones.")
        elif ficha["ranuras_libres"] > 0:
            recs.append(f"RAM: agregar módulo {ficha['tipo_ram']} (hasta {ficha['ram_max_gb']} GB en total; "
                        f"{ficha['ranuras_libres']} ranura(s) libre(s)). Verificar consumo sostenido.")
        else:
            recs.append(f"RAM: sin ranuras libres; solo sustituir módulos {ficha['tipo_ram']} por otros de "
                        f"mayor capacidad (máx. {ficha['ram_max_gb']} GB). Verificar consumo sostenido.")
    if disco == "HDD":
        if ficha is None:
            recs.append("Disco: evaluar migración a SSD; verificar bahía/interfaz disponible.")
        elif ficha["interfaz"] in ("SATA", "M.2"):
            recs.append(f"Disco: migración a SSD {ficha['interfaz']} viable según la ficha; "
                        "confirmar espacio físico y clonación.")
        else:
            recs.append(f"Disco: interfaz {ficha['interfaz']} no admite SSD SATA/M.2 estándar; "
                        "requiere validación técnica antes de recomendar.")
    if libre < UMBRAL_LIBRE:
        recs.append("Almacenamiento: liberar espacio y volver a medir después de aplicar la mejora.")
    if cpu_pico:
        recs.append("CPU: volver a medir con una carga representativa antes de concluir.")
    if cpu_sostenida:
        recs.append("CPU: aplicar primero las mejoras de RAM/SSD y volver a medir. El reemplazo del "
                    "equipo solo se evalúa si persiste el problema, considerando compatibilidad, "
                    "antigüedad, requisitos del software, estado general y costos.")
    if not recs:
        recs.append("Sin acciones inmediatas. Mantener monitoreo periódico.")
    return recs


def tabla_mejoras(ram, disco, libre, ficha=None):
    """Compara la configuración actual con la mejora propuesta. Devuelve filas (componente, actual, propuesta).
    Criterio del prototipo: si la RAM supera el umbral, proponer duplicarla sin pasar del máximo de la placa."""
    if ficha is None:
        return [("RAM", "sin ficha F01", "validar compatibilidad antes de proponer una capacidad" if ram > UMBRAL_RAM
                  else "sin cambio"),
                 ("Disco", disco, "SSD, sujeto a validar bahía e interfaz" if disco == "HDD" else "sin cambio")]
    filas = []
    if ram > UMBRAL_RAM:
        actual = f"{ficha['ram_gb']} GB {ficha['tipo_ram']}"
        if ficha["ram_gb"] >= ficha["ram_max_gb"]:
            filas.append(("RAM", actual, f"sin ampliación posible (máx. {ficha['ram_max_gb']} GB)"))
        else:
            meta = min(ficha["ram_gb"] * 2, ficha["ram_max_gb"])
            forma = "agregar módulo" if ficha["ranuras_libres"] > 0 else "sustituir módulos, sin ranuras libres"
            filas.append(("RAM", actual, f"{meta} GB {ficha['tipo_ram']} ({forma})"))
    else:
        filas.append(("RAM", f"{ficha['ram_gb']} GB {ficha['tipo_ram']}", "sin cambio"))
    if disco == "HDD":
        if ficha["interfaz"] in ("SATA", "M.2"):
            filas.append(("Disco", f"HDD ({ficha['interfaz']})", f"SSD {ficha['interfaz']}"))
        else:
            filas.append(("Disco", f"HDD ({ficha['interfaz']})", "SSD solo tras validación técnica"))
    else:
        filas.append(("Disco", f"SSD ({ficha['interfaz']})", "sin cambio"))
    if libre < UMBRAL_LIBRE:
        filas.append(("Espacio libre", f"{libre:g} %", f"liberar espacio hasta superar {UMBRAL_LIBRE} %"))
    return filas


# ---------- F05: reporte consolidado y exportación ----------
def generar_reporte(equipo_id, entrada, estado, hallazgos, oportunidades, recomendaciones, ficha=None):
    lineas = ["=" * 60, "REPORTE DE DIAGNÓSTICO - CASO 13 (datos simulados/ingresados)",
              f"Equipo: {equipo_id}     Fecha: {datetime.now():%d/%m/%Y %H:%M}", "=" * 60]
    if ficha:
        lineas += ["[Configuración actual - ficha F01]",
                   f" CPU: {ficha['cpu_modelo']} | RAM: {ficha['ram_gb']} GB {ficha['tipo_ram']} "
                   f"(máx. {ficha['ram_max_gb']} GB, {ficha['ranuras_libres']} ranura(s) libre(s))",
                   f" Disco: {ficha['disco']} ({ficha['interfaz']})"]
    lineas += ["[Métricas ingresadas]",
               f" CPU {entrada['cpu']:g} % ({entrada['minutos']:g} min) | RAM {entrada['ram']:g} % | "
               f"Disco {entrada['disco']} | Libre {entrada['libre']:g} %",
               f"[Estado] {estado}", "[Hallazgos]"]
    lineas += [f" - {h}" for h in hallazgos]
    lineas += [f" - {o}" for o in oportunidades]
    lineas += ["[Configuración actual -> mejora propuesta]"]
    lineas += [f" {c:<14}{a:<22}-> {p}" for c, a, p in
               tabla_mejoras(entrada["ram"], entrada["disco"], entrada["libre"], ficha)]
    lineas += ["[Recomendaciones]"]
    lineas += [f" - {r}" for r in recomendaciones]
    lineas += ["[Nota] Reglas preliminares del proyecto; no sustituyen un diagnóstico técnico con "


               "cargas de trabajo representativas. Las recomendaciones de RAM y SSD son preliminares: "
               "no se han comprobado físicamente en el equipo.", "=" * 60]
    return "\n".join(lineas)


def exportar_reporte(texto, equipo_id, carpeta=None):
    """Guarda el reporte (reporte_<ID>_<fecha>.txt) sin sobrescribir los anteriores y devuelve su ruta."""
    carpeta = Path(carpeta) if carpeta else carpeta_datos()
    carpeta.mkdir(parents=True, exist_ok=True)
    ident = re.sub(r"[^A-Za-z0-9_-]+", "_", str(equipo_id)).strip("_")[:40] or "equipo"
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = carpeta / f"reporte_{ident}_{sello}.txt"
    contador = 1
    while ruta.exists(): # no sobrescribe reportes anteriores del mismo equipo
        contador += 1
        ruta = carpeta / f"reporte_{ident}_{sello}_{contador}.txt"
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(texto)
    return ruta


# ---------- Flujo principal ----------
def diagnosticar_equipo(ruta=ARCHIVO_FICHAS):
    print("\n--- F02-F05: EVALUACIÓN DEL EQUIPO ---")
    equipo_id = pedir("ID del equipo: ", validar_texto, "ID").upper()
    ficha = cargar_fichas(ruta).get(equipo_id)
    print(" Ficha F01 encontrada." if ficha else " Sin ficha F01: la compatibilidad queda sujeta a validación.")
    ref = EQUIPOS_REFERENCIA.get(equipo_id, {}).get("metricas") if ficha else None
    if ref and input(" Equipo de la Tabla 2. ¿Usar sus métricas de referencia? (S/N): ").strip().upper() == "S":
         entrada = {**ref, "disco": ficha["disco"]}
         print(f" Métricas de referencia: CPU {ref['cpu']} % ({ref['minutos']} min), RAM {ref['ram']} %, "
               f"libre {ref['libre']} %")
    else:
         entrada = {
             "cpu": pedir("Uso de CPU (%): ", validar_porcentaje, "CPU"),
             "minutos": pedir("Minutos con ese uso de CPU: ", validar_minutos),
             "ram": pedir("Uso de RAM (%): ", validar_porcentaje, "RAM"),
             "disco": ficha["disco"] if ficha else pedir("Tipo de disco (HDD/SSD): ", validar_opcion, "Disco", ("HDD", "SSD")),
             "libre": pedir("Espacio libre (%): ", validar_porcentaje, "Espacio libre"),
         }
    estado, hallazgos, oportunidades = evaluar(entrada["cpu"], entrada["minutos"], entrada["ram"],
                                                entrada["disco"], entrada["libre"])
    recs = recomendar(entrada["cpu"], entrada["minutos"], entrada["ram"], entrada["disco"],
                       entrada["libre"], ficha)
    reporte = generar_reporte(equipo_id, entrada, estado, hallazgos, oportunidades, recs, ficha)
    print("\n" + reporte)
    if input("\n¿Exportar reporte a archivo local? (S/N): ").strip().upper() == "S":
         print(" Reporte guardado en:", exportar_reporte(reporte, equipo_id))


def menu():
    print(f"Carpeta de datos (fichas y reportes): {carpeta_datos()}")
    while True:
        print("\n=== DIAGNÓSTICO DE VIDA ÚTIL DE PC ===\n1. Registrar equipo (F01)\n"
              "2. Evaluar equipo (F02-F05)\n3. Ver fichas registradas\n"
              "4. Cargar equipos de referencia (PC-01 a PC-03)\n5. Salir")
        opcion = input("Opción: ").strip()
        if opcion == "1":
            registrar_equipo()
        elif opcion == "2":
            diagnosticar_equipo()
        elif opcion == "3":
            for id_equipo, f in cargar_fichas().items():
                print(f" {id_equipo}: {f['cpu_modelo']} | {f['ram_gb']} GB {f['tipo_ram']} | {f['disco']} {f['interfaz']}")
        elif opcion == "4":
            cargar_referencias()
        elif opcion == "5":
            break
        else:
            print(" [ENTRADA INVÁLIDA] Elija 1, 2, 3, 4 o 5.")


if __name__ == "__main__":
    try:
        menu()
    except (EOFError, KeyboardInterrupt):
        print("\nPrograma finalizado.")
