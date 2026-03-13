from flask import jsonify, request
from app.reports import reports_bp as report

from app.utils import *

# ✅ CREATE
@report.route("/api/reports", methods=['POST'])
def report_add():
    return "ADD REPORT"

# ✅ READ
@report.route("/api/reports", methods=['GET'])
def reports_get():
    report_list = get_reports_list()
    # return "READ REPORTS"
    return jsonify({
        'name_files': report_list
    })

@report.route("/api/reports/<string:file_name>", methods=['GET', 'POST'])
def report_get(file_name):
    data = request.get_json()
    identification = data.get('identification')

    if not data:
        return jsonify({
            'error': "identification is needed."
        }), 400

    result = get_student_data(file_name, identification)
    
    if result:
        return jsonify({
            'result': result
        }), 200
    
    return jsonify({
        'error': "Student not found."
    }), 404

    # try:
    #     return jsonify({
    #         'identification': identification,
    #         'file': report
    #     })
    # except:
    #     pass

# ✅ UPDATE
@report.route("/api/reports/<string:file_name>", methods=['PUT'])
def report_update(file_name):
    pass

# ✅ DELETE
@report.route("/api/reports/<string:file_name>", methods=['DELETE'])
def report_delete(file_name):
    return "DEL REPORT"