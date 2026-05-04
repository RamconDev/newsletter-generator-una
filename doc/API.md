# API Reference

**Base URL**: `http://127.0.0.1:5000`  
**Content-Type**: `application/json` (except file uploads)  
**Auth**: No token layer yet — all endpoints are open.

---

## Roles

The system has three built-in roles: `Admin`, `Editor`, `Viewer`.  
New users are automatically assigned the `Viewer` role on creation.

---

## Auth Endpoints

### POST `/api/v1/auth/user` — Create user

Creates a new user and auto-assigns the `Viewer` role.

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `firstname` | string | yes |
| `lastname` | string | yes |
| `username` | string | yes (unique) |
| `email` | string | yes (unique) |
| `password` | string | yes |
| `phone` | string | no |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/user \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "Oscar",
    "lastname": "Zambrano",
    "username": "ozambrano",
    "email": "oscar@example.com",
    "password": "secret123",
    "phone": "04121234567"
  }'
```

**Response `200`**
```json
{
  "message": "registered successfully",
  "data": {
    "id": 1,
    "firstname": "Oscar",
    "lastname": "Zambrano",
    "username": "ozambrano",
    "email": "oscar@example.com",
    "phone": "04121234567",
    "is_active": true,
    "roles": ["Viewer"]
  }
}
```

**Response `400`** — missing body or DB/validation error
```json
{ "error": "not data recived" }
```

---

### GET `/api/v1/auth/user` — List all users

Returns all users ordered by ID descending.

```bash
curl http://127.0.0.1:5000/api/v1/auth/user
```

**Response `200`**
```json
{
  "status": "success",
  "message": "Usuarios obtenidos correctamente.",
  "data": [
    {
      "id": 2,
      "firstname": "Ana",
      "lastname": "López",
      "username": "alopez",
      "email": "ana@example.com",
      "phone": null,
      "is_active": true,
      "roles": ["Admin"]
    }
  ]
}
```

**Response `404`** — no users in DB
```json
{ "status": "error", "message": "No se encontraron usuarios registrados." }
```

---

### GET `/api/v1/auth/user/:id` — Get user by ID

```bash
curl http://127.0.0.1:5000/api/v1/auth/user/1
```

**Response `200`**
```json
{
  "status": "success",
  "message": "Usuario obtenido correctamente.",
  "data": {
    "id": 1,
    "firstname": "Oscar",
    "lastname": "Zambrano",
    "username": "ozambrano",
    "email": "oscar@example.com",
    "phone": "04121234567",
    "is_active": true,
    "roles": ["Viewer"]
  }
}
```

**Response `404`**
```json
{ "status": "error", "message": "usuario id 1 no existe." }
```

---

### PUT `/api/v1/auth/user/:id` — Update user

> **Not implemented yet.** The route exists but the body is empty (`pass`). Returns no response.

```bash
curl -X PUT http://127.0.0.1:5000/api/v1/auth/user/1 \
  -H "Content-Type: application/json" \
  -d '{ "firstname": "Oscar Gabriel" }'
```

---

### DELETE `/api/v1/auth/user/:id` — Delete user

```bash
curl -X DELETE http://127.0.0.1:5000/api/v1/auth/user/1
```

**Response `200`**
```json
{
  "status": "success",
  "message": "Usuario eliminado correctamente.",
  "data": { "id": 1, "username": "ozambrano" }
}
```

**Response `404`**
```json
{ "status": "error", "message": "usuario id 1 no existe." }
```

---

### POST `/api/v1/auth/user/:id/role` — Assign role

Adds a role to the user. Roles available: `Admin`, `Editor`, `Viewer`.

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `role` | string | yes |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/user/1/role \
  -H "Content-Type: application/json" \
  -d '{ "role": "Admin" }'
```

**Response `200` — role assigned**
```json
{
  "status": "success",
  "message": "Rol asignado correctamente.",
  "data": {
    "id": 1,
    "username": "ozambrano",
    "roles": ["Viewer", "Admin"]
  }
}
```

