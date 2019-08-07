from os import path

PACKAGE_DIR = path.dirname(__file__)
PROJECT_DIR = path.dirname(PACKAGE_DIR)


def get_dir(*path_elements: str) -> str:
    return path.join(PROJECT_DIR, *path_elements)


def get_data_dir(*path_elements: str) -> str:
    return get_dir('data', *path_elements)
