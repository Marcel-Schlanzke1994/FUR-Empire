#!/usr/bin/env python3
"""Validiert Vollständigkeit des FUR EMPIRE Masterpakets, nicht den eigentlichen Spielcode."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
REQUIRED = [
 '00_START_HIER.md','AGENTS.md','agent/AGENTS.md','agent/AGENT_START_PROMPT.md',
 'agent/BUILD_LOOP.md','agent/RESUME_PROMPT.md',
 *[f'docs/{i:02d}_{n}.md' for i,n in [
   (1,'MASTER_GAME_DESIGN'),(2,'TECHNICAL_CONTRACTS'),(3,'IMPLEMENTATION_ROADMAP'),
   (4,'SECURITY_OPERATIONS_LIVE'),(5,'TEST_STRATEGY'),(6,'SOURCE_LICENSE_REGISTER'),
   (7,'COMPLETE_SCREEN_AND_GAMEPLAY_MATRIX'),(8,'GAME_MECHANICS_STATE_MACHINES'),
   (9,'AGENT_ACCEPTANCE_AND_OWNER_HANDOFF')]],
 'spec/FEATURES.json','spec/FEATURES.csv','spec/FEATURE_INDEX.md','spec/FEATURES.schema.json',
 'rulesets/FUR_2_REFERENCE_RULES.json','rulesets/FUR_3_ORBIT_1_PROPOSED_RULES.json',
 'reference/SPIELANLEITUNG_FUR2_ORIGINAL.md','reference/FUR2_55_GAPS_ORIGINAL.json',
 'reference/9_REPOSITORY_ANALYSIS.md','scripts/validate_package.py',
]
errors=[]
for f in REQUIRED:
    p=P/f
    if not p.is_file() or p.stat().st_size<=10:errors.append(f'Fehlt/leer: {f}')
data=json.loads((P/'spec/FEATURES.json').read_text(encoding='utf8'))
features=data['features']
ids=[f['id'] for f in features]
if len(ids)!=len(set(ids)):errors.append('IDs nicht eindeutig')
if len(features)!=data['total'] or len(features)<300:errors.append('Featureliste unvollständig oder Count falsch')
origins={v['origin'] for v in features}
for key in {'fur2_documented','gap_from_prior_review','new_design'}:
    if key not in origins:errors.append(f'Quelle fehlt: {key}')
old=json.loads((P/'reference/FUR2_55_GAPS_ORIGINAL.json').read_text(encoding='utf8'))
missing={f['id'] for f in old['items']}-set(ids)
if missing:errors.append(f'Original-55 fehlen: {sorted(missing)}')
for f in features:
    if not f.get('behavior_contract') or len(f['behavior_contract'])<15:errors.append('Ungenügender Vertrag '+f['id'])
    if len(f.get('acceptance',[]))<3:errors.append('Zu wenige Akzeptanzkriterien '+f['id'])
    if f.get('status')=='verified':errors.append('Initial-Paket darf keine ungeprüft verifizierte Funktion behaupten')
for p in P.rglob('*'):
    if p.suffix=='.json' and p.is_file():
        try:json.loads(p.read_text(encoding='utf8'))
        except Exception as e:errors.append(f'Ungültiges JSON {p.name}: {e}')
    if p.is_file() and p.suffix in {'.md','.json','.py','.csv'}:
        c=p.read_text(encoding='utf8')
        for pat in [r'github_pat_[A-Za-z0-9_]{25,}',r'ghp_[A-Za-z0-9]{30,}',r'(?<![\w-])sk-proj-[A-Za-z0-9_-]{30,}',r'https://discord\.com/api/webhooks/\d+/[A-Za-z0-9_-]{25,}']:
            if re.search(pat,c):errors.append('Verdacht auf offengelegtes Secret in '+str(p.relative_to(P)))
if errors:
    print('Paket ungültig:')
    for x in errors:print('ERROR:',x)
    sys.exit(1)
print(f'PASS — Paketstruktur vollständig, {len(features)} eindeutige Features, {len(old["items"])} Ursprungs-Lücken übernommen, JSON gültig, keine bekannten Secret-Muster.')
print('Hinweis: Dieses Prüfsystem validiert die SPEZIFIKATION, nicht die spätere vollständige Spielimplementierung.')
