"""
Repository Layer for Reports
Encapsulates all database access logic for academic models.
Follows Single Responsibility Principle: each repository handles one model.

NOTE: create/update methods use flush() instead of commit() so the calling
service controls the transaction boundary with a single commit.
"""

from sqlalchemy import asc as asc_fn, desc as desc_fn
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Subject, Major, Student, Grade, AcademicPeriod


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

        query = (
            db.session.query(Student)
            .join(Major, Student.major_id == Major.id)
            .join(Grade, Grade.student_id == Student.id)
            .join(AcademicPeriod, Grade.academic_period_id == AcademicPeriod.id)
            .filter(AcademicPeriod.code == period_code)
            .options(joinedload(Student.major))
            .distinct()
        )

        if carrera:
            query = query.filter(Major.code == carrera)
        if nombre:
            escaped = _escape_like(nombre)
            query = query.filter(Student.full_name.ilike(f"%{escaped}%", escape='\\'))

        query = query.order_by(asc_fn(col) if ascending else desc_fn(col))

        total = query.count()
        students = query.offset(init).limit(limit).all()
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
    def create(code: str) -> AcademicPeriod:
        period = AcademicPeriod(code=code)
        db.session.add(period)
        db.session.flush()
        return period

    @staticmethod
    def get_all() -> list:
        return AcademicPeriod.query.all()


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
    def create(
        final_score: str,
        condition: str,
        student_id: int,
        subject_id: int,
        academic_period_id: int = None,
        absent: bool = False,
    ) -> Grade:
        grade = Grade(
            final_score=final_score,
            condition=condition,
            student_id=student_id,
            subject_id=subject_id,
            academic_period_id=academic_period_id,
            absent=absent,
        )
        db.session.add(grade)
        db.session.flush()
        return grade

    @staticmethod
    def update(grade: Grade, final_score: str, condition: str, absent: bool = False) -> Grade:
        grade.final_score = final_score
        grade.condition = condition
        grade.absent = absent
        db.session.flush()
        return grade
