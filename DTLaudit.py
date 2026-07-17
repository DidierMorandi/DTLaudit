#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""DTLaudit - rapport comparatif en lecture seule, avec interface console."""

from __future__ import annotations

import argparse
import contextlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_NAME = "DTLaudit"
VERSION = "v1.1-0"
APP_SUITE = "Un outil de la suite NetDTL"
APP_WEBSITE = "www.netdtl.com"
APP_SUBTITLE = "Audit comparatif de projets en lecture seule"
LOGO_LINES = (
    "┌─┬─┬─┬─┬─┬─┐",
    "│N│e│t│D│T│L│",
    "└─┴─┴─┴─┴─┴─┘",
)
ANSI_LOGO = "\033[38;2;255;255;255;48;2;2;1;183m"
ANSI_BOLD = "\033[1m"
ANSI_RED = "\033[38;2;255;0;0m"
ANSI_GREEN = "\033[38;2;0;255;0m"
ANSI_RESET = "\033[0m"
DEFAULT_OUTPUT_DIR = application_dir()
DEFAULT_JSON_REPORT = "DTLaudit_rapport.json"
DEFAULT_TXT_REPORT = "DTLaudit_rapport.txt"
DEFAULT_HTML_REPORT = "DTLaudit_rapport.html"
XAMPP_JSON_DIR = Path(r"C:\xampp\htdocs\DTLaudit")
GENERATED_DIRS = {"build", "dist", "__pycache__", ".pytest_cache", ".mypy_cache"}
LOCAL_DIRS = {"logs", "tmp", "temp"}
TEMP_SUFFIXES = {".tmp", ".bak", ".old", ".log", ".pyc", ".pyo"}
LARGE_FILE_BYTES = 5 * 1024 * 1024
PROJECT_FILE_PATTERNS = (
    "*.py",
    "*.ps1",
    "*.vbs",
    "*.bat",
    "*.cmd",
    "README*",
)
QUIET = False
DEBUG = False


