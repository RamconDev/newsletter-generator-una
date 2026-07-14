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
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    role_id          INTEGER REFERENCES roles(id) ON DELETE SET NULL
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
    code VARCHAR(10)  NOT NULL UNIQUE,
    name VARCHAR(150)
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

CREATE TABLE academic_periods_audit (
    id            SERIAL PRIMARY KEY,
    period_code   VARCHAR(20)  NOT NULL,
    operation     VARCHAR(20)  NOT NULL,  -- CREACIÓN | ACTUALIZACIÓN | ELIMINACIÓN
    user_email    VARCHAR(100),
    user_fullname VARCHAR(200),
    operation_at  TIMESTAMP    NOT NULL,
    source_file   VARCHAR(255),
    ip_address    VARCHAR(45),
    affected_rows JSON
);

CREATE TABLE grades (
    id                 SERIAL PRIMARY KEY,
    condition          VARCHAR(20),              -- RG | RP (condición real del estudiante)
    absent             BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE si "No Presento"
    obj_1              BOOLEAN NOT NULL DEFAULT FALSE,  -- objetivo T1 logrado
    obj_2              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_3              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_4              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_5              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_6              BOOLEAN NOT NULL DEFAULT FALSE,
    objectives_max     INTEGER NOT NULL DEFAULT 0,      -- máx. objetivos posibles para la asignatura
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
CREATE INDEX idx_users_role_id  ON users(role_id);

-- Lookup rápido de tokens revocados por JTI
CREATE UNIQUE INDEX ix_revoked_tokens_jti ON revoked_tokens(jti);

-- Consultas de auditoría por período y por rango de fechas
CREATE INDEX idx_ap_audit_period_code  ON academic_periods_audit (period_code);
CREATE INDEX idx_ap_audit_operation_at ON academic_periods_audit (operation_at);
```

---

## 5. Migraciones — bases de datos existentes

Aplicar en orden sobre una DB ya creada con el DDL anterior.

```sql
-- Snapshot de auditoría del usuario que subió el reporte, tomado del JWT
ALTER TABLE academic_periods ADD COLUMN uploaded_by_email    VARCHAR(100);
ALTER TABLE academic_periods ADD COLUMN uploaded_by_fullname VARCHAR(200);

-- Tabla de auditoría para INSERT y DELETE en academic_periods
CREATE TABLE academic_periods_audit (
    id            SERIAL PRIMARY KEY,
    period_code   VARCHAR(20)  NOT NULL,
    operation     VARCHAR(20)  NOT NULL,
    user_email    VARCHAR(100),
    user_fullname VARCHAR(200),
    operation_at  TIMESTAMP    NOT NULL,
    source_file   VARCHAR(255),
    ip_address    VARCHAR(45),
    affected_rows JSON
);
CREATE INDEX idx_ap_audit_period_code  ON academic_periods_audit (period_code);
CREATE INDEX idx_ap_audit_operation_at ON academic_periods_audit (operation_at);

-- Objetivos individuales por asignatura (reemplaza final_score)
-- Archivo de migración completo: doc/collections/migration_grades_objectives.sql
ALTER TABLE grades DROP COLUMN IF EXISTS final_score;
ALTER TABLE grades ADD COLUMN obj_1          BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE grades ADD COLUMN obj_2          BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE grades ADD COLUMN obj_3          BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE grades ADD COLUMN obj_4          BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE grades ADD COLUMN obj_5          BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE grades ADD COLUMN obj_6          BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE grades ADD COLUMN objectives_max INTEGER NOT NULL DEFAULT 0;

-- Un solo rol por usuario: reemplaza la relación M:N roles_users por FK role_id
ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL;
CREATE INDEX idx_users_role_id ON users(role_id);

-- Backfill: tomar el rol de mayor privilegio de cada usuario (Admin > Editor > Viewer)
UPDATE users u
SET role_id = (
    SELECT ru.role_id
    FROM roles_users ru
    JOIN roles r ON r.id = ru.role_id
    WHERE ru.user_id = u.id
    ORDER BY CASE r.name
        WHEN 'Admin'  THEN 1
        WHEN 'Editor' THEN 2
        WHEN 'Viewer' THEN 3
        ELSE 4
    END
    LIMIT 1
);

DROP TABLE roles_users;

-- Operación de auditoría en español (scripts: doc/schema_alter_operation_es.sql
-- y doc/schema_alter_operation_es_rollback.sql)
ALTER TABLE academic_periods_audit ALTER COLUMN operation TYPE VARCHAR(20);
ALTER TABLE users_audit            ALTER COLUMN operation TYPE VARCHAR(20);
UPDATE academic_periods_audit SET operation = CASE operation
    WHEN 'INSERT' THEN 'CREACIÓN' WHEN 'UPDATE' THEN 'ACTUALIZACIÓN'
    WHEN 'DELETE' THEN 'ELIMINACIÓN' ELSE operation END;
UPDATE users_audit SET operation = CASE operation
    WHEN 'INSERT' THEN 'CREACIÓN' WHEN 'UPDATE' THEN 'ACTUALIZACIÓN'
    WHEN 'DELETE' THEN 'ELIMINACIÓN' ELSE operation END;
```

---

## 6. Diagrama de relaciones

```
roles ──────────────┐
                    │ (1:N — users.role_id, SET NULL on delete)
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
