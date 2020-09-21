from pathlib import Path

from pca.utils.os import read_from_file

import bgap

DATA_DIRS = (d.resolve() for d in (
    Path(__file__) / '../../data',
    Path(bgap.__file__) / '../../data',
))
DATA_DIRS = tuple(d for d in DATA_DIRS if d.exists())


def load_data(file_name: str, encoding: str = 'utf-8', errors: str = 'replace') -> str:
    for data_dir in DATA_DIRS:
        try:
            return read_from_file(data_dir / file_name, encoding=encoding, errors=errors)
        except OSError:
            pass
    raise ValueError(f"File '{file_name}' not found in {[str(d) for d in DATA_DIRS]}")
