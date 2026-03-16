from flask import jsonify, request
from app.reports import reports_bp as report

from app.utils import get_reports_list, get_student_data

# CREATE
@report.route("/api/reports", methods=['POST'])
def report_add():
    return "ADD REPORT"

# READ
@report.route("/api/reports", methods=['GET'])
def reports_get():
    report_list = get_reports_list()
    return jsonify({
        'name_files': report_list
    })

@report.route("/api/reports/<string:file_name>", methods=['GET', 'POST'])
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