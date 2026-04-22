from flask import Flask

from .utils import get_reports_list

from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    CORS(app)

    app.config['UPLOAD_FOLDER'] = 'data'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

    from .blueprints import register_blueprints

    register_blueprints(app)
    
    @app.route("/")
    def index():
        files_reports = get_reports_list()
        return f"Initialiced App! { files_reports }"
    
    return app

def read_reports():
    pass