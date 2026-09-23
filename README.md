# gitignore builder

Create a `.gitignore` file based on [templates](https://github.com/github/gitignore) from GitHub.  
It is also possible to add custom rules.

## Example

```yml
- name: Add .gitignore
  uses: gitignore-builder
  with:
    templates:
      - "Java"
      - "Global/JetBrains"
    rules:
      - "ignore-me-too"
    output-directory: out
```

## Options

The following options are available:

```yaml
templates:
    description: "GitHub templates to use"
    required: true
    type: array
    items: string
rules:
    description: "Extra rules to add"
    required: false
    type: array
    items: string
caching:
    description: "For how long (in minutes) templates should be cached (to disable, use a value less or equal to zero)"
    required: false
    type: integer
    default: 10080 # One week
output-directory:
    description: "Output directory where the new .gitignore should be placed, it is created if needed"
    required: false
    type: string
    default: "."
allow-outside-working-directory:
    description: "The output directory can be outside the working directory"
    required: false
    type: boolean
    default: false
```

The output directory is created if it doesn't exist. An existing `.gitignore` in it is overwritten. A directory outside the working directory (e.g. `../out`) fails, unless `allow-outside-working-directory` is set.

## Releases

Releases are automated with [semantic-release](https://semantic-release.gitbook.io/). Pull requests are squash merged, so the PR title becomes the commit on `main` and must follow [Conventional Commits](https://www.conventionalcommits.org/) (checked on every PR):

| PR title | Release |
|----------|---------|
| `fix: ...`, `perf: ...` | patch (1.2.3 → 1.2.4) |
| `feat: ...` | minor (1.2.3 → 1.3.0) |
| `!` after the type (e.g. `feat!: ...`, `refactor!: ...`) or a `BREAKING CHANGE:` footer | major (1.2.3 → 2.0.0) |
| `docs:`, `chore:`, `ci:`, `build:`, `refactor:`, `test:`, `style:`, `revert:` | no release |

On every merge to `main` the next version is determined, tagged (`vX.Y.Z`) and a GitHub release is created. The major tag (e.g. `v1`) is moved to the new release, so `uses: gitignore-builder@v1` always gets the newest 1.x version.

Because the major tag moves, `git pull` in an existing clone can fail with `! [rejected] v1 -> v1 (would clobber existing tag)`. Update the tags once with `git fetch --tags --force` and pull again.
