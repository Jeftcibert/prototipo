# Matriz de casos de prueba de la T2 (CP-01 a CP-10) para el prototipo del Caso 13.
# Los resultados esperados se definieron a partir de la jerarquía R1-R4 antes de ejecutar el código.
# Uso: colocar este archivo junto a diagnostico_pc.py y ejecutar «python pruebas_t2.py».
import json
import tempfile
from pathlib import Path
import diagnostico_pc as d

res = []


def registrar(cid, desc, entrada, esperado, obtenido, ok):
    estado = "APROBADO" if ok else "FALLÓ"
    res.append({"id": cid, "desc": desc, "entrada": entrada, "esperado": esperado,
                "obtenido": obtenido, "estado": estado})
    print(f"{cid} | {desc} | {estado}")
    print(f"        esperado: {esperado}")
    print(f"        obtenido: {obtenido}")


def estado_de(cpu, minutos, ram, disco, libre):
    return d.evaluar(cpu, minutos, ram, disco, libre)


# CP-01 Escenario NORMAL
est, _, opo = estado_de(50, 0, 30, "SSD", 40)
registrar("CP-01", "Escenario Normal", "CPU 50 %, 0 min, RAM 30 %, SSD, libre 40 %",
          "NORMAL", est, est == "NORMAL" and not opo)

# CP-02 Escenario ADVERTENCIA (espacio libre bajo)
est, hall, _ = estado_de(40, 0, 20, "SSD", 10)
recs = d.recomendar(40, 0, 20, "SSD", 10)
registrar("CP-02", "Escenario Advertencia (libre 10 %)", "CPU 40 %, 0 min, RAM 20 %, SSD, libre 10 %",
          "ADVERTENCIA + liberar espacio", est + (" + liberar espacio" if any("liberar" in r for r in recs) else ""),
          est == "ADVERTENCIA" and any("liberar" in r for r in recs))

# CP-03 Escenario CRÍTICO con la ficha de PC-01 (equipo de referencia)
ref = d.EQUIPOS_REFERENCIA["PC-01"]
m, f = ref["metricas"], ref["ficha"]
est, _, opo = estado_de(m["cpu"], m["minutos"], m["ram"], f["disco"], m["libre"])
filas = d.tabla_mejoras(m["ram"], f["disco"], m["libre"], f)
ok = est == "CRÍTICO" and bool(opo) and filas[0][2].startswith("8 GB") and filas[1][2] == "SSD SATA"
registrar("CP-03", "Escenario Crítico (PC-01)", "CPU 90 %, 15 min, RAM 95 %, HDD SATA, libre 40 %",
          "CRÍTICO; RAM 4 GB→8 GB; SSD SATA", f"{est}; RAM {filas[0][1][:4]}→{filas[0][2][:4]}; {filas[1][2]}", ok)

# CP-04 Valores límite: ninguno activa alertas (comparaciones estrictas)
lim = [estado_de(50, 0, 80, "SSD", 40)[0], estado_de(40, 0, 20, "SSD", 15)[0], estado_de(85, 30, 40, "SSD", 40)[0]]
registrar("CP-04", "Valores límite RAM 80, libre 15, CPU 85", "RAM 80 %; libre 15 %; CPU 85 % con 30 min",
          "NORMAL, NORMAL, NORMAL", ", ".join(lim), lim == ["NORMAL"] * 3)

# CP-05 Duración de la CPU alta: pico (5 min) frente a sostenida (10 min)
pico, sost = estado_de(90, 5, 40, "SSD", 40)[0], estado_de(90, 10, 40, "SSD", 40)[0]
registrar("CP-05", "CPU 90 %: 5 min frente a 10 min", "CPU 90 % con 5 min y con 10 min; RAM 40 %; libre 40 %",
          "ADVERTENCIA y CRÍTICO", f"{pico} y {sost}", (pico, sost) == ("ADVERTENCIA", "CRÍTICO"))

# CP-06 HDD sin otras alertas: NORMAL con oportunidad de mejora
est, _, opo = estado_de(50, 0, 30, "HDD", 40)
registrar("CP-06", "HDD sin otras alertas", "CPU 50 %, 0 min, RAM 30 %, HDD, libre 40 %",
          "NORMAL + oportunidad SSD", est + (" + oportunidad SSD" if opo else ""), est == "NORMAL" and bool(opo))

