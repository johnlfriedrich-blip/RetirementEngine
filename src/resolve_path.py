from pathlib import Path


def get_project_root() -> Path:
    """Resolves the project root directory.

    This function assumes that the script is located within the project structure
    and ascends the directory tree to find a marker file or directory
    (e.g., .git, pyproject.toml) that indicates the project root.

    Returns:
        Path: The absolute path to the project root.
    """
    # Start from the directory of the current file
    current_path = Path(__file__).resolve().parent
    # Ascend until a project marker is found
    while (
        not (current_path / ".git").exists()
        and not (current_path / "pyproject.toml").exists()
    ):
        if current_path.parent == current_path:
            # Reached the filesystem root without finding the marker
            raise FileNotFoundError("Project root not found.")
        current_path = current_path.parent
    return current_path


def resolve_path(relative_path: str) -> str:
    """Resolves a relative path to an absolute path from the project root.

    Args:
        relative_path (str): The relative path to resolve.

    Returns:
        str: The absolute path.
    """
    project_root = get_project_root()
    return str(project_root / relative_path)
