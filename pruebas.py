# Ejecuta la matriz de pruebas del prototipo (casos T01-T11) y compara con el resultado esperado.
import json
import tempfile
from pathlib import Path
import diagnostico_pc as d


CASOS = [
  # id, descripción, (cpu, min, ram, disco, libre), estado esperado
  ("T01","Normal",                     (50,0,30,"SSD",40), "NORMAL"),
  ("T02","Espacio libre bajo (10 %)", (40,0,20,"SSD",10), "ADVERTENCIA"),
  ("T03","RAM crítica (90 %)",         (58,0,90,"SSD",40), "CRÍTICO"),
  ("T04","Límite RAM = 80 %",          (50,0,80,"SSD",40), "NORMAL"),
  ("T05","Límite libre = 15 %",        (40,0,20,"SSD",15), "NORMAL"),
  ("T06","Límite CPU = 85 % (30 min)", (85,30,40,"SSD",40), "NORMAL"),
  ("T07","CPU 90 % por 5 min (pico)", (90,5,40,"SSD",40), "ADVERTENCIA"),
  ("T08","CPU 90 % por 10 min",        (90,10,40,"SSD",40), "CRÍTICO"),
  ("T09","HDD sin otras alertas",      (50,0,30,"HDD",40), "NORMAL"),
  ("T10","Combinación de alertas",     (90,15,95,"HDD",10), "CRÍTICO"),
]
res = []
for cid, desc, (cpu,mn,ram,disco,libre), esperado in CASOS:
     estado, hall, opo = d.evaluar(cpu,mn,ram,disco,libre)
     ok = "APROBADO" if estado == esperado else "FALLÓ"
     res.append({"id":cid,"desc":desc,"entrada":f"CPU {cpu} %, {mn} min, RAM {ram} %, {disco}, libre {libre} %",
                 "esperado":esperado,"obtenido":estado + (" + oportunidad SSD" if opo else ""),"estado":ok})
     extra = " +SSD" if opo else ""
     print(f"{cid} | {desc:28} | esp: {esperado:11} | obt: {estado + extra:16} | {ok}")
# T11: entradas inválidas
invalidas = [("CPU","abc",d.validar_porcentaje),("RAM","120",d.validar_porcentaje),
              ("Disco","NVME",None),("Libre","-5",d.validar_porcentaje)]


rechazos = 0
for nom, val, fn in invalidas:
    try:
        if fn is None: d.validar_opcion(val,"Disco",("HDD","SSD"))
        else: fn(val,nom)
    except ValueError as e:
        rechazos += 1; print(" rechazado:", e)
ok = "APROBADO" if rechazos == 4 else "FALLÓ"
print(f"T11 | Entradas inválidas            | rechazadas {rechazos}/4 | {ok}")
res.append({"id":"T11","desc":"Entradas inválidas","entrada":"CPU 'abc'; RAM 120; disco 'NVME'; libre -5",
             "esperado":"Rechazar las 4 entradas","obtenido":f"Rechazadas {rechazos}/4","estado":ok})
# T12-T15: F04, verificación de compatibilidad con la ficha del equipo
def ficha_base(**cambios):
    f = {"id": "PC-X", "cpu_modelo": "Prueba", "ram_gb": 4, "tipo_ram": "DDR3", "ram_max_gb": 8,
         "ranuras_libres": 1, "disco": "HDD", "interfaz": "SATA"}
    f.update(cambios)
    return f


def caso_f04(cid, desc, entrada, esperado, ficha, ram, disco, texto_esperado, en_tabla=False):
    recs = d.recomendar(50, 0, ram, disco, 40, ficha)
    if en_tabla:
        recs = recs + [" ".join(c for fila in d.tabla_mejoras(ram, disco, 40, ficha) for c in fila)]
    ok = "APROBADO" if any(texto_esperado in r for r in recs) else "FALLÓ"
    print(f"{cid} | {desc:36} | {ok}")
    res.append({"id": cid, "desc": desc, "entrada": entrada, "esperado": esperado,
                 "obtenido": esperado if ok == "APROBADO" else "No coincide", "estado": ok})


caso_f04("T12", "RAM ya está en el máximo de la placa", "RAM 8/8 GB, uso 90 %",
         "Sin ampliación posible", ficha_base(ram_gb=8), 90, "SSD", "no es posible ampliar")
caso_f04("T13", "Sin ranuras libres", "RAM 4/8 GB, 0 ranuras, uso 90 %",
         "Sustituir módulos (no agregar)", ficha_base(ranuras_libres=0), 90, "SSD", "sin ranuras libres")
caso_f04("T14", "Interfaz IDE (SSD no estándar)", "HDD con interfaz IDE",
         "Requiere validación técnica", ficha_base(interfaz="IDE"), 30, "HDD", "requiere validación técnica")
caso_f04("T15", "Equipo sin ficha F01", "RAM 90 %, HDD, sin ficha",
         "Compatibilidad sujeta a validación", None, 90, "HDD", "validarse técnicamente")
# T16: validación de la ficha F01 (campo vacío y RAM máxima menor que la instalada)
rech16 = 0
for fn, args in [(d.validar_texto, ("   ", "ID")), (d.validar_ram_maxima, ("4", 8))]:
    try:
        fn(*args)
    except ValueError as e:
        rech16 += 1; print(" rechazado:", e)
