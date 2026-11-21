'use strict';
/* global state, command */

(() => {
  const root = document.getElementById('live-chat');
  if (!root) return;
  const body = document.getElementById('live-chat-body');
  const messagesElement = document.getElementById('live-chat-messages');
  const statusElement = document.getElementById('live-chat-status');
  const form = document.getElementById('live-chat-form');
  const input = document.getElementById('live-chat-input');
  const recipient = document.getElementById('live-chat-recipient');
  const recipientLabel = document.getElementById('live-chat-recipient-label');
  const tabs = [...document.querySelectorAll('[data-live-channel]')];
  let socket = null;
  let reconnectTimer = null;
  let reconnectDelay = 1000;
  let activeChannel = 'world';
  let snapshot = {messages: {world: [], alliance: [], system: [], private: []}};
  const known = new Set();
  const unread = {world: 0, alliance: 0, system: 0, private: 0};

  function translate(key, fallback) {
    const value = globalThis.FURI18n?.t(key);
    return value && value !== key ? value : fallback;
  }

  function setStatus(key, fallback, connected = false) {
    statusElement.textContent = translate(key, fallback);
    root.classList.toggle('connected', connected);
  }

  function updateRecipients() {
    const previous = recipient.value;
    const blocked = new Set((state?.social?.blocked || []).map(person => person.id));
    recipient.replaceChildren();
    for (const player of state?.players || []) {
      if (player.id === state.id || blocked.has(player.id)) continue;
      const option = document.createElement('option');
      option.value = player.name;
      option.textContent = player.name;
      recipient.append(option);
    }
    if ([...recipient.options].some(option => option.value === previous)) recipient.value = previous;
  }

  function renderTabs() {
    for (const tab of tabs) {
      const channel = tab.dataset.liveChannel;
      tab.classList.toggle('selected', channel === activeChannel);
      tab.setAttribute('aria-selected', String(channel === activeChannel));
      const badge = tab.querySelector('b');
      badge.textContent = String(unread[channel]);
      badge.hidden = unread[channel] === 0;
      if (channel === 'alliance') tab.disabled = !snapshot.alliance_id;
    }
  }

  function messageNode(message) {
    const article = document.createElement('article');
    article.className = `live-chat-message ${message.channel === 'system' ? 'system' : ''}`;
    article.dataset.messageId = message.id;
    const header = document.createElement('div');
    const name = document.createElement('strong');
    name.textContent = message.name;
    const time = document.createElement('time');
    time.dateTime = new Date(message.created * 1000).toISOString();
    time.textContent = new Intl.DateTimeFormat(globalThis.FURI18n?.locale || 'de-DE', {
      hour: '2-digit', minute: '2-digit'
    }).format(message.created * 1000);
    header.append(name, time);
    const text = document.createElement('p');
    text.textContent = message.body;
    article.append(header, text);
    return article;
  }

  function renderMessages() {
    const atEnd = messagesElement.scrollHeight - messagesElement.scrollTop - messagesElement.clientHeight < 32;
    const previousHeight = messagesElement.scrollHeight;
    const list = [...(snapshot.messages[activeChannel] || [])].reverse();
    messagesElement.replaceChildren(...list.map(messageNode));
    if (atEnd) messagesElement.scrollTop = messagesElement.scrollHeight;
    else messagesElement.scrollTop += messagesElement.scrollHeight - previousHeight;
    recipientLabel.hidden = activeChannel !== 'private';
    const readOnly = activeChannel === 'system';
    form.classList.toggle('read-only', readOnly);
    input.disabled = readOnly;
    form.querySelector('[type="submit"]').disabled = readOnly;
    input.placeholder = readOnly
      ? translate('chat.system_readonly', 'Systemmeldungen sind schreibgeschützt.')
      : translate('chat.placeholder', 'Nachricht schreiben …');
    updateRecipients();
  }

  function receive(data) {
    if (data.type !== 'snapshot' || !data.messages) return;
    const first = known.size === 0;
    for (const [channel, list] of Object.entries(data.messages)) {
      for (const message of list) {
        if (!known.has(message.id) && !first && channel !== activeChannel) unread[channel] += 1;
        known.add(message.id);
      }
    }
    snapshot = data;
    renderTabs();
    renderMessages();
  }

  function scheduleReconnect() {
    clearTimeout(reconnectTimer);
    if (document.getElementById('game').hidden) return;
    reconnectTimer = setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 15000);
  }

  function connect() {
    if (document.getElementById('game').hidden || socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) return;
    setStatus('chat.connecting', 'Verbindung wird hergestellt …');
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${protocol}//${location.host}/api/v1/chat/live`);
    socket.addEventListener('open', () => {
      reconnectDelay = 1000;
      setStatus('chat.connected', 'Live verbunden', true);
    });
    socket.addEventListener('message', event => {
      try { receive(JSON.parse(event.data)); }
      catch { setStatus('chat.invalid_data', 'Ungültige Chatdaten'); }
    });
    socket.addEventListener('close', event => {
      socket = null;
      if (event.code === 4401) setStatus('chat.signed_out', 'Sitzung beendet');
      else {
        setStatus('chat.reconnecting', 'Verbindung unterbrochen · neuer Versuch …');
        scheduleReconnect();
      }
    });
    socket.addEventListener('error', () => socket?.close());
  }

  for (const tab of tabs) tab.addEventListener('click', () => {
    activeChannel = tab.dataset.liveChannel;
    unread[activeChannel] = 0;
    renderTabs();
    renderMessages();
  });

  document.getElementById('live-chat-toggle').addEventListener('click', event => {
    const collapsed = root.classList.toggle('collapsed');
    body.hidden = collapsed;
    event.currentTarget.setAttribute('aria-expanded', String(!collapsed));
    event.currentTarget.textContent = collapsed ? '▴' : '▾';
    try { localStorage.setItem('fur.chat.collapsed', String(collapsed)); } catch { /* optional */ }
  });

  document.getElementById('live-chat-emoji').addEventListener('click', () => {
    const picker = document.getElementById('live-chat-emojis');
    picker.hidden = !picker.hidden;
  });
  document.querySelectorAll('#live-chat-emojis button').forEach(button => button.addEventListener('click', () => {
    input.setRangeText(button.textContent, input.selectionStart, input.selectionEnd, 'end');
    input.focus();
  }));
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const bodyText = input.value.trim();
    if (!bodyText || activeChannel === 'system') return;
    const payload = {channel: activeChannel, body: bodyText};
    if (activeChannel === 'private') {
      if (!recipient.value) return;
      payload.name = recipient.value;
    }
    input.disabled = true;
    try {
      if (await command('message', payload)) input.value = '';
    } finally {
      input.disabled = false;
      input.focus();
    }
  });

  try {
    const collapsed = localStorage.getItem('fur.chat.collapsed') === 'true';
    root.classList.toggle('collapsed', collapsed);
    body.hidden = collapsed;
  } catch { /* optional */ }
  window.addEventListener('fur:session-started', connect);
  window.addEventListener('fur:session-ended', () => {
    clearTimeout(reconnectTimer);
    socket?.close(1000);
    socket = null;
    known.clear();
  });
  window.addEventListener('fur:language-changed', () => {
    renderMessages();
    if (socket?.readyState === WebSocket.OPEN) setStatus('chat.connected', 'Live verbunden', true);
  });
  setInterval(connect, 1000);
})();