**Response `200` — already has the role**
```json
{ "status": "error", "message": "El usuario ya tiene el rol 'Admin'." }
```

**Response `400`** — missing `role` field
```json
{ "status": "error", "message": "El rol es requerido." }
```

**Response `404`** — user or role not found
```json
{ "status": "error", "message": "Rol 'SuperAdmin' no existe." }
```

---

### DELETE `/api/v1/auth/user/:id/role/:role_name` — Remove role

```bash
curl -X DELETE http://127.0.0.1:5000/api/v1/auth/user/1/role/Admin
```

**Response `200` — role removed**
```json
{
  "status": "success",
  "message": "Rol eliminado correctamente.",
  "data": {
    "id": 1,
    "username": "ozambrano",
    "roles": ["Viewer"]
  }
}
```

**Response `200` — user did not have the role**
```json
{ "status": "error", "message": "El usuario no tiene el rol 'Admin'." }
```

**Response `404`** — user or role not found
```json
{ "status": "error", "message": "usuario id 99 no existe." }
```

---

## Reports Endpoints

### POST `/api/v1/reports` — Upload report file

Uploads, validates, and processes a `.REP` academic report file. The file must:
- Have `.rep` extension
- Be under 5 MB
- Contain `"UNIVERSIDAD NACIONAL ABIERTA"` in the first 256 bytes (plain text, `latin-1` encoded)

The server extracts student, subject, grade, major, and academic period data and persists them to the database.

**Request**: `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `file` | file (`.rep`) | yes |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/reports \
  -F "file=@/path/to/reporte.rep"
```

**Response `200`**
```json
{
  "status": "success",
  "message": "Archivo cargado, validado y guardado correctamente.",
  "filename": "reporte.rep"
}
```

**Response `400`** — no file sent
```json
{ "status": "error", "message": "No se envió ningun archivo." }
```

**Response `400`** — wrong extension
```json
{ "status": "error", "message": "Formato no permitido. Solo se permiten archivos .rep" }
```

**Response `400`** — file too large
```json
{ "status": "error", "message": "El archivo excede el tamaño máximo permitido." }
```

**Response `400`** — not a valid UNA report
```json
{ "status": "error", "message": "El archivo no es un archivo de reporte valido." }
```

**Response `500`** — DB persistence error
```json
{ "status": "error", "message": "Error al guardar el archivo en la base de datos." }
```

---

### GET `/api/v1/reports` — List uploaded reports

Returns the filenames of all `.REP` files stored in the `data/` directory.

```bash
curl http://127.0.0.1:5000/api/v1/reports
```

**Response `200`**
```json
{
  "name_files": ["reporte_2023-1.rep", "reporte_2023-2.rep"]
}
```

---

### GET `/api/v1/academic-periods` — List academic periods

Returns all academic periods found in the database (populated after uploading reports).

```bash
curl http://127.0.0.1:5000/api/v1/academic-periods
```

**Response `200`**
```json
{
  "status": "success",
  "message": "Academic periods list.",
  "data": {
    "academic_periods": ["2023-1", "2023-2", "2024-1"]
  }
}
```

**Response `500`** — unexpected error
```json
{ "status": "error", "message": "Error al obtener los periodos académicos: <detail>" }
```

---

### GET `/api/v1/students/:identification` — Search student by cédula

Looks up a student by their Venezuelan national ID (`cédula`).

```bash
curl http://127.0.0.1:5000/api/v1/students/12345678
```

**Response `200`**
```json
{
  "status": "success",
  "message": "Student found.",
  "data": {
    "identification": "12345678",
    "name": "Juan Pérez",
    "major": "Administración",
    "grades": [
      { "subject_code": "010", "subject_name": "Matemáticas I", "period": "2023-1", "grade": 14 }
    ]
  }
}
```

**Response `404`**
```json
{ "status": "error", "message": "Student not found." }
```