ok = "APROBADO" if rech16 == 2 else "FALLÓ"
print(f"T16 | Validación de la ficha F01            | rechazadas {rech16}/2 | {ok}")
res.append({"id": "T16", "desc": "Validación de la ficha F01", "entrada": "ID vacío; RAM máxima 4 GB con 8 GB instalados",
            "esperado": "Rechazar las 2 entradas", "obtenido": f"Rechazadas {rech16}/2", "estado": ok})
# T17: minutos no finitos (nan, inf) y negativos deben rechazarse
rech17 = 0
for v in ("nan", "inf", "-3"):
    try:
        d.validar_minutos(v)
    except ValueError as e:
        rech17 += 1; print(" rechazado:", e)
ok = "APROBADO" if rech17 == 3 else "FALLÓ"
print(f"T17 | Minutos no finitos o negativos        | rechazadas {rech17}/3 | {ok}")
res.append({"id": "T17", "desc": "Minutos no finitos o negativos", "entrada": "minutos «nan», «inf» y −3",
            "esperado": "Rechazar las 3 entradas", "obtenido": f"Rechazadas {rech17}/3", "estado": ok})


# Integración con el programa principal: F01 (guardar/leer ficha) y F05 (exportar reporte)
with tempfile.TemporaryDirectory() as tmp:
    ficha = {"id": "PC-TEST", "cpu_modelo": "Prueba", "ram_gb": 4, "tipo_ram": "DDR3", "ram_max_gb": 8,
             "ranuras_libres": 1, "disco": "HDD", "interfaz": "SATA"}
    ruta = Path(tmp) / "fichas_equipos.json"
    d.guardar_ficha(ficha, ruta)
    f_ok = d.cargar_fichas(ruta).get("PC-TEST") == ficha
    est, hall, opo = d.evaluar(58, 0, 90, "HDD", 40)
    recs = d.recomendar(58, 0, 90, "HDD", 40, ficha)
    texto = d.generar_reporte("PC-TEST", {"cpu": 58, "minutos": 0, "ram": 90, "disco": "HDD", "libre": 40},
                              est, hall, opo, recs, ficha)
    ruta_rep = d.exportar_reporte(texto, "PC-TEST", tmp)
    r_ok = ruta_rep.exists() and "CRÍTICO" in ruta_rep.read_text(encoding="utf-8")
# Integración 3: tabla actual -> propuesta con la ficha de PC-01 (RAM 4 GB, máx. 8 GB, sin ranuras libres)
m1 = d.EQUIPOS_REFERENCIA["PC-01"]
filas = d.tabla_mejoras(m1["metricas"]["ram"], "HDD", m1["metricas"]["libre"], m1["ficha"])
t_ok = filas[0][1].startswith("4 GB") and filas[0][2].startswith("8 GB") and filas[1][2] == "SSD SATA"
# Integración 4: carga de los equipos de referencia PC-01 a PC-03 como fichas F01
with tempfile.TemporaryDirectory() as tmp2:
    ruta2 = Path(tmp2) / "fichas_equipos.json"
    d.cargar_referencias(ruta2)
    c_ok = sorted(d.cargar_fichas(ruta2)) == ["PC-01", "PC-02", "PC-03"]
# Integración 5: un archivo de fichas dañado no debe detener el programa
with tempfile.TemporaryDirectory() as tmp3:
    ruta3 = Path(tmp3) / "fichas_equipos.json"
    ruta3.write_text("{esto no es json", encoding="utf-8")
    dañado_ok = d.cargar_fichas(ruta3) == {} and ruta3.with_suffix(".bak").exists()
# Integración 6 y 7: ID con caracteres no válidos y dos exportaciones sucesivas del mismo equipo
with tempfile.TemporaryDirectory() as tmp4:


    r1 = d.exportar_reporte("uno", "PC/01 prueba", tmp4)
    r2 = d.exportar_reporte("dos", "PC/01 prueba", tmp4)
    id_ok = r1.exists() and r1.parent == Path(tmp4)
    sobre_ok = r1 != r2 and r1.read_text(encoding="utf-8") == "uno" and r2.read_text(encoding="utf-8") == "dos"
print(f"INT | F01 ficha guardada y recuperada | {'APROBADO' if f_ok else 'FALLÓ'}")
print(f"INT | F05 reporte exportado y leído   | {'APROBADO' if r_ok else 'FALLÓ'}")
print(f"INT | F05 tabla actual -> propuesta    | {'APROBADO' if t_ok else 'FALLÓ'}")
print(f"INT | F01 carga de PC-01 a PC-03       | {'APROBADO' if c_ok else 'FALLÓ'}")
print(f"INT | F01 archivo de fichas dañado     | {'APROBADO' if dañado_ok else 'FALLÓ'}")
print(f"INT | F05 ID con caracteres no válidos | {'APROBADO' if id_ok else 'FALLÓ'}")
print(f"INT | F05 reportes sin sobrescritura    | {'APROBADO' if sobre_ok else 'FALLÓ'}")


# Guardar resultados en la carpeta de datos (Documentos/Diagnostico_PC)
ruta_json = d.carpeta_datos() / "resultados_pruebas.json"
json.dump(res, open(ruta_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL aprobados:", sum(r["estado"] == "APROBADO" for r in res), "de", len(res))
print("Resultados guardados en:", ruta_json)
