# Release process

## Prerequisites (one-time)

1. Create accounts
   - [TestPyPI](https://test.pypi.org/account/register/)
   - [PyPI](https://pypi.org/account/register/)
2. Create API tokens
   - TestPyPI → Account settings → API tokens → "Add API token" (scope: entire account for first push, then per-project)
   - PyPI → same flow
3. Store tokens in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEI...<your prod token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEI...<your test token>
```

Lock it down: `chmod 600 ~/.pypirc` on Unix, or set file as read-only + user-only on Windows via `icacls`.

## Cutting a release

1. Bump `version` in `pyproject.toml` and `src/judgelab/__init__.py` (keep them in sync).
2. Update `CHANGELOG.md` with the new version header.
3. Commit, tag, push:

```bash
git add -A
git commit -m "release: vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

4. Clean, build, verify:

```bash
rm -rf dist build *.egg-info
python -m build --wheel --sdist
twine check dist/*
```

5. Upload to TestPyPI first (dry run):

```bash
twine upload -r testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --no-deps judgelab
python -c "import judgelab; print(judgelab.__version__)"
```

6. Upload to real PyPI:

```bash
twine upload dist/*
```

7. Verify:

```bash
pip install --upgrade judgelab
judgelab --help
```

8. Create a GitHub Release from the tag; attach the built wheel and sdist from `dist/`.

## Automation (optional)

Add `.github/workflows/publish.yml`:

```yaml
name: publish
on:
  push:
    tags: ["v*"]
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # trusted publishing
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Requires one-time setup on PyPI: **Account → Publishing → Add a new pending publisher** pointing at `Sdm08/judgelab` and this workflow filename. After that, pushing a `vX.Y.Z` tag publishes automatically with no stored token.

## Post-release checklist

- [ ] `pip install judgelab` works from a clean env
- [ ] `judgelab --help` prints commands
- [ ] GitHub Release notes mirror CHANGELOG entry
- [ ] Announce (optional): HN Show, r/LocalLLaMA, Twitter
