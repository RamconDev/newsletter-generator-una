import os
from pathlib import Path
import re
from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Subject, Major, Student, Grade, AcademicPeriod
from app.reports.repository import (
    SubjectRepository,
    MajorRepository,
    StudentRepository,
    AcademicPeriodRepository,
    GradeRepository
)

def get_path_data():
    directory = Path(current_app.root_path) / '../data'
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def get_reports_list():
    try:
        directory = get_path_data()
        print(f"✅ Searching files in: {directory}")

        archives_list = [archive.name for archive in directory.iterdir() if archive.is_file()]

        print(f"✅ Files found: { archives_list }")

        return archives_list
    except Exception as e:
        print(f"✅ Error: {e}")
        return ['Nothing']

def get_report(file_name, encoding="utf-8"):
    path = get_path_data()
    file_path = path / file_name

    print(f"✅ {file_path}")

    try:
        if not file_path.exists() or not file_path.is_file():
            print("✅ The file doesn't exists or isn't valid.")
            return None
        
        with open(file_path, 'r', encoding=encoding) as f:
            for line in f:
                line.strip().split('REPORTE DE OBJETIVOS LOGRADOS (Acumulados)')
    except Exception:
        return None

def add_report_to_list(archive):
    if archive:
        secure_name = secure_filename(archive.filename)
        save_directory = get_path_data() / secure_name
        archive.save(str(save_directory))
        return True
    return False

def delete_report(filename):
    file_directory = get_path_data() / secure_filename(filename)
    if file_directory.exists():
        os.remove(file_directory)
        return True
    return False

