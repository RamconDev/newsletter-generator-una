# Newsletter Generator UNA - Backend (Flask API)

API RESTful desarrollada en Python y Flask diseñada para procesar reportes académicos de la Universidad Nacional Abierta (UNA). Permite la carga estructurada de archivos planos (.REP, .TXT), los almacena en base de datos de forma relacional y expone la información académica de los estudiantes agrupada por períodos.

## Características y Avances Desarrollados

1. **Gestión de Carga de Archivos Segura**:
   - Validación robusta de tipo de archivo (mediante cabeceras y contenido), extensión (`.REP`, `.TXT`) y límites de tamaño definidos a través de variables de entorno (`.env` y `config.py`).
   - Lógica de procesamiento capaz de leer el reporte plano, parsearlo y extraer datos específicos de estudiantes, cursos y calificaciones.

2. **Soporte de Períodos Académicos**:
   - Refactorización de la base de datos y la lógica para que las calificaciones e información de los estudiantes se vinculen y agrupen correctamente según sus períodos académicos (lapsos), facilitando el consumo por parte del frontend.

3. **Módulo de Autenticación y Usuarios**:
   - Implementación de un modelo de usuarios (`User`) y roles (`Role`) utilizando SQLAlchemy.
   - Rutas dedicadas para la creación, consulta, modificación y eliminación de usuarios (CRUD completo).
   - Asignación dinámica de roles (ej. `Viewer`) para control de acceso.

4. **Arquitectura Escalable**:
   - Patrón de diseño de "Application Factory" con Blueprints (`auth_bp` y `reports_bp`) para separar responsabilidades.
   - Uso de `SQLAlchemy` para el ORM de la base de datos.

---

## Documentación de Endpoints

La API cuenta con dos dominios principales: la gestión de reportes/estudiantes y la gestión de usuarios/autenticación. Todas las rutas operan bajo el prefijo `/api/v1`.

### 📚 Módulo de Reportes y Estudiantes

#### 1. Cargar Nuevo Reporte
- **Endpoint**: `POST /api/v1/reports`
- **Descripción**: Permite subir un archivo de reporte al servidor. El servidor verifica que contenga la cabecera "UNIVERSIDAD NACIONAL ABIERTA", comprueba su extensión y tamaño máximo. Si es válido, lo procesa y guarda la información estructurada en la base de datos.
- **Body**: `multipart/form-data` con el campo `file` conteniendo el archivo.

#### 2. Listar Reportes Procesados
- **Endpoint**: `GET /api/v1/reports`
- **Descripción**: Devuelve la lista de archivos de reporte que han sido procesados y almacenados.

#### 3. Listar Períodos Académicos
- **Endpoint**: `GET /api/v1/academic-periods`
- **Descripción**: Obtiene una lista de todos los períodos académicos únicos registrados actualmente en la base de datos provenientes de los distintos reportes.

#### 4. Búsqueda de Estudiante por Cédula
- **Endpoint**: `GET /api/v1/students/<identificacion>`
- **Descripción**: Realiza una búsqueda exacta de un estudiante utilizando su documento de identidad (Cédula). Devuelve la información personal del estudiante junto con todas sus asignaturas, calificaciones y créditos, correctamente agrupados por sus respectivos períodos académicos.

---

### 🔐 Módulo de Usuarios y Autenticación

#### 5. Crear Usuario
- **Endpoint**: `POST /api/v1/auth/user`
- **Descripción**: Registra un nuevo usuario en el sistema. Automáticamente le asigna el rol base de `Viewer`.
- **Body (JSON)**: `firstname`, `lastname`, `username`, `email`, `phone`, `password`.

#### 6. Obtener Todos los Usuarios
- **Endpoint**: `GET /api/v1/auth/user`
- **Descripción**: Devuelve un listado con la información de todos los usuarios registrados, ordenados por los más recientes.

#### 7. Obtener Usuario por ID
- **Endpoint**: `GET /api/v1/auth/user/<user_id>`
- **Descripción**: Retorna la información detallada de un usuario específico mediante su ID.

#### 8. Actualizar Usuario
- **Endpoint**: `PUT /api/v1/auth/user/<user_id>`
- **Descripción**: Actualiza los datos de un usuario existente.

#### 9. Eliminar Usuario
- **Endpoint**: `DELETE /api/v1/auth/user/<user_id>`
- **Descripción**: Elimina del sistema a un usuario específico a través de su ID.

