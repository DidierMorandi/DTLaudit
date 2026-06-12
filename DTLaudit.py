#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""DTLaudit - rapport comparatif en lecture seule."""

from __future__ import annotations

import argparse
import contextlib
import html
import io
import json
import os
import shutil
import subprocess
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


VERSION = "v1.0-1"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent
DEFAULT_JSON_REPORT = "DTLaudit_rapport.json"
DEFAULT_TXT_REPORT = "DTLaudit_rapport.txt"
DEFAULT_HTML_REPORT = "DTLaudit_rapport.html"
GENERATED_DIRS = {"build", "dist", "__pycache__", ".pytest_cache", ".mypy_cache"}
LOCAL_DIRS = {"logs", "tmp", "temp"}
TEMP_SUFFIXES = {".tmp", ".bak", ".old", ".log", ".pyc", ".pyo"}
LARGE_FILE_BYTES = 5 * 1024 * 1024


@dataclass
class GitInfo:
    present: bool = False
    branch: str | None = None
    remote: str | None = None
    remote_github: bool = False
    changed_files: int | None = None
    tags_count: int | None = None
    latest_tag: str | None = None


@dataclass
class GitHubInfo:
    checked: bool = False
    available: bool = False
    repository: str | None = None
    url: str | None = None
    visibility: str | None = None
    default_branch: str | None = None
    latest_release: str | None = None
    open_prs: int | None = None
    open_issues: int | None = None
    note: str | None = None


@dataclass
class FileEntry:
    path: str
    kind: str
    size: int
    modified: str


@dataclass
class ProjectReport:
    name: str
    path: str
    files: list[FileEntry] = field(default_factory=list)
    git: GitInfo = field(default_factory=GitInfo)
    github: GitHubInfo = field(default_factory=GitHubInfo)


def run_command(args: list[str], cwd: Path, timeout: int = 12) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return completed.returncode, completed.stdout.strip()


def iso_mtime(path: Path) -> str:
    return path.stat().st_mtime_ns.__str__()


def discover_projects(suite_root: Path) -> list[Path]:
    projects = []
    try:
        children = sorted(suite_root.iterdir(), key=lambda item: item.name.lower())
    except OSError:
        return projects

    for child in children:
        if not child.is_dir() or child.name.startswith("."):
            continue
        try:
            has_git = (child / ".git").exists()
            has_project_files = any(child.glob("*.py")) or any(child.glob("README*"))
        except OSError:
            continue
        if has_git or has_project_files:
            projects.append(child)
    return projects


def collect_files(project: Path) -> list[FileEntry]:
    entries: list[FileEntry] = []
    for root, dirs, files in os.walk(project, onerror=lambda error: None):
        root_path = Path(root)
        dirs[:] = [name for name in dirs if name != ".git"]

        for dirname in dirs:
            path = root_path / dirname
            rel = path.relative_to(project).as_posix() + "/"
            entries.append(
                FileEntry(
                    path=rel,
                    kind="directory",
                    size=0,
                    modified=iso_mtime(path),
                )
            )

        for filename in files:
            path = root_path / filename
            rel = path.relative_to(project).as_posix()
            try:
                stat = path.stat()
            except OSError:
                continue
            entries.append(
                FileEntry(
                    path=rel,
                    kind="file",
                    size=stat.st_size,
                    modified=str(stat.st_mtime_ns),
                )
            )
    return sorted(entries, key=lambda entry: entry.path.lower())


def collect_git(project: Path) -> GitInfo:
    info = GitInfo(present=(project / ".git").exists())
    if not info.present:
        return info

    code, branch = run_command(["git", "branch", "--show-current"], project)
    info.branch = branch if code == 0 and branch else None

    code, remote = run_command(["git", "remote", "get-url", "origin"], project)
    if code != 0 or not remote:
        code, remote = run_command(["git", "remote", "-v"], project)
    info.remote = remote.splitlines()[0] if remote else None
    info.remote_github = bool(info.remote and "github.com" in info.remote.lower())

    code, status = run_command(["git", "status", "--short"], project)
    info.changed_files = len(status.splitlines()) if code == 0 and status else 0

    code, tags = run_command(["git", "tag", "--list"], project)
    tag_lines = tags.splitlines() if code == 0 and tags else []
    info.tags_count = len(tag_lines)
    info.latest_tag = tag_lines[-1] if tag_lines else None
    return info


def repo_slug_from_remote(remote: str | None) -> str | None:
    if not remote or "github.com" not in remote.lower():
        return None
    cleaned = remote.strip()
    if cleaned.startswith("git@github.com:"):
        slug = cleaned.split("git@github.com:", 1)[1]
    elif "github.com/" in cleaned:
        slug = cleaned.split("github.com/", 1)[1]
    else:
        return None
    slug = slug.replace(".git", "").split()[0]
    return slug.strip("/") or None


