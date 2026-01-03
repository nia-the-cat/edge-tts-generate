import hashlib
import os
import subprocess
import sys
import urllib.request
import zipfile
from functools import lru_cache


PYTHON_VERSION = "3.14.2"
EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
EDGE_TTS_SPEC = "edge-tts==7.2.7"

EXPECTED_HASHES = {
    EMBED_URL: "fefdb4dddb2f7851bc1e87f4b0fbdf651ae0d3b62f6133b17012d10325e4a49a",
    GET_PIP_URL: "1c3f1ab6f6b0c8ad4e4f4148e90fd89a3248dbe4a564c39b2971f91e78f7a9b9",
}


def _get_subprocess_flags():
    """Get subprocess creation flags to hide console windows on Windows."""
    if sys.platform == "win32":
        # On Windows, use CREATE_NO_WINDOW flag to prevent console window from appearing
        # This is equivalent to the old STARTF_USESHOWWINDOW with SW_HIDE
        # CREATE_NO_WINDOW = 0x08000000
        return {"creationflags": 0x08000000}
    return {}


def _download(url: str, destination: str, *, expected_hash: str | None = None, retries: int = 3, timeout: int = 30) -> None:
    for attempt in range(1, retries + 1):
        try:
            if os.path.exists(destination):
                os.remove(destination)
            with urllib.request.urlopen(url, timeout=timeout) as response, open(destination, "wb") as target:
                digest = hashlib.sha256()
                for chunk in iter(lambda: response.read(8192), b""):
                    target.write(chunk)
                    digest.update(chunk)
            actual_hash = digest.hexdigest()
            if expected_hash is not None and actual_hash != expected_hash:
                os.remove(destination)
                raise ValueError(
                    "Downloaded file hash did not match expected value. "
                    f"Expected {expected_hash} but got {actual_hash}. "
                    "The download may be corrupted or tampered with."
                )
            return
        except Exception as exc:  # noqa: BLE001 - we want to handle all errors for retries
            if attempt == retries:
                raise RuntimeError(f"Failed to download {url} after {retries} attempts") from exc
            # Remove partially downloaded files before retrying to avoid caching corrupt data
            if os.path.exists(destination):
                os.remove(destination)


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
        _download(GET_PIP_URL, script_path, expected_hash=EXPECTED_HASHES[GET_PIP_URL])
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
        _download(EMBED_URL, archive_path, expected_hash=EXPECTED_HASHES[EMBED_URL])
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
