import json
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError

import pytest
import yaml
from pytest_mock import MockerFixture

from prepare_gitignore_builder.main import main, get_cache_path

TASK = Path(__file__).parent.parent / "task.yml"
BASE_URL = "https://raw.githubusercontent.com/github/gitignore/main"
TEMPLATES = {
    "Java": "*.class\n*.jar\n",
    "Global/JetBrains": ".idea/\n*.iml\n",
}


def set_inputs(monkeypatch: pytest.MonkeyPatch, **inputs: Any) -> None:
    """
    Pass the inputs like prepare-assignment core does: as JSON in PREPARE_<NAME> environment variables,
    including the defaults from task.yml. Use the names from task.yml, with '_' for '-'.
    """
    definition: Dict[str, Any] = yaml.safe_load(TASK.read_text(encoding="utf-8"))["inputs"]
    values = {name: spec["default"] for name, spec in definition.items() if "default" in spec}
    values.update({key.replace("_", "-"): value for key, value in inputs.items()})
    for key, value in values.items():
        if value is not None:
            monkeypatch.setenv(f"PREPARE_{key.upper()}", json.dumps(value))


@pytest.fixture
def urls(mocker: MockerFixture) -> List[str]:
    """
    Serve the templates without touching the network: the tests would otherwise download from
    raw.githubusercontent.com on every run, on every platform.
    """
    requested: List[str] = []

    def urlopen(url: str, *args: Any, **kwargs: Any) -> BytesIO:
        requested.append(url)
        template = url.removeprefix(f"{BASE_URL}/").removesuffix(".gitignore")
        if template not in TEMPLATES:
            raise HTTPError(url, 404, "Not Found", {}, None)  # type: ignore[arg-type]
        return BytesIO(TEMPLATES[template].encode("utf-8"))

    mocker.patch("urllib.request.urlopen", side_effect=urlopen)
    return requested


@pytest.fixture
def cache(tmp_path: Path, mocker: MockerFixture) -> Path:
    """The templates are cached in the OS cache directory, not in the project"""
    path = tmp_path / "cache"
    mocker.patch("prepare_gitignore_builder.main.get_cache_path", return_value=path)
    return path


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "project"
    path.mkdir()
    monkeypatch.chdir(path)
    return path


def test_download(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch,
                  mocker: MockerFixture) -> None:
    set_inputs(monkeypatch, templates=["Java"])
    failed = mocker.patch("prepare_gitignore_builder.main.set_failed")
    main()
    failed.assert_not_called()
    assert urls == [f"{BASE_URL}/Java.gitignore"]
    assert (cache / "Java.gitignore").read_text() == TEMPLATES["Java"]
    assert (project / ".gitignore").read_text() == "### Java\n*.class\n*.jar\n\n"


def test_several_templates(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """A template in a subdirectory ('Global/JetBrains') is cached in that subdirectory"""
    set_inputs(monkeypatch, templates=["Java", "Global/JetBrains"])
    main()
    assert (cache / "Global" / "JetBrains.gitignore").read_text() == TEMPLATES["Global/JetBrains"]
    assert (project / ".gitignore").read_text() == ("### Java\n*.class\n*.jar\n\n"
                                                    "### Global/JetBrains\n.idea/\n*.iml\n\n")


def test_cached(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """A fresh template is read from the cache, without a request"""
    (cache / "Java.gitignore").parent.mkdir(parents=True)
    (cache / "Java.gitignore").write_text("cached\n")
    set_inputs(monkeypatch, templates=["Java"])
    main()
    assert urls == []
    assert (project / ".gitignore").read_text() == "### Java\ncached\n\n"


def test_cache_too_old(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch) -> None:
    cached = cache / "Java.gitignore"
    cached.parent.mkdir(parents=True)
    cached.write_text("cached\n")
    hour_ago = time.time() - 3600
    os.utime(cached, (hour_ago, hour_ago))
    set_inputs(monkeypatch, templates=["Java"], caching=10)
    main()
    assert urls == [f"{BASE_URL}/Java.gitignore"]
    assert cached.read_text() == TEMPLATES["Java"]


def test_caching_disabled(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """With 'caching' zero or less the template is always downloaded again"""
    cached = cache / "Java.gitignore"
    cached.parent.mkdir(parents=True)
    cached.write_text("cached\n")
    set_inputs(monkeypatch, templates=["Java"], caching=0)
    main()
    assert urls == [f"{BASE_URL}/Java.gitignore"]


def test_rules(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch) -> None:
    set_inputs(monkeypatch, templates=["Java"], rules=["out/", "*.log"])
    main()
    assert (project / ".gitignore").read_text() == ("### Java\n*.class\n*.jar\n\n"
                                                    "### Custom rules\nout/\n*.log\n")


def test_output_directory(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch) -> None:
    (project / "assignment").mkdir()
    set_inputs(monkeypatch, templates=["Java"], output_directory="assignment")
    main()
    assert (project / "assignment" / ".gitignore").is_file()
    assert not (project / ".gitignore").exists()


def test_existing_gitignore_is_overwritten(project: Path, cache: Path, urls: List[str],
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    (project / ".gitignore").write_text("old\n")
    set_inputs(monkeypatch, templates=["Java"])
    main()
    assert (project / ".gitignore").read_text() == "### Java\n*.class\n*.jar\n\n"


def test_unknown_template(project: Path, cache: Path, urls: List[str], monkeypatch: pytest.MonkeyPatch,
                          mocker: MockerFixture) -> None:
    set_inputs(monkeypatch, templates=["Jave"])
    failed = mocker.patch("prepare_gitignore_builder.main.set_failed")
    main()
    failed.assert_called_once()
    assert not (project / ".gitignore").exists()


def test_exception(project: Path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture) -> None:
    mocker.patch("prepare_gitignore_builder.main.get_input", side_effect=Exception("Test Exception"))
    failed = mocker.patch("prepare_gitignore_builder.main.set_failed")
    main()
    failed.assert_called_once()


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_cache_path(platform: str, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture) -> None:
    mocker.patch("sys.platform", platform)
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\test\\AppData\\Local")
    assert get_cache_path().name in {"gitignore-builder", "cache"}


def test_cache_path_unsupported_platform(mocker: MockerFixture) -> None:
    mocker.patch("sys.platform", "solaris")
    with pytest.raises(AssertionError):
        get_cache_path()
