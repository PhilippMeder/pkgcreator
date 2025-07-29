### Main code

- [x] github handling
- [x] git repository (creation) handling
- [x] venv (creation) handling
- [x] structure
- [x] settings should use `ghutils` for the github urls
- [x] improve `pkgfiles` file content
- [x] better pyproject.toml creation
- [x] combined cli
- [x] add subparsers/commands and reduce to one callable script (e.g. like `git [commit | add | init]`)

### Tests

- [x] builder/cli
- [x] git
- [x] venv
- [x] tools
- [x] ghutils urls
- [ ] ghutils download (`requests` to the GitHub API are limited, so how can this be done without a real access?)

#### README
- [x] venv
- [x] logging tools
- [x] cli tools
- [x] toc
- [x] check
- [x] logo

### Inline documentation

- [x] add missing docstrings
- [x] take care of type annotations for optional parameters, e.g. `list[str] = None` should be `list[str] | None = None` according to PEP 484

### Project

- [ ] update pyproject.toml
    - [x] add dev tools `pytest` and `ruff` with config
    - [ ] maybe `dynamic = ["description"]` to create description dynamically (README)?
- [x] GitHub workflows
    - [x] push/pull to main branch should trigger `pytest` and `ruff`
    - [x] creating a release should run `pytest` and upload to PyPI
- [ ] publish
