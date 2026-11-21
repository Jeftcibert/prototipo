import sys, json, itertools, re
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import diagnostico_pc as d
fichas = {"none": None,
 "PC-01": d.EQUIPOS_REFERENCIA["PC-01"]["ficha"], "PC-02": d.EQUIPOS_REFERENCIA["PC-02"]["ficha"], "PC-03": d.EQUIPOS_REFERENCIA["PC-03"]["ficha"],
 "max": {"id":"X","cpu_modelo":"Prueba","ram_gb":8,"tipo_ram":"DDR4","ram_max_gb":8,"ranuras_libres":1,"disco":"HDD","interfaz":"SATA"},
 "ide": {"id":"X","cpu_modelo":"Prueba","ram_gb":4,"tipo_ram":"DDR3","ram_max_gb":8,"ranuras_libres":1,"disco":"HDD","interfaz":"IDE"},
 "m2ssd": {"id":"X","cpu_modelo":"Prueba","ram_gb":4,"tipo_ram":"DDR5","ram_max_gb":16,"ranuras_libres":0,"disco":"SSD","interfaz":"M.2"}}
cpus=[0,40,84.9,85,85.1,90,100]; mins=[0,5,9.9,10,15,300]; rams=[0,30,79.9,80,80.1,95,100]; libres=[0,10,14.9,15,15.1,40,100]
casos=[]
for fk,f in fichas.items():
  for cpu,mn,ram,libre in itertools.product(cpus,mins,rams,libres):
    for disco in ("HDD","SSD"):
      if f and f["disco"]!=disco: continue
      e={"cpu":float(cpu),"minutos":float(mn),"ram":float(ram),"disco":disco,"libre":float(libre)}
      est,h,o=d.evaluar(e["cpu"],e["minutos"],e["ram"],disco,e["libre"])
      recs=d.recomendar(e["cpu"],e["minutos"],e["ram"],disco,e["libre"],f)
      rep=d.generar_reporte("EQ",e,est,h,o,recs,f)
      rep=re.sub(r"Fecha: .*","Fecha: X",rep)
      casos.append({"f":fk,"e":e,"estado":est,"h":h,"o":o,"recs":recs,"tabla":[list(x) for x in d.tabla_mejoras(e["ram"],disco,e["libre"],f)],"rep":rep})
# validaciones
vals=[]
for t in ["abc","120","-5","50","50,5","nan","inf","-inf","","  ","1e2","101","0","100",".5","5.","+7"," 42 "]:
  for nom,fn in (("CPU",lambda x:d.validar_porcentaje(x,"CPU")),("MIN",d.validar_minutos)):
    try: r=("ok",fn(t))
    except ValueError as ex: r=("err",str(ex))
    vals.append({"t":t,"n":nom,"r":list(r)})
json.dump({"fichas":fichas,"casos":casos,"vals":vals},open(AQUI / "py.json","w"),ensure_ascii=False)
print(len(casos),"casos;",len(vals),"validaciones")
