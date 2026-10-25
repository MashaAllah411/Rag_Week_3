"""Tests for the self-bootstrapping launcher (run.py): fingerprinting, .env handling, dependency sync."""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("launcher_under_test", ROOT / "run.py")
launcher = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(launcher)


def _names(lines):
    out = set()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.add(re.split(r"[\[<>=!~ ;]", line.strip().strip('",'), maxsplit=1)[0].lower().replace("_", "-"))
    return out


def test_requirements_and_pyproject_declare_the_same_runtime_packages():
    """run.py installs from requirements.txt; pyproject.toml must not drift from it."""
    reqs = _names((ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines())
    reqs -= {"pytest", "reportlab"}                      # dev-only entries
    block = re.search(r"dependencies = \[(.*?)\n\]", (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.S).group(1)
    assert reqs == _names(block.splitlines())


def test_every_required_module_belongs_to_a_declared_package():
    declared = _names((ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines())
    to_package = {"multipart": "python-multipart", "dotenv": "python-dotenv", "PIL": "pillow",
                  "rank_bm25": "rank-bm25", "sentence_transformers": "sentence-transformers",
                  "opentelemetry.sdk": "opentelemetry-sdk"}
    for module in launcher.REQUIRED_MODULES:
        package = to_package.get(module, module.replace("_", "-")).lower()
        assert package in declared, f"{module} -> {package} not in requirements.txt"


def test_fingerprint_changes_when_requirements_change(tmp_path, monkeypatch):
    req = tmp_path / "requirements.txt"
    req.write_text("fastapi\n", encoding="utf-8")
    monkeypatch.setattr(launcher, "REQUIREMENTS", req)
    monkeypatch.setattr(launcher, "PYPROJECT", tmp_path / "missing.toml")
    first = launcher._dependency_fingerprint()
    assert first == launcher._dependency_fingerprint()   # stable when nothing changes
    req.write_text("fastapi\nstreamlit\n", encoding="utf-8")
    assert launcher._dependency_fingerprint() != first


def test_missing_modules_reports_what_is_absent(monkeypatch):
    monkeypatch.setattr(launcher, "REQUIRED_MODULES", ["json", "definitely_not_installed_pkg"])
    assert launcher._missing_modules() == ["definitely_not_installed_pkg"]


def _point_env(monkeypatch, tmp_path, example_text):
    example, env = tmp_path / ".env.example", tmp_path / ".env"
    example.write_text(example_text, encoding="utf-8")
    monkeypatch.setattr(launcher, "ENV_EXAMPLE", example)
    monkeypatch.setattr(launcher, "ENV_FILE", env)
    return env


def test_env_is_created_from_template_and_no_required_keys_means_no_stop(tmp_path, monkeypatch, capsys):
    env = _point_env(monkeypatch, tmp_path, "# plain\nPORT=8000\n")
    launcher.ensure_env_file()
    assert env.exists() and "PORT=8000" in env.read_text(encoding="utf-8")


def test_launcher_stops_and_lists_required_keys_that_are_empty(tmp_path, monkeypatch, capsys):
    env = _point_env(monkeypatch, tmp_path, "# [required] get one from the vendor\nSERVICE_KEY=\nOTHER=1\n")
    with pytest.raises(SystemExit) as stop:
        launcher.ensure_env_file()
    assert stop.value.code == 2
    assert "SERVICE_KEY" in capsys.readouterr().out and env.exists()


def test_launcher_continues_once_required_keys_are_filled(tmp_path, monkeypatch):
    env = _point_env(monkeypatch, tmp_path, "# [required]\nSERVICE_KEY=\n")
    env.write_text("SERVICE_KEY=abc123\n", encoding="utf-8")
    launcher.ensure_env_file()                            # must not exit


def test_shipped_env_example_requires_no_secrets():
    assert launcher._required_env_keys() == []


def test_children_get_src_and_repo_root_on_pythonpath():
    paths = launcher.child_env()["PYTHONPATH"].split(launcher.os.pathsep)
    assert str(ROOT / "src") in paths and str(ROOT) in paths


def test_api_binds_to_localhost_by_default():
    source = (ROOT / "run.py").read_text(encoding="utf-8")
    assert 'os.getenv("BACKEND_HOST", "127.0.0.1")' in source and '"0.0.0.0"' not in source
