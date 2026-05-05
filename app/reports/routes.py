from flask import request, jsonify, current_app
from app.reports import reports_bp as report
import os

from app.reports.services import (
    get_reports_list,
    get_student_data_from_db,
    get_students_by_period,
    process_and_save_report,
    get_all_academic_periods,
)
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

###
#
# ✅ ADD NEW REPORT
#
###
@report.route("/api/v1/reports", methods=['POST'])
def report_add():
    # 1. Verify if the file is sended
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No se envió ningun archivo.'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Archivo no seleccionado.'}), 400
    
    # 2. Verify if the file extension is valid
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Formato no permitido. Solo se permiten archivos .rep'}), 400

    file.seek(0, os.SEEK_END) # Go to end archive
    file_length = file.tell() # Get size archive
    file.seek(0,0) # Back to start archive

    if file_length > current_app.config['MAX_FILE_SIZE']:
        return jsonify({'status': 'error', 'message': 'El archivo excede el tamaño máximo permitido.'}), 400

    # 4. Verify if the file is a valid report
    try:
        cabecera = file.read(256).decode('latin-1')
        file.seek(0, 0)
        if "UNIVERSIDAD NACIONAL ABIERTA" not in cabecera:
            return jsonify({'status': 'error', 'message': 'El archivo no es un archivo de reporte valido.'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'El archivo parece estar dañado o no es texto plano.'}), 400

    # 5. Save the file
    try:
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # DB BACKEND LOGIC
        exito = process_and_save_report(filename)

        if not exito:
            return jsonify({
                'status': 'error',
                'message': 'Error al guardar el archivo en la base de datos.'
                }), 500

        return jsonify({
            'status': 'success',
            'message': 'Archivo cargado, validado y guardado correctamente.',
            'filename': filename
            }), 200
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al guardar el archivo: {str(e)}'
            }), 500

###
#
# ⚠️⚠️⚠️ READ
#
###
@report.route("/api/v1/reports", methods=['GET'])
def reports_get():
    report_list = get_reports_list()
    return jsonify({
        'name_files': report_list
    })

###
#
# ⚠️⚠️⚠️ GET REPORT OF STUDENT BY IDENTIFICATION
#
###
# @report.route("/api/v1/reports/<string:file_name>", methods=['GET', 'POST'])
# def report_get(file_name):
#     data = request.get_json(silent=True) or {}
#     identification = data.get('identification') or request.args.get('identification')
#     mode = (data.get('mode') or request.args.get('mode') or 'exact').strip().lower()

#     if not identification:
#         return jsonify({
#             'error': "identification is needed."
#         }), 400

#     if mode not in {'exact', 'prefix'}:
#         return jsonify({
#             'error': "Invalid mode. Use 'exact' or 'prefix'."
#         }), 400

#     is_prefix_mode = mode == 'prefix'
#     result = get_student_data_from_db(
#         identification,
#         mode=mode
#     )

#     if result:
#         if is_prefix_mode:
#             return jsonify({
#                 'results': result,
#                 'count': len(result)
#             }), 200

#         return jsonify({
#             'result': result
#         }), 200
    
#     return jsonify({
#         'error': "Student not found.",
#         'mode': mode
#     }), 404


# ⚠️⚠️⚠️ UPDATE
# @report.route("/api/reports/<string:file_name>", methods=['PUT'])
# def report_update(file_name):
#     return jsonify({
#         'error': 'Not implemented in this demo.'
#     }), 501

#  ⚠️⚠️⚠️ DELETE
# @report.route("/api/reports/<string:file_name>", methods=['DELETE'])
# def report_delete(file_name):
#     return "DEL REPORT"

###
#
# ✅ ALL ACADEMIC PERIODS LIST [Home Dashboard]
#
###
@report.route("/api/v1/academic-periods", methods=['GET'])
def academic_periods_get():
    # Import inside the function or file level, we can import from app.utils
    from app.utils import get_all_academic_periods
    
    try:
        academic_periods = get_all_academic_periods()
        return jsonify({
            'status': 'success',
            'message': 'Academic periods list.',
            'data': {
                'academic_periods': academic_periods
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al obtener los periodos académicos: {str(e)}'
        }), 500

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
        return jsonify({'status': 'error', 'message': "'init' debe ser un entero >= 0."}), 400

    try:
        limit = int(raw_limit)
        if not (1 <= limit <= 100):
            raise ValueError
    except ValueError:
        return jsonify({'status': 'error', 'message': "'limit' debe ser un entero entre 1 y 100."}), 400

    valid_orders = {'cedula', 'nombre', 'carrera'}
    if raw_order not in valid_orders:
        return jsonify({'status': 'error', 'message': f"'order' debe ser uno de: {', '.join(sorted(valid_orders))}."}), 400

    ascending = raw_asc.lower() != 'false'

    result = get_students_by_period(period_code, init, limit, raw_order, ascending, carrera, nombre)

    if result is None:
        return jsonify({'status': 'error', 'message': f"Período académico '{period_code}' no encontrado."}), 404

    return jsonify({'status': 'success', 'message': 'Students list.', 'data': result}), 200


###
#
# ✅ STUDENT SEARCH BY IDENTIFICATION [Home Dashboard]
#
###
@report.route("/api/v1/students/<string:identification>", methods=['GET'])
def student_search(identification):
    period_filter = request.args.get('period')
    result = get_student_data_from_db(identification, period_filter=period_filter)

    if result:
        return jsonify(
            {
                'status': 'success',
                'message': 'Student found.',
                'data': result
            }), 200
    
    return jsonify({
        'status': 'error',
        'message': 'Student not found.'
    }), 404