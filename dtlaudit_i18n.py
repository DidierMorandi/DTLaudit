"""Catalogue FR/EN centralisé des textes visibles de DTLaudit."""

from __future__ import annotations

import os
from typing import Any


SUPPORTED_LANGUAGES = ("fr", "en")
_language = "fr"


TRANSLATIONS: dict[str, dict[str, str]] = {
    "txxxx_app_suite": {"fr": "Un outil de la suite NetDTL", "en": "A tool from the NetDTL suite"},
    "txxxx_app_subtitle": {"fr": "Audit comparatif de projets en lecture seule", "en": "Read-only comparative project audit"},
    "txxxx_app_language_hint": {"fr": "For English speaking, type 1.", "en": "Pour le français, tapez 2."},
    "txxxx_common_yes": {"fr": "oui", "en": "yes"},
    "txxxx_common_no": {"fr": "non", "en": "no"},
    "txxxx_common_yes_cap": {"fr": "Oui", "en": "Yes"},
    "txxxx_common_no_cap": {"fr": "Non", "en": "No"},
    "txxxx_common_present": {"fr": "présent", "en": "present"},
    "txxxx_common_absent": {"fr": "absent", "en": "absent"},
    "txxxx_common_complete": {"fr": "complète", "en": "complete"},
    "txxxx_common_not_detected": {"fr": "non détecté", "en": "not detected"},
    "txxxx_common_not_detected_f": {"fr": "non détectée", "en": "not detected"},
    "txxxx_common_not_detected_plural": {"fr": "non détectées", "en": "not detected"},
    "txxxx_common_not_available": {"fr": "non disponible", "en": "unavailable"},
    "txxxx_common_none_f": {"fr": "absente", "en": "none"},
    "txxxx_common_public": {"fr": "public", "en": "public"},
    "txxxx_common_private": {"fr": "privé", "en": "private"},
    "txxxx_common_invalid_choice": {"fr": "Choix invalide. Saisissez une option proposée.", "en": "Invalid choice. Enter one of the available options."},
    "txxxx_common_invalid_yes_no": {"fr": "Réponse invalide. Saisissez O ou N.", "en": "Invalid answer. Enter Y or N."},
    "txxxx_common_yes_no_default_yes": {"fr": "O/n", "en": "Y/n"},
    "txxxx_common_yes_no_default_no": {"fr": "o/N", "en": "y/N"},
    "txxxx_unit_mb": {"fr": "Mo", "en": "MB"},
    "txxxx_unit_kb": {"fr": "Ko", "en": "KB"},
    "txxxx_unit_byte": {"fr": "o", "en": "B"},
    "txxxx_count_project_one": {"fr": "{count} projet", "en": "{count} project"},
    "txxxx_count_project_other": {"fr": "{count} projets", "en": "{count} projects"},
    "txxxx_count_items_more": {"fr": "... {count} autres éléments", "en": "... {count} more items"},
    "txxxx_label_project": {"fr": "Projet", "en": "Project"},
    "txxxx_label_projects": {"fr": "Projets", "en": "Projects"},
    "txxxx_label_version": {"fr": "Version", "en": "Version"},
    "txxxx_label_branch": {"fr": "Branche", "en": "Branch"},
    "txxxx_label_visibility_short": {"fr": "Visib.", "en": "Visib."},
    "txxxx_label_visibility": {"fr": "Visibilité", "en": "Visibility"},
    "txxxx_label_changes": {"fr": "Modifs", "en": "Changes"},
    "txxxx_label_local_changes": {"fr": "Modifications locales", "en": "Local changes"},
    "txxxx_label_repository": {"fr": "Dépôt", "en": "Repository"},
    "txxxx_label_recent_release": {"fr": "Release récente", "en": "Latest release"},
    "txxxx_label_open_prs": {"fr": "Pull requests ouvertes", "en": "Open pull requests"},
    "txxxx_label_open_issues": {"fr": "Issues ouvertes", "en": "Open issues"},
    "txxxx_label_status": {"fr": "Statut", "en": "Status"},
    "txxxx_label_summary": {"fr": "Synthèse", "en": "Summary"},
    "txxxx_label_root": {"fr": "Racine", "en": "Root"},
    "txxxx_label_scanned_projects": {"fr": "Projets scannés", "en": "Projects scanned"},
    "txxxx_label_notable_observations": {"fr": "Observations remarquables", "en": "Notable observations"},
    "txxxx_label_files_observed": {"fr": "Fichiers et répertoires observés", "en": "Observed files and directories"},
    "txxxx_label_single_project_items": {"fr": "Présents dans un seul projet", "en": "Present in only one project"},
    "txxxx_label_some_project_items": {"fr": "Présents dans plusieurs projets, mais pas tous", "en": "Present in several projects, but not all"},
    "txxxx_label_path": {"fr": "Chemin", "en": "Path"},
    "txxxx_label_count_short": {"fr": "Nb", "en": "Count"},
    "txxxx_label_english": {"fr": "anglais", "en": "English"},
    "txxxx_label_french": {"fr": "français", "en": "French"},
    "txxxx_label_english_cap": {"fr": "Anglais", "en": "English"},
    "txxxx_label_french_cap": {"fr": "Français", "en": "French"},
    "txxxx_label_normative_docs": {"fr": "Documentation normative", "en": "Normative documentation"},
    "txxxx_label_assessment": {"fr": "Bilan", "en": "Assessment"},
    "txxxx_label_tool_version": {"fr": "Version outil", "en": "Tool version"},
    "txxxx_label_git": {"fr": "Git", "en": "Git"},
    "txxxx_label_github": {"fr": "GitHub", "en": "GitHub"},
    "txxxx_label_remote_github": {"fr": "Remote GitHub", "en": "GitHub remote"},
    "txxxx_label_tags": {"fr": "Tags", "en": "Tags"},
    "txxxx_label_readme": {"fr": "README", "en": "README"},
    "txxxx_label_readme_en_short": {"fr": "README En", "en": "README En"},
    "txxxx_label_readme_fr_short": {"fr": "README Fr", "en": "README Fr"},
    "txxxx_label_reference_fr_short": {"fr": "RF Fr", "en": "RM Fr"},
    "txxxx_label_user_guide_fr_short": {"fr": "GU Fr", "en": "UG Fr"},
    "txxxx_label_reference_en_short": {"fr": "RF En", "en": "RM En"},
    "txxxx_label_user_guide_en_short": {"fr": "GU En", "en": "UG En"},
    "txxxx_label_release": {"fr": "Release", "en": "Release"},
    "txxxx_doc_reference_fr": {"fr": "Manuel de référence (FR)", "en": "Reference Manual (FR)"},
    "txxxx_doc_user_guide_fr": {"fr": "Guide utilisateur (FR)", "en": "User Guide (FR)"},
    "txxxx_doc_reference_en": {"fr": "Reference Manual (EN)", "en": "Reference Manual (EN)"},
    "txxxx_doc_user_guide_en": {"fr": "User Guide (EN)", "en": "User Guide (EN)"},
    "txxxx_report_comparative": {"fr": "Rapport comparatif entre projets", "en": "Comparative project report"},
    "txxxx_report_read_only": {"fr": "Aucune modification effectuée", "en": "No changes made"},
    "txxxx_report_complete_count": {"fr": "{count}/{total} présents", "en": "{count}/{total} present"},
    "txxxx_report_projects_in_path": {"fr": "{count} projets ({names})", "en": "{count} projects ({names})"},
    "txxxx_report_no_observation": {"fr": "Aucune observation.", "en": "No observations."},
    "txxxx_report_no_file": {"fr": "Aucun fichier à signaler.", "en": "No files to report."},
    "txxxx_report_html_tagline": {"fr": "DTL Projects · Rapport d’audit", "en": "DTL Projects · Audit report"},
    "txxxx_report_html_meta": {"fr": "Racine : {root} · {count} projet(s) scanné(s) · aucune modification effectuée", "en": "Root: {root} · {count} project(s) scanned · no changes made"},
    "txxxx_report_project_details": {"fr": "Détail par projet", "en": "Project details"},
    "txxxx_report_mode": {"fr": "rapport comparatif", "en": "comparative report"},
    "txxxx_github_not_queried": {"fr": "non interrogé", "en": "not queried"},
    "txxxx_github_gh_unavailable": {"fr": "commande gh non disponible", "en": "gh command unavailable"},
    "txxxx_github_repo_not_detected": {"fr": "dépôt GitHub non détecté", "en": "GitHub repository not detected"},
    "txxxx_github_unreadable_response": {"fr": "réponse GitHub non lisible", "en": "unreadable GitHub response"},
    "txxxx_observation_readme": {"fr": "README est présent dans {count} sur {total}.", "en": "A README is present in {count} out of {total}."},
    "txxxx_observation_readme_en": {"fr": "README anglais est présent dans {count} sur {total}.", "en": "An English README is present in {count} out of {total}."},
    "txxxx_observation_readme_fr": {"fr": "README français est présent dans {count} sur {total}.", "en": "A French README is present in {count} out of {total}."},
    "txxxx_observation_docs_complete": {"fr": "Documentation normative complète (4/4) dans {count} sur {total}.", "en": "Complete normative documentation (4/4) in {count} out of {total}."},
    "txxxx_observation_doc_missing": {"fr": "{label} manquant dans : {projects}.", "en": "{label} missing from: {projects}."},
    "txxxx_observation_git": {"fr": "Git est présent dans {count} sur {total}.", "en": "Git is present in {count} out of {total}."},
    "txxxx_observation_github_remote": {"fr": "Remote GitHub est présent dans {count} sur {total}.", "en": "A GitHub remote is present in {count} out of {total}."},
    "txxxx_observation_github_status": {"fr": "Status GitHub disponible dans {count} sur {total}.", "en": "GitHub status is available in {count} out of {total}."},
    "txxxx_observation_branch": {"fr": "Branche {branch} observée dans {count} sur {total}.", "en": "Branch {branch} found in {count} out of {total}."},
    "txxxx_observation_unique_files": {"fr": "{count} fichiers sont présents uniquement dans {project}.", "en": "{count} files are present only in {project}."},
    "txxxx_observation_generated_dirs": {"fr": "Répertoires générés observés dans {project} : {names}", "en": "Generated directories found in {project}: {names}"},
    "txxxx_observation_large_file": {"fr": "Fichier volumineux observé dans {project} : {path} ({size})", "en": "Large file found in {project}: {path} ({size})"},
    "txxxx_cli_help": {"fr": "Affiche cette aide et quitte", "en": "Show this help message and exit"},
    "txxxx_cli_project": {"fr": "Analyse un projet unique", "en": "Audit a single project"},
    "txxxx_cli_suite": {"fr": "Analyse un répertoire contenant plusieurs projets", "en": "Audit a directory containing several projects"},
    "txxxx_cli_json": {"fr": "Produire un rapport au format JSON", "en": "Write a JSON report"},
    "txxxx_cli_no_github": {"fr": "Ne pas interroger GitHub avec gh", "en": "Do not query GitHub with gh"},
    "txxxx_cli_text": {"fr": "Produire un rapport au format texte", "en": "Write a text report"},
    "txxxx_cli_html": {"fr": "Produire un rapport au format HTML", "en": "Write an HTML report"},
    "txxxx_cli_quiet": {"fr": "Ne pas afficher les messages de diagnostic console", "en": "Hide console diagnostic messages"},
    "txxxx_cli_debug": {"fr": "Affiche des informations techniques détaillées en cas d'erreur inattendue", "en": "Show detailed technical information after an unexpected error"},
    "txxxx_cli_lang": {"fr": "Langue de l'interface (fr ou en)", "en": "Interface language (fr or en)"},
    "txxxx_cli_usage": {"fr": "python dtlaudit.py (--project <projet> | --suite <répertoire>) [options]", "en": "python dtlaudit.py (--project <project> | --suite <directory>) [options]"},
    "txxxx_cli_error": {"fr": "ERREUR :", "en": "ERROR:"},
    "txxxx_cli_error_target_required": {"fr": "une des options --project ou --suite est obligatoire", "en": "one of --project or --suite is required"},
    "txxxx_cli_error_argument_value": {"fr": "l'option {argument} attend une valeur", "en": "argument {argument}: expected one value"},
    "txxxx_cli_error_invalid_choice": {"fr": "valeur incorrecte pour {argument} : {value} (choisir parmi {choices})", "en": "invalid value for {argument}: {value} (choose from {choices})"},
    "txxxx_cli_error_unrecognized": {"fr": "option(s) non reconnue(s) : {arguments}", "en": "unrecognized argument(s): {arguments}"},
    "txxxx_cli_description": {"fr": "DESCRIPTION :", "en": "DESCRIPTION:"},
    "txxxx_cli_description_text": {"fr": "        DTLaudit compare un ou plusieurs projets et génère un rapport HTML, TXT ou JSON.", "en": "        DTLaudit compares one or more projects and writes an HTML, TXT or JSON report."},
    "txxxx_cli_syntax": {"fr": "SYNTAXE :", "en": "USAGE:"},
    "txxxx_cli_syntax_project": {"fr": "        python DTLaudit --project <répertoire>", "en": "        python DTLaudit --project <directory>"},
    "txxxx_cli_syntax_suite": {"fr": "        python DTLaudit --suite <répertoire>", "en": "        python DTLaudit --suite <directory>"},
    "txxxx_cli_options": {"fr": "OPTIONS :", "en": "OPTIONS:"},
    "txxxx_cli_examples": {"fr": "EXEMPLES :", "en": "EXAMPLES:"},
    "txxxx_cli_example_project": {"fr": "        python DTLaudit --project C:\\MesProjets\\GitDTL", "en": "        python DTLaudit --project C:\\MyProjects\\GitDTL"},
    "txxxx_cli_example_suite": {"fr": "        python DTLaudit --suite C:\\MesProjets", "en": "        python DTLaudit --suite C:\\MyProjects"},
    "txxxx_cli_example_reports": {"fr": "        python DTLaudit --suite C:\\MesProjets --json --html", "en": "        python DTLaudit --suite C:\\MyProjects --json --html"},
    "txxxx_interactive_choose_mode": {"fr": "\nChoisissez un mode :\n", "en": "\nChoose a mode:\n"},
    "txxxx_interactive_audit_suite": {"fr": "A : Auditer un dossier contenant plusieurs projets", "en": "A: Audit a directory containing several projects"},
    "txxxx_interactive_audit_project": {"fr": "B : Auditer un seul projet", "en": "B: Audit a single project"},
    "txxxx_interactive_quit": {"fr": "Q : Quitter", "en": "Q: Quit"},
    "txxxx_interactive_choice": {"fr": "\nVotre choix : ", "en": "\nYour choice: "},
    "txxxx_interactive_choose_suite": {"fr": "Choisir le dossier contenant les projets", "en": "Choose the directory containing the projects"},
    "txxxx_interactive_choose_project": {"fr": "Choisir le dossier du projet à auditer", "en": "Choose the project directory to audit"},
    "txxxx_interactive_picker_error": {"fr": "Impossible d'ouvrir le sélecteur de dossiers : {error}", "en": "Unable to open the directory picker: {error}"},
    "txxxx_interactive_return": {"fr": "\nAppuyer sur <Return> pour revenir au menu principal.", "en": "\nPress <Return> to go back to the main menu."},
    "txxxx_interactive_folder": {"fr": "Dossier", "en": "Directory"},
    "txxxx_interactive_audit_start": {"fr": "L'audit démarre. Aucun fichier du projet ne sera modifié.\n", "en": "The audit is starting. No project files will be changed.\n"},
    "txxxx_interactive_html_report": {"fr": "Rapport HTML", "en": "HTML report"},
    "txxxx_interactive_open_report": {"fr": "Ouvrir le rapport maintenant ?", "en": "Open the report now?"},
    "txxxx_error_open_report": {"fr": "Impossible d'ouvrir le rapport : {error}", "en": "Unable to open the report: {error}"},
    "txxxx_error_command_not_found": {"fr": "commande introuvable : {command}", "en": "command not found: {command}"},
    "txxxx_error_command_timeout": {"fr": "délai dépassé après {seconds} secondes", "en": "timed out after {seconds} seconds"},
    "txxxx_error_command_launch": {"fr": "impossible de lancer une commande externe", "en": "unable to start an external command"},
    "txxxx_error_command_failed": {"fr": "commande terminée avec le code {code}", "en": "command exited with code {code}"},
    "txxxx_error_cwd": {"fr": "Répertoire courant : {path}", "en": "Working directory: {path}"},
    "txxxx_error_command": {"fr": "Commande : {command}", "en": "Command: {command}"},
    "txxxx_error_no_command_output": {"fr": "Aucun message retourné par la commande.", "en": "The command returned no output."},
    "txxxx_audit_start": {"fr": "DTLaudit {version} démarre", "en": "DTLaudit {version} is starting"},
    "txxxx_audit_folder_not_found": {"fr": "dossier introuvable : {path}", "en": "directory not found: {path}"},
    "txxxx_audit_single_target": {"fr": "projet unique : {path}", "en": "single project: {path}"},
    "txxxx_audit_suite_target": {"fr": "suite de projets : {path}", "en": "project suite: {path}"},
    "txxxx_audit_discovered": {"fr": "{count} projet(s) détecté(s)", "en": "{count} project(s) detected"},
    "txxxx_audit_no_project": {"fr": "aucun projet détecté", "en": "no project detected"},
    "txxxx_audit_json_written": {"fr": "Rapport JSON écrit : {path}", "en": "JSON report written: {path}"},
    "txxxx_audit_text_written": {"fr": "Rapport TXT écrit : {path}", "en": "TXT report written: {path}"},
    "txxxx_audit_html_written": {"fr": "Rapport HTML écrit : {path}", "en": "HTML report written: {path}"},
    "txxxx_audit_done": {"fr": "audit terminé", "en": "audit complete"},
    "txxxx_audit_interrupted": {"fr": "interruption par l'utilisateur", "en": "interrupted by user"},
    "txxxx_audit_unexpected_error": {"fr": "erreur Python inattendue", "en": "unexpected Python error"},
    "txxxx_audit_debug_hint": {"fr": "Relancer avec --debug pour afficher la pile Python complète.", "en": "Run again with --debug to display the full Python traceback."},
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


def toggle_language() -> str:
    """Bascule entre le français et l'anglais et retourne la langue active."""
    return set_language("en" if _language == "fr" else "fr")


def t(key: str, **values: Any) -> str:
    """Translate a semantic key and interpolate named placeholders."""
    item = TRANSLATIONS.get(key)
    if item is None:
        raise KeyError(f"Unknown translation key: {key}")
    text = item[_language]
    return text.format(**values) if values else text


set_language(None)