def clear_console() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def configure_console_streams() -> None:
    """Garantit l'affichage du français et du logo, même avec une sortie redirigée."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def console_width() -> int:
    try:
        return max(76, min(shutil.get_terminal_size().columns, 160))
    except OSError:
        return 100


def supports_color() -> bool:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return False
    if os.name != "nt":
        return os.environ.get("TERM", "").casefold() != "dumb"
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if handle in (0, -1) or not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError, ValueError):
        return False


def styled(text: str, ansi_code: str, color: bool | None = None) -> str:
    enabled = supports_color() if color is None else color
    return f"{ansi_code}{text}{ANSI_RESET}" if enabled else text


def brand_header_lines(screen_width: int, color: bool = False) -> list[str]:
    left = (f"{APP_NAME} {VERSION}", APP_SUITE, APP_WEBSITE)
    gap = 3
    logo_width = len(LOGO_LINES[0])
    left_width = max(0, screen_width - logo_width - gap)
    result: list[str] = []
    for index, (text, logo) in enumerate(zip(left, LOGO_LINES)):
        text = text[:left_width]
        padding = " " * (left_width - len(text))
        visible_text = (
            f"{ANSI_BOLD}{text}{ANSI_RESET}{padding}"
            if color and index == 0
            else f"{text}{padding}"
        )
        visible_logo = f"{ANSI_LOGO}{logo}{ANSI_RESET}" if color else logo
        result.append(f"{visible_text}{' ' * gap}{visible_logo}")
    result.extend(("", APP_SUBTITLE, "", "=" * screen_width))
    return result


def show_application_header() -> None:
    clear_console()
    print("\n".join(brand_header_lines(console_width(), supports_color())))


def validated_choice(prompt: str, choices: set[str]) -> str:
    while True:
        value = input(prompt).strip().upper()
        if value in choices:
            return value
        print(styled("Choix invalide. Saisissez une option proposée.", ANSI_RED))


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "O/n" if default else "o/N"
    while True:
        value = input(f"{prompt} [{suffix}] : ").strip().casefold()
        if not value:
            return default
        if value in {"o", "oui", "y", "yes"}:
            return True
        if value in {"n", "non", "no"}:
            return False
        print(styled("Réponse invalide. Saisissez O ou N.", ANSI_RED))


def console_message(code: str, message: str, *, stream: Any | None = None) -> None:
    """Affiche un message de diagnostic façon DEC/VMS sur stderr par défaut."""
    if QUIET:
        return
    target = stream if stream is not None else sys.stderr
    try:
        print(f"{code}, {message}", file=target)
    except Exception:
        pass


def console_detail(message: str, *, stream: Any | None = None) -> None:
    """Affiche une ligne de détail indentée."""
    if QUIET:
        return
    target = stream if stream is not None else sys.stderr
    try:
        print(f"    {message}", file=target)
    except Exception:
        pass


def command_label(args: list[str]) -> str:
    return " ".join(str(part) for part in args)



def subprocess_window_options() -> dict[str, Any]:
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


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
    pushed_at: str | None = None
    latest_release: str | None = None
    open_prs: int | None = None
    open_issues: int | None = None
    note: str | None = None


# Patterns de suffixes attendus pour le contrôle normatif documentaire.
# La détection est insensible à la casse et basée sur les suffixes de noms de fichiers
# afin de gérer le préfixe variable selon le projet (ex. DTLknowsWhy_Manuel_de_reference.html).
DOC_NORM_ITEMS: list[tuple[str, str]] = [
    ("manuel_ref_fr", "_Manuel_de_reference.html"),
    ("guide_user_fr", "_Guide_Utilisateur.html"),
    ("ref_manual_en", "_Reference_Manual.html"),
    ("user_guide_en", "_User_Guide.html"),
]


@dataclass
class DocAudit:
    manuel_ref_fr: bool = False
    guide_user_fr: bool = False
    ref_manual_en: bool = False
    user_guide_en: bool = False

    def all_present(self) -> bool:
        return all(getattr(self, key) for key, _ in DOC_NORM_ITEMS)

    def count_present(self) -> int:
        return sum(1 for key, _ in DOC_NORM_ITEMS if getattr(self, key))


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
    tool_version: str | None = None
    files: list[FileEntry] = field(default_factory=list)
    git: GitInfo = field(default_factory=GitInfo)
    github: GitHubInfo = field(default_factory=GitHubInfo)
    doc_audit: DocAudit = field(default_factory=DocAudit)


def run_command(args: list[str], cwd: Path, timeout: int = 12) -> tuple[int, str]:
    """Exécute une commande externe et affiche les erreurs en mode console.

    Ancien comportement :
        stderr=subprocess.DEVNULL
    Conséquence :
        les messages Git, gh ou Windows disparaissaient.

    Nouveau comportement :
        stderr=subprocess.PIPE
        les erreurs sont affichées sur stderr, mais ne polluent pas les champs du rapport.
    """
    label = command_label(args)

    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            **subprocess_window_options(),
        )
    except FileNotFoundError:
        console_message(
            "%DTLaudit-E-CMDNOTFOUND",
            f"commande introuvable : {args[0]}",
        )
        console_detail(f"Répertoire courant : {cwd}")
        console_detail(f"Commande : {label}")
        return 1, ""
    except subprocess.TimeoutExpired:
        console_message(
            "%DTLaudit-E-CMDTIMEOUT",
            f"délai dépassé après {timeout} secondes",
        )
        console_detail(f"Répertoire courant : {cwd}")
        console_detail(f"Commande : {label}")
        return 1, ""
    except OSError as exc:
        console_message(
            "%DTLaudit-E-CMDERROR",
            "impossible de lancer une commande externe",
        )
        console_detail(f"Répertoire courant : {cwd}")
        console_detail(f"Commande : {label}")
        console_detail(str(exc))
        return 1, ""

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    if completed.returncode != 0:
        console_message(
            "%DTLaudit-W-CMDFAILED",
            f"commande terminée avec le code {completed.returncode}",
        )
        console_detail(f"Répertoire courant : {cwd}")
        console_detail(f"Commande : {label}")
        if stderr:
            for line in stderr.splitlines():
                console_detail(line)
        elif stdout:
            for line in stdout.splitlines()[:12]:
                console_detail(line)
        else:
            console_detail("Aucun message retourné par la commande.")

        # Important : ne pas retourner stderr ici.
        # Les collecteurs testent le code retour et doivent garder un champ vide en cas d'échec.
        return completed.returncode, ""

    return completed.returncode, stdout


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
            has_project_files = any(
                any(child.glob(pattern)) for pattern in PROJECT_FILE_PATTERNS
            )
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
            "nameWithOwner,url,visibility,defaultBranchRef,pushedAt",
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
    info.pushed_at = data.get("pushedAt")

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


def collect_doc_audit(project: Path, files: list[FileEntry]) -> DocAudit:
    """Vérifie la présence des 4 documents normatifs attendus.

    Les fichiers HTML sont cherchés dans l'ensemble de l'arborescence du projet
    par correspondance de suffixe insensible à la casse.
    Exemple : DTLknowsWhy_Manuel_de_reference.html satisfait le suffixe _Manuel_de_reference.html.
    """
    audit = DocAudit()
    file_paths_lower = [entry.path.lower() for entry in files if entry.kind == "file"]

    suffixes = {
        "manuel_ref_fr": "_manuel_de_reference.html",
        "guide_user_fr": "_guide_utilisateur.html",
        "ref_manual_en": "_reference_manual.html",
        "user_guide_en": "_user_guide.html",
    }
    for key, suffix in suffixes.items():
        for p in file_paths_lower:
            if p.endswith(suffix):
                setattr(audit, key, True)
                break

    return audit


def collect_project_version(project: Path) -> str | None:
    version_file = project / ".dtl_version"
    if version_file.is_file():
        try:
            data = json.loads(version_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}

        display_version = data.get("display_version")
        if isinstance(display_version, str) and display_version.strip():
            return display_version.strip()

        version = data.get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()

    candidate_files = [project / f"{project.name}.py"]
    candidate_files.extend(sorted(project.glob("*.py"), key=lambda item: item.name.lower()))

    for candidate in candidate_files:
        if not candidate.is_file():
            continue
        try:
            content = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = re.search(r'^\s*VERSION\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

    return None


def scan_project(project: Path, github_enabled: bool) -> ProjectReport:
    git = collect_git(project)
    files = collect_files(project)
    return ProjectReport(
        name=project.name,
        path=str(project),
        tool_version=collect_project_version(project),
        files=files,
        git=git,
        github=collect_github(project, git, github_enabled),
        doc_audit=collect_doc_audit(project, files),
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


def project_has_file(project: ProjectReport, filenames: set[str]) -> bool:
    return any(
        entry.path.lower() in filenames
        for entry in project.files
    )


def project_has_readme_en(project: ProjectReport) -> bool:
    return project_has_file(project, {"readme.md", "readme_en.md"})


def project_has_readme_fr(project: ProjectReport) -> bool:
    return project_has_file(project, {"readme_fr.md"})


def project_has_readme(project: ProjectReport) -> bool:
    return project_has_readme_en(project) or project_has_readme_fr(project)
 
def oui_non(value: bool) -> str:
    return "Oui" if value else "Non"


def visibility_label(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized == "public":
        return "public"
    if normalized in {"private", "internal"}:
        return "privé"
    return "-"


def print_summary_table(projects: list[ProjectReport]) -> None:
    rows = []
    for project in sorted(projects, key=lambda item: item.name.lower()):
        rows.append(
            {
                "Projet":   project.name,
                "Version":  project.tool_version or "-",
                "Git":      oui_non(project.git.present),
                "GitHub":   oui_non(project.git.remote_github or project.github.available),
                "Branche":  project.git.branch or "-",
                "Visib.":   visibility_label(project.github.visibility),
                "README En": oui_non(project_has_readme_en(project)),
                "README Fr": oui_non(project_has_readme_fr(project)),
                "RF Fr":    oui_non(project.doc_audit.manuel_ref_fr),
                "UG Fr":    oui_non(project.doc_audit.guide_user_fr),
                "RF En":    oui_non(project.doc_audit.ref_manual_en),
                "UG En":    oui_non(project.doc_audit.user_guide_en),
                "Release":  oui_non(bool(project.github.latest_release)),
                "Modifs":   str(project.git.changed_files or 0),
            }
        )

    columns = ["Projet", "Version", "Git", "GitHub", "Branche", "Visib.", "README En", "README Fr", "RF Fr", "UG Fr", "RF En", "UG En", "Release", "Modifs"]
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
    print("Version :")
    print(f"    {project.tool_version or 'non détectée'}")
    print("README :")
    print(f"    anglais : {present_absent(project_has_readme_en(project))}")
    print(f"    français : {present_absent(project_has_readme_fr(project))}")
    print("Documentation normative :")
    doc_labels = {
        "manuel_ref_fr": "Manuel de référence (FR)",
        "guide_user_fr": "Guide utilisateur (FR)",
        "ref_manual_en": "Reference Manual (EN)",
        "user_guide_en": "User Guide (EN)",
    }
    for key, label in doc_labels.items():
        status = present_absent(getattr(project.doc_audit, key))
        print(f"    {label} : {status}")
    complete = "complète" if project.doc_audit.all_present() else f"{project.doc_audit.count_present()}/{len(DOC_NORM_ITEMS)} présents"
    print(f"    Bilan : {complete}")
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
    readme_en_count = count_projects(project_has_readme_en)
    readme_fr_count = count_projects(project_has_readme_fr)
    observations.append(
        f"README est présent dans {project_count_label(readme_count)} sur {total}."
    )
    observations.append(
        f"README anglais est présent dans {project_count_label(readme_en_count)} sur {total}."
    )
    observations.append(
        f"README français est présent dans {project_count_label(readme_fr_count)} sur {total}."
    )

    # Contrôle normatif documentation
    full_doc_count = count_projects(lambda project: project.doc_audit.all_present())
    observations.append(
        f"Documentation normative complète (4/4) dans {project_count_label(full_doc_count)} sur {total}."
    )
    doc_labels = {
        "manuel_ref_fr": "Manuel de référence (FR)",
        "guide_user_fr": "Guide utilisateur (FR)",
        "ref_manual_en": "Reference Manual (EN)",
        "user_guide_en": "User Guide (EN)",
    }
    for key, label in doc_labels.items():
        missing = [p.name for p in projects if not getattr(p.doc_audit, key)]
        if missing:
            observations.append(
                f"{label} manquant dans : {', '.join(missing)}."
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


def _h(value: str) -> str:
    """Raccourci html.escape."""
    return html.escape(value)


def _yn_cell(value: bool, css_class: str = "") -> str:
    """Cellule <td> Oui/Non colorée."""
    class_suffix = f" {css_class}" if css_class else ""
    if value:
        return f'<td class="yn-yes{class_suffix}">Oui</td>'
    return f'<td class="yn-no{class_suffix}">Non</td>'


def _html_summary_table(projects: list[ProjectReport]) -> str:
    rows = []
    for project in sorted(projects, key=lambda p: p.name.lower()):
        g = project.git
        gh = project.github
        da = project.doc_audit
        rows.append(
            f"<tr>"
            f"<td class='project-name'>{_h(project.name)}</td>"
            f"<td class='tool-version'>{_h(project.tool_version or '-')}</td>"
            f"{_yn_cell(g.present)}"
            f"{_yn_cell(bool(g.remote_github or gh.available), 'github-cell')}"
            f"<td>{_h(g.branch or '-')}</td>"
            f"<td class='visibility'>{_h(visibility_label(gh.visibility))}</td>"
            f"{_yn_cell(project_has_readme_en(project))}"
            f"{_yn_cell(project_has_readme_fr(project))}"
            f"{_yn_cell(da.manuel_ref_fr)}"
            f"{_yn_cell(da.guide_user_fr)}"
            f"{_yn_cell(da.ref_manual_en)}"
            f"{_yn_cell(da.user_guide_en)}"
            f"{_yn_cell(bool(gh.latest_release))}"
            f"<td>{g.changed_files or 0}</td>"
            f"</tr>"
        )
    headers = ["Projet", "Version", "Git", "GitHub", "Branche", "Visib.", "README En", "README Fr", "RF Fr", "UG Fr", "RF En", "UG En", "Release", "Modifs"]
    thead = "".join(f"<th>{h}</th>" for h in headers)
    colgroup = '<colgroup><col class="project-col"><col class="data-col" span="13"></colgroup>'
    tbody = "\n".join(rows)
    return f"<table>\n{colgroup}\n<thead><tr>{thead}</tr></thead>\n<tbody>\n{tbody}\n</tbody>\n</table>"


def _html_project_blocks(projects: list[ProjectReport]) -> str:
    blocks = []
    doc_fields = [
        ("manuel_ref_fr", "Manuel de référence (FR)"),
        ("guide_user_fr", "Guide utilisateur (FR)"),
        ("ref_manual_en", "Reference Manual (EN)"),
        ("user_guide_en", "User Guide (EN)"),
    ]
    for project in projects:
        g = project.git
        gh = project.github
        da = project.doc_audit

        doc_rows = ""
        for key, label in doc_fields:
            doc_rows += f"<tr><td class='lbl'>{_h(label)}</td>{_yn_cell(getattr(da, key))}</tr>\n"

        bilan = "complète" if da.all_present() else f"{da.count_present()}/{len(DOC_NORM_ITEMS)} présents"

        git_rows = f"<tr><td class='lbl'>Présent</td>{_yn_cell(g.present)}</tr>\n"
        if g.present:
            git_rows += (
                f"<tr><td class='lbl'>Branche</td><td>{_h(g.branch or 'non détectée')}</td></tr>\n"
                f"<tr><td class='lbl'>Remote GitHub</td>{_yn_cell(g.remote_github)}</tr>\n"
                f"<tr><td class='lbl'>Modifications locales</td><td>{g.changed_files or 0}</td></tr>\n"
                f"<tr><td class='lbl'>Tags</td><td>{g.tags_count or 0}</td></tr>\n"
            )

        if gh.available:
            gh_rows = (
                f"<tr><td class='lbl'>Dépôt</td><td>{_h(gh.repository or 'non détecté')}</td></tr>\n"
                f"<tr><td class='lbl'>Visibilité</td><td>{_h(gh.visibility or 'non détectée')}</td></tr>\n"
                f"<tr><td class='lbl'>Release récente</td><td>{_h(gh.latest_release or 'absente')}</td></tr>\n"
                f"<tr><td class='lbl'>Pull requests ouvertes</td><td>{gh.open_prs if gh.open_prs is not None else 'non détectées'}</td></tr>\n"
                f"<tr><td class='lbl'>Issues ouvertes</td><td>{gh.open_issues if gh.open_issues is not None else 'non détectées'}</td></tr>\n"
            )
        else:
            gh_rows = f"<tr><td class='lbl'>Statut</td><td>{_h(gh.note or 'non disponible')}</td></tr>\n"

        blocks.append(f"""
