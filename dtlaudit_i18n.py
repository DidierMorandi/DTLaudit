"""Small, explicit FR/EN catalogue for DTLaudit user-facing text."""

from __future__ import annotations

import os
from typing import Any


SUPPORTED_LANGUAGES = ("fr", "en")
_language = "fr"


TRANSLATIONS: dict[str, dict[str, str]] = {
    "app.suite": {"fr": "Un outil de la suite NetDTL", "en": "A tool from the NetDTL suite"},
    "app.subtitle": {"fr": "Audit comparatif de projets en lecture seule", "en": "Read-only comparative project audit"},
    "common.yes": {"fr": "oui", "en": "yes"},
    "common.no": {"fr": "non", "en": "no"},
    "common.yes_cap": {"fr": "Oui", "en": "Yes"},
    "common.no_cap": {"fr": "Non", "en": "No"},
    "common.present": {"fr": "présent", "en": "present"},
    "common.absent": {"fr": "absent", "en": "absent"},
    "common.complete": {"fr": "complète", "en": "complete"},
    "common.not_detected": {"fr": "non détecté", "en": "not detected"},
    "common.not_detected_f": {"fr": "non détectée", "en": "not detected"},
    "common.not_detected_plural": {"fr": "non détectées", "en": "not detected"},
    "common.not_available": {"fr": "non disponible", "en": "unavailable"},
    "common.none_f": {"fr": "absente", "en": "none"},
    "common.public": {"fr": "public", "en": "public"},
    "common.private": {"fr": "privé", "en": "private"},
    "common.invalid_choice": {"fr": "Choix invalide. Saisissez une option proposée.", "en": "Invalid choice. Enter one of the available options."},
    "common.invalid_yes_no": {"fr": "Réponse invalide. Saisissez O ou N.", "en": "Invalid answer. Enter Y or N."},
    "common.yes_no_default_yes": {"fr": "O/n", "en": "Y/n"},
    "common.yes_no_default_no": {"fr": "o/N", "en": "y/N"},
    "unit.mb": {"fr": "Mo", "en": "MB"},
    "unit.kb": {"fr": "Ko", "en": "KB"},
    "unit.byte": {"fr": "o", "en": "B"},
    "count.project.one": {"fr": "{count} projet", "en": "{count} project"},
    "count.project.other": {"fr": "{count} projets", "en": "{count} projects"},
    "count.items.more": {"fr": "... {count} autres éléments", "en": "... {count} more items"},
    "label.project": {"fr": "Projet", "en": "Project"},
    "label.projects": {"fr": "Projets", "en": "Projects"},
    "label.version": {"fr": "Version", "en": "Version"},
    "label.branch": {"fr": "Branche", "en": "Branch"},
    "label.visibility_short": {"fr": "Visib.", "en": "Visib."},
    "label.visibility": {"fr": "Visibilité", "en": "Visibility"},
    "label.changes": {"fr": "Modifs", "en": "Changes"},
    "label.local_changes": {"fr": "Modifications locales", "en": "Local changes"},
    "label.repository": {"fr": "Dépôt", "en": "Repository"},
    "label.recent_release": {"fr": "Release récente", "en": "Latest release"},
    "label.open_prs": {"fr": "Pull requests ouvertes", "en": "Open pull requests"},
    "label.open_issues": {"fr": "Issues ouvertes", "en": "Open issues"},
    "label.status": {"fr": "Statut", "en": "Status"},
    "label.summary": {"fr": "Synthèse", "en": "Summary"},
    "label.root": {"fr": "Racine", "en": "Root"},
    "label.scanned_projects": {"fr": "Projets scannés", "en": "Projects scanned"},
    "label.notable_observations": {"fr": "Observations remarquables", "en": "Notable observations"},
    "label.files_observed": {"fr": "Fichiers et répertoires observés", "en": "Observed files and directories"},
    "label.single_project_items": {"fr": "Présents dans un seul projet", "en": "Present in only one project"},
    "label.some_project_items": {"fr": "Présents dans plusieurs projets, mais pas tous", "en": "Present in several projects, but not all"},
    "label.path": {"fr": "Chemin", "en": "Path"},
    "label.count_short": {"fr": "Nb", "en": "Count"},
    "label.english": {"fr": "anglais", "en": "English"},
    "label.french": {"fr": "français", "en": "French"},
    "label.english_cap": {"fr": "Anglais", "en": "English"},
    "label.french_cap": {"fr": "Français", "en": "French"},
    "label.normative_docs": {"fr": "Documentation normative", "en": "Normative documentation"},
    "label.assessment": {"fr": "Bilan", "en": "Assessment"},
    "label.tool_version": {"fr": "Version outil", "en": "Tool version"},
    "doc.reference_fr": {"fr": "Manuel de référence (FR)", "en": "Reference Manual (FR)"},
    "doc.user_guide_fr": {"fr": "Guide utilisateur (FR)", "en": "User Guide (FR)"},
    "doc.reference_en": {"fr": "Reference Manual (EN)", "en": "Reference Manual (EN)"},
    "doc.user_guide_en": {"fr": "User Guide (EN)", "en": "User Guide (EN)"},
    "report.comparative": {"fr": "Rapport comparatif entre projets", "en": "Comparative project report"},
    "report.read_only": {"fr": "Aucune modification effectuée", "en": "No changes made"},
    "report.complete_count": {"fr": "{count}/{total} présents", "en": "{count}/{total} present"},
    "report.projects_in_path": {"fr": "{count} projets ({names})", "en": "{count} projects ({names})"},
    "report.no_observation": {"fr": "Aucune observation.", "en": "No observations."},
    "report.no_file": {"fr": "Aucun fichier à signaler.", "en": "No files to report."},
    "report.html_tagline": {"fr": "DTL Projects · Rapport d’audit", "en": "DTL Projects · Audit report"},
    "report.html_meta": {"fr": "Racine : {root} · {count} projet(s) scanné(s) · aucune modification effectuée", "en": "Root: {root} · {count} project(s) scanned · no changes made"},
    "report.project_details": {"fr": "Détail par projet", "en": "Project details"},
    "github.not_queried": {"fr": "non interrogé", "en": "not queried"},
    "github.gh_unavailable": {"fr": "commande gh non disponible", "en": "gh command unavailable"},
    "github.repo_not_detected": {"fr": "dépôt GitHub non détecté", "en": "GitHub repository not detected"},
    "github.unreadable_response": {"fr": "réponse GitHub non lisible", "en": "unreadable GitHub response"},
    "observation.readme": {"fr": "README est présent dans {count} sur {total}.", "en": "A README is present in {count} out of {total}."},
    "observation.readme_en": {"fr": "README anglais est présent dans {count} sur {total}.", "en": "An English README is present in {count} out of {total}."},
    "observation.readme_fr": {"fr": "README français est présent dans {count} sur {total}.", "en": "A French README is present in {count} out of {total}."},
    "observation.docs_complete": {"fr": "Documentation normative complète (4/4) dans {count} sur {total}.", "en": "Complete normative documentation (4/4) in {count} out of {total}."},
    "observation.doc_missing": {"fr": "{label} manquant dans : {projects}.", "en": "{label} missing from: {projects}."},
    "observation.git": {"fr": "Git est présent dans {count} sur {total}.", "en": "Git is present in {count} out of {total}."},
    "observation.github_remote": {"fr": "Remote GitHub est présent dans {count} sur {total}.", "en": "A GitHub remote is present in {count} out of {total}."},
    "observation.github_status": {"fr": "Status GitHub disponible dans {count} sur {total}.", "en": "GitHub status is available in {count} out of {total}."},
    "observation.branch": {"fr": "Branche {branch} observée dans {count} sur {total}.", "en": "Branch {branch} found in {count} out of {total}."},
    "observation.unique_files": {"fr": "{count} fichiers sont présents uniquement dans {project}.", "en": "{count} files are present only in {project}."},
    "observation.generated_dirs": {"fr": "Répertoires générés observés dans {project} : {names}", "en": "Generated directories found in {project}: {names}"},
    "observation.large_file": {"fr": "Fichier volumineux observé dans {project} : {path} ({size})", "en": "Large file found in {project}: {path} ({size})"},
    "cli.help": {"fr": "Affiche cette aide et quitte", "en": "Show this help message and exit"},
    "cli.project": {"fr": "Analyse un projet unique", "en": "Audit a single project"},
    "cli.suite": {"fr": "Analyse un répertoire contenant plusieurs projets", "en": "Audit a directory containing several projects"},
    "cli.json": {"fr": "Produire un rapport au format JSON", "en": "Write a JSON report"},
    "cli.no_github": {"fr": "Ne pas interroger GitHub avec gh", "en": "Do not query GitHub with gh"},
    "cli.text": {"fr": "Produire un rapport au format texte", "en": "Write a text report"},
    "cli.html": {"fr": "Produire un rapport au format HTML", "en": "Write an HTML report"},
    "cli.quiet": {"fr": "Ne pas afficher les messages de diagnostic console", "en": "Hide console diagnostic messages"},
    "cli.debug": {"fr": "Affiche des informations techniques détaillées en cas d'erreur inattendue", "en": "Show detailed technical information after an unexpected error"},
    "cli.lang": {"fr": "Langue de l'interface (fr ou en)", "en": "Interface language (fr or en)"},
    "cli.usage": {"fr": "python dtlaudit.py (--project <projet> | --suite <répertoire>) [options]", "en": "python dtlaudit.py (--project <project> | --suite <directory>) [options]"},
    "cli.error": {"fr": "ERREUR :", "en": "ERROR:"},
    "cli.error_target_required": {"fr": "une des options --project ou --suite est obligatoire", "en": "one of --project or --suite is required"},
    "cli.error_argument_value": {"fr": "l'option {argument} attend une valeur", "en": "argument {argument}: expected one value"},
    "cli.error_invalid_choice": {"fr": "valeur incorrecte pour {argument} : {value} (choisir parmi {choices})", "en": "invalid value for {argument}: {value} (choose from {choices})"},
    "cli.error_unrecognized": {"fr": "option(s) non reconnue(s) : {arguments}", "en": "unrecognized argument(s): {arguments}"},
    "cli.description": {"fr": "DESCRIPTION :", "en": "DESCRIPTION:"},
    "cli.description_text": {"fr": "        DTLaudit compare un ou plusieurs projets et génère un rapport HTML, TXT ou JSON.", "en": "        DTLaudit compares one or more projects and writes an HTML, TXT or JSON report."},
    "cli.syntax": {"fr": "SYNTAXE :", "en": "USAGE:"},
    "cli.syntax_project": {"fr": "        python DTLaudit --project <répertoire>", "en": "        python DTLaudit --project <directory>"},
    "cli.syntax_suite": {"fr": "        python DTLaudit --suite <répertoire>", "en": "        python DTLaudit --suite <directory>"},
    "cli.options": {"fr": "OPTIONS :", "en": "OPTIONS:"},
    "cli.examples": {"fr": "EXEMPLES :", "en": "EXAMPLES:"},
    "interactive.choose_mode": {"fr": "\nChoisissez un mode :\n", "en": "\nChoose a mode:\n"},
    "interactive.audit_suite": {"fr": "1  Auditer un dossier contenant plusieurs projets", "en": "1  Audit a directory containing several projects"},
    "interactive.audit_project": {"fr": "2  Auditer un seul projet", "en": "2  Audit a single project"},
    "interactive.quit": {"fr": "Q : Quitter", "en": "Q: Quit"},
    "interactive.choice": {"fr": "\nVotre choix : ", "en": "\nYour choice: "},
    "interactive.choose_suite": {"fr": "Choisir le dossier contenant les projets", "en": "Choose the directory containing the projects"},
    "interactive.choose_project": {"fr": "Choisir le dossier du projet à auditer", "en": "Choose the project directory to audit"},
    "interactive.picker_error": {"fr": "Impossible d'ouvrir le sélecteur de dossiers : {error}", "en": "Unable to open the directory picker: {error}"},
    "interactive.return": {"fr": "\nAppuyer sur <Return> pour revenir au menu principal.", "en": "\nPress <Return> to go back to the main menu."},
    "interactive.folder": {"fr": "Dossier", "en": "Directory"},
    "interactive.audit_start": {"fr": "L'audit démarre. Aucun fichier du projet ne sera modifié.\n", "en": "The audit is starting. No project files will be changed.\n"},
    "interactive.html_report": {"fr": "Rapport HTML", "en": "HTML report"},
    "interactive.open_report": {"fr": "Ouvrir le rapport maintenant ?", "en": "Open the report now?"},
    "error.open_report": {"fr": "Impossible d'ouvrir le rapport : {error}", "en": "Unable to open the report: {error}"},
    "error.command_not_found": {"fr": "commande introuvable : {command}", "en": "command not found: {command}"},
    "error.command_timeout": {"fr": "délai dépassé après {seconds} secondes", "en": "timed out after {seconds} seconds"},
    "error.command_launch": {"fr": "impossible de lancer une commande externe", "en": "unable to start an external command"},
    "error.command_failed": {"fr": "commande terminée avec le code {code}", "en": "command exited with code {code}"},
    "error.cwd": {"fr": "Répertoire courant : {path}", "en": "Working directory: {path}"},
    "error.command": {"fr": "Commande : {command}", "en": "Command: {command}"},
    "error.no_command_output": {"fr": "Aucun message retourné par la commande.", "en": "The command returned no output."},
    "audit.start": {"fr": "DTLaudit {version} démarre", "en": "DTLaudit {version} is starting"},
    "audit.folder_not_found": {"fr": "dossier introuvable : {path}", "en": "directory not found: {path}"},
    "audit.single_target": {"fr": "projet unique : {path}", "en": "single project: {path}"},
    "audit.suite_target": {"fr": "suite de projets : {path}", "en": "project suite: {path}"},
    "audit.discovered": {"fr": "{count} projet(s) détecté(s)", "en": "{count} project(s) detected"},
    "audit.no_project": {"fr": "aucun projet détecté", "en": "no project detected"},
    "audit.json_written": {"fr": "Rapport JSON écrit : {path}", "en": "JSON report written: {path}"},
    "audit.text_written": {"fr": "Rapport TXT écrit : {path}", "en": "TXT report written: {path}"},
    "audit.html_written": {"fr": "Rapport HTML écrit : {path}", "en": "HTML report written: {path}"},
    "audit.done": {"fr": "audit terminé", "en": "audit complete"},
    "audit.interrupted": {"fr": "interruption par l'utilisateur", "en": "interrupted by user"},
    "audit.unexpected_error": {"fr": "erreur Python inattendue", "en": "unexpected Python error"},
    "audit.debug_hint": {"fr": "Relancer avec --debug pour afficher la pile Python complète.", "en": "Run again with --debug to display the full Python traceback."},
}


def set_language(language: str | None) -> str:
    """Select a supported language and return its normalized code."""
    global _language
    candidate = (language or os.environ.get("DTL_LANGUAGE") or "fr").casefold()[:2]
    if candidate not in SUPPORTED_LANGUAGES:
        candidate = "fr"
    _language = candidate
    return _language


def get_language() -> str:
    return _language


def t(key: str, **values: Any) -> str:
    """Translate a semantic key and interpolate named placeholders."""
    item = TRANSLATIONS.get(key)
    if item is None:
        raise KeyError(f"Unknown translation key: {key}")
    text = item[_language]
    return text.format(**values) if values else text


set_language(None)
