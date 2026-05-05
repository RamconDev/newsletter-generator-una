import logging
import os

from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.errors import api_error, api_success
from app.reports import reports_bp as report
from app.reports.services import (
    get_reports_list,
    get_student_data_from_db,
    get_students_by_period,
    process_and_save_report,
    get_all_academic_periods,
)

logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


###
#
# ✅ ADD NEW REPORT
#
###
@report.route("/api/v1/reports", methods=['POST'])
def report_add():
    if 'file' not in request.files:
        return api_error("ARCHIVO_NO_ENVIADO", "No se envió ningún archivo.", campo="file")

    file = request.files['file']

    if file.filename == '':
        return api_error("ARCHIVO_NO_SELECCIONADO", "Archivo no seleccionado.", campo="file")

    if not allowed_file(file.filename):
        return api_error("FORMATO_INVALIDO", "Solo se permiten archivos .rep", campo="file")

    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0, 0)

    if file_length > current_app.config['MAX_FILE_SIZE']:
        return api_error("ARCHIVO_MUY_GRANDE", "El archivo excede el tamaño máximo permitido.", campo="file")

    try:
        cabecera = file.read(256).decode('latin-1')
        file.seek(0, 0)
        if "UNIVERSIDAD NACIONAL ABIERTA" not in cabecera:
            return api_error("ARCHIVO_INVALIDO", "El archivo no es un reporte UNA válido.", campo="file")
    except UnicodeDecodeError:
        return api_error("ARCHIVO_CORRUPTO", "El archivo parece estar dañado o no es texto plano.", campo="file")

    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(save_path)
    except OSError:
        logger.exception("Error saving uploaded file: %s", filename)
        return api_error("ERROR_GUARDADO", "No se pudo guardar el archivo en disco.", http_status=500)

    exito = process_and_save_report(filename)

    if not exito:
        try:
            os.remove(save_path)
        except OSError:
            logger.warning("Could not remove orphaned file after failed processing: %s", save_path)
        return api_error("ERROR_PROCESAMIENTO", "Error al procesar el reporte en la base de datos.", http_status=500)

    return api_success(
        data={"filename": filename},
        mensaje="Archivo cargado, validado y guardado correctamente.",
        http_status=200,
    )


###
#
# ✅ LIST REPORTS
#
###
@report.route("/api/v1/reports", methods=['GET'])
def reports_get():
    return api_success(data={"files": get_reports_list()}, mensaje="Listado de reportes.")


###
#
# ✅ ALL ACADEMIC PERIODS LIST
#
###
@report.route("/api/v1/academic-periods", methods=['GET'])
def academic_periods_get():
    try:
        periods = get_all_academic_periods()
        return api_success(data={"academic_periods": periods}, mensaje="Períodos académicos.")
    except Exception:
        logger.exception("Error fetching academic periods")
        return api_error("ERROR_INTERNO", "Error al obtener los períodos académicos.", http_status=500)


###
#
# ✅ STUDENTS BY ACADEMIC PERIOD (paginated, filtered, ordered)
#
###
@report.route("/api/v1/academic-periods/<string:period_code>/students", methods=['GET'])
def students_by_period(period_code):
    raw_init  = request.args.get('init',  '0')
    raw_limit = request.args.get('limit', '20')
    raw_order = request.args.get('order', 'nombre')
    raw_asc   = request.args.get('asc',   'true')
    carrera   = request.args.get('carrera') or None
    nombre    = request.args.get('nombre')  or None

    try:
        init = int(raw_init)
        if init < 0:
            raise ValueError
    except ValueError:
        return api_error("PARAM_INVALIDO", "'init' debe ser un entero >= 0.", campo="init")

    try:
        limit = int(raw_limit)
        if not (1 <= limit <= 100):
            raise ValueError
    except ValueError:
        return api_error("PARAM_INVALIDO", "'limit' debe ser un entero entre 1 y 100.", campo="limit")

    valid_orders = {'cedula', 'nombre', 'carrera'}
    if raw_order not in valid_orders:
        return api_error(
            "PARAM_INVALIDO",
            f"'order' debe ser uno de: {', '.join(sorted(valid_orders))}.",
            campo="order",
        )

    ascending = raw_asc.lower() != 'false'
    result = get_students_by_period(period_code, init, limit, raw_order, ascending, carrera, nombre)

    if result is None:
        return api_error("PERIODO_NO_ENCONTRADO", f"Período académico '{period_code}' no encontrado.", http_status=404)

    return api_success(data=result, mensaje="Listado de estudiantes.")


###
#
# ✅ STUDENT SEARCH BY IDENTIFICATION
#
###
@report.route("/api/v1/students/<string:identification>", methods=['GET'])
def student_search(identification):
    period_filter = request.args.get('period')
    result = get_student_data_from_db(identification, period_filter=period_filter)

    if result:
        return api_success(data=result, mensaje="Estudiante encontrado.")

    return api_error("ESTUDIANTE_NO_ENCONTRADO", "Estudiante no encontrado.", http_status=404)
