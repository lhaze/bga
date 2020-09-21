from os import path

PROJECT_DIR = path.dirname(path.dirname(__file__))


def get_dir(*path_elements: str) -> str:
    return path.join(PROJECT_DIR, *path_elements)


def get_data_dir(*path_elements: str) -> str:
    return get_dir("data", *path_elements)
