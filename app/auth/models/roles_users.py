from app import db

# class RolesUsers(db.Table):
#     __tablename__ = 'roles_users'

#     user_id = db.Column('user_id', db.Integer(), db.ForeignKey('users.id'), ondelete='CASCADE')
#     role_id = db.Column('role_id', db.Integer(), db.ForeignKey('roles.id'), ondelete='CASCADE')

roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'))
)