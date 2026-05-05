import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def api_error(codigo: str, descripcion: str, campo: str = None, http_status: int = 400):
    body = {"codigo": codigo, "descripcion": descripcion}
    if campo is not None:
        body["campo"] = campo
    return jsonify(body), http_status


def api_success(data=None, mensaje: str = "OK", http_status: int = 200):
    body = {"status": "success", "mensaje": mensaje}
    if data is not None:
        body["data"] = data
    return jsonify(body), http_status


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return api_error("NOT_FOUND", "Recurso no encontrado.", http_status=404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return api_error("METHOD_NOT_ALLOWED", "Método no permitido.", http_status=405)

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return api_error("ARCHIVO_MUY_GRANDE", "El archivo excede el tamaño máximo permitido.", http_status=413)

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Error interno no manejado")
        return api_error("ERROR_INTERNO", "Error interno del servidor.", http_status=500)
