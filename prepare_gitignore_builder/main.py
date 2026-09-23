import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import List, Optional, Final
from urllib.error import HTTPError, URLError

from prepare_toolbox.core import get_input, set_failed, set_output, info

# Without a timeout an unreachable github.com makes the task hang until the whole run is killed
TIMEOUT: Final[int] = 30
GITHUB_GITIGNORE: Final[str] = "https://github.com/github/gitignore"


def __cache_file(cache_path: Path, template: str) -> str:
    """
    The file a template is cached in. A template name ends up in this path, so a name like '../../evil' or an
    absolute path would read and write files outside the cache directory.
    """
    path = os.path.normpath(os.path.join(cache_path, f"{template}.gitignore"))
    if not Path(path).is_relative_to(os.path.normpath(cache_path)):
        raise ValueError(f"Invalid template '{template}', use a name from {GITHUB_GITIGNORE} "
                         f"like 'Java' or 'Global/JetBrains'")
    return path


def __download(url: str, template: str) -> str:
    """
    Download a template. urllib's own errors don't mention the template, and a 404 (a typo in the name) looks
    like a broken task instead of a wrong input.
    """
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return str(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            raise ValueError(f"Template '{template}' doesn't exist, see {GITHUB_GITIGNORE} for the "
                             f"available templates") from error
        raise ValueError(f"Could not download template '{template}' from {url}: "
                         f"{error.code} {error.reason}") from error
    except (URLError, TimeoutError) as error:
        reason = getattr(error, "reason", error)
        raise ValueError(f"Could not download template '{template}' from {url}: {reason}") from error


def main() -> None:
    try:
        templates: List[str] = get_input("templates", required=True)
        rules: Optional[List[str]] = get_input("rules")
        caching: int = get_input("caching")
        output_directory: str = get_input("output-directory")
        allow_outside: bool = get_input("allow-outside-working-directory")

        cache_path: Final[Path] = get_cache_path()
        base_url = "https://raw.githubusercontent.com/github/gitignore/main"
        output_path = Path(os.path.normpath(os.path.join(os.getcwd(), output_directory)))
        if not allow_outside and not output_path.is_relative_to(os.getcwd()):
            set_failed(f"The output directory '{Path(output_directory).as_posix()}' is outside the working "
                       f"directory, set 'allow-outside-working-directory' to allow this")
        ignore_path = output_path / ".gitignore"
        ignore = ""
        for template in templates:
            template_path = __cache_file(cache_path, template)
            content = ""
            if os.path.isfile(template_path) and int((time.time() - os.path.getmtime(template_path)) / 60) < caching:
                info(f"Template {template} is already present and fresh enough")
                with open(template_path) as handle:
                    content = handle.read()
            else:
                info(f"Template {template} not present or too old")
                url = f"{base_url}/{template}.gitignore"
                content = __download(url, template)
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

        # The task's whole job is producing this file, so create the directory it goes in
        output_path.mkdir(parents=True, exist_ok=True)
        with open(ignore_path, 'w') as handle:
            handle.write(ignore)
        # The path as other steps can use it, always with '/' (also on Windows)
        relative = ignore_path.relative_to(os.getcwd()) if ignore_path.is_relative_to(os.getcwd()) else ignore_path
        set_output("file", relative.as_posix())

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
