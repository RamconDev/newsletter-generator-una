from pathlib import Path

import os
from pathlib import Path
from flask import current_app
from werkzeug.utils import secure_filename

def get_path_data():
    directory = Path(current_app.root_path) / '../data'
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def get_reports_list():
    try:
        directory = get_path_data()
        print(f"✅ Searching files in: {directory}")

        archives_list = [archive.name for archive in directory.iterdir() if archive.is_file()]

        print(f"✅ Files found: { archives_list }")

        return archives_list
    except Exception as e:
        print(f"✅ Error: {e}")
        return ['Nothing']
    
def get_report(file_name, encoding="utf-8"):
    path = get_path_data()
    print(f"✅ {path}")
    try:
        if not path.exists():
            print("✅ The file doesn't exists.")
            return None
        if not path.is_file():
            print("✅ The path doesn't lead to a valid file.")
            return None
        
        content = path.read_text(encoding=encoding)
        return path
    except:
        pass
    
def add_report_to_list(archive):
    if archive:
        secure_name = secure_filename(archive.filename)
        save_directory = get_path_data() / secure_name
        archive.save(str(save_directory))
        return True
    return False

def delete_report(filename):
    file_directory = get_path_data / secure_filename(filename)
    if file_directory.exists():
        os.remove(file_directory)
        return True
    return False