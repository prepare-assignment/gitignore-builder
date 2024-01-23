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
    description: "Output directory where the new .gitignore should be placed"
    required: false
    type: string
    default: "."
```