def process_and_save_report(file_name, encoding='latin-1'):
    path = get_path_data()
    file_path = path / file_name

    current_subject = None
    current_academic_period = None
    max_objectives = 0 
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            for line in f:
                # 1. Search asignatura
                # Example: | ASIGNATURA: (000) CURSO INTRODUCTORIO
                if "ASIGNATURA:" in line:
                    match_sub = re.search(r'\|\s*ASIGNATURA:\s*\((\d{3})\)\s*([^\|]+)', line)
                    if match_sub:
                        codigo_materia = match_sub.group(1).strip()
                        nombre_materia = match_sub.group(2).strip()

                        current_subject = SubjectRepository.find_by_code(codigo_materia)

                        if not current_subject:
                            current_subject = SubjectRepository.create(codigo_materia, nombre_materia)
                        continue
                
                # Buscar Periodo
                if "PERIODO" in line:
                    match_period = re.search(r'PERIODO\s*:\s*([\w\-]+)', line)
                    if match_period:
                        period_code = match_period.group(1).strip()
                        current_academic_period = AcademicPeriodRepository.find_by_code(period_code)
                        if not current_academic_period:
                            current_academic_period = AcademicPeriodRepository.create(period_code)
                        continue
                
                # 2. Search max objectives
                if "OBJETIVO" in line and current_subject:
                    max_objectives = len(re.findall(r'\|\d{2}\s', line))
                    if max_objectives == 0:
                        max_objectives = -1
                    continue

                # 3. Search student data
                cedula_match = re.search(r'\b([VEJP]-\d+)\b', line)
                if cedula_match and current_subject:
                    cedula = cedula_match.group(1)
                    
                    # Limpiamos los múltiples espacios para separar fácil
                    linea_limpia = re.sub(r'\s+', ' ', line.strip())
                    partes = linea_limpia.split(cedula)
                    
                    if len(partes) > 1:
                        resto = partes[1].strip() # Ej: "610 JAIMES CAMACHO LUSMILA RG 1 1 1 1 1 1 6"
                        
                        # Si dice "No Presento", es un caso especial
                        if "No Presento" in resto:
                            carrera_codigo = resto.split()[0]
                            nombre = resto.replace(carrera_codigo, "").replace("No Presento", "").strip()
                            condicion = "NP"
                            nota_final = "No Presentó"
                        else:
                            tokens = resto.split()
                            carrera_codigo = tokens[0]
                            
                            # La nota final es el último número
                            nota_cruda = tokens[-1]
                            # Formateamos al estilo X/Y (Ej: "6/6" o "4/6")
                            nota_final = f"{nota_cruda}/{max_objectives}"
                            
                            # Condición suele ser RG (Regular), RP (Repitiente), etc.
                            # Asumimos que los 1 y 0 son objetivos, así que buscamos la última letra antes de los números
                            letras_tokens = [t for t in tokens[1:-1] if not t.isdigit()]
                            condicion = letras_tokens[-1] if letras_tokens else "N/A"
                            
                            # El nombre es todo lo que está entre la carrera y la condición
                            nombre_tokens = []
                            for t in tokens[1:]:
                                if t == condicion or t.isdigit():
                                    break
                                nombre_tokens.append(t)
                            nombre = " ".join(nombre_tokens)

                        # --- GUARDADO EN BASE DE DATOS ---
                        
                        # A. Gestionar Carrera (Major)
                        major = MajorRepository.find_by_code(carrera_codigo)
                        if not major:
                            major = MajorRepository.create(carrera_codigo)

                        # B. Gestionar Estudiante (Student)
                        student = StudentRepository.find_by_identification(cedula)
                        if not student:
                            student = StudentRepository.create(cedula, nombre, major.id)
                            
                        # C. Gestionar Nota (Grade)
                        # Verificamos si ya existe esta nota para no duplicarla si suben el archivo 2 veces
                        grade = GradeRepository.find_existing(
                            student.id,
                            current_subject.id,
                            current_academic_period.id if current_academic_period else None
                        )
                        
                        if not grade:
                            grade = GradeRepository.create(
                                nota_final,
                                condicion,
                                student.id,
                                current_subject.id,
                                current_academic_period.id if current_academic_period else None
                            )
                        else:
                            # Si ya existe, la actualizamos por si el nuevo reporte tiene correcciones
                            grade = GradeRepository.update(grade, nota_final, condicion)

            # Hacer un commit final para guardar todas las calificaciones
            db.session.commit()
            print("✅ Base de datos poblada exitosamente.")
            return True
                
    except Exception as e:
        db.session.rollback() # Si algo falla, revertimos los cambios en la BD
        print(f"❌ Error procesando el archivo para la BD: {e}")
        return False

def _format_student_data(student, grades=None):
    resultado = {
        "cedula": student.identification,
        "nombre": student.full_name,
        "carrera": student.major.code,
        "periodos": []
    }

    grade_list = grades if grades is not None else student.grades
    periodos_dict = {}
    for grade in grade_list:
        period_code = grade.academic_period.code if grade.academic_period else "Desconocido"
        period_id = grade.academic_period.id if grade.academic_period else None
                
        if period_code not in periodos_dict:
            periodos_dict[period_code] = {
                "id": period_id,
                "materias": []
            }
            
        periodos_dict[period_code]["materias"].append({
            "codigo_asignatura": grade.subject.code,
            "asignatura": grade.subject.name,
            "condicion": grade.condition,
            "nota_final": grade.final_score
        })
        
    for period_code, val in periodos_dict.items():
        resultado["periodos"].append({
            "id": val["id"],
            "codigo": period_code,
            "materias": val["materias"]
        })
        
    return resultado

def get_student_data_from_db(target_cedula, mode="exact", period_filter=None):
    if mode == "prefix":
        students = StudentRepository.find_by_prefix(target_cedula)
        if not students:
            return None
        if period_filter:
            return [
                _format_student_data(
                    s,
                    grades=GradeRepository.find_by_student_and_period(s.id, period_filter)
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

def get_all_academic_periods():
    periods = AcademicPeriodRepository.get_all()
    return [{"id": p.id, "code": p.code} for p in periods]
