'use strict';
window.FURI18n = (() => {
  const supported = ['de', 'en', 'es', 'fr'];
  const locales = {de: 'de-DE', en: 'en-GB', es: 'es-ES', fr: 'fr-FR'};
  let language = 'de';
  let catalogs = {};
  function translate(key, values = {}) {
    const template = catalogs[language]?.[key] ?? catalogs.de?.[key] ?? key;
    return template.replace(/\{(\w+)\}/g, (match, name) => Object.hasOwn(values, name) ? String(values[name]) : match);
  }
  function apply(root = document) {
    function valuesFor(element) {
      let values = {};
      try { values = JSON.parse(element.getAttribute?.('data-i18n-values') || '{}'); } catch { /* Keep safe placeholder fallback. */ }
      return values && typeof values === 'object' ? values : {};
    }
    root.querySelectorAll('[data-i18n]').forEach(element => {
      const translated = translate(element.dataset.i18n, valuesFor(element));
      if (translated !== element.dataset.i18n) element.textContent = translated;
    });
    for (const attribute of ['placeholder', 'aria-label', 'title']) {
      root.querySelectorAll('[data-i18n-' + attribute + ']').forEach(element => {
        const key = element.getAttribute('data-i18n-' + attribute);
        const translated = translate(key, valuesFor(element));
        if (translated !== key) element.setAttribute(attribute, translated);
      });
    }
    document.documentElement.lang = language;
  }
  function setLanguage(value) {
    language = supported.includes(value) ? value : 'de';
    try { localStorage.setItem('fur.language', language); } catch { /* Storage may be unavailable. */ }
    apply();
    document.querySelectorAll('[data-language-select]').forEach(select => { select.value = language; });
    window.dispatchEvent(new CustomEvent('fur:language-changed', {detail: {language}}));
  }
  function localizeCatalog(gameCatalog) {
    for (const kind of ['buildings', 'tech', 'units']) {
      for (const [id, item] of Object.entries(gameCatalog?.[kind] || {})) {
        for (const field of ['name', 'description']) {
          const key = 'catalog.' + kind + '.' + id + '.' + field;
          if (catalogs.de?.[key]) item[field] = translate(key);
        }
      }
    }
  }
  function reportText(report, field) {
    const key = report[field + '_key'];
    if (!key) return report[field];
    const values = {...report.message_params};
    if (values.label_key) {
      const label = translate(values.label_key);
      if (label !== values.label_key) values.label = label;
    }
    for (const name of Object.keys(values)) {
      if (typeof values[name] === 'number') values[name] = new Intl.NumberFormat(locales[language]).format(values[name]);
    }
    const text = translate(key, values);
    return text === key ? report[field] : text;
  }
  const ready = Promise.all(supported.map(async code => {
    try {
      const response = await fetch(`/static/locales/${code}.json`);
      if (!response.ok) return [code, {}];
      return [code, await response.json()];
    } catch {
      return [code, {}];
    }
  })).then(entries => {
    catalogs = Object.fromEntries(entries);
    let saved;
    try { saved = localStorage.getItem('fur.language'); } catch { /* Use browser preference. */ }
    const browser = (navigator.languages || [navigator.language]).map(value => value.split('-')[0]).find(value => supported.includes(value));
    document.querySelectorAll('[data-language-select]').forEach(select => { select.addEventListener('change', () => setLanguage(select.value)); });
    setLanguage(saved || browser || 'de');
  });
  return {
    ready, t: translate, apply, setLanguage, localizeCatalog, reportText,
    get language() { return language; },
    get locale() { return locales[language]; },
    number(value, options = {}) { return new Intl.NumberFormat(locales[language], options).format(value); },
    date(value, options = {}) { return new Intl.DateTimeFormat(locales[language], options).format(value); }
  };
})();
