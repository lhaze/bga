from pathlib import Path
import typing as t

from pca.utils.os import read_from_file


def get_data_dirs() -> t.Tuple[Path, ...]:
    try:
        import bgap
    except ImportError:
        bgap = None
    directories = (Path(__file__).parent / "../../data",)
    if bgap:
        directories += (Path(bgap.__file__).parent / "../data",)
    return tuple(d.resolve() for d in directories if d.exists())


def load_data(file_name: str, encoding: str = "utf-8", errors: str = "replace") -> str:
    data_dirs = get_data_dirs()
    for data_dir in data_dirs:
        try:
            return read_from_file(data_dir / file_name, encoding=encoding, errors=errors)
        except OSError:
            pass
    raise ValueError(f"File '{file_name}' not found in {[str(d) for d in data_dirs]}")


def get_data_filepath(filename: str) -> Path:
    return (Path(__file__) / "../../data" / filename).resolve()
