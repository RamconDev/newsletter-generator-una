import os
from pathlib import Path
import re
from flask import current_app
from werkzeug.utils import secure_filename

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

def _extract_cedula(line):
    match = re.search(r"\b[VEJP]-\d+\b", line)
    return match.group(0) if match else None

def _matches_cedula(parsed_cedula, target_cedula, mode):
    if mode == "prefix":
        return parsed_cedula.startswith(target_cedula)
    return parsed_cedula == target_cedula

def _build_student_subject(line, current_subject):
    clean_line = line.replace('|', ' ')
    parts = clean_line.split()
    if len(parts) < 4:
        return None

    carrera = parts[2]
    start_index = line.find(carrera) + len(carrera)
    end_index = line.rfind("  ")
    nombre = line[start_index:end_index].strip() if end_index != -1 else " ".join(parts[3:])

    tot_match = re.search(r"(\d+|No Presento)\s*$", line.strip())
    nota = tot_match.group(1) if tot_match else "N/A"

    return {
        "carrera": carrera,
        "nombre": nombre,
        "materia": {
            "asignatura": current_subject,
            "nota_final": nota,
        },
    }

def _append_student_match(students_map, line, current_subject, target_cedula, mode):
    parsed_cedula = _extract_cedula(line)
    if not parsed_cedula or not _matches_cedula(parsed_cedula, target_cedula, mode):
        return

    student_row = _build_student_subject(line, current_subject)
    if not student_row:
        return

    if parsed_cedula not in students_map:
        students_map[parsed_cedula] = {
            "cedula": parsed_cedula,
            "nombre": student_row["nombre"],
            "carrera": student_row["carrera"],
            "materias": [],
        }

    students_map[parsed_cedula]["materias"].append(student_row["materia"])

def get_student_data(file_name, target_cedula, encoding="latin-1", mode="exact", return_all=False):
    path = get_path_data()
    file_path = path / file_name

    students_map = {}

    print(f"✅ {target_cedula}")

    current_subject = None

    try:
        with open(file_path, 'r', encoding=encoding) as f:
            print(f"✅ {file_path}")
            for line in f:
                # 1. Detectar la Asignatura (está en una línea que contiene 'ASIGNATURA:')
                if "ASIGNATURA:" in line:
                    # Extraemos lo que esté entre 'ASIGNATURA:' y el siguiente '|'
                    match_sub = re.search(r"ASIGNATURA:\s*(.*?)\s*\|", line)
                    if match_sub:
                        current_subject = match_sub.group(1).strip()

                _append_student_match(students_map, line, current_subject, target_cedula, mode)

        if return_all:
            return list(students_map.values())

        return students_map.get(target_cedula)

    except Exception as e:
        print(f"❌ Error procesando el archivo: {e}")
        return [] if return_all else None