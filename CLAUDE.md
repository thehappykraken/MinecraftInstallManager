# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`mim` (Minecraft Install Manager) is a Python CLI that queries, downloads, and installs Minecraft server jars and plugins from multiple upstream repositories, driven either by ad-hoc CLI flags or by a declarative JSON/YAML config file. Published to PyPI as `minecraft-install-manager`; requires Python >= 3.11.

## Commands

```bash
# Dev install (required — tests/test_mim.py imports the installed `mim` package)
python -m pip install -e .
pip install -r requirements.txt

# Run all tests (pytest is unconfigured; run from repo root)
pytest

# Single test file / single test
pytest tests/util/test_PaperRepository.py
pytest tests/test_mim.py::test_main_install

# Lint exactly as CI does
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Exercise the CLI without writing files
mim install --file tests/config.json --destination /tmp/server --dryrun
```

CI (`.github/workflows/python-ci.yml`) runs flake8 + pytest on push/PR to `main`. Publishing to PyPI is triggered by a published GitHub Release; bump `version` in `pyproject.toml` as part of the change (see the "Update package version" commits).

## Tests hit the live network

There is no mocking layer. The test suite calls the real PaperMC, Modrinth, Spiget, GitHub, Jenkins, and GeyserMC APIs and downloads real jars into temp directories. Consequences:

- Tests are slow and fail when upstream is down, rate-limits, or removes a pinned version.
- Tests assert on specific upstream artifacts (e.g. `WorldEdit 7.3.9`, `QuickShop-Hikari 3.3.0.0`, Paper `1.21.1`/`1.21.9`). A failure often means upstream drift, not a regression — verify against the API before "fixing" code.
- `tests/conftest.py` overrides pytest's built-in `tmp_path` with a `str` (not `pathlib.Path`), so test code passes plain strings into install paths.

## Architecture

Two parallel plugin-style hierarchies live in `src/mim/util/Repository.py`, both using the same pattern:

- **Servers**: `ServerRepository` (abstract) → `Server` value objects. Implemented by `PaperRepository`.
- **Plugins**: `PluginRepository` (abstract) → `Plugin` → `PluginVersion` → `PluginAsset`. Implemented by `GeyserRepository`, `GithubRepository`, `JenkinsRepository`, `ModrinthRepository`, `SpigetRepository`.

Key mechanics that span files:

- **Registration by construction.** A repository's `__init__` inserts `self` into the class-level `_registry` dict keyed by lowercase name. `mim.main()` instantiates all six repositories before dispatching; tests use session-scoped autouse fixtures in `tests/util/conftest.py`. `PluginRepository.searchAll()` / `ServerRepository.searchAll()` fan out over the registry — a repository that is never constructed is invisible to search.
- **Server identity, not equality.** `Server` defines no `__eq__`. Compatibility filtering throughout `mim.py` (`s in servers`, `server in v.compatibility`) and up-to-date checks (`current_servers[0] != server`) rely on *object identity*. This only works because `PaperRepository.list()` memoizes into `self.servers` and every lookup returns the same instances. Do not construct fresh `Server` objects for comparison, and do not re-instantiate repositories mid-run — either silently breaks compatibility matching.
- **Lazy fan-out.** `Plugin.versions` and `PluginVersion.assets` are cached properties that trigger network calls on first access; a single `find_versions()` call queries every registered plugin repository.
- **Compatibility is populated at search time.** Modrinth/Spiget/Geyser resolve their declared game versions into concrete `Server` objects via `ServerRepository.searchAll()` during `search()`. GitHub and Jenkins report `compatibility=None`, which every filter treats as "compatible with anything".
- **Install/uninstall by filename convention.** "Installed" state is inferred purely by probing the destination directory for expected filenames (`Server.asset` = `{name}-{server_version}.jar`; `Plugin.installedVersions()` matches asset filenames). Repositories rewrite asset filenames to embed the version (`filename.replace('.jar', f'-{version}.jar')`) so that detection and cleanup of old versions work. Changing a filename scheme breaks upgrade detection for already-installed users.
- **Version-string handling.** Ordering uses `packaging.version.Version` with a lexical fallback on `InvalidVersion` — necessary because Jenkins versions are build numbers/permalinks (`lastStableBuild`) and Geyser versions are `{version}.{build}`. `PaperRepository.search()` implements the `1.x.x` wildcard by rewriting `.x` to the regex `.?\d*` and full-matching.

`src/mim/mim.py` holds the argparse CLI (`versions`, `assets`, `download`, `install`) plus the install resolution algorithm.

## The install resolution algorithm (`install()` in mim.py)

This is the most subtle code in the repo and the subject of the most recent bug fixes. It partitions plugins into two buckets and narrows the candidate server list separately for each:

1. Plugins **with** an explicit `version` — compatibility is evaluated but *not enforced* (per the documented config format).
2. Plugins **without** a version — the highest compatible version is chosen, and incompatible servers are eliminated.

It then prefers servers satisfying both buckets, falls back to the unspecified-only set with a "Continuing at risk" warning, picks the highest server version, and resolves each unspecified plugin against that chosen server. When editing, preserve the "warn and continue at risk" behavior — failing hard here was the bug fixed in `0087e8f`.

## Config file format gotcha

`install()` reads the server version from the **`version`** key (`data.get('version', '1.x.x')`), but `README.md` documents the key as `server:` and `tests/config.json` also uses `server`. Configs using `server:` silently fall back to `1.x.x`. Confirm which key is intended before "fixing" either side. `--file` accepts JSON or YAML; JSON is tried first and YAML is the fallback on `JSONDecodeError`.

## Import paths

Two import spellings coexist: `tests/test_mim.py` imports the installed package (`import mim.mim`), while `tests/util/conftest.py` and the util tests import through the source tree (`from src.mim.util...`). These resolve to *different module objects* with *different* `_registry` dicts. Keep new tests consistent with the file they sit next to, and be aware that registry state is not shared across the two spellings.
