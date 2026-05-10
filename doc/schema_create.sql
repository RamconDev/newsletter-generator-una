-- =========================================================
-- newsletter_db — Schema completo
-- Aplica sobre una base de datos vacía y recién creada.
-- =========================================================

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

CREATE TABLE academic_periods_audit (
    id            SERIAL PRIMARY KEY,
    period_code   VARCHAR(20)  NOT NULL,
    operation     VARCHAR(10)  NOT NULL,
    user_email    VARCHAR(100),
    user_fullname VARCHAR(200),
    operation_at  TIMESTAMP    NOT NULL,
    source_file   VARCHAR(255),
    ip_address    VARCHAR(45),
    affected_rows JSON
);

CREATE TABLE grades (
    id                 SERIAL PRIMARY KEY,
    condition          VARCHAR(20),              -- RG | RP
    absent             BOOLEAN NOT NULL DEFAULT FALSE,
    obj_1              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_2              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_3              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_4              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_5              BOOLEAN NOT NULL DEFAULT FALSE,
    obj_6              BOOLEAN NOT NULL DEFAULT FALSE,
    objectives_max     INTEGER NOT NULL DEFAULT 0,
    student_id         INTEGER NOT NULL REFERENCES students(id),
    subject_id         INTEGER NOT NULL REFERENCES subjects(id),
    academic_period_id INTEGER REFERENCES academic_periods(id),
    CONSTRAINT uq_grade_student_subject_period
        UNIQUE (student_id, subject_id, academic_period_id)
);

-- ─────────────────────────────────────────
-- ÍNDICES
-- ─────────────────────────────────────────

CREATE INDEX idx_students_identification    ON students(identification);
CREATE INDEX idx_students_major_id          ON students(major_id);

CREATE INDEX idx_grades_student_id          ON grades(student_id);
CREATE INDEX idx_grades_subject_id          ON grades(subject_id);
CREATE INDEX idx_grades_academic_period_id  ON grades(academic_period_id);

CREATE INDEX idx_users_username             ON users(username);
CREATE INDEX idx_users_email               ON users(email);

CREATE UNIQUE INDEX ix_revoked_tokens_jti  ON revoked_tokens(jti);

CREATE INDEX idx_ap_audit_period_code      ON academic_periods_audit(period_code);
CREATE INDEX idx_ap_audit_operation_at     ON academic_periods_audit(operation_at);

-- ─────────────────────────────────────────
-- SEED DATA
-- ─────────────────────────────────────────

INSERT INTO roles (name, description) VALUES
    ('Admin',  'Acceso total: gestión de usuarios, roles y reportes.'),
    ('Editor', 'Puede cargar y gestionar reportes académicos.'),
    ('Viewer', 'Solo lectura: consulta de estudiantes y períodos.');
