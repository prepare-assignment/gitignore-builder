import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import List, Optional, Final

from prepare_toolbox.core import get_input, set_failed, info


def main() -> None:
    try:
        templates: List[str] = get_input("templates", required=True)
        rules: Optional[List[str]] = get_input("rules")
        caching: int = get_input("caching")
        output_directory: str = get_input("output-directory")

        cache_path: Final[Path] = get_cache_path()
        base_url = "https://raw.githubusercontent.com/github/gitignore/main"
        ignore_path = os.path.normpath(os.path.join(os.getcwd(), output_directory, ".gitignore"))
        ignore = ""
        for template in templates:
            template_path = f"{os.path.join(cache_path, template)}.gitignore"
            content = ""
            if os.path.isfile(template_path) and int((time.time() - os.path.getmtime(template_path)) / 60) < caching:
                info(f"Template {template} is already present and fresh enough")
                with open(template_path) as handle:
                    content = handle.read()
            else:
                info(f"Template {template} not present or too old")
                url = f"{base_url}/{template}.gitignore"
                with urllib.request.urlopen(url) as handle:
                    content = handle.read().decode("utf-8")
                    basedir = os.path.dirname(template_path)
                    if not os.path.isdir(basedir):
                        Path(basedir).mkdir(parents=True, exist_ok=True)
                    with open(template_path, 'w') as file:
                        file.write(content)
            ignore += f"### {template}\n"
            ignore += content
            ignore += "\n"
        if rules is not None:
            ignore += "### Custom rules\n"
            for rule in rules:
                ignore += f"{rule}\n"

        with open(ignore_path, 'w') as handle:
            handle.write(ignore)

    except Exception as e:
        set_failed(e)


def get_cache_path() -> Path:
    """
    Get the path to the default cache location for applications
    :return: Path to the OS specific application cache
    :raises: AssertionError: if OS is not one of Linux, macOS or Windows
    """
    if sys.platform == "linux":
        cache = os.environ.get("XDG_CACHE_HOME")
        if cache is None:
            cache = "~/.cache"
        return Path(f"{cache}/gitignore-builder").expanduser()
    elif sys.platform == "darwin":
        return Path("~/Library/Caches/gitignore-builder").expanduser()
    elif sys.platform == "win32":
        lad = f"{os.environ.get('LOCALAPPDATA')}"
        return Path(os.path.join(lad, "gitignore-builder", "cache"))
    else:
        raise AssertionError("Unsupported OS")


if __name__ == "__main__":
    main()