<div class="project-block">
  <h2>{_h(project.name)}</h2>
  <h3>Version</h3>
  <table class="inner">
    <tr><td class='lbl'>Version outil</td><td>{_h(project.tool_version or 'non détectée')}</td></tr>
  </table>
  <h3>README</h3>
  <table class="inner">
    <tr><td class='lbl'>Anglais</td>{_yn_cell(project_has_readme_en(project))}</tr>
    <tr><td class='lbl'>Français</td>{_yn_cell(project_has_readme_fr(project))}</tr>
  </table>
  <h3>Documentation normative</h3>
  <table class="inner">
    {doc_rows}
    <tr><td class='lbl'>Bilan</td><td>{_h(bilan)}</td></tr>
  </table>
  <h3>Git</h3>
  <table class="inner">
    {git_rows}
  </table>
  <h3>GitHub</h3>
  <table class="inner">
    {gh_rows}
  </table>
</div>""")
    return "\n".join(blocks)


def _html_observations(projects: list[ProjectReport]) -> str:
    items = notable_observations(projects)
    if not items:
        return "<p>Aucune observation.</p>"
    lis = "\n".join(f"<li>{_h(obs)}</li>" for obs in items)
    return f"<ul>\n{lis}\n</ul>"


def _html_file_matrix(projects: list[ProjectReport]) -> str:
    path_projects: dict[str, set[str]] = defaultdict(set)
    for project in projects:
        for entry in project.files:
            path_projects[entry.path].add(project.name)

    total = len(projects)
    rare = sorted((p, n) for p, n in path_projects.items() if len(n) == 1)
    frequent = sorted((p, n) for p, n in path_projects.items() if 1 < len(n) < total)

    sections = []
    if rare:
        rows = ""
        for path, names in rare[:40]:
            rows += f"<tr><td>{_h(next(iter(names)))}</td><td>{_h(path)}</td></tr>\n"
        if len(rare) > 40:
            rows += f"<tr><td colspan='2' class='muted'>... {len(rare) - 40} autres éléments</td></tr>\n"
        sections.append(f"<h3>Présents dans un seul projet</h3><table class='inner'><tr><th>Projet</th><th>Chemin</th></tr>\n{rows}</table>")

    if frequent:
        rows = ""
        for path, names in frequent[:40]:
            names_label = ", ".join(sorted(names))
            rows += f"<tr><td>{_h(path)}</td><td>{len(names)}</td><td>{_h(names_label)}</td></tr>\n"
        if len(frequent) > 40:
            rows += f"<tr><td colspan='3' class='muted'>... {len(frequent) - 40} autres éléments</td></tr>\n"
        sections.append(f"<h3>Présents dans plusieurs projets, mais pas tous</h3><table class='inner'><tr><th>Chemin</th><th>Nb</th><th>Projets</th></tr>\n{rows}</table>")

    return "\n".join(sections) if sections else "<p>Aucun fichier à signaler.</p>"


def build_html_report(projects: list[ProjectReport], root: Path) -> str:
    import datetime
    title = f"DTLaudit {VERSION}"
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    summary_table = _html_summary_table(projects)
    project_blocks = _html_project_blocks(projects)
    observations = _html_observations(projects)
    file_matrix = _html_file_matrix(projects)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_h(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:       #0b0d0f;
      --surface:  #131619;
      --surface2: #1a1e23;
      --border:   rgba(255,255,255,0.07);
      --border2:  rgba(255,255,255,0.12);
      --text:     #e8eaed;
      --muted:    #7a8290;
      --accent:   #38bdf8;
      --yes:      #4ade80;
      --no:       #ff7a45;
    }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      line-height: 1.7;
      min-height: 100vh;
    }}

    .grid-bg {{
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
      z-index: 0;
    }}

    header {{
      position: relative;
      z-index: 1;
      padding: 48px 48px 36px;
      max-width: 1200px;
      margin: 0 auto;
      border-bottom: 0.5px solid var(--border2);
    }}

    .header-tag {{
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 12px;
    }}

    h1 {{
      font-family: 'Syne', sans-serif;
      font-size: 36px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
      margin-bottom: 6px;
    }}

    .meta {{
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }}

    main {{
      position: relative;
      z-index: 1;
      max-width: 1200px;
      margin: 0 auto;
      padding: 40px 48px 64px;
    }}

    section {{ margin-bottom: 48px; }}

    h2 {{
      font-family: 'Syne', sans-serif;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 0.5px solid var(--border2);
    }}

    h3 {{
      font-size: 11px;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--muted);
      margin: 16px 0 6px;
    }}

    /* Tables */
    table {{
      width: 100%;
      table-layout: fixed;
      border-collapse: collapse;
      font-size: 13px;
    }}
    col.project-col {{ width: 180px; }}
    col.data-col {{ width: 68px; }}
    table.inner {{
      width: auto;
      table-layout: auto;
      min-width: 360px;
    }}
    thead tr {{
      border-bottom: 0.5px solid var(--border2);
    }}
    th {{
      font-size: 10px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
      padding: 0 16px 10px 0;
      font-weight: 400;
      text-align: left;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      background: transparent;
      border: none;
    }}
    td {{
      padding: 8px 16px 8px 0;
      border-bottom: 0.5px solid var(--border);
      vertical-align: middle;
      color: var(--text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    td.project-name {{
      font-weight: 600;
    }}
    td.tool-version {{
    }}
    td.visibility {{
    }}
    td.github-cell {{
    }}
    tr:last-child td {{ border-bottom: none; }}
    td.lbl {{
      color: var(--muted);
      white-space: nowrap;
      width: 220px;
      font-size: 12px;
    }}
    .yn-yes {{
      color: var(--yes);
      font-weight: 500;
      text-align: center;
      padding-right: 8px;
      width: 46px;
    }}
    .yn-no {{
      color: var(--no);
      font-weight: 500;
      text-align: center;
      padding-right: 8px;
      width: 46px;
    }}
    .muted-cell {{ color: var(--muted); font-style: italic; }}

    /* Blocs projet */
    .project-block {{
      background: var(--surface);
      border: 0.5px solid var(--border2);
      border-left: 2px solid var(--accent);
      padding: 20px 24px;
      margin-bottom: 12px;
    }}
    .project-block h2 {{
      font-family: 'Syne', sans-serif;
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.01em;
      text-transform: none;
      color: var(--accent);
      border: none;
      padding: 0;
      margin-bottom: 12px;
    }}

    /* Observations */
    ul {{
      padding-left: 18px;
      line-height: 2;
    }}
    li {{ color: var(--text); font-size: 13px; }}

    footer {{
      position: relative;
      z-index: 1;
      border-top: 0.5px solid var(--border2);
      padding: 20px 48px;
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--muted);
      letter-spacing: 0.05em;
    }}
  </style>
</head>
<body>
  <div class="grid-bg"></div>
  <header>
    <p class="header-tag">DTL Projects &bull; Rapport d&rsquo;audit</p>
    <h1>{_h(title)}</h1>
    <p class="meta">Racine&nbsp;: {_h(str(root))} &bull; {len(projects)} projet(s) scann&eacute;(s) &bull; aucune modification effectu&eacute;e</p>
  </header>
  <main>
    <section>
      <h2>Synth&egrave;se</h2>
      {summary_table}
    </section>

    <section>
      <h2>D&eacute;tail par projet</h2>
      {project_blocks}
    </section>

    <section>
      <h2>Observations remarquables</h2>
      {observations}
    </section>

    <section>
      <h2>Fichiers et r&eacute;pertoires observ&eacute;s</h2>
      {file_matrix}
    </section>
  </main>
  <footer>
    <span>{_h(title)} &mdash; {generated}</span>
    <span>aucune modification effectu&eacute;e</span>
  </footer>
</body>
</html>
"""


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_json_to_xampp(
    serialized_report: dict[str, Any],
    source_path: Path | None = None,
) -> None:
    try:
        if not XAMPP_JSON_DIR.is_dir():
            return

        target_path = XAMPP_JSON_DIR / DEFAULT_JSON_REPORT
        if source_path is not None and source_path.is_file():
            shutil.copy2(source_path, target_path)
            return

        write_text_file(
            target_path,
            json.dumps(serialized_report, ensure_ascii=False, indent=2),
        )
    except OSError:
        return


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

