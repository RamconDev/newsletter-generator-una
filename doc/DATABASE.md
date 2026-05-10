# Database — PostgreSQL DDL

Schema autoritativo del proyecto. El DBA aplica este archivo directamente.
Todo cambio de esquema se coordina actualizando este documento primero.
El orden de creación respeta las dependencias de foreign keys.

---

## 1. Crear la base de datos

```sql
CREATE DATABASE newsletter_db;
\c newsletter_db
```

---

## 2. CREATE TABLE

```sql
-- ─────────────────────────────────────────
-- AUTH
-- ─────────────────────────────────────────

CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE users (
    id               SERIAL PRIMARY KEY,
    firstname        VARCHAR(100) NOT NULL,
    lastname         VARCHAR(100) NOT NULL,
    username         VARCHAR(100) NOT NULL UNIQUE,
    email            VARCHAR(100) NOT NULL UNIQUE,
    password_hash    VARCHAR(255) NOT NULL,
    phone            VARCHAR(100),
    create_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    modificated_at   TIMESTAMP,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE roles_users (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE revoked_tokens (
    id         SERIAL PRIMARY KEY,
    jti        VARCHAR(36) NOT NULL,
    revoked_at TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_revoked_tokens_jti UNIQUE (jti)
);

-- ─────────────────────────────────────────
-- ACADEMIC DOMAIN
-- ─────────────────────────────────────────

CREATE TABLE majors (
    id   SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE students (
    id             SERIAL PRIMARY KEY,
    identification VARCHAR(20)  NOT NULL UNIQUE,
    full_name      VARCHAR(150) NOT NULL,
    major_id       INTEGER NOT NULL REFERENCES majors(id)
);

CREATE TABLE subjects (
    id   SERIAL PRIMARY KEY,
    code VARCHAR(10)  NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL
);

CREATE TABLE academic_periods (
    id                   SERIAL PRIMARY KEY,
    code                 VARCHAR(20) NOT NULL UNIQUE,
    uploaded_by_id       INTEGER REFERENCES users(id) ON DELETE SET NULL,
    uploaded_by_email    VARCHAR(100),
    uploaded_by_fullname VARCHAR(200),
    uploaded_at          TIMESTAMP,
    source_file          VARCHAR(255)
);

CREATE TABLE grades (
    id                 SERIAL PRIMARY KEY,
    final_score        VARCHAR(20) NOT NULL,   -- puede ser "No Presento"
    condition          VARCHAR(20),             -- e.g. 'RG', 'RP'
    absent             BOOLEAN NOT NULL DEFAULT FALSE,
    student_id         INTEGER NOT NULL REFERENCES students(id),
    subject_id         INTEGER NOT NULL REFERENCES subjects(id),
    academic_period_id INTEGER REFERENCES academic_periods(id),
    CONSTRAINT uq_grade_student_subject_period
        UNIQUE (student_id, subject_id, academic_period_id)
);
```

---

## 3. Seed data — tablas normalizadas

### 3.1 Roles

Solo `roles` requiere datos iniciales. El resto se puebla al subir archivos `.REP`.

```sql
INSERT INTO roles (name, description) VALUES
    ('Admin',  'Acceso total: gestión de usuarios, roles y reportes.'),
    ('Editor', 'Puede cargar y gestionar reportes académicos.'),
    ('Viewer', 'Solo lectura: consulta de estudiantes y períodos.');
```

## 4. Índices

```sql
-- Búsquedas frecuentes de estudiantes por cédula
CREATE INDEX idx_students_identification ON students(identification);
CREATE INDEX idx_students_major_id       ON students(major_id);

-- Búsquedas de notas por estudiante, asignatura y por período
CREATE INDEX idx_grades_student_id         ON grades(student_id);
CREATE INDEX idx_grades_subject_id         ON grades(subject_id);
CREATE INDEX idx_grades_academic_period_id ON grades(academic_period_id);

-- Login / lookup de usuario por username y email
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email    ON users(email);

-- Lookup rápido de tokens revocados por JTI
CREATE UNIQUE INDEX ix_revoked_tokens_jti ON revoked_tokens(jti);
```

---

## 5. Migraciones — bases de datos existentes

Aplicar en orden sobre una DB ya creada con el DDL anterior.

```sql
-- Snapshot de auditoría del usuario que subió el reporte, tomado del JWT
ALTER TABLE academic_periods ADD COLUMN uploaded_by_email    VARCHAR(100);
ALTER TABLE academic_periods ADD COLUMN uploaded_by_fullname VARCHAR(200);
```

---

## 6. Diagrama de relaciones

```
roles ──────────────┐
                    │ (M:N via roles_users)
users ──────────────┘
  │
  │ uploaded_by_id (SET NULL on delete)
  ▼
academic_periods ───┐
                    │
majors ──── students ──── grades ──── subjects
                    └──────────────── academic_periods

revoked_tokens  (standalone — almacena JTIs de tokens JWT invalidados)
```

---