def collect_github(project: Path, git: GitInfo, enabled: bool) -> GitHubInfo:
    info = GitHubInfo(checked=enabled)
    if not enabled:
        info.note = "non interrogé"
        return info
    if shutil.which("gh") is None:
        info.note = "commande gh non disponible"
        return info

    slug = repo_slug_from_remote(git.remote)
    base_cmd = ["gh", "repo", "view"]
    if slug:
        base_cmd.append(slug)
    base_cmd.extend(
        [
            "--json",
            "nameWithOwner,url,visibility,defaultBranchRef",
        ]
    )

    code, output = run_command(base_cmd, project, timeout=20)
    if code != 0 or not output:
        info.note = "dépôt GitHub non détecté"
        return info

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        info.note = "réponse GitHub non lisible"
        return info

    info.available = True
    info.repository = data.get("nameWithOwner")
    info.url = data.get("url")
    info.visibility = data.get("visibility")
    branch = data.get("defaultBranchRef") or {}
    info.default_branch = branch.get("name")

    release_cmd = ["gh", "release", "list", "--limit", "1", "--json", "tagName"]
    if slug:
        release_cmd.extend(["--repo", slug])
    code, output = run_command(release_cmd, project, timeout=20)
    if code == 0 and output:
        try:
            releases = json.loads(output)
            if releases:
                info.latest_release = releases[0].get("tagName")
        except json.JSONDecodeError:
            pass

    pr_cmd = ["gh", "pr", "list", "--state", "open", "--json", "number"]
    if slug:
        pr_cmd.extend(["--repo", slug])
    code, output = run_command(pr_cmd, project, timeout=20)
    if code == 0 and output:
        try:
            info.open_prs = len(json.loads(output))
        except json.JSONDecodeError:
            pass

    issue_cmd = ["gh", "issue", "list", "--state", "open", "--json", "number"]
    if slug:
        issue_cmd.extend(["--repo", slug])
    code, output = run_command(issue_cmd, project, timeout=20)
    if code == 0 and output:
        try:
            info.open_issues = len(json.loads(output))
        except json.JSONDecodeError:
            pass

    return info


def scan_project(project: Path, github_enabled: bool) -> ProjectReport:
    git = collect_git(project)
    return ProjectReport(
        name=project.name,
        path=str(project),
        files=collect_files(project),
        git=git,
        github=collect_github(project, git, github_enabled),
    )


def present_absent(value: bool) -> str:
    return "présent" if value else "absent"


def yes_no(value: bool) -> str:
    return "oui" if value else "non"


def size_label(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} Mo"
    if size >= 1024:
        return f"{size / 1024:.1f} Ko"
    return f"{size} o"


def project_count_label(count: int) -> str:
    return f"{count} projet" if count == 1 else f"{count} projets"


def project_has_readme(project: ProjectReport) -> bool:
    return any(entry.path.lower().startswith("readme") for entry in project.files)


def oui_non(value: bool) -> str:
    return "Oui" if value else "Non"


def print_summary_table(projects: list[ProjectReport]) -> None:
    rows = []
    for project in sorted(projects, key=lambda item: item.name.lower()):
        rows.append(
            {
                "Projet": project.name,
                "Git": oui_non(project.git.present),
                "GitHub": oui_non(project.git.remote_github or project.github.available),
                "README": oui_non(project_has_readme(project)),
                "Release": oui_non(bool(project.github.latest_release)),
                "Branche": project.git.branch or "-",
                "Modifs": str(project.git.changed_files or 0),
            }
        )

    columns = ["Projet", "Git", "GitHub", "README", "Release", "Branche", "Modifs"]
    widths = {
        column: max(len(column), *(len(row[column]) for row in rows)) if rows else len(column)
        for column in columns
    }

    print("Synthèse")
    print("========")
    print("  ".join(column.ljust(widths[column]) for column in columns))
    print("  ".join("-" * widths[column] for column in columns))
    for row in rows:
        print("  ".join(row[column].ljust(widths[column]) for column in columns))
    print()


