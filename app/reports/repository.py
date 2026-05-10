"""
Repository Layer for Reports
Encapsulates all database access logic for academic models.
Follows Single Responsibility Principle: each repository handles one model.

NOTE: create/update methods use flush() instead of commit() so the calling
service controls the transaction boundary with a single commit.
"""

from datetime import datetime, timezone

from sqlalchemy import asc as asc_fn, desc as desc_fn, func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Subject, Major, Student, Grade, AcademicPeriod, AcademicPeriodAudit


def _escape_like(value: str) -> str:
    """Escape LIKE special characters to prevent wildcard injection."""
    return value.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')


class SubjectRepository:
    """Repository for Subject (Asignatura) operations."""

    @staticmethod
    def find_by_code(code: str) -> Subject:
        return Subject.query.filter_by(code=code).first()

    @staticmethod
    def create(code: str, name: str) -> Subject:
        subject = Subject(code=code, name=name)
        db.session.add(subject)
        db.session.flush()
        return subject


class MajorRepository:
    """Repository for Major (Carrera) operations."""

    @staticmethod
    def find_by_code(code: str) -> Major:
        return Major.query.filter_by(code=code).first()

    @staticmethod
    def create(code: str) -> Major:
        major = Major(code=code)
        db.session.add(major)
        db.session.flush()
        return major


class StudentRepository:
    """Repository for Student operations."""

    @staticmethod
    def find_by_identification(identification: str) -> Student:
        return (
            Student.query
            .options(
                joinedload(Student.grades).joinedload(Grade.subject),
                joinedload(Student.grades).joinedload(Grade.academic_period),
            )
            .filter_by(identification=identification)
            .first()
        )

    @staticmethod
    def find_by_id(student_id: int) -> Student:
        return db.session.get(Student, student_id)

    @staticmethod
    def find_by_prefix(prefix: str) -> list:
        escaped = _escape_like(prefix)
        return (
            Student.query
            .options(
                joinedload(Student.grades).joinedload(Grade.subject),
                joinedload(Student.grades).joinedload(Grade.academic_period),
            )
            .filter(Student.identification.like(f"{escaped}%", escape='\\'))
            .all()
        )

    @staticmethod
    def find_by_period_paginated(
        period_code: str,
        init: int,
        limit: int,
        order: str,
        ascending: bool,
        carrera: str | None,
        nombre: str | None,
    ) -> tuple[list, int]:
        order_map = {
            "cedula": Student.identification,
            "nombre": Student.full_name,
            "carrera": Major.code,
        }
        col = order_map.get(order, Student.full_name)

        # Base query without eager loading — used for counting
        base_query = (
            db.session.query(Student.id)
            .join(Major, Student.major_id == Major.id)
            .join(Grade, Grade.student_id == Student.id)
            .join(AcademicPeriod, Grade.academic_period_id == AcademicPeriod.id)
            .filter(AcademicPeriod.code == period_code)
            .distinct()
        )

        if carrera:
            base_query = base_query.filter(Major.code == carrera)
        if nombre:
            escaped = _escape_like(nombre)
            base_query = base_query.filter(Student.full_name.ilike(f"%{escaped}%", escape='\\'))

        total = db.session.query(func.count()).select_from(base_query.subquery()).scalar()

        # Data query with eager loading for the page slice
        data_query = (
            db.session.query(Student)
            .join(Major, Student.major_id == Major.id)
            .join(Grade, Grade.student_id == Student.id)
            .join(AcademicPeriod, Grade.academic_period_id == AcademicPeriod.id)
            .filter(AcademicPeriod.code == period_code)
            .options(joinedload(Student.major))
            .distinct()
        )

        if carrera:
            data_query = data_query.filter(Major.code == carrera)
        if nombre:
            escaped = _escape_like(nombre)
            data_query = data_query.filter(Student.full_name.ilike(f"%{escaped}%", escape='\\'))

        students = data_query.order_by(asc_fn(col) if ascending else desc_fn(col)).offset(init).limit(limit).all()
        return students, total

    @staticmethod
    def create(identification: str, full_name: str, major_id: int) -> Student:
        student = Student(
            identification=identification,
            full_name=full_name,
            major_id=major_id,
        )
        db.session.add(student)
        db.session.flush()
        return student


