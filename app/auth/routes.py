import logging
import re
from datetime import datetime, timezone

from flask import request, current_app, g
from sqlalchemy.exc import SQLAlchemyError

from app.errors import api_error, api_success
from app.extensions import db
from app.auth import auth_bp as auth
from app.auth.jwt_utils import require_auth, require_role, current_user_id, current_user_has_role, _build_token, _decode_token
from .models.user import User
from .models.role import Role

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def _validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))


def _validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un número."
    return True, ""


###
#
# ✅ LOGIN — público
#
###
@auth.route("/auth/login", methods=['POST'])
def user_login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return api_error("CAMPO_REQUERIDO", "username y password son requeridos.")

    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return api_error("CREDENCIALES_INVALIDAS", "Credenciales inválidas.", http_status=401)

    user_payload = {
        'sub': user.id,
        'email': user.email,
        'firstname': user.firstname,
        'lastname': user.lastname,
        'roles': [role.name for role in user.roles],
    }
    token = _build_token(user_payload, 'access', current_app.config['JWT_EXP_HOURS'])
    refresh_token = _build_token(user_payload, 'refresh', current_app.config['JWT_REFRESH_EXP_HOURS'])

    return api_success(data={"token": token, "refresh_token": refresh_token}, mensaje="Login exitoso.")


###
#
# ✅ REFRESH TOKEN — público
#
###
@auth.route("/auth/refresh-token", methods=['POST'])
def token_refresh():
    data = request.get_json()
    if not data or not data.get('refresh_token'):
        return api_error("CAMPO_REQUERIDO", "El campo 'refresh_token' es requerido.", campo="refresh_token")

    payload, err = _decode_token(data['refresh_token'], expected_type='refresh')
    if err:
        return err

    user_payload = {k: payload[k] for k in ('sub', 'email', 'firstname', 'lastname', 'roles') if k in payload}
    token = _build_token(user_payload, 'access', current_app.config['JWT_EXP_HOURS'])
    refresh_token = _build_token(user_payload, 'refresh', current_app.config['JWT_REFRESH_EXP_HOURS'])

    return api_success(data={"token": token, "refresh_token": refresh_token}, mensaje="Token renovado exitosamente.")


###
#
# ✅ LOGOUT — requiere auth
#
###
@auth.route("/auth/logout", methods=['POST'])
@require_auth
def user_logout():
    from app.auth.models.revoked_token import RevokedToken
    jti = g.current_user.get('jti')
    if jti:
        RevokedToken.revoke(jti)
    return api_success(mensaje="Sesión cerrada correctamente.")


###
#
# ✅ CREATE NEW USER — Admin
#
###
@auth.route("/auth/user", methods=['POST'])
@require_role('Admin')
def user_create():
    data = request.get_json()
    if not data:
        return api_error("CUERPO_REQUERIDO", "El cuerpo de la solicitud es requerido.")

    required = ['firstname', 'lastname', 'username', 'email', 'password']
    for field in required:
        if not data.get(field):
            return api_error("CAMPO_REQUERIDO", f"El campo '{field}' es requerido.", campo=field)

    if not _validate_email(data['email']):
        return api_error("EMAIL_INVALIDO", "El formato del email no es válido.", campo="email")

    valid, msg = _validate_password(data['password'])
    if not valid:
        return api_error("PASSWORD_DEBIL", msg, campo="password")

    try:
        new_user = User(
            firstname=data['firstname'],
            lastname=data['lastname'],
            username=data['username'],
            email=data['email'],
            phone=data.get('phone'),
        )
        new_user.set_password(data['password'])

        viewer_role = Role.query.filter_by(name='Viewer').first()
        if viewer_role:
            new_user.add_role(viewer_role)

        db.session.add(new_user)
        db.session.commit()

        return api_success(data=new_user.to_dict(), mensaje="Usuario registrado correctamente.", http_status=201)

    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Error creating user")
        return api_error("ERROR_BASE_DATOS", "No se pudo crear el usuario. El username o email ya existe.", http_status=409)


###
#
# ✅ GET ALL USERS — Admin
#
###
@auth.route("/auth/user", methods=['GET'])
@require_role('Admin')
def user_get():
    users = db.session.execute(
        db.select(User).order_by(User.id.desc())
    ).scalars().all()

    if not users:
        return api_error("USUARIOS_NO_ENCONTRADOS", "No se encontraron usuarios registrados.", http_status=404)

    return api_success(data=[u.to_dict() for u in users], mensaje="Usuarios obtenidos correctamente.")


###
#
# ✅ GET USER BY ID — Admin o propio usuario
#
###
@auth.route("/auth/user/<int:user_id>", methods=['GET'])
@require_auth
def user_get_id(user_id):
    if not current_user_has_role('Admin') and current_user_id() != user_id:
        return api_error("ACCESO_DENEGADO", "Solo puedes consultar tu propio perfil.", http_status=403)

    user = db.session.get(User, user_id)
    if not user:
        return api_error("USUARIO_NO_ENCONTRADO", f"El usuario {user_id} no existe.", http_status=404)

    return api_success(data=user.to_dict(), mensaje="Usuario obtenido correctamente.")


