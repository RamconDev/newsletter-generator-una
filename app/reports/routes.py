from flask import request, jsonify, current_app
from app.reports import reports_bp as report
import os

from app.utils import get_reports_list, get_student_data
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'rep'}
MAX_FILE_SIZE = 5 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    if file_length > MAX_FILE_SIZE:
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

        return jsonify({
            'status': 'success',
            'message': 'Archivo cargado y validado correctamente.',
            'filename': filename
            }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al guardar el archivo: {str(e)}'
            }), 500

###
#
# ✅ READ
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
# ✅ GET REPORT BY NAME
#
###
@report.route("/api/v1/reports/<string:file_name>", methods=['GET', 'POST'])
def report_get(file_name):
    data = request.get_json(silent=True) or {}
    identification = data.get('identification') or request.args.get('identification')
    mode = (data.get('mode') or request.args.get('mode') or 'exact').strip().lower()

    if not identification:
        return jsonify({
            'error': "identification is needed."
        }), 400

    if mode not in {'exact', 'prefix'}:
        return jsonify({
            'error': "Invalid mode. Use 'exact' or 'prefix'."
        }), 400

    is_prefix_mode = mode == 'prefix'
    result = get_student_data(
        file_name,
        identification,
        mode=mode,
        return_all=is_prefix_mode
    )

    if result:
        if is_prefix_mode:
            return jsonify({
                'results': result,
                'count': len(result)
            }), 200

        return jsonify({
            'result': result
        }), 200
    
    return jsonify({
        'error': "Student not found.",
        'mode': mode
    }), 404


# UPDATE
@report.route("/api/reports/<string:file_name>", methods=['PUT'])
def report_update(file_name):
    return jsonify({
        'error': 'Not implemented in this demo.'
    }), 501

# DELETE
@report.route("/api/reports/<string:file_name>", methods=['DELETE'])
def report_delete(file_name):
    return "DEL REPORT"