#### 10. Asignar Rol a un Usuario
- **Endpoint**: `POST /api/v1/auth/user/<user_id>/role`
- **Descripción**: Asigna un rol específico (previamente creado en la base de datos) a un usuario.
- **Body (JSON)**: `{"role": "NombreDelRol"}`

#### 11. Remover Rol de un Usuario
- **Endpoint**: `DELETE /api/v1/auth/user/<user_id>/role/<role_name>`
- **Descripción**: Elimina un rol específico del listado de roles asignados a un usuario particular.

---

## Requisitos y Configuración Local

- Python 3.10+
- Entorno Virtual (`venv`) recomendado.

### Instalación

1. Crear y activar el entorno virtual:
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\Activate.ps1
   # Linux/Mac
   source .venv/bin/activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar el servidor de pruebas:
   ```bash
   python run.py
   ```
El servidor se inicializará por defecto en `http://127.0.0.1:5000`.

## Variables de Entorno y Despliegue

La aplicación utiliza una sola variable de entorno para la conexión a la base de datos en producción: `DATABASE_URL`. Ejemplo de `DATABASE_URL`:

```
postgresql://USER:PASSWORD@HOST:5432/DBNAME
```

Recomendaciones rápidas:

- Para desarrollo local puedes copiar `.env.example` a `.env` y adaptar las credenciales.
- En producción, exporta `DATABASE_URL` en el entorno del proceso o configúralo en tu orquestador (systemd, Docker, Heroku, etc.).

Ejemplos de uso:

PowerShell (Windows):
```powershell
$env:DATABASE_URL = 'postgresql://user:password@db-host:5432/newsletter_db'
python run.py
```

Linux / macOS (bash):
```bash
export DATABASE_URL='postgresql://user:password@db-host:5432/newsletter_db'
python run.py
```

Ejemplo mínimo `docker-compose` (servicio app + postgres):
```yaml
version: '3.8'
services:
   db:
      image: postgres:15
      environment:
         POSTGRES_USER: user
         POSTGRES_PASSWORD: password
         POSTGRES_DB: newsletter_db
      volumes:
         - db-data:/var/lib/postgresql/data

   app:
      build: .
      environment:
         DATABASE_URL: postgres://user:password@db:5432/newsletter_db
      depends_on:
         - db

volumes:
   db-data:
```

Nota: Docker Compose ejemplo usa `postgres://` para compatibilidad con algunas herramientas; la aplicación normaliza `postgres://` a `postgresql://` automáticamente.

## Nueva estructura del proyecto (refactor)

Recientemente se refactorizó la aplicación hacia una estructura modular más clara. Cambios principales:

- `app/extensions.py`: centraliza las extensiones de Flask (`db`, `migrate`, `cors`, etc.).
- `app/reports/services.py`: contiene la lógica de procesamiento de archivos de reporte y funciones relacionadas (`process_and_save_report`, `get_reports_list`, `get_student_data_from_db`, `get_all_academic_periods`, ...).
- `app/utils.py`: ahora es una fachada de compatibilidad que re-exporta las funciones de reportes desde `app.reports.services` para mantener compatibilidad con importaciones existentes.
- Blueprints: las rutas HTTP permanecen en `app/reports/routes.py` y `app/auth/routes.py`; la lógica de negocio se traslada a `services` dentro de cada módulo.

Objetivos de la refactorización:

- Separar responsabilidades: rutas (HTTP) → servicios (lógica) → modelos/repositorios (DB).
- Facilitar pruebas unitarias y reutilización del código.
- Reducir acoplamiento entre módulos y centralizar configuración/extensiones.

Notas de migración y pruebas rápidas

1. Para ejecutar localmente (desde la raíz del proyecto):

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
python run.py
```

2. Verifica la ruta base (index) y listado de reportes:

- `GET /` — devuelve mensaje de inicio y lista de archivos encontrados en `data/`.
- `GET /api/v1/reports` — lista de archivos `.REP` disponibles.

3. Probar subida de archivo (ejemplo con `curl`):

```bash
curl -F "file=@data/LISEVAL3.REP" http://127.0.0.1:5000/api/v1/reports
```

4. Comentarios para desarrolladores

- Si exportas funciones desde `app.utils`, ya funcionan porque `app.utils` re-exporta desde `app.reports.services`.
- Para mover más lógica a servicios, crea `app/<module>/services.py` y deja las rutas ligeras.

Si quieres, puedo:

- ejecutar el servidor localmente y realizar una subida de prueba con `data/LISEVAL3.REP` para validar el flujo end-to-end, o
- preparar una PR con estos cambios y un conjunto mínimo de pruebas unitarias para `app.reports.services`.

