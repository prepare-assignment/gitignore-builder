def main() -> None:
    try:
        include: List[str] = get_input("include", required=True)
        exclude: Optional[List[str]] = get_input("exclude")
        cwd: str = get_input("working-directory")
        allow_outside: bool = get_input("allow-outside-working-directory")
        out: str = get_input("output-directory")
        comment: str = get_input("comment")
        recursive: bool = get_input("recursive")
        verbosity: int = get_input("verbosity")
        dry_run: bool = get_input("dry-run")


    except Exception as e:
        set_failed(e)


if __name__ == "__main__":
    main()