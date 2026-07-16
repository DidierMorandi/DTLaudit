<?php
// DTLaudit dashboard live.
// Place this file beside DTLaudit.py, then open it through XAMPP/PHP.
// It launches DTLaudit.py itself and refreshes every 60 seconds.

$PYTHON = 'C:\Program Files\Python314\python.exe';
$DTLAUDIT_SCRIPT = 'D:\Documents\Mes sites Web\Secours catholique\outils\DTLaudit\DTLaudit.py';
$SUITE_ROOT = 'D:\Documents\Mes sites Web\Secours catholique\outils';
$REPORT_JSON = __DIR__ . DIRECTORY_SEPARATOR . 'DTLaudit_rapport.json';
$USE_GITHUB = true;
$LOCK_FILE = __DIR__ . DIRECTORY_SEPARATOR . 'DTLaudit_scan.lock';

function json_response($data, $status = 200) {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_INVALID_UTF8_SUBSTITUTE);
    if ($json === false) {
        http_response_code(500);
        $json = json_encode(array(
            'ok' => false,
            'error' => 'Erreur encodage JSON : ' . json_last_error_msg()
        ), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
    echo $json;
    exit;
}

function detect_tool_version($project) {
    $project_dir = $project['path'] ?? '';
    if (!is_string($project_dir) || $project_dir === '' || !is_dir($project_dir)) {
        return null;
    }

    $version_file = $project_dir . DIRECTORY_SEPARATOR . '.dtl_version';
    if (is_file($version_file)) {
        $raw = @file_get_contents($version_file);
        $data = json_decode($raw, true);
        if (is_array($data)) {
            foreach (array('display_version', 'version') as $key) {
                if (!empty($data[$key]) && is_string($data[$key])) {
                    return trim($data[$key]);
                }
            }
        }
    }

    $candidates = array();
    $project_name = $project['name'] ?? '';
    if (is_string($project_name) && $project_name !== '') {
        $candidates[] = $project_dir . DIRECTORY_SEPARATOR . $project_name . '.py';
    }
    foreach (glob($project_dir . DIRECTORY_SEPARATOR . '*.py') ?: array() as $path) {
        $candidates[] = $path;
    }

    foreach (array_unique($candidates) as $path) {
        if (!is_file($path)) {
            continue;
        }
        $content = @file_get_contents($path);
        if (is_string($content) && preg_match('/^\s*VERSION\s*=\s*[\'"]([^\'"]+)[\'"]/m', $content, $matches)) {
            return trim($matches[1]);
        }
    }

    return null;
}

function run_dtlaudit($PYTHON, $DTLAUDIT_SCRIPT, $SUITE_ROOT, $REPORT_JSON, $USE_GITHUB, $LOCK_FILE, $FORCE_SCAN = false) {
    if (!file_exists($DTLAUDIT_SCRIPT)) {
        return array(false, "DTLaudit.py introuvable : " . $DTLAUDIT_SCRIPT);
    }

    // Avoid launching several scans at the same time.
	 if (!$FORCE_SCAN && file_exists($LOCK_FILE) && (time() - filemtime($LOCK_FILE)) < 55) {
		return array(true, "Scan déjà en cours ou lancé récemment ; rapport existant conservé.");
	}

    file_put_contents($LOCK_FILE, date('c'));

    $cmd = escapeshellarg($PYTHON) . ' ' .
        escapeshellarg($DTLAUDIT_SCRIPT) .
        ' --suite ' . escapeshellarg($SUITE_ROOT) .
        ' --json ' . escapeshellarg($REPORT_JSON);

    if (!$USE_GITHUB) {
        $cmd .= ' --no-github';
    }

    $cmd .= ' 2>&1';

    $output = array();
    $code = 0;
    exec($cmd, $output, $code);
    @unlink($LOCK_FILE);

    if ($code !== 0) {
        return array(false, "Erreur DTLaudit code " . $code . "\nCommande : " . $cmd . "\n\n" . implode("\n", $output));
    }

    return array(true, implode("\n", array_slice($output, 0, 12)));
}

function run_selftest($PYTHON, $DTLAUDIT_SCRIPT, $REPORT_JSON) {
    $checks = array(
        'php' => extension_loaded('json'),
        'python' => false,
        'json' => false,
        'html' => false,
        'javascript' => false,
    );
    $projects = 0;

    if (is_file($PYTHON) && is_file($DTLAUDIT_SCRIPT)) {
        $python_output = array();
        $python_code = 1;
        exec(escapeshellarg($PYTHON) . ' --version 2>&1', $python_output, $python_code);
        $checks['python'] = ($python_code === 0);
    }

    if (is_file($REPORT_JSON)) {
        $report = json_decode((string) @file_get_contents($REPORT_JSON), true);
        $checks['json'] = is_array($report) && isset($report['projects']) && is_array($report['projects']);
        if ($checks['json']) {
            $projects = count($report['projects']);
        }
    }

    $source = (string) @file_get_contents(__FILE__);
    $html_markers = array('<!doctype html>', '<html', '<head>', '</head>', '<body>', '</body>', '</html>');
    $checks['html'] = $source !== '';
    foreach ($html_markers as $marker) {
        if (stripos($source, $marker) === false) {
            $checks['html'] = false;
            break;
        }
    }

    if (preg_match('/<script\b[^>]*>(.*?)<\/script>/is', $source, $script_match)) {
        $javascript = $script_match[1];
        $checks['javascript'] =
            strpos($javascript, 'function render(') !== false &&
            strpos($javascript, 'async function loadReport(') !== false &&
            strpos($javascript, 'addEventListener(') !== false &&
            strpos($javascript, 'setInterval(') !== false;

        // Si Node.js est disponible, compléter le contrôle structurel par une
        // véritable validation syntaxique, sans exécuter le JavaScript.
        if ($checks['javascript']) {
            $node_version = array();
            $node_version_code = 1;
            exec('node --version 2>&1', $node_version, $node_version_code);
            if ($node_version_code === 0) {
                $temporary_script = tempnam(sys_get_temp_dir(), 'dtlaudit_js_');
                if ($temporary_script === false) {
                    $checks['javascript'] = false;
                } else {
                    file_put_contents($temporary_script, $javascript);
                    $node_output = array();
                    $node_code = 1;
                    exec('node --check ' . escapeshellarg($temporary_script) . ' 2>&1', $node_output, $node_code);
                    @unlink($temporary_script);
                    $checks['javascript'] = ($node_code === 0);
                }
            }
        }
    }

    $warnings = count(array_filter($checks, static function ($ok) {
        return !$ok;
    }));

    $result = array();
    foreach ($checks as $name => $ok) {
        $result[$name] = $ok ? 'ok' : 'error';
    }
    $result['projects'] = $projects;
    $result['warnings'] = $warnings;

    return $result;
}

if (($_GET['action'] ?? '') === 'selftest') {
    $result = run_selftest($PYTHON, $DTLAUDIT_SCRIPT, $REPORT_JSON);
    json_response($result, $result['warnings'] === 0 ? 200 : 503);
}

if (($_GET['action'] ?? '') === 'scan') {
    $force_scan = (($_GET['force'] ?? '') === '1');
    list($ok, $message) = run_dtlaudit($PYTHON, $DTLAUDIT_SCRIPT, $SUITE_ROOT, $REPORT_JSON, $USE_GITHUB, $LOCK_FILE, $force_scan);

    if (!file_exists($REPORT_JSON)) {
        json_response(array(
            'ok' => false,
            'error' => 'Rapport JSON introuvable : ' . $REPORT_JSON,
            'message' => $message
        ), 500);
    }

    $raw = file_get_contents($REPORT_JSON);
    $data = json_decode($raw, true);

    if (!is_array($data)) {
        json_response(array(
            'ok' => false,
            'error' => 'Rapport JSON illisible.',
            'message' => $message
        ), 500);
    }

    if (!empty($data['projects']) && is_array($data['projects'])) {
        foreach ($data['projects'] as &$project) {
            if (empty($project['tool_version'])) {
                $project['tool_version'] = detect_tool_version($project) ?: '-';
            }
        }
        unset($project);
    }

    $data['_dashboard'] = array(
        'ok' => $ok,
        'message' => $message,
        'generated_at' => date('Y-m-d H:i:s')
    );

    json_response($data, $ok ? 200 : 500);
}
?><!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>DTLaudit — Tableau de bord en direct</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#0b0d0f;--panel:#131619;--panel2:#1a1e23;--line:rgba(255,255,255,.10);--txt:#e8eaed;--muted:#7a8290;--yes:#4ade80;--no:#ff7a45;--warn:#facc15;--blue:#38bdf8}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--txt);font-family:Consolas,"Courier New",monospace}
body:before{content:"";position:fixed;inset:0;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:40px 40px;pointer-events:none}
header,main{position:relative;z-index:1}header{padding:12px 18px 4px}.brand{display:flex;align-items:flex-start;justify-content:space-between;gap:24px}.brand-copy{min-width:0}h1{font-family:inherit;font-size:16px;font-weight:700;line-height:1.2;margin:0 0 4px}.brand-suite,.brand-website{font-size:12px;line-height:1.35}.brand-suite{color:var(--txt)}.brand-website{color:var(--muted);text-decoration:none}.brand-website:hover{color:var(--blue)}.netdtl-logo{display:grid;grid-template-columns:repeat(6,20px);flex:0 0 auto;border:1px solid #fff;background:#0201b7}.netdtl-logo span{display:grid;place-items:center;height:34px;color:#fff;font:700 16px Arial,sans-serif;border-right:1px solid rgba(255,255,255,.78)}.netdtl-logo span:last-child{border-right:0}.subtitle{margin-top:8px;font-size:13px;font-weight:700}.meta{margin-top:3px;color:var(--muted);font-size:12px}
main{padding:10px 18px}.cards{display:flex;align-items:baseline;gap:28px;flex-wrap:wrap;margin-bottom:10px}.card{display:flex;align-items:baseline;gap:7px;background:none;border:0;border-radius:0;padding:0}.label{color:var(--muted);text-transform:uppercase;letter-spacing:.10em;font-size:10px}.value{font-size:inherit;font-weight:700}
.toolbar{display:flex;gap:12px;align-items:center;color:var(--muted);font-size:12px;margin-bottom:10px;flex-wrap:wrap}button{background:var(--panel2);color:var(--txt);border:1px solid var(--line);border-radius:6px;padding:6px 10px;font-family:inherit;cursor:pointer}button:hover{border-color:var(--blue)}button:disabled{opacity:.55;cursor:wait}.scanning{color:var(--warn);font-weight:700;animation:blinkScan .9s ease-in-out infinite}@keyframes blinkScan{0%,100%{opacity:1}50%{opacity:.18}}
table{width:100%;table-layout:fixed;border-collapse:collapse;background:rgba(19,22,25,.75);border:1px solid var(--line)}col.project-col{width:180px}col.data-col{width:68px}th{color:var(--muted);text-align:left;font-size:11px;letter-spacing:.10em;text-transform:uppercase;padding:12px 6px;border-bottom:1px solid var(--line);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}td{padding:2px 6px;border-bottom:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}tr:hover td{background:rgba(56,189,248,.06)}.project{font-weight:700}.project.dirty{color:var(--warn)}.yes{color:var(--yes);font-weight:700}.no{color:var(--no);font-weight:700}.warn{color:var(--warn);font-weight:700}.okrow td:first-child{border-left:3px solid var(--yes)}.workrow td:first-child{border-left:3px solid var(--warn)}.badrow td:first-child{border-left:3px solid var(--no)}.error{border:1px solid rgba(255,122,69,.55);background:rgba(255,122,69,.08);padding:16px;border-radius:8px;color:var(--no);white-space:pre-wrap}
@media (max-width:640px){.brand{gap:14px}.cards{gap:10px 22px}.netdtl-logo{grid-template-columns:repeat(6,18px)}.netdtl-logo span{height:30px;font-size:14px}}
@media (max-width:460px){.brand{display:block}.netdtl-logo{margin-top:8px;width:max-content}}
</style>
</head>
<body>
<header>
<div class="brand">
<div class="brand-copy">
<h1>DTLaudit <span id="app-version"></span></h1>
<div class="brand-suite">Un outil de la suite NetDTL</div>
<a class="brand-website" href="https://www.netdtl.com/" target="_blank" rel="noopener noreferrer">www.netdtl.com</a>
</div>
<div class="netdtl-logo" role="img" aria-label="Logo NetDTL">
<span>N</span><span>e</span><span>t</span><span>D</span><span>T</span><span>L</span>
</div>
</div>
<div class="subtitle">Tableau de bord d’audit des projets en direct</div>
<div class="meta" id="meta">Prêt à lancer le premier scan...</div>
</header>
<main>
<div class="cards">
<div class="card"><div class="label">Projets</div><div class="value" id="c-projects">-</div></div>
<div class="card"><div class="label">GitHub</div><div class="value" id="c-github">-</div></div>
<div class="card"><div class="label">Docs 4/4</div><div class="value" id="c-docs">-</div></div>
<div class="card"><div class="label">Releases</div><div class="value" id="c-releases">-</div></div>
<div class="card"><div class="label">Modifs</div><div class="value" id="c-changes">-</div></div>
</div>
<div class="toolbar">
<button id="scan-button" type="button">Scanner maintenant</button>
<span>Le dashboard lance DTLaudit toutes les 60 secondes.</span>
<span id="last-refresh"></span>
</div>
<div id="content"></div>
</main>
<script>
const REFRESH_MS=60000;
let scanInProgress=false;
function safe(x){return String(x??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;")}
function yn(x){return x?'<span class="yes">Oui</span>':'<span class="no">Non</span>'}
function hasFile(p,names){return (p.files||[]).some(e=>names.includes(String(e.path||"").toLowerCase()))}
function hasReadmeEn(p){return hasFile(p,["readme.md","readme_en.md"])}
function hasReadmeFr(p){return hasFile(p,["readme_fr.md"])}
function hasReadme(p){return hasReadmeEn(p)||hasReadmeFr(p)}
function docCount(p){const d=p.doc_audit||{};return ["manuel_ref_fr","guide_user_fr","ref_manual_en","user_guide_en"].filter(k=>!!d[k]).length}
function toolVersion(p){return p.tool_version||p.display_version||p.version||p.dtl_version?.display_version||p.dtl_version?.version||"-"}
function visibility(gh){const v=String(gh?.visibility||"").toLowerCase(); if(v==="public") return "public"; if(v==="private"||v==="internal") return "privé"; return "-"}
function render(data){
 const projects=data.projects||[]; const total=projects.length; let ghc=0,docs=0,rel=0,chg=0;
 const rows=projects.slice().sort((a,b)=>a.name.localeCompare(b.name,"fr",{sensitivity:"base"})).map(p=>{
  const g=p.git||{}, gh=p.github||{}, d=p.doc_audit||{}; const hasGh=!!(g.remote_github||gh.available); const hasRel=!!gh.latest_release; const m=Number(g.changed_files||0); const dc=docCount(p);
  ghc+=hasGh?1:0; docs+=dc===4?1:0; rel+=hasRel?1:0; chg+=m;
  let cls="okrow"; if(!g.present||!hasGh||!hasReadme(p)) cls="badrow"; else if(m>0||dc<4||!hasRel) cls="workrow";
  const version=toolVersion(p);
  const vis=visibility(gh);
  const projectClass=m>0?"project dirty":"project";
  return `<tr class="${cls}"><td class="${projectClass}" title="${safe(p.name)}">${safe(p.name)}</td><td class="version" title="${safe(version)}">${safe(version)}</td><td>${yn(!!g.present)}</td><td class="github">${yn(hasGh)}</td><td>${safe(g.branch||"-")}</td><td class="visibility" title="${safe(vis)}">${safe(vis)}</td><td>${yn(hasReadmeEn(p))}</td><td>${yn(hasReadmeFr(p))}</td><td>${yn(!!d.manuel_ref_fr)}</td><td>${yn(!!d.guide_user_fr)}</td><td>${yn(!!d.ref_manual_en)}</td><td>${yn(!!d.user_guide_en)}</td><td>${yn(hasRel)}</td><td>${m?`<span class="warn">${m}</span>`:'<span class="yes">0</span>'}</td></tr>`;
 }).join("");
 document.getElementById("c-projects").textContent=total;
 document.getElementById("c-github").textContent=`${ghc}/${total}`;
 document.getElementById("c-docs").textContent=`${docs}/${total}`;
 document.getElementById("c-releases").textContent=`${rel}/${total}`;
 document.getElementById("c-changes").textContent=chg;
 document.getElementById("app-version").textContent=data.version||"";
 document.getElementById("meta").textContent=`Racine : ${data.root||""}`;
 document.getElementById("content").innerHTML=`<table><colgroup><col class="project-col"><col class="data-col" span="13"></colgroup><thead><tr><th>Projet</th><th>Version</th><th>Git</th><th>GitHub</th><th>Branche</th><th>Visib.</th><th>README En</th><th>README Fr</th><th>RF Fr</th><th>UG Fr</th><th>RF En</th><th>UG En</th><th>Release</th><th>Modifs</th></tr></thead><tbody>${rows}</tbody></table>`;
}
async function loadReport(force=false){
  if(scanInProgress) return;
  scanInProgress=true;

  const status=document.getElementById("last-refresh");
  const button=document.getElementById("scan-button");

  if(button){
    button.disabled=true;
    button.textContent="Scan en cours...";
  }

  status.textContent="Scan en cours...";
  status.classList.add("scanning");

  try {
    const r = await fetch("?action=scan&force="+(force?"1":"0")+"&t="+Date.now(), {cache:"no-store"});
    const text = await r.text();

    if (!text.trim()) {
      throw new Error("Réponse vide de DTLaudit_dashboard_live.php?action=scan");
    }

    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      console.error("Réponse brute reçue :", text);
      throw new Error("Réponse JSON invalide de DTLaudit");
    }

    if (data.ok === false) {
      throw new Error(data.error || "DTLaudit a retourné une erreur");
    }

    render(data);
    status.textContent="Dernier scan : " + new Date().toLocaleString();

  } catch(e) {
    const msg = e && e.message ? e.message : String(e);

    document.getElementById("content").innerHTML = `
      <div class="error">
        <b>%DTLaudit_dashboard_live-E-CONNECTION</b><br><br>

        Impossible de contacter DTLaudit.<br>
        Vérifier que le serveur Apache a été lancé.<br>
        Vérifier également que DTLaudit.py est installé dans le répertoire du dashboard.<br><br>

        <details>
          <summary>Détail technique</summary>
          <pre>${msg}</pre>
        </details>
      </div>
    `;

    status.textContent="Erreur";
  } finally {
    scanInProgress=false;
    status.classList.remove("scanning");

    if(button){
      button.disabled=false;
      button.textContent="Relancer le scan";
    }
  }
}
document.getElementById("scan-button").addEventListener("click", function(){
  loadReport(true);
});

loadReport(false);

setInterval(function(){
  loadReport(false);
}, REFRESH_MS);
</script>
</body>
</html>