def print_project_block(project: ProjectReport) -> None:
    print(project.name)
    print("-" * len(project.name))
    print("README :")
    print(f"    {present_absent(project_has_readme(project))}")
    print("Git :")
    print(f"    {present_absent(project.git.present)}")
    if project.git.present:
        print("Branche :")
        print(f"    {project.git.branch or 'non détectée'}")
        print("Remote GitHub :")
        print(f"    {present_absent(project.git.remote_github)}")
        print("Modifications locales :")
        print(f"    {project.git.changed_files or 0}")
        print("Tags :")
        print(f"    {project.git.tags_count or 0}")
    print("GitHub :")
    if project.github.available:
        print(f"    dépôt : {project.github.repository or 'non détecté'}")
        print(f"    visibilité : {project.github.visibility or 'non détectée'}")
        print(f"    release récente : {project.github.latest_release or 'absente'}")
        print(f"    pull requests ouvertes : {project.github.open_prs if project.github.open_prs is not None else 'non détectées'}")
        print(f"    issues ouvertes : {project.github.open_issues if project.github.open_issues is not None else 'non détectées'}")
    else:
        print(f"    {project.github.note or 'non disponible'}")
    print()


def notable_observations(projects: list[ProjectReport]) -> list[str]:
    observations: list[str] = []
    total = len(projects)
    if not total:
        return observations

    def count_projects(predicate: Any) -> int:
        return sum(1 for project in projects if predicate(project))

    readme_count = count_projects(project_has_readme)
    observations.append(
        f"README est présent dans {project_count_label(readme_count)} sur {total}."
    )

    git_count = count_projects(lambda project: project.git.present)
    observations.append(
        f"Git est présent dans {project_count_label(git_count)} sur {total}."
    )

    github_remote_count = count_projects(lambda project: project.git.remote_github)
    observations.append(
        f"Remote GitHub est présent dans {project_count_label(github_remote_count)} sur {total}."
    )

    github_available_count = count_projects(lambda project: project.github.available)
    observations.append(
        f"Status GitHub disponible dans {project_count_label(github_available_count)} sur {total}."
    )

    branch_counts = Counter(project.git.branch for project in projects if project.git.branch)
    for branch, count in branch_counts.most_common():
        observations.append(
            f"Branche {branch} observée dans {project_count_label(count)} sur {total}."
        )

    path_projects: dict[str, set[str]] = defaultdict(set)
    for project in projects:
        for entry in project.files:
            path_projects[entry.path].add(project.name)

    unique_files = {
        path: next(iter(names))
        for path, names in path_projects.items()
        if len(names) == 1 and not path.endswith("/")
    }
    if unique_files:
        by_project: dict[str, int] = Counter(unique_files.values())
        for project_name, count in by_project.most_common():
            observations.append(
                f"{count} fichiers sont présents uniquement dans {project_name}."
            )

    generated_by_project: dict[str, list[str]] = {}
    for project in projects:
        generated = [
            entry.path
            for entry in project.files
            if entry.kind == "directory" and entry.path.strip("/") in GENERATED_DIRS
        ]
        if generated:
            generated_by_project[project.name] = generated
    for project_name, names in generated_by_project.items():
        observations.append(
            f"Répertoires générés observés dans {project_name} : {', '.join(names)}"
        )

    large_files: list[tuple[str, str, int]] = []
    for project in projects:
        for entry in project.files:
            if entry.kind == "file" and entry.size >= LARGE_FILE_BYTES:
                large_files.append((project.name, entry.path, entry.size))
    for project_name, path, size in sorted(large_files, key=lambda item: item[2], reverse=True):
        observations.append(
            f"Fichier volumineux observé dans {project_name} : {path} ({size_label(size)})"
        )

    return observations


def print_file_matrix(projects: list[ProjectReport]) -> None:
    path_projects: dict[str, set[str]] = defaultdict(set)
    for project in projects:
        for entry in project.files:
            path_projects[entry.path].add(project.name)

    total = len(projects)
    rare = sorted(
        (path, names)
        for path, names in path_projects.items()
        if len(names) == 1
    )
    frequent = sorted(
        (path, names)
        for path, names in path_projects.items()
        if 1 < len(names) < total
    )

    print("Fichiers et répertoires observés")
    print("================================")
    if rare:
        print()
        print("Présents dans un seul projet")
        print("----------------------------")
        for path, names in rare[:40]:
            print(f"{next(iter(names))} : {path}")
        if len(rare) > 40:
            print(f"... {len(rare) - 40} autres éléments")

    if frequent:
        print()
        print("Présents dans plusieurs projets, mais pas tous")
        print("----------------------------------------------")
        for path, names in frequent[:40]:
            names_label = ", ".join(sorted(names))
            print(f"{path} : {len(names)} projets ({names_label})")
        if len(frequent) > 40:
            print(f"... {len(frequent) - 40} autres éléments")
    print()


def print_report(projects: list[ProjectReport], root: Path) -> None:
    print(f"DTLaudit {VERSION}")
    print("Rapport comparatif entre projets")
    print("Aucune modification effectuée")
    print()
    print(f"Racine : {root}")
    print(f"Projets scannés : {len(projects)}")
    print()

    print_summary_table(projects)

    for project in projects:
        print_project_block(project)

    print("Observations remarquables")
    print("=========================")
    for observation in notable_observations(projects):
        print(f"- {observation}")
    print()

    print_file_matrix(projects)


