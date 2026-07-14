# Referencia de la API

**Base URL**: `http://127.0.0.1:5000`
**Prefijo**: todas las rutas cuelgan de `/api/v1`.
**Content-Type**: `application/json` (excepto la subida de archivos, que usa `multipart/form-data`).
**Autenticación**: el login devuelve un JWT. Los endpoints protegidos esperan la cabecera `Authorization: Bearer <token>`.

## Formato de respuesta

Todas las respuestas (éxito y error) tienen la misma envoltura:

```json
{ "status": "success | error", "message": "…", "data": { } }
```

- En las respuestas exitosas, **el contenido útil siempre va dentro de `data`** (nunca en la raíz).
- En los errores, `data` es un objeto vacío `{}` y solo importa `message`. No se emiten códigos ni nombres de campo.
- Los errores HTTP genéricos (401, 403, 404, 405, 413, 422, 500) están centralizados y devuelven la misma envoltura.

## Roles

Existen tres roles: `Admin`, `Editor`, `Viewer`. **Cada usuario tiene un único rol** (no una lista). Al crear un usuario sin `role` válido se asigna `Viewer` por defecto.

---

## Índice

### Auth
- [POST `/auth/login` — Iniciar sesión](#post-authlogin--iniciar-sesión)
- [POST `/auth/refresh-token` — Renovar token](#post-authrefresh-token--renovar-token)
- [POST `/auth/logout` — Cerrar sesión](#post-authlogout--cerrar-sesión)
- [POST `/auth/user` — Crear usuario](#post-authuser--crear-usuario)
- [GET `/auth/user` — Listar usuarios](#get-authuser--listar-usuarios)
- [GET `/auth/user/:id` — Obtener usuario por ID](#get-authuserid--obtener-usuario-por-id)
- [PUT `/auth/user/:id` — Actualizar usuario](#put-authuserid--actualizar-usuario)
- [DELETE `/auth/user/:id` — Eliminar usuario](#delete-authuserid--eliminar-usuario)
- [GET `/auth/roles` — Listar roles](#get-authroles--listar-roles)
- [POST `/auth/user/:id/role` — Asignar rol](#post-authuseridrole--asignar-rol)
- [DELETE `/auth/user/:id/role/:role_name` — Quitar rol](#delete-authuseridrolerole_name--quitar-rol)

### Reports
- [POST `/reports` — Subir reporte](#post-reports--subir-reporte)
- [GET `/reports` — Auditoría de períodos](#get-reports--auditoría-de-períodos)
- [GET `/academic-periods` — Listar períodos](#get-academic-periods--listar-períodos)
- [GET `/academic-periods/:period_code/students` — Estudiantes por período](#get-academic-periodsperiod_codestudents--estudiantes-por-período)
- [DELETE `/academic-periods/:period_code` — Eliminar período](#delete-academic-periodsperiod_code--eliminar-período)
- [GET `/students/:identification` — Buscar estudiante](#get-studentsidentification--buscar-estudiante)
- [GET `/reports/audit/users` — Auditoría de usuarios](#get-reportsauditusers--auditoría-de-usuarios)

### Careers (Carreras)
- [GET `/careers` — Listar carreras](#get-careers--listar-carreras)
- [GET `/careers/:major_id` — Obtener carrera](#get-careersmajor_id--obtener-carrera)
- [POST `/careers` — Crear/actualizar carreras (lote)](#post-careers--crearactualizar-carreras-lote)
- [PUT `/careers/:major_id` — Actualizar carrera](#put-careersmajor_id--actualizar-carrera)
- [DELETE `/careers/:major_id` — Eliminar carrera](#delete-careersmajor_id--eliminar-carrera)

### Exports
- [GET/POST `/exports/pdf/:identification/:period_id` — Ficha académica PDF](#getpost-exportspdfidentificationperiod_id--ficha-académica-pdf)

---

## Auth

### POST `/auth/login` — Iniciar sesión

Público. Valida `username` + `password` y devuelve un JWT de acceso y uno de refresco. El token de acceso expira según `JWT_EXP_HOURS` (por defecto 1 hora).

**Body**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `username` | string | sí |
| `password` | string | sí |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "ozambrano", "password": "Secret123"}'
```

**`200`**
```json
{
  "status": "success",
  "message": "Login exitoso.",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

El payload del token de acceso contiene: `sub` (id), `email`, `firstname`, `lastname`, `role` (nombre del rol, string), `type`, `jti`, `exp`.

**`400`** — faltan campos · **`401`** — credenciales inválidas.

**Variables de entorno**

| Variable | Default | Propósito |
|----------|---------|-----------|
| `JWT_SECRET_KEY` | `jwt_secret_key` | Secreto de firma |
| `JWT_EXP_HOURS` | `1` | Vida del token de acceso (horas) |
| `JWT_REFRESH_EXP_HOURS` | `JWT_EXP_HOURS * 2` | Vida del token de refresco |

---

### POST `/auth/refresh-token` — Renovar token

Público. Recibe un token de refresco válido y devuelve un nuevo par de tokens.

**Body**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `refresh_token` | string | sí |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGci..."}'
```

**`200`**
```json
{
  "status": "success",
  "message": "Token renovado exitosamente.",
  "data": { "token": "eyJ...", "refresh_token": "eyJ..." }
}
```

**`400`** — falta `refresh_token` · **`401`** — token inválido, expirado, de tipo incorrecto, ya usado (rotación: cada refresh revoca el token usado) o usuario inexistente/inactivo.

---

### POST `/auth/logout` — Cerrar sesión

Requiere autenticación. Revoca el `jti` del token actual para que no pueda reutilizarse.

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/logout \
  -H "Authorization: Bearer <token>"
```

**`200`**
```json
{ "status": "success", "message": "Sesión cerrada correctamente.", "data": {} }
```

---

### POST `/auth/user` — Crear usuario

**Rol**: `Admin`. Si `role` se omite, viene vacío o `null`, se asigna `Viewer`.

**Body**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `firstname` | string | sí |
| `lastname` | string | sí |
| `username` | string | sí (único) |
| `email` | string | sí (único, formato válido) |
| `password` | string | sí (mín. 8 caracteres, 1 mayúscula, 1 dígito) |
| `phone` | string | no |
| `role` | string | no (default `Viewer`; debe existir) |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/user \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "firstname": "Oscar", "lastname": "Zambrano",
    "username": "ozambrano", "email": "oscar@example.com",
    "password": "Secret123", "phone": "04121234567", "role": "Editor"
  }'
```

**`201`**
```json
{
  "status": "success",
  "message": "Usuario registrado correctamente.",
  "data": {
    "id": 1, "firstname": "Oscar", "lastname": "Zambrano",
    "username": "ozambrano", "email": "oscar@example.com",
    "phone": "04121234567", "is_active": true, "roles": "Editor"
  }
}
```

**`400`** — cuerpo/campo requerido, email inválido o contraseña débil · **`404`** — el rol no existe · **`409`** — username o email ya existe.

---

### GET `/auth/user` — Listar usuarios

**Rol**: `Admin`. Devuelve todos los usuarios ordenados por ID descendente.

```bash
curl http://127.0.0.1:5000/api/v1/auth/user -H "Authorization: Bearer <admin_token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Usuarios obtenidos correctamente.",
  "data": [
    {
      "id": 2, "firstname": "Ana", "lastname": "López",
      "username": "alopez", "email": "ana@example.com",
      "phone": null, "is_active": true, "roles": "Admin"
    }
  ]
}
```

**`404`** — no hay usuarios registrados.

---

### GET `/auth/user/:id` — Obtener usuario por ID

Requiere autenticación. Permitido a `Admin` o al **propio usuario**; en otro caso `403`.

```bash
curl http://127.0.0.1:5000/api/v1/auth/user/1 -H "Authorization: Bearer <token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Usuario obtenido correctamente.",
  "data": {
    "id": 1, "firstname": "Oscar", "lastname": "Zambrano",
    "username": "ozambrano", "email": "oscar@example.com",
    "phone": "04121234567", "is_active": true, "roles": "Viewer"
  }
}
```

**`403`** — solo puedes consultar tu propio perfil · **`404`** — el usuario no existe.

---

### PUT `/auth/user/:id` — Actualizar usuario

Requiere autenticación. Permitido a `Admin` o al **propio usuario**. Campos actualizables: `firstname`, `lastname`, `email`, `phone`, `password`. Cada cambio queda registrado en la auditoría de usuarios (ver `/reports/audit/users`); la contraseña se registra solo como "Modificó la contraseña" (nunca su valor).

**Body** (todos opcionales; se aplican los presentes y no nulos)

| Campo | Tipo | Validación |
|-------|------|-----------|
| `firstname` | string | — |
| `lastname` | string | — |
| `email` | string | formato válido |
| `phone` | string | — |
| `password` | string | mín. 8 caracteres, 1 mayúscula, 1 dígito |

```bash
curl -X PUT http://127.0.0.1:5000/api/v1/auth/user/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{ "firstname": "Oscar Gabriel", "email": "oscar.g@example.com" }'
```

**`200`**
```json
{
  "status": "success",
  "message": "Usuario actualizado correctamente.",
  "data": {
    "id": 1, "firstname": "Oscar Gabriel", "lastname": "Zambrano",
    "username": "ozambrano", "email": "oscar.g@example.com",
    "phone": "04121234567", "is_active": true, "roles": "Viewer"
  }
}
```

**`400`** — cuerpo requerido, email inválido o contraseña débil · **`403`** — solo tu propio perfil · **`404`** — usuario no existe · **`409`** — error de base de datos (p. ej. email duplicado).

---

### DELETE `/auth/user/:id` — Eliminar usuario

**Rol**: `Admin`. Registra la eliminación en la auditoría de usuarios.

```bash
curl -X DELETE http://127.0.0.1:5000/api/v1/auth/user/1 -H "Authorization: Bearer <admin_token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Usuario eliminado correctamente.",
  "data": { "id": 1, "username": "ozambrano" }
}
```

**`404`** — usuario no existe · **`500`** — error de base de datos.

---

### GET `/auth/roles` — Listar roles

**Rol**: `Admin`. Devuelve los roles del sistema ordenados por ID.

```bash
curl http://127.0.0.1:5000/api/v1/auth/roles -H "Authorization: Bearer <admin_token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Roles obtenidos correctamente.",
  "data": [
    { "id": 1, "name": "Admin", "description": "Acceso total: gestión de usuarios, roles y reportes." },
    { "id": 2, "name": "Editor", "description": "Puede cargar y gestionar reportes académicos." },
    { "id": 3, "name": "Viewer", "description": "Solo lectura: consulta de estudiantes y períodos." }
  ]
}
```

---

### POST `/auth/user/:id/role` — Asignar rol

**Rol**: `Admin`. Reemplaza el rol del usuario. No se puede degradar al último `Admin` del sistema. Registra el cambio en la auditoría de usuarios.

**Body**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `role` | string | sí |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/user/1/role \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{ "role": "Editor" }'
```

**`201`**
```json
{
  "status": "success",
  "message": "Rol asignado correctamente.",
  "data": {
    "id": 1, "firstname": "Oscar", "lastname": "Zambrano",
    "username": "ozambrano", "email": "oscar@example.com",
    "phone": null, "is_active": true, "roles": "Editor"
  }
}
```

**`400`** — falta `role` o es inválido · **`404`** — usuario o rol no existe · **`409`** — no se puede degradar al último administrador · **`500`** — error de base de datos.

---

### DELETE `/auth/user/:id/role/:role_name` — Quitar rol

**Rol**: `Admin`. Quita el rol indicado (deja al usuario sin rol). No se puede remover el rol al último `Admin`. Registra el cambio en la auditoría de usuarios.

```bash
curl -X DELETE http://127.0.0.1:5000/api/v1/auth/user/1/role/Editor \
  -H "Authorization: Bearer <admin_token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Rol eliminado correctamente.",
  "data": {
    "id": 1, "firstname": "Oscar", "lastname": "Zambrano",
    "username": "ozambrano", "email": "oscar@example.com",
    "phone": null, "is_active": true, "roles": null
  }
}
```

**`404`** — usuario no existe, rol no existe o el usuario no tiene ese rol · **`409`** — no se puede remover el último administrador · **`500`** — error de base de datos.

---

## Reports

### POST `/reports` — Subir reporte

**Roles**: `Admin`, `Editor`. Sube, valida y procesa un archivo `.REP`. El archivo debe:
- Tener extensión `.rep`.
- Pesar menos de 5 MB.
- Contener `"UNIVERSIDAD NACIONAL ABIERTA"` en los primeros 256 bytes (texto plano, codificación `latin-1`).

Al crear un período nuevo se registran el usuario que subió el archivo, la marca de tiempo y el nombre de archivo de origen. `carreras_sin_nombre` lista los códigos de carrera detectados que aún no tienen nombre registrado. `lineas_descartadas` cuenta las líneas con cédula que no pudieron parsearse (malformadas o incoherentes con el layout). El archivo se elimina del disco tras procesarse (éxito o fallo); sus datos quedan en la base de datos.

**Request**: `multipart/form-data`

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `file` | file (`.rep`) | sí |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/reports \
  -H "Authorization: Bearer <token>" \
  -F "file=@/ruta/al/reporte.rep"
```

**`201`**
```json
{
  "status": "success",
  "message": "Archivo cargado, validado y guardado correctamente.",
  "data": { "filename": "reporte.rep", "carreras_sin_nombre": ["610", "810"], "lineas_descartadas": 0 }
}
```

**`400`** — no se envió archivo, archivo no seleccionado, formato no permitido, archivo muy grande, archivo inválido o corrupto · **`422`** — reporte vacío o ilegible · **`500`** — error al guardar o al procesar.

---

### GET `/reports` — Auditoría de períodos

**Roles**: `Admin`, `Editor`. Devuelve el historial de auditoría de períodos académicos (altas/bajas de períodos), no la lista de períodos. El campo `id` se excluye de cada registro. Paginado con `init` (offset, default `0`) y `limit` (default `20`, máximo `100`); la respuesta incluye `total`.

```bash
curl "http://127.0.0.1:5000/api/v1/reports?init=0&limit=20" -H "Authorization: Bearer <token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Historial de auditoría.",
  "data": {
    "audit_records": [
      {
        "period_code": "2023-1",
        "operation": "CREACIÓN",
        "sede_id": 1,
        "user_email": "editor@example.com",
        "user_fullname": "Editor Ejemplo",
        "operation_at": "2026-05-05T14:30:00",
        "source_file": "reporte_2023-1.rep",
        "ip_address": "127.0.0.1",
        "affected_rows": null
      }
    ],
    "total": 1,
    "init": 0,
    "limit": 20
  }
}
```

---

### GET `/academic-periods` — Listar períodos

**Roles**: `Admin`, `Editor`, `Viewer`. Devuelve todos los períodos académicos (solo `id` y `code`).

```bash
curl http://127.0.0.1:5000/api/v1/academic-periods -H "Authorization: Bearer <token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Períodos académicos.",
  "data": {
    "academic_periods": [
      { "id": 1, "code": "2023-1" },
      { "id": 2, "code": "2023-2" }
    ]
  }
}
```

**`500`** — error inesperado.

---

### GET `/academic-periods/:period_code/students` — Estudiantes por período

**Roles**: `Admin`, `Editor`, `Viewer`. Lista paginada, filtrable y ordenable de estudiantes con al menos una nota en el período.

**Path**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `period_code` | string | Código del período (p. ej. `2023-1`) |

**Query**

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `init` | int | `0` | Offset (registros a saltar, ≥ 0) |
| `limit` | int | `20` | Tamaño de página (1–100) |
| `order` | string | `nombre` | Orden: `cedula`, `nombre`, `carrera` |
| `asc` | bool | `true` | `true` = ASC, `false` = DESC |
| `carrera` | string | — | Filtro exacto por código de carrera |
| `nombre` | string | — | Filtro parcial (case-insensitive) por nombre |

```bash
curl "http://127.0.0.1:5000/api/v1/academic-periods/2023-1/students?init=0&limit=20&order=cedula&asc=false" \
  -H "Authorization: Bearer <token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Listado de estudiantes.",
  "data": {
    "students": [
      { "cedula": "V-12345678", "nombre": "Juan García", "carrera": "610" }
    ],
    "total": 85, "init": 0, "limit": 20
  }
}
```

`total` es el conteo completo tras aplicar filtros. Nº de páginas = `ceil(total / limit)`.

**`400`** — parámetro de query inválido · **`404`** — período no encontrado.

---

### DELETE `/academic-periods/:period_code` — Eliminar período

**Rol**: `Admin`. Elimina el período en cascada: (1) sus notas, (2) los estudiantes que queden sin notas en ningún período, (3) el período. Operación irreversible; estudiantes y asignaturas compartidos con otros períodos no se ven afectados.

```bash
curl -X DELETE http://127.0.0.1:5000/api/v1/academic-periods/2023-1 \
  -H "Authorization: Bearer <admin_token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Período '2023-1' eliminado correctamente.",
  "data": { "period_code": "2023-1", "grades_deleted": 142, "students_deleted": 38 }
}
```

**`404`** — período no encontrado · **`500`** — error inesperado.

---

### GET `/students/:identification` — Buscar estudiante

**Roles**: `Admin`, `Editor`, `Viewer`. Busca un estudiante por cédula. Opcionalmente filtra por período con `?period` (a nivel de base de datos).

**Query**

| Param | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `period` | string | no | Código de período; si se omite, devuelve todos |

```bash
curl "http://127.0.0.1:5000/api/v1/students/V-12345678?period=2023-1" \
  -H "Authorization: Bearer <token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Estudiante encontrado.",
  "data": {
    "cedula": "V-12345678",
    "nombre": "Juan Pérez",
    "carrera": "610",
    "periodos": [
      {
        "id": 1, "codigo": "2023-1",
        "materias": [
          { "codigo_asignatura": "010", "asignatura": "Curso Introductorio", "condicion": "RG", "nota_final": "6/6" }
        ]
      }
    ]
  }
}
```

Si se envía `?period` y el estudiante no tiene notas en él, `periodos` es `[]`.

**`404`** — estudiante no encontrado.

---

### GET `/reports/audit/users` — Auditoría de usuarios

**Rol**: `Admin`. Historial de operaciones sobre usuarios (creación, actualización, eliminación, cambios de rol), ordenado por fecha descendente. Paginado con `init` (offset, default `0`) y `limit` (default `20`, máximo `100`); la respuesta incluye `total`.

Cada registro:

| Campo | Descripción |
|-------|-------------|
| `ip_address` | IP desde donde se realizó la operación |
| `operation` | `CREACIÓN`, `ACTUALIZACIÓN` o `ELIMINACIÓN` |
| `operation_at` | Fecha/hora ISO-8601 (UTC) |
| `user_email` | Correo de **quien realizó** la modificación (actor) |
| `user_modify` | Correo del **usuario modificado** (afectado) |
| `descripcion` | Lista de textos que describen lo ocurrido |

```bash
curl http://127.0.0.1:5000/api/v1/reports/audit/users -H "Authorization: Bearer <admin_token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Historial de auditoría de usuarios.",
  "data": {
    "audit_records": [
      {
        "ip_address": "127.0.0.1",
        "operation": "ACTUALIZACIÓN",
        "operation_at": "2026-06-28T03:45:37.798354",
        "user_email": "admin@example.com",
        "user_modify": "prueba@example.com",
        "descripcion": [
          "Modificó nombre: antes='Juan' después='Juancho'",
          "Modificó correo: antes='a@x.com' después='b@x.com'",
          "Modificó la contraseña"
        ]
      },
      {
        "ip_address": "127.0.0.1",
        "operation": "CREACIÓN",
        "operation_at": "2026-06-28T03:40:00.000000",
        "user_email": "admin@example.com",
        "user_modify": "prueba@example.com",
        "descripcion": ["Creación de usuario Juan Perez (prueba@example.com)"]
      }
    ],
    "total": 2,
    "init": 0,
    "limit": 20
  }
}
```

---

## Careers (Carreras)

### GET `/careers` — Listar carreras

**Roles**: `Admin`, `Editor`, `Viewer`.

```bash
curl http://127.0.0.1:5000/api/v1/careers -H "Authorization: Bearer <token>"
```

**`200`**
```json
{
  "status": "success",
  "message": "Carreras.",
  "data": { "careers": [ { "id": 1, "code": "610", "name": "Matemática" } ] }
}
```

---

### GET `/careers/:major_id` — Obtener carrera

**Roles**: `Admin`, `Editor`, `Viewer`.

```bash
curl http://127.0.0.1:5000/api/v1/careers/1 -H "Authorization: Bearer <token>"
```

**`200`**
```json
{ "status": "success", "message": "Carrera encontrada.", "data": { "id": 1, "code": "610", "name": "Matemática" } }
```

**`404`** — carrera no encontrada.

---

### POST `/careers` — Crear/actualizar carreras (lote)

**Roles**: `Admin`, `Editor`. El cuerpo es un **arreglo** de carreras. Hace *upsert* por `code`: si el código existe, actualiza su `name`; si es nuevo, lo crea. Los ítems sin `code` se reportan como fallidos.

**Body**: arreglo de objetos `{ "code": string, "name": string }`.

```bash
curl -X POST http://127.0.0.1:5000/api/v1/careers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '[ { "code": "610", "name": "Matemática" }, { "code": "810", "name": "Educación" } ]'
```

**`201`** — todas guardadas
```json
{
  "status": "success",
  "message": "Carreras guardadas correctamente.",
  "data": { "procesadas": [ { "id": 1, "code": "610", "name": "Matemática" } ] }
}
```

**`207`** — guardado parcial (algunos códigos no se guardaron); `status` es `error`
```json
{
  "status": "error",
  "message": "Códigos no guardados: (vacío).",
  "data": { "procesadas": [ { "id": 1, "code": "610", "name": "Matemática" } ], "fallidas": ["(vacío)"] }
}
```

**`400`** — el cuerpo no es un arreglo o está vacío · **`500`** — error de base de datos.

---

### PUT `/careers/:major_id` — Actualizar carrera

**Roles**: `Admin`, `Editor`. Actualiza `code` y/o `name` de una carrera existente.

**Body**

| Campo | Tipo | Notas |
|-------|------|-------|
| `code` | string | opcional; no puede quedar vacío si se envía |
| `name` | string | opcional; vacío se guarda como `null` |

```bash
curl -X PUT http://127.0.0.1:5000/api/v1/careers/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{ "name": "Matemáticas Puras" }'
```

**`200`**
```json
{ "status": "success", "message": "Carrera actualizada correctamente.", "data": { "id": 1, "code": "610", "name": "Matemáticas Puras" } }
```

**`400`** — cuerpo requerido o `code` vacío · **`404`** — carrera no encontrada · **`409`** — código duplicado · **`500`** — error de base de datos.

---

### DELETE `/careers/:major_id` — Eliminar carrera

**Rol**: `Admin`. No se puede eliminar una carrera con estudiantes asociados.

```bash
curl -X DELETE http://127.0.0.1:5000/api/v1/careers/1 -H "Authorization: Bearer <admin_token>"
```

**`200`**
```json
{ "status": "success", "message": "Carrera eliminada correctamente.", "data": { "id": 1 } }
```

**`404`** — carrera no encontrada · **`409`** — la carrera tiene estudiantes asociados · **`500`** — error de base de datos.

---

## Exports

### GET/POST `/exports/pdf/:identification/:period_id` — Ficha académica PDF

Genera y devuelve la ficha académica del estudiante para un período en formato **PDF** (`Content-Type: application/pdf`, `inline`). No devuelve JSON en el caso exitoso y no exige rol.

**Path**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `identification` | string | Cédula del estudiante |
| `period_id` | int | ID del período académico a incluir |

```bash
curl "http://127.0.0.1:5000/api/v1/exports/pdf/V-12345678/1" -o ficha.pdf
```

**`200`** — cuerpo binario PDF (`filename=ficha_<identification>_<period_id>.pdf`).

**`404`** — estudiante no encontrado (respuesta JSON de error) · **`500`** — no se pudo generar el PDF o error interno.
