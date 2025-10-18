# retirement_engine/resolve_path.py

import platform
from pathlib import Path


def resolve_path(relative_path):
    """
    Resolves a file path across WSL and Windows environments.
    Accepts a relative path like 'data/market.csv' and returns an absolute path.
    """
    base = Path(__file__).resolve().parent.parent  # go up to project root
    full_path = base / relative_path

    if platform.system() == "Linux" and "microsoft" in platform.release().lower():
        return str(full_path)
    elif platform.system() == "Windows":
        return str(full_path)
    else:
        raise EnvironmentError("Unsupported platform")
