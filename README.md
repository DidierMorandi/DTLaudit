# DTLaudit

DTLaudit is a read-only audit tool for comparing a local set of projects.

It scans one project or a directory containing several projects, then produces a compact report about project structure, Git status, GitHub availability, README files, releases, generated folders, large files, and files that appear only in some projects.

## Features

- Audits a single local project or a whole project suite.
- Detects Git repositories, current branch, origin remote, local changes, and tags.
- Detects GitHub remotes.
- Optionally queries GitHub through the `gh` CLI for repository metadata, latest release, open pull requests, and open issues.
- Highlights generated folders such as `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`, and `.mypy_cache/`.
- Reports large files above 5 MB.
- Produces an HTML report by default.
- Can also write JSON and text reports on demand.
- Never modifies audited projects.

## Requirements

- Python 3.10 or newer.
- Git, for Git repository information.
- Optional: GitHub CLI (`gh`), authenticated, if you want live GitHub metadata.

DTLaudit itself uses only the Python standard library.

## Usage

When launched without arguments, DTLaudit displays a console interface inspired
by DTLi18n:

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py"
```

The menu lets the user audit a project suite or one project and opens Windows
Explorer to select the folder. When the audit completes, DTLaudit offers to open
the HTML report and then returns to the main menu.

Audit a directory containing several projects:

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils"
```

Audit one project:

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --project "D:\Documents\Mes sites Web\outils\GitHubMenu"
```

Skip GitHub queries:

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils" --no-github
```

## Output Files

By default, DTLaudit writes only the HTML report:

```text
DTLaudit_rapport.html
```

The file is written in the DTLaudit directory, next to `DTLaudit.py`.

To also write JSON and text reports:

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils" --json --text
```

This creates:

```text
DTLaudit_rapport.html
DTLaudit_rapport.json
DTLaudit_rapport.txt
```

You can choose custom output paths:

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils" --html "audit.html" --json "audit.json" --text "audit.txt"
```

Relative output paths are resolved from the DTLaudit directory.

## Options

```text
--project PATH       Audit one local project.
--suite PATH         Audit a directory containing several projects.
--json [PATH]        Also write a JSON report.
--text [PATH]        Also write a text report.
--txt [PATH]         Alias for --text.
--html [PATH]        Write an HTML report. Enabled by default.
--no-github          Do not query GitHub through the gh CLI.
--lang {fr,en}       Select the interface and report language.
```

French is used by default. The language can also be set with the
`DTL_LANGUAGE=fr` or `DTL_LANGUAGE=en` environment variable.

User-facing text is centralized in `dtlaudit_i18n.py`. Every key in this bilingual
catalogue uses the `txxxx_` prefix.

`--project` and `--suite` are mutually exclusive. One of them is required in
command-line mode; with no arguments, the interactive console menu is used.

## Project Discovery

When using `--suite`, DTLaudit scans the direct subdirectories of the suite directory.

A subdirectory is considered a project when it contains at least one of the following:

- a `.git` directory;
- a Python file (`*.py`);
- a Windows script file (`*.ps1`, `*.vbs`, `*.bat`, or `*.cmd`);
- a README file (`README*`).

Hidden directories are ignored during project discovery.

## Report Contents

The report starts with a summary table:

```text
Projet      Git  GitHub  README  Release  Branche  Modifs
----------  ---  ------  ------  -------  -------  ------
GitHubMenu  Oui  Oui     Oui     Oui      main     960
DTLaudit    Non  Non     Non     Non      -        0
```

Then each project gets a detailed block with:

- README presence;
- Git status;
- current branch;
- GitHub remote presence;
- local modified file count;
- tag count;
- GitHub repository metadata, when available;
- latest GitHub release, when available;
- open pull request and issue counts, when available.

The report also includes notable observations and a file matrix showing files or directories that appear only in one project or in some projects but not all.

## GitHub Metadata

GitHub metadata is collected only when:

- `--no-github` is not used;
- the `gh` command is installed;
- `gh` is authenticated;
- the project has a GitHub remote or can be resolved by `gh`.

If these conditions are not met, the report still works with local Git information.

## Safety

DTLaudit is intentionally read-only.

It walks project files, reads Git metadata, and optionally calls `gh`, but it does not change audited projects, run builds, clean files, commit, push, or delete anything.

## Notes

Generated artifacts such as `build/`, `dist/`, and executable files can create a lot of Git noise if they are tracked. DTLaudit highlights these cases so they can be reviewed and, when appropriate, added to `.gitignore`.

## Update - 14 June 2026

The current code reports `v1.1-6` in `DTLaudit.py`.

New and confirmed from the code (`v1.1-0`, July 16, 2026):

- The Tkinter interface has been replaced with a console interface consistent with DTLi18n.
- Launching without arguments opens a menu for auditing a suite or a single project.
- The interactive menu displays `A` for a suite, `B` for a project, and `Q` to quit. The hint below the subtitle uses `1` to switch from French to English and `2` to return to French.
- Folder selection uses Windows Explorer; progress, report opening, and return to the menu remain controlled from the console.
- The HTML report is generated by default as `DTLaudit_rapport.html`.
- JSON and text outputs remain optional through `--json` and `--txt` / `--text`.
- The audit now checks for user guides and reference manuals in addition to the README.
- GitHub metadata can be enriched through `gh`: repository visibility, latest release, open pull requests, and open issues.
- A helper can copy the JSON output to a XAMPP environment when a local PHP dashboard is used.
- `DTLaudit_dashboard_live.php` complements the static report for a more dynamic local dashboard.
