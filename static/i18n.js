'use strict';
window.FURI18n = (() => {
  const supported = ['de', 'en', 'es', 'fr'];
  const locales = {de: 'de-DE', en: 'en-GB', es: 'es-ES', fr: 'fr-FR'};
  let language = 'de';
  let catalogs = {};
  let legacyCatalogs = {};
  const originalText = new WeakMap();
  const originalAttributes = new WeakMap();
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
    applyLegacy(root);
    document.documentElement.lang = language;
  }
  function legacyText(value) {
    if (!value || language === 'de') return value;
    const direct = legacyCatalogs[language]?.[value];
    if (direct) return direct;
    const trimmed = value.trim();
    const translated = legacyCatalogs[language]?.[trimmed];
    if (!translated) return value;
    const start = value.indexOf(trimmed);
    return value.slice(0, start) + translated + value.slice(start + trimmed.length);
  }
  function excludedLegacyNode(element) {
    return Boolean(element?.closest?.(
      '[translate="no"], [data-user-content], #commander, #live-chat-messages, #mail-preview, '
      + 'textarea, .message p, .message-body, .bulletin-entry h4, .bulletin-entry p, '
      + '.forum-thread-heading h4, .forum-post-heading b, .forum-post p, .forum-report p, '
      + '.private-note-body, .rank b, .map-target b, .target-row b'
    ));
  }
  function applyLegacy(root = document) {
    if (!document.createTreeWalker || !legacyCatalogs[language]) return;
    const scope = root === document
      ? [...document.querySelectorAll('#content, #mission, #account-dialog, #ban-appeal, aside, main > header, main > footer')]
      : [root];
    for (const container of scope) {
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (excludedLegacyNode(node.parentElement)) continue;
        if (!originalText.has(node)) originalText.set(node, node.nodeValue);
        node.nodeValue = legacyText(originalText.get(node));
      }
      for (const element of container.querySelectorAll?.('[placeholder], [aria-label], [title]') || []) {
        if (excludedLegacyNode(element)) continue;
        let originals = originalAttributes.get(element);
        if (!originals) {
          originals = {};
          originalAttributes.set(element, originals);
        }
        for (const attribute of ['placeholder', 'aria-label', 'title']) {
          if (!element.hasAttribute(attribute) || element.hasAttribute(`data-i18n-${attribute}`)) continue;
          if (!Object.hasOwn(originals, attribute)) originals[attribute] = element.getAttribute(attribute);
          element.setAttribute(attribute, legacyText(originals[attribute]));
        }
      }
    }
  }
  function setLanguage(value) {
    language = supported.includes(value) ? value : 'de';
    try { localStorage.setItem('fur.language', language); } catch { /* Storage may be unavailable. */ }
    apply();
    document.title = `${translate('app.title')} · FUR EMPIRE`;
    const labels = [
      ['[data-language-select]', 'language'],
      ['aside nav', 'aria.game_areas'],
      ['#live-chat-tabs', 'aria.chat_channels'],
      ['#live-chat-emoji', 'aria.emoji']
    ];
    for (const [selector, key] of labels) document.querySelector?.(selector)?.setAttribute('aria-label', translate(key));
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
  const catalogReady = Promise.all(supported.map(async code => {
    try {
      const response = await fetch(`/static/locales/${code}.json`);
      if (!response.ok) return [code, {}];
      return [code, await response.json()];
    } catch {
      return [code, {}];
    }
  })).then(entries => { catalogs = Object.fromEntries(entries); });
  const legacyReady = fetch('/static/locales/legacy-ui.json')
    .then(response => response.ok ? response.json() : {})
    .catch(() => ({}));
  const ready = Promise.all([catalogReady, legacyReady]).then(([, legacy]) => {
    legacyCatalogs = legacy;
    let saved;
    try { saved = localStorage.getItem('fur.language'); } catch { /* Use browser preference. */ }
    const browser = (navigator.languages || [navigator.language]).map(value => value.split('-')[0]).find(value => supported.includes(value));
    document.querySelectorAll('[data-language-select]').forEach(select => { select.addEventListener('change', () => setLanguage(select.value)); });
    setLanguage(saved || browser || 'de');
  });
  return {
    ready, t: translate, apply, setLanguage, localizeCatalog, reportText, legacyText,
    get language() { return language; },
    get locale() { return locales[language]; },
    number(value, options = {}) { return new Intl.NumberFormat(locales[language], options).format(value); },
    date(value, options = {}) { return new Intl.DateTimeFormat(locales[language], options).format(value); }
  };
})();
