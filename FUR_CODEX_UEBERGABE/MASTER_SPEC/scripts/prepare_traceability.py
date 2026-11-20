#!/usr/bin/env python3
"""Initialisiert Beweismatrix/Resume-State ohne einen Implementierungsnachweis vorzutäuschen."""
from pathlib import Path
import json,sys,csv
P=Path(__file__).resolve().parents[1]
project=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
if not project.is_dir():raise SystemExit('Projektverzeichnis existiert nicht')
items=json.loads((P/'spec/FEATURES.json').read_text(encoding='utf8'))['features']
p=project/'TRACEABILITY.md'
if p.exists():raise SystemExit('TRACEABILITY.md existiert bereits. Nicht überschreiben.')
with p.open('w',encoding='utf8') as f:
    f.write('# FUR EMPIRE — feature proof matrix\n\n')
    f.write('| ID | Titel | Priority | Code | Migration | API | UI | Policy | Tests | Doku | Status |\n|---|---|---|---|---|---|---|---|---|---|---|\n')
    for item in items:
        title=item['title'].replace('|','/')
        f.write(f'| {item["id"]} | {title} | {item["priority"]} | — | — | — | — | — | — | — | not_verified |\n')
r=project/'RESUME_STATE.json'
if not r.exists():r.write_text(json.dumps({'project':'FUR EMPIRE','stage':'E00','git_commit':None,'git_branch':None,'last_verified_feature':None,'feature_count':len(items),'next_actions':['Audit current repository','Run baseline tests','Protect data backup','Update TRACEABILITY with evidence'],'external_blockers':[],'test_commands':[],'last_results':[],'note':'Template, no game implementation is claimed.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for name,text in {'PROGRESS_LOG.md':'# FUR EMPIRE — PROGRESS\n\n','OWNER_HANDOFF.md':'# FUR EMPIRE — externe Betreiberaktionen\n\n','AUDIT_CURRENT_FUR2.md':'# FUR-2 Audit — erst mit echten Repo-Belegen ausfüllen\n\n'}.items():
    f=project/name
    if not f.exists():f.write_text(text,encoding='utf8')
print(f'Initialisiert {p}; {len(items)} IDs. Keine vorhandenen Dateien überschrieben.')
