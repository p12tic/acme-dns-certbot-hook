The project uses ruff for formatting and simple lint checks, and mypy for typing.
When creating a PR make sure to run the following and ensure that no errors are
detected:

```
uv run ruff format
uv run ruff check --fix
uv run mypy .
```

Tests are run using the following

```
python3 -m unittest discover
```
