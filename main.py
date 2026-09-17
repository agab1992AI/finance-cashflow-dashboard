import importlib.util
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"


def ensure_runtime():
    if importlib.util.find_spec("customtkinter") is not None:
        return

    if not VENV_DIR.exists():
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    if os.name == "nt":
        python_executable = VENV_DIR / "Scripts" / "python.exe"
        pip_executable = VENV_DIR / "Scripts" / "pip.exe"
    else:
        python_executable = VENV_DIR / "bin" / "python"
        pip_executable = VENV_DIR / "bin" / "pip"

    if not python_executable.exists() or not pip_executable.exists():
        raise RuntimeError("Unable to create the project virtual environment.")

    subprocess.run([str(python_executable), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
    os.execv(str(python_executable), [str(python_executable), str(PROJECT_ROOT / "main.py")])


if __name__ == "__main__":
    ensure_runtime()

    from app.dashboard import DashboardApp

    app = DashboardApp()
    app.run()