###
#
# ✅ UPDATE USER — Admin o propio usuario
#
###
@auth.route("/auth/user/<int:user_id>", methods=['PUT'])
@require_auth
def user_update(user_id):
    if not current_user_has_role('Admin') and current_user_id() != user_id:
        return api_error("ACCESO_DENEGADO", "Solo puedes actualizar tu propio perfil.", http_status=403)

    user = db.session.get(User, user_id)
    if not user:
        return api_error("USUARIO_NO_ENCONTRADO", f"El usuario {user_id} no existe.", http_status=404)

    data = request.get_json()
    if not data:
        return api_error("CUERPO_REQUERIDO", "El cuerpo de la solicitud es requerido.")

    if 'email' in data and data['email']:
        if not _validate_email(data['email']):
            return api_error("EMAIL_INVALIDO", "El formato del email no es válido.", campo="email")

    if data.get('password'):
        valid, msg = _validate_password(data['password'])
        if not valid:
            return api_error("PASSWORD_DEBIL", msg, campo="password")

    updatable = ('firstname', 'lastname', 'email', 'phone')
    for field in updatable:
        if field in data and data[field] is not None:
            setattr(user, field, data[field])

    if data.get('password'):
        user.set_password(data['password'])

    user.modificated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
        return api_success(data=user.to_dict(), mensaje="Usuario actualizado correctamente.")
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Error updating user %d", user_id)
        return api_error("ERROR_BASE_DATOS", "No se pudo actualizar el usuario.", http_status=409)


###
#
# ✅ REMOVE USER — Admin
#
###
@auth.route("/auth/user/<int:user_id>", methods=['DELETE'])
@require_role('Admin')
def user_delete(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return api_error("USUARIO_NO_ENCONTRADO", f"El usuario {user_id} no existe.", http_status=404)

    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        return api_success(data={"id": user_id, "username": username}, mensaje="Usuario eliminado correctamente.")
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Error deleting user %d", user_id)
        return api_error("ERROR_BASE_DATOS", "No se pudo eliminar el usuario.", http_status=500)


###
#
# ✅ ASSIGN ROLE — Admin
#
###
@auth.route("/auth/user/<int:user_id>/role", methods=['POST'])
@require_role('Admin')
def user_assign_role(user_id):
    data = request.get_json()
    if not data or not data.get('role'):
        return api_error("CAMPO_REQUERIDO", "El campo 'role' es requerido.", campo="role")

    role_name = data.get('role', '').strip()
    if not role_name or len(role_name) > 100:
        return api_error("ROL_INVALIDO", "El campo 'role' es inválido.", campo="role")

    user = db.session.get(User, user_id)
    if not user:
        return api_error("USUARIO_NO_ENCONTRADO", f"El usuario {user_id} no existe.", http_status=404)

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return api_error("ROL_NO_ENCONTRADO", "El rol no existe.", http_status=404, campo="role")

    if user.has_role(role_name):
        return api_error("ROL_YA_ASIGNADO", "El usuario ya tiene ese rol.", http_status=409)

    try:
        user.add_role(role)
        db.session.commit()
        return api_success(data=user.to_dict(), mensaje="Rol asignado correctamente.", http_status=201)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Error assigning role to user %d", user_id)
        return api_error("ERROR_BASE_DATOS", "No se pudo asignar el rol.", http_status=500)


###
#
# ✅ REMOVE ROLE — Admin
#
###
@auth.route("/auth/user/<int:user_id>/role/<string:role_name>", methods=['DELETE'])
@require_role('Admin')
def user_remove_role(user_id, role_name):
    user = db.session.get(User, user_id)
    if not user:
        return api_error("USUARIO_NO_ENCONTRADO", f"El usuario {user_id} no existe.", http_status=404)

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return api_error("ROL_NO_ENCONTRADO", "El rol no existe.", http_status=404)

    if not user.has_role(role_name):
        return api_error("ROL_NO_ASIGNADO", "El usuario no tiene ese rol.", http_status=404)

    if role_name == 'Admin':
        admin_count = User.query.join(User.roles).filter(Role.name == 'Admin').count()
        if admin_count <= 1:
            return api_error(
                "OPERACION_NO_PERMITIDA",
                "No se puede remover el último administrador del sistema.",
                http_status=409,
            )

    try:
        user.roles.remove(role)
        db.session.commit()
        return api_success(data=user.to_dict(), mensaje="Rol eliminado correctamente.")
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Error removing role from user %d", user_id)
        return api_error("ERROR_BASE_DATOS", "No se pudo eliminar el rol.", http_status=500)
