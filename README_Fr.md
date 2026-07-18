# DTLaudit

DTLaudit est un outil d'audit en lecture seule pour comparer un ensemble de projets locaux.

Il analyse un projet unique ou un dossier contenant plusieurs projets, puis produit un rapport compact sur la structure des projets, l'état Git, la présence GitHub, les fichiers README, les releases, les dossiers générés, les gros fichiers et les fichiers présents seulement dans certains projets.

## Fonctionnalités

- Audit d'un projet local ou d'une suite complète de projets.
- Détection des dépôts Git, de la branche courante, du remote `origin`, des modifications locales et des tags.
- Détection des remotes GitHub.
- Interrogation optionnelle de GitHub via `gh` pour les métadonnées du dépôt, la dernière release, les pull requests ouvertes et les issues ouvertes.
- Signalement des dossiers générés comme `build/`, `dist/`, `__pycache__/`, `.pytest_cache/` et `.mypy_cache/`.
- Signalement des fichiers de plus de 5 Mo.
- Production d'un rapport HTML par défaut.
- Production optionnelle de rapports JSON et texte.
- Aucun changement dans les projets audités.

## Prérequis

- Python 3.10 ou plus récent.
- Git, pour lire les informations des dépôts.
- Optionnel : GitHub CLI (`gh`) authentifié, pour obtenir les métadonnées GitHub en direct.

DTLaudit n'utilise que la bibliothèque standard de Python.

## Utilisation

Lancé sans argument, DTLaudit affiche une interface console inspirée de DTLi18n :

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py"
```

Le menu permet de choisir l'audit d'une suite ou d'un projet, puis ouvre
l'Explorateur Windows afin de sélectionner le dossier. Une fois l'audit terminé,
DTLaudit propose d'ouvrir le rapport HTML et revient au menu principal.

Auditer un dossier contenant plusieurs projets :

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils"
```

Auditer un seul projet :

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --project "D:\Documents\Mes sites Web\outils\GitHubMenu"
```

Ignorer les requêtes GitHub :

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils" --no-github
```

## Fichiers produits

Par défaut, DTLaudit écrit seulement le rapport HTML :

```text
DTLaudit_rapport.html
```

Le fichier est écrit dans le dossier DTLaudit, à côté de `DTLaudit.py`.

Pour produire aussi les rapports JSON et texte :

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils" --json --text
```

Fichiers créés :

```text
DTLaudit_rapport.html
DTLaudit_rapport.json
DTLaudit_rapport.txt
```

Il est possible de choisir des chemins de sortie personnalisés :

```powershell
python "D:\Documents\Mes sites Web\outils\DTLaudit\DTLaudit.py" --suite "D:\Documents\Mes sites Web\outils" --html "audit.html" --json "audit.json" --text "audit.txt"
```

Les chemins relatifs sont résolus depuis le dossier DTLaudit.

## Options

```text
--project PATH       Auditer un projet local.
--suite PATH         Auditer un dossier contenant plusieurs projets.
--json [PATH]        Écrire aussi un rapport JSON.
--text [PATH]        Écrire aussi un rapport texte.
--txt [PATH]         Alias de --text.
--html [PATH]        Écrire un rapport HTML. Activé par défaut.
--no-github          Ne pas interroger GitHub avec gh.
--lang {fr,en}       Choisir la langue de l'interface et des rapports.
```

Le français est utilisé par défaut. La langue peut aussi être définie avec la
variable d'environnement `DTL_LANGUAGE=fr` ou `DTL_LANGUAGE=en`.

`--project` et `--suite` sont exclusifs. L'un des deux est obligatoire en mode
ligne de commande ; sans argument, le menu console interactif est utilisé.

## Découverte des projets

Avec `--suite`, DTLaudit inspecte les sous-dossiers directs du dossier de suite.

Un sous-dossier est considéré comme un projet s'il contient au moins l'un des éléments suivants :

- un dossier `.git` ;
- un fichier Python (`*.py`) ;
- un script Windows (`*.ps1`, `*.vbs`, `*.bat` ou `*.cmd`) ;
- un fichier README (`README*`).

Les dossiers cachés sont ignorés.

## Contenu du rapport

Le rapport commence par un tableau de synthèse, puis détaille chaque projet :

- présence du README ;
- état Git ;
- branche courante ;
- présence d'un remote GitHub ;
- nombre de fichiers modifiés localement ;
- nombre de tags ;
- métadonnées GitHub si disponibles ;
- dernière release GitHub si disponible ;
- nombre de pull requests et issues ouvertes si disponible.

Le rapport contient aussi des observations notables et une matrice de fichiers montrant les fichiers ou dossiers présents seulement dans un ou plusieurs projets.

## Métadonnées GitHub

Les métadonnées GitHub sont collectées uniquement si :

- `--no-github` n'est pas utilisé ;
- la commande `gh` est installée ;
- `gh` est authentifié ;
- le projet possède un remote GitHub ou peut être résolu par `gh`.

Si ces conditions ne sont pas réunies, le rapport reste fonctionnel avec les seules informations Git locales.

## Sécurité

DTLaudit est volontairement en lecture seule.

Il parcourt les fichiers, lit les métadonnées Git et appelle éventuellement `gh`, mais il ne modifie aucun projet audité, ne lance aucun build, ne nettoie aucun fichier, ne commit pas, ne pousse rien et ne supprime rien.

## Notes

Les artefacts générés comme `build/`, `dist/` et les exécutables peuvent créer beaucoup de bruit Git s'ils sont suivis. DTLaudit les signale afin de permettre une revue et, si nécessaire, leur ajout dans `.gitignore`.

## Mise à jour - 16 juillet 2026

Le code courant annonce `v1.1-0` dans `DTLaudit.py`.

Nouveautés confirmées dans le code :

- L'interface Tkinter a été remplacée par une interface console cohérente avec DTLi18n.
- Le lancement sans argument affiche un menu permettant d'auditer une suite ou un projet.
- La sélection du dossier se fait dans l'Explorateur Windows ; la progression, l'ouverture du rapport et le retour au menu restent pilotés depuis la console.
- Le rapport HTML est généré par défaut sous le nom `DTLaudit_rapport.html`.
- Les sorties JSON et texte restent optionnelles via `--json` et `--txt` / `--text`.
- L'audit vérifie maintenant la présence des guides utilisateur et manuels de référence en plus du README.
- Les métadonnées GitHub peuvent être enrichies avec `gh` : visibilité, dernière release, pull requests ouvertes et issues ouvertes.
- Une fonction peut copier la sortie JSON vers un environnement XAMPP lorsqu'un tableau de bord PHP local est utilisé.
- `DTLaudit_dashboard_live.php` complète le rapport statique avec un tableau de bord local plus dynamique.