class DTLArgumentParser(argparse.ArgumentParser):

    def error(self, message):

        print()
        print("%DTLaudit-E-SYNTAX")
        print()
        print("ERREUR :")
        print(f"        {message}")
        print()
        print("DESCRIPTION :")
        print("        DTLaudit compare un ou plusieurs projets et génère un rapport HTML, TXT ou JSON.")
        print()
        print("SYNTAXE :")
        print("        python DTLaudit --project <répertoire>")
        print("        python DTLaudit --suite <répertoire>")
        print()
        print("OPTIONS :")
        print("        --project      Analyse un seul projet.")
        print("        --suite        Analyse plusieurs projets.")
        print("        --json         Génère un rapport JSON.")
        print("        --txt          Génère un rapport texte.")
        print("        --html         Génère un rapport HTML.")
        print("        --no-github    N'interroge pas GitHub.")
        print("        --debug        Affiche les informations de diagnostic.")
        print("        --quiet        N'affiche que les erreurs et les avertissements.")
        print()
        print("EXEMPLES :")
        print("        python DTLaudit --project C:\\MesProjets\\GitDTL")
        print("        python DTLaudit --suite C:\\MesProjets")
        print("        python DTLaudit --suite C:\\MesProjets --json --html")
        print()

        raise SystemExit(2)

