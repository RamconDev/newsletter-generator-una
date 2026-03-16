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

## Endpoints principales

### GET /api/reports

Lista los archivos disponibles en `data/`.

Ejemplo:

```bash
curl http://127.0.0.1:5000/api/reports
```

### GET /api/reports/{file_name}

Busca un estudiante en un archivo de reporte.

Nota: en la implementacion actual este endpoint espera JSON en el body con `identification`.

Ejemplo:

```bash
curl -X GET "http://127.0.0.1:5000/api/reports/LISEVAL3.REP" \
  -H "Content-Type: application/json" \
  -d '{"identification":"V-13149341"}'
```

Respuesta esperada (referencial):

```json
{
  "result": {
    "cedula": "V-13149341",
    "nombre": "NOMBRE APELLIDO",
    "carrera": "XX",
    "materias": [
      {
        "asignatura": "MATERIA",
        "nota_final": "15"
      }
    ]
  }
}
```

## Notas para demo

- El parser depende del formato actual de los archivos REP/TXT.
- Se recomienda usar archivos de prueba en `data/` para la validacion funcional.
- Esta version prioriza velocidad de demostracion sobre endurecimiento productivo.
