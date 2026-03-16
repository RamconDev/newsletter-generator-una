# Newsletter Generator UNA (Demo)

Aplicacion demo en Python + Flask para leer reportes academicos en archivos planos y exponer resultados en formato JSON via API.

## Objetivo

Este proyecto permite:

- Listar archivos de reportes disponibles en la carpeta `data/`.
- Consultar la informacion de un estudiante dentro de un reporte por cedula.

## Stack

- Python 3.10+
- Flask 3.x
- Werkzeug / Jinja2 (dependencias de Flask)

## Estructura basica

```text
.
|-- run.py                  # Punto de entrada
|-- requirements.txt        # Dependencias
|-- app/
|   |-- __init__.py         # App factory Flask
|   |-- blueprints.py       # Registro de blueprints
|   |-- utils.py            # Lectura de archivos y parsing
|   |-- reports/
|   |   |-- __init__.py     # Blueprint de reportes
|   |   |-- routes.py       # Endpoints REST
|   |-- templates/
|       |-- index.html
|-- data/                   # Archivos REP/TXT de entrada
```

## Requisitos previos

- Python instalado y disponible en PATH.
- PowerShell (Windows) o terminal equivalente.

## Ejecucion local

### 1) Crear y activar entorno virtual

En PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si tu comando principal es `py`, usa:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3) Ejecutar la aplicacion

```powershell
python run.py
```

La API inicia en:

- `http://127.0.0.1:5000`

## Endpoints API

Base URL:

- `http://127.0.0.1:5000`

### 1) GET /api/reports

Lista los archivos disponibles en `data/`.

```bash
curl "http://127.0.0.1:5000/api/reports"
```

### 2) GET /api/reports/{file_name}

Busca estudiante por cedula dentro del archivo.

Parametros:

- `identification` (requerido): cedula a buscar.
- `mode` (opcional): `exact` (default) o `prefix`.

Ejemplo exacto (recomendado):

```bash
curl "http://127.0.0.1:5000/api/reports/LISEVAL3.REP?identification=V-31859916"
```

Ejemplo prefix (devuelve multiples coincidencias):

```bash
curl "http://127.0.0.1:5000/api/reports/LISEVAL3.REP?identification=V-31859&mode=prefix"
```

Errores comunes:

```bash
# identification faltante -> 400
curl "http://127.0.0.1:5000/api/reports/LISEVAL3.REP"

# mode invalido -> 400
curl "http://127.0.0.1:5000/api/reports/LISEVAL3.REP?identification=V-31859&mode=foo"
```

### 3) POST /api/reports/{file_name}

Misma logica que el GET anterior, pero enviando los datos en JSON body.

Ejemplo exacto (body JSON):

```bash
curl -X POST "http://127.0.0.1:5000/api/reports/LISEVAL3.REP" \
  -H "Content-Type: application/json" \
  -d '{"identification":"V-31859916"}'
```

Ejemplo prefix (body JSON):

```bash
curl -X POST "http://127.0.0.1:5000/api/reports/LISEVAL3.REP" \
  -H "Content-Type: application/json" \
  -d '{"identification":"V-31859","mode":"prefix"}'
```

### 4) POST /api/reports

Endpoint placeholder de demo (pendiente por implementar).

```bash
curl -X POST "http://127.0.0.1:5000/api/reports"
```

### 5) PUT /api/reports/{file_name}

Endpoint no implementado en esta demo (retorna `501`).

```bash
curl -X PUT "http://127.0.0.1:5000/api/reports/LISEVAL3.REP"
```

### 6) DELETE /api/reports/{file_name}

Endpoint placeholder de demo.

```bash
curl -X DELETE "http://127.0.0.1:5000/api/reports/LISEVAL3.REP"
```

## Notas para demo

- El parser depende del formato actual de los archivos REP/TXT.
- Se recomienda usar archivos de prueba en `data/` para la validacion funcional.
- Para consultas productivas de demo, usar `mode=exact`; `mode=prefix` sirve para exploracion.
- Esta version prioriza velocidad de demostracion sobre endurecimiento productivo.
