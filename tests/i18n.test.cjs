const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

async function setup(browserLanguage, saved, unavailable = '') {
  const storage = new Map(saved ? [['fur.language', saved]] : []);
  const events = [];
  const label = {dataset: {i18n: 'auth.login'}, textContent: 'Einloggen →'};
  const document = {
    documentElement: {},
    querySelectorAll: selector => selector === '[data-i18n]' ? [label] : []
  };
  const window = {dispatchEvent: event => events.push(event)};
  const context = vm.createContext({
    window, document, Intl,
    navigator: {languages: [browserLanguage]},
    localStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value)},
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
    fetch: async url => {
      const code = url.split('/').pop().replace('.json', '');
      return {ok: code !== unavailable, json: async () => JSON.parse(fs.readFileSync(path.join(__dirname, '../static/locales', code + '.json'), 'utf8'))};
    }
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/i18n.js'), 'utf8'), context);
  await window.FURI18n.ready;
  return {i18n: window.FURI18n, storage, document, label, events};
}

for (const language of ['de', 'en', 'es', 'fr']) {
  test('browser selection and persistent switching for ' + language, async () => {
    const {i18n, storage, document, label} = await setup(language + '-XX');
    assert.equal(i18n.language, language);
    assert.equal(document.documentElement.lang, language);
    assert.equal(document.title, `${i18n.t('app.title')} · FUR EMPIRE`);
    assert.equal(label.textContent, i18n.t('auth.login'));
    assert.equal(i18n.number(12345.6), new Intl.NumberFormat(i18n.locale).format(12345.6));
    i18n.setLanguage('fr');
    assert.equal(storage.get('fur.language'), 'fr');
    assert.equal(document.title, 'Frontières · FUR EMPIRE');
  });
}
test('saved language overrides browser and missing catalog falls back to German', async () => {
  const saved = await setup('en-US', 'es');
  assert.equal(saved.i18n.language, 'es');
  const fallback = await setup('fr-FR', null, 'fr');
  assert.equal(fallback.i18n.t('auth.login'), 'Einloggen →');
  fallback.i18n.setLanguage('unsupported');
  assert.equal(fallback.i18n.language, 'de');
});

test('catalog language changes preserve game identifiers and numeric rules', async () => {
  const {i18n} = await setup('en-GB');
  const gameCatalog = {buildings: {hq: {name: 'Kommandozentrale', cost: [150, 120, 80], requirements: {hq: 1}}}};
  i18n.localizeCatalog(gameCatalog);
  assert.equal(gameCatalog.buildings.hq.name, 'Command centre');
  assert.deepEqual(gameCatalog.buildings.hq.cost, [150, 120, 80]);
  i18n.setLanguage('fr');
  i18n.localizeCatalog(gameCatalog);
  assert.equal(gameCatalog.buildings.hq.name, 'Centre de commandement');
  i18n.setLanguage('de');
  i18n.localizeCatalog(gameCatalog);
  assert.equal(gameCatalog.buildings.hq.name, 'Kommandozentrale');
  assert.deepEqual(gameCatalog.buildings.hq.requirements, {hq: 1});
});

test('dynamic player names remain text during translation', async () => {
  const {i18n, label} = await setup('en-GB');
  const name = '<img src=x onerror=alert(1)>';
  label.dataset.i18n = 'overview.welcome';
  label.getAttribute = attribute => attribute === 'data-i18n-values' ? JSON.stringify({name}) : null;
  i18n.apply();
  assert.equal(label.textContent, 'Welcome back, ' + name + '. Your next move changes this world.');
  assert.equal(label.innerHTML, undefined);
  label.getAttribute = () => '{invalid';
  assert.doesNotThrow(() => i18n.apply());
  assert.match(label.textContent, /\{name\}/);
});

test('structured reports translate parameters and retain historical text fallback', async () => {
  const {i18n} = await setup('en-GB');
  const report = {title:'Auftrag abgeschlossen', body:'Original', title_key:'report.order_title', body_key:'report.order_body', message_params:{label:'Bioforst',label_key:'catalog.buildings.wood.name',level:2}};
  assert.equal(i18n.reportText(report,'title'), 'Order completed');
  assert.equal(i18n.reportText(report,'body'), 'Bioforest is now level 2.');
  assert.equal(i18n.reportText({body:'Historic report'},'body'), 'Historic report');
  i18n.setLanguage('fr');
  assert.equal(i18n.reportText(report,'body'), 'Bioforêt atteint le niveau 2.');
});

test('queue accessibility labels interpolate names as text attributes', async () => {
  const {i18n} = await setup('en');
  const attributes = {'data-i18n-aria-label':'queue.cancel_label','data-i18n-values':JSON.stringify({label:'<Commander & "ally">'})};
  const element = {getAttribute:key=>attributes[key],setAttribute:(key,value)=>{attributes[key]=value;}};
  i18n.apply({querySelectorAll:selector=>selector==='[data-i18n-aria-label]'?[element]:[]});
  assert.equal(attributes['aria-label'],'Cancel <Commander & "ally">');
  i18n.setLanguage('fr');
  i18n.apply({querySelectorAll:selector=>selector==='[data-i18n-aria-label]'?[element]:[]});
  assert.equal(attributes['aria-label'],'Annuler <Commander & "ally">');
});

test('all supported catalogs preserve translation keys and interpolation parameters', () => {
  const load = code => JSON.parse(fs.readFileSync(path.join(__dirname, '../static/locales', code + '.json'), 'utf8'));
  const baseline = load('de');
  const parameters = text => [...new Set([...text.matchAll(/\{(\w+)\}/g)].map(match => match[1]))].sort();
  for (const code of ['en', 'es', 'fr']) {
    const catalog = load(code);
    assert.deepEqual(Object.keys(catalog).sort(), Object.keys(baseline).sort(), code);
    for (const [key, value] of Object.entries(baseline)) {
      assert.equal(typeof catalog[key], 'string', code + ':' + key);
      assert.deepEqual(parameters(catalog[key]), parameters(value), code + ':' + key);
    }
  }
});

test('legacy UI catalog covers the same source fragments in all four languages', async () => {
  const legacy = JSON.parse(fs.readFileSync(path.join(__dirname, '../static/locales/legacy-ui.json'), 'utf8'));
  const source = Object.keys(legacy.de).sort();
  assert.ok(source.length >= 800);
  for (const code of ['en', 'es', 'fr']) {
    assert.deepEqual(Object.keys(legacy[code]).sort(), source, code);
    assert.equal(Object.values(legacy[code]).every(value => typeof value === 'string' && value.length > 0), true, code);
  }
  const {i18n} = await setup('en-GB');
  assert.equal(i18n.legacyText('Gemeinsame Terra-Angriffe'), 'Joint Terra Attacks');
  assert.equal(i18n.legacyText('Spieler Gemeinsame Terra-Angriffe'), 'Spieler Gemeinsame Terra-Angriffe');
  i18n.setLanguage('fr');
  assert.equal(i18n.legacyText('Gemeinsame Terra-Angriffe'), legacy.fr['Gemeinsame Terra-Angriffe']);
  i18n.setLanguage('de');
  assert.equal(i18n.legacyText('Gemeinsame Terra-Angriffe'), 'Gemeinsame Terra-Angriffe');
});
