from flask import request, jsonify
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.auth import auth_bp as auth

from sqlalchemy.exc import SQLAlchemyError

from .models.user import User
from .models.role import Role
##
#
#
#
##
@auth.route("/auth")
def login():
    return "Login Authentication Test"

###
#
# ✅ CREATE NEW USER
#
###
@auth.route("/api/v1/auth/user", methods=['POST'])
def user_create():
    data = request.get_json()

    if not data:
        return jsonify({
            'error': 'not data recived'
        }), 400
    
    try:
        new_user = User(
            firstname = data.get('firstname'),
            lastname = data.get('lastname'),
            username = data.get('username'),
            email = data.get('email'),
            phone = data.get('phone')
        )
        new_user.set_password(data.get('password'))

        viewer_role = Role.query.filter_by(name='Viewer').first()
        if viewer_role:
            new_user.add_role(viewer_role)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': 'registered successfully',
            'data': new_user.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'error': 'database error',
            'details': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'exception error',
            'details': str(e)
        }), 400
   
###
#
# ✅ GET ALL USERS
#
### 
@auth.route("/api/v1/auth/user", methods=['GET'])
def user_get():
    users_list = db.session.execute(
        db.select(User).order_by(User.id.desc())
    ).scalars().all()

    results = [user.to_dict() for user in users_list]

    if not results:
        return jsonify({
            'status': 'error',
            'message': 'No se encontraron usuarios registrados.'
        }), 404

    return jsonify({
        'status': 'success',
        'message': 'Usuarios obtenidos correctamente.',
        'data': results
    }), 200
   
###
#
# ✅ GET USER BY ID
#
###

@auth.route("/api/v1/auth/user/<int:user_id>", methods=['GET'])
def user_get_id(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            'status': 'error',
            'message': f"usuario id {user_id} no existe."
        }), 404

    return jsonify({
        'status': 'success',
        'message': 'Usuario obtenido correctamente.',
        'data': user.to_dict()
    }), 200

###
#
# ✅ UPDATE USER
#
###
@auth.route("/api/v1/auth/user/<int:user_id>", methods=['PUT'])
def user_update(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            'status': 'error',
            'message': f"usuario id {user_id} no existe."
        }), 404
    
    try:
        pass
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error de base de datos.',
            'details': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error inesperado.',
            'details': str(e)
        }), 400


###
#
# ✅ REMOVE USER
#
###
@auth.route("/api/v1/auth/user/<int:user_id>", methods=['DELETE'])
def user_delete(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            'status': 'error',
            'message': f"usuario id {user_id} no existe."
        }), 404
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Usuario eliminado correctamente.',
            'data': {
               'id': user_id,
               'username': username
            }
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error de base de datos.',
            'details': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error inesperado.',
            'details': str(e)
        }), 400

###
#
# ✅ ASSING ROLE
#
###
@auth.route("/api/v1/auth/user/<int:user_id>/role", methods=['POST'])
def user_assign_role(user_id):
    data = request.get_json()
    if not data or not data.get('role'):
        return jsonify({
            'status': 'error',
            'message': 'El rol es requerido.'
        }), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            'status': 'error',
            'message': f"usuario id {user_id} no existe."
        }), 404

    role_name = data.get('role')
    role = Role.query.filter_by(name=role_name).first()

    if not role:
        return jsonify({
            'status': 'error',
            'message': f"Rol '{role_name}' no existe."
        }), 404

    if user.has_role(role_name):
        return jsonify({
            'status': 'error',
            'message': f"El usuario ya tiene el rol '{role_name}'."
        }), 200

    try:
        user.add_role(role)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Rol asignado correctamente.',
            'data': user.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error de base de datos.',
            'details': str(e)
        }), 400

###
#
# ✅ REMOVE ROLE
#
###
@auth.route("/api/v1/auth/user/<int:user_id>/role/<string:role_name>", methods=['DELETE'])
def user_remove_role(user_id, role_name):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            'status': 'error',
            'message': f"usuario id {user_id} no existe."
        }), 404

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({
            'status': 'error',
            'message': f"Rol '{role_name}' no existe."
        }), 404

    if not user.has_role(role_name):
        return jsonify({
            'status': 'error',
            'message': f"El usuario no tiene el rol '{role_name}'."
        }), 200

    try:
        user.roles.remove(role)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Rol eliminado correctamente.',
            'data': user.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error de base de datos.',
            'details': str(e)
        }), 400