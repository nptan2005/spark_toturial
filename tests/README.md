```bash
.PHONY: test lint

test:
\tpytest -vv --log-cli-level=INFO

test-quiet:
\tpytest -q

lint:
\tpython -m compileall common_lib

```

run:

```bash
make test
```

Run test local

```bash
pytest -vv --log-cli-level=INFO
```