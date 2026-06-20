import os
import base64
from flask import render_template, make_response, current_app
from xhtml2pdf import pisa
from io import BytesIO

from app.utils import get_student_data_from_db
from app.errors import api_error
from app.exports import exports_bp as exports

@exports.route("/exports/pdf/<string:identification>/<int:period_id>", methods=['GET','POST'])
def exports_student_pdf(identification, period_id):
    try:
        student_data = get_student_data_from_db(identification)

        if not student_data:
            return api_error("ESTUDIANTE_NO_ENCONTRADO", "Estudiante no encontrado", http_status=404)

        # Filtrar periodos para mostrar solo el solicitado
        if 'periodos' in student_data:
            student_data['periodos'] = [p for p in student_data['periodos'] if p['id'] == period_id]

        # Agregar fecha de emisión
        from datetime import datetime
        student_data['fecha_emision'] = datetime.now().strftime("%d/%m/%Y")

        directory_logo = 'logo-una.png'
        # root_path apunta a la carpeta "app", por lo que subimos un nivel para llegar a "static"
        logo_path = os.path.abspath(os.path.join(current_app.root_path, '..', 'static', 'img', directory_logo))
        
        with open(logo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        logo_uri = f'data:image/png;base64,{encoded_string}'

        html_content = render_template('academic-record.html', data=student_data, period_id=period_id, logo_uri=logo_uri)

        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html_content.encode('utf-8')), dest=pdf)

        if pisa_status.err:
            return api_error("ERROR_PDF", "No se pudo generar el PDF.", http_status=500)

        response = make_response(pdf.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=ficha_{identification}_{period_id}.pdf'
        return response

    except Exception as e:
        return api_error("ERROR_INTERNO", str(e), http_status=500)