def parse_args() -> argparse.Namespace:
    parser = DTLArgumentParser(
        description=f"DTLaudit {VERSION}",
        add_help=False,
        usage="python dtlaudit.py (--project <projet> | --suite <répertoire>) [options]"
    )
    target = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Affiche cette aide et quitte"
)
    target.add_argument("--project", help="Analyse un projet unique")
    target.add_argument("--suite", help="Analyse un répertoire contenant plusieurs projets")
    parser.add_argument(
        "--json",
        nargs="?",
        const=DEFAULT_JSON_REPORT,
        help="Produire un rapport au format JSON",
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
        help="Produire un rapport au format texte",
    )
    parser.add_argument(
        "--html",
        nargs="?",
        const=DEFAULT_HTML_REPORT,
        help="Produire un rapport au format HTML",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Ne pas afficher les messages de diagnostic console",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Affiche des informations techniques détaillées en cas d'erreur inattendue",
    )
    return parser.parse_args()


def choose_start_mode() -> str:
    show_application_header()
    print("\nChoisissez un mode :\n")
    print("1  Auditer un dossier contenant plusieurs projets")
    print("2  Auditer un seul projet")
    print("Q : Quitter")
    return validated_choice("\nVotre choix : ", {"1", "2", "Q"})


def choose_directory(mode: str) -> Path | None:
    """Ouvre le sélecteur de dossiers natif, comme DTLi18n."""
    title = (
        "Choisir le dossier contenant les projets"
        if mode == "suite"
        else "Choisir le dossier du projet à auditer"
    )
    root = None
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.update_idletasks()
        selected = filedialog.askdirectory(parent=root, title=title, mustexist=True)
        return Path(selected).resolve() if selected else None
    except Exception as exc:
        print(styled(f"Impossible d'ouvrir le sélecteur de dossiers : {exc}", ANSI_RED))
        input("\nAppuyer sur <Return> pour revenir au menu principal.")
        return None
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def interactive_args(mode: str, path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        project=str(path) if mode == "project" else None,
        suite=str(path) if mode == "suite" else None,
        json=None,
        text=None,
        html=None,
        no_github=False,
        quiet=False,
        debug=False,
        interactive=True,
    )


