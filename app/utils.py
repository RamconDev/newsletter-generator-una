from pathlib import Path

import os
from pathlib import Path
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
                columns = line.strip().split('REPORTE DE OBJETIVOS LOGRADOS (Acumulados)')
    except:
        pass
    
def add_report_to_list(archive):
    if archive:
        secure_name = secure_filename(archive.filename)
        save_directory = get_path_data() / secure_name
        archive.save(str(save_directory))
        return True
    return False

def delete_report(filename):
    file_directory = get_path_data / secure_filename(filename)
    if file_directory.exists():
        os.remove(file_directory)
        return True
    return False

import re

def get_student_data(file_name, target_cedula, encoding="latin-1"):
    path = get_path_data()
    file_path = path / file_name
    
    student_info = {
        "cedula": target_cedula,
        "nombre": None,
        "carrera": None,
        "materias": []
    }

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

                # 2. Buscar la cédula del estudiante en la línea actual
                # Usamos el target_cedula (ej: V-13149341)
                if target_cedula in line:
                    print(f"✅ {line}")

                    # El formato del reporte es de ancho fijo. 
                    # Según el snippet: N°(5), CEDULA(13), CARRERA(8), NOMBRE(30)... y al final TOT.
                    
                    # Limpiamos la línea de los caracteres de tabla '|'
                    clean_line = line.replace('|', ' ')
                    parts = clean_line.split()
                    
                    # Si la línea tiene suficientes partes (Nro, Cedula, Carrera, Nombre...)
                    if len(parts) >= 4:
                        # Guardamos datos básicos si no los tenemos
                        if not student_info["nombre"]:
                            # El nombre suele estar después de la carrera (índice 2)
                            # Intentamos capturar el nombre completo reconstruyendo los strings
                            student_info["carrera"] = parts[2]
                            # El nombre está entre la carrera y los resultados numéricos
                            # Buscamos la posición de la carrera y tomamos lo que sigue
                            start_index = line.find(parts[2]) + len(parts[2])
                            end_index = line.rfind("  ") # Donde empiezan los espacios antes de las notas
                            student_info["nombre"] = line[start_index:end_index].strip()

                        # 3. Extraer la nota final (TOT.)
                        # Es el último valor numérico de la línea
                        tot_match = re.search(r"(\d+|No Presento)\s*$", line.strip())
                        nota = tot_match.group(1) if tot_match else "N/A"

                        student_info["materias"].append({
                            "asignatura": current_subject,
                            "nota_final": nota
                        })

        return student_info if student_info["nombre"] else None

    except Exception as e:
        print(f"❌ Error procesando el archivo: {e}")
        return None