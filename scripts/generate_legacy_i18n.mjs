import {createRequire} from 'node:module';
import {readFile, writeFile} from 'node:fs/promises';

const require = createRequire(import.meta.url);
const espree = require('espree');
const sourceFiles = ['static/app.js', 'static/community.js'];
const htmlFiles = ['static/index.html'];
const targets = ['en', 'es', 'fr'];
const outputPath = 'static/locales/legacy-ui.json';
const germanMarkers = /[äöüÄÖÜß]|\b(?:abbrechen|abgelaufen|ablehnen|aktiv|allianz|allianzen|angriff|angriffe|annehmen|anzeigen|archivieren|auftrag|ausbau|ausführen|ausgehende|auswählen|außenposten|beitritt|benötigt|bericht|berichte|bestätigen|blockieren|einheiten|einstellungen|einzahlen|entwurf|erfolg|erreicht|erz|flotte|flotten|forschung|gebäude|gefecht|gelände|gemeinsam|gespeichert|grenzgebiete|handel|heimat|hinflug|holz|keine|keinen|keiner|kolonie|kolonien|kommandant|kommando|krieg|laden|leitung|markt|meldung|meldungen|mission|nachricht|nachrichten|notiz|offen|punkte|produktionsgrafik|rangliste|regel|regeln|ressourcen|rückflug|schließen|schiffe|sektor|senden|sicherheit|spieler|speichern|stein|strategiespiel|stufe|synchronisiert|system|truppen|verfügbar|verteidigung|voll|vorlage|welt|welten|zurück|zurückrufen)\b/i;

function walk(value, visit) {
  if (!value || typeof value !== 'object') return;
  visit(value);
  for (const child of Object.values(value)) {
    if (Array.isArray(child)) child.forEach(item => walk(item, visit));
    else walk(child, visit);
  }
}

function visibleFragments(value) {
  return value
    .replace(/<[^>]*>/g, '\n')
    .replace(/&(?:nbsp|amp|lt|gt|quot|#39);/g, ' ')
    .split(/\r?\n/)
    .map(item => item.replace(/\\n/g, ' ').replace(/\s+/g, ' ').trim())
    .filter(item => item.length > 1 && item.length <= 900 && (
      germanMarkers.test(item) || (/\s/.test(item) && /[A-Z][a-z]/.test(item))
    ))
    .filter(item => !item.startsWith('/') && !/^[.#\[\]a-z0-9_-]+$/i.test(item));
}
const phrases = new Set();
for (const file of htmlFiles) {
  const source = await readFile(file, 'utf8');
  visibleFragments(source).forEach(value => phrases.add(value));
  for (const match of source.matchAll(/(?:aria-label|placeholder|title)="([^"]+)"/g)) {
    visibleFragments(match[1]).forEach(value => phrases.add(value));
  }
}

for (const file of sourceFiles) {
  const source = await readFile(file, 'utf8');
  const tree = espree.parse(source, {ecmaVersion: 'latest', sourceType: 'script'});
  walk(tree, node => {
    if (node.type === 'Literal' && typeof node.value === 'string') {
      visibleFragments(node.value).forEach(value => phrases.add(value));
    }
    if (node.type === 'TemplateElement') {
      visibleFragments(node.value.raw).forEach(value => phrases.add(value));
    }
  });
}

const sorted = [...phrases].sort((left, right) => left.localeCompare(right, 'de'));
let previous = {};
try { previous = JSON.parse(await readFile(outputPath, 'utf8')); } catch { /* First generation. */ }
const output = {de: Object.fromEntries(sorted.map(value => [value, value]))};
for (const target of targets) output[target] = Object.fromEntries(
  sorted.filter(phrase => previous[target]?.[phrase]).map(phrase => [phrase, previous[target][phrase]])
);
async function checkpoint() {
  await writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
}

async function translate(text, target) {
  const params = new URLSearchParams({client: 'gtx', sl: 'de', tl: target, dt: 't', q: text});
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      const response = await fetch(`https://translate.googleapis.com/translate_a/single?${params}`);
      if (response.ok) {
        const payload = await response.json();
        return payload[0].map(part => part[0]).join('');
      }
    } catch { /* Retry a transient connection failure. */ }
    await new Promise(resolve => setTimeout(resolve, 1500 * (attempt + 1)));
  }
  throw new Error(`Übersetzung fehlgeschlagen (${target}): ${text}`);
}

for (const target of targets) {
  const translated = output[target];
  let nextIndex = 0;
  let completed = 0;
  async function worker() {
    while (nextIndex < sorted.length) {
      const index = nextIndex;
      nextIndex += 1;
      const phrase = sorted[index];
      if (!translated[phrase]) translated[phrase] = await translate(phrase, target);
      completed += 1;
      if (completed % 50 === 0) {
        process.stdout.write(`${target}: ${completed}/${sorted.length}\n`);
        await checkpoint();
      }
    }
  }
  await Promise.all(Array.from({length: 2}, () => worker()));
  await checkpoint();
}

await checkpoint();
process.stdout.write(`legacy-ui.json: ${sorted.length} Textfragmente × 4 Sprachen\n`);
