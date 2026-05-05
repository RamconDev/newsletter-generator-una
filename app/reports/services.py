import logging
import os
from pathlib import Path

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Subject, Major, Student, Grade, AcademicPeriod
from app.reports.parser import parse_report
from app.reports.repository import (
    SubjectRepository,
    MajorRepository,
    StudentRepository,
    AcademicPeriodRepository,
    GradeRepository,
)

logger = logging.getLogger(__name__)


def get_path_data() -> Path:
    directory = Path(current_app.root_path) / '../data'
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_reports_list() -> list[str]:
    try:
        directory = get_path_data()
        return [f.name for f in directory.iterdir() if f.is_file()]
    except OSError:
        logger.exception("Error listing report files")
        return []


def get_report(file_name: str, encoding: str = "latin-1"):
    path = get_path_data()
    file_path = path / file_name
    try:
        if not file_path.exists() or not file_path.is_file():
            return None
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except OSError:
        logger.exception("Error reading report file: %s", file_name)
        return None


def add_report_to_list(archive) -> bool:
    if archive:
        secure_name = secure_filename(archive.filename)
        save_directory = get_path_data() / secure_name
        archive.save(str(save_directory))
        return True
    return False


def delete_report(filename: str) -> bool:
    file_directory = get_path_data() / secure_filename(filename)
    if file_directory.exists():
        os.remove(file_directory)
        return True
    return False


def process_and_save_report(file_name: str, encoding: str = 'latin-1') -> bool:
    file_path = get_path_data() / file_name
    try:
        parsed_grades = parse_report(file_path, encoding=encoding)

        for record in parsed_grades:
            subject = SubjectRepository.find_by_code(record.subject_code)
            if not subject:
                subject = SubjectRepository.create(record.subject_code, record.subject_name)

            period = None
            if record.period_code:
                period = AcademicPeriodRepository.find_by_code(record.period_code)
                if not period:
                    period = AcademicPeriodRepository.create(record.period_code)

            major = MajorRepository.find_by_code(record.carrera_codigo)
            if not major:
                major = MajorRepository.create(record.carrera_codigo)

            student = StudentRepository.find_by_identification(record.cedula)
            if not student:
                student = StudentRepository.create(record.cedula, record.full_name, major.id)

            period_id = period.id if period else None
            grade = GradeRepository.find_existing(student.id, subject.id, period_id)
            if not grade:
                GradeRepository.create(
                    record.nota_final,
                    record.condicion,
                    student.id,
                    subject.id,
                    period_id,
                    absent=record.absent,
                )
            else:
                GradeRepository.update(grade, record.nota_final, record.condicion, absent=record.absent)

        db.session.commit()
        logger.info("Report '%s' processed successfully (%d records).", file_name, len(parsed_grades))
        return True

    except (OSError, UnicodeDecodeError) as e:
        db.session.rollback()
        logger.error("Error reading report file '%s': %s", file_name, e)
        return False
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Database error processing report '%s': %s", file_name, e)
        return False


def _format_student_data(student: Student, grades=None) -> dict:
    resultado = {
        "cedula": student.identification,
        "nombre": student.full_name,
        "carrera": student.major.code,
        "periodos": [],
    }

    grade_list = grades if grades is not None else student.grades
    periodos_dict = {}
    for grade in grade_list:
        period_code = grade.academic_period.code if grade.academic_period else "Desconocido"
        period_id = grade.academic_period.id if grade.academic_period else None

        if period_code not in periodos_dict:
            periodos_dict[period_code] = {"id": period_id, "materias": []}

        periodos_dict[period_code]["materias"].append({
            "codigo_asignatura": grade.subject.code,
            "asignatura": grade.subject.name,
            "condicion": grade.condition,
            "nota_final": grade.final_score,
            "ausente": grade.absent,
        })

    for period_code, val in periodos_dict.items():
        resultado["periodos"].append({
            "id": val["id"],
            "codigo": period_code,
            "materias": val["materias"],
        })

    return resultado


def get_student_data_from_db(target_cedula: str, mode: str = "exact", period_filter: str = None):
    if mode == "prefix":
        students = StudentRepository.find_by_prefix(target_cedula)
        if not students:
            return None
        if period_filter:
            return [
                _format_student_data(
                    s,
                    grades=GradeRepository.find_by_student_and_period(s.id, period_filter),
                )
                for s in students
            ]
        return [_format_student_data(s) for s in students]
    else:
        student = StudentRepository.find_by_identification(target_cedula)
        if not student:
            return None
        if period_filter:
            grades = GradeRepository.find_by_student_and_period(student.id, period_filter)
            return _format_student_data(student, grades=grades)
        return _format_student_data(student)


def get_students_by_period(
    period_code: str,
    init: int,
    limit: int,
    order: str,
    ascending: bool,
    carrera: str | None,
    nombre: str | None,
) -> dict | None:
    period = AcademicPeriodRepository.find_by_code(period_code)
    if not period:
        return None

    students, total = StudentRepository.find_by_period_paginated(
        period_code, init, limit, order, ascending, carrera, nombre
    )
    return {
        "students": [
            {
                "cedula": s.identification,
                "nombre": s.full_name,
                "carrera": s.major.code,
            }
            for s in students
        ],
        "total": total,
        "init": init,
        "limit": limit,
    }


def get_all_academic_periods() -> list[dict]:
    periods = AcademicPeriodRepository.get_all()
    return [{"id": p.id, "code": p.code} for p in periods]
