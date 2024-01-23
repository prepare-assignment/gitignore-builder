import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import List, Optional

import pytest
from pytest_mock import MockerFixture

from gitignore_builder.main import main


def set_environment(out: Path, templates: List[str], rules: Optional[List[str]] = None, caching: int = 10080) -> None:
    os.environ["PREPARE_TEMPLATES"] = json.dumps(templates)
    if rules is not None:
        os.environ["PREPARE_RULES"] = json.dumps(rules)
    os.environ["PREPARE_CACHING"] = json.dumps(caching)
    os.environ["PREPARE_OUTPUT-DIRECTORY"] = json.dumps(str(out))


def set_cache_path(path: Path, mocker: MockerFixture) -> None:
    mocker.patch("gitignore_builder.main.get_cache_path", return_value=path)


def test_not_present(tmp_path: Path, mocker: MockerFixture) -> None:
    set_cache_path(tmp_path, mocker)
    set_environment(tmp_path, ["Java"])
    main()
    assert os.path.isfile(os.path.join(tmp_path, "Java.gitignore"))


def test_too_old(tmp_path: Path, mocker: MockerFixture) -> None:
    set_cache_path(tmp_path, mocker)
    set_environment(tmp_path, ["Java"])
    template_path = os.path.join(tmp_path, "Java.gitignore")
    Path(template_path).touch()
    os.utime(template_path, (0, 0))
    main()
    assert os.path.getmtime(template_path) > 0


def test_present(tmp_path: Path, mocker: MockerFixture) -> None:
    set_cache_path(tmp_path, mocker)
    set_environment(tmp_path, ["Java"])
    template_path = os.path.join(tmp_path, "Java.gitignore")
    Path(template_path).touch()
    epoch = os.path.getmtime(template_path)
    main()
    assert os.path.getmtime(template_path) == epoch


def test_subdirs(tmp_path: Path, mocker: MockerFixture) -> None:
    set_cache_path(tmp_path, mocker)
    set_environment(tmp_path, ["Global/JetBrains"])
    main()
    assert os.path.isdir(os.path.join(tmp_path, "Global"))


def test_rules(tmp_path: Path, mocker: MockerFixture) -> None:
    set_cache_path(tmp_path, mocker)
    set_environment(tmp_path, ["Java"], ["extrarule"])
    main()
    with open(os.path.join(tmp_path, ".gitignore"), 'rb') as handle:
        for line in handle:
            pass
        last_line = line
    assert last_line == b"extrarule\n"


def test_exception(mocker: MockerFixture) -> None:
    mocker.patch("gitignore_builder.main.get_input", side_effect=Exception("Test Exception"))
    spy = mocker.patch("gitignore_builder.main.set_failed")
    main()
    spy.assert_called_once()