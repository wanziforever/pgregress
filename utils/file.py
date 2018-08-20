"""all file or directory related util functions
"""
import os

def create_directory(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def create_directory_for_file(filepath):
    dirpath = os.path.dirname(filepath)
    create_directory(dirpath)

def get_file_name_from_path(path):
    return os.path.basename(path)
