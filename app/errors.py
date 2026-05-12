import logging
from flask import jsonify, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def api_error(codigo: str, descripcion: str, campo: str = None, http_status: int = 400):
    entry = {"codigo": codigo, "descripcion": descripcion}
    if campo is not None:
        entry["campo"] = campo
    return jsonify({"error": [entry]}), http_status


def api_errors(errors: list[dict], http_status: int = 400):
    return jsonify({"error": errors}), http_status


def api_success(data=None, mensaje: str = "OK", http_status: int = 200):
    body = {"data": data} if data is not None else {}
    return jsonify(body), http_status


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return api_error("BAD_REQUEST", "Solicitud inválida o JSON malformado.", http_status=400)

    @app.errorhandler(401)
    def unauthorized(e):
        return api_error("NO_AUTORIZADO", "Autenticación requerida.", http_status=401)

    @app.errorhandler(403)
    def forbidden(e):
        return api_error("ACCESO_DENEGADO", "No tienes permiso para acceder a este recurso.", http_status=403)

    @app.errorhandler(404)
    def not_found(e):
        return api_error("NOT_FOUND", "Recurso no encontrado.", http_status=404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return api_error("METHOD_NOT_ALLOWED", "Método no permitido.", http_status=405)

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return api_error("ARCHIVO_MUY_GRANDE", "El archivo excede el tamaño máximo permitido.", http_status=413)

    @app.errorhandler(422)
    def unprocessable_entity(e):
        return api_error("DATOS_INVALIDOS", "Los datos enviados no pudieron ser procesados.", http_status=422)

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Error interno no manejado")
        return api_error("ERROR_INTERNO", "Error interno del servidor.", http_status=500)

    @app.errorhandler(HTTPException)
    def http_exception(e):
        logger.warning("HTTPException no mapeada: %d %s", e.code, e.name)
        return api_error("HTTP_ERROR", "Error en la solicitud.", http_status=e.code)

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        logger.exception("Excepción no controlada: %s", type(e).__name__)
        return api_error("ERROR_INTERNO", "Error interno del servidor.", http_status=500)
