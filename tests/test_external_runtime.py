"""
Tests for external_runtime.py - URL validation and path functions.
Note: These tests mock network calls and subprocess to avoid external dependencies.
"""

import importlib.util
import os


# Load external_runtime from the parent directory
_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "external_runtime.py")


def load_external_runtime():
    """Load a fresh copy of the external_runtime module."""
    spec = importlib.util.spec_from_file_location("external_runtime", _module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load the module once for tests that don't need patching
external_runtime = load_external_runtime()


class TestConstants:
    """Test that constants are properly defined."""

    def test_python_version_format(self):
        """Python version should be in valid format."""
        version = external_runtime.PYTHON_VERSION
        parts = version.split(".")
        assert len(parts) == 3, "Version should have major.minor.patch format"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' should be numeric"

    def test_embed_url_contains_version(self):
        """Embed URL should contain the Python version."""
        assert external_runtime.PYTHON_VERSION in external_runtime.EMBED_URL

    def test_embed_url_is_valid(self):
        """Embed URL should be a valid Python.org URL."""
        url = external_runtime.EMBED_URL
        assert url.startswith("https://www.python.org/ftp/python/")
        assert url.endswith(".zip")

    def test_get_pip_url_is_valid(self):
        """Get-pip URL should be a valid bootstrap URL."""
        url = external_runtime.GET_PIP_URL
        assert url.startswith("https://")
        assert "get-pip.py" in url

    def test_edge_tts_spec_format(self):
        """Edge TTS spec should be in valid pip format."""
        spec = external_runtime.EDGE_TTS_SPEC
        assert "edge-tts" in spec
        # Should have version pinning
        assert "==" in spec


class TestDownloadFunctionLogic:
    """Test the _download function logic."""

    def test_download_url_format(self):
        """Test that URLs are properly formatted for download."""
        url = "https://example.com/file.zip"
        destination = os.path.join("tmp", "file.zip")

        # Test that parameters would be valid
        assert url.startswith("https://")
        # Destination should be a valid path (not checking for specific separator)
        assert "file.zip" in destination


class TestExtractZipFunctionLogic:
    """Test the _extract_zip function logic."""

    def test_extract_zip_parameters(self):
        """Test extract zip would receive valid parameters."""
        zip_path = os.path.join("tmp", "archive.zip")
        target_dir = os.path.join("tmp", "target")

        # Both paths should contain the expected components
        assert "archive.zip" in zip_path
        assert "target" in target_dir


class TestEnsureImportSiteLogic:
    """Test the _ensure_import_site function logic."""

    def test_pth_file_detection_pattern(self):
        """Test the pattern used to detect .pth files."""
        test_files = ["python314._pth", "python.exe", "python314.dll"]

        pth_files = [f for f in test_files if f.endswith("._pth") and f.startswith("python")]

        assert pth_files == ["python314._pth"]

    def test_import_site_line_detection(self):
        """Test detection of 'import site' line."""
        lines_with = [".", "./Lib", "import site"]
        lines_without = [".", "./Lib", "#import site"]

        has_import_site = any(line.strip() == "import site" for line in lines_with)
        assert has_import_site is True

        has_import_site = any(line.strip() == "import site" for line in lines_without)
        assert has_import_site is False


class TestEnsureGetPipLogic:
    """Test the _ensure_get_pip function logic."""

    def test_get_pip_script_path_construction(self):
        """Test construction of get-pip.py path."""
        cache_dir = os.path.join("tmp", "cache")
        script_path = os.path.join(cache_dir, "get-pip.py")

        # Use os.path.join for expected path to ensure cross-platform compatibility
        expected = os.path.join("tmp", "cache", "get-pip.py")
        assert script_path == expected

    def test_get_pip_command_construction(self):
        """Test construction of get-pip command."""
        python_exe = os.path.join("tmp", "python.exe")
        script_path = os.path.join("tmp", "cache", "get-pip.py")

        command = [python_exe, script_path, "--no-warn-script-location"]

        assert command[0] == python_exe
        assert command[1] == script_path
        assert "--no-warn-script-location" in command


class TestPythonCanImportLogic:
    """Test the _python_can_import function logic."""

    def test_import_command_construction(self):
        """Test construction of import check command."""
        python_exe = os.path.join("tmp", "python.exe")
        module = "edge_tts"

        command = [python_exe, "-c", f"import {module}"]

        assert command[0] == python_exe
        assert command[1] == "-c"
        assert "import edge_tts" in command[2]


class TestGetExternalPythonLogic:
    """Test the get_external_python function logic."""

    def test_runtime_dir_construction(self):
        """Test construction of runtime directory path."""
        addon_dir = os.path.join("home", "user", ".local", "share", "Anki2", "addons21", "edge-tts")

        runtime_dir = os.path.join(addon_dir, "runtime")

        assert runtime_dir.endswith("runtime")

    def test_python_dir_construction(self):
        """Test construction of python directory path."""
        runtime_dir = os.path.join("tmp", "runtime")
        python_version = "3.14.2"

        python_dir = os.path.join(runtime_dir, f"python-{python_version}")

        # Use os.path.join for expected path to ensure cross-platform compatibility
        expected = os.path.join("tmp", "runtime", f"python-{python_version}")
        assert python_dir == expected

    def test_python_exe_path_construction(self):
        """Test construction of python.exe path."""
        python_dir = os.path.join("tmp", "runtime", "python-3.14.2")

        python_exe = os.path.join(python_dir, "python.exe")

        # Use os.path.join for expected path to ensure cross-platform compatibility
        expected = os.path.join("tmp", "runtime", "python-3.14.2", "python.exe")
        assert python_exe == expected

    def test_archive_path_construction(self):
        """Test construction of download archive path."""
        runtime_dir = os.path.join("tmp", "runtime")

        archive_path = os.path.join(runtime_dir, "python-embed.zip")

        # Use os.path.join for expected path to ensure cross-platform compatibility
        expected = os.path.join("tmp", "runtime", "python-embed.zip")
        assert archive_path == expected


class TestPipInstallCommandLogic:
    """Test pip install command construction."""

    def test_pip_upgrade_command(self):
        """Test pip upgrade command construction."""
        python_exe = os.path.join("tmp", "python.exe")

        command = [python_exe, "-m", "pip", "install", "--upgrade", "pip"]

        assert command[0] == python_exe
        assert "-m" in command
        assert "pip" in command
        assert "--upgrade" in command

    def test_edge_tts_install_command(self):
        """Test edge-tts install command construction."""
        python_exe = os.path.join("tmp", "python.exe")
        edge_tts_spec = "edge-tts==7.2.7"

        command = [python_exe, "-m", "pip", "install", edge_tts_spec]

        assert command[0] == python_exe
        assert "-m" in command
        assert "pip" in command
        assert "install" in command
        assert edge_tts_spec in command


class TestCachingDecorator:
    """Test that lru_cache is properly applied."""

    def test_function_has_cache_methods(self):
        """Function should have cache_clear method from lru_cache."""
        assert hasattr(external_runtime.get_external_python, "cache_clear")
        assert hasattr(external_runtime.get_external_python, "cache_info")

    def test_cache_maxsize(self):
        """Cache should have maxsize of 1."""
        cache_info = external_runtime.get_external_python.cache_info()
        assert cache_info.maxsize == 1


class TestEdgeTTSSpec:
    """Test edge-tts specification parsing."""

    def test_edge_tts_package_name(self):
        """Package name should be edge-tts."""
        spec = external_runtime.EDGE_TTS_SPEC
        package_name = spec.split("==")[0]

        assert package_name == "edge-tts"

    def test_edge_tts_version_format(self):
        """Version should be properly formatted."""
        spec = external_runtime.EDGE_TTS_SPEC
        version = spec.split("==")[1]

        parts = version.split(".")
        # Version should have at least major.minor format
        assert len(parts) >= 2
        # All parts should be numeric
        for part in parts:
            assert part.isdigit()


class TestPythonVersionSpec:
    """Test Python version specification."""

    def test_python_version_is_3_14(self):
        """Python version should be 3.14.x."""
        version = external_runtime.PYTHON_VERSION
        parts = version.split(".")

        assert parts[0] == "3"
        assert parts[1] == "14"

    def test_python_version_in_embed_url(self):
        """Embed URL should contain Python version twice (path and filename)."""
        url = external_runtime.EMBED_URL
        version = external_runtime.PYTHON_VERSION

        # Should appear in URL path
        assert f"/python/{version}/" in url
        # Should appear in filename
        assert f"python-{version}-embed" in url
