'use strict';
// Additional views share the same authenticated state and command pipeline.
const systemTabs = ['alliance', 'messages', 'market', 'worldops', 'account', 'admin'];
const factionNames = {pioneers:'Pioniere',wardens:'Wächterbund',syndicate:'Syndikat'};
let messageChannel = 'world';
let accountSessionSnapshot = null, accountSessionSnapshotOwner = '', accountSessionSnapshotAt = 0;
function clearAccountSessionSnapshot() { accountSessionSnapshot = null; accountSessionSnapshotOwner = ''; accountSessionSnapshotAt = 0; }
if(typeof window!=='undefined') {
  window.addEventListener('fur:session-started',clearAccountSessionSnapshot);
  window.addEventListener('fur:session-ended',clearAccountSessionSnapshot);
}
function initSystems() {
  const nav=document.querySelector('nav');
  const before=nav.querySelector('[data-tab=help]');
  for(const [key,label,icon] of [['alliance','Allianz','alliance'],['messages','Nachrichten','messages'],['market','Spielermarkt','trade'],['worldops','Weltbetrieb','administration'],['account','Kontosicherheit','security'],['admin','Spielleitung','administration']]) {
    const button=document.createElement('button');button.dataset.tab=key;button.innerHTML=`<img class="nav-icon" src="/static/assets/game/terra/ui/navigation/${icon}.svg" alt="" aria-hidden="true"> <span data-i18n="nav.${key}">${label}</span>`;if(key==='admin')button.hidden=true;nav.insertBefore(button,before);
  }
  document.getElementById('password').parentElement.insertAdjacentHTML('afterend','<label id="auth-email-label" hidden><span data-i18n="auth.email">E-Mail für Wiederherstellung</span><input id="auth-email" type="email" autocomplete="email"></label><label id="auth-totp-label"><span data-i18n="auth.totp">Authenticator-Code (falls aktiviert)</span><input id="auth-code" inputmode="numeric" autocomplete="one-time-code" maxlength="6"></label><label id="auth-recovery-label" hidden><span data-i18n="auth.recovery">Einmaliger Recovery-Code</span><input id="auth-recovery-code" autocomplete="one-time-code" maxlength="20" spellcheck="false"></label><button type="button" id="toggle-recovery-login" data-i18n="auth.use_recovery" class="text-button">Stattdessen Recovery-Code verwenden</button>');
  document.getElementById('toggle-recovery-login').onclick=()=>{const recovery=document.getElementById('auth-recovery-label');const active=recovery.hidden;recovery.hidden=!active;document.getElementById('auth-totp-label').hidden=active;const button=document.getElementById('toggle-recovery-login');button.dataset.i18n=active?'auth.use_totp':'auth.use_recovery';window.FURI18n.apply();};
  document.getElementById('ban-appeal-submit').onclick=async()=>{const button=document.getElementById('ban-appeal-submit'),result=document.getElementById('ban-appeal-result'),recovery=!document.getElementById('auth-recovery-label').hidden;button.disabled=true;result.textContent='';try{const receipt=await api('auth/ban-appeal',{name:document.getElementById('name').value,password:document.getElementById('password').value,reason:document.getElementById('ban-appeal-reason').value,code:recovery?'':document.getElementById('auth-code').value,recovery_code:recovery?document.getElementById('auth-recovery-code').value:''});result.textContent=receipt.message;}catch(error){result.textContent=error.message;}finally{button.disabled=false;}};
  document.getElementById('toggle-auth').insertAdjacentHTML('afterend','<button type="button" id="recover-account" data-i18n="auth.recover" class="text-button">Passwort vergessen / E-Mail bestätigen</button><p><a class="legal-link" data-i18n="legal.link" href="/legal" target="_blank" rel="noopener">Betreiber & Datenschutz</a></p>');
  document.getElementById('recover-account').onclick=()=>document.getElementById('account-dialog').showModal();
  document.getElementById('close-account').onclick=()=>document.getElementById('account-dialog').close();
  document.getElementById('public-account-form').onsubmit=async e=>{e.preventDefault();try {const result=await api('account/public',Object.fromEntries(new FormData(e.currentTarget)));document.getElementById('account-result').textContent=result.message||window.FURI18n.t('auth.action_completed');}catch(error){document.getElementById('account-result').textContent=error.message;}};
  document.getElementById('target-info').insertAdjacentHTML('afterend','<label id="mission-mode-label" hidden>Mission<select id="mission-mode"><option value="attack">Angriff</option><option value="transport">Rohstofftransport</option></select></label><div id="cargo-fields" hidden>'+['Holz','Stein','Erz'].map((n,i)=>`<label>${n}<input id="cargo-${i}" type="number" min="0" value="0"></label>`).join('')+'</div>');
}
function input(name, label, type='text', value='', extra='') {
  return `<label>${escapeHtml(label)}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${extra}></label>`;
}
function select(name,label,options) {
  return `<label>${escapeHtml(label)}<select name="${name}">${options.map(([value,text])=>`<option value="${escapeHtml(value)}">${escapeHtml(text)}</option>`).join('')}</select></label>`;
}
function commandForm(action,body,label='Ausführen',extra='') {
  return `<form class="system-form" data-system="${action}" ${extra}>${body}<button>${label}</button></form>`;
}
function actionButton(action,key,label,fields={}) {
  return `<button class="compact" data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key,...fields}))}">${label}</button>`;
}
function terraAllianceAttackMarkup(attacks,userId) {
  const operations=(attacks||[]).map(attack=>`<article class="quest"><div><b>${escapeHtml(attack.target_name)} · ${attack.target_kind==='player'?'Spielerziel':'Außenposten'}</b><small>${attack.participant_count}/12 Mitglieder · Sammelphase endet ${new Date(attack.join_until*1000).toLocaleTimeString(globalThis.FURI18n?.locale || 'de-DE')} · Einsatzleitung ${escapeHtml(attack.leader_name)}</small></div>${attack.joined?attack.leader_id===userId?actionButton('alliance_attack_cancel',attack.id,'Gesamten Angriff zurückziehen'):actionButton('alliance_attack_withdraw',attack.id,'Aussteigen'):`<button type="button" data-alliance-attack-target="${escapeHtml(attack.target_kind==='player'?'player:':'')}${escapeHtml(attack.target_id)}">Truppen beitreten</button>`}</article>`).join('');
  return `<article class="panel queue-panel" aria-labelledby="terra-alliance-attacks-title"><h3 id="terra-alliance-attacks-title">Gemeinsame Terra-Angriffe</h3><p>Eröffne einen Verband über die Weltkarte. Die Sammelphase dauert fünf Minuten; vor ihrer Frist kann die Einsatzleitung den Angriff zurückziehen und können Teilnehmer aussteigen.</p>${operations||'<p class="empty">Keine offenen Allianzangriffe.</p>'}</article>`;
}
function alliedGarrisonMarkup() {
  if (!state.membership) return '';
  const homePolicy = state.alliance_garrison_policy || {enabled:false,capacity:300};
  const isHome = state.alliance_garrison_home_colony_id === state.colony_id;
  const targets = state.alliance_garrison_targets || [];
  const policy = isHome ? `<article class="panel queue-panel"><h3>Verteidigung deiner Heimat teilen</h3>
    <p>Du entscheidest je Heimatkolonie und Allianz, ob Mitglieder Truppen stationieren dürfen. Die Kapazität gilt für anreisende und stationierte Einheiten; Deaktivieren ruft eingetroffene Garnisonen zurück.</p>
    <form class="system-form" data-system="alliance_garrison_policy"><label><input name="enabled" type="checkbox" ${homePolicy.enabled?'checked':''}> Alliierte Garnisonen erlauben</label>
      ${input('capacity','Gesamtkapazität','number',homePolicy.capacity||300,'min="1" max="300" required')}<button>Freigabe speichern</button></form></article>` : '';
  const units = Object.keys(state.units || {}).map(unit => input(`garrison_${unit}`,state.catalog?.units?.[unit]?.name||unit,'number',0,`min="0" max="${number(state.units[unit])}"`)).join('');
  const deployment = targets.length ? `<form id="alliance-garrison-form" class="system-form">
    ${select('key','Ziel-Heimatkolonie',targets.map(target=>[target.colony_id,`${target.host_name} · ${target.name} · Kapazität ${number(target.capacity)}`]))}
    ${units}<button>Garnison entsenden</button></form>` : '<p>Kein Allianzmitglied hat eine Heimatkolonie für Garnisonen freigegeben.</p>';
  const groups = (state.alliance_garrisons||[]).map(g=>`<li>${escapeHtml(g.contributor_name)} → ${escapeHtml(g.host_name)} · ${g.status==='active'?'stationiert':'anreisend'} · ${Object.entries(g.army).map(([unit,count])=>`${number(count)} ${escapeHtml(state.catalog?.units?.[unit]?.name||unit)}`).join(', ')} ${g.can_recall?actionButton('alliance_garrison_recall',g.id,'Zurückrufen'):''}</li>`).join('');
  return `<article class="panel queue-panel"><h3>Alliierte Garnisonen</h3><p>Truppen sind bis zur Ankunft gebunden. Zustimmung, Allianz und Kapazität werden bei Ankunft erneut geprüft. Kampfverluste bleiben dem beitragenden Konto zugeordnet.</p>${policy}${deployment}${groups?`<h4>Stationierte und anreisende Einheiten</h4><ul>${groups}</ul>`:''}</article>`;
}
function syndicateConvoyMarkup(offers) {
  const pending = (state.syndicate_convoys || []).map(convoy => `<li>${number(convoy.amount)} ${names[convoy.resource]} · Ankunft ${new Date(convoy.due*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</li>`).join('');
  const targets = (state.colonies || []).filter(colony => !colony.selected);
  const available = offers.filter(offer => offer.owner !== state.id);
  const ready = state.faction_research?.includes('smuggler_navigation')
    && (state.syndicate_convoy_ready_at || 0) <= state.server_time && targets.length && available.length;
  if (!ready && !pending) return '';
  return `<article class="panel queue-panel"><h3>Geschützter Syndikatkonvoi</h3>
    <p>Bezahle vom aktiven Depot. Die gekaufte Ware erreicht eine andere eigene Kolonie ohne eigene Träger. Ein Konvoi je 24 Stunden.</p>
    ${pending ? `<ul>${pending}</ul>` : ''}
    ${ready ? commandForm('market_protected_convoy',
      select('key','Angebot',available.map(offer => [offer.id,`${offer.name} · ${number(offer.give_amount)} ${names[offer.give_resource]} gegen ${number(offer.want_amount)} ${names[offer.want_resource]}`]))
      + select('colony_id','Zielkolonie',targets.map(target => [target.colony_id,target.name])),
      'Kaufen und geschützt liefern') : ''}
  </article>`;
}
function intro(eyebrow,title,description='') {
  return `<div class="section-intro"><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${description}</p></div>`;
}
function diplomacyChronicleMarkup() {
  const events=state.diplomacy_events||[];
  const labels={nap_proposed:'Nichtangriffspakt angeboten',nap_accepted:'Nichtangriffspakt angenommen',war_declared:'Krieg erklärt',neutralized:'Diplomatiestatus auf neutral gesetzt'};
  const rows=events.length?`<ol role="list">${events.map(event=>`<li role="listitem"><time datetime="${new Date(Number(event.created)*1000).toISOString()}">${new Date(Number(event.created)*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</time><b>${escapeHtml(event.actor_alliance_tag)}: ${escapeHtml(labels[event.event_type]||'Diplomatieänderung')}</b><span>[${escapeHtml(event.alliance_a_tag)}] ↔ [${escapeHtml(event.alliance_b_tag)}]</span></li>`).join('')}</ol>`:'<p>Noch keine öffentlichen Diplomatieereignisse.</p>';
  const more=state.diplomacy_events_has_more&&events.length?'<button type="button" class="secondary" data-diplomacy-events-more aria-controls="diplomacy-event-list">Ältere Diplomatieereignisse laden</button><p role="status" data-diplomacy-events-status aria-live="polite"></p>':'';
  return `<article class="panel queue-panel" aria-labelledby="diplomacy-chronicle-title"><h3 id="diplomacy-chronicle-title">Öffentliches Diplomatieprotokoll</h3><p>Neueste NAP-, Kriegs- und Neutralitätsänderungen.</p><div id="diplomacy-event-list">${rows}</div>${more}</article>`;
}
function allianceWarsMarkup(own,canDiplomacy) {
  const wars=state.alliance_wars||[];
  const rules=state.alliance_war_rules||{};
  const labels={active:'Aktiv',peace_offered:'Friedensvorschlag offen',ended:'Beendet'};
  const reasons={peace:'Frieden angenommen',objective:'Kriegsziel erreicht',objective_draw:'Kriegsziel gleichzeitig erreicht'};
  const rows=wars.map(war=>{
    const isA=own?.id===war.alliance_a, isB=own?.id===war.alliance_b;
    const controls=canDiplomacy&&(isA||isB)&&war.status!=='ended'
      ? war.status==='active'
        ? actionButton('alliance_peace_offer',war.id,'Frieden anbieten')
        : war.peace_offered_by===own.id
          ? actionButton('alliance_peace_cancel',war.id,'Angebot zurücknehmen')
          : actionButton('alliance_peace_accept',war.id,'Frieden annehmen')+actionButton('alliance_peace_decline',war.id,'Ablehnen')
      : '';
    const winner=war.winner_name?` · Sieger: ${escapeHtml(war.winner_name)}`:'';
    return `<li role="listitem"><div><b>[${escapeHtml(war.alliance_a_tag)}] ${escapeHtml(war.alliance_a_name)} ↔ [${escapeHtml(war.alliance_b_tag)}] ${escapeHtml(war.alliance_b_name)}</b><small>${escapeHtml(labels[war.status]||war.status)} · ${number(war.score_a)} : ${number(war.score_b)} / ${number(war.target_points)} · ${escapeHtml(war.rules_version)}${war.end_reason?` · ${escapeHtml(reasons[war.end_reason]||war.end_reason)}${winner}`:''}</small><small>Start ${new Date(Number(war.started)*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small></div>${controls}</li>`;
  }).join('');
  const events=state.alliance_war_events||[];
  const eventLabels={declared:'Krieg erklärt',battle_score:'Gefechtswertung aktualisiert',peace_offered:'Frieden angeboten',peace_declined:'Friedensangebot abgelehnt',peace_cancelled:'Friedensangebot zurückgenommen',ended_peace:'Frieden geschlossen',ended_objective:'Kriegsziel erreicht'};
  const feed=events.map(event=>`<li role="listitem"><time datetime="${new Date(Number(event.created)*1000).toISOString()}">${new Date(Number(event.created)*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</time><b>${escapeHtml(event.actor_tag||'Welt')} · ${escapeHtml(eventLabels[event.event_type]||'Kriegsereignis')}</b><span>[${escapeHtml(event.alliance_a_tag)}] ↔ [${escapeHtml(event.alliance_b_tag)}]</span>${event.event_type==='battle_score'?`<small>Verluste Angreifer/Verteidiger: ${number(event.details.attacker_losses)} / ${number(event.details.defender_losses)} · Wertung ${number(event.details.score_a)} : ${number(event.details.score_b)}</small>`:''}</li>`).join('');
  return `<article class="panel queue-panel" aria-labelledby="alliance-wars-title"><h3 id="alliance-wars-title">Formelle Allianzkriege</h3><p>${escapeHtml(rules.version||'FUR-3')}-Entwurfswertung: eine Wertung je verlorener gegnerischer Einheit; Ziel ${number(rules.target_points||1000)} Punkte. Der Regelstand wird je Krieg festgehalten und bleibt bis zur Balancefreigabe vorläufig.</p>${rows?`<ul role="list">${rows}</ul>`:'<p>In dieser Welt wurde noch kein formeller FUR-3-Allianzkrieg begonnen.</p>'}${feed?`<h4>Öffentliches Kriegsprotokoll</h4><ol role="list">${feed}</ol>`:''}</article>`;
}
function adminLiveEventFormMarkup() {
  return `<article class="panel"><h3>Produktionsereignis</h3><p>Versionierter FUR-2-Regelsatz. Das Ziel ist der höchste Spielerwert der FUR-2-Weltrangliste dieser Welt. Die Warnzeit plant den Start; in der Endphase gilt der Endbonus. Gleichzeitig aktive Ereignisse addieren sich bis höchstens 100 Prozentpunkte.</p>${commandForm('admin_event',input('name','Ereignisname','text','','required minlength="3" maxlength="60"')+input('hours','Aktive Dauer in Stunden','number',24,'required min="1" max="168"')+input('warning_hours','Vorwarnung bis zum Start in Stunden','number',1,'required min="0" max="168"')+input('bonus','Produktionsbonus in Prozentpunkten','number',25,'required min="0" max="100"')+input('goal_score','Zielwert der FUR-2-Weltrangliste','number',10000,'required min="1" max="1000000000"')+input('end_hours','Dauer der Endphase in Stunden','number',1,'required min="0" max="168"')+input('end_bonus','Produktionsbonus der Endphase','number',50,'required min="0" max="100"'),'Ereignis planen')}</article>`;
}
function liveEventsMarkup() {
  const events=state.events||[];
  const activeTotal=Number(events[0]?.world_active_bonus||0);
  const phases={warning:'Ankündigung',active:'Aktiv',end:'Endphase'};
  const rows=events.length?events.map(event=>`<article class="quest"><div><b>${escapeHtml(event.name)}</b><small>${escapeHtml(phases[event.phase]||'Live-Ereignis')} · ${event.active_bonus}% Produktionsbonus · endet ${new Date(event.ends*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small>${event.goal_score?`<small>FUR-2-Ziel: bester Weltwert ${number(event.goal_progress)} / ${number(event.goal_score)} Punkte · ${event.goal_reached?'Ziel erreicht':'Ziel offen'}</small>`:'<small>Altbestand ohne konfiguriertes Ranglistenziel</small>'}<small>Regelstand ${escapeHtml(event.rules_version||'legacy')} · SHA-256 ${escapeHtml((event.rules_digest||'').slice(0,12)||'unbekannt')}</small></div></article>`).join(''):'<p>Aktuell keine Live-Ereignisse.</p>';
  const more=state.events_has_more&&events.length?'<button type="button" class="secondary" data-live-events-more aria-controls="live-events-list">Ältere Ereignisse laden</button><p role="status" data-live-events-status aria-live="polite"></p>':'';
  return `<div id="live-events-list" aria-label="Live-Ereignisse">${activeTotal?`<p>Aktuell angewendeter Gesamtbonus: ${activeTotal}% (Obergrenze 100%).</p>`:''}${rows}</div>${more}`;
}
function playerProfileSettingsMarkup() {
  const profile=state.profile||{};
  const rules=state.profile_rules||{titles:{none:'Kein Titel'},badges:{},max_badges:3};
  const selected=new Set(profile.public_profile_badges||[]);
  const titles=Object.entries(rules.titles||{}).map(([id,label])=>`<option value="${escapeHtml(id)}" ${profile.public_profile_title===id?'selected':''}>${escapeHtml(label)}</option>`).join('');
  const rewardTitles=Object.entries(rules.reward_titles||{}).map(([id,label])=>`<option value="${escapeHtml(id)}" ${profile.public_profile_reward_title===id?'selected':''}>${escapeHtml(label)}</option>`).join('');
  const skins=Object.entries(rules.skins||{}).map(([id,label])=>`<option value="${escapeHtml(id)}" ${profile.public_profile_skin===id?'selected':''}>${escapeHtml(label)}</option>`).join('');
  const banners=Object.entries(rules.banners||{}).map(([id,label])=>`<option value="${escapeHtml(id)}" ${profile.public_profile_banner===id?'selected':''}>${escapeHtml(label)}</option>`).join('');
  const badges=Object.entries(rules.badges||{}).map(([id,label])=>`<label><input type="checkbox" name="profile_badge" value="${escapeHtml(id)}" ${selected.has(id)?'checked':''}>${escapeHtml(label)}</label>`).join('');
  return `<section class="player-profile-settings" aria-labelledby="player-profile-settings-title"><h3 id="player-profile-settings-title">Öffentliches Kommandantenprofil</h3><p>Standardmäßig privat. Bei Freigabe erscheinen Titel, freigeschaltete Skins und Banner sowie frei gewählte, rein kosmetische Abzeichen in deiner Profilkarte. Rangliste und Punktzahl deiner aktiven Welt sind bereits unabhängig davon öffentlich. Im Profil werden E-Mail, Kontosicherheitsdaten, Koordinaten, Kolonien, Ressourcen, Truppen, Allianz, Kontakte und Nachrichten nicht angezeigt.</p><form id="player-profile-settings-form"><label>Sichtbarkeit<select name="profile_visibility"><option value="private" ${profile.public_profile_visibility!=='public'?'selected':''}>Privat</option><option value="public" ${profile.public_profile_visibility==='public'?'selected':''}>Öffentlich</option></select></label><label>Profil-Titel<select name="profile_title">${titles}</select></label><label>Erspielter Titel<select name="profile_reward_title"><option value="none" ${profile.public_profile_reward_title==='none'?'selected':''}>Keiner</option>${rewardTitles}</select></label><label>Kommandanten-Skin<select name="profile_skin"><option value="none" ${profile.public_profile_skin==='none'?'selected':''}>Standard</option>${skins}</select></label><label>Profilbanner<select name="profile_banner"><option value="none" ${profile.public_profile_banner==='none'?'selected':''}>Keines</option>${banners}</select></label><fieldset><legend>Profilabzeichen · höchstens ${number(rules.max_badges||3)}</legend>${badges}</fieldset><small>Abzeichen sind frei gewählte Kosmetik und keine erspielten Auszeichnungen. Alle Kampagnenbelohnungen sind rein kosmetisch.</small><button>Profil speichern</button><p role="status" aria-live="polite" data-profile-settings-status></p></form></section>`;
}
function socialMarkup() {
  const social=state.social||{friends:[],incoming_requests:[],outgoing_requests:[],blocked:[]};
  const friends=new Set(social.friends.map(person=>person.id));
  const incoming=new Set(social.incoming_requests.map(person=>person.id));
  const outgoing=new Set(social.outgoing_requests.map(person=>person.id));
  const blocked=new Set(social.blocked.map(person=>person.id));
  const candidates=(state.players||[]).filter(player=>player.id!==state.id&&!friends.has(player.id)&&!incoming.has(player.id)&&!outgoing.has(player.id)&&!blocked.has(player.id));
  const rows=(items,render,empty)=>items.length?`<ul role="list">${items.map(render).join('')}</ul>`:`<p>${empty}</p>`;
  return `<article class="panel queue-panel social-panel" aria-labelledby="social-contacts-title"><h2 id="social-contacts-title">Freunde & Blockliste</h2><p>Kontaktlisten sind nur für dich sichtbar. Anfragen brauchen Zustimmung. Blockierte Konten können dir keine privaten Nachrichten senden; beim Blockieren wird ein bestehender Kontakt entfernt.</p>${playerProfileSettingsMarkup()}${sharedReportsMarkup()}<div class="columns"><section><h3>Kontakte</h3>${rows(social.friends,person=>`<li role="listitem"><b>${escapeHtml(person.name)}</b>${actionButton('friend_remove',person.id,'Kontakt entfernen')}${actionButton('player_block',person.id,'Blockieren')}</li>`,'Noch keine bestätigten Kontakte.')}${socialMoreMarkup('friends')}</section><section><h3>Eingehende Anfragen</h3>${rows(social.incoming_requests,person=>`<li role="listitem"><b>${escapeHtml(person.name)}</b>${actionButton('friend_accept',person.id,'Annehmen')}${actionButton('friend_decline',person.id,'Ablehnen')}</li>`,'Keine offenen Anfragen.')}${socialMoreMarkup('incoming_requests')}</section><section><h3>Ausgehende Anfragen</h3>${rows(social.outgoing_requests,person=>`<li role="listitem"><b>${escapeHtml(person.name)}</b>${actionButton('friend_cancel',person.id,'Zurücknehmen')}</li>`,'Keine offenen Anfragen.')}${socialMoreMarkup('outgoing_requests')}</section><section><h3>Spieler dieser Welt</h3>${rows(candidates,person=>`<li role="listitem"><b>${escapeHtml(person.name)}</b><small>${person.x}:${person.y}</small>${actionButton('friend_request',person.id,'Kontakt anfragen')}${actionButton('player_block',person.id,'Blockieren')}</li>`,'Keine weiteren Spieler in dieser Welt.')}${playerDirectoryMoreMarkup()}</section><section><h3>Blockliste</h3>${rows(social.blocked,person=>`<li role="listitem"><b>${escapeHtml(person.name)}</b>${actionButton('player_unblock',person.id,'Entsperren')}</li>`,'Keine blockierten Spieler.')}${socialMoreMarkup('blocked')}</section></div></article>`;
}
function sharedReportsMarkup() {
  if(!state.membership) return '';
  const shared=state.shared_combat_report_keys||{};
  const ownReports=(state.reports||[]).filter(report=>report?.combat&&typeof report.id==='string'&&(shared[report.id]||report.share_owner?.allowed===true));
  const reportControls=ownReports.length?`<ul role="list">${ownReports.map(report=>{
    const shareId=shared[report.id];
    return `<li role="listitem"><b>${escapeHtml(report.title||'Gefechtsbericht')}</b>${actionButton(shareId?'report_unshare':'report_share',shareId||report.id,shareId?'Freigabe widerrufen':'In Allianz teilen')}</li>`;
  }).join('')}</ul>`:'<p>In dieser Kolonie gibt es noch keine Gefechtsberichte.</p>';
  const entries=state.alliance_shared_reports||[];
  const rows=entries.length?`<ul role="list">${entries.map(entry=>{
    const summary=entry.summary||{}, rounds=Array.isArray(summary.rounds)?summary.rounds:[];
    const outcome=summary.outcome==='victory'?'Sieg':'Niederlage';
    const roundRows=rounds.map(round=>`<li>Runde ${number(round.number)} · ${round.outcome==='victory'?'Sieg':'Niederlage'} · eigene Verluste ${number(round.own_losses)} · eigene Überlebende ${number(round.own_survivors)}</li>`).join('');
    return `<li role="listitem"><b>Geteilter Kampfbericht · ${escapeHtml(entry.owner_name)}</b><p>Endergebnis: ${outcome}</p><ul>${roundRows}</ul>${entry.can_revoke?actionButton('report_unshare',entry.id,'Freigabe widerrufen'):''}</li>`;
  }).join('')}</ul>`:'<p>In dieser Allianz wurden noch keine Kampfberichte geteilt.</p>';
  const more=state.alliance_shared_reports_has_more&&entries.length?'<button type="button" class="secondary" data-shared-reports-more>Weitere geteilte Berichte laden</button><p role="status" data-shared-reports-status aria-live="polite"></p>':'';
  return `<section class="panel queue-panel shared-reports" aria-labelledby="shared-reports-title"><h3 id="shared-reports-title">Geteilte Kampfberichte</h3><p>Du entscheidest pro Bericht. Allianzmitglieder derselben Welt sehen nur Rundenresultat sowie die Summen deiner eigenen Verluste und Überlebenden. Namen, Koordinaten, Gegnertruppen, Beute, genauer Zeitpunkt und Rohbericht bleiben verborgen. Beim Verlassen oder Entfernen des Berichteigentümers werden dessen Freigaben widerrufen; austretende Empfänger verlieren den Zugriff sofort.</p><h4>Eigene Gefechtsberichte</h4>${reportControls}<h4>Mit der Allianz geteilt</h4>${rows}${more}</section>`;
}
function socialMoreMarkup(listName) {
  const entries=state.social?.[listName]||[];
  return state.social?.[`${listName}_has_more`]&&entries.length
    ? `<button type="button" class="secondary" data-social-more="${listName}">Weitere Einträge laden</button><p role="status" data-social-status="${listName}" aria-live="polite"></p>`
    : '';
}
function playerDirectoryMoreMarkup() {
  return state.players_has_more&&state.players?.length
    ? '<button type="button" class="secondary" data-player-directory-more>Weitere Kommandanten laden</button><p role="status" data-player-directory-status aria-live="polite"></p>'
    : '';
}
function notesMarkup() {
  const notes=state.notes||[], reports=state.reports||[];
  const reportOptions=reports.map(report=>[report.id,report.title]);
  const noteRows=notes.length?`<ul role="list">${notes.map(note=>{
    const target=note.target_kind==='sector'?`Sektor ${note.x}:${note.y}`:`Bericht: ${note.report_title||'nicht mehr im aktuellen Verlauf'}`;
    const targetFields=note.target_kind==='sector'?`<input name="target_kind" type="hidden" value="sector"><input name="x" type="hidden" value="${note.x}"><input name="y" type="hidden" value="${note.y}">`:`<input name="target_kind" type="hidden" value="report"><input name="key" type="hidden" value="${escapeHtml(note.report_id)}">`;
    return `<li role="listitem"><b>${escapeHtml(target)}</b>${commandForm('note_save',targetFields+`<label>Private Notiz<textarea name="body" maxlength="500" rows="3" required>${escapeHtml(note.body)}</textarea></label>`,'Speichern',`data-form-key="note-${escapeHtml(note.id)}"`)}${actionButton('note_delete',note.id,'Notiz löschen')}</li>`;
  }).join('')}</ul>`:'<p>Noch keine Notizen in dieser Welt.</p>';
  const reportCreate=reportOptions.length?`<section><h3>Berichtsnotiz hinzufügen</h3>${commandForm('note_save',`<input name="target_kind" type="hidden" value="report">${select('key','Eigener Bericht',reportOptions)}<label>Private Notiz<textarea name="body" maxlength="500" rows="3" required></textarea></label>`,'Notiz speichern','data-form-key="note-new-report"')}</section>`:'<section><h3>Berichtsnotiz hinzufügen</h3><p>In dieser Kolonie gibt es noch keine Berichte.</p></section>';
  const more=state.notes_has_more&&notes.length?'<button type="button" class="secondary" data-notes-more>Weitere Notizen laden</button><p role="status" data-notes-status aria-live="polite"></p>':'';
  return `<article class="panel queue-panel notes-panel" aria-labelledby="private-notes-title"><h2 id="private-notes-title">Private Notizen · ${escapeHtml(state.active_world?.name||'Welt')}</h2><p>Nur für dich sichtbar und an diese Welt gebunden. Notizen sind auf 500 Zeichen begrenzt.</p>${noteRows}${more}<div class="columns"><section><h3>Koordinatennotiz hinzufügen</h3>${commandForm('note_save',`<input name="target_kind" type="hidden" value="sector">${input('x','X-Koordinate','number','','min="0" max="63" required')}${input('y','Y-Koordinate','number','','min="0" max="63" required')}<label>Private Notiz<textarea name="body" maxlength="500" rows="3" required></textarea></label>`,'Notiz speichern','data-form-key="note-new-sector"')}</section>${reportCreate}</div></article>`;
}
function allianceBulletinMarkup() {
  if(!state.membership) return '';
  const canModerate=(state.alliance_permissions||[]).includes('bulletin');
  const entries=state.alliance_bulletins||[];
  const rows=entries.length?`<ul id="alliance-bulletin-list" role="list">${entries.map(entry=>{
    const updated=entry.updated!==entry.created?` · bearbeitet ${new Date(entry.updated*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}`:'';
    const editor=canModerate&&!entry.archived?commandForm('alliance_bulletin_update',`<input name="key" type="hidden" value="${escapeHtml(entry.id)}">${input('name','Titel','text',entry.title,'required minlength="1" maxlength="80"')}<label>Text<textarea name="body" maxlength="2000" rows="4" required>${escapeHtml(entry.body)}</textarea></label>`,'Änderungen speichern',`data-form-key="bulletin-${escapeHtml(entry.id)}"`)+actionButton('alliance_bulletin_archive',entry.id,'Archivieren'):'';
    return `<li role="listitem" class="bulletin-entry"><div class="bulletin-heading"><h4>${escapeHtml(entry.title)}</h4>${entry.archived?'<span class="eyebrow">Archiviert</span>':''}</div><p>${escapeHtml(entry.body)}</p><small>Von ${escapeHtml(entry.author_name)} · ${new Date(entry.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}${updated}</small>${editor}</li>`;
  }).join('')}</ul>`:'<p>Die Pinnwand ist noch leer.</p>';
  const compose=canModerate?`<details class="bulletin-compose"><summary>Ankündigung verfassen</summary>${commandForm('alliance_bulletin_create',input('name','Titel','text','','required minlength="1" maxlength="80"')+'<label>Text<textarea name="body" maxlength="2000" rows="4" required></textarea></label>','Veröffentlichen','data-form-key="bulletin-new"')}</details>`:'';
  const older=state.alliance_bulletins_has_more&&entries.length?`<button type="button" class="secondary" data-bulletin-more="${escapeHtml(entries[entries.length-1].id)}" aria-controls="alliance-bulletin-list">Ältere Beiträge laden</button><p data-bulletin-more-status role="status" aria-live="polite"></p>`:'';
  return `<section class="alliance-bulletin" aria-labelledby="alliance-bulletin-title"><h3 id="alliance-bulletin-title">Allianz-Pinnwand</h3><p>Nur aktuelle Mitglieder sehen die Pinnwand. Die Berechtigung dafür wird von der Allianzleitung vergeben.</p>${compose}${rows}${older}</section>`;
}
function allianceForumMarkup() {
  if(!state.membership) return '';
  const canModerate=(state.alliance_permissions||[]).includes('forum_moderation');
  const threads=state.alliance_forum||[], reports=state.alliance_forum_reports||[];
  const myPendingPosts=new Set(reports.filter(report=>report.reporter_id===state.id&&report.status==='pending').map(report=>report.post_id));
  const threadRows=threads.length?`<ul id="alliance-forum-list" role="list">${threads.map(thread=>{
    const posts=(thread.posts||[]).map(post=>{
      const canEdit=post.author_id===state.id||canModerate;
      const edit=canEdit&&!thread.archived?commandForm('alliance_forum_post_edit',`<input name="key" type="hidden" value="${escapeHtml(post.id)}"><label>Beitrag bearbeiten<textarea name="body" maxlength="4000" rows="4" required>${escapeHtml(post.body)}</textarea></label>`,'Änderungen speichern',`data-form-key="forum-post-${escapeHtml(post.id)}"`):'';
      const report=post.author_id!==state.id&&!myPendingPosts.has(post.id)?commandForm('alliance_forum_report',`<input name="key" type="hidden" value="${escapeHtml(post.id)}"><label>Begründung der Meldung<textarea name="body" maxlength="500" rows="2" required></textarea></label>`,'Beitrag melden',`data-form-key="forum-report-${escapeHtml(post.id)}"`):myPendingPosts.has(post.id)?'<small>Meldung zur Prüfung eingereicht</small>':'';
      return `<li role="listitem" class="forum-post"><div class="forum-post-heading"><b>${escapeHtml(post.author_name)}</b><small>${new Date(post.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}${post.updated!==post.created?' · bearbeitet':''}</small></div><p>${escapeHtml(post.body)}</p>${edit}${report}</li>`;
    }).join('');
    const threadEdit=thread.author_id===state.id||canModerate?commandForm('alliance_forum_thread_edit',`<input name="key" type="hidden" value="${escapeHtml(thread.id)}">${input('name','Thema bearbeiten','text',thread.title,'required minlength="1" maxlength="100"')}`,'Titel speichern',`data-form-key="forum-thread-${escapeHtml(thread.id)}"`):'';
    const reply=thread.archived?'':commandForm('alliance_forum_reply',`<input name="key" type="hidden" value="${escapeHtml(thread.id)}"><label>Antwort<textarea name="body" maxlength="4000" rows="3" required></textarea></label>`,'Antwort senden',`data-form-key="forum-reply-${escapeHtml(thread.id)}"`);
    return `<li role="listitem" class="forum-thread"><article><div class="forum-thread-heading"><h4>${escapeHtml(thread.title)}</h4>${thread.archived?'<span class="eyebrow">Archiviert</span>':''}</div><small>Gestartet von ${escapeHtml(thread.author_name)} · ${new Date(thread.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small><ul class="forum-post-list" role="list">${posts}</ul>${threadEdit}${canModerate&&!thread.archived?actionButton('alliance_forum_archive',thread.id,'Thema archivieren'):''}${reply}</article></li>`;
  }).join('')}</ul>`:'<p>Noch keine Themen. Eröffne die erste Allianzbesprechung.</p>';
  const compose=commandForm('alliance_forum_thread_create',input('name','Thema','text','','required minlength="1" maxlength="100"')+'<label>Erster Beitrag<textarea name="body" maxlength="4000" rows="5" required></textarea></label>','Thema eröffnen','data-form-key="forum-thread-new"');
  const older=state.alliance_forum_has_more&&threads.length?`<button type="button" class="secondary" data-forum-more="${escapeHtml(threads[threads.length-1].id)}" aria-controls="alliance-forum-list">Ältere Themen laden</button><p data-forum-more-status role="status" aria-live="polite"></p>`:'';
  const reportsMore=state.alliance_forum_reports_has_more&&reports.length?`<button type="button" class="secondary" data-forum-reports-more="${escapeHtml(reports[reports.length-1].id)}" aria-controls="alliance-forum-reports-list">Weitere Meldungen laden</button><p data-forum-reports-more-status role="status" aria-live="polite"></p>`:'';
  const reportRows=canModerate&&reports.length?`<section class="forum-reports" aria-labelledby="forum-reports-title"><h4 id="forum-reports-title">Meldungen der Allianz</h4><ul id="alliance-forum-reports-list" role="list">${reports.map(report=>`<li role="listitem" class="forum-report"><b>${escapeHtml(report.thread_title)} · ${escapeHtml(report.post_author_name)}</b><p>${escapeHtml(report.post_body)}</p><p><b>Meldung von ${escapeHtml(report.reporter_name)}:</b> ${escapeHtml(report.reason)}</p><small>${report.status==='pending'?'Offen':'Geprüft'}${report.resolver_name?` · von ${escapeHtml(report.resolver_name)}`:''}</small>${report.status==='pending'?actionButton('alliance_forum_report_resolve',report.id,'Als geprüft markieren'):''}</li>`).join('')}</ul>${reportsMore}</section>`:'';
  return `<section class="alliance-forum" aria-labelledby="alliance-forum-title"><h3 id="alliance-forum-title">Allianzforum</h3><p>Aktuelle Mitglieder können Themen und Antworten verfassen. Du kannst eigene Beiträge bearbeiten; die Berechtigung zur Moderation und Einsicht in Meldungen vergibt die Allianzleitung.</p>${compose}${threadRows}${older}${reportRows}</section>`;
}
function allianceDirectoryMarkup(own,officer) {
  const alliances=state.alliances||[];
  const rows=alliances.map(alliance=>{
    const pact=alliance.diplomacy_status?{status:alliance.diplomacy_status,accepted:alliance.diplomacy_accepted,proposed_by:alliance.diplomacy_proposed_by}:null;
    const applicationAction=!own&&!state.membership?actionButton(alliance.application_id?'alliance_application_withdraw':'alliance_apply',alliance.application_id||alliance.id,alliance.application_id?'Bewerbung zurückziehen':'Bewerben'):'';
    return `<div class="alliance-row"><div><b>[${escapeHtml(alliance.tag)}] ${escapeHtml(alliance.name)}</b><small>${alliance.size} Mitglieder · ${pact?escapeHtml(pact.status)+(pact.accepted?' aktiv':' angeboten'):'Neutral'}</small></div>${applicationAction}${officer&&alliance.id!==own?.id?`${actionButton('diplomacy',alliance.id,'Pakt anbieten',{status:'nap'})}${pact&&!pact.accepted&&pact.proposed_by!==own.id?actionButton('diplomacy',alliance.id,'Pakt annehmen',{status:'accept'}):''}${actionButton('diplomacy',alliance.id,'Krieg',{status:'war'})}${actionButton('diplomacy',alliance.id,'Neutral',{status:'neutral'})}`:''}</div>`;
  }).join('');
  return `<article class="panel queue-panel"><h3>Allianzregister</h3>${rows||'<p>Noch keine Allianzen gegründet.</p>'}${state.alliances_has_more?'<button type="button" class="secondary" data-alliance-directory-more>Weitere Allianzen laden</button><p role="status" data-alliance-directory-status aria-live="polite"></p>':''}</article>`;
}
function allianceApplicationsMarkup(direction) {
  const incoming=direction==='incoming';
  if(incoming&&(!state.membership||!(state.alliance_permissions||[]).includes('applications')))return '';
  if(!incoming&&state.membership)return '';
  const key=incoming?'alliance_incoming_applications':'alliance_applications';
  const entries=state[key]||[];
  const hasMore=Boolean(state[`${key}_has_more`]);
  if(!entries.length&&!hasMore)return '';
  const rows=incoming?entries.map(application=>`<div class="quest"><div><b>${escapeHtml(application.name)}</b><small>Bewerbung eingegangen</small></div>${actionButton('alliance_application_accept',application.id,'Aufnehmen')}${actionButton('alliance_application_reject',application.id,'Ablehnen')}</div>`).join(''):entries.map(application=>`<div class="quest"><div><b>[${escapeHtml(application.tag)}] ${escapeHtml(application.name)}</b><small>Bewerbung offen</small></div>${actionButton('alliance_application_withdraw',application.id,'Zurückziehen')}</div>`).join('');
  return `<article class="panel queue-panel"><h3>${incoming?'Bewerbungen an deine Allianz':'Deine Bewerbungen'}</h3>${rows}${hasMore?`<button type="button" class="secondary" data-alliance-applications-more="${direction}">Weitere Bewerbungen laden</button><p role="status" data-alliance-applications-status="${direction}" aria-live="polite"></p>`:''}</article>`;
}
function allianceInvitationsMarkup(direction) {
  const outgoing=direction==='outgoing';
  if(outgoing&&(!state.membership||!(state.alliance_permissions||[]).includes('invitations')))return '';
  const key=outgoing?'alliance_outgoing_invites':'invites';
  const entries=state[key]||[];
  const hasMore=Boolean(state[`${key}_has_more`]);
  if(!entries.length&&!hasMore)return '';
  const rows=outgoing?entries.map(invite=>`<div class="quest"><div><b>${escapeHtml(invite.name)}</b><small>Einladung noch offen</small></div>${actionButton('alliance_invite_cancel',invite.id,'Einladung zurücknehmen')}</div>`).join(''):entries.map(invite=>`<div class="quest"><div><b>[${escapeHtml(invite.tag)}] ${escapeHtml(invite.name)}</b><small>${state.membership?'Verlasse zuerst deine Allianz, um anzunehmen.':'Einladung zu dieser Allianz.'}</small></div>${state.membership?'':actionButton('alliance_accept',invite.id,'Annehmen')}${actionButton('alliance_invite_decline',invite.id,'Ablehnen')}</div>`).join('');
  return `<article class="panel queue-panel"><h3>${outgoing?'Offene Einladungen deiner Allianz':'Einladungen'}</h3>${rows}${hasMore?`<button type="button" class="secondary" data-alliance-invitations-more="${direction}">Weitere Einladungen laden</button><p role="status" data-alliance-invitations-status="${direction}" aria-live="polite"></p>`:''}</article>`;
}
function allianceMembersMoreMarkup() {
  return state.members_has_more?'<button type="button" class="secondary" data-alliance-members-more>Weitere Mitglieder laden</button><p role="status" data-alliance-members-status aria-live="polite"></p>':'';
}
function allianceCandidatesMoreMarkup() {
  const candidates=state.alliance_candidates||[];
  return state.alliance_candidates_has_more&&candidates.length?`<button type="button" class="secondary" data-alliance-candidates-more aria-controls="alliance-invite-candidate-select">Weitere Kandidaten laden</button><p role="status" data-alliance-candidates-status aria-live="polite"></p>`:'';
}
function allianceRolePermissionsMarkup() {
  if(state.membership?.role!=='leader') return '';
  const catalog=state.alliance_permission_catalog||[], roles=state.alliance_role_permissions||{};
  return `<section class="alliance-role-permissions" aria-labelledby="alliance-permissions-title"><h3 id="alliance-permissions-title">Rollenberechtigungen</h3><p>Nur die Allianzleitung kann diese Rechte ändern. Führungsübertrag und Servermoderation sind hier nicht vergebbar.</p>${['officer','member'].map(role=>{
    const selected=new Set(roles[role]||[]);
    const checks=catalog.map(permission=>`<label><input type="checkbox" name="permission" value="${escapeHtml(permission.id)}" ${selected.has(permission.id)?'checked':''}> ${escapeHtml(permission.label)}</label>`).join('');
    return commandForm('alliance_permissions_update',`<input type="hidden" name="role" value="${role}"><fieldset><legend>${role==='officer'?'Offiziere':'Mitglieder'}</legend>${checks}</fieldset>`,`Rechte für ${role==='officer'?'Offiziere':'Mitglieder'} speichern`);
  }).join('')}</section>`;
}
function allianceTransferMarkup(transfer,userId) {
  if(!transfer) return '';
  const actions=transfer.successor_id===userId
    ? actionButton('alliance_transfer_accept',transfer.id,'Führung annehmen')+actionButton('alliance_transfer_decline',transfer.id,'Ablehnen')
    : actionButton('alliance_transfer_cancel',transfer.id,'Vorschlag zurücknehmen');
  return `<section class="alliance-transfer" aria-labelledby="alliance-transfer-title"><h3 id="alliance-transfer-title">Führungsübergabe ausstehend</h3><p>${escapeHtml(transfer.leader_name)} hat ${escapeHtml(transfer.successor_name)} als neue Allianzleitung vorgeschlagen. Die Führung bleibt bis zur Annahme unverändert.</p><small>Vorgeschlagen am ${new Date(transfer.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small>${actions}</section>`;
}
function allianceTreasuryMarkup() {
  if(!state.membership) return '';
  const balances=state.alliance_treasury_balances||[], requests=state.alliance_treasury_requests||[];
  const resources=['Holz','Stein','Erz'];
  const amountsForm=(label)=>`<fieldset><legend>${label} · gewünschte Auszahlung</legend>${resources.map((name,index)=>`<label>${name}<input name="resource-${index}" type="number" min="0" max="99000" value="0" required></label>`).join('')}<small>Die Allianzkasse trägt zusätzlich 1 % je Ressource als Gebühr; die Gebühr wird je Ressource aufgerundet. Beträge ab 5.000 einschließlich Gebühr benötigen zwei unabhängige Freigaben.</small></fieldset>`;
  const statusNames={pending:'wartet auf Freigabe',paid:'ausgezahlt',declined:'abgelehnt',cancelled:'storniert',expired:'abgelaufen',void_membership:'wegen Mitgliedschaft beendet'};
  const requestMarkup=requests.map(request=>{
    const gross=JSON.parse(request.gross_json), fee=JSON.parse(request.fee_json), net=JSON.parse(request.net_json);
    const pending=request.status==='pending', own=request.requester_id===state.id, manager=Boolean(state.alliance_treasury_can_manage);
    const controls=pending&&own?actionButton('alliance_treasury_cancel',request.id,'Antrag stornieren'):'';
    const approvals=pending&&manager&&!own?actionButton('alliance_treasury_approve',request.id,'Freigeben')+actionButton('alliance_treasury_decline',request.id,'Ablehnen'):'';
    return `<article class="quest"><div><b>${escapeHtml(request.requester_name)} · ${escapeHtml(statusNames[request.status]||request.status)}</b><small>Brutto ${gross.map((amount,index)=>`${number(amount)} ${resources[index]}`).join(' · ')} · Gebühr ${fee.map((amount,index)=>`${number(amount)} ${resources[index]}`).join(' · ')} · Auszahlung ${net.map((amount,index)=>`${number(amount)} ${resources[index]}`).join(' · ')}</small><small>${number(request.approval_count)} / ${number(request.required_approvals)} unabhängige Freigaben · Frist ${new Date(request.expires*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small></div>${controls}${approvals}</article>`;
  }).join('');
  const ledger=(state.alliance_treasury_ledger||[]).map(row=>{
    const details=JSON.parse(row.details||'{}'), amount=details.resources||details.gross||[0,0,0];
    return `<div class="audit-row" role="listitem"><small>${new Date(row.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})} · ${escapeHtml(row.actor_name||'Spielleitung')} · ${escapeHtml(row.event_type)}</small><span>${amount.map((value,index)=>`${number(value)} ${resources[index]}`).join(' · ')}</span></div>`;
  }).join('');
  return `<section class="panel queue-panel alliance-treasury" aria-labelledby="alliance-treasury-title"><h3 id="alliance-treasury-title">Allianzkasse · ${escapeHtml(state.active_world?.name||'aktive Welt')}</h3><p>FUR-3-Regeln freigegeben · weltgebundener Bestand. Spenden sind gebührenfrei. Auszahlungsanträge reservieren den Bruttobetrag bis Freigabe, Storno oder Ablauf nach sieben Tagen. Ab 5.000 Brutto-Ressourcen sind zwei Freigeber erforderlich; Antragsteller können nie selbst freigeben.</p><div class="rank-list">${balances.map((balance,index)=>`<div class="rank"><b>${resources[index]}</b><span>${number(balance.available)} verfügbar · ${number(balance.reserved)} reserviert</span></div>`).join('')}</div><div class="columns"><article class="panel"><h4>Rohstoffe spenden</h4>${commandForm('alliance_treasury_donate',amountsForm('Spende'),'Einzahlen')}</article><article class="panel"><h4>Auszahlung beantragen</h4><p>Der Bruttobetrag wird sofort reserviert. Die Auszahlung geht an deine aktuelle Kolonie dieser Welt.</p>${commandForm('alliance_treasury_request',amountsForm('Antrag'),'Antrag stellen')}</article></div><h4>Auszahlungsanträge</h4>${requestMarkup||'<p>Keine Anträge in dieser Welt.</p>'}<details><summary>Kassenbuch</summary><div class="market-history" role="list" aria-label="Allianz-Kassenbuch">${ledger||'<p>Noch keine Kassenbewegungen.</p>'}</div></details></section>`;
}
function allianceProjectMarkup() {
  if(!state.membership) return '';
  const projects=state.alliance_projects||[], rules=state.alliance_project_rules||{}, resources=['Holz','Stein','Erz'];
  const catalog=rules.projects||[], manager=Boolean(state.alliance_project_can_manage);
  const statusNames={active:'läuft',completed:'abgeschlossen',cancelled:'abgebrochen',expired:'abgelaufen'};
  const cards=projects.map(project=>{
    const target=JSON.parse(project.target_json), contributed=JSON.parse(project.contributed_json), active=project.status==='active';
    const progress=target.map((amount,index)=>`${resources[index]} ${number(contributed[index])} / ${number(amount)}`).join(' · ');
    const contributionForm=active?commandForm('alliance_project_contribute',`<input type="hidden" name="key" value="${escapeHtml(project.id)}"><fieldset><legend>Beitrag aus deiner aktiven Kolonie</legend>${resources.map((name,index)=>`<label>${name}<input name="resource-${index}" type="number" min="0" max="100000" value="0" required></label>`).join('')}</fieldset>`,'Beitrag leisten'):'';
    const cancel=active&&manager?actionButton('alliance_project_cancel',project.id,'Projekt abbrechen und Beiträge erstatten'):'';
    const deadline=active?` · Frist ${new Date(project.deadline*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}`:'';
    const reward=project.status==='completed'?`<small>Allianzrekord: ${escapeHtml(project.record_reward)} · nur ein sichtbarer Eintrag, ohne Wirtschafts- oder Kampfvorteil.</small>`:'';
    return `<article class="quest"><div><b>${escapeHtml(project.title)} · ${escapeHtml(statusNames[project.status]||project.status)}</b><small>${progress}${deadline}</small>${reward}</div>${contributionForm}${cancel}</article>`;
  }).join('');
  const create=manager?`<article class="panel"><h4>Neues Gemeinschaftsziel</h4><p>Je Allianz und Welt kann ein Projekt gleichzeitig laufen. Beiträge oberhalb des Restziels werden abgelehnt.</p>${commandForm('alliance_project_create',`<label>Projektvorlage<select name="key" required>${catalog.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)} · ${item.target.map((amount,index)=>`${number(amount)} ${resources[index]}`).join(' / ')} · ${Math.ceil(item.duration_seconds/86400)} Tage</option>`).join('')}</select></label>`,'Projekt starten')}</article>`:'';
  const ledger=(state.alliance_project_ledger||[]).map(row=>`<div class="audit-row" role="listitem"><small>${new Date(row.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})} · ${escapeHtml(row.actor_name||'Spielleitung')} · ${row.event_type==='refund'?'Rückzahlung':'Beitrag'}</small><span>${number(row.amount)} ${resources[row.resource_index]}</span></div>`).join('');
  return `<section class="panel queue-panel alliance-projects" aria-labelledby="alliance-projects-title"><h3 id="alliance-projects-title">Gemeinschaftsprojekte · ${escapeHtml(state.active_world?.name||'aktive Welt')}</h3><p>Vorläufiger FUR-3-Entwurf. Aktuelle Mitglieder spenden aus ihrer aktiven Kolonie. Überschüsse werden abgewiesen. Unvollständige Beiträge werden beim Abbruch oder nach Fristablauf vollständig an die jeweilige Spenderkolonie zurückgezahlt. Ein Abschluss erzeugt nur einen Allianzrekord und keine Ressourcen-, Produktions-, Kampf- oder Ranglistenboni.</p>${create}<h4>Projektübersicht</h4>${cards||'<p>Für diese Welt gibt es noch kein Allianzprojekt.</p>'}<details><summary>Projektbuch</summary><div class="market-history" role="list" aria-label="Allianzprojektbuch">${ledger||'<p>Noch keine Projektbeiträge.</p>'}</div></details></section>`;
}
function adminUsersMarkup(admin) {
  const rows=(admin.users||[]).map(user=>`<div class="alliance-row"><div><b>${escapeHtml(user.name)}</b><small>${escapeHtml(user.role)} · ${user.banned?'gesperrt':'aktiv'}</small></div>${user.role==='player'?actionButton('admin_ban',user.id,user.banned?'Entsperren':'Sperren',{value:user.banned?0:1})+actionButton('admin_mute',user.id,'1 h stummschalten',{minutes:60})+actionButton('admin_mute',user.id,'Stummschaltung aufheben',{minutes:0}):''}</div>`).join('');
  const more=admin.users_has_more?'<button type="button" class="secondary" data-admin-list-more="users">Weitere Kommandanten laden</button><p role="status" data-admin-list-status="users" aria-live="polite"></p>':'';
  return `<article class="panel queue-panel"><h3>Kommandanten moderieren</h3><div id="admin-users-list">${rows||'<p>Keine Konten vorhanden.</p>'}</div>${more}</article>${adminModerationCasesMarkup(admin)}`;
}
function adminModerationCasesMarkup(admin) {
  const cases=admin.cases||[];
  const rows=cases.map(item=>{
    const appeal=item.case_type==='mute_appeal';
    const banAppeal=item.case_type==='account_ban_appeal';
    const actions=banAppeal
      ?actionButton('admin_case_resolve',item.id,'Einspruch ablehnen',{value:'deny_ban_appeal'})+actionButton('admin_case_resolve',item.id,'Sperre aufheben',{value:'grant_ban_appeal'})
      :appeal
      ?actionButton('admin_case_resolve',item.id,'Einspruch ablehnen',{value:'deny_appeal'})+actionButton('admin_case_resolve',item.id,'Stummschaltung aufheben',{value:'lift_mute'})
      :actionButton('admin_case_resolve',item.id,'Meldung schließen',{value:'dismiss'})+actionButton('admin_case_resolve',item.id,'Nachricht ausblenden',{value:'hide_message'});
    const title=banAppeal?'Einspruch gegen Kontosperrung':appeal?'Einspruch gegen Stummschaltung':'Nachrichtenmeldung';
    return `<article class="quest"><div><b>${title} · ${escapeHtml(item.reporter_name)}</b><small>${appeal||banAppeal?'Betroffenes Konto':'Meldung über'}: ${escapeHtml(item.target_name)} · ${new Date(item.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small>${item.body!==null?`<p>${escapeHtml(item.body)}</p>`:''}<p>${escapeHtml(item.reason)}</p></div><div class="button-row">${actions}</div></article>`;
  }).join('');
  const more=admin.cases_has_more&&cases.length?'<button type="button" class="secondary" data-admin-cases-more>Weitere Moderationsfälle laden</button><p role="status" data-admin-cases-status aria-live="polite"></p>':'';
  return `<article class="panel queue-panel"><h3>Offene Meldungen und Einsprüche</h3><p>Diese Einträge sind nur für Moderation und Administration sichtbar. Entscheidungen werden protokolliert.</p><div id="admin-cases-list">${rows||'<p>Keine offenen Fälle.</p>'}</div>${more}</article>`;
}
function playerModerationCasesMarkup(state) {
  const cases=state.moderation_cases||[];
  const names={message_report:'Nachrichtenmeldung',mute_appeal:'Einspruch gegen Stummschaltung',account_ban_appeal:'Einspruch gegen Kontosperrung'};
  const statuses={open:'Offen',resolved:'Bearbeitet'};
  const outcomes={dismiss:'Ohne Maßnahme geschlossen',hide_message:'Nachricht ausgeblendet',deny_appeal:'Einspruch abgelehnt',lift_mute:'Stummschaltung aufgehoben',deny_ban_appeal:'Einspruch abgelehnt',grant_ban_appeal:'Kontosperrung aufgehoben'};
  const rows=cases.map(item=>`<li><b>${names[item.case_type]||'Moderationsfall'}</b> · ${statuses[item.status]||'Unbekannt'}${item.resolution?` · ${outcomes[item.resolution]||'Entschieden'}`:''} · ${new Date(item.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</li>`).join('');
  const appeal=state.profile?.muted_until>state.server_time&&!cases.some(item=>item.case_type==='mute_appeal'&&item.status==='open')
    ?commandForm('mute_appeal','<label>Begründung für den Einspruch<textarea name="body" minlength="3" maxlength="500" rows="3" required></textarea></label>','Einspruch einreichen')
    :'';
  return `<article class="panel queue-panel"><h3>Deine Moderationsfälle</h3><p>Nur du siehst deine Meldungen und Einsprüche. Für eine aktive Stummschaltung kannst du einen Einspruch einreichen.</p><ul>${rows||'<li>Noch keine Fälle.</li>'}</ul>${appeal}</article>`;
}
function systemCommunicationMarkup(state) {
  const announcements=state.announcements||[];
  const mail=state.system_mail||[];
  const canArchive=item=>state.profile?.role==='admin'||(state.profile?.role==='moderator'&&item.world_id!==null&&Number(item.world_id)===Number(state.active_world?.id||state.world_id));
  const announcementRows=announcements.map(item=>`<article class="message"><div><b>${item.emergency?'🚨 NOTFALL · ':''}${escapeHtml(item.title)}</b><small>${item.world_id===null?'Alle Welten':`Welt ${number(item.world_id)}`} · ${escapeHtml(item.author_name)} · ${item.publish_at>state.server_time?`geplant für ${new Date(item.publish_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}`:new Date(item.publish_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small></div><p>${escapeHtml(item.body)}</p>${canArchive(item)?actionButton('admin_announcement_archive',item.id,item.publish_at>state.server_time?'Planung abbrechen':'Archivieren'):''}</article>`).join('');
  const mailRows=mail.map(item=>`<article class="message"><div><b>${escapeHtml(item.title)}</b><small>${escapeHtml(item.author_name)} · ${new Date(item.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})} · ${item.read_at?'Gelesen':'Ungelesen'}</small></div><p>${escapeHtml(item.body)}</p>${item.read_at?'':actionButton('mail_read',item.id,'Als gelesen markieren')}</article>`).join('');
  const announcementMore=state.announcements_has_more&&announcements.length?'<button type="button" class="secondary" data-announcements-more>Ältere Ankündigungen laden</button><p role="status" data-announcements-status aria-live="polite"></p>':'';
  const mailMore=state.system_mail_has_more&&mail.length?'<button type="button" class="secondary" data-system-mail-more>Ältere Post laden</button><p role="status" data-system-mail-status aria-live="polite"></p>':'';
  const role=state.profile?.role;
  const announcementComposer=state.administration?`<article class="panel"><h3>Ankündigung planen</h3><p>Weltankündigungen sehen Spieler dieser Welt; globale Beiträge sehen alle angemeldeten Spieler. Eine leere Zeit veröffentlicht sofort. Geplante Beiträge lassen sich bis zur Veröffentlichung abbrechen.</p>${commandForm('admin_announcement_create',`<label>Reichweite<select name="target_kind"><option value="world">Aktive Welt</option>${role==='admin'?'<option value="global">Alle Welten</option>':''}</select></label><input type="hidden" name="world_id" value="${number(state.active_world?.id||state.world_id)}">${input('name','Titel','text','','required minlength="1" maxlength="80"')}<label>Text<textarea name="body" maxlength="2000" rows="4" required></textarea></label><label>Veröffentlichung (Europe/Berlin, optional)<input name="publish_at_local" type="datetime-local"></label><label><input name="emergency" type="checkbox"> Notfallankündigung deutlich markieren</label>`,'Planen oder veröffentlichen')}</article>`:'';
  const mailComposer=role==='admin'?`<article class="panel"><h3>Private Systemnachricht senden</h3><p>Nur der ausgewählte Empfänger sieht diese Nachricht in seinem Systempostfach.</p>${commandForm('admin_mail_send',`<label>Empfänger<select name="key" required>${(state.administration.users||[]).map(user=>`<option value="${escapeHtml(user.id)}">${escapeHtml(user.name)}</option>`).join('')}</select></label>${input('name','Titel','text','','required minlength="1" maxlength="80"')}<label>Nachricht<textarea name="body" maxlength="2000" rows="4" required></textarea></label>`,'Privat senden')}${state.administration.users_has_more?'<p>Weitere Empfänger werden über die Kommandantenliste im Verwaltungsbereich geladen.</p>':''}</article>`:'';
  return `<div class="columns queue-panel"><article class="panel"><h3>Weltankündigungen</h3><p>Globale und aktive-Welt-Nachrichten bleiben vom persönlichen Postfach getrennt.</p>${announcementRows||'<p>Keine aktuellen Ankündigungen.</p>'}${announcementMore}</article><article class="panel"><h3>Systempostfach</h3><p>Nur du kannst die an dein Konto gesendeten Systemnachrichten lesen. Sie bleiben erhalten.</p>${mailRows||'<p>Keine Systempost.</p>'}${mailMore}</article></div>${state.administration?`<div class="columns queue-panel">${announcementComposer}${mailComposer}</div>`:''}`;
}
function adminFailuresMarkup(admin) {
  const rows=(admin.failures||[]).map(failure=>`<div class="quest"><div><b>${escapeHtml(failure.error)}</b><small>${failure.attempts} Versuche · Auftrag ${escapeHtml(failure.job_id)}</small></div>${actionButton('admin_retry',failure.id,'Erneut versuchen')}</div>`).join('');
  const more=admin.failures_has_more?'<button type="button" class="secondary" data-admin-list-more="failures">Weitere Auftragsfehler laden</button><p role="status" data-admin-list-status="failures" aria-live="polite"></p>':'';
  return `<article class="panel queue-panel"><h3>Auftragsfehler</h3><div id="admin-failures-list">${rows||'<p>Keine fehlerhaften Aufträge.</p>'}</div>${more}</article>`;
}
function adminAuditMarkup(admin) {
  const entries=admin.audit||[];
  const rows=entries.map(a=>`<div class="audit-row" role="listitem"><small>${new Date(a.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small><b>${escapeHtml(a.action)}</b><code>${escapeHtml(a.target)}</code></div>`).join('');
  const more=admin.audit_has_more&&entries.length?'<button type="button" class="secondary" data-admin-audit-more aria-controls="admin-audit-list">Ältere Audit-Einträge laden</button><p role="status" data-admin-audit-status aria-live="polite"></p>':'';
  return `<article class="panel queue-panel"><h3>Auditprotokoll</h3><div id="admin-audit-list" role="list" aria-label="Auditprotokoll">${rows||'<p>Noch keine Einträge.</p>'}</div>${more}</article>`;
}
function systemsView() {
  if(tab==='alliance') {
    const mine=state.membership, own=state.alliances.find(a=>a.id===mine?.alliance_id), permissions=new Set(state.alliance_permissions||[]), canInvite=permissions.has('invitations'), canEditDescription=permissions.has('description'), canRemove=permissions.has('member_removal'), canDiplomacy=permissions.has('diplomacy'), transfer=state.alliance_transfer_request;
    return intro('GEMEINSAM / DIPLOMATIE','Aus Verbündeten wird Macht.','Einladungen, Rollen und Nichtangriffspakte verbinden deine Allianz mit der Welt.')+
       (own ? `<article class="panel"><span class="eyebrow">[${escapeHtml(own.tag)}] · ${escapeHtml(mine.role)}</span><h2>${escapeHtml(own.name)}</h2><p>${escapeHtml(own.description||'Noch keine Allianzbeschreibung.')}</p>${allianceTreasuryMarkup()}${allianceProjectMarkup()}${terraAllianceAttackMarkup(state.terra_alliance_attacks,state.id)}${alliedGarrisonMarkup()}${allianceBulletinMarkup()}${allianceForumMarkup()}${allianceApplicationsMarkup('incoming')}${allianceInvitationsMarkup('incoming')}${allianceInvitationsMarkup('outgoing')}<div class="member-list">${state.members.map(m=>`<div class="rank"><b>${escapeHtml(m.name)}</b><span>${escapeHtml(m.role)}</span>${mine.role==='leader'&&m.user_id!==state.id ? actionButton('alliance_role',m.user_id,m.role==='officer'?'Mitglied':'Offizier',{role:m.role==='officer'?'member':'officer'})+(!transfer?actionButton('alliance_transfer',m.user_id,'Nachfolger vorschlagen'):'') : ''}${canRemove&&m.user_id!==state.id&&m.role!=='leader'?actionButton('alliance_kick',m.user_id,'Entfernen'):''}</div>`).join('')}</div>${allianceTransferMarkup(transfer,state.id)}${allianceMembersMoreMarkup()}${canInvite ? commandForm('alliance_invite',`<label>Kommandant auswählen<select id="alliance-invite-candidate-select" name="name" required>${state.alliance_candidates.map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)} · ${p.x}:${p.y}</option>`).join('')}</select></label>${allianceCandidatesMoreMarkup()}`,'Einladen') : ''}${canEditDescription ? commandForm('alliance_edit',input('description','Allianzbeschreibung','text',own.description,'required maxlength="1000"'),'Beschreibung speichern') : ''}${allianceRolePermissionsMarkup()}${mine.role!=='leader'?actionButton('alliance_leave','','Allianz verlassen'): '<p>Die Führung kann an ein anderes Mitglied übertragen werden.</p>'}</article>` : `<div class="columns"><article class="panel"><h3>Allianz gründen</h3>${commandForm('alliance_create',input('tag','Tag (3–8 Zeichen)','text','','required pattern="[A-Za-z0-9]{3,8}"')+input('name','Allianzname','text','','required minlength="3" maxlength="30"'),'Allianz gründen')}</article></div>${allianceInvitationsMarkup('incoming')}${allianceApplicationsMarkup('outgoing')}`)+
      allianceDirectoryMarkup(own,canDiplomacy)+allianceWarsMarkup(own,canDiplomacy)+diplomacyChronicleMarkup();
  }
  if(tab==='messages') {
    const messages=state.messages.filter(m=>m.channel===messageChannel);
    const reported=new Set((state.moderation_cases||[]).filter(item=>item.case_type==='message_report').map(item=>item.message_id));
    const rows=messages.length?messages.map(m=>{
      const report=m.sender!==state.id&&!reported.has(m.id)
        ?`<details><summary>Nachricht melden</summary>${commandForm('message_report',`<input type="hidden" name="key" value="${escapeHtml(m.id)}"><label>Begründung<textarea name="body" minlength="3" maxlength="500" rows="2" required></textarea></label>`,'Meldung senden')}</details>`:'';
      return `<article class="message"><div><b>${escapeHtml(m.name)}</b><small>${new Date(m.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small></div><p>${escapeHtml(m.body)}</p>${state.administration?actionButton('admin_hide',m.id,'Ausblenden'):''}${report}</article>`;
    }).join(''):'<p>Noch keine Nachrichten in diesem Kanal.</p>';
    return intro('FUR NETWORK / KOMMUNIKATION','Eine Welt. Viele Stimmen.')+systemCommunicationMarkup(state)+socialMarkup()+notesMarkup()+`<div class="channel-tabs">${['world','alliance','private'].map(c=>`<button data-channel="${c}" class="${messageChannel===c?'selected':''}">${({world:'Weltkanal',alliance:'Allianzkanal',private:'Private Nachrichten'})[c]}</button>`).join('')}</div><div class="columns"><article class="panel messages"><h3>${messageChannel==='private'?'Gesendete und empfangene Nachrichten':'Kanalverlauf'}</h3>${rows}${state.message_has_more?.[messageChannel]?'<button type="button" class="secondary" data-message-more>Ältere Nachrichten laden</button>':''}</article><article class="panel"><h3>Nachricht verfassen</h3>${commandForm('message',`<input name="channel" type="hidden" value="${messageChannel}">${messageChannel==='private'?`<label>Empfänger auswählen<select name="name" required>${state.players.filter(p=>p.id!==state.id&&!new Set((state.social?.blocked||[]).map(person=>person.id)).has(p.id)).map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)} · ${p.x}:${p.y}</option>`).join('')}</select></label>`:''}<label>Nachricht<textarea name="body" maxlength="2000" rows="6" required></textarea></label>`,'Senden')}<p>Respektiere andere Kommandanten. Moderation kann Nachrichten ausblenden und Schreibrechte einschränken.</p></article></div>${playerModerationCasesMarkup(state)}`;
  }
  if(tab==='market') {
    const options=names.map((n,i)=>[String(i),n]);
    const history=state.market_history||[];
    const historyMarkup = history.length
      ? `<div class="market-history" role="list" aria-label="Preisverlauf der Welt">${history.map(row=>`<div class="audit-row" role="listitem"><small>${new Date(row.timestamp*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})} · ${row.trade_kind==='neutral'?'Neutrale Börse':'Spielermarkt'}</small><b>${names[row.source_resource]} → ${names[row.target_resource]}</b><span>${number(row.source_amount)} → ${number(row.target_amount)} · ${number(row.trade_count)} Trades · Ø ${number(row.weighted_price_milli/1000)} ${names[row.target_resource]}</span></div>`).join('')}</div>`
      : '<p role="status">Noch keine abgeschlossenen Trades im Zeitraum.</p>';
    const offers=state.offers||[];
    const offersMore=state.offers_has_more&&offers.length?`<button type="button" class="secondary" data-market-offers-more="${escapeHtml(offers[offers.length-1].id)}" aria-controls="market-offers-list">Weitere Angebote laden</button><p data-market-offers-more-status role="status" aria-live="polite"></p>`:'';
    return intro('WIRTSCHAFT / SPIELERMARKT','Ein Handel, der beide stärkt.','Ware wird bei Erstellung hinterlegt. Ein Angebot kann genau einmal angenommen werden und läuft nach 24 Stunden ab.')+`<div class="columns"><article class="panel"><h3>Neues Angebot</h3>${commandForm('market_create',select('give','Du bietest',options)+input('amount','Angebotene Menge','number',100,'min="10" max="100000" required')+select('want','Du suchst',options)+input('price','Gewünschte Menge','number',100,'min="10" max="100000" required'),'Ware hinterlegen')}</article><article class="panel"><h3>Reserve-Lager</h3><p>Lieferungen, Handelsware und Rückerstattungen sind hier sicher, auch wenn dein Depot voll ist.</p><div class="cost">${state.reserve.map((n,i)=>`<span>${icons[i]} ${number(n)}</span>`).join('')}</div>${actionButton('reserve_claim','','Ins Depot übernehmen')}</article></div><article class="panel queue-panel"><h3>Offene Angebote</h3><div id="market-offers-list">${offers.length?offers.map(o=>`<div class="alliance-row"><div><b>${escapeHtml(o.name)}</b><small>${number(o.give_amount)} ${names[o.give_resource]} gegen ${number(o.want_amount)} ${names[o.want_resource]}</small></div>${actionButton(o.owner===state.id?'market_cancel':'market_accept',o.id,o.owner===state.id?'Zurücknehmen':'Tauschen')}</div>`).join(''):'<p>Keine offenen Angebote. Erstelle den ersten Handel.</p>'}</div>${offersMore}</article>${syndicateConvoyMarkup(offers)}<article class="panel queue-panel" aria-labelledby="market-history-title"><h3 id="market-history-title">Preisverlauf der Welt (30 Tage)</h3><p>Stundenwerte abgeschlossener Trades; ohne Kontodaten. Preis zeigt Tauscheinheiten je Einheit des ersten Rohstoffs.</p>${historyMarkup}</article>`;
  }
  if(tab==='worldops') {
    return intro('GENESIS / WELTBETRIEB','Dein Platz in der neuen Welt.','Fraktionen, Live-Ereignisse und Saisons prägen die gemeinsame Spielwelt.')+`<div class="cards">${Object.entries(factionNames).map(([k,n])=>`<article class="card"><h3>${n}</h3><p>${({pioneers:'+10 Prozentpunkte Rohstoffproduktion.',wardens:'Der Schildwall deiner Kolonie ist im PvP 40 % stärker.',syndicate:'Der neutrale Tausch liefert 60 statt 50 Prozent.'})[k]}</p>${state.faction_chosen?`<small>${state.profile.faction===k?'DEINE FRAKTION':'Fraktion bereits gewählt'}</small>`:actionButton('faction',k,'Fraktion wählen')}</article>`).join('')}</div><div class="columns queue-panel"><article class="panel"><h3>Live-Ereignisse</h3>${liveEventsMarkup()}</article><article class="panel"><h3>Saisons</h3>${state.seasons.length?state.seasons.map(s=>`<div class="quest"><div><b>${escapeHtml(s.name)}</b><small>${s.archived?'Abgeschlossen':'Wettbewerb läuft'} · Ende ${new Date(s.ends*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</small><small>Regelstand ${escapeHtml(s.rules_version||'unbekannt')} · SHA-256 ${escapeHtml((s.rules_digest||'').slice(0,12)||'nicht verfügbar')}${s.rules_source==='legacy_backfill'?' · Referenz nach Saisonstart ergänzt':''}</small>${s.archived?`<p>${JSON.parse(s.standings).slice(0,3).map((r,i)=>`${i+1}. ${escapeHtml(r.name)} (${r.score})`).join('<br>')}</p>${s.alliance_rules_version?`<small>FUR-3-Allianzarchiv · ${escapeHtml(s.alliance_rules_version)} · SHA-256 ${escapeHtml(s.alliance_rules_digest.slice(0,12))} · bestätigte Konten mit E-Mail</small><p>${(s.alliance_standings||[]).map(r=>`${r.rank}. ${escapeHtml(r.alliance_tag)} ${escapeHtml(r.alliance_name)} · ${number(r.score)} Punkte · ${number(r.eligible_accounts)} Konten`).join('<br>')||'Keine qualifizierte Allianzwertung.'}</p>`:''}`:''}</div></div>`).join(''):'<p>Die nächste Saison wird von der Spielleitung angekündigt.</p>'}</article></div><article class="panel queue-panel"><h3>Urlaubsmodus</h3><p>Mindestens 24 Stunden. Währenddessen ruhen Produktion und eigene Spielaktionen; deine Kolonie ist vor neuen Angriffen geschützt. Nur ohne laufende Aufträge und feindliche Anmärsche aktivierbar.</p>${state.vacation_until>state.server_time?`<b>Geschützt bis ${new Date(state.vacation_until*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})}</b>`:actionButton('vacation','','24 Stunden pausieren')}</article>`;
  }
  if(tab==='account') {
    return intro('KONTO / SICHERHEIT','Dein Kommando bleibt deins.')+`<div class="columns"><article class="panel"><h3>Kommandantenname</h3><p>Änderung alle 24 Stunden. Zuletzt geändert: ${state.profile.name_changed_at?new Date(state.profile.name_changed_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE'):'Noch nie'}.</p>${commandForm('account_rename',input('new_name','Neuer Kommandantenname','text','','required minlength="3" maxlength="24"')+input('password','Aktuelles Passwort','password','','required autocomplete="current-password"')+(state.profile.mfa_enabled?input('code','Authenticator-Code','text','','required inputmode="numeric" autocomplete="one-time-code"'):''),'Namen ändern')}<h3>E-Mail & Wiederherstellung</h3><p>${escapeHtml(state.profile.email||'Noch keine E-Mail hinterlegt.')} · ${state.profile.verified?'bestätigt':'unbestätigt'}</p>${commandForm('account_email',input('email','E-Mail-Adresse','email','','required')+input('password','Aktuelles Passwort','password','','required autocomplete="current-password"')+input('code','Authenticator-Code (falls aktiv)','text','','inputmode="numeric" autocomplete="one-time-code"'),'Adresse speichern')}<button class="compact" id="resend-verification">Bestätigung erneut anfordern</button><button class="text-button" id="open-public-account">E-Mail bestätigen / Passwort zurücksetzen</button><p>Exportiere deine Kontodaten als JSON. Zur Bestätigung werden dein aktuelles Passwort und bei aktivem Authenticator ein frischer Code verlangt.</p>${commandForm('account_export',input('password','Aktuelles Passwort','password','','required autocomplete="current-password"')+(state.profile.mfa_enabled?input('code','Authenticator-Code','text','','required inputmode="numeric" autocomplete="one-time-code"'):''),'Datenexport erstellen')}</article><article class="panel"><h3>Authenticator (TOTP)</h3><p>${state.profile.mfa_enabled?'Aktiviert. Anmeldungen benötigen einen zeitbasierten Code.':'Noch nicht aktiviert. Für Administrationskonten im Livebetrieb erforderlich.'}</p>${commandForm(state.profile.mfa_enabled?'account_mfa_disable':'account_mfa_begin',input('password','Aktuelles Passwort','password','','required autocomplete="current-password"')+(state.profile.mfa_enabled?input('code','Authenticator-Code','text','','required inputmode="numeric" autocomplete="one-time-code"'):''),state.profile.mfa_enabled?'Authenticator deaktivieren':'Einrichtung starten')}<div id="mfa-setup" hidden><p>Übertrage diesen Schlüssel in deine Authenticator-App und bestätige den ersten Code. Der Schlüssel wird nur hier angezeigt:</p><code id="mfa-secret"></code>${commandForm('account_mfa_confirm',input('code','Aktueller Authenticator-Code','text','','required pattern="[0-9]{6}" autocomplete="one-time-code"'),'Aktivieren')}</div>${state.profile.mfa_enabled?`<h4>Recovery-Codes</h4><p>Jeder Code ist einmalig. Bei Neuausstellung werden bisherige Codes ungültig; erforderlich sind aktuelles Passwort und ein neuer Authenticator-Code.</p>${commandForm('account_recovery_codes_regenerate',input('password','Aktuelles Passwort','password','','required autocomplete="current-password"')+input('code','Aktueller Authenticator-Code','text','','required inputmode="numeric" autocomplete="one-time-code"'),'Neue Codes ausstellen')}<div id="recovery-codes-result" hidden role="status" aria-live="polite"><p>Jetzt sicher speichern. Diese Codes werden nicht erneut angezeigt.</p><pre id="recovery-codes-list"></pre><button type="button" id="recovery-codes-done" class="secondary">Gespeichert, weiter</button></div>`:''}</article></div><article class="panel queue-panel"><h3>Passwort ändern</h3>${commandForm('account_password',input('password','Aktuelles Passwort','password','','required autocomplete="current-password"')+input('new_password','Neues Passwort','password','','required minlength="8" maxlength="128" autocomplete="new-password"')+input('code','Authenticator-Code (falls aktiviert)','text','','inputmode="numeric" autocomplete="one-time-code"'),'Passwort ändern')}<p>Zur Sicherheit wirst du nach dem Wechsel auf allen Geräten abgemeldet.</p></article><article class="panel queue-panel"><h3>Angemeldete Geräte und Sitzungen</h3><p>Hier siehst du aktive Anmeldungen für dein Konto. Sitzungstoken und Netzwerkadressen werden nicht angezeigt.</p><div id="account-sessions" role="list" aria-live="polite">Sitzungen werden geladen …</div><div class="button-row"><button type="button" id="revoke-other-sessions" class="secondary">Andere Sitzungen abmelden</button><button type="button" id="revoke-all-sessions" class="secondary">Alle Sitzungen abmelden</button></div><p id="session-management-status" role="status" aria-live="polite"></p></article><article class="panel queue-panel"><h3>Betreiber & Datenschutz</h3><div id="operator-info"><p>Betreiberangaben werden geladen …</p></div><button id="local-mail" class="compact">Lokale Mailvorschau öffnen</button><div id="mail-preview"></div></article>`;
  }
  if(tab==='admin') {
    const admin=state.administration;
    if(!admin) return intro('SPIELLEITUNG','Kein Administrationszugriff.','Administrationsrechte werden ausschließlich über die Serverkonsole vergeben.');
    return intro('SPIELLEITUNG / KONTROLLE','Eine verlässliche Welt.','Alle Moderations- und Weltregeländerungen werden protokolliert.')+`<article class="panel"><h3>Betriebszustand</h3><p>Worker: ${admin.worker?new Date(admin.worker.heartbeat*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'}):'Noch kein Lebenszeichen'} · ${admin.failure_total??admin.failures.length} fehlerhafte Aufträge</p><div class="button-row">${Object.entries(state.flags).map(([key,value])=>actionButton('admin_flag',key,`${key}: ${value?'AN':'AUS'}`,{value:String(!value)})).join('')}</div></article><div class="columns queue-panel">${adminLiveEventFormMarkup()}<article class="panel"><h3>Saisonwettbewerb</h3>${commandForm('admin_season',input('name','Saisonname','text','','required minlength="3" maxlength="60"')+input('days','Dauer in Tagen','number',30,'required min="1" max="365"'),'Saison starten')}<p>Saisons archivieren die Rangliste. Spielstände bleiben erhalten. Jede Saisonwelt hat einen Wettbewerb. Lege für die nächste Runde eine neue Saisonwelt an. Sandboxwelten sind Übungswelten ohne PvP und Saisonwettbewerbe.</p></article></div>${adminUsersMarkup(admin)}${adminFailuresMarkup(admin)}${adminAuditMarkup(admin)}`;
  }
  return '';
}
async function accountCall(action,values={}) {
  try {
    const result=await api('account/private',{action,...values});
    if(result.format==='fur-empire-account-export') { const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='fur-empire-account-export.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),0);notify('Dein Datenexport wurde heruntergeladen.'); }
    else if(result.secret) { document.getElementById('mfa-setup').hidden=false; document.getElementById('mfa-secret').textContent=result.secret; }
    else if(result.recovery_codes) { let panel=document.getElementById('recovery-codes-result'); if(!panel) { panel=document.createElement('div');panel.id='recovery-codes-result';panel.setAttribute('role','status');panel.setAttribute('aria-live','polite');panel.innerHTML='<p>Jetzt sicher speichern. Diese Codes werden nicht erneut angezeigt.</p><pre id="recovery-codes-list"></pre><button type="button" id="recovery-codes-done" class="secondary">Gespeichert, weiter</button>';document.getElementById('mfa-setup')?.append(panel); } window.furRecoveryCodesPending=true; document.getElementById('recovery-codes-list').textContent=result.recovery_codes.join('\n'); panel.hidden=false; document.getElementById('mfa-setup').hidden=false; document.getElementById('recovery-codes-done').onclick=()=>{window.furRecoveryCodesPending=false;location.reload();}; }
    else if(['mfa_confirm','mfa_disable','password'].includes(action)) { location.reload(); }
    else { notify('Kontoaktion ausgeführt.'); await refresh(); }
  } catch(error) { notify(error.message); }
}
function bindSystems() {
  const profileForm=document.querySelector('#player-profile-settings-form');
  if(profileForm)profileForm.onsubmit=event=>{
    event.preventDefault();
    const form=event.currentTarget;
    const badges=[...form.querySelectorAll('input[name="profile_badge"]:checked')].map(input=>input.value);
    const status=form.querySelector('[data-profile-settings-status]');
    if(badges.length>3){if(status)status.textContent='Wähle höchstens drei Abzeichen.';return;}
    command('profile_settings_update',{
      profile_visibility:form.elements.profile_visibility.value,
      profile_title:form.elements.profile_title.value,
      profile_reward_title:form.elements.profile_reward_title.value,
      profile_skin:form.elements.profile_skin.value,
      profile_banner:form.elements.profile_banner.value,
      profile_badges:badges.join(','),
    });
  };
  document.querySelectorAll('[data-system-action]').forEach(b=>b.onclick=()=>command(b.dataset.systemAction,JSON.parse(b.dataset.payload)));
  document.querySelectorAll('[data-system]').forEach(f=>f.onsubmit=async event=>{
    event.preventDefault();
    const data=Object.fromEntries(new FormData(f));
    f.querySelectorAll('input[type="number"]').forEach(e=>{data[e.name]=Number(e.value);});
    if(Object.hasOwn(data,'world_id'))data.world_id=Number(data.world_id);
    f.querySelectorAll('input[type="checkbox"]').forEach(e=>{data[e.name]=e.checked;});
    const action=f.dataset.system;
    if(action==='admin_announcement_create') {
      const localTime=data.publish_at_local;
      if(localTime) {
        const publishAt=Math.floor(new Date(localTime).getTime()/1000);
        if(!Number.isSafeInteger(publishAt)){notify('Ungültiger Veröffentlichungszeitpunkt.');return;}
        data.publish_at=publishAt;
      } else data.publish_at=Number(state.server_time||Math.floor(Date.now()/1000));
      delete data.publish_at_local;
    }
    if(action==='alliance_permissions_update') data.permissions=Array.from(f.querySelectorAll('input[name="permission"]:checked'),input=>input.value);
    if(['alliance_treasury_donate','alliance_treasury_request','alliance_project_contribute'].includes(action)) { data.resources=[0,1,2].map(index=>Number(f.elements[`resource-${index}`].value));[0,1,2].forEach(index=>delete data[`resource-${index}`]); }
    if(action.startsWith('account_')) { await accountCall(action.slice(8),data); if(action==='account_export') f.reset(); }
    else if(await command(action,data)) { if(action==='message'||['alliance_treasury_donate','alliance_treasury_request','alliance_project_contribute'].includes(action)) f.reset(); }
  });
  document.getElementById('alliance-garrison-form')?.addEventListener('submit',async event=>{
    event.preventDefault();
    const form=event.currentTarget, army={};
    Object.keys(state.units||{}).forEach(unit=>{army[unit]=Number(form.elements[`garrison_${unit}`].value);});
    await command('alliance_garrison_station',{key:form.elements.key.value,army});
  });
  document.querySelectorAll('[data-channel]').forEach(b=>b.onclick=()=>{messageChannel=b.dataset.channel;render();});
  document.querySelector('[data-announcements-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget, entries=state?.announcements, cursor=entries?.at(-1)?.id, owner=state?.id, worldId=state?.active_world?.id;
    if(!owner||!worldId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-announcements-status]');
    if(status)status.textContent='Ältere Ankündigungen werden geladen …';
    try{
      const page=await api(`announcements?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==owner||state?.active_world?.id!==worldId)return;
      const known=new Set(entries.map(item=>item.id));
      state.announcements.push(...page.entries.filter(item=>!known.has(item.id)));
      state.announcements_has_more=page.has_more;
      render();
    }catch(error){button.disabled=false;if(status)status.textContent=error.message;}
  });
  document.querySelector('[data-system-mail-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget, entries=state?.system_mail, cursor=entries?.at(-1)?.id, owner=state?.id;
    if(!owner||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-system-mail-status]');
    if(status)status.textContent='Ältere Systemnachrichten werden geladen …';
    try{
      const page=await api(`system-mail?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==owner)return;
      const known=new Set(entries.map(item=>item.id));
      state.system_mail.push(...page.entries.filter(item=>!known.has(item.id)));
      state.system_mail_has_more=page.has_more;
      render();
    }catch(error){button.disabled=false;if(status)status.textContent=error.message;}
  });
  document.querySelector('[data-notes-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget, entries=state?.notes, cursor=entries?.at(-1)?.id, userId=state?.id, worldId=state?.active_world?.id;
    if(!userId||!worldId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-notes-status]');
    if(status)status.textContent='Weitere Notizen werden geladen …';
    try{
      const page=await api(`notes?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.active_world?.id!==worldId)return;
      const known=new Set(state.notes.map(note=>note.id));
      state.notes.push(...page.notes.filter(note=>!known.has(note.id)));
      state.notes_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-shared-reports-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget, entries=state?.alliance_shared_reports, cursor=entries?.at(-1)?.id, userId=state?.id, worldId=state?.active_world?.id;
    if(!userId||!worldId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-shared-reports-status]');
    if(status)status.textContent='Weitere geteilte Berichte werden geladen …';
    try{
      const page=await api(`alliance/shared-reports?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.active_world?.id!==worldId)return;
      const known=new Set(entries.map(entry=>entry.id));
      state.alliance_shared_reports.push(...page.entries.filter(entry=>!known.has(entry.id)));
      state.alliance_shared_reports_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelectorAll('[data-player-directory-more]').forEach(button=>button.addEventListener('click',async()=>{
    const userId=state?.id, worldId=state?.active_world?.id;
    const cursor=state?.players?.at(-1)?.id;
    if(!userId||!worldId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-player-directory-status]');
    if(status)status.textContent='Weitere Kommandanten werden geladen …';
    try{
      const page=await api(`players?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.active_world?.id!==worldId)return;
      const known=new Set((state.players||[]).map(player=>player.id));
      state.players.push(...page.players.filter(player=>!known.has(player.id)));
      state.players_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  }));
  document.querySelectorAll('[data-social-more]').forEach(button=>button.addEventListener('click',async()=>{
    const listName=button.dataset.socialMore;
    const userId=state?.id, entries=state?.social?.[listName];
    const cursor=entries?.at(-1)?.id;
    if(!userId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector(`[data-social-status="${listName}"]`);
    if(status)status.textContent='Weitere Kontakte werden geladen …';
    try{
      const query=new URLSearchParams({list:listName,before:cursor});
      const page=await api(`social?${query.toString()}`);
      if(state?.id!==userId||!state?.social)return;
      const known=new Set(state.social[listName].map(entry=>entry.id));
      state.social[listName].push(...page.entries.filter(entry=>!known.has(entry.id)));
      state.social[`${listName}_has_more`]=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  }));
  document.querySelectorAll('[data-admin-list-more]').forEach(button=>button.addEventListener('click',async()=>{
    const kind=button.dataset.adminListMore;
    const key=kind==='users'?'users':'failures';
    const cursor=state?.administration?.[key]?.at(-1)?.id;
    const userId=state?.id;
    if(!userId||!cursor||button.disabled||!state?.administration)return;
    button.disabled=true;
    const status=document.querySelector(`[data-admin-list-status="${kind}"]`);
    if(status)status.textContent=kind==='users'?'Weitere Kommandanten werden geladen …':'Weitere Auftragsfehler werden geladen …';
    try{
      const endpoint=kind==='users'?'admin/users':'admin/job-failures';
      const page=await api(`${endpoint}?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||!state?.administration)return;
      const known=new Set(state.administration[key].map(entry=>entry.id));
      state.administration[key].push(...page[key].filter(entry=>!known.has(entry.id)));
      state.administration[`${key}_has_more`]=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  }));
  document.querySelector('[data-admin-cases-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget, cases=state?.administration?.cases, cursor=cases?.at(-1)?.id, userId=state?.id;
    if(!userId||!cursor||button.disabled||!state?.administration)return;
    button.disabled=true;
    const status=document.querySelector('[data-admin-cases-status]');
    if(status)status.textContent='Weitere Moderationsfälle werden geladen …';
    try{
      const page=await api(`admin/moderation-cases?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||!state?.administration)return;
      const known=new Set(state.administration.cases.map(item=>item.id));
      state.administration.cases.push(...page.cases.filter(item=>!known.has(item.id)));
      state.administration.cases_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-admin-audit-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const entries=state?.administration?.audit;
    const cursor=entries?.at(-1)?.id;
    const userId=state?.id;
    if(!userId||!cursor||button.disabled||!state?.administration)return;
    button.disabled=true;
    const status=document.querySelector('[data-admin-audit-status]');
    if(status)status.textContent='Ältere Audit-Einträge werden geladen …';
    try{
      const page=await api(`admin/audit?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||!state?.administration)return;
      const known=new Set(state.administration.audit.map(entry=>entry.id));
      state.administration.audit.push(...page.entries.filter(entry=>!known.has(entry.id)));
      state.administration.audit_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-diplomacy-events-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const events=state?.diplomacy_events;
    const cursor=events?.at(-1)?.id;
    const userId=state?.id;
    if(!userId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-diplomacy-events-status]');
    if(status)status.textContent='Ältere Diplomatieereignisse werden geladen …';
    try{
      const page=await api(`diplomacy/events?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId)return;
      const known=new Set(state.diplomacy_events.map(entry=>entry.id));
      state.diplomacy_events.push(...page.events.filter(entry=>!known.has(entry.id)));
      state.diplomacy_events_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-live-events-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const entries=state?.events;
    const cursor=entries?.at(-1)?.id;
    const userId=state?.id;
    if(!userId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-live-events-status]');
    if(status)status.textContent='Ältere Ereignisse werden geladen …';
    try{
      const page=await api(`events?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId)return;
      const known=new Set(state.events.map(entry=>entry.id));
      state.events.push(...page.events.filter(entry=>!known.has(entry.id)));
      state.events_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-alliance-directory-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const userId=state?.id;
    const cursor=state?.alliances?.at(-1)?.id;
    if(!userId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-alliance-directory-status]');
    if(status)status.textContent='Weitere Allianzen werden geladen …';
    try{
      const page=await api(`alliances?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId)return;
      const known=new Set(state.alliances.map(alliance=>alliance.id));
      state.alliances.push(...page.alliances.filter(alliance=>!known.has(alliance.id)));
      state.alliances_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-alliance-members-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const userId=state?.id, allianceId=state?.membership?.alliance_id;
    const cursor=state?.members?.at(-1)?.user_id;
    if(!userId||!allianceId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-alliance-members-status]');
    if(status)status.textContent='Weitere Mitglieder werden geladen …';
    try{
      const page=await api(`alliance/members?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.membership?.alliance_id!==allianceId)return;
      const known=new Set(state.members.map(member=>member.user_id));
      state.members.push(...page.members.filter(member=>!known.has(member.user_id)));
      state.members_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-alliance-candidates-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const userId=state?.id, allianceId=state?.membership?.alliance_id;
    const worldId=state?.active_world?.id, cursor=state?.alliance_candidates?.at(-1)?.id;
    if(!userId||!allianceId||!worldId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-alliance-candidates-status]');
    if(status)status.textContent='Weitere Kandidaten werden geladen …';
    try{
      const page=await api(`alliance/candidates?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.membership?.alliance_id!==allianceId||state?.active_world?.id!==worldId)return;
      const known=new Set((state.alliance_candidates||[]).map(candidate=>candidate.id));
      state.alliance_candidates.push(...page.candidates.filter(candidate=>!known.has(candidate.id)));
      state.alliance_candidates_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelector('[data-forum-reports-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const userId=state?.id, allianceId=state?.membership?.alliance_id;
    const cursor=state?.alliance_forum_reports?.at(-1)?.id;
    if(!userId||!allianceId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-forum-reports-more-status]');
    if(status)status.textContent='Weitere Meldungen werden geladen …';
    try{
      const page=await api(`alliance/forum-reports?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.membership?.alliance_id!==allianceId)return;
      const known=new Set((state.alliance_forum_reports||[]).map(report=>report.id));
      state.alliance_forum_reports.push(...page.reports.filter(report=>!known.has(report.id)));
      state.alliance_forum_reports_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  document.querySelectorAll('[data-alliance-applications-more]').forEach(button=>button.addEventListener('click',async()=>{
    const direction=button.dataset.allianceApplicationsMore;
    const userId=state?.id, allianceId=state?.membership?.alliance_id||'';
    const key=direction==='incoming'?'alliance_incoming_applications':'alliance_applications';
    const cursor=state?.[key]?.at(-1)?.id;
    if(!userId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector(`[data-alliance-applications-status="${direction}"]`);
    if(status)status.textContent='Weitere Bewerbungen werden geladen …';
    try{
      const query=new URLSearchParams({direction,before:cursor});
      const page=await api(`alliance/applications?${query.toString()}`);
      if(state?.id!==userId||(state?.membership?.alliance_id||'')!==allianceId)return;
      const known=new Set((state[key]||[]).map(application=>application.id));
      state[key].push(...page.applications.filter(application=>!known.has(application.id)));
      state[`${key}_has_more`]=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  }));
  document.querySelectorAll('[data-alliance-invitations-more]').forEach(button=>button.addEventListener('click',async()=>{
    const direction=button.dataset.allianceInvitationsMore;
    const userId=state?.id, allianceId=state?.membership?.alliance_id||'';
    const key=direction==='outgoing'?'alliance_outgoing_invites':'invites';
    const cursor=state?.[key]?.at(-1)?.id;
    if(!userId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector(`[data-alliance-invitations-status="${direction}"]`);
    if(status)status.textContent='Weitere Einladungen werden geladen …';
    try{
      const query=new URLSearchParams({direction,before:cursor});
      const page=await api(`alliance/invitations?${query.toString()}`);
      if(state?.id!==userId||(state?.membership?.alliance_id||'')!==allianceId)return;
      const known=new Set((state[key]||[]).map(invite=>invite.id));
      state[key].push(...page.invitations.filter(invite=>!known.has(invite.id)));
      state[`${key}_has_more`]=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  }));
  document.querySelector('[data-message-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    button.disabled=true;
    const visible=state.messages.filter(message=>message.channel===messageChannel);
    const before=visible.length?visible[visible.length-1].id:'';
    try {
      const query=new URLSearchParams({channel:messageChannel});
      if(before)query.set('before',before);
      const page=await api(`messages?${query.toString()}`);
      const known=new Set(state.messages.map(message=>message.id));
      state.messages.push(...page.messages.filter(message=>!known.has(message.id)));
      state.messages.sort((left,right)=>right.created-left.created||(left.id<right.id?1:left.id>right.id?-1:0));
      state.message_has_more[messageChannel]=page.has_more;
      render();
    } catch(error) {
      button.disabled=false;
      notify(error.message);
    }
  });
  document.querySelector('[data-market-offers-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const userId=state?.id, worldId=state?.active_world?.id;
    const cursor=state?.offers?.at(-1)?.id;
    if(!userId||!worldId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-market-offers-more-status]');
    if(status)status.textContent='Weitere Angebote werden geladen …';
    try{
      const page=await api(`market/offers?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.active_world?.id!==worldId)return;
      const known=new Set((state.offers||[]).map(offer=>offer.id));
      state.offers.push(...page.offers.filter(offer=>!known.has(offer.id)));
      state.offers_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  if(document.getElementById('open-public-account')) document.getElementById('open-public-account').onclick=()=>document.getElementById('account-dialog').showModal();
  if(document.getElementById('resend-verification')) document.getElementById('resend-verification').onclick=()=>accountCall('verification_resend');
  if(document.getElementById('local-mail')) document.getElementById('local-mail').onclick=async()=>{try {const mail=await api('account/local-mail');document.getElementById('mail-preview').innerHTML=mail.map(m=>`<article class="message"><b>${escapeHtml(m.subject)}</b><pre>${escapeHtml(m.body)}</pre></article>`).join('')||'<p>Noch keine lokalen Testmails.</p>';}catch(error){notify(error.message);}};
  bindSessionManagement();
  if(tab==='account') api('public-config').then(config=>{const el=document.getElementById('operator-info');if(el) el.innerHTML=`<p>${escapeHtml(config.operator_name||'Lokale Entwicklungswelt')}<br>${escapeHtml(config.operator_contact||'Noch keine öffentlichen Betreiberangaben hinterlegt.')}<br>Kontodaten, Spielbefehle und Nachrichten werden zum Betrieb der Spielwelt gespeichert. Auskunft oder Löschung bitte beim Betreiber anfragen.</p>`;const b=document.getElementById('local-mail');if(b)b.hidden=config.production;}).catch(error=>notify(error.message));
}

function renderAccountSessions(list,snapshot) {
  const sessions=snapshot?.sessions||[];
  list.innerHTML=sessions.length?sessions.map(item=>{const created=item.created?new Date(item.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE'):'Zeitpunkt nicht verfügbar';return `<article class="quest" role="listitem"><div><b>${item.current?'Diese Sitzung':'Angemeldetes Gerät'}</b><small>${escapeHtml(item.user_agent||'Gerät nicht angegeben')} · gestartet ${created} · gültig bis ${new Date(item.expires*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</small></div>${item.current?'<span>Aktuell</span>':`<button type="button" class="secondary" data-revoke-session="${escapeHtml(item.id)}">Abmelden</button>`}</article>`;}).join(''):'<p>Keine aktiven Sitzungen gefunden.</p>';
  if(snapshot?.has_more&&sessions.length)list.insertAdjacentHTML('beforeend','<button type="button" class="secondary" data-account-sessions-more>Weitere Sitzungen laden</button><p role="status" data-account-sessions-status aria-live="polite"></p>');
  list.querySelector('[data-account-sessions-more]')?.addEventListener('click',loadOlderAccountSessions);
  list.querySelectorAll('[data-revoke-session]').forEach(button=>button.onclick=async()=>{
    try {await api(`account/sessions/revoke/${encodeURIComponent(button.dataset.revokeSession)}`,{});document.getElementById('session-management-status').textContent='Sitzung abgemeldet.';await loadAccountSessions(true);}
    catch(error){document.getElementById('session-management-status').textContent=error.message;}
  });
}

async function loadOlderAccountSessions(event) {
  const button=event.currentTarget;
  const owner=state?.id||'';
  const sessions=accountSessionSnapshot?.sessions||[];
  const cursor=sessions.at(-1)?.id;
  if(!owner||!cursor||button.disabled)return;
  button.disabled=true;
  const status=document.querySelector('[data-account-sessions-status]');
  if(status)status.textContent='Weitere Sitzungen werden geladen …';
  try {
    const page=await api(`account/sessions?before=${encodeURIComponent(cursor)}`);
    if(state?.id!==owner||accountSessionSnapshotOwner!==owner)return;
    const known=new Set(sessions.map(item=>item.id));
    accountSessionSnapshot.sessions.push(...page.sessions.filter(item=>!known.has(item.id)));
    accountSessionSnapshot.has_more=page.has_more;
    accountSessionSnapshotAt=Date.now();
    const list=document.getElementById('account-sessions');
    if(list)renderAccountSessions(list,accountSessionSnapshot);
  } catch(error) {
    button.disabled=false;
    if(status)status.textContent=error.message;
  }
}

async function loadAccountSessions(force=false) {
  const list=document.getElementById('account-sessions');
  if(!list)return;
  const owner=state?.id||'';
  if(accountSessionSnapshotOwner!==owner)clearAccountSessionSnapshot();
  accountSessionSnapshotOwner=owner;
  if(!force&&accountSessionSnapshot&&Date.now()-accountSessionSnapshotAt<15000){renderAccountSessions(list,accountSessionSnapshot);return;}
  try {
    const result=await api('account/sessions');
    accountSessionSnapshot=result;
    accountSessionSnapshotAt=Date.now();
    renderAccountSessions(list,accountSessionSnapshot);
  } catch(error) { list.textContent=error.message; }
}

function bindSessionManagement() {
  const list=document.getElementById('account-sessions');
  if(!list)return;
  loadAccountSessions();
  const status=document.getElementById('session-management-status');
  document.getElementById('revoke-other-sessions').onclick=async()=>{
    if(!window.confirm('Alle anderen Sitzungen dieses Kontos abmelden?'))return;
    try {const result=await api('account/sessions/revoke-others',{});status.textContent=`${result.revoked} andere Sitzung(en) abgemeldet.`;await loadAccountSessions(true);}
    catch(error){status.textContent=error.message;}
  };
  document.getElementById('revoke-all-sessions').onclick=async()=>{
    if(!window.confirm('Alle Sitzungen abmelden? Du wirst auch auf diesem Gerät abgemeldet.'))return;
    try {await api('account/sessions/revoke-all',{});clearAccountSessionSnapshot();window.dispatchEvent(new Event('fur:logout-everywhere'));notify('Alle Sitzungen wurden abgemeldet. Bitte melde dich erneut an.');}
    catch(error){status.textContent=error.message;}
  };
}
