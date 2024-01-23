import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional

import pytest
from pytest_mock import MockerFixture

from gitignore_builder.main import main


def set_environment(templates: List[str], rules: Optional[List[str]] = None, caching: int = 10080, out: str = ".") -> None:
    os.environ["PREPARE_TEMPLATES"] = json.dumps(templates)
    if rules is not None:
        os.environ["PREPARE_RULES"] = json.dumps(rules)
    os.environ["PREPARE_CACHING"] = json.dumps(caching)
    os.environ["PREPARE_OUTPUT-DIRECTORY"] = json.dumps(out)


def set_cache_path(path: Path, mocker: MockerFixture) -> None:
    mocker.patch("gitignore_builder.main.get_cache_path", return_value=path)


def test_not_present(tmp_path: Path, mocker: MockerFixture) -> None:
    set_cache_path(tmp_path, mocker)
    set_environment(["Java"])
    main()

