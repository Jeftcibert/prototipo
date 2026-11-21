# Caso 13 · Prototipo de diagnóstico de vida útil de PC (Grupo 13)

Datos ingresados o simulados; no mide el hardware.

## Contenido
- `index.html` — prototipo web interactivo (un solo archivo, sin dependencias).
- `diagnostico_pc.py` — programa de consola (F01–F05). `python diagnostico_pc.py`
- `pruebas.py` — casos T01–T17 + 7 verificaciones de integración (T1). `python pruebas.py`
- `pruebas_t2.py` — casos CP-01 a CP-10 (T2). `python pruebas_t2.py`
- `verificacion/` — compara la lógica de la web con la de Python (16 464 combinaciones):
  `python verificacion/gen_py.py` y luego `node verificacion/comparar_web_python.js` (requiere Node.js).

## Publicar el enlace (GitHub Pages)
1. Crear un repositorio público en GitHub y subir todos estos archivos.
2. Settings → Pages → Source: «Deploy from a branch», rama `main`, carpeta `/ (root)` → Save.
3. Esperar 1–2 minutos. El enlace será `https://<usuario>.github.io/<repositorio>/`.
4. Abrirlo en una ventana de incógnito para comprobar que es público y funciona; pegar ese enlace y el del repositorio en la Tabla 17 del informe.

## Repetir las capturas con sus propios equipos
- Web: abrir el enlace, pulsar cada escenario y capturar la pantalla (Figuras 9 a 14).
- Consola: ejecutar `python pruebas_t2.py` y `python pruebas.py` y capturar la salida (Figuras 15 y 16).