class AcademicPeriodRepository:
    """Repository for AcademicPeriod operations."""

    @staticmethod
    def find_by_code(code: str) -> AcademicPeriod:
        return AcademicPeriod.query.filter_by(code=code).first()

    @staticmethod
    def create(
        code: str,
        uploaded_by_id: int | None = None,
        uploaded_by_email: str | None = None,
        uploaded_by_fullname: str | None = None,
        uploaded_at: datetime | None = None,
        source_file: str | None = None,
    ) -> AcademicPeriod:
        period = AcademicPeriod(
            code=code,
            uploaded_by_id=uploaded_by_id,
            uploaded_by_email=uploaded_by_email,
            uploaded_by_fullname=uploaded_by_fullname,
            uploaded_at=uploaded_at,
            source_file=source_file,
        )
        db.session.add(period)
        db.session.flush()
        return period

    @staticmethod
    def get_all() -> list:
        return AcademicPeriod.query.all()

    @staticmethod
    def delete_period_cascade(period_code: str) -> dict | None:
        period = AcademicPeriod.query.filter_by(code=period_code).first()
        if not period:
            return None

        affected_student_ids = [
            row[0]
            for row in (
                db.session.query(Grade.student_id)
                .filter(Grade.academic_period_id == period.id)
                .distinct()
                .all()
            )
        ]

        grades_deleted = Grade.query.filter_by(academic_period_id=period.id).delete()

        orphan_ids = [
            sid for sid in affected_student_ids
            if not Grade.query.filter_by(student_id=sid).first()
        ]
        if orphan_ids:
            Student.query.filter(Student.id.in_(orphan_ids)).delete(synchronize_session=False)

        db.session.delete(period)

        return {
            "grades_deleted": grades_deleted,
            "students_deleted": len(orphan_ids),
        }


class AcademicPeriodAuditRepository:
    """Repository for AcademicPeriodAudit operations."""

    @staticmethod
    def create(
        period_code: str,
        operation: str,
        user_email: str | None = None,
        user_fullname: str | None = None,
        operation_at: datetime | None = None,
        source_file: str | None = None,
        ip_address: str | None = None,
        affected_rows: dict | None = None,
    ) -> AcademicPeriodAudit:
        audit = AcademicPeriodAudit(
            period_code=period_code,
            operation=operation,
            user_email=user_email,
            user_fullname=user_fullname,
            operation_at=operation_at or datetime.now(timezone.utc),
            source_file=source_file,
            ip_address=ip_address,
            affected_rows=affected_rows,
        )
        db.session.add(audit)
        return audit


class GradeRepository:
    """Repository for Grade (Nota) operations."""

    @staticmethod
    def find_by_student_and_period(student_id: int, period_code: str) -> list:
        return (
            Grade.query
            .options(joinedload(Grade.subject), joinedload(Grade.academic_period))
            .join(AcademicPeriod, Grade.academic_period_id == AcademicPeriod.id)
            .filter(
                Grade.student_id == student_id,
                AcademicPeriod.code == period_code,
            )
            .all()
        )

    @staticmethod
    def find_existing(student_id: int, subject_id: int, academic_period_id: int = None) -> Grade:
        return Grade.query.filter_by(
            student_id=student_id,
            subject_id=subject_id,
            academic_period_id=academic_period_id,
        ).first()

    @staticmethod
    def _unpack_objectives(objectives: list[bool]) -> dict:
        padded = (objectives + [False] * 6)[:6]
        return {
            'obj_1': padded[0],
            'obj_2': padded[1],
            'obj_3': padded[2],
            'obj_4': padded[3],
            'obj_5': padded[4],
            'obj_6': padded[5],
        }

    @staticmethod
    def create(
        condition: str,
        student_id: int,
        subject_id: int,
        objectives: list[bool],
        objectives_max: int,
        academic_period_id: int = None,
        absent: bool = False,
    ) -> Grade:
        obj_fields = GradeRepository._unpack_objectives(objectives)
        grade = Grade(
            condition=condition,
            student_id=student_id,
            subject_id=subject_id,
            academic_period_id=academic_period_id,
            absent=absent,
            objectives_max=objectives_max,
            **obj_fields,
        )
        db.session.add(grade)
        db.session.flush()
        return grade

    @staticmethod
    def update(
        grade: Grade,
        condition: str,
        objectives: list[bool],
        objectives_max: int,
        absent: bool = False,
    ) -> Grade:
        obj_fields = GradeRepository._unpack_objectives(objectives)
        grade.condition = condition
        grade.absent = absent
        grade.objectives_max = objectives_max
        for k, v in obj_fields.items():
            setattr(grade, k, v)
        db.session.flush()
        return grade
