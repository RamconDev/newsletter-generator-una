import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, request
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Subject, Major, Student, Grade, AcademicPeriod
from app.reports.parser import parse_report
from app.reports.repository import (
    SubjectRepository,
    MajorRepository,
    StudentRepository,
    SedeRepository,
    AcademicPeriodRepository,
    AcademicPeriodAuditRepository,
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


def process_and_save_report(
    file_name: str,
    encoding: str = 'latin-1',
    uploaded_by_id: int | None = None,
    uploaded_by_email: str | None = None,
    uploaded_by_fullname: str | None = None,
    source_file: str | None = None,
) -> tuple[bool, str | None]:
    """
    Returns (True, None) on success, (False, error_code) on failure.
    error_code values: "REPORTE_VACIO" | "ERROR_LECTURA" | "ERROR_DB"
    """
    file_path = get_path_data() / file_name
    try:
        parsed_grades = parse_report(file_path, encoding=encoding)
    except (OSError, UnicodeDecodeError) as e:
        logger.error("Error reading report file '%s': %s", file_name, e)
        return False, "ERROR_LECTURA"

    if not parsed_grades:
        logger.warning("Report '%s' produced 0 records — no valid data detected.", file_name)
        return False, "REPORTE_VACIO"

    try:
        first = parsed_grades[0]

        # 1. Sede — una sola por archivo
        sede_id = None
        if first.universidad:
            sede = SedeRepository.find_or_create(first.universidad, first.centro_local, first.oficina)
            sede_id = sede.id

        # 2. Período — uno solo por archivo
        period = None
        period_code = first.period_code
        if period_code:
            period = AcademicPeriodRepository.find_by_code(period_code, sede_id=sede_id)
            is_new_period = period is None
            if is_new_period:
                period = AcademicPeriodRepository.create(
                    period_code,
                    sede_id=sede_id,
                    uploaded_by_id=uploaded_by_id,
                    uploaded_by_email=uploaded_by_email,
                    uploaded_by_fullname=uploaded_by_fullname,
                    uploaded_at=datetime.now(timezone.utc),
                    source_file=source_file,
                )
            # Auditoría siempre: INSERT si es nuevo, UPDATE si ya existía
            AcademicPeriodAuditRepository.create(
                period_code=period_code,
                operation='INSERT' if is_new_period else 'UPDATE',
                sede_id=sede_id,
                user_email=uploaded_by_email,
                user_fullname=uploaded_by_fullname,
                operation_at=datetime.now(timezone.utc),
                source_file=source_file,
                ip_address=request.remote_addr,
            )

        period_id = period.id if period else None

        # 3. Loop de registros (subject/major/student/grade)
        for record in parsed_grades:
            subject = SubjectRepository.find_by_code(record.subject_code)
            if not subject:
                subject = SubjectRepository.create(record.subject_code, record.subject_name)

            major = MajorRepository.find_by_code(record.carrera_codigo)
            if not major:
                major = MajorRepository.create(record.carrera_codigo)

            student = StudentRepository.find_by_identification(record.cedula)
            if not student:
                student = StudentRepository.create(record.cedula, record.full_name, major.id)

            grade = GradeRepository.find_existing(student.id, subject.id, period_id)
            if not grade:
                GradeRepository.create(
                    condition=record.condicion,
                    student_id=student.id,
                    subject_id=subject.id,
                    objectives_achieved=record.objectives_achieved,
                    objectives_total=record.objectives_total,
                    calificacion=record.calificacion,
                    academic_period_id=period_id,
                    absent=record.absent,
                )
            else:
                GradeRepository.update(
                    grade,
                    condition=record.condicion,
                    objectives_achieved=record.objectives_achieved,
                    objectives_total=record.objectives_total,
                    calificacion=record.calificacion,
                    absent=record.absent,
                )

        db.session.commit()
        logger.info("Report '%s' processed successfully (%d records).", file_name, len(parsed_grades))
        return True, None

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Database error processing report '%s': %s", file_name, e)
        return False, "ERROR_DB"


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
        period_id   = grade.academic_period.id   if grade.academic_period else None

        if period_code not in periodos_dict:
            periodos_dict[period_code] = {"id": period_id, "materias": []}

        if grade.absent or not grade.objectives_total or not grade.objectives_achieved:
            nota_final = "No Presento"
        elif grade.calificacion:
            nota_final = grade.calificacion
        else:
            nota_final = f"{grade.objectives_achieved}/{grade.objectives_total}"

        periodos_dict[period_code]["materias"].append({
            "codigo_asignatura": grade.subject.code,
            "asignatura":        grade.subject.name,
            "condicion":         grade.condition,
            "ausente":           grade.absent,
            "nota_final":        nota_final,
        })

    for period_code, val in periodos_dict.items():
        resultado["periodos"].append({
            "id":       val["id"],
            "codigo":   period_code,
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
    return [p.to_dict() for p in periods]


def get_all_audit_records() -> list[dict]:
    records = AcademicPeriodAuditRepository.get_all()
    return [{k: v for k, v in r.to_dict().items() if k != 'id'} for r in records]


def delete_academic_period(
    period_code: str,
    deleted_by_email: str | None = None,
    deleted_by_fullname: str | None = None,
) -> dict | None:
    result = AcademicPeriodRepository.delete_period_cascade(period_code)
    if result is None:
        return None
    AcademicPeriodAuditRepository.create(
        period_code=period_code,
        operation='DELETE',
        user_email=deleted_by_email,
        user_fullname=deleted_by_fullname,
        ip_address=request.remote_addr,
        affected_rows={
            'grades_deleted': result['grades_deleted'],
            'students_deleted': result['students_deleted'],
        },
    )
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Database error deleting period '%s': %s", period_code, e)
        raise
    return result
