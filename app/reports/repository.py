"""
Repository Layer for Reports
Encapsulates all database access logic for academic models.
Follows Single Responsibility Principle: each repository handles one model.
"""

from sqlalchemy import asc as asc_fn, desc as desc_fn

from app.extensions import db
from app.models import Subject, Major, Student, Grade, AcademicPeriod


class SubjectRepository:
    """Repository for Subject (Asignatura) operations."""

    @staticmethod
    def find_by_code(code: str) -> Subject:
        """Find subject by code, returns None if not found."""
        return Subject.query.filter_by(code=code).first()

    @staticmethod
    def create(code: str, name: str) -> Subject:
        """Create and persist a new subject."""
        subject = Subject(code=code, name=name)
        db.session.add(subject)
        db.session.commit()
        return subject


class MajorRepository:
    """Repository for Major (Carrera) operations."""

    @staticmethod
    def find_by_code(code: str) -> Major:
        """Find major by code, returns None if not found."""
        return Major.query.filter_by(code=code).first()

    @staticmethod
    def create(code: str) -> Major:
        """Create and persist a new major."""
        major = Major(code=code)
        db.session.add(major)
        db.session.commit()
        return major


class StudentRepository:
    """Repository for Student operations."""

    @staticmethod
    def find_by_identification(identification: str) -> Student:
        """Find student by identification (cédula), returns None if not found."""
        return Student.query.filter_by(identification=identification).first()

    @staticmethod
    def find_by_id(student_id: int) -> Student:
        """Find student by ID, returns None if not found."""
        return db.session.get(Student, student_id)

    @staticmethod
    def find_by_prefix(prefix: str) -> list:
        """Find all students whose identification starts with prefix."""
        return Student.query.filter(Student.identification.like(f"{prefix}%")).all()

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
            .distinct()
        )

        if carrera:
            query = query.filter(Major.code == carrera)
        if nombre:
            query = query.filter(Student.full_name.ilike(f"%{nombre}%"))

        query = query.order_by(asc_fn(col) if ascending else desc_fn(col))

        total = query.count()
        students = query.offset(init).limit(limit).all()
        return students, total

    @staticmethod
    def create(identification: str, full_name: str, major_id: int) -> Student:
        """Create and persist a new student."""
        student = Student(
            identification=identification,
            full_name=full_name,
            major_id=major_id
        )
        db.session.add(student)
        db.session.commit()
        return student


class AcademicPeriodRepository:
    """Repository for AcademicPeriod operations."""

    @staticmethod
    def find_by_code(code: str) -> AcademicPeriod:
        """Find academic period by code, returns None if not found."""
        return AcademicPeriod.query.filter_by(code=code).first()

    @staticmethod
    def create(code: str) -> AcademicPeriod:
        """Create and persist a new academic period."""
        period = AcademicPeriod(code=code)
        db.session.add(period)
        db.session.commit()
        return period

    @staticmethod
    def get_all() -> list:
        """Retrieve all academic periods."""
        return AcademicPeriod.query.all()


class GradeRepository:
    """Repository for Grade (Nota) operations."""

    @staticmethod
    def find_by_student_and_period(student_id: int, period_code: str) -> list:
        return (
            Grade.query
            .join(AcademicPeriod, Grade.academic_period_id == AcademicPeriod.id)
            .filter(
                Grade.student_id == student_id,
                AcademicPeriod.code == period_code
            )
            .all()
        )

    @staticmethod
    def find_existing(student_id: int, subject_id: int, academic_period_id: int = None) -> Grade:
        """
        Find existing grade for a student-subject-period combination.
        Returns None if not found.
        """
        return Grade.query.filter_by(
            student_id=student_id,
            subject_id=subject_id,
            academic_period_id=academic_period_id
        ).first()

    @staticmethod
    def create(
        final_score: str,
        condition: str,
        student_id: int,
        subject_id: int,
        academic_period_id: int = None
    ) -> Grade:
        """Create and persist a new grade."""
        grade = Grade(
            final_score=final_score,
            condition=condition,
            student_id=student_id,
            subject_id=subject_id,
            academic_period_id=academic_period_id
        )
        db.session.add(grade)
        db.session.commit()
        return grade

    @staticmethod
    def update(grade: Grade, final_score: str, condition: str) -> Grade:
        """Update an existing grade."""
        grade.final_score = final_score
        grade.condition = condition
        db.session.commit()
        return grade