# CP-07 Entradas inválidas en E1
rechazos = 0
for fn, val in [(lambda v: d.validar_porcentaje(v, "CPU"), "abc"), (d.validar_minutos, "-3"),
                (lambda v: d.validar_porcentaje(v, "RAM"), "120"), (lambda v: d.validar_porcentaje(v, "Libre"), "-5")]:
    try:
        fn(val)
    except ValueError as e:
        rechazos += 1
        print("   rechazado:", e)
registrar("CP-07", "Entradas inválidas (E1)", "CPU «abc»; minutos −3; RAM 120; libre −5",
          "Rechazar las 4 entradas", f"Rechazadas {rechazos}/4", rechazos == 4)

# CP-08 Compatibilidad (F04) con la ficha de PC-02: hay una ranura libre, se puede agregar módulo
ref2 = d.EQUIPOS_REFERENCIA["PC-02"]
m2, f2 = ref2["metricas"], ref2["ficha"]
recs2 = d.recomendar(m2["cpu"], m2["minutos"], m2["ram"], f2["disco"], m2["libre"], f2)
fila2 = d.tabla_mejoras(m2["ram"], f2["disco"], m2["libre"], f2)[0]
ok = any("agregar módulo DDR4" in r for r in recs2) and fila2[1] == "8 GB DDR4" and fila2[2].startswith("16 GB DDR4 (agregar")
registrar("CP-08", "Compatibilidad F04 con ficha PC-02", "RAM 85 %; ficha 8 GB DDR4, máx. 16 GB, 1 ranura libre",
          "Agregar módulo DDR4; 8 GB→16 GB", f"{'Agregar módulo DDR4' if ok else 'No coincide'}; {fila2[1][:4]}→{fila2[2][:5]}", ok)

# CP-09 F05: exportación con ID no válido y sin sobrescribir
with tempfile.TemporaryDirectory() as tmp:
    est, hall, opo = estado_de(90, 15, 95, "HDD", 40)
    recs = d.recomendar(90, 15, 95, "HDD", 40, f)
    texto = d.generar_reporte("PC/01 prueba", {"cpu": 90, "minutos": 15, "ram": 95, "disco": "HDD", "libre": 40},
                              est, hall, opo, recs, f)
    r1 = d.exportar_reporte(texto, "PC/01 prueba", tmp)
    r2 = d.exportar_reporte(texto, "PC/01 prueba", tmp)
    ok = (r1 != r2 and r1.parent == Path(tmp) and r2.parent == Path(tmp) and "CRÍTICO" in r1.read_text(encoding="utf-8")
          and "/" not in r1.name)
    nombre = r1.name.rsplit("_", 2)[0]
registrar("CP-09", "Exportar reporte (F05)", "ID «PC/01 prueba»; dos exportaciones seguidas",
          "2 archivos; reporte_PC_01_prueba_…", f"2 archivos; {nombre}_…" if ok else "No coincide", ok)

# CP-10 F01: carga de PC-01 a PC-03 y archivo de fichas dañado
with tempfile.TemporaryDirectory() as tmp:
    ruta = Path(tmp) / "fichas_equipos.json"
    d.cargar_referencias(ruta)
    cargadas = sorted(d.cargar_fichas(ruta))
    ruta.write_text("{esto no es json", encoding="utf-8")
    vacio = d.cargar_fichas(ruta) == {} and ruta.with_suffix(".bak").exists()
registrar("CP-10", "Fichas F01: carga y archivo dañado", "Cargar PC-01 a PC-03; luego un JSON dañado",
          "3 fichas; copia .bak sin error", f"{len(cargadas)} fichas; .bak {'creada' if vacio else 'no creada'}",
          cargadas == ["PC-01", "PC-02", "PC-03"] and vacio)

ruta_json = d.carpeta_datos() / "resultados_t2.json"
json.dump(res, open(ruta_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL aprobados:", sum(r["estado"] == "APROBADO" for r in res), "de", len(res))
print("Resultados guardados en:", ruta_json)
