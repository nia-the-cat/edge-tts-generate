import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from functools import lru_cache


PYTHON_VERSION = "3.14.2"
EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
EDGE_TTS_SPEC = "edge-tts==7.2.7"


def _get_subprocess_flags():
    """Get subprocess creation flags to hide console windows on Windows."""
    if sys.platform == "win32":
        # On Windows, use CREATE_NO_WINDOW flag to prevent console window from appearing
        # This is equivalent to the old STARTF_USESHOWWINDOW with SW_HIDE
        # CREATE_NO_WINDOW = 0x08000000
        return {"creationflags": 0x08000000}
    return {}


def _download(url: str, destination: str) -> None:
    with urllib.request.urlopen(url) as response, open(destination, "wb") as target:
        shutil.copyfileobj(response, target)


def _extract_zip(zip_path: str, target_dir: str) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(target_dir)


def _ensure_import_site(python_dir: str) -> None:
    pth_files = [file for file in os.listdir(python_dir) if file.endswith("._pth") and file.startswith("python")]
    for pth_name in pth_files:
        pth_path = os.path.join(python_dir, pth_name)
        with open(pth_path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        if any(line.strip() == "import site" for line in lines):
            continue
        lines.append("import site")
        with open(pth_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))


def _ensure_get_pip(python_exe: str, cache_dir: str) -> str:
    script_path = os.path.join(cache_dir, "get-pip.py")
    if not os.path.exists(script_path):
        _download(GET_PIP_URL, script_path)
    subprocess.run(
        [python_exe, script_path, "--no-warn-script-location"],
        check=True,
        capture_output=True,
        **_get_subprocess_flags(),
    )
    return script_path


def _python_can_import(python_exe: str, module: str) -> bool:
    try:
        subprocess.run(
            [python_exe, "-c", f"import {module}"],
            check=True,
            capture_output=True,
            **_get_subprocess_flags(),
        )
        return True
    except subprocess.CalledProcessError:
        return False


@lru_cache(maxsize=1)
def get_external_python(addon_dir: str) -> str:
    runtime_dir = os.path.join(addon_dir, "runtime")
    python_dir = os.path.join(runtime_dir, f"python-{PYTHON_VERSION}")
    python_exe = os.path.join(python_dir, "python.exe")
    os.makedirs(runtime_dir, exist_ok=True)

    if not os.path.exists(python_exe):
        archive_path = os.path.join(runtime_dir, "python-embed.zip")
        _download(EMBED_URL, archive_path)
        _extract_zip(archive_path, python_dir)
        _ensure_import_site(python_dir)

    if not _python_can_import(python_exe, "pip"):
        _ensure_get_pip(python_exe, runtime_dir)
        subprocess.run(
            [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            **_get_subprocess_flags(),
        )

    if not _python_can_import(python_exe, "edge_tts"):
        subprocess.run(
            [python_exe, "-m", "pip", "install", EDGE_TTS_SPEC],
            check=True,
            capture_output=True,
            **_get_subprocess_flags(),
        )

    return python_exe