def build_text_report(projects: list[ProjectReport], root: Path) -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        print_report(projects, root)
    return buffer.getvalue()


def build_html_report(projects: list[ProjectReport], root: Path) -> str:
    title = f"DTLaudit {VERSION}"
    text_report = build_text_report(projects, root)
    escaped_report = html.escape(text_report)
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 0;
      background: #f5f5f2;
      color: #242424;
      font-family: Arial, Helvetica, sans-serif;
    }}
    main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 32px 24px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 700;
    }}
    .meta {{
      margin: 0 0 24px;
      color: #555;
      font-size: 14px;
    }}
    pre {{
      margin: 0;
      padding: 20px;
      overflow: auto;
      background: #ffffff;
      border: 1px solid #d8d8d2;
      border-radius: 8px;
      line-height: 1.45;
      font-family: Consolas, "Courier New", monospace;
      font-size: 14px;
      white-space: pre-wrap;
    }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(title)}</h1>
    <p class="meta">Rapport comparatif entre projets - aucune modification effectuée</p>
    <pre>{escaped_report}</pre>
  </main>
</body>
</html>
"""


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def print_if_available(message: str, stream: Any | None = None, end: str = "\n") -> None:
    target = stream if stream is not None else sys.stdout
    if target is None:
        return
    print(message, file=target, end=end)


def output_path(value: str, root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def serialize(projects: list[ProjectReport], root: Path) -> dict[str, Any]:
    return {
        "tool": "DTLaudit",
        "version": VERSION,
        "mode": "rapport comparatif",
        "root": str(root),
        "projects": [asdict(project) for project in projects],
        "observations": notable_observations(projects),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"DTLaudit {VERSION}")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--project", help="Projet local à scanner")
    target.add_argument("--suite", help="Répertoire contenant plusieurs projets")
    parser.add_argument(
        "--json",
        nargs="?",
        const=DEFAULT_JSON_REPORT,
        help="Écrire aussi un rapport JSON",
    )
    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Ne pas interroger GitHub avec gh",
    )
    parser.add_argument(
        "--txt",
        "--text",
        dest="text",
        nargs="?",
        const=DEFAULT_TXT_REPORT,
        help="Écrire aussi un rapport texte",
    )
    parser.add_argument(
        "--html",
        nargs="?",
        const=DEFAULT_HTML_REPORT,
        help="Écrire aussi un rapport HTML",
    )
    return parser.parse_args()


def show_missing_parameters_dialog() -> None:
    message = textwrap.dedent(
        f"""\
        DTLaudit {VERSION}

        Cet outil doit etre lance avec un dossier a auditer.

        Exemples :
          DTLaudit.exe --suite "C:\\chemin\\vers\\outils"
          DTLaudit.exe --project "C:\\chemin\\vers\\un-projet"

        Astuce : utilisez un raccourci Windows qui ajoute --suite ou --project dans la cible.
        """
    )
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showwarning("DTLaudit - dossier requis", message, parent=root)
        root.destroy()
    except Exception:
        print_if_available(message, sys.stderr)


def main() -> int:
    if len(sys.argv) == 1:
        show_missing_parameters_dialog()
        return 2

    args = parse_args()
    github_enabled = not args.no_github
    html_output = args.html or DEFAULT_HTML_REPORT

    if args.project:
        root = Path(args.project).resolve()
        project_paths = [root]
    else:
        root = Path(args.suite).resolve()
        project_paths = discover_projects(root)

    projects = [scan_project(path, github_enabled) for path in project_paths]
    serialized_report = serialize(projects, root)

    text_report = None
    if args.text or html_output:
        text_report = build_text_report(projects, root)

    if args.json:
        json_path = output_path(args.json, DEFAULT_OUTPUT_DIR)
        write_text_file(
            json_path,
            json.dumps(serialized_report, ensure_ascii=False, indent=2),
        )
        print_if_available(f"Rapport JSON écrit : {json_path}", sys.stderr)

    if args.text:
        txt_path = output_path(args.text, DEFAULT_OUTPUT_DIR)
        write_text_file(txt_path, text_report or build_text_report(projects, root))
        print_if_available(f"Rapport TXT écrit : {txt_path}", sys.stderr)

    if html_output:
        html_path = output_path(html_output, DEFAULT_OUTPUT_DIR)
        write_text_file(html_path, build_html_report(projects, root))
        print_if_available(f"Rapport HTML écrit : {html_path}", sys.stderr)

    print_if_available(
        text_report if text_report is not None else build_text_report(projects, root),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