def open_report(report_path: Path) -> None:
    try:
        if os.name == "nt":
            os.startfile(report_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(report_path)])
        else:
            subprocess.Popen(["xdg-open", str(report_path)])
    except OSError as exc:
        print(styled(f"Impossible d'ouvrir le rapport : {exc}", ANSI_RED))


def run_audit(args: argparse.Namespace) -> tuple[int, Path | None]:
    global QUIET, DEBUG

    QUIET = bool(getattr(args, "quiet", False))
    DEBUG = bool(getattr(args, "debug", False))

    github_enabled = not args.no_github
    html_output = args.html or DEFAULT_HTML_REPORT

    console_message("%DTLaudit-I-START", f"DTLaudit {VERSION} démarre")

    if args.project:
        root = Path(args.project).resolve()
        if not root.is_dir():
            console_message("%DTLaudit-E-NOTFOUND", f"dossier introuvable : {root}")
            return 2, None
        console_message("%DTLaudit-I-TARGET", f"projet unique : {root}")
        project_paths = [root]
    else:
        root = Path(args.suite).resolve()
        if not root.is_dir():
            console_message("%DTLaudit-E-NOTFOUND", f"dossier introuvable : {root}")
            return 2, None
        console_message("%DTLaudit-I-TARGET", f"suite de projets : {root}")
        project_paths = discover_projects(root)
        console_message("%DTLaudit-I-DISCOVER", f"{len(project_paths)} projet(s) détecté(s)")

    projects = []
    for index, path in enumerate(project_paths, start=1):
        console_message("%DTLaudit-I-SCAN", f"{index}/{len(project_paths)} {path.name}")
        projects.append(scan_project(path, github_enabled))

    if not projects:
        console_message("%DTLaudit-W-NOPROJECT", "aucun projet détecté")

    serialized_report = serialize(projects, root)

    text_report = None
    json_path = None
    html_path = None
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

    copy_json_to_xampp(serialized_report, json_path)

    print_if_available(
        text_report if text_report is not None else build_text_report(projects, root),
        end="",
    )
    console_message("%DTLaudit-I-DONE", "audit terminé")
    return 0, html_path


