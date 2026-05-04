# Database — PostgreSQL DDL

Schema completo del proyecto. El orden de creación respeta las dependencias de foreign keys.

> **Nota**: si usas Flask-Migrate (`flask db upgrade`) no necesitas correr este DDL manualmente — Alembic genera y aplica las migraciones automáticamente. Este archivo sirve como referencia y para crear la DB desde cero en un entorno limpio.

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
    id   SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE grades (
    id                 SERIAL PRIMARY KEY,
    final_score        VARCHAR(20) NOT NULL,   -- puede ser "No Presento"
    condition          VARCHAR(20),             -- e.g. 'RG', 'RP'
    student_id         INTEGER NOT NULL REFERENCES students(id),
    subject_id         INTEGER NOT NULL REFERENCES subjects(id),
    academic_period_id INTEGER REFERENCES academic_periods(id)
);
```

---

## 3. Seed data — tablas normalizadas

Solo `roles` requiere datos iniciales. El resto se puebla al subir archivos `.REP`.

```sql
INSERT INTO roles (name, description) VALUES
    ('Admin',  'Acceso total: gestión de usuarios, roles y reportes.'),
    ('Editor', 'Puede cargar y gestionar reportes académicos.'),
    ('Viewer', 'Solo lectura: consulta de estudiantes y períodos.');
```

> El comando `flask --app run init-roles` hace exactamente esto desde la aplicación. Usa uno u otro, no ambos, para evitar duplicados.

---

## 4. Índices recomendados

```sql
-- Búsquedas frecuentes de estudiantes por cédula
CREATE INDEX idx_students_identification ON students(identification);

-- Búsquedas de notas por estudiante y por período
CREATE INDEX idx_grades_student_id         ON grades(student_id);
CREATE INDEX idx_grades_academic_period_id ON grades(academic_period_id);

-- Login / lookup de usuario por username y email
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email    ON users(email);
```

---

## 5. Diagrama de relaciones

```
roles ──────────────┐
                    │ (M:N via roles_users)
users ──────────────┘

majors ──── students ──── grades ──── subjects
                    └──────────────── academic_periods
```
