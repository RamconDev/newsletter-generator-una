def register_blueprints(app):
    from app.reports import reports_bp
    app.register_blueprint(reports_bp)
    
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)