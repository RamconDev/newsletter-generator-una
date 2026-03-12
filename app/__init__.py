from flask import Flask

from .utils import get_reports_list

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        files_reports = get_reports_list()
        return f"Initialiced App!"
    
    return app

def read_reports():
    pass