def run_interactive() -> int:
    while True:
        choice = choose_start_mode()
        if choice == "Q":
            return 0
        mode = "suite" if choice == "1" else "project"
        path = choose_directory(mode)
        if path is None:
            continue

        show_application_header()
        print(f"\nDossier : {styled(str(path), ANSI_GREEN)}")
        print("L'audit démarre. Aucun fichier du projet ne sera modifié.\n")
        code, report_path = run_audit(interactive_args(mode, path))

        if code == 0 and report_path is not None:
            print(f"\nRapport HTML : {styled(str(report_path), ANSI_GREEN)}")
            if ask_yes_no("Ouvrir le rapport maintenant ?", True):
                open_report(report_path)
        input("\nAppuyer sur <Return> pour revenir au menu principal.")


def main() -> int:
    configure_console_streams()
    if len(sys.argv) == 1:
        return run_interactive()
    args = parse_args()
    code, _ = run_audit(args)
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console_message("%DTLaudit-F-ABORT", "interruption par l'utilisateur")
        raise SystemExit(130)
    except Exception as exc:
        console_message("%DTLaudit-F-ABORT", "erreur Python inattendue")
        console_detail(str(exc))
        if DEBUG:
            traceback.print_exc()
        else:
            console_detail("Relancer avec --debug pour afficher la pile Python complète.")
        raise SystemExit(1)
