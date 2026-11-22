'use strict';
let state, csrf = '', tab = 'overview', register = false, target, busy = false, mapX = 0, mapY = 0, renderedTab = '', mapSearch = '', mapFilter = 'all', mapRouteId = '', missionTemplates = [], missionTemplateOwner = '', productionTemplates = [], productionTemplateOwner = '';
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let gameAssetCatalog = null;
const gameAssetCatalogReady = fetch('/static/assets/game/asset-catalog.json').then(response => {
  if (!response.ok) throw new Error(`Assetkatalog nicht erreichbar (${response.status})`);
  return response.json();
}).then(catalog => { gameAssetCatalog = catalog; }).catch(error => {
  console.error('FUR-Assetkatalog konnte nicht geladen werden:', error);
});
function assetUrl(key) {
  if (!gameAssetCatalog || typeof key !== 'string') return '';
  const resolved = gameAssetCatalog.assets[key] ? key : gameAssetCatalog.aliases[key];
  const asset = resolved && gameAssetCatalog.assets[resolved];
  return asset?.files?.find(file => file.endsWith('.webp'))
    || asset?.files?.find(file => file.endsWith('.svg'))
    || asset?.files?.[0] || '';
}
function assetImage(key, alt, className = 'game-asset') {
  const source = assetUrl(key);
  return source ? `<img class="${escapeHtml(className)}" src="${source}" alt="${escapeHtml(alt)}" loading="lazy" decoding="async">` : '';
}
function gameAssetKey(kind, id) {
  if (!gameAssetCatalog || typeof id !== 'string') return '';
  const roots = {buildings:['terra/buildings','orbit/buildings'],research:['terra/research','orbit/research'],units:['terra/units','orbit/units'],inventory:['terra/inventory']};
  const itemAliases = {repair_kit:'field_repair_kit',prestige_token_non_purchasable:'prestige_token'};
  const candidates = (roots[kind] || []).map(root => `${root}/${itemAliases[id] || id}`);
  return candidates.find(key => gameAssetCatalog.assets[key]) || '';
}
const names = ['Holz', 'Stein', 'Erz'];
const icons = ['♣', '▧', '◈'];
const resourceIcon = (index, className='resource-icon') => assetImage(`terra/resources/${['wood','stone','ore'][index]}`,names[index],className);
const number = n => window.FURI18n ? window.FURI18n.number(n) : new Intl.NumberFormat('de-DE').format(n);
const MAP_SIZE = 64, MAP_VIEW_SIZE = 20, MAP_MAX_START = MAP_SIZE - MAP_VIEW_SIZE;
function productionGraphMarkup(details) {
  if (!Array.isArray(details) || details.length !== names.length) return '';
  const rates = details.map(detail => Math.max(0, Number(detail.per_second_ten_thousandths || 0) / 10000));
  const maximum = Math.max(...rates, 0.01);
  const rows = details.map((detail, index) => {
    const rate = rates[index];
    const width = Math.max(0, Math.min(100, rate / maximum * 100));
    const forecast = detail.paused ? 'Produktion pausiert' : detail.seconds_to_cap === null
      ? 'Depot voll' : `Depot voll in ca. ${number(Math.ceil(detail.seconds_to_cap / 60))} min`;
    const label = `${names[index]}: ${rate.toFixed(2)} pro Sekunde`;
    return `<li><div class="production-graph-row"><strong>${resourceIcon(index)} ${names[index]}</strong><progress max="${maximum}" value="${rate}" aria-label="${escapeHtml(label)}">${width}%</progress><b>${rate.toFixed(2)}/s</b></div><small>Basis ${number(detail.base_per_second)}/s · Bonus ${number(detail.bonus_percent)}% · ${escapeHtml(detail.terrain)} ${number(detail.terrain_percent)}% · ${number(detail.storage)} / ${number(detail.storage_cap)} · ${forecast}</small></li>`;
  }).join('');
  return `<details class="production-graph"><summary>Produktionsgrafik</summary><section class="production-graph-panel" aria-label="Aktuelle Rohstoffproduktion"><p>Aktuelle Serverrate einschließlich Boni und Gelände. Zukünftige Regel- oder Ereignisänderungen sind nicht prognostiziert.</p><ul>${rows}</ul></section></details>`;
}
function genericItemInventoryMarkup(inventory) {
  if (!inventory?.items?.length) return '';
  const rows = inventory.items.map(item => {
    const freeStack = item.amount > 0 || inventory.used_stack_types < inventory.max_stack_types;
    const room = freeStack ? Math.max(0, inventory.stack_limit - item.amount - item.incoming_amount) : 0;
    const claimable = Math.min(item.reserve_amount, room);
    return `<article class="panel good-card inventory-card">${assetImage(gameAssetKey('inventory',item.id),item.name,'inventory-art')}<h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description)}</p><strong>${number(item.amount)} / ${number(inventory.stack_limit)}</strong><p>Unterwegs: ${number(item.incoming_amount)} · Reserve: ${number(item.reserve_amount)}</p>${item.reserve_amount?`<button type="button" data-item-claim="${escapeHtml(item.id)}" data-item-amount="${claimable}" ${claimable<1?'disabled':''}>Reserve ins Inventar holen</button>`:''}</article>`;
  }).join('');
  return `<article class="panel"><h2 data-i18n="section.inventory">Gegenstandsinventar</h2><p>${number(inventory.used_stack_types)} von ${number(inventory.max_stack_types)} Stapelplätzen belegt · höchstens ${number(inventory.stack_limit)} je Gegenstandsart · ${escapeHtml(inventory.version)}</p><div class="goods-grid">${rows}</div></article>`;
}

function commanderMarkup(commander, doctrines, respec, resources, serverTime) {
  if (!commander) return '';
  if (!commander.enabled) return '<article class="panel queue-panel"><h2>Commander</h2><p>Die Heldenverwaltung ist in dieser Welt nicht aktiviert.</p></article>';
  const labels = {military:'Militär',economy:'Wirtschaft',recon:'Aufklärung',command:'Kommando'};
  const stats = Object.entries(labels).map(([id,label]) => {const available=(commander.available_stats||[]).includes(id);return `<article class="panel good-card"><h3>${label}</h3><strong>Stufe ${number(commander.stats[id])} / ${number(commander.stat_cap)}</strong><button type="button" data-hero-stat="${id}" aria-label="Skillpunkt für ${label} vergeben" ${!available||commander.skill_points<1||commander.stats[id]>=commander.stat_cap?'disabled':''}>Skillpunkt vergeben</button>${available?'':'<small>Wird mit der FUR-3-Doktrinenregel freigeschaltet.</small>'}</article>`;}).join('');
  const progress = commander.level>=commander.level_cap ? 'Höchststufe erreicht' : `${number(commander.experience_to_next)} XP bis Stufe ${number(commander.level+1)}`;
  const bonuses=doctrines?.bonuses||{};
  const doctrineText=doctrines?.enabled?`Aktive FUR-3-Doktrinen (${escapeHtml(doctrines.rules_version)}): Wirtschaft +${number(bonuses.production_percent||0)} % Produktion · Militär +${number(bonuses.combat_damage_percent||0)} % Kampfschaden · Aufklärung +${number(bonuses.intel_lifetime_percent||0)} % Berichtsdauer · Kommando +${number(bonuses.mission_slots||0)} Missionsplätze. Obergrenzen: 20 %, 20 %, 100 %, 5.`:'Doktrinen sind weltweise separat abschaltbar; ohne sie sind nur Wirtschaftspunkte nutzbar.';
  const cost=respec?.cost||{};
  const enough=Array.isArray(resources)&&resources.length===3&&resources[0]>=(cost.wood||0)&&resources[1]>=(cost.stone||0)&&resources[2]>=(cost.ore||0);
  const waiting=Boolean(respec?.available_at&&serverTime<respec.available_at);
  const respecText=respec?.enabled?`<p>Attribut-Reset (${escapeHtml(respec.rules_version)}): Kosten ${number(cost.wood||0)} Holz, ${number(cost.stone||0)} Stein und ${number(cost.ore||0)} Erz. Abklingzeit: ${Math.ceil((respec.cooldown_seconds||0)/86400)} Tage. XP und XP-Buchungen bleiben erhalten.</p><button type="button" data-hero-respec ${!respec.has_allocated_stats||waiting||!enough?'disabled':''}>Commander-Attribute zurücksetzen</button>${waiting?`<small>Verfügbar ab ${new Date(respec.available_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}.</small>`:''}${!enough?'<small>Auf der aktiven Kolonie fehlen Reset-Rohstoffe.</small>':''}`:'<p>Attribut-Reset ist in dieser Welt deaktiviert.</p>';
  return `<article class="panel queue-panel"><h2>Dein Commander · ${escapeHtml(commander.rules_version)}</h2><p>Stufe ${number(commander.level)} / ${number(commander.level_cap)} · ${number(commander.experience)} XP · ${escapeHtml(progress)} · ${number(commander.skill_points)} freie Skillpunkte</p><p>Erfahrung gibt es für abgeschlossene Kampf-, Aufklärungs- und Expeditionsmissionen, nicht durch Kauf. Wirtschaftsattribut: +2 % Rohstoffproduktion je Stufe, höchstens +20 %.</p><p>${doctrineText}</p><div class="goods-grid">${stats}</div><section class="panel" aria-label="Commander-Attributreset">${respecText}</section></article>`;
}

function craftingMarkup(crafting) {
  if (!crafting?.recipes?.length) return '';
  const jobs = (state.jobs||[]).filter(job=>job.kind==='craft');
  const recipes = crafting.recipes.map(recipe => {
    const ingredients = [
      ...Object.entries(recipe.resources).map(([id,amount])=>`${number(amount)} ${id}`),
      ...Object.entries(recipe.goods).map(([id,amount])=>`${number(amount)} ${id}`),
      ...Object.entries(recipe.items).map(([id,amount])=>`${number(amount)} ${id}`),
    ];
    const output = Object.entries(recipe.output).map(([id,amount])=>`${number(amount)} ${id}`).join(', ');
    return `<article class="panel good-card"><h3>${escapeHtml(recipe.name)}</h3><p>${escapeHtml(recipe.description)}</p><p>Eingaben je Durchlauf: ${ingredients.map(escapeHtml).join(' · ')||'keine'}</p><p>Ausgabe: ${escapeHtml(output)} · ${number(recipe.duration_seconds)} Sekunden · HQ Stufe ${number(recipe.min_hq)}</p><form data-craft-recipe="${escapeHtml(recipe.id)}"><label>Durchläufe<input type="number" name="batches" min="1" max="10" value="1" required></label><button type="submit" ${recipe.available?'':'disabled'}>Fertigung starten →</button></form></article>`;
  }).join('');
  const active = jobs.map(job=>`<li>${escapeHtml(job.label)} · noch ${number(Math.max(0,job.due-state.server_time))} s <button type="button" data-action="cancel_job" data-key="${escapeHtml(job.id)}">Abbrechen und vollständig erstatten</button></li>`).join('');
  return `<article class="panel"><h2>Fertigung · ${escapeHtml(crafting.version)}</h2><p>${number(crafting.active_jobs)} von ${number(crafting.max_active_jobs)} Aufträgen belegt. Eingaben werden beim Start reserviert. Abbruch vor Fälligkeit erstattet die vollständigen Eingaben; Depotübermengen wandern in Reservelager.</p><div class="goods-grid">${recipes}</div>${active?`<h3>Laufende Fertigung</h3><ul>${active}</ul>`:''}</article>`;
}

function recyclingMarkup(recycling) {
  if (!recycling?.recipes?.length) return '';
  const recipes = recycling.recipes.map(recipe => {
    const itemOutput = Object.entries(recipe.output_items).map(([id, amount]) => `${number(amount)} ${id}`).join(', ');
    const goodsOutput = Object.entries(recipe.output_goods).map(([id, amount]) => `${number(amount)} ${id}`).join(', ');
    return `<article class="panel good-card"><h3>${escapeHtml(recipe.name)}</h3><p>${escapeHtml(recipe.description)}</p><p>Rückgabe: ${escapeHtml(itemOutput)}${itemOutput && goodsOutput ? ' · ' : ''}${escapeHtml(goodsOutput)}. Überschüsse gehen ins jeweilige Reservelager.</p><form data-item-recycle="${escapeHtml(recipe.item_id)}"><label>Menge<input type="number" name="amount" min="1" max="${number(recycling.max_units_per_command)}" value="1" required></label><button type="submit" ${recipe.available ? '' : 'disabled'}>Gegenstände zerlegen →</button></form></article>`;
  }).join('');
  return `<article class="panel"><h2>Gegenstandsrecycling · ${escapeHtml(recycling.version)}</h2><p>Vorläufiger, verlustbehafteter FUR-3-Regelentwurf. FUR-2 bleibt unverändert.</p><div class="goods-grid">${recipes}</div></article>`;
}

function neutralMarketMarkup(market) {
  if (!market?.goods?.length) return '<article class="panel"><p>Der Warenkatalog ist derzeit nicht verfügbar.</p></article>';
  const options = market.goods.map(good => `<option value="${escapeHtml(good.id)}">${escapeHtml(good.name)} · ${number(good.amount)} verfügbar</option>`).join('');
  const knownAssets = new Set(['wood','stone','ore','alloy','circuits','textiles','rations','medicine','lubricant','ceramics']);
  const slots = market.material_stacks || {used:0,available_types:7};
  const marketGoods = market.goods.map(good => ({...good, claimable_amount:Math.max(0,Math.min(good.reserve_amount||0,market.capacity-good.amount-(good.incoming_amount||0)))}));
  return `<article class="panel"><h2>Neutrale Warenbörse</h2><p>Alle zehn Güter gehören zum Lager der aktiven Kolonie. Materialstapel: ${number(slots.used)} von ${number(slots.available_types)} Warenarten belegt. Je Gut passen ${number(market.capacity)} Einheiten ins Depot. Der Tausch liefert ${number(market.payout_percent)} % des Warenwerts; Zielmengen werden abgerundet. Holz, Stein und Erz haben Wert 1. Energie ist keine Handelsware.</p><form id="goods-trade-form" class="goods-trade-form"><label>Du gibst<select name="goods_source">${options}</select></label><label>Du erhältst<select name="goods_destination">${market.goods.map((good,index)=>`<option value="${escapeHtml(good.id)}" ${index===2?'selected':''}>${escapeHtml(good.name)}</option>`).join('')}</select></label><label>Menge abgeben<input name="amount" type="number" min="${market.minimum_amount}" max="${market.maximum_amount}" step="1" value="100" required></label><p id="goods-trade-quote" role="status" aria-live="polite"></p><button type="submit">Waren tauschen →</button></form><p>Ein Tausch ist nur bei ausreichendem Vorrat und freiem Zieldepot möglich. Materialwaren lassen sich jederzeit zurücktauschen; sie geben derzeit keine passiven Produktions- oder Kampfboni. Rückkehrende Materialwaren können im Warenreserve-Lager liegen.</p><p>Regelstand: ${escapeHtml(market.version)}</p></article><div class="goods-grid" role="list" aria-label="Zehn Marktgüter">${marketGoods.map(good=>`<article class="panel good-card" role="listitem">${knownAssets.has(good.id)?`<img src="/static/assets/goods/${good.id}.svg" width="64" height="64" alt="" loading="lazy">`:''}<h3>${escapeHtml(good.name)}</h3><strong>${number(good.amount)}</strong>${good.reserve_amount?`<p>${number(good.reserve_amount)} im Reserve-Lager <button type="button" data-goods-claim="${escapeHtml(good.id)}" data-goods-amount="${good.claimable_amount}" ${good.claimable_amount<1?'disabled':''}>Ins Depot holen</button></p>`:''}<p>Warenwert ${number(good.value)}</p><p>${escapeHtml(good.description)}</p></article>`).join('')}</div>`;
}
function bindNeutralMarket() {
  const form = $('goods-trade-form');
  if (!form) return;
  const quote = () => {
    const market = state.neutral_market;
    const source = market.goods.find(good => good.id === form.elements.goods_source.value);
    const destination = market.goods.find(good => good.id === form.elements.goods_destination.value);
    const amount = Number(form.elements.amount.value);
    const received = source && destination ? Math.floor(amount * source.value * market.payout_percent / (100 * destination.value)) : 0;
    const valid = source && destination && source.id !== destination.id && Number.isSafeInteger(amount) && amount >= market.minimum_amount && amount <= market.maximum_amount && source.amount >= amount && received > 0 && destination.amount + (destination.incoming_amount||0) + received <= market.capacity;
    $('goods-trade-quote').textContent = valid ? `Vorschau: ${number(received)} ${destination.name}. Der Server prüft den Tausch erneut.` : 'Wähle unterschiedliche Güter, ausreichenden Vorrat und genügend Platz im Zieldepot.';
    form.querySelector('button[type="submit"]').disabled = !valid;
  };
  form.addEventListener('input', quote);
  form.addEventListener('change', quote);
  form.onsubmit = event => {
    event.preventDefault();
    command('goods_trade', {goods_source:form.elements.goods_source.value,goods_destination:form.elements.goods_destination.value,amount:Number(form.elements.amount.value)});
  };
  document.querySelectorAll('[data-goods-claim]').forEach(button => button.addEventListener('click', () => command('goods_reserve_claim', {good_id:button.dataset.goodsClaim, amount:Number(button.dataset.goodsAmount)})));
  document.querySelectorAll('[data-item-claim]').forEach(button => button.addEventListener('click', () => command('item_reserve_claim', {item_id:button.dataset.itemClaim, amount:Number(button.dataset.itemAmount)})));
  quote();
}
function bindCrafting() {
  document.querySelectorAll('[data-craft-recipe]').forEach(form=>form.addEventListener('submit',event=>{
    event.preventDefault();
    command('craft_start',{recipe_id:form.dataset.craftRecipe,batches:Number(form.elements.batches.value)});
  }));
  document.querySelectorAll('[data-item-recycle]').forEach(form=>form.addEventListener('submit',event=>{
    event.preventDefault();
    command('item_recycle',{item_id:form.dataset.itemRecycle,item_amount:Number(form.elements.amount.value)});
  }));
}
function mapCoordinates(x, y) {
  const startX = Math.max(0, Math.min(MAP_MAX_START, Math.trunc(Number(x) || 0)));
  const startY = Math.max(0, Math.min(MAP_MAX_START, Math.trunc(Number(y) || 0)));
  const coordinates = [];
  for (let row = startY; row < Math.min(MAP_SIZE, startY + MAP_VIEW_SIZE); row++)
    for (let column = startX; column < Math.min(MAP_SIZE, startX + MAP_VIEW_SIZE); column++)
      coordinates.push([column, row]);
  return coordinates;
}
function terraMinimapMarkup(snapshot, startX, startY) {
  const terrain = snapshot.terrain_map || {};
  const colors = {plain:'#6d6953',forest:'#3e755e',water:'#286589',mountain:'#8a8580',pass:'#b39b66'};
  const shapes = Object.fromEntries(Object.keys(colors).map(kind=>[kind,[]]));
  for (const [key,kind] of Object.entries(terrain)) {
    const point = /^(\d{1,2}):(\d{1,2})$/.exec(key);
    if (!point || !Object.hasOwn(shapes,kind)) continue;
    const x=Number(point[1]), y=Number(point[2]);
    if (x<MAP_SIZE && y<MAP_SIZE) shapes[kind].push(`M${x} ${y}h1v1h-1z`);
  }
  const known = item => Number.isInteger(item.x) && Number.isInteger(item.y) &&
    item.x>=0 && item.x<MAP_SIZE && item.y>=0 && item.y<MAP_SIZE &&
    Object.hasOwn(terrain,`${item.x}:${item.y}`);
  const mark = (items,color,radius) => items.filter(known).map(item=>
    `<circle cx="${item.x+.5}" cy="${item.y+.5}" r="${radius}" fill="${color}"/>`).join('');
  const outposts = mark(snapshot.world||[],'#e6bd63',.65);
  const players = mark((snapshot.players||[]).filter(item=>item.id!==snapshot.id),'#db6868',.9);
  const colonies = mark(snapshot.colonies||[],'#68d5c0',1.1);
  const label = escapeHtml(window.FURI18n.t('map.minimap'));
  const help = escapeHtml(window.FURI18n.t('map.minimap_help'));
  return `<div class="terra-minimap"><h3>${label}</h3><svg id="terra-minimap" viewBox="0 0 64 64" tabindex="0" role="img" aria-label="${label}" aria-description="${help}"><rect width="64" height="64" fill="#10161d"/>${Object.entries(shapes).map(([kind,parts])=>parts.length?`<path d="${parts.join('')}" fill="${colors[kind]}"/>`:'').join('')}${outposts}${players}${colonies}<rect x="${startX}" y="${startY}" width="${MAP_VIEW_SIZE}" height="${MAP_VIEW_SIZE}" fill="none" stroke="#f4d590" stroke-width=".65" pointer-events="none"/></svg><p>${help}</p></div>`;
}
function minimapPointerSector(clientX, clientY, box) {
  if (!box.width || !box.height) return null;
  const x=Math.floor((clientX-box.left)*MAP_SIZE/box.width);
  const y=Math.floor((clientY-box.top)*MAP_SIZE/box.height);
  return x>=0 && x<MAP_SIZE && y>=0 && y<MAP_SIZE ? [x,y] : null;
}
function knownTerrainRoute(terrainMap, terrainCatalog, start, finish) {
  const pointKey = ([x, y]) => `${x}:${y}`;
  const parsePoint = key => {
    const match = /^(\d{1,2}):(\d{1,2})$/.exec(key);
    if (!match) return null;
    const point = [Number(match[1]), Number(match[2])];
    return point.every(value => value >= 0 && value < MAP_SIZE) ? point : null;
  };
  const costs = new Map();
  for (const [key, terrain] of Object.entries(terrainMap || {})) {
    const point = parsePoint(key), rule = terrainCatalog?.[terrain];
    if (point && rule && Number.isFinite(rule.movement_cost) && rule.movement_cost > 0)
      costs.set(key, rule.movement_cost);
  }
  const startKey = pointKey(start), finishKey = pointKey(finish);
  if (!costs.has(startKey) || !costs.has(finishKey)) return null;
  if (startKey === finishKey) return [start];

  const distances = new Map([[startKey, 0]]), previous = new Map(), heap = [];
  const before = (a, b) => a.cost - b.cost || a.x - b.x || a.y - b.y;
  const push = node => {
    heap.push(node);
    let index = heap.length - 1;
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (before(heap[parent], node) <= 0) break;
      heap[index] = heap[parent];
      index = parent;
    }
    heap[index] = node;
  };
  const pop = () => {
    const first = heap[0], last = heap.pop();
    if (heap.length && last) {
      let index = 0;
      while (true) {
        const left = index * 2 + 1, right = left + 1;
        if (left >= heap.length) break;
        const child = right < heap.length && before(heap[right], heap[left]) < 0 ? right : left;
        if (before(last, heap[child]) <= 0) break;
        heap[index] = heap[child];
        index = child;
      }
      heap[index] = last;
    }
    return first;
  };
  push({x:start[0], y:start[1], cost:0});
  while (heap.length) {
    const current = pop(), currentKey = `${current.x}:${current.y}`;
    if (current.cost !== distances.get(currentKey)) continue;
    if (currentKey === finishKey) break;
    const currentTerrainCost = costs.get(currentKey);
    for (const [x, y] of [[current.x-1,current.y],[current.x+1,current.y],[current.x,current.y-1],[current.x,current.y+1]]) {
      const neighborKey = `${x}:${y}`, neighborTerrainCost = costs.get(neighborKey);
      if (neighborTerrainCost === undefined) continue;
      const nextCost = current.cost + Math.floor((currentTerrainCost + neighborTerrainCost) / 2);
      if (nextCost >= (distances.get(neighborKey) ?? Infinity)) continue;
      distances.set(neighborKey, nextCost);
      previous.set(neighborKey, currentKey);
      push({x,y,cost:nextCost});
    }
  }
  if (!distances.has(finishKey)) return null;
  const path = [];
  for (let key = finishKey; key; key = previous.get(key)) {
    const point = parsePoint(key);
    if (!point) return null;
    path.push(point);
    if (key === startKey) break;
  }
  if (pointKey(path[path.length - 1]) !== startKey) return null;
  return path.reverse();
}
function routeCoordinates(route) {
  return route.map(([x,y])=>`${x}:${y}`).join(' → ');
}
function isMapBookmarked(bookmarks, targetId) {
  return Boolean(targetId && bookmarks.has(targetId));
}
function activeWorldLabel(world) {
  const id = Number.isInteger(world?.id) ? world.id : 1;
  return `${world?.name || 'Genesis'} · WELT ${String(id).padStart(2, '0')}`;
}
function outpostStockSummary(outpost) {
  if (outpost.owner || !Array.isArray(outpost.stock) || outpost.stock.length !== 3) return '';
  return `Vorräte ${outpost.stock.map((amount,index)=>`${resourceIcon(index,'stock-icon')} ${number(amount)}`).join(' · ')}`;
}
function outpostConversionMarkup(outpost, state) {
  if (outpost.owner !== state.id || outpost.tier >= 8) return '';
  const cost = [6000, 4500, 3000];
  const distant = (state.colonies || []).every(colony => Math.hypot(colony.x-outpost.x,colony.y-outpost.y) >= 6);
  const enabled = state.buildings.hq >= 3 && state.colony_count < state.colony_slot_limit
    && cost.every((value,index) => state.resources[index] >= value) && distant
    && !state.terra_sector_rules?.[`${outpost.x}:${outpost.y}`];
  return `<button type="button" class="compact outpost-convert" data-convert="${escapeHtml(outpost.id)}" data-convert-name="${escapeHtml(outpost.name)}" ${enabled?'':'disabled'}>Zu Kolonie ausbauen · 6.000 / 4.500 / 3.000</button>`;
}
function regionControlMarkup(regions, playerId, productionBonus) {
  const cards=(regions||[]).map(region=>{
    if(region.surveyed===false) return `<li class="region-card unexplored"><h4>${escapeHtml(region.id)}</h4><p>Sektoren ${region.x_min}–${region.x_max} : ${region.y_min}–${region.y_max}</p><p>Gebiet noch nicht vollständig erkundet</p></li>`;
    const controlled=Boolean(region.owner_id), mine=region.owner_id===playerId;
    const status=!region.outpost_count?'Keine Außenposten in diesem Gebiet':controlled
      ?`${mine?'Deine Kontrolle':'Kontrolliert von '+escapeHtml(region.owner_name||'Kommandant')} · ${region.leader_outposts}/${region.required_posts} Ziele`
      :region.leader_tied?`Gleichstand · ${region.leader_outposts}/${region.required_posts} Ziele`
      :region.leader_name?`Führend: ${escapeHtml(region.leader_name)} · ${region.leader_outposts}/${region.required_posts} Ziele`
      :`Noch keine kontrollierten Ziele · 0/${region.required_posts}`;
    const allianceStatus=region.alliance_owner_id
      ?`Allianzgebiet: ${escapeHtml(region.alliance_owner_name||'Allianz')}`
      :region.alliance_leader_tied?'Allianzen im Gleichstand':'';
    return `<li class="region-card${mine?' mine':''}"><h4>${escapeHtml(region.id)}</h4><p>Sektoren ${region.x_min}–${region.x_max} : ${region.y_min}–${region.y_max}</p><p>${status}</p>${allianceStatus?`<p>${allianceStatus}</p>`:''}${controlled?`<small>+${region.production_bonus_percent}% Produktion für den Besitzer</small>`:''}</li>`;
  }).join('');
  return `<section class="panel queue-panel region-summary" aria-labelledby="region-summary-title"><h3 id="region-summary-title">Regionale Kontrolle</h3><p>Die Welt ist in 16 Gebiete aus je 16 × 16 Sektoren geteilt. Kontrolle verlangt mindestens zwei und mehr als die Hälfte der Außenposten. Jedes kontrollierte Gebiet gibt seinem Besitzer +2 Prozentpunkte Produktion.</p><p class="eyebrow">DEIN REGIONSBONUS · +${productionBonus||0}%</p><ul class="region-grid">${cards}</ul></section>`;
}
function npcFactionMarkup(factions) {
  const rows=(factions||[]).map(faction=>`<li><strong>${escapeHtml(faction.name)}</strong><span>${number(faction.outposts)} neutrale Außenposten · Bedrohungsstufe ${number(faction.threat_level)} · Grenzdruck ${number(faction.pressure)} Punkte</span></li>`).join('');
  return `<section class="panel queue-panel npc-frontiers" aria-labelledby="npc-frontiers-title"><h3 id="npc-frontiers-title">Fraktionen der Grenzregion</h3><p>Drei eigenständige NPC-Fraktionen verstärken neutrale Außenposten im Fünf-Minuten-Takt. Höhere Postenstufen erzeugen schneller Grenzdruck. Bei 100 Druckpunkten liefern sie Vorräte bis zur Außenpostengrenze nach. Die Bedrohungsstufe zeigt den gesammelten Druck pro Fraktion; automatische Angriffe auf Spielerbasen finden nicht statt.</p><ul>${rows||'<li>In dieser Welt gibt es derzeit keine neutralen Fraktionsposten.</li>'}</ul></section>`;
}
function npcCampMarkup(camps, ruleset) {
  if (!['FUR-3-NPC-CAMPS-1','FUR-3-NPC-CAMPS-2','FUR-3-NPC-CAMPS-3'].includes(ruleset) || !Array.isArray(camps) || camps.length === 0) return '';
  const hasMovement=['FUR-3-NPC-CAMPS-2','FUR-3-NPC-CAMPS-3'].includes(ruleset);
  const hasAttacks=ruleset==='FUR-3-NPC-CAMPS-3';
  const labels={resupply:'Versorgung',scout:'Aufklärung',reinforce:'Verstärkung',fortify:'Befestigung',maneuver:'Manöver'};
  const cards=camps.map(camp=>`<li><h4>${escapeHtml(camp.name)}</h4><p>Doktrin: ${escapeHtml(camp.doctrine)} · Erlaubte Aktionen: ${camp.actions.map(action=>escapeHtml(labels[action]||action)).join(', ')}</p><p>Vorräte: ${camp.resources.map(number).join(' / ')} · Truppen: ${Object.entries(camp.units).map(([unit,count])=>`${escapeHtml(unit)} ${number(count)}`).join(', ')}</p><p>Befestigung Stufe ${number(camp.fortification_level)} · Aufklärungsaufträge ${number(camp.scout_actions)} · Manöver ${number(camp.maneuver_actions)}</p>${hasMovement?`<p>Standort ${camp.x===null||camp.y===null?'wird initialisiert':`${number(camp.x)}:${number(camp.y)}`} · bekannte Außenposten ${number(camp.scouted_outposts)}</p>`:''}<p>Bewegungen: ${number(camp.movement_quota)} · Bereitstellungen: ${number(camp.deployment_quota)}</p></li>`).join('');
  const movementText=hasMovement?' Aufklärung erfasst neutrale und besetzte Außenposten im Manhattan-Radius 3 mit sieben Tagen Gültigkeit nur für die NPC-Planung. Ein Manöver bewegt das Lager einen Schritt auf dem kürzesten begehbaren Vier-Wege-Pfad zum nächsten bekannten neutralen Außenposten. Lager bleiben außerhalb des Sechs-Sektoren-Abstands zu Spielerbasen und betreten keine Kolonie-, Außenposten-, Ruinen- oder Wassersektoren.':' Aufklärung und Manöver protokollieren nur den Auftrag; Kartenbewegung ist in dieser Regelversion nicht aktiv.';
  return `<section class="panel queue-panel npc-camps" aria-labelledby="npc-camps-title"><h3 id="npc-camps-title">NPC-Lager · FUR-3</h3><p>Fünf eigenständige Lager mit getrennten Vorräten und Truppen. Regeln: ${escapeHtml(ruleset)} · Entwurfsbalance. Versorgung kostet 100/50/50 und füllt Vorräte auf; Verstärkung kostet 100/80/120 und bildet 2 Ranger sowie 1 Wächter aus; Befestigung kostet 80/160/100 je Stufe bis 10. Aufklärung und Manöver kosten Vorräte und verbrauchen je eine von 4 täglichen Bewegungen;${movementText} Verstärkung verbraucht eines von 8 täglichen Bereitstellungskontingenten. Quoten werden nach UTC-Kalendertag erneuert. Je aktivem Lager wird täglich höchstens eine bezahlbare Profilaktion automatisch ausgeführt. ${hasAttacks?'FUR-3-Angriffe warnen fünf Minuten vorher, greifen höchstens einmal täglich denselben Spieler an und können nur Außenposten-Garnisonen sowie höchstens 10 % (maximal 200 je Rohstoff) der Vorräte betreffen; Außenposten werden nicht erobert.':'Angriffe, Kriege, Veränderungen an Spielerbesitz und Spielerbeute sind nicht aktiviert.'}</p><ul>${cards}</ul></section>`;
}
function npcAttackPlanMarkup(plans, ruleset) {
  if (!['FUR-3-NPC-CAMPS-2','FUR-3-NPC-CAMPS-3'].includes(ruleset) || !Array.isArray(plans) || plans.length === 0) return '';
  const attacks=ruleset==='FUR-3-NPC-CAMPS-3';
  const rows=plans.map(plan=>{const status=plan.attack_status;const detail=attacks?(status==='resolved'?`Kampf beendet: ${escapeHtml(plan.attack_outcome||'Ergebnis verfügbar')}.`:status==='cancelled'?'Der Angriff wurde ohne Kampf abgebrochen.':`Angriff angekündigt; Ankunft ${new Date(Number(plan.attack_arrival)*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}.`):'Unverbindlicher NPC-Plan; kein Angriff wurde gestartet und es wurden keine Truppen oder Ressourcen verändert.';return `<li><strong>${escapeHtml(plan.target_name)}</strong><span>Sektor ${number(plan.target_x)}:${number(plan.target_y)} · Plan erstellt ${new Date(Number(plan.created)*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</span><small>${detail}</small></li>`;}).join('');
  return `<section class="panel queue-panel npc-attack-plans" aria-labelledby="npc-attack-plans-title"><h3 id="npc-attack-plans-title">${attacks?'NPC-Angriffsberichte':'NPC-Aufklärungswarnungen'}</h3><p>${attacks?'FUR-3 kündigt Angriffe mindestens fünf Minuten vorher an. Pro Spieler gibt es höchstens einen Angriff innerhalb von 24 Stunden.':'FUR-3 plant höchstens ein Ziel je Welt und Fünf-Minuten-Takt. Ein Plan ist nur eine private Warnung, kein gestarteter Angriff.'}</p><ul>${rows}</ul></section>`;
}
let orbitChart, orbitChartRequest;
let worldEventFeed;
let worldEventCategory = '';
async function loadWorldEventFeed(category = worldEventCategory) {
  if (!state?.id || !state?.active_world?.id) return;
  const user = state.id, worldId = state.active_world.id;
  const selectedCategory = category || '';
  worldEventCategory = selectedCategory;
  if (worldEventFeed?.user === user && worldEventFeed.world_id === worldId) render();
  try {
    const result = await api(`game-events?world_id=${worldId}${selectedCategory?`&category=${encodeURIComponent(selectedCategory)}`:''}`);
    if (state?.id !== user || state.active_world.id !== worldId || result.world_id !== worldId || worldEventCategory !== selectedCategory) return;
    worldEventFeed = {...result,user,category:selectedCategory};
    render();
  } catch (error) {
    if (state?.id === user && state.active_world.id === worldId && worldEventCategory === selectedCategory) notify(error.message);
  }
}
let pushUiState = {user:'',enabled:false,subscribed:false,count:0,status:''};
function encodeVapidKey(value) {
  const padded=value+'='.repeat((4-value.length%4)%4);
  const raw=atob(padded.replace(/-/g,'+').replace(/_/g,'/'));
  return Uint8Array.from(raw,character=>character.charCodeAt(0));
}
async function loadPushState(user) {
  if(tab!=='colonies') {if(pushUiState.user!==user)pushUiState={user,enabled:false,subscribed:false,count:0,status:'',loaded:false};return;}
  if(pushUiState.user===user&&pushUiState.loaded)return;
  pushUiState={user,enabled:false,subscribed:false,count:0,status:''};
  pushUiState.loaded=true;
  if(tab!=='colonies')return;
  if(!('serviceWorker' in navigator)||!('PushManager' in window)||!('Notification' in window))return;
  try {
    const config=await api('push/config');
    if(state?.id!==user)return;
    if(!config.enabled){pushUiState.enabled=false;return;}
    const registration=await navigator.serviceWorker.register('/service-worker.js',{scope:'/'});
    const subscription=await registration.pushManager.getSubscription();
    const listing=await api('push/subscriptions');
    if(state?.id!==user)return;
    pushUiState={user,enabled:true,subscribed:Boolean(subscription),count:listing.subscriptions.length,status:''};
  } catch(error) { pushUiState={user,enabled:false,subscribed:false,count:0,status:error.message}; }
}
async function enableBrowserPush() {
  const user=state?.id;
  if(!user)return;
  const button=$('push-enable');if(button)button.disabled=true;
  try {
    const permission=await Notification.requestPermission();
    if(permission!=='granted')throw new Error('Die Browserfreigabe wurde nicht erteilt.');
    const config=await api('push/config');
    if(!config.enabled||!config.public_key)throw new Error('Push ist auf diesem Server nicht eingerichtet.');
    const registration=await navigator.serviceWorker.register('/service-worker.js',{scope:'/'});
    const subscription=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:encodeVapidKey(config.public_key)});
    const serialized=subscription.toJSON();
    await api('push/subscriptions',{endpoint:serialized.endpoint,keys:serialized.keys},'POST');
    await loadPushState(user);
    if(state?.id===user)render();
  }catch(error){if(state?.id===user){pushUiState.status=error.message;if($('push-status'))$('push-status').textContent=error.message;const current=$('push-enable');if(current)current.disabled=false;}}
}
async function disableBrowserPush() {
  const user=state?.id;
  try {
    const registration=await navigator.serviceWorker.getRegistration('/');
    const subscription=await registration?.pushManager.getSubscription();
    if(subscription){await api(`push/subscriptions?endpoint=${encodeURIComponent(subscription.endpoint)}`,undefined,'DELETE');await subscription.unsubscribe();}
    await loadPushState(user);
    if(state?.id===user)render();
  }catch(error){if(state?.id===user){pushUiState.status=error.message;if($('push-status'))$('push-status').textContent=error.message;}}
}
function worldEventFeedMarkup() {
  const feed = worldEventFeed?.user === state.id && worldEventFeed.world_id === state.active_world.id
    ? worldEventFeed.events : null;
  const prefs = worldEventFeed?.user === state.id && worldEventFeed.world_id === state.active_world.id
    ? worldEventFeed.preferences : {economy:false,research:false,military:false,social:false,system:false};
  const failures = worldEventFeed?.user === state.id && worldEventFeed.world_id === state.active_world.id
    ? worldEventFeed.delivery_failures : [];
  const pushStatus=pushUiState.user===state.id?pushUiState:{enabled:false,subscribed:false,count:0,status:''};
  const hasMore = worldEventFeed?.user === state.id && worldEventFeed.world_id === state.active_world.id
    ? worldEventFeed.has_more : false;
  const cursor = worldEventFeed?.user === state.id && worldEventFeed.world_id === state.active_world.id
    ? worldEventFeed.cursor : null;
  const categories = [['economy','Wirtschaft'],['research','Forschung'],['military','Militär'],['social','Soziales'],['system','System']];
  const selectedCategory=worldEventFeed?.user===state.id&&worldEventFeed.world_id===state.active_world.id?(worldEventFeed.category||''):worldEventCategory;
  return `<section class="panel queue-panel"><h3>Privates Weltprotokoll</h3>
    <p>Persönliche Spielereignisse dieser Welt. Kategorien lassen sich einzeln stummschalten.</p>
    <button type="button" id="refresh-world-event-feed">Protokoll laden</button>
    <label for="world-event-category">Ereignisse filtern</label><select id="world-event-category"><option value="">Alle Kategorien</option>${categories.map(([key,label])=>`<option value="${key}" ${selectedCategory===key?'selected':''}>${label}</option>`).join('')}</select>
    <fieldset class="world-event-preferences"><legend>Benachrichtigungskategorien</legend>${categories.map(([key,label])=>`<label><input type="checkbox" data-notification-category="${key}" ${prefs[key]?'checked':''}> ${label} stumm</label>`).join('')}</fieldset>
    <section aria-labelledby="push-heading"><h4 id="push-heading">Browser-Mitteilungen</h4><p>Optional. Vorschauen enthalten keine Spiel-, Nachrichten- oder Kontodetails.</p>
      ${pushStatus.enabled ? (pushStatus.subscribed ? `<p role="status">Browser-Mitteilungen aktiv · ${number(pushStatus.count)} Gerät(e)</p><button type="button" id="push-disable">Browser-Mitteilungen ausschalten</button>` : `<button type="button" id="push-enable">Browser-Mitteilungen aktivieren</button>`) : '<p>Dieser Server hat Browser-Mitteilungen nicht konfiguriert.</p>'}
      <p role="status" id="push-status">${escapeHtml(pushStatus.status||'')}</p></section>
    ${failures.length?`<div role="status"><h4>Nicht zugestellte Ereignisse</h4><ul>${failures.map(item=>`<li>${escapeHtml(item.kind.replaceAll('_',' '))} · ${number(item.attempts)} Versuche · ${new Date(item.failed_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</li>`).join('')}</ul></div>`:''}
    <p role="status">${feed ? `${number(feed.length)} Einträge geladen.` : ''}</p>
    ${feed?.length ? `<ol>${feed.map(event => `<li><strong>${escapeHtml(categories.find(([key])=>key===event.category)?.[1]||'Ereignis')}</strong> · ${escapeHtml(event.kind === 'gateway_cargo_arrived' ? 'Gateway-Fracht angekommen' : event.kind.replaceAll('_',' '))} · ${new Date(event.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</li>`).join('')}</ol>` : ''}
    ${hasMore&&cursor?`<button type="button" data-world-events-more="${cursor}">Ältere Ereignisse laden</button><p role="status" data-world-events-more-status aria-live="polite"></p>`:''}
  </section>`;
}
function orbitTemplateMarkup(kind, access) {
  const templates = (access.templates || []).filter(template => template.kind === kind);
  return `<label>Vorlage <select name="orbit_template">
    <option value="">Vorlage wählen</option>
    ${templates.map(template => `<option value="${escapeHtml(template.id)}">${escapeHtml(template.name)}</option>`).join('')}
  </select></label>
  <button type="button" data-orbit-template-apply="${kind}">Vorlage laden</button>
  <button type="button" data-orbit-template-delete>Vorlage löschen</button>
  <label>Vorlagenname <input name="orbit_template_name" minlength="2" maxlength="32"></label>
  <button type="button" data-orbit-template-save="${kind}">Als Vorlage speichern</button>`;
}
function orbitShipyardMarkup(colony, access) {
  const id = escapeHtml(colony.mission_id);
  if (!colony.shipbuilding_ready_at) {
    return `<p>Schiffbauforschung benötigt eine Ätherraffinerie und ${number(access.shipbuilding_ore)} Orbit-Erz.</p>
      <button type="button" data-orbit-research="${id}" ${colony.refinery < 1 || colony.ore < access.shipbuilding_ore ? 'disabled' : ''}>Schiffbau erforschen</button>`;
  }
  if (colony.shipbuilding_ready_at > state.server_time) {
    return '<p>Schiffbauforschung läuft.</p>';
  }
  const ships = Object.entries(access.ship_catalog);
  return `<h5>Werft</h5>
    <p>Munition: ${number(colony.lances)} Sternlanzen · ${number(colony.screens)} Schleier-Abfänger.</p>
    ${Object.entries({lances:'Sternlanze',screens:'Schleier-Abfänger'}).map(([kind,label]) => {
      const [ore,ether] = access.ammunition_costs[kind];
      return `<button type="button" data-orbit-ammunition="${kind}" data-orbit-colony="${id}" ${colony[kind] >= access.ammunition_cap || colony.ore < ore || colony.ether < ether ? 'disabled' : ''}>${label} fertigen · ${number(ore)} Erz / ${number(ether)} Äther</button>`;
    }).join(' ')}
    <p>${colony.defense_ready_at
      ? (colony.defense_ready_at <= state.server_time ? 'Verteidigungsplattform aktiv.' : 'Verteidigungsplattform im Bau.')
      : `<button type="button" data-orbit-defense="${id}" ${colony.ore < access.defense_cost.ore || colony.ether < access.defense_cost.ether ? 'disabled' : ''}>Verteidigungsplattform bauen · ${number(access.defense_cost.ore)} Erz / ${number(access.defense_cost.ether)} Äther</button>`}</p>
    <ul class="orbit-ship-roster">${ships.filter(([key]) => colony.ships[key]).map(([key, rule]) => `<li>${assetImage(`orbit/ships/${key}`,rule.role,'roster-ship-art')}<span>${escapeHtml(rule.role)} · ${number(colony.ships[key])} verfügbar</span></li>`).join('')}</ul>
    ${colony.wrecks.map(wreck => {
      const rule = access.ship_catalog[wreck.ship];
      if (!rule) return '';
      return `<p>${number(wreck.amount)} × ${escapeHtml(wreck.ship)} reparierbar
        <button type="button" data-orbit-repair="${escapeHtml(wreck.ship)}" data-orbit-colony="${id}" ${colony.ship_order ? 'disabled' : ''}>Ein Wrack reparieren · ${number(Math.ceil(rule.ore_cost/2))} Erz / ${number(Math.ceil(rule.ether_cost/2))} Äther</button></p>`;
    }).join('')}
    ${colony.ship_order ? `<p>Auftrag läuft: ${number(colony.ship_order.amount)} × ${escapeHtml(colony.ship_order.ship)}</p>` : `
      <form id="orbit-shipyard-${id}" data-orbit-shipyard="${id}">
        <label>Schiffsklasse <select name="ship">${ships.map(([key, rule]) => `<option value="${escapeHtml(key)}">${escapeHtml(key)} · ${number(rule.ore_cost)} Erz / ${number(rule.ether_cost)} Äther</option>`).join('')}</select></label>
        <label>Anzahl <input name="count" type="number" value="1" min="1" max="100" required></label>
        <button>Schiffsbau beauftragen</button>
        ${orbitTemplateMarkup('shipyard', access)}
      </form>`}
  `;
}
function orbitStationMarkup(colony) {
  const id = escapeHtml(colony.mission_id);
  const station = colony.station;
  const level = station.level || 0;
  const oreCost = 600 * (level + 1);
  const etherCost = 120 * (level + 1);
  const researchRunning = colony.shipbuilding_ready_at > state.server_time;
  const researchReady = colony.shipbuilding_ready_at && !researchRunning;
  const canBuild = researchReady && colony.ore >= oreCost && colony.ether >= etherCost;
  const buildBlockReason = !colony.shipbuilding_ready_at
    ? 'Schiffbauforschung erforderlich.'
    : researchRunning
      ? 'Schiffbauforschung läuft.'
      : colony.ore < oreCost || colony.ether < etherCost
        ? 'Nicht genügend Orbit-Erz oder Äther für den Ausbau.'
        : '';
  const transfer = (action, label, ships) => {
    const available = Object.entries(ships).filter(([,count]) => count > 0);
    return available.length ? `<form id="${action}-${id}" data-orbit-station-transfer="${action}" data-orbit-colony="${id}">
      <label>Schiffsklasse <select name="ship">${available.map(([ship,count]) => `<option value="${escapeHtml(ship)}">${escapeHtml(ship)} · ${number(count)}</option>`).join('')}</select></label>
      <label>Anzahl <input name="count" type="number" value="1" min="1" max="100" required></label>
      <button>${label}</button>
    </form>` : '';
  };
  return `<h5>Raumstation</h5>
    ${level ? `<p>Stufe ${number(level)} · ${station.active ? 'Einsatzbereit' : 'Wartung fällig'} · Garnison ${number(Object.values(station.ships).reduce((a,b)=>a+b,0))}/${number(level*100)}</p>` : ''}
    ${station.ready_at ? '<p>Stationsbau läuft.</p>' : level < 3 ? `<button type="button" data-orbit-station="orbit_station_build" data-orbit-colony="${id}" ${canBuild ? '' : 'disabled'}>Station ausbauen · ${number(oreCost)} Erz / ${number(etherCost)} Äther</button>${buildBlockReason ? `<small>${buildBlockReason}</small>` : ''}` : ''}
    ${level ? `<button type="button" data-orbit-station="orbit_station_upkeep" data-orbit-colony="${id}">24 Stunden Wartung · ${number(24*level)} Äther</button>
      ${station.active ? transfer('orbit_station_deploy','Zur Garnison versetzen',colony.ships) : ''}
      ${transfer('orbit_station_withdraw','Zur Kolonie zurückholen',station.ships)}` : ''}
  `;
}
function orbitJumpgateMarkup(colony, access) {
  const id = escapeHtml(colony.mission_id);
  const gate = colony.jumpgate;
  if (!gate) {
    if ((colony.station.level || 0) < 2) return '';
    return `<button type="button" data-orbit-gate="${id}" ${state.buildings.hq < access.jumpgate_hq || colony.ore < access.jumpgate_ore ? 'disabled' : ''}>Sprungtor bauen · ${number(access.jumpgate_ore)} Erz · Terra-HQ ${number(access.jumpgate_hq)}</button>`;
  }
  const ready = candidate => candidate.station.active && candidate.jumpgate
    && Math.max(candidate.jumpgate.ready_at,candidate.jumpgate.cooldown_until) <= state.server_time;
  const targets = access.colonies.filter(candidate => candidate.mission_id !== colony.mission_id && ready(candidate));
  const ships = Object.entries(colony.ships).filter(([,count]) => count > 0);
  return `<p>Sprungtor · ${ready(colony) ? 'Bereit' : 'Im Bau, in Abklingzeit oder Station inaktiv'}</p>
    ${ready(colony) && targets.length && ships.length ? `<form id="orbit-jump-${id}" data-orbit-jump="${id}">
      <label>Zieltor <select name="target">${targets.map(target => `<option value="${escapeHtml(target.mission_id)}">${number(target.galaxy)}:${number(target.system)}:${number(target.slot)}</option>`).join('')}</select></label>
      <label>Schiffsklasse <select name="ship">${ships.map(([ship,count]) => `<option value="${escapeHtml(ship)}">${escapeHtml(ship)} · ${number(count)}</option>`).join('')}</select></label>
      <label>Anzahl <input name="count" type="number" value="1" min="1" max="100" required></label>
      <button>Sprung auslösen</button>
    </form>` : ''}`;
}
function orbitGatewayCargoMarkup(colony, access) {
  const id = escapeHtml(colony.mission_id);
  const busyRoute = colony.gateway_cargo.some(cargo => cargo.terra_colony === state.colony_id);
  return `<h5>Terra-Orbit-Fracht</h5>
    <p>Route zwischen dieser Orbit-Kolonie und deiner aktiven Terra-Kolonie. Je Start fallen ${number(access.gateway_cargo_fee)} Erz Gebühr am Abflugort an.</p>
    ${colony.gateway_cargo.map(cargo => `<p>${cargo.to_orbit ? 'Terra → Orbit' : 'Orbit → Terra'} · ${number(cargo.ore)} Erz · Ankunft ${new Date(cargo.due*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</p>`).join('')}
    ${busyRoute ? '' : `<form id="orbit-gateway-cargo-${id}" data-orbit-gateway-cargo="${id}">
      <label>Erzmenge <input name="ore" type="number" min="1" max="${number(access.gateway_cargo_limit)}" value="100" required></label>
      <button type="submit" data-direction="import">Von Terra zum Orbit</button>
      <button type="submit" data-direction="export">Vom Orbit zu Terra</button>
    </form>`}`;
}
function orbitFreightMarkup(colony, colonies) {
  const id = escapeHtml(colony.mission_id);
  const targets = colonies.filter(target => target.mission_id !== colony.mission_id);
  return `<h5>Fracht</h5>
    <p>Reserve: ${number(colony.ore_reserve)} Erz · ${number(colony.ether_reserve)} Äther</p>
    ${colony.ore_reserve || colony.ether_reserve ? `<button type="button" data-orbit-collect="${id}">Fracht ins Lager übernehmen</button>` : ''}
    ${colony.transports.map(trip => `<p>${number(trip.ships)} ${trip.salvage_report ? 'Bergungsschiffe' : 'Frachter'} · ${trip.recalled ? 'Zurückgerufen' : trip.returning ? 'Rückflug' : 'Hinflug'} · ${new Date(trip.due * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}
      ${trip.returning ? '' : `<button type="button" data-orbit-recall="${escapeHtml(trip.id)}" data-orbit-colony="${id}">Flug zurückrufen</button>`}</p>`).join('')}
    ${targets.length && colony.ships.freighter ? `<form id="orbit-freight-${id}" data-orbit-freight="${id}">
      <label>Ziel <select name="target">${targets.map(target => `<option value="${escapeHtml(target.mission_id)}">${number(target.galaxy)}:${number(target.system)}:${number(target.slot)}</option>`).join('')}</select></label>
      <label>Frachter <input type="number" name="count" min="1" max="${Math.min(100,colony.ships.freighter)}" value="1" required></label>
      <label>Erz <input type="number" name="ore" min="0" max="${number(colony.ore)}" value="0" required></label>
      <label>Äther <input type="number" name="ether" min="0" max="${number(colony.ether)}" value="0" required></label>
      <button>Fracht senden</button>
      <small>Der Treibstoff für beide Strecken wird beim Start abgebucht. Fracht landet in der Zielreserve.</small>
    </form>` : ''}
  `;
}
function orbitAttackMarkup(chart, access) {
  const targets = chart?.slots.filter(slot => slot.occupied && slot.expires_at > state.server_time) || [];
  const fleets = (access.colonies || []).flatMap(colony => Object.entries(colony.ships)
    .filter(([, count]) => count > 0).map(([ship, count]) => ({colony, ship, count})));
  if (!targets.length || !fleets.length || !state.world_pvp_enabled) return '';
  return `<form id="orbit-attack-form">
    <h4>Orbit-Angriff</h4>
    <label>Zielsektor <select name="slot">${targets.map(target => `<option value="${number(target.slot)}">${number(target.slot)}${target.moon ? ' · Mond beobachtet' : ''}</option>`).join('')}</select></label>
    <label>Startkolonie und Schiffsklasse <select name="fleet">${fleets.map(({colony,ship,count}) => `<option data-origin="${escapeHtml(colony.mission_id)}" value="${escapeHtml(colony.mission_id + ':' + ship)}" data-ship="${escapeHtml(ship)}">${number(colony.galaxy)}:${number(colony.system)}:${number(colony.slot)} · ${escapeHtml(ship)} (${number(count)})</option>`).join('')}</select></label>
    <label>Schiffe <input type="number" name="count" min="1" max="100" value="1" required></label>
    <button>Angriff entsenden</button>
    <label>Rückzug ab Verlust in Prozent <input type="number" name="retreat" min="10" max="100" placeholder="Optional"></label>
    <label>Sternlanzen für die Eröffnungssalve <input type="number" name="lances" min="0" max="${number(access.ammunition_cap)}" value="0"></label>
    <small>Sternlanzen reichen 48 Plätze weit innerhalb derselben Galaxie. Schleier-Abfänger neutralisieren sie einzeln.</small>
    ${orbitTemplateMarkup('fleet', access)}
    ${state.membership ? '<button type="submit" data-allied-attack>Allianzverband eröffnen</button>' : ''}
    ${targets.some(target => target.moon) && fleets.some(fleet => fleet.ship === 'siege_ship' && fleet.count >= 3)
      ? '<button type="submit" data-moon-siege>Mond belagern</button><small>Benötigt Mondaufklärung und mindestens drei Belagerungsschiffe. Bei Erfolg wird ein Schiff verbraucht.</small>' : ''}
  </form>`;
}
function orbitAllianceMarkup(access) {
  const fleets = (access.colonies || []).flatMap(colony => Object.entries(colony.ships)
    .filter(([,count]) => count > 0).map(([ship,count]) => ({colony,ship,count})));
  if (!access.alliance_attacks?.length || !fleets.length) return '';
  return `<form id="orbit-alliance-form">
    <h4>Orbit-Allianzverband</h4>
    <label>Verband <select name="attack">${access.alliance_attacks.map(attack => `<option value="${escapeHtml(attack.id)}">${number(attack.galaxy)}:${number(attack.system)}:${number(attack.slot)} · ${new Date(attack.due*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</option>`).join('')}</select></label>
    <label>Startkolonie und Schiffsklasse <select name="fleet">${fleets.map(({colony,ship,count}) => `<option data-origin="${escapeHtml(colony.mission_id)}" value="${escapeHtml(colony.mission_id+':'+ship)}" data-ship="${escapeHtml(ship)}">${number(colony.galaxy)}:${number(colony.system)}:${number(colony.slot)} · ${escapeHtml(ship)} (${number(count)})</option>`).join('')}</select></label>
    <label>Schiffe <input type="number" name="count" min="1" max="100" value="1" required></label>
    <button>Verband beitreten</button>
  </form>`;
}
const orbitEventNames = {solar:'Sonnensturm',anomaly:'Orbit-Anomalie',boss:'Wächterbegegnung'};
function orbitSpecialEventsMarkup(access) {
  const events = access.special_events || [];
  return `<h4>Orbit-Ereignisse</h4>
    ${events.length ? events.map(event => `<p>${escapeHtml(orbitEventNames[event.kind])} · endet ${new Date(event.ends*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</p>`).join('') : '<p>Derzeit läuft kein Spezialereignis.</p>'}
    ${state.profile.role === 'admin' && !events.length ? `<form id="orbit-event-form">
      <label>Ereignis <select name="kind">${Object.entries(orbitEventNames).map(([key,label]) => `<option value="${key}">${escapeHtml(label)}</option>`).join('')}</select></label>
      <button>Orbit-Ereignis starten</button>
    </form>` : ''}`;
}
function orbitExpeditionMarkup(chart, access) {
  const origins = (access.colonies || []).filter(colony => colony.ships.courier > 0);
  if (!chart || !origins.length) return '';
  return `<form id="orbit-expedition-form">
    <h4>Orbit-Expedition</h4><p>Kurierschiffe untersuchen Ruinen und Anomalien. Ionenstürme können Schiffe zerstören.</p>
    <label>Startkolonie <select name="origin">${origins.map(colony => `<option value="${escapeHtml(colony.mission_id)}">${number(colony.galaxy)}:${number(colony.system)}:${number(colony.slot)} · ${number(colony.ships.courier)} Kurierschiffe</option>`).join('')}</select></label>
    <label>Zielsektor <select name="slot">${chart.slots.map(slot => `<option>${number(slot.slot)}</option>`).join('')}</select></label>
    <label>Schiffe <input type="number" name="count" min="1" max="100" value="1" required></label>
    <label>Expeditionsziel <select name="special"><option value="">Reguläre Expedition</option>
      ${(access.special_events || []).map(event => `<option value="${escapeHtml(event.id)}">${escapeHtml(orbitEventNames[event.kind])}</option>`).join('')}
    </select></label>
    <small>Je Konto ist eine Ereignisbelohnung möglich, pro Welt und Ereignis insgesamt bis zu 20. Für die Wächterbegegnung werden mindestens acht Kurierschiffe empfohlen.</small>
    <button>Expedition entsenden</button>
  </form>`;
}
function orbitPhalanxMarkup(chart, colony, access) {
  const scan = colony.phalanx;
  const withinRange = chart && chart.galaxy === colony.galaxy
    && Math.abs(chart.system - colony.system) <= access.phalanx_range;
  return `<h5>Sensorphalanx</h5>
    <p>Reichweite: ${number(access.phalanx_range)} Systeme in dieser Galaxie. Der Scan kostet ${number(access.phalanx_cost)} Äther.</p>
    ${scan ? `<p>Sektor ${scan.coordinates.map(number).join(':')} · ${scan.jammed ? 'Signal gestört' : scan.missions.length ? 'Anflüge erfasst' : 'Keine Anflüge erfasst'}</p>
      <ul>${scan.missions.map(mission => `<li>${mission.kind === 'attack' ? 'Angriff' : 'Fracht'} · Ankunft ${new Date(mission.due * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</li>`).join('')}</ul>`
      : withinRange ? `<form id="orbit-phalanx-${escapeHtml(colony.mission_id)}" data-orbit-phalanx="${escapeHtml(colony.mission_id)}">
        <label>Zielsektor <select name="slot">${chart.slots.map(slot => `<option>${number(slot.slot)}</option>`).join('')}</select></label>
        <button>Einflugverkehr scannen</button>
      </form>` : '<p>Wähle auf der Orbit-Karte ein System in Reichweite.</p>'}`;
}
let orbitReportPage, orbitReportRequest;
function orbitReportMarkup(colony) {
  const page = orbitReportPage?.user === state.id && orbitReportPage.world_id === state.active_world.id
    && orbitReportPage.colony_id === colony.mission_id ? orbitReportPage : null;
  const id = escapeHtml(colony.mission_id);
  return `<h5>Orbit-Gefechtsberichte</h5>
    <button type="button" data-orbit-reports="${id}">Neueste Berichte laden</button>
    ${page && !page.reports.length ? '<p>Keine Berichte vorhanden.</p>' : ''}
    ${(page?.reports || []).map(report => `<details><summary>Orbit-Gefechtsbericht · ${report.attacker_won ? 'Angreifer siegt' : 'Position verteidigt'}</summary>
          ${report.moon_formed ? '<p>Ein Teil der Trümmer hat einen Mond an der Zielkolonie gebildet.</p>' : ''}
          ${report.moon_siege ? `<p>${report.moon_siege.destroyed ? 'Mond zerstört. Ein Belagerungsschiff wurde dabei verbraucht.' : 'Mondbelagerung gescheitert.'}</p>` : ''}
          ${report.retreated ? `<p>Taktischer Rückzug ab ${number(report.retreat_pct)} Prozent Verlust.</p>` : ''}
          ${report.ammunition?.lances ? `<p>${number(report.ammunition.lances)} Sternlanzen geladen · ${number(report.ammunition.intercepted)} abgefangen.</p>` : ''}
          ${report.debris_expires > state.server_time && (report.debris_ore || report.debris_ether) ? `<p>Trümmer: ${number(report.debris_ore)} Erz · ${number(report.debris_ether)} Äther</p>
            ${colony.ships.salvager ? `<button type="button" data-orbit-salvage="${escapeHtml(report.id)}" data-orbit-colony="${escapeHtml(colony.mission_id)}">Ein Bergungsschiff entsenden</button>` : '<p>Ein Bergungsschiff dieser Kolonie wird benötigt.</p>'}` : ''}
          <pre>${escapeHtml(JSON.stringify(report,null,2))}</pre></details>`).join('')}
    ${page?.before ? `<button type="button" data-orbit-reports="${id}" data-before="${escapeHtml(page.before)}">Ältere Berichte laden</button>` : ''}
  `;
}
function orbitAccessMarkup(access) {
  if (!access) return '';
  if (access.unlocked) {
    const chart = orbitChart?.user === state.id && orbitChart.world_id === state.active_world.id
      ? orbitChart : null;
    const origins = (access.colonies || []).filter(colony => colony.ships?.colony_ship > 0);
    const scouts = (access.colonies || []).filter(colony => colony.ships?.probe > 0);
    const canColonize = (access.pioneer_available || origins.length > 0)
      && (access.claims || []).length < access.colony_limit;
    return `<article class="panel queue-panel orbit-showcase">${assetImage('orbit/backgrounds/orbit_title','Orbit-Grenzraum','orbit-banner')}<div class="orbit-showcase-content"><h3>Orbit-Karte</h3>
      <p>Regelstand ${escapeHtml(access.rule_version)}. Die Karte zeigt die Geografie, während Flotten und Kolonien eigene Sichtregeln haben.</p>
      <form id="orbit-chart-form-${state.active_world.id}" data-orbit-chart>
        <label>Galaxie <input name="galaxy" type="number" required min="1" max="${number(access.galaxies)}" value="${chart?.galaxy ?? 1}"></label>
        <label>System <input name="system" type="number" required min="1" max="${number(access.systems_per_galaxy)}" value="${chart?.system ?? 1}"></label>
        <button type="submit">System anzeigen</button>
      </form>
      <p role="status" aria-live="polite">${chart ? `Galaxie ${number(chart.galaxy)} · System ${number(chart.system)}` : 'Wähle eine Galaxie und ein System.'}</p>
      ${access.pioneer_available ? '<p>Ein Pionierschiff mit Treibstoff für einen einfachen Flug steht bereit. Es wird bei der Gründung verbraucht.</p>' : ''}
      <p>Kolonien und reservierte Ziele: ${number((access.claims || []).length)} / ${number(access.colony_limit)}.</p>
      ${chart && canColonize ? `<label>Startpunkt für Kolonisation <select id="orbit-colony-origin">
        ${access.pioneer_available ? '<option value="">Terra-Gateway · Pionierschiff</option>' : ''}
        ${origins.map(colony => `<option value="${escapeHtml(colony.mission_id)}">Orbit-Kolonie ${number(colony.galaxy)}:${number(colony.system)}:${number(colony.slot)} · Kolonieschiff und Äther</option>`).join('')}
      </select></label>` : ''}
      ${chart && scouts.length ? `<label>Startkolonie für Spähsonde <select id="orbit-scout-origin">
        ${scouts.map(colony => `<option value="${escapeHtml(colony.mission_id)}">${number(colony.galaxy)}:${number(colony.system)}:${number(colony.slot)}</option>`).join('')}
      </select></label>` : ''}
      ${chart ? `<ol class="colony-grid">${chart.slots.map(slot => `<li>Sektor ${number(slot.slot)} · ${escapeHtml(slot.terrain)}
        · ${slot.expires_at > state.server_time ? (slot.intel_level === 0 ? 'Sonde abgefangen' : slot.occupied ? `Kolonie beobachtet${slot.ships === null || slot.ships === undefined ? '' : ` · ${number(slot.ships)} Schiffe`}` : 'Bei Aufklärung frei') : 'Belegung unbekannt'}
        ${canColonize ? `<button type="button" data-orbit-slot="${number(slot.slot)}" aria-label="Kolonieschiff zu Sektor ${number(slot.slot)} senden">Kolonieschiff senden</button>` : ''}
        ${scouts.length ? `<button type="button" data-orbit-scout="${number(slot.slot)}" aria-label="Sektor ${number(slot.slot)} aufklären">Aufklären</button>` : ''}
      </li>`).join('')}</ol>` : ''}
      ${orbitAttackMarkup(chart, access)}
      ${orbitAllianceMarkup(access)}
      ${orbitSpecialEventsMarkup(access)}
      ${orbitExpeditionMarkup(chart, access)}
      ${(access.claims || []).map(claim => `<p>Dein Ziel ${number(claim.galaxy)}:${number(claim.system)}:${number(claim.slot)} · ${claim.founded_at ? 'Kolonie gegründet' : `Ankunft ${new Date(claim.arrival * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}`}</p>`).join('')}
      <div class="orbit-assets" aria-label="Orbitale Flotten und Anlagen">${Object.entries(access.ship_catalog||{}).slice(0,14).map(([ship,rule])=>assetImage(`orbit/ships/${ship}`,rule.role||ship,'orbit-ship-art')).join('')}${['moon','asteroid_field','space_station','defense_platform','jump_gate'].map(object=>assetImage(`orbit/orbital_objects/${object}`,object.replaceAll('_',' '),'orbit-object-art')).join('')}</div></div>
      ${(access.colonies || []).map(colony => `<section class="panel queue-panel orbit-colony">
        ${assetImage(colony.moon_formed_at?'orbit/orbital_objects/moon':'orbit/planets/planet_rock',`Orbit-Kolonie ${number(colony.galaxy)}:${number(colony.system)}:${number(colony.slot)}`,'orbit-colony-art')}<h4>Orbit-Kolonie ${number(colony.galaxy)}:${number(colony.system)}:${number(colony.slot)}</h4>
        <p>${colony.supplied_until > state.server_time ? `Flotte versorgt bis ${new Date(colony.supplied_until * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}` : 'Flottenversorgung abgelaufen. Neue Starts sind gesperrt.'}</p>
        ${colony.supplied_until < state.server_time + access.fleet_supply_seconds ? `<button type="button" data-orbit-supply="${escapeHtml(colony.mission_id)}" ${colony.ether < access.fleet_supply_ether ? 'disabled' : ''}>Flotte 24 Stunden versorgen · ${number(access.fleet_supply_ether)} Äther</button>` : ''}
        ${colony.moon_formed_at ? '<p>Zu dieser Kolonie gehört ein Mond.</p>' : ''}
        ${colony.moon_formed_at ? (colony.scanner_ready_at
          ? `<p>Mondscanner ${colony.scanner_ready_at <= state.server_time ? 'aktiv' : 'im Bau'}.</p>`
          : `<button type="button" data-orbit-scanner="${escapeHtml(colony.mission_id)}">Mondscanner bauen · ${number(access.scanner_cost.ore)} Erz / ${number(access.scanner_cost.ether)} Äther</button>`) : ''}
        ${colony.scanner_ready_at && colony.scanner_ready_at <= state.server_time ? orbitPhalanxMarkup(chart, colony, access) : ''}
        <p>${number(colony.ore)} Erz · ${number(colony.ether)} Äther · Energie ${number(Math.min(colony.solar,colony.refinery))}/${number(colony.solar)}</p>
        <details><summary>Letzte Bestandsbuchungen</summary>
          <ol>${colony.resource_ledger.map(entry => `<li>${new Date(entry.recorded_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')} · Lager ${number(entry.ore)} Erz / ${number(entry.ether)} Äther · Reserve ${number(entry.ore_reserve)} Erz / ${number(entry.ether_reserve)} Äther</li>`).join('')}</ol>
        </details>
        <p>Die Kolonie fördert ${number(access.ore_per_hour)} Erz pro Stunde. Jede versorgte Raffineriestufe erzeugt 12 Äther pro Stunde.</p>
        ${colony.job ? `<p>Ausbau läuft bis ${new Date(colony.due * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}.</p>` : ''}
        ${Object.entries({solar:'Solaranlage',refinery:'Ätherraffinerie'}).map(([key,label]) => {
          const price = (colony[key] + 1) * access.building_costs[key];
          return `<button type="button" data-orbit-build="${key}" data-orbit-colony="${escapeHtml(colony.mission_id)}" ${colony.job || colony[key] >= access.building_max_level || price > colony.ore ? 'disabled' : ''}>${label} Stufe ${number(colony[key])} ausbauen · ${number(price)} Erz</button>`;
        }).join(' ')}
        ${orbitShipyardMarkup(colony, access)}
        ${colony.shipbuilding_ready_at && colony.shipbuilding_ready_at <= state.server_time ? orbitStationMarkup(colony) : ''}
        ${orbitFreightMarkup(colony, access.colonies)}
        ${orbitGatewayCargoMarkup(colony, access)}
        ${orbitJumpgateMarkup(colony, access)}
        ${colony.expeditions.map(trip => {
          const result = trip.result;
          const event = result && ({ion_storm:'Ionensturm',quiet:'Keine Funde',ruins:'Raumruinen',anomaly:'Anomalie',boss_retreat:'Rückzug vor dem Wächter',boss_salvage:'Wrackfund beim Wächter',solar_samples:'Sonnenproben',reward_limit:'Ereignis-Belohnungsgrenze erreicht'})[result.event];
          return `<p>Expedition ${number(trip.galaxy)}:${number(trip.system)}:${number(trip.slot)} · ${result ? `${escapeHtml(event)} · ${number(result.lost)} verloren · ${number(result.ore)} Erz / ${number(result.ether)} Äther` : trip.returning ? 'Rückflug' : 'Hinflug'}</p>`;
        }).join('')}
        ${colony.scouts.map(scout => `<p>Spähsonde ${number(scout.galaxy)}:${number(scout.system)}:${number(scout.slot)} · ${scout.returning ? 'Rückflug' : 'Hinflug'} · ${new Date(scout.due * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</p>`).join('')}
        ${colony.attacks.map(attack => `<p>Angriffsflotte · ${number(attack.amount)} × ${escapeHtml(attack.ship)} · ${attack.recalled ? 'Zurückgerufen' : attack.returning ? 'Rückflug' : 'Hinflug'} · Seed-Hash ${escapeHtml(attack.seed_commitment)}
          ${attack.fuel_spent === null || attack.fuel_spent === undefined ? '' : ` · ${number(attack.fuel_spent)} Äther gebucht`}
          ${attack.returning ? '' : `<button type="button" data-orbit-attack-recall="${escapeHtml(attack.id)}" data-orbit-colony="${escapeHtml(colony.mission_id)}">Angriff zurückrufen</button>`}</p>`).join('')}
        ${colony.allied_wings.map(wing => `<p>Allianzverband · ${number(wing.amount)} × ${escapeHtml(wing.ship)} · ${wing.returning ? 'Rückflug' : 'Gemeinsamer Anflug'} · ${new Date(wing.due * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</p>`).join('')}
        ${orbitReportMarkup(colony)}
      </section>`).join('')}
    </article>`;
  }
  return `<article class="panel queue-panel orbit-showcase">${assetImage('orbit/backgrounds/orbit_title','Orbit-Grenzraum','orbit-banner')}<div class="orbit-showcase-content"><h3>Orbit-Zugang</h3><p>Kommandozentrale Stufe ${number(access.hq_required)} und entweder die Kernzitadelle in dieser Welt oder Ingenieurswesen und Logistik auf Stufe ${number(access.hq_required)}.</p><p>Materialien: ${number(access.costs[0])} Holz, ${number(access.costs[1])} Stein, ${number(access.costs[2])} Erz.</p><button type="button" data-action="orbit_unlock" ${access.eligible?'':'disabled'}>Orbit freischalten →</button></div></article>`;
}
function worldSettingsMarkup(world) {
  const choices={
    terra_combat_ruleset:[['FUR-2','FUR-2 · Legacy'],['FUR-3-TERRA-COMBAT-1','FUR-3 · 6 Runden (Beta)'],['FUR-3-TERRA-COMBAT-2','FUR-3 · Außenpostenbefestigung (Entwurf)'],['FUR-3-TERRA-COMBAT-3','FUR-3 · Rollen + Truppenbewegung (Entwurf)'],['FUR-3-TERRA-COMBAT-4','FUR-3 · Roster-Lebenszyklus (Entwurf)'],['FUR-3-TERRA-COMBAT-5','FUR-3 · Festungsregeneration (Entwurf)']],
    crafting_ruleset:[['FUR-2','FUR-2 · aus'],['FUR-CRAFTING-1','FUR-3 · Fertigung und Recycling (Entwurf)']],
    hero_ruleset:[['FUR-2','FUR-2 · aus'],['FUR-3-HERO-1','FUR-3 · Commander-Fortschritt (Entwurf)']],
    hero_doctrine_ruleset:[['FUR-2','FUR-2 · aus'],['FUR-3-HERO-2','FUR-3 · Commander-Doktrinen (Entwurf)']],
    hero_respec_ruleset:[['FUR-2','FUR-2 · aus'],['FUR-3-HERO-3','FUR-3 · Attribut-Reset (Entwurf)']],
    npc_camps_ruleset:[['FUR-2','FUR-2 · aus'],['FUR-3-NPC-CAMPS-1','FUR-3 · NPC-Lager (Entwurfsbalance)'],['FUR-3-NPC-CAMPS-2','FUR-3 · NPC-Aufklärung und Bewegung (Entwurf)'],['FUR-3-NPC-CAMPS-3','FUR-3 · NPC-Angriffe (Balanceentwurf)']],
    terra_ruin_exploration_ruleset:[['FUR-2','FUR-2 · aus'],['FUR-3-TERRA-RUIN-EXPLORATION-1','FUR-3 · Ruinenerkundung (Entwurf)']],
  };
  const current={terra_combat_ruleset:world.terra_combat_ruleset,crafting_ruleset:world.crafting_ruleset,hero_ruleset:world.hero_ruleset,hero_doctrine_ruleset:world.hero_doctrine_ruleset,hero_respec_ruleset:world.hero_respec_ruleset,npc_camps_ruleset:world.npc_camps_ruleset||'FUR-2',terra_ruin_exploration_ruleset:world.terra_ruin_exploration_ruleset||'FUR-2'};
  const select=(key,label)=>`<label>${label}<select name="${key}">${choices[key].map(([value,text])=>`<option value="${value}" ${current[key]===value?'selected':''}>${text}</option>`).join('')}</select></label>`;
  const statuses={pending:'geplant',applied:'aktiviert',cancelled:'abgebrochen',failed:'fehlgeschlagen'};
  const history=(world.pending_rule_rollouts||[]).map(item=>`<li>${escapeHtml(item.rule_key)} → ${escapeHtml(item.target_version)} · ${new Date(Number(item.active_at)*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE',{timeZone:'Europe/Berlin'})} · ${statuses[item.status]||'unbekannt'}${item.failure_code?` · ${escapeHtml(item.failure_code)}`:''}${item.status==='pending'?` <button type="button" class="secondary" data-rule-rollout-cancel="${escapeHtml(item.id)}">Planung abbrechen</button>`:''}</li>`).join('');
  const ruleForm=`<details><summary>Regelupdate für diese Welt planen</summary><p>Die Änderung wird frühestens in einer Minute und spätestens in 90 Tagen aktiv. Bereits gestartete Missionen behalten ihre gespeicherte Regelversion. Nicht mehr kompatible Aufträge können ein Update zum Aktivierungszeitpunkt blockieren.</p><form data-rule-rollout="${number(world.id)}"><label>Regelart<select name="rule_key"><option value="terra_combat_ruleset">Terra-Kampf</option><option value="crafting_ruleset">Fertigung</option><option value="hero_ruleset">Commander</option><option value="hero_doctrine_ruleset">Commander-Doktrinen</option><option value="hero_respec_ruleset">Commander-Reset</option><option value="npc_camps_ruleset">NPC-Lager</option><option value="terra_ruin_exploration_ruleset">Ruinenerkundung</option></select></label><label>Zielversion<select name="target_version"><option value="FUR-2">FUR-2</option><option value="FUR-3-NPC-CAMPS-1">FUR-3-NPC-CAMPS-1 · Entwurfsbalance</option><option value="FUR-3-NPC-CAMPS-2">FUR-3-NPC-CAMPS-2 · Bewegung (Entwurf)</option><option value="FUR-3-NPC-CAMPS-3">FUR-3-NPC-CAMPS-3 · NPC-Angriffe (Balanceentwurf)</option><option value="FUR-3-TERRA-RUIN-EXPLORATION-1">FUR-3-TERRA-RUIN-EXPLORATION-1 · Balanceentwurf</option></select></label><label>Aktiv ab (Europe/Berlin)<input name="active_at_local" type="datetime-local" required></label><button>Regelupdate einplanen</button></form><h4>Letzte Planungen</h4><ul>${history||'<li>Keine Planungen gespeichert.</li>'}</ul></details>`;
  return `<form id="world-settings-form-${world.id}" data-world-settings="${world.id}"><label>Weltname<input name="name" minlength="3" maxlength="48" required value="${escapeHtml(world.name)}"></label><label><input name="joinable" type="checkbox" ${world.joinable?'checked':''}>Spielerbeitritt erlauben</label>${select('terra_combat_ruleset','Kampfregeln')}<label>FUR-3-Rückzug ab Verlusten (%)<input name="terra_retreat_threshold_percent" type="number" min="1" max="100" step="1" required value="${Number(world.terra_retreat_threshold_percent??60)}"></label>${select('crafting_ruleset','FUR-3-Gegenstandssysteme')}${select('hero_ruleset','FUR-3-Heldenverwaltung')}${select('hero_doctrine_ruleset','FUR-3-Commander-Doktrinen')}${select('hero_respec_ruleset','FUR-3-Commander-Reset')}<small>Fertigung und Commander-Erweiterungen sind weltweise FUR-3-Regelstände. Bereits laufende Aufträge behalten den gespeicherten Vertrag. Die angegebenen FUR-3-Balancewerte bleiben Entwürfe.</small><button>Einstellungen sofort speichern →</button></form>${ruleForm}`;
}

function worldRulesSummaryMarkup(world) {
  const rules=[
    ['Grundregeln','FUR-2'],
    ['Terra-Kampf',world.terra_combat_ruleset],
    ['Fertigung',world.crafting_ruleset],
    ['Commander',world.hero_ruleset],
    ['Commander-Doktrinen',world.hero_doctrine_ruleset],
    ['Commander-Reset',world.hero_respec_ruleset],
    ['NPC-Lager',world.npc_camps_ruleset],
    ['Ruinenerkundung',world.terra_ruin_exploration_ruleset],
  ];
  return `<details><summary>Regeln dieser Welt</summary><ul>${rules.map(([name,value])=>`<li>${escapeHtml(name)}: ${escapeHtml(value||'FUR-2')}</li>`).join('')}</ul><p>Die Rangliste folgt den Regeln der ausgewählten Welt.</p></details>`;
}

function worldCreationRulesMarkup() {
  return `<details><summary>Startregelprofil</summary><p>Neue Welten starten in FUR-2. FUR-3-Entwürfe bleiben aus, bis du sie hier ausdrücklich auswählst.</p><label>Kampfregeln<select name="terra_combat_ruleset"><option value="FUR-2">FUR-2 · Legacy</option><option value="FUR-3-TERRA-COMBAT-1">FUR-3 · 6 Runden (Beta)</option><option value="FUR-3-TERRA-COMBAT-2">FUR-3 · Außenpostenbefestigung (Entwurf)</option><option value="FUR-3-TERRA-COMBAT-3">FUR-3 · Rollen + Truppenbewegung (Entwurf)</option><option value="FUR-3-TERRA-COMBAT-4">FUR-3 · Roster-Lebenszyklus (Entwurf)</option><option value="FUR-3-TERRA-COMBAT-5">FUR-3 · Festungsregeneration (Entwurf)</option></select></label><label>FUR-3-Rückzug ab Verlusten (%)<input name="terra_retreat_threshold_percent" type="number" min="1" max="100" step="1" value="60" required></label><label>Fertigung<select name="crafting_ruleset"><option value="FUR-2">FUR-2 · aus</option><option value="FUR-CRAFTING-1">FUR-3 · Fertigung und Recycling (Entwurf)</option></select></label><label>Commander<select name="hero_ruleset"><option value="FUR-2">FUR-2 · aus</option><option value="FUR-3-HERO-1">FUR-3 · Fortschritt (Entwurf)</option></select></label><label>Commander-Doktrinen<select name="hero_doctrine_ruleset"><option value="FUR-2">FUR-2 · aus</option><option value="FUR-3-HERO-2">FUR-3 · Doktrinen (Entwurf, benötigt Commander)</option></select></label><label>Commander-Reset<select name="hero_respec_ruleset"><option value="FUR-2">FUR-2 · aus</option><option value="FUR-3-HERO-3">FUR-3 · Reset (Entwurf, benötigt Commander)</option></select></label><label>NPC-Lager<select name="npc_camps_ruleset"><option value="FUR-2">FUR-2 · aus</option><option value="FUR-3-NPC-CAMPS-1">FUR-3 · NPC-Lager (Entwurfsbalance)</option><option value="FUR-3-NPC-CAMPS-2">FUR-3 · NPC-Aufklärung und Bewegung (Entwurf)</option><option value="FUR-3-NPC-CAMPS-3">FUR-3 · NPC-Angriffe (Balanceentwurf)</option></select></label><label>Ruinenerkundung<select name="terra_ruin_exploration_ruleset"><option value="FUR-2">FUR-2 · aus</option><option value="FUR-3-TERRA-RUIN-EXPLORATION-1">FUR-3 · Ruinenerkundung (Entwurf)</option></select></label></details>`;
}

function seasonSummaryMarkup(current) {
  if (current.active_world?.mode !== 'season') return '';
  const seasons=Array.isArray(current.seasons)?current.seasons:[];
  if (!seasons.length) return current.profile?.role === 'admin' ? `<section class="panel queue-panel"><h3>Saison starten</h3><p>Die Saisonwertung verwendet den eingefrorenen FUR-2-Punktestand. Kommandanten erreichen das gesetzte Punkteziel bis zum Saisonende; die Rangfolge und das Ziel werden danach archiviert.</p><form id="season-create-form"><label for="season-name">Saisonname</label><input id="season-name" name="name" minlength="3" maxlength="60" required><label for="season-days">Laufzeit in Tagen</label><input id="season-days" name="days" type="number" min="1" max="365" value="30" required><label for="season-goal-score">Punkteziel</label><input id="season-goal-score" name="goal_score" type="number" min="1" max="1000000000" value="10000" required><button>Saison starten →</button></form></section>` : '<p role="status">Für diese Saisonwelt wurde noch kein Wettbewerb gestartet.</p>';
  const categoryNames={overall:'Gesamt',economy:'Wirtschaft',research:'Forschung',pve:'PvE',war:'Krieg',regions:'Regionen'};
  const hall=current.hall_of_fame||{};
  const prestige=current.prestige||{level:0,max_level:3,milestones:[]};
  const hallSeasons=hall.seasons||[],hallAlliances=hall.alliances||[],hallBosses=hall.bosses||[],hallWars=hall.wars||[];
  const hallMarkup=`<section class="panel queue-panel" aria-labelledby="hall-of-fame-title"><h3 id="hall-of-fame-title">Hall of Fame</h3><p>Deine historischen Ehrungen aus dieser Welt.</p><h4>Imperiums-Prestige · Stufe ${number(prestige.level||0)} / ${number(prestige.max_level||3)}</h4><p>${escapeHtml(prestige.badge||'Noch kein Prestigeabzeichen')} · dauerhaft kosmetisch, ohne Kampf- oder Ranglistenbonus.</p><ol>${(prestige.milestones||[]).map(record=>`<li>${escapeHtml(({campaign_victory:'Kampagnensieg',season_champion:'Saisonmeister',season_goal_achieved:'Saisonziel erreicht'})[record.source_type]||record.source_type)} · Stufe ${number(record.prestige_level)} · ${escapeHtml(record.rules_version||'FUR-3-PRESTIGE-1')}</li>`).join('')||'<li>Erreiche einen Kampagnensieg oder ein Saisonziel, um Prestige zu sammeln.</li>'}</ol><h4>Saisonerfolge</h4><ol>${hallSeasons.map(record=>`<li>${escapeHtml(record.season_name)} · ${record.award==='season_champion'?'Saisonmeister':'Saisonziel erreicht'} · ${number(record.score)} Punkte</li>`).join('')||'<li>Noch keine Saisonerfolge.</li>'}</ol><h4>Allianzsaisons</h4><ol>${hallAlliances.map(record=>`<li>${escapeHtml(record.alliance_name)} [${escapeHtml(record.alliance_tag)}] · Platz ${number(record.rank)} · ${number(record.score)} Punkte</li>`).join('')||'<li>Noch keine archivierten Allianzerfolge.</li>'}</ol><h4>Wächterbegegnungen</h4><ol>${hallBosses.map(record=>`<li><time>${new Date(Number(record.ends)*1000).toLocaleDateString(globalThis.FURI18n?.locale || 'de-DE')}</time> · Orbit-Wächter geborgen</li>`).join('')||'<li>Noch kein Wächtererfolg archiviert.</li>'}</ol><h4>Allianzkriege</h4><ol>${hallWars.map(record=>`<li>[${escapeHtml(record.alliance_a_tag)}] ${escapeHtml(record.alliance_a_name)} ↔ [${escapeHtml(record.alliance_b_tag)}] ${escapeHtml(record.alliance_b_name)} · ${record.end_reason==='peace'?'Frieden geschlossen':'Kriegsziel erreicht'}${record.winner===record.actor_alliance?' · Sieg deiner Allianz':''}</li>`).join('')||'<li>Noch kein beendeter Allianzkrieg.</li>'}</ol></section>`;
  return `${hallMarkup}<section class="panel queue-panel"><h3>Saisonarchiv</h3>${seasons.map(season=>{let standings=[];try{standings=typeof season.standings==='string'?JSON.parse(season.standings):season.standings||[];}catch{standings=[];}if(!Array.isArray(standings))standings=[];const alliances=Array.isArray(season.alliance_standings)?season.alliance_standings:[];const categoryStandings=Array.isArray(season.category_standings)?season.category_standings:[];const awards=Array.isArray(season.awards)?season.awards:[];const categories=Object.keys(categoryNames).map(category=>{const rows=categoryStandings.filter(row=>row.category===category).slice(0,3);return rows.length?`<h6>${categoryNames[category]}</h6><ol>${rows.map(row=>`<li>${escapeHtml(row.display_name)} · ${number(row.score)} Punkte</li>`).join('')}</ol>`:'';}).join('');return `<article><h4>${escapeHtml(season.name)}</h4><p>${season.archived?'Beendet':'Läuft'} · Ziel ${number(season.goal_score)} Punkte · Ende ${new Date(season.ends*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</p><h5>Kommandanten · Gesamt</h5><ol>${standings.map(row=>`<li>${escapeHtml(row.name||'Kommandant')} · ${number(row.score)} Punkte${row.goal_reached?' · Ziel erreicht':''}${row.awards?.includes('season_champion')?' · Saisonmeister':''}</li>`).join('')}</ol>${categoryStandings.length?`<details><summary>Weitere saisonale Ranglisten · ${escapeHtml(season.ranking_rules_version||'unbekannte Regelversion')}</summary>${categories}</details>`:''}<h5>Allianzen</h5><ol>${alliances.map(row=>`<li>${escapeHtml(row.alliance_name||row.name)} [${escapeHtml(row.alliance_tag||row.tag)}] · ${number(row.score)} Punkte</li>`).join('')||'<li>Keine gewerteten Allianzen.</li>'}</ol><h5>Auszeichnungen</h5><ul>${awards.map(award=>`<li>${escapeHtml(award.name)} · ${award.award==='season_champion'?'Saisonmeister':'Saisonziel erreicht'} · ${number(award.score)} Punkte</li>`).join('')||'<li>Noch keine Auszeichnungen.</li>'}</ul></article>`;}).join('')}</section>`;
}
function colonyRenameMarkup(colony) {
  return `<form data-colony-rename="${escapeHtml(colony.colony_id)}"><label for="rename-${escapeHtml(colony.colony_id)}">Kolonie umbenennen</label><input id="rename-${escapeHtml(colony.colony_id)}" name="name" minlength="3" maxlength="32" aria-describedby="rename-help-${escapeHtml(colony.colony_id)}" required value="${escapeHtml(colony.name)}"><small id="rename-help-${escapeHtml(colony.colony_id)}">3–32 Buchstaben, Zahlen, Leerzeichen oder Bindestriche; weltweit eindeutig.</small><button>Umbenennen</button></form>`;
}
function colonyAbandonMarkup(colony) {
  if (colony.is_home) return '<p role="status">Heimatkolonien sind geschützt. Wechsle zuerst die Heimatkolonie.</p>';
  return `<button type="button" data-colony-abandon="${escapeHtml(colony.colony_id)}" data-colony-name="${escapeHtml(colony.name)}">Kolonie aufgeben</button><small>Erst nach Abschluss aller Aufträge und Rücknahme offener Handelsangebote möglich. Eine Ruine sperrt den Sektor für 24 Stunden.</small>`;
}
function colonyHomeMarkup(colony) {
  if (colony.is_home || colony.world_id !== state.active_world?.id) return '';
  const status = state.home_designation;
  if (!status) return '';
  if (!status.available) return `<p>Heimatwechsel wieder möglich: ${escapeHtml(new Date(status.next_change * 1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE'))}.</p>`;
  return `<p>Heimatwechsel: keine Übertragung von Vorräten oder Truppen; danach 24 Stunden Sperrfrist in dieser Welt.</p><button type="button" class="secondary" data-action="colony_home" data-key="${escapeHtml(colony.colony_id)}">Als Heimatkolonie festlegen</button>`;
}
initSystems();
async function api(path, body, method) {
  const requestMethod=method||(body?'POST':'GET');
  const csrfRequired = requestMethod !== 'GET' && !path.startsWith('auth/') && path !== 'account/public';
  const options = {method:requestMethod, headers: {'Content-Type':'application/json',...(csrfRequired?{'X-CSRF-Token':csrf}:{})}, ...(body ? {body:JSON.stringify(body)} : {})};
  if (globalThis.FURI18n) Object.assign(options.headers, {'Accept-Language': globalThis.FURI18n.language, 'X-FUR-I18N': '1'});
  let response = await fetch('/api/v1/' + path, options);
  let result = await response.json();
  if (csrfRequired && response.status === 400 && (result.code === 'invalid_csrf' || result.error === 'Ungültiger Sitzungsschutz. Bitte Seite neu laden.')) {
    const refreshed = await fetch('/api/v1/state');
    const session = await refreshed.json();
    if (refreshed.ok && typeof session.csrf === 'string' && session.csrf) {
      csrf = session.csrf;
      options.headers = {...options.headers,'X-CSRF-Token':csrf};
      response = await fetch('/api/v1/' + path, options);
      result = await response.json();
    }
  }
  if (!response.ok) { const error=new Error(result.error || 'Bitte Eingaben prüfen oder erneut versuchen.'); error.status=response.status; throw error; }
  return result;
}
async function loadMissionTemplates(userId) {
  if (missionTemplateOwner === userId) return;
  const result=await api('mission-templates');
  missionTemplates=result.templates;
  missionTemplateOwner=userId;
}
async function loadProductionTemplates(userId) {
  if (productionTemplateOwner === userId) return;
  const result=await api('production-templates');
  productionTemplates=result.templates;
  productionTemplateOwner=userId;
}
function productionTemplateOptions(templates, kind) {
  return '<option value="">Vorlage wählen</option>'+templates.filter(item=>item.kind===kind).map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)} · ${escapeHtml(item.key)}${kind==='train'?` × ${item.count}`:''}</option>`).join('');
}
function productionTemplatePanel(kind) {
  const catalog=kind==='build'?state.catalog.buildings:kind==='research'?state.catalog.tech:Object.fromEntries(Object.entries(state.catalog.units).filter(([key])=>canTrainUnit(key)&&key!=='outpost_fortification'));
  const label=kind==='build'?'Bau':kind==='research'?'Forschung':'Rekrutierung';
  const selected=productionTemplates.filter(item=>item.kind===kind);
  return `<section class="production-templates" aria-label="${label}vorlagen"><h2>${label}vorlagen</h2><p>Vorlagen speichern nur den Auftrag. Beim Einreihen gelten Ressourcen, Voraussetzungen und Queue-Limits der aktiven Kolonie.</p><label for="production-template-select">Gespeicherte Vorlage</label><select id="production-template-select">${productionTemplateOptions(productionTemplates,kind)}</select><div><button type="button" class="secondary" id="queue-production-template" ${selected.length?'':'disabled'}>Einreihen</button> <button type="button" class="secondary" id="delete-production-template" ${selected.length?'':'disabled'}>Vorlage löschen</button></div><form id="production-template-form" data-production-kind="${kind}"><label for="production-template-name">Name</label><input id="production-template-name" name="name" minlength="2" maxlength="32" required autocomplete="off"><label for="production-template-key">${label}</label><select id="production-template-key" name="key">${Object.entries(catalog).map(([key,item])=>`<option value="${escapeHtml(key)}">${escapeHtml(item.name)}</option>`).join('')}</select>${kind==='train'?'<label for="production-template-count">Anzahl</label><input id="production-template-count" name="count" type="number" min="1" max="100" value="5" required>':''}<button class="secondary">Vorlage speichern</button></form><p id="production-template-status" role="status" aria-live="polite"></p></section>`;
}
function notify(message) { $('notice').textContent = message; $('notice').classList.add('visible'); setTimeout(() => $('notice').classList.remove('visible'), 5000); }
function commandOrigin() {
  return {
    world_id: state.active_world.id,
    colony_id: state.colony_id,
    rule_version: state.rules_version
  };
}
async function command(action, payload) {
  if (busy) return;
  if (action === 'world_select' || action === 'world_join') mapRouteId = '';
  busy = true;
  try { state = await api('command', {action,payload,token:crypto.randomUUID(),origin:commandOrigin()}); render(); notify(window.FURI18n ? window.FURI18n.t('command.confirmed') : 'Befehl bestätigt.'); return true; }
  catch (error) { notify(error.message); return false; }
  finally { busy = false; }
}
async function showGame() { await gameAssetCatalogReady; if (window.FURI18n) { await window.FURI18n.ready; window.FURI18n.setLanguage(state.language || window.FURI18n.language); } $('auth').hidden = true; $('game').hidden = false; $('commander').textContent = state.name; render(); }
function updateAuthLanguage() {
  if (!window.FURI18n) return;
  const i18n = window.FURI18n;
  $('auth-title').textContent = i18n.t(register ? 'auth.register_title' : 'auth.login_title');
  $('auth-submit').dataset.i18n = register ? 'auth.register_submit' : 'auth.login';
  $('toggle-auth').dataset.i18n = register ? 'auth.switch_login' : 'auth.register';
  i18n.apply();
}
$('toggle-auth').onclick = () => {
  register = !register;
  $('password').autocomplete = register ? 'new-password' : 'current-password';
  $('auth-email-label').hidden = !register;
  $('auth-email').required = register;
  $('password').minLength = register ? 12 : 8;
  $('beta-registration-fields').hidden = !register;
  $('beta-registration-fields').disabled = !register;
  updateAuthLanguage();
};
if (window.FURI18n) window.FURI18n.ready.then(() => window.FURI18n.setLanguage(window.FURI18n.language));
let languageSave = Promise.resolve();
window.addEventListener('fur:language-changed', () => {
  updateAuthLanguage();
  names.splice(0, names.length, ...['wood', 'stone', 'ore'].map(key => window.FURI18n.t('resource.' + key)));
  if (state) {
    render();
    const language = window.FURI18n.language;
    languageSave = languageSave.then(() => api('account/language', {language})).catch(() => notify(window.FURI18n.t('language.save_failed')));
  }
});

if(typeof window!=='undefined')window.addEventListener('fur:account-banned',()=>{const appeal=$('ban-appeal');if(appeal)appeal.hidden=false;});
$('auth-form').onsubmit = async event => { event.preventDefault(); $('auth-submit').disabled = true; $('auth-error').textContent = ''; try { if(register && $('password').value !== $('password-confirmation').value) throw new Error(window.FURI18n.t('error.password_confirmation')); const recovery=$('auth-recovery-label')&&!$('auth-recovery-label').hidden; const result = await api('auth/' + (register ? 'register' : 'login'), {...(register?{password_confirmation:$('password-confirmation').value,terms_accepted:$('terms-accepted').checked,privacy_acknowledged:$('privacy-acknowledged').checked,registration_version:'2026-11-20',language:window.FURI18n.language}:{}),name:$('name').value,password:$('password').value,email:register?$('auth-email').value:'',code:recovery?'':$('auth-code').value,recovery_code:recovery?$('auth-recovery-code').value:''}); csrf = result.csrf; state = await api('state'); window.dispatchEvent(new Event('fur:session-started')); await loadMissionTemplates(state.id); await loadProductionTemplates(state.id); $('password').value = ''; if($('auth-recovery-code'))$('auth-recovery-code').value=''; await showGame(); } catch (error) { $('auth-error').textContent = error.message; if(!register&&error.message==='Dieses Konto ist gesperrt.')window.dispatchEvent(new Event('fur:account-banned')); } finally { $('auth-submit').disabled = false; } };
$('logout').onclick = async () => { try { await api('logout', {}); state = undefined; missionTemplates=[]; missionTemplateOwner=''; productionTemplates=[]; productionTemplateOwner=''; window.dispatchEvent(new Event('fur:session-ended')); $('game').hidden = true; $('auth').hidden = false; } catch (error) { notify(error.message); } };
if(typeof window!=='undefined')window.addEventListener('fur:logout-everywhere',()=>{state=undefined;missionTemplates=[];missionTemplateOwner='';productionTemplates=[];productionTemplateOwner='';$('game').hidden=true;$('auth').hidden=false;});
document.querySelectorAll('nav button').forEach(button => button.onclick = () => { tab = button.dataset.tab; document.querySelectorAll('nav button').forEach(b => b.classList.toggle('active', b === button)); $('page-title').textContent = button.querySelector('span')?.textContent.trim() || button.textContent.trim(); render(); window.scrollTo(0, 0); });
function cost(item, level = 0, count = 1) { return item.cost.map((n,i) => `<span>${resourceIcon(i,'cost-icon')} ${number(n * (level + 1) * count)} ${names[i]}</span>`).join(''); }
function terraDefenseMarkup() {
  const defense=state.terra_defense;
  if(!defense)return '';
  const cards=Object.entries(defense.catalog||{}).map(([key,item])=>{
    const stack=defense.stacks?.[key]||[], damaged=stack.filter(integrity=>integrity<100).length;
    const requirements=Object.entries(item.prerequisites?.buildings||{}).map(([id,level])=>({label:`${state.catalog.buildings[id]?.name||id} ${level}`,met:(state.buildings[id]||0)>=level})).concat(Object.entries(item.prerequisites?.tech||{}).map(([id,level])=>({label:`${state.catalog.tech[id]?.name||id} ${level}`,met:(state.tech[id]||0)>=level})));
    const ready=requirements.every(req=>req.met), enough=item.cost.every((amount,index)=>state.resources[index]>=amount), full=stack.length>=item.maximum_count, slotsFull=defense.slot_usage+item.slot_cost>defense.slot_limit, repairCost=item.cost.map(amount=>stack.filter(integrity=>integrity<100).reduce((sum,integrity)=>sum+Math.ceil(amount*(100-integrity)*item.repair_cost_percent/10000),0)), repairEnough=repairCost.every((amount,index)=>state.resources[index]>=amount);
    const blockers=[!ready?'Voraussetzungen fehlen':null,!enough?'Rohstoffe fehlen':null,full?'Anlagenlimit erreicht':null,slotsFull?'Verteidigungsslots belegt':null].filter(Boolean);
    const integrity=stack.length?stack.map(value=>`${number(value)} %`).join(', '):'Keine Anlage errichtet';
    return `<article class="card"><div class="card-top"><span class="building-icon">⌬</span><span class="level">${stack.length} / ${number(item.maximum_count)}</span></div><h3>${escapeHtml(item.name)}</h3><p>${item.kind==='minefield'?'Minenfeld':item.kind==='support'?'Unterstützungsbauwerk':item.kind==='shield'?'Schildanlage':'Geschütz'} · Verteidigung ${number(item.defense_power)}</p><p>Integrität: ${escapeHtml(integrity)}</p><p>Voraussetzungen: ${requirements.length?requirements.map(req=>`${req.met?'✓':'✕'} ${escapeHtml(req.label)}`).join(' · '):'keine'}</p><div class="cost">${cost(item)}</div><button type="button" data-action="terra_defense_build" data-key="${escapeHtml(key)}" ${blockers.length?'disabled':''}>Errichten · ${item.cost.map((amount,index)=>`${icons[index]} ${number(amount)}`).join(' ')}</button>${blockers.length?`<small>Gesperrt: ${blockers.map(escapeHtml).join(' · ')}</small>`:''}${damaged?`<p>Reparaturkosten: ${repairCost.map((amount,index)=>`${icons[index]} ${number(amount)}`).join(' ')}</p><button type="button" class="secondary" data-action="terra_defense_repair" data-key="${escapeHtml(key)}" data-count="${damaged}" ${repairEnough?'':'disabled'}>Alle ${damaged} beschädigten reparieren</button>`:''}</article>`;
  }).join('');
  return `<section class="defense-buildings" aria-labelledby="terra-defense-title"><div class="section-intro"><p class="eyebrow">FUR-3 · VORLÄUFIGER ENTWURF ${escapeHtml(defense.version)}</p><h2 id="terra-defense-title">Kolonieverteidigung</h2><p>Anlagen belegen eigene Slots und haben getrennte Integrität. Nur in COMBAT-4-Welten verfügbar. Werte sind noch nicht balanceabgenommen. Slots: ${number(defense.slot_usage)} / ${number(defense.slot_limit)} · Anlagenwert ${number(defense.power)}.</p></div><div class="cards">${cards}</div><p role="note">Geschütze, Schilde und Bunker nehmen an Spieler- und Allianzgefechten teil. Minen werden deterministisch ausgewürfelt; Schäden und Minenverbrauch stehen im Gefechtsbericht. Reparaturen sind bei eingehenden feindlichen Anmärschen gesperrt.</p></section>`;
}
function itemPrerequisites(item) {
  const requirements=item.requirements||{buildings:{},tech:{}};
  return [
    ...Object.entries(requirements.buildings||{}).map(([key,level])=>({kind:'buildings',key,level})),
    ...Object.entries(requirements.tech||{}).map(([key,level])=>({kind:'tech',key,level}))
  ];
}
function rankingListMarkup(entries, offset, hasMore) {
  return `<article class="panel" aria-label="Rangliste"><ol class="ranking-list">${entries.map((entry,index)=>`<li class="rank"><strong>${String(offset+index+1).padStart(2,'0')}</strong><b>${escapeHtml(entry.name)}</b><span>${number(entry.score)} Punkte</span><button type="button" class="secondary" data-player-profile="${escapeHtml(entry.id)}">Profil ansehen</button></li>`).join('')}</ol>${hasMore?'<button type="button" class="secondary" data-ranking-more>Weitere Ranglistenplätze laden</button><p role="status" data-ranking-status aria-live="polite"></p>':''}</article>`;
}
function publicPlayerProfileMarkup(profile) {
  if(!profile)return '';
  const cosmetics=[profile.skin,profile.banner].filter(Boolean);
  return `<article class="panel public-player-profile" aria-labelledby="public-player-profile-title" data-profile-skin="${escapeHtml(profile.skin_id||'none')}" data-profile-banner="${escapeHtml(profile.banner_id||'none')}"><button type="button" class="secondary" data-player-profile-close>Profil schließen</button><h2 id="public-player-profile-title">${escapeHtml(profile.name)}${profile.title&&profile.title!=='Kein Titel'?` · ${escapeHtml(profile.title)}`:''}</h2>${cosmetics.length?`<p class="profile-cosmetics">${cosmetics.map(escapeHtml).join(' · ')}</p>`:''}<p>${escapeHtml(profile.world)} · Rang ${number(profile.rank)} · ${number(profile.score)} Punkte</p>${profile.badges?.length?`<ul class="profile-badges" aria-label="Profilabzeichen">${profile.badges.map(badge=>`<li>${escapeHtml(badge)}</li>`).join('')}</ul>`:'<p>Keine ausgewählten Profilabzeichen.</p>'}<small>${escapeHtml(profile.rules_version)} · Öffentliche Profildaten, vom Spieler freigegeben.</small></article>`;
}
function isLegacyUnit(key) {
  return ['ranger','sentinel','mech'].includes(key) || Object.hasOwn(state.faction_unit_requirements||{},key);
}
function canTrainUnit(key) {
  return canTrainFactionUnit(key) && (isLegacyUnit(key) || state.active_world?.unit_training_enabled === true);
}
function terraRecoveryMarkup() {
  if (!['FUR-3-TERRA-COMBAT-4','FUR-3-TERRA-COMBAT-5'].includes(state.active_world?.terra_combat_ruleset)) return '';
  const rules=state.terra_recovery_rules, wrecks=state.terra_unit_wrecks||[];
  const repairsBusy=state.jobs.some(job=>job.kind==='terra_repair');
  const rows=wrecks.map(wreck=>{
    const unit=state.catalog.units[wreck.unit], count=Number(wreck.amount);
    if(!unit||!Number.isInteger(count)||count<1)return '';
    const repairCosts=unit.cost.map(value=>Math.ceil(value*rules.repair_cost_percent/100));
    return `<article class="terra-wreck"><h4>${escapeHtml(unit.name)} · ${number(count)} reparierbar</h4>
      <p>Wrackfrist bis ${new Date(wreck.expires*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}. Kosten je Einheit: ${repairCosts.map(number).join(' / ')} Holz, Stein, Erz. Reparaturzeit: ${number(unit.time)} Sekunden je Einheit.</p>
      <form data-terra-repair="${escapeHtml(wreck.id)}"><label><span data-i18n="game.count">Anzahl</span><input name="count" type="number" min="1" max="${count}" value="${count}" required></label>
      <button ${repairsBusy?'disabled':''}>Wrack reparieren →</button></form></article>`;
  }).join('');
  return `<section class="panel terra-recovery" aria-labelledby="terra-recovery-title"><h3 id="terra-recovery-title">Terra-Wrackreparatur</h3>
    <p>Regel ${escapeHtml(rules.version)} · ${number(rules.loss_recovery_percent)}% der Verluste werden je Einheitstyp zur Reparatur geborgen; Wracks verfallen nach 48 Stunden. Kosten: halber Einheitspreis, je Rohstoff aufgerundet. Diese Werte sind ein nicht ausbalancierter Entwurf.</p>
    ${rows||'<p class="empty">Keine reparierbaren Wracks in dieser Kolonie.</p>'}</section>`;
}
function canTrainFactionUnit(key) {
  const rule = state.faction_unit_requirements?.[key];
  return !rule || (rule.own_faction && state.faction_research?.includes(rule.research));
}
function itemPrerequisitesMet(item) {
  return itemPrerequisites(item).every(({kind,key,level})=>Number(state[kind]?.[key]||0)>=Number(level));
}
function itemPrerequisitesLabel(item) {
  return itemPrerequisites(item).map(({kind,key,level})=>` ${escapeHtml(state.catalog[kind]?.[key]?.name||key)} Stufe ${level}`).join(' · ');
}
function ruinExplorationMarkup(current) {
  const enabled=current.active_world?.terra_ruin_exploration_ruleset==='FUR-3-TERRA-RUIN-EXPLORATION-1';
  const targets=current.terra_ruin_targets||[];
  const observations=Object.values(current.terra_ruin_intel||{});
  if(!enabled&&!observations.length)return '';
  const labels={relic_cache:'Reliktlager geborgen',salvage:'Fracht geborgen',unstable_ruin:'Instabile Kammern',hazard:'Gefährliche Trümmer',quiet:'Keine besonderen Vorkommnisse'};
  const known=targets.map(ruin=>{
    const travel=Number.isInteger(ruin.travel_seconds)?`${number(ruin.travel_seconds)} s Hinweg`:'kein begehbarer Weg';
    return `<li><button type="button" id="explore-ruin-${escapeHtml(ruin.id)}" class="target-row" data-ruin="${escapeHtml(ruin.id)}"><span>Kolonieruine ${number(ruin.x)}:${number(ruin.y)} · ${travel}</span></button><small>Aufbruch bis ${new Date(ruin.expires*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</small></li>`;
  }).join('');
  const surveyed=observations.map(ruin=>`<li>${number(ruin.x)}:${number(ruin.y)} · ${escapeHtml(labels[ruin.outcome]||'Ruine erkundet')} · gültig bis ${new Date(ruin.expires_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</li>`).join('');
  return `<section class="panel queue-panel" aria-labelledby="ruin-exploration-title"><h3 id="ruin-exploration-title">Ruinenerkundung</h3>${enabled?(known?`<ul aria-label="Bekannte Kolonieruinen">${known}</ul>`:'<p>Keine aktiven Ruinen in Sichtweite.</p>'):''}${surveyed?`<h4>Private Ruinenbeobachtungen</h4><ul>${surveyed}</ul>`:''}</section>`;
}
function npcConvoyMarkup(current) {
  const program=current.npc_convoy;
  if(!program)return '';
  const {convoy,rewards}=program;
  const admin=current.profile?.role==='admin';
  if(!convoy&&!rewards.length&&!admin)return '';
  const utc=seconds=>`<time datetime="${new Date(seconds*1000).toISOString()}">${new Date(seconds*1000).toISOString().slice(0,16).replace('T',' ')} UTC</time>`;
  const rangers=Math.min(current.units.ranger||0,program.maximum_rangers);
  const points=convoy?`<ol aria-label="Öffentlicher Konvoi-Fahrplan">${convoy.checkpoints.map(point=>`<li>Treffpunkt ${number(point.stage+1)} · ${number(point.x)}:${number(point.y)} · ${utc(point.starts)} bis ${utc(point.ends)}</li>`).join('')}</ol>`:'';
  const target=convoy?.rendezvous;
  const signup=convoy?.can_join&&rangers>0?`<form data-convoy-join="${escapeHtml(convoy.id)}"><p>Treffpunkt ${number(target.stage+1)} · Ankunft ${utc(target.due)}. Eine frühe Ankunft wartet auf den Konvoi.</p><label>Einsatz<select name="role"><option value="escort">Eskorte gegen NPC-Plünderer</option><option value="raid">Überfall auf die NPC-Wache</option></select></label><label>Ranger<input name="count" type="number" min="1" max="${Number(rangers)}" value="1" required></label><button>Ranger entsenden</button></form>`:'';
  const own=convoy?.own;
  const status=own?own.status==='marching'?'Dein Trupp ist unterwegs.':own.status==='cancelled'?'Dein Einsatz wurde zurückgerufen.':own.victory?'Dein Trupp hat gewonnen.':'Dein Trupp hat verloren.':'';
  const recall=own?.status==='marching'&&(current.jobs||[]).some(job=>job.id===own.mission_id)?`<button type="button" data-action="npc_convoy_recall" data-key="${escapeHtml(own.mission_id)}">Konvoiauftrag zurückrufen</button>`:'';
  const schedule=admin&&!convoy?'<form data-convoy-schedule><label>Name des Konvois<input name="name" minlength="3" maxlength="48" required></label><button>NPC-Konvoi für diese Welt ansetzen</button></form>':'';
  const claims=rewards.map(reward=>`<li>${escapeHtml(reward.name)} · ${number(reward.reward_ore)} Erz <button type="button" data-action="npc_convoy_claim" data-key="${escapeHtml(reward.id)}">Belohnung abholen</button></li>`).join('');
  return `<section class="panel queue-panel" aria-labelledby="npc-convoy-title"><h3 id="npc-convoy-title">NPC-Handelskonvoi</h3><p>Vorläufige Balance. Reines PvE mit getrennten NPC-Gefechten. Je Konto ein Einsatz, auch nach Rückruf. ${number(program.slots)} Plätze und höchstens ${number(program.slots*program.reward_ore)} Erz insgesamt. Jeder Sieg bringt ${number(program.reward_ore)} Erz.</p><p>Jeder Ranger hat ${number(program.power_per_ranger)} Kampfkraft. Plünderer haben ${number(program.npc_power.escort)}, die Konvoiwache ${number(program.npc_power.raid)}. Ab gleicher Stärke gewinnst du. Verluste bei Sieg ${number(program.victory_loss_percent)} %, bei Niederlage ${number(program.defeat_loss_percent)} %, jeweils aufgerundet. Rückruf vor Ankunft bringt alle Ranger zurück, ohne Belohnung.</p>${convoy?`<h4>${escapeHtml(convoy.name)}</h4><p>${number(convoy.booked)}/${number(program.slots)} Plätze belegt${convoy.starts>current.server_time?' · Warnphase':''}</p>${points}<p>${status}</p>${recall}${signup}`:''}${schedule}${claims?`<ul aria-label="Deine Konvoi-Belohnungen">${claims}</ul>`:''}</section>`;
}
function terraBossMarkup(current) {
  const boss=current.terra_boss;
  if(!boss)return '';
  const {raid,rewards}=boss;
  const admin=current.profile?.role==='admin';
  if(!raid&&!rewards.length&&!admin)return '';
  const rangers=Math.min(current.units.ranger||0,boss.max_rangers);
  const formatTime=seconds=>new Date(seconds*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE');
  const signup=raid?.can_join&&rangers>0?`<form data-boss-attack="${escapeHtml(raid.id)}"><p>Beim Angriff können Ranger verloren gehen. Überlebende kehren zur Ausgangskolonie zurück.</p><label>Ranger entsenden<input name="count" type="number" min="1" max="${Number(rangers)}" value="1" required></label><button>Angriff buchen</button></form>`:'';
  const schedule=admin&&!raid?'<form data-boss-schedule><label>Name des Weltbosses<input name="name" minlength="3" maxlength="48" required></label><button>Weltboss für diese Welt ansetzen</button></form>':'';
  const status=raid?.defeated_at?'Gemeinsam besiegt':raid?.starts>current.server_time?`Beginn ${formatTime(raid.starts)}`:raid?`Phase ${number(raid.phase)} · aktiv bis ${formatTime(raid.ends)}`:'';
  const progress=raid?`<h4>${escapeHtml(raid.name)}</h4><p>${status} · ${number(raid.booked)}/${number(boss.attack_slots)} Angriffsplätze belegt</p><label>Boss-Integrität <meter min="0" max="${Number(raid.health)}" value="${Number(raid.remaining_health)}">${number(raid.remaining_health)}</meter> ${number(raid.remaining_health)} / ${number(raid.health)}</label>${raid.joined?`<p>${raid.damage===null?'Dein Angriff ist unterwegs.':`Dein Beitrag: ${number(raid.damage)} Schaden.`}</p>`:''}${signup}`:'';
  const claims=rewards.map(reward=>`<li>${escapeHtml(reward.name)} · ${number(reward.ore)} Erz <button type="button" data-action="terra_boss_claim" data-key="${escapeHtml(reward.id)}">Belohnung abholen</button></li>`).join('');
  return `<section class="panel queue-panel" aria-labelledby="terra-boss-title"><h3 id="terra-boss-title">Kooperativer Weltboss</h3><p>Entwurfsbalance. Je Konto ist ein Angriff möglich. Nach dem gemeinsamen Sieg werden bis zu ${number(boss.reward_ore_pool)} Erz nach verursachtem Schaden verteilt.</p>${progress}${schedule}${claims?`<ul aria-label="Deine Boss-Belohnungen">${claims}</ul>`:''}</section>`;
}
function npcInvasionMarkup(current) {
  const events=current.npc_invasions;
  if(!events)return '';
  const {items,enabled}=events;
  const canSchedule=enabled&&current.profile?.role==='admin'&&!items.some(event=>event.status!=='ended');
  if(!items.length&&!canSchedule)return '';
  const labels={warning:'Warnphase',active:'Aktiv',ended:'Beendet'};
  const time=seconds=>new Date(seconds*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE');
  const history=items.map(event=>`<li><b>${escapeHtml(event.name)}</b> · ${labels[event.status]} · ${time(event.starts)} bis ${time(event.ends)}<p>${number(event.planned)}/${number(event.budget)} Angriffe angesetzt · ${number(event.resolved)} abgeschlossen · ${number(event.cancelled)} abgebrochen</p></li>`).join('');
  const schedule=canSchedule?'<form data-invasion-schedule><label>Name der Invasion<input name="name" minlength="3" maxlength="48" required></label><button>Invasion für diese Welt ansetzen</button></form>':'';
  return `<section class="panel queue-panel" aria-labelledby="npc-invasion-title"><h3 id="npc-invasion-title">NPC-Weltinvasion</h3><p>Entwurfsbalance. Während einer aktiven Invasion planen NPC-Lager Angriffe im angezeigten Budget. Persönliche Warnungen findest du unter NPC-Angriffsberichte auf der Karte.</p>${history?`<ul>${history}</ul>`:''}${schedule}</section>`;
}
function expeditionCatalogSummary(catalog) {
  if(!catalog?.outcome_rolls||!catalog.outcomes?.length)return 'Die Expeditionsregeln sind momentan nicht verfügbar.';
  const labels={discovery:'Fundort',cache:'Vorräte',skirmish:'Patrouille',hazard:'Geländegefahr',quiet:'Ereignislos'};
  const outcomes=catalog.outcomes.map(outcome=>{
    const chance=number(100*outcome.weight/catalog.outcome_rolls);
    const resources=outcome.resource_max?`, ${number(outcome.resource_min)}–${number(outcome.resource_max)} einer Rohstoffart vor Traglastprüfung`:'';
    const losses=outcome.loss_max_percent?`, ${number(outcome.loss_min_percent)}–${number(outcome.loss_max_percent)} % Verlustrate`:'';
    return `${labels[outcome.id]||'Ereignis'} ${chance} %${resources}${losses}`;
  });
  return `${catalog.version} · ${outcomes.join(' · ')}.`;
}
function queue() {
  if (!state.jobs.length) return '<p class="empty" data-i18n="queue.empty">Alle Systeme bereit. Starte einen neuen Auftrag.</p>';
  const types={build:'Ausbau',research:'Forschung',train:'Ausbildung',craft:'Fertigung',terra_repair:'Reparatur',raid:'Anmarsch',attack:'Spielerangriff',transport:'Transport',scout:'Aufklärung',expedition:'Expedition',ruin_exploration:'Ruinenerkundung',colony_supply:'Kolonieversorgung',alliance_supply:'Allianzversorgung',station:'Garnisonsmarsch',return:'Rückmarsch'};
  return [...state.jobs].sort((a,b)=>a.due-b.due).map(j=>{
    const upgrade=['build','research'].includes(j.kind), planned=upgrade?state.jobs.filter(item=>item.kind===j.kind).sort((a,b)=>(a.queue_order??-1)-(b.queue_order??-1)||a.due-b.due):[], position=planned.findIndex(item=>item.id===j.id);
    const section={build:'buildings',research:'tech',train:'units'}[j.kind];
    const key=section&&j.key?'catalog.'+section+'.'+j.key+'.name':'';
    const translated=key&&globalThis.FURI18n?.t(key);
    const displayLabel=translated&&translated!==key?translated:j.label;
    const label=`${j.kind==='build'?'Bauauftrag':'Forschungsauftrag'} ${j.label}`;
    const controls=upgrade?`${j.queued?`<button class="secondary" data-action="queue_move" data-direction="up" data-key="${escapeHtml(j.id)}" aria-label="${escapeHtml(label)} nach oben verschieben" data-i18n-aria-label="queue.move_up_label" data-i18n-values="${escapeHtml(JSON.stringify({label:displayLabel}))}" ${position<=1?'disabled':''}>↑</button><button class="secondary" data-action="queue_move" data-direction="down" data-key="${escapeHtml(j.id)}" aria-label="${escapeHtml(label)} nach unten verschieben" data-i18n-aria-label="queue.move_down_label" data-i18n-values="${escapeHtml(JSON.stringify({label:displayLabel}))}" ${position>=planned.length-1?'disabled':''}>↓</button>`:''}<button class="secondary" data-action="cancel_job" data-key="${escapeHtml(j.id)}" aria-label="${escapeHtml(label)} abbrechen" data-i18n-aria-label="queue.cancel_label" data-i18n-values="${escapeHtml(JSON.stringify({label:displayLabel}))}" data-i18n="queue.cancel">Abbrechen</button>`:j.kind==='craft'?`<button class="secondary" data-action="cancel_job" data-key="${escapeHtml(j.id)}" aria-label="${escapeHtml(displayLabel)} abbrechen und erstatten" data-i18n-aria-label="queue.refund_label" data-i18n-values="${escapeHtml(JSON.stringify({label:displayLabel}))}" data-i18n="queue.refund">Abbrechen und erstatten</button>`:j.kind==='terra_repair'?`<button class="secondary" data-action="cancel_job" data-key="${escapeHtml(j.id)}" aria-label="${escapeHtml(displayLabel)} abbrechen und erstatten" data-i18n-aria-label="queue.refund_label" data-i18n-values="${escapeHtml(JSON.stringify({label:displayLabel}))}" data-i18n="queue.refund">Abbrechen und erstatten</button>`:j.kind==='alliance_supply'?`<button class="secondary" data-action="alliance_supply_cancel" data-key="${escapeHtml(j.id)}" aria-label="${escapeHtml(label)} abbrechen" data-i18n-aria-label="queue.cancel_label" data-i18n-values="${escapeHtml(JSON.stringify({label:displayLabel}))}" data-i18n="queue.cancel">Abbrechen</button>`:['raid','attack','scout','transport','colony_supply','station','expedition','ruin_exploration'].includes(j.kind)?`<button class="secondary" data-action="mission_recall" data-key="${escapeHtml(j.id)}" aria-label="${escapeHtml(displayLabel)} zurückrufen" data-i18n-aria-label="queue.recall_label" data-i18n-values="${escapeHtml(JSON.stringify({label:displayLabel}))}" data-i18n="queue.recall">Zurückrufen</button>`:'';
    return `<div class="queue-item"><span class="pulse"></span><div><b>${escapeHtml(displayLabel)}${j.target_level?` · <span data-i18n="game.level">Stufe</span> ${j.target_level}`:''}</b><small><span data-i18n="queue.kind.${escapeHtml(j.kind)}">${types[j.kind]||'Auftrag'}</span>${j.queued?' · <span data-i18n="queue.waiting">Warteschlange</span>':''}</small></div><strong>${Math.max(0,j.due - state.server_time)}s</strong>${controls}</div>`;
  }).join('');
}
function colonySupplyMarkup() {
  const destinations = (state.colonies || []).filter(colony => !colony.selected && colony.world_id === state.colonies.find(item => item.selected)?.world_id);
  const allied = (state.alliance_supply_targets || []).filter(target => target.world_id === state.colonies.find(item => item.selected)?.world_id);
  const form = (id, selectId, targets, label) => `<form id="${id}"><label for="${selectId}">Empfangende Kolonie</label><select id="${selectId}" name="destination" required>${targets.map(target=>`<option value="${escapeHtml(target.colony_id)}">${escapeHtml(target.name)} · ${target.x}:${target.y}</option>`).join('')}</select><fieldset class="supply-fields"><legend>Träger aus ${escapeHtml(state.colony_name || state.name)} (verfügbar)</legend>${Object.entries(state.catalog.units).map(([key,item])=>`<label>${escapeHtml(item.name)}<input type="number" name="carrier-${key}" min="0" max="${state.units[key]}" value="0" inputmode="numeric"></label>`).join('')}</fieldset><fieldset class="supply-fields"><legend>Rohstoffe (verfügbar)</legend>${names.map((name,index)=>`<label>${name}<input type="number" name="cargo-${index}" min="0" max="${state.resources[index]}" value="0" inputmode="numeric"></label>`).join('')}</fieldset>${id === 'colony-supply-form' ? `<fieldset class="supply-fields"><legend>Materialwaren (verfügbar)</legend>${(state.neutral_market?.goods||[]).filter(good=>!['wood','stone','ore'].includes(good.id)).map(good=>`<label>${escapeHtml(good.name)}<input type="number" name="goods-${escapeHtml(good.id)}" min="0" max="${good.amount}" value="0" inputmode="numeric"></label>`).join('')}</fieldset><fieldset class="supply-fields"><legend>Gegenstände (verfügbar)</legend>${(state.generic_items?.items||[]).map(item=>`<label>${escapeHtml(item.name)}<input type="number" name="item-${escapeHtml(item.id)}" min="0" max="${item.amount}" value="0" inputmode="numeric"></label>`).join('')}</fieldset>` : ''}<button type="submit">${label} →</button>${id === 'colony-supply-form' ? '<label>Routenintervall in Stunden <input name="route_hours" type="number" min="1" max="168" value="24"></label><button type="submit" data-create-route>Als Handelsroute planen</button>' : ''}</form>`;
  const ownMarkup = destinations.length ? `<article class="panel queue-panel"><h3>Versorgung zwischen eigenen Kolonien</h3><p>Die aktive Kolonie entsendet Rohstoffe und Materialwaren mit Trägern. Materialwaren werden bei Ankunft im Zieldepot eingelagert; die Träger kehren anschließend zurück.</p>${form('colony-supply-form','supply-destination',destinations,'Versorgung entsenden')}</article>` : '<article class="panel queue-panel"><h3>Kolonieversorgung</h3><p>Gründe zuerst eine zweite Kolonie in derselben Welt, um Fracht zu senden.</p></article>';
  const allianceMore = state.alliance_supply_targets_has_more ? '<button type="button" class="secondary" data-alliance-supply-more>Weitere Allianzmitglieder laden</button><p role="status" data-alliance-supply-status aria-live="polite"></p>' : '';
  const allianceMarkup = state.membership && (allied.length || state.alliance_supply_targets_has_more) ? `<article class="panel queue-panel"><h3>Allianzversorgung</h3><p>Schicke Fracht über die Geländeroute an die Heimatkolonie eines Allianzmitglieds derselben Welt. Die Lieferung wird bei Ankunft gutgeschrieben; bis dahin kannst du sie abbrechen. Verlässt ein Beteiligter die Allianz vor Ankunft, wird die Fracht erstattet.</p>${form('alliance-supply-form','alliance-supply-destination',allied,'Allianzversorgung entsenden')}${allianceMore}</article>` : '';
  const routes = (state.terra_trade_routes || []).map(route => `<li>${escapeHtml(destinations.find(target => target.colony_id === route.target)?.name || route.name_key)} · alle ${number(route.interval_seconds/3600)} h · ${route.paused ? escapeHtml(route.reason) : new Date(route.due*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}
    ${route.paused ? `<button type="button" data-terra-route-action="terra_route_resume" data-terra-route-id="${escapeHtml(route.id)}">Fortsetzen</button>` : ''}
    <button type="button" data-terra-route-action="terra_route_stop" data-terra-route-id="${escapeHtml(route.id)}">Route beenden</button></li>`).join('');
  const fortify = state.faction_research?.includes('kinetic_shield') && allied.length
    ? `<form id="warden-fortify-form"><h3>Wächterbefestigung</h3>
      <p>200 Erz für zehn Prozent zusätzliche Verteidigung einer verbündeten Kolonie während einer Stunde.</p>
      <label>Zielkolonie <select name="target">${allied.map(target => `<option value="${escapeHtml(target.colony_id)}">${escapeHtml(target.name)}</option>`).join('')}</select></label>
      <button ${state.resources[2] < 200 || (state.warden_fortify_ready_at || 0) > state.server_time ? 'disabled' : ''}>Kolonie befestigen</button></form>` : '';
  const activeFortification = state.warden_fortified ? '<p>Wächterbefestigung aktiv.</p>' : '';
  return ownMarkup + (routes ? `<article class="panel queue-panel"><h3>Dauerhafte Handelsrouten</h3><ul>${routes}</ul></article>` : '') + allianceMarkup + fortify + activeFortification;
}
function combatIntelKnown(target, player, own, now) {
  if (player) return Boolean(target.intel_report?.status === 'fresh' && target.intel_report.level >= 2 && target.intel_report.data?.defense !== undefined && target.intel_report.expires_at > now);
  return (!target.owner || own) && target.intel_level !== 'unknown';
}
function scoutMissionRisk(activeWorld) {
  if (activeWorld?.terra_combat_ruleset?.startsWith('FUR-3-TERRA-COMBAT-')) {
    return 'Nur Ranger fliegen Aufklärung. FUR-3-Gegenaufklärung kann dich entdecken; bei einem Abfang verlierst du einen Ranger und erhältst keine neuen Zieldaten. Der Verteidiger erhält nur einen allgemeinen Alarm. Überlebende Ranger kehren zurück.';
  }
  return 'Nur Ranger fliegen Aufklärung. Der Bericht bleibt privat; Ranger kehren nach der Ankunft zurück.';
}
function missionTemplateOptions(templates) {
  const modes={attack:'Angriff',scout:'Aufklärung',transport:'Transport',station:'Garnison',expedition:'Expedition'};
  return '<option value="">Vorlage wählen</option>'+templates.map(template=>`<option value="${escapeHtml(template.id)}">${escapeHtml(template.name)} · ${modes[template.mode]||'Mission'}</option>`).join('');
}
function directivesMarkup() {
  return state.quests.map(q=>{
    const claimed=state.claimed.includes(q.id), unlocked=q.unlocked!==false;
    const statusKey=claimed?'claimed':!unlocked?'locked_detail':q.done?'ready':'open';
    const labelKey=claimed?'complete':!unlocked?'locked':q.done?'claim':'open';
    const titleKey='quest.name.'+q.id;
    const translated=globalThis.FURI18n?.t(titleKey);
    const title=translated&&translated!==titleKey?translated:q.name;
    const status=claimed?'Erfüllt':!unlocked?'Gesperrt · zuerst die vorherige Direktive abholen':q.done?'Bereit zur Abholung':'Offen';
    const label=claimed?'✓':!unlocked?'Gesperrt':q.done?'Abholen':'Offen';
    return `<div class="quest">${assetImage(`orbit/campaign/campaign_directive_${String(state.quests.indexOf(q)+1).padStart(2,'0')}`,title,'directive-art')}<div><b>${escapeHtml(title)}</b><small><span data-i18n="quest.reward" data-i18n-values="${escapeHtml(JSON.stringify({amount:number(q.reward)}))}">Belohnung: je ${number(q.reward)} Rohstoffe</span> · <span data-i18n="quest.${statusKey}">${status}</span></small></div><button data-quest="${escapeHtml(q.id)}" data-i18n="quest.${labelKey}" aria-label="${escapeHtml(title)}: ${label}" data-i18n-aria-label="quest.claim_label" data-i18n-values="${escapeHtml(JSON.stringify({name:title}))}" ${!q.done||!unlocked||claimed?'disabled':''}>${label}</button></div>`;
  }).join('');
}
function recurringQuestMarkup(program, isAdmin) {
  if (!program || (!program.enabled && !program.quests.length && !isAdmin)) return '';
  const resetFormat = new Intl.DateTimeFormat(globalThis.FURI18n?.locale || 'de-DE', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC'
  });
  const groups = [['daily', 'Tagesaufgaben'], ['weekly', 'Wochenaufgaben']].map(([period, title]) => {
    const quests = program.quests.filter(quest => quest.period === period);
    if (!quests.length) return '';
    const rows = quests.map(quest => {
      const completed = quest.progress >= quest.target;
      const titleKey='recurring.name.'+quest.id;
      const translated=globalThis.FURI18n?.t(titleKey);
      const title=translated&&translated!==titleKey?translated:quest.title;
      const reward = quest.reward.map((amount, index) => `${number(amount)} ${names[index]}`).join(' · ');
      const status = quest.claimed ? 'Abgeholt' : completed ? 'Bereit zur Abholung' : 'Offen';
      const button = completed && !quest.claimed
        ? `<button type="button" data-action="recurring_quest_claim" data-key="${escapeHtml(quest.key)}" aria-label="${escapeHtml(title)} – Belohnung abholen" data-i18n-aria-label="recurring.claim_label" data-i18n-values="${escapeHtml(JSON.stringify({name:title}))}" data-i18n="quest.claim">Abholen</button>`
        : '';
      return `<li><div class="quest"><div><b>${escapeHtml(title)}</b><small>${number(quest.progress)} / ${number(quest.target)} · <span data-i18n="${quest.claimed?'quest.claimed':completed?'quest.ready':'quest.open'}">${status}</span></small><small>${reward}</small></div>${button}</div></li>`;
    }).join('');
    const end = new Date(quests[0].ends * 1000);
    return `<h4 data-i18n="recurring.${period}">${title}</h4><p><span data-i18n="recurring.ends">Endet am</span> <time datetime="${end.toISOString()}">${resetFormat.format(end)} UTC</time>.</p><ul>${rows}</ul>`;
  }).join('');
  const admin = isAdmin
    ? `<button type="button" data-i18n="${program.enabled?'recurring.pause':'recurring.enable'}" data-recurring-quests-enabled="${!program.enabled}">${program.enabled ? 'Für diese Welt pausieren' : 'Für diese Welt aktivieren'}</button>`
    : '';
  const paused = program.enabled ? '' : '<p data-i18n="recurring.paused">Die Aufgaben sind in dieser Welt pausiert. Verdiente Belohnungen können bis zum Periodenende abgeholt werden.</p>';
  return `<section class="panel queue-panel" aria-labelledby="recurring-quests-title"><h3 id="recurring-quests-title" data-i18n="recurring.title">Wiederkehrende Aufgaben</h3>${paused}${groups}${admin}</section>`;
}
function combatReportMarkup(combat) {
  if (!combat || !Array.isArray(combat.rounds)) return '';
  const defenseNames={kinetic_turret:'Kinetikgeschütz',aegis_emitter:'Aegis-Emitter',command_bunker:'Gefechtsbunker'};
  const structureName=id=>{const profile=/^furdef_(kinetic_turret|aegis_emitter|command_bunker)_\d+$/.exec(id);return profile?defenseNames[profile[1]]:null;};
  const sideMarkup=(label,side)=>{
    const units=Object.keys(side?.sent||{});
    if(!units.length)return `<p><strong>${label}:</strong> <span data-i18n="combat.no_troops">keine Truppen</span></p>`;
    return `<p><strong>${label}:</strong> ${units.map(key=>{
      const name=escapeHtml(state.catalog?.units?.[key]?.name||(structureName(key)||(key==='outpost_fortification'?'Außenpostenbefestigung':key)));
      const sent=Number(side.sent[key]||0),losses=Number(side.losses?.[key]||0),survivors=Number(side.survivors?.[key]||0);
      return `${name}: ${number(sent)} <span data-i18n="combat.sent">eingesetzt</span> · ${number(losses)} <span data-i18n="combat.lost">verloren</span> · ${number(survivors)} <span data-i18n="combat.survived">überlebt</span>`;
    }).join(' — ')}</p>`;
  };
  const defense=combat.terra_defense;
  const hasMine=(defense?.initial_stacks?.proximity_mines||[]).some(integrity=>Number(integrity)>0);
  const defenseMarkup=defense?`<section aria-label="Kolonieverteidigung"><h4 data-i18n="combat.colony_defense">Kolonieverteidigung</h4>${hasMine?`<p>${defense.minefield?.triggered?'Annäherungsminen ausgelöst; ein Minenfeld wurde verbraucht und der Angriffsschaden reduziert.':'Minenfeld nicht ausgelöst.'}</p>`:''}${Object.entries(defense.structure_remaining||{}).map(([id,integrity])=>`<p>${escapeHtml(structureName(id)||id)}: ${number(integrity)} % Integrität</p>`).join('')}</section>`:'';
  const outcome=combat.outcome?` · ${combat.outcome==='attacker_win'?'Sieg':combat.outcome==='defender_win'?'Niederlage':combat.outcome==='attacker_retreat'?'Rückzug':'Unentschieden'}`:'';
  return `<details class="combat-report"><summary><span data-i18n="combat.details">Gefechtsdetails</span> · ${escapeHtml(combat.alliance_rules_version||combat.rules_version||'Regelstand unbekannt')}${outcome}${combat.alliance_rules_digest?` · SHA-256 ${escapeHtml(combat.alliance_rules_digest.slice(0,12))}`:combat.rules_digest?` · SHA-256 ${escapeHtml(combat.rules_digest.slice(0,12))}`:''}</summary>${combat.rounds.slice(0,6).map(round=>`<section aria-label="Runde ${number(round.round)}"><h4>Runde ${number(round.round)} · ${round.victory===undefined?'Gefechtsphase':round.victory?'Sieg':'Niederlage'} · Angriff ${number(round.attack_power)} / Verteidigung ${number(round.defense_power)}</h4><p>${escapeHtml(combat.participants?.attacker||'Angreifer')} gegen ${escapeHtml(combat.participants?.defender||'Verteidiger')}</p>${Array.isArray(round.attacker_wings)?round.attacker_wings.map(wing=>sideMarkup(`Trupp von ${escapeHtml(wing.commander||'Allianzmitglied')}`,wing)).join(''):sideMarkup('Angreifer',round.attacker)}${sideMarkup('Verteidiger',round.defender)}<p><span data-i18n="combat.loot">Beute:</span> ${(round.loot||[]).slice(0,3).map((amount,index)=>`${icons[index]} ${number(amount)}`).join(' · ')}</p></section>`).join('')}${defenseMarkup}</details>`;
}
function allianceViewMarkup() {
  const member=state.membership;
  const alliance=(state.alliances||[]).find(item=>item.id===member?.alliance_id);
  const canManage=Boolean(member&&['leader','officer'].includes(member.role));
  const invitations=(state.invites||[]).map(invite=>`<article class="quest"><div><b>${escapeHtml(invite.name)} [${escapeHtml(invite.tag)}]</b><small>${member?'Verlasse zuerst deine Allianz, um anzunehmen.':'Einladung zu dieser Allianz.'}</small></div>${member?'':`<button data-action="alliance_accept" data-key="${escapeHtml(invite.id)}">Annehmen</button>`}<button class="secondary" data-action="alliance_invite_decline" data-key="${escapeHtml(invite.id)}">Ablehnen</button></article>`).join('');
  const applications=state.alliance_applications||[];
  if (!member) {
    const applicationsByAlliance=new Map(applications.map(application=>[application.alliance_id,application]));
    const alliances=(state.alliances||[]).map(alliance=>{const application=applicationsByAlliance.get(alliance.id);return `<li><strong>${escapeHtml(alliance.name)} [${escapeHtml(alliance.tag)}]</strong> · ${number(alliance.size)} Mitglieder ${application?`<button class="secondary compact" data-action="alliance_application_withdraw" data-key="${escapeHtml(application.id)}">Bewerbung zurücknehmen</button>`:`<button class="compact" data-action="alliance_apply" data-key="${escapeHtml(alliance.id)}">Bewerben</button>`}</li>`;}).join('');
    const myApplications=applications.map(application=>`<li>${escapeHtml(application.name)} [${escapeHtml(application.tag)}] · Bewerbung offen <button class="secondary compact" data-action="alliance_application_withdraw" data-key="${escapeHtml(application.id)}">Zurücknehmen</button></li>`).join('');
    return `<div class="section-intro"><p class="eyebrow">DIPLOMATIE / GEMEINSCHAFT</p><h1>Allianzen</h1><p>Gründe einen Bund, bewirb dich oder verwalte deine persönlichen Einladungen.</p></div>${invitations?`<article class="panel queue-panel"><h2>Offene Einladungen</h2>${invitations}</article>`:''}${myApplications?`<article class="panel queue-panel"><h2>Deine Bewerbungen</h2><ul>${myApplications}</ul></article>`:''}<article class="panel queue-panel"><h2>Allianz gründen</h2><form id="alliance-create-form"><label for="alliance-create-tag">Kürzel (3–8 Zeichen)</label><input id="alliance-create-tag" name="tag" minlength="3" maxlength="8" pattern="[A-Za-z0-9]{3,8}" required><label for="alliance-create-name">Name (3–30 Zeichen)</label><input id="alliance-create-name" name="name" minlength="3" maxlength="30" required><button>Allianz gründen →</button></form></article><article class="panel queue-panel"><h2>Allianzen · Bewerben</h2><ul>${alliances||'<li>Es gibt noch keine Allianzen.</li>'}</ul></article>`;
  }
  const members=(state.members||[]).map(other=>`<li><strong>${escapeHtml(other.name)}</strong> · ${other.role==='leader'?'Leitung':other.role==='officer'?'Offizier':'Mitglied'}${member.role==='leader'&&other.user_id!==state.id&&other.role!=='leader'?` <button type="button" class="compact" data-alliance-transfer="${escapeHtml(other.user_id)}" data-member-name="${escapeHtml(other.name)}">Führung übertragen</button>`:''}</li>`).join('');
  const outgoing=canManage?(state.alliance_outgoing_invites||[]).map(invite=>`<article class="quest"><div><b>${escapeHtml(invite.name)}</b><small>Einladung noch offen</small></div><button type="button" class="secondary" data-action="alliance_invite_cancel" data-key="${escapeHtml(invite.id)}">Einladung zurücknehmen</button></article>`).join(''):'';
  const incomingApplications=canManage?(state.alliance_incoming_applications||[]).map(application=>`<article class="quest"><div><b>${escapeHtml(application.name)}</b><small>Bewerbung eingegangen</small></div><button data-action="alliance_application_accept" data-key="${escapeHtml(application.id)}">Aufnehmen</button><button class="secondary" data-action="alliance_application_reject" data-key="${escapeHtml(application.id)}">Ablehnen</button></article>`).join(''):'';
  const candidates=state.alliance_candidates||[];
  const inviteForm=canManage?`<form id="alliance-invite-form"><label for="alliance-invite-player">Spieler auswählen</label><select id="alliance-invite-player" name="player" required>${candidates.map(player=>`<option value="${escapeHtml(player.name)}">${escapeHtml(player.name)}</option>`).join('')}</select><button ${candidates.length?'':'disabled'}>Einladung senden →</button></form>`:'<p>Nur Leitung und Offiziere können Mitglieder einladen.</p>';
  const homePolicy=state.alliance_garrison_home_colony_id===state.colony_id;
  const policy=state.alliance_garrison_policy||{enabled:false,capacity:300};
  const policyPanel=homePolicy?`<article class="panel queue-panel"><h2>Verteidigung deiner Heimat teilen</h2><p>Du entscheidest je Allianz, ob Mitglieder Truppen stationieren dürfen. Bis zu 300 Einheiten; das Deaktivieren ruft bereits eingetroffene Garnisonen zurück.</p><form id="alliance-garrison-policy-form"><label><input name="enabled" type="checkbox" ${policy.enabled?'checked':''}> Alliierte Garnisonen erlauben</label><label>Gesamtkapazität<input name="capacity" type="number" min="1" max="300" value="${number(policy.capacity||300)}" required></label><button>Freigabe speichern</button></form></article>`:'';
  const garrisonTargets=state.alliance_garrison_targets||[];
  const garrisonUnits=Object.keys(state.units||{}).map(unit=>`<label>${escapeHtml(state.catalog?.units?.[unit]?.name||unit)}<input name="unit-${escapeHtml(unit)}" type="number" min="0" max="${number(state.units[unit])}" value="0"></label>`).join('');
  const garrisonPanel=member?`<article class="panel queue-panel"><h2>Alliierte Garnisonen</h2><p>Truppen werden bis zur Ankunft gebunden. Zustimmung, Allianz und freie Kapazität werden beim Eintreffen erneut geprüft. Verluste bleiben dem jeweiligen Konto zugeordnet.</p>${garrisonTargets.length?`<form id="alliance-garrison-form"><label>Ziel-Heimatkolonie<select name="target" required>${garrisonTargets.map(target=>`<option value="${escapeHtml(target.colony_id)}">${escapeHtml(target.host_name)} · ${escapeHtml(target.name)} · Kapazität ${number(target.capacity)}</option>`).join('')}</select></label>${garrisonUnits}<button>Garnison entsenden</button></form>`:'<p>Kein Allianzmitglied hat eine Heimatkolonie für Garnisonen freigegeben.</p>'}${(state.alliance_garrisons||[]).length?`<h3>Stationierte und anreisende Einheiten</h3><ul>${state.alliance_garrisons.map(g=>`<li>${escapeHtml(g.contributor_name)} → ${escapeHtml(g.host_name)} · ${g.status==='active'?'stationiert':'anreisend'} · ${Object.entries(g.army).map(([unit,count])=>`${number(count)} ${escapeHtml(state.catalog?.units?.[unit]?.name||unit)}`).join(', ')} ${g.can_recall?`<button type="button" class="secondary" data-action="alliance_garrison_recall" data-key="${escapeHtml(g.id)}">Zurückrufen</button>`:''}</li>`).join('')}</ul>`:''}</article>`:'';
  return `<div class="section-intro"><p class="eyebrow">DIPLOMATIE / GEMEINSCHAFT</p><h1>${escapeHtml(alliance?.name||'Deine Allianz')}</h1><p>Kürzel ${escapeHtml(alliance?.tag||'')} · Deine Rolle: ${member.role==='leader'?'Leitung':member.role==='officer'?'Offizier':'Mitglied'}.</p></div>${invitations?`<article class="panel queue-panel"><h2>Weitere Einladungen</h2>${invitations}</article>`:''}${policyPanel}${garrisonPanel}<div class="columns"><article class="panel queue-panel"><h2>Mitglieder</h2><ul>${members}</ul>${member.role==='leader'?'<p>Übertrage die Führung, bevor du die Allianz verlässt.':''}<button type="button" class="secondary" data-action="alliance_leave">Allianz verlassen</button>${incomingApplications?`<h3>Bewerbungen</h3>${incomingApplications}`:''}</article><article class="panel queue-panel"><h2>Mitglieder einladen</h2>${inviteForm}${outgoing?`<h3>Offene Einladungen</h3>${outgoing}`:''}</article></div>`;
}
function render() {
  if (!state) return;
  globalThis.FURI18n?.localizeCatalog(state.catalog);
  const cap = 2000 + state.buildings.storage * 2000;
  $('active-world-label').textContent = activeWorldLabel(state.active_world);
  $('active-world-footer').textContent = `${state.active_world?.name || 'Genesis'} · STRATEGIESPIEL`;
  document.querySelector('[data-tab=admin]').hidden = !state.administration;
  $('resources').innerHTML = state.resources.map((r,i) => { const detail=state.production_details?.[i], rate=detail?.per_second_hundredths ?? state.production[i], fill=detail?.seconds_to_cap; return `<div><span>${resourceIcon(i)} ${names[i]}</span><b>${number(r)}</b><small title="${detail ? `Basis ${detail.base_per_second}/s, Bonus ${detail.bonus_percent}%, Gelände ${detail.terrain} ${detail.terrain_percent}%` : ''}">+${((detail?.per_second_ten_thousandths ?? rate*100)/10000).toFixed(1)}/s · ${detail?.terrain || 'Gelände'}${detail?.paused ? (state.terra_dormant ? ' · Ruhemodus' : ' · Urlaubspause') : fill === null ? '' : typeof fill === 'number' ? ` · voll in ${number(Math.ceil(fill/60))} min` : ''} · ${number(detail?.storage_cap ?? cap)} max.</small></div>`; }).join('') + productionGraphMarkup(state.production_details);
  $('sync').textContent = state.incoming_count ? '⚑ '+state.incoming_count+' feindliche Anmärsche' : '● Synchronisiert';
  let html = '';
  if (systemTabs.includes(tab)) { html = systemsView(); } else if (tab === 'overview') {
      html = `<div class="hero"><div><p class="eyebrow">SEKTOR ${state.x} : ${state.y} / FUR-KOLONIE</p><h1 data-i18n="overview.heading">Die Grenze gehört dir.</h1><p data-i18n="overview.welcome" data-i18n-values="${escapeHtml(JSON.stringify({name:state.name}))}">Willkommen zurück, ${escapeHtml(state.name)}.<br>Dein nächster Zug verändert diese Welt.</p><button data-goto="map" data-i18n="overview.map">Weltkarte öffnen ↗</button></div><div class="city-art" aria-hidden="true"><div class="orbit"></div><div class="tower t1"></div><div class="tower t2"></div><div class="tower t3"></div><div class="tower t4"></div><div class="ground"></div><span>FUR // OUTPOST 01</span></div></div><div class="stats"><article><small data-i18n="overview.power">IMPERIUMSMACHT</small><strong>${number(state.ranking_score||0)}</strong><span data-i18n="overview.power_detail">Ausbau · Wissen · Eroberungen</span></article><article><small data-i18n="overview.garrison">GARNISON</small><strong>${number(Object.values(state.units).reduce((a,b)=>a+b,0))}</strong><span data-i18n="overview.units_ready">Einheiten einsatzbereit</span></article><article><small data-i18n="overview.outposts">AUSSENPOSTEN</small><strong>${state.captures} <em>/ ${state.world.length}</em></strong><span data-i18n="overview.control">Unter deiner Kontrolle</span></article></div><div class="columns"><article class="panel"><div class="panel-title"><h3 data-i18n="overview.operations">Operationszentrale</h3><span>LIVE</span></div>${queue()}</article><article class="panel"><div class="panel-title"><h3 data-i18n="overview.directives">Deine Direktiven</h3><span data-i18n="overview.campaign_order">KAMPAGNE · IN REIHENFOLGE</span></div>${directivesMarkup()}</article></div>${state.citadel ? '<div class="victory"><h2 data-i18n="overview.victory">Der Kern gehört FUR.</h2><p>Kampagne gewonnen! Du kannst dein Imperium weiter ausbauen.</p></div>' : ''}`;
  } else if (tab === 'buildings' || tab === 'research') {
    const build = tab === 'buildings', catalog = state.catalog[build ? 'buildings' : 'tech'], levels = state[build ? 'buildings' : 'tech'];
    html = `<div class="section-intro"><p class="eyebrow">${build ? 'ENTWICKLUNG / INFRASTRUKTUR' : 'ENTWICKLUNG / TECHNOLOGIEN'}</p><h1 data-i18n="${build ? 'game.build_heading' : 'game.research_heading'}">${build ? 'Ein Fundament für Macht.' : 'Wissen ist dein Vorteil.'}</h1><p data-i18n="${build ? 'game.build_description' : 'game.research_description'}">Jeder Ausbau stärkt deinen Außenposten. Maximalstufe: 10. Bis zu fünf Aufträge je Warteschlange.</p></div>${productionTemplatePanel(build?'build':'research')}<div class="cards">${Object.entries(catalog).map(([key,item]) => { const queueKind=build?'build':'research', queueJobs=state.jobs.filter(j=>j.kind===queueKind), projected=levels[key]+queueJobs.filter(j=>j.key===key).length, full=queueJobs.length>=5, maxed=projected>=10; return `<article class="card"><div class="card-top">${assetImage(gameAssetKey(build?'buildings':'research',key),item.name,'catalog-art') || `<span class="building-icon">${item.icon || '⌬'}</span>`}<span class="level"><span data-i18n="game.level">STUFE</span> ${levels[key]}${projected>levels[key]?` · geplant ${projected}`:''}</span></div><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description)}</p>${itemPrerequisites(item).length?`<small><span data-i18n="game.requirements">Voraussetzungen:</span>${itemPrerequisitesLabel(item)}</small>`:''}<div class="cost">${cost(item,projected)}</div><button data-i18n="${maxed ? 'game.queue_max' : full ? 'game.queue_full' : 'game.queue_add'}" data-action="${queueKind}" data-key="${key}" ${full || maxed || !itemPrerequisitesMet(item) ? 'disabled' : ''}>${maxed ? 'Maximum geplant' : full ? 'Warteschlange voll' : 'In Warteschlange →'}</button></article>`; }).join('')}</div><article class="panel queue-panel"><h3 data-i18n="game.planning">Bau- und Forschungsplanung</h3>${queue()}</article>${build?terraDefenseMarkup():''}`;
  } else if (tab === 'army') {
    html = `<div class="section-intro"><p class="eyebrow">VERTEIDIGUNG / MOBILISIERUNG</p><h1 data-i18n="game.army_heading">Stärke zeigt Wirkung.</h1><p><span data-i18n="game.army_description">Truppen benötigen eine Kaserne. Kämpfende Einheiten sind bis zur Rückkehr gebunden.</span>${state.active_world?.terra_combat_ruleset==='FUR-3-TERRA-COMBAT-4'?' COMBAT-4 ist ein vorläufiger Regelentwurf; neue Rosterprofile bleiben gesperrt, bestehende Einheiten bleiben verfügbar.':state.active_world?.terra_combat_ruleset==='FUR-3-TERRA-COMBAT-5'?' COMBAT-5 ergänzt beschädigbare neutrale Festungen; sie regenerieren um 2 % ihrer maximalen Integrität je Minute. Der Regelstand ist vorläufig.':''}</p></div>${terraRecoveryMarkup()}${productionTemplatePanel('train')}<div class="cards">${Object.entries(state.catalog.units).filter(([key])=>key!=='outpost_fortification'&&(!state.faction_unit_requirements?.[key] || state.faction_unit_requirements[key].own_faction || state.units[key]>0)).map(([key,item]) => `<article class="card"><div class="card-top">${assetImage(gameAssetKey('units',key),item.name,'catalog-art') || `<span class="building-icon">${key === 'mech' ? '♜' : key === 'sentinel' ? '⬡' : '⚑'}</span>`}<span class="level">${state.units[key]} <span data-i18n="game.ready">BEREIT</span></span></div><h3>${escapeHtml(item.name)}</h3><p data-i18n="game.unit_stats" data-i18n-values="${escapeHtml(JSON.stringify({power:item.power,level:item.require,seconds:item.time}))}">Kampfkraft ${item.power} · Kaserne Stufe ${item.require} · Ausbildungszeit: ${item.time}s je Einheit</p><div class="cost">${cost(item)} / Einheit</div><form data-train="${key}"><label><span data-i18n="game.count">Anzahl</span><input name="count" type="number" value="5" min="1" max="100" required></label><button ${!canTrainUnit(key) || !itemPrerequisitesMet(item) || state.jobs.some(j=>j.kind==='train') ? 'disabled' : ''} data-i18n="game.recruit">Rekrutieren →</button></form></article>`).join('')}</div><article class="panel queue-panel"><h3 data-i18n="game.movements">Truppenbewegungen</h3>${queue()}</article>`;
  } else if (tab === 'colonies') {
    const worlds=(state.worlds||[]).map(world=>`<article class="panel colony-card"><p class="eyebrow">WELT ${world.id} · ${({permanent:"Dauerwelt",season:"Saisonwelt",sandbox:"Sandbox"})[world.mode]||"Dauerwelt"}</p><h2>${escapeHtml(world.name)}</h2><p>${world.joinable?'Spielerbeitritt geöffnet':'Keine neuen Spieler'} · ${number(world.player_count||0)} Kommandant(en) · ${world.has_colony?'Deine Kolonie vorhanden':'Noch ohne deine Kolonie'}</p>${worldRulesSummaryMarkup(world)}${world.id===state.active_world.id?`<strong class="selected-colony">Aktive Welt</strong><p><button type="button" data-goto="ranking">Rangliste dieser Welt öffnen →</button></p>${seasonSummaryMarkup(state)}`:world.has_colony?`<button data-action="world_select" data-world-id="${world.id}">Welt betreten →</button>`:world.joinable?`<button data-action="world_join" data-world-id="${world.id}">Kolonie gründen und beitreten →</button>`:''}${state.profile.role==='admin'?worldSettingsMarkup(world):''}</article>`).join('');
    const worldCreate=state.profile.role==='admin'?`<article class="panel queue-panel"><h3 data-i18n="section.new_world">Neue Welt anlegen</h3><form id="world-create-form"><label>Weltname<input name="name" minlength="3" maxlength="48" required></label><label>Seed<input name="seed" type="number" min="0" value="504921" required></label><label>Außenposten<input name="outposts" type="number" min="8" max="300" value="104" required></label><label>Weltmodus<select name="mode"><option value="permanent">Dauerwelt</option><option value="season">Saisonwelt</option><option value="sandbox">Sandbox · ohne PvP und Saison</option></select></label><label><input name="joinable" type="checkbox" checked>Beitritt erlauben</label>${worldCreationRulesMarkup()}<button>Welt generieren →</button></form></article>`:'';
    const worldMore=state.worlds_has_more?'<button type="button" class="secondary" data-worlds-more>Weitere Welten laden</button><p role="status" data-worlds-status aria-live="polite"></p>':'';
    const colonyMore=state.empire_colonies_has_more?'<button type="button" class="secondary" data-colonies-more>Weitere Kolonien laden</button><p role="status" data-colonies-status aria-live="polite"></p>':'';
    html = `<div class="section-intro"><p class="eyebrow">IMPERIUM / KOLONIEN</p><h1 data-i18n="section.colonies_heading">Alle Basen. Ein Imperium.</h1><p>Jede Kolonie besitzt eigene Rohstoffe, Gebäude, Forschung, Truppen und Aufträge. Von hier aus planst du Rohstoffversorgung zwischen deinen Basen; deine Träger kehren nach der Lieferung zurück.</p></div><h2 data-i18n="section.worlds">Spielwelten</h2><div class="colony-grid">${worlds||'<article class="panel">Keine Welten verfügbar.</article>'}</div>${worldMore}${worldCreate}${orbitAccessMarkup(state.orbit_access)}<h2 data-i18n="section.colonies">Kolonien</h2><div class="colony-grid">${(state.empire_colonies||[]).map(c=>`<article class="panel colony-card"><p class="eyebrow">${c.is_home?'HAUPTKOLONIE':'AUSSENKOLONIE'} · SEKTOR ${c.x}:${c.y}</p><h2>${escapeHtml(c.name)}</h2><p>Kommandozentrale Stufe ${c.hq} · Welt ${c.world_id}</p>${colonyRenameMarkup(c)}${colonyHomeMarkup(c)}${colonyAbandonMarkup(c)}${c.selected?'<strong class="selected-colony">Aktiv verwalten</strong>':`<button data-action="colony_select" data-key="${escapeHtml(c.colony_id)}">Diese Kolonie verwalten →</button>`}</article>`).join('')}</div>${colonyMore}<article class="panel queue-panel"><h3 data-i18n="section.slots">Kolonieslots</h3><p>${state.colony_count} von ${state.colony_slot_limit} verfügbaren Basen belegt. Slots steigen mit der Kommandozentrale der aktiven Kolonie (ein zusätzlicher Slot je drei Stufen, höchstens vier).</p><p>Die Weltkarte erlaubt die Gründung auf einem freien Sektor. Kosten: 2.000 Holz, 1.500 Stein und 1.000 Erz; Mindestabstand zu anderen Kolonien: sechs Sektoren.</p></article>${colonySupplyMarkup()}`;
  } else if (tab === 'map') {
    const bookmarks = new Set(state.map_bookmarks || []);
    const routeTarget = state.world.find(town=>town.id===mapRouteId&&bookmarks.has(town.id));
    const route = routeTarget ? knownTerrainRoute(state.terrain_map,state.catalog?.terrain,[state.x,state.y],[routeTarget.x,routeTarget.y]) : null;
    const routeTiles = new Set((route||[]).map(([x,y])=>`${x}:${y}`));
    const tiles = [];
    for (const [x,y] of mapCoordinates(mapX,mapY)) {
      const town = state.world.find(t=>t.x===x && t.y===y), ownColony = (state.colonies||[]).find(c=>c.x===x&&c.y===y), home = Boolean(ownColony), activeHome = ownColony?.selected, player = state.players.find(p=>p.x===x&&p.y===y&&p.id!==state.id);
      const sectorIntel = state.sector_intel?.[`${x}:${y}`];
      const terrain = state.terrain_map?.[`${x}:${y}`] || 'unknown';
      const terrainIcon = ({plain:'·',forest:'♣',water:'≈',mountain:'▲',pass:'⌁'})[terrain];
      const bookmarked = isMapBookmarked(bookmarks, town?.id);
      const onRoute = routeTiles.has(`${x}:${y}`);
      const terrainRule=state.catalog?.terrain?.[terrain];
      const terrainName=terrain==='unknown'?'Unbekannt':terrainRule?.name || ({plain:'Ebene',forest:'Wald',water:'Wasser · unpassierbar',mountain:'Gebirge',pass:'Pass'})[terrain];
      const visibility=sectorIntel?.status || 'unknown';
      const ruin = state.terra_ruins?.[`${x}:${y}`] > state.server_time;
      const markerKey = terrain==='unknown'?'terra/fog/fog_unknown':home?'terra/markers/colony_own':player?'terra/markers/colony_foreign':town?(town.owner?'terra/markers/outpost_occupied':town.tier===8?'terra/markers/citadel_boss':'terra/markers/outpost_neutral'):ruin?'terra/markers/ruin':onRoute?'terra/markers/attack':'';
      const markerAlt = home?'Eigene Kolonie':player?'Fremde Kolonie':town?(town.owner?'Besetzter Außenposten':town.tier===8?'Zitadelle':'Neutraler Außenposten'):ruin?'Ruine':onRoute?'Geplanter Weg':terrain==='unknown'?'Nicht erkundeter Sektor':'';
      const marker = assetImage(markerKey, markerAlt, 'map-marker') || (terrain==='unknown'?'?':home ? activeHome?'⌂':'⌘' : player ? '♙' : town ? town.owner ? '⚑' : town.tier===8 ? '♜' : '⬡' : ruin?'◇':onRoute?'•':terrainIcon);
      tiles.push(`<button class="tile ${terrain} ${visibility} ${home ? 'home' : town ? (town.owner ? 'owned' : 'enemy') : ''} ${bookmarked ? 'bookmarked' : ''} ${onRoute ? 'route' : ''}" ${town ? `data-target="${town.id}"` : player ? `data-player="${player.id}"` : 'disabled'} title="${home ? (activeHome?'Aktive Kolonie: ':'Deine Kolonie: ')+escapeHtml(ownColony.name)+' · '+terrainName : town ? escapeHtml(town.name)+' · '+terrainName+' · Reise '+(town.travel_seconds??'kein Weg')+'s · '+(town.intel_level==='unknown'?'Stärke unbekannt':'Verteidigung '+number(town.defense))+(bookmarked?' · Gemerkt':'')+(onRoute?' · Auf geplanter Route':'') : 'Sektor '+x+':'+y+' · '+terrainName+(ruin?' · Kolonieruine':'')+(onRoute?' · Auf geplanter Route':'')+(visibility==='stale'?' · zuletzt '+new Date(sectorIntel.observed_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE'):'')}">${marker}</button>`);
    }
    html = `<div class="section-intro"><p class="eyebrow">AUFKLÄRUNG / WELT ${String(state.active_world?.id || 1).padStart(2, '0')}</p><h1>Die Grenzgebiete.</h1><p>Gelände wirkt auf Weg, Produktion und Verteidigung: Wald +20 % Holz/+10 % Verteidigung; Gebirge +20 % Stein/Erz/+25 % Verteidigung; Pässe −20 % Wegkosten/+5 % Produktion; Wasser ist unpassierbar. Merke bis zu 20 Außenposten je Welt.</p></div><div class="button-row map-controls"><button data-pan="left">← West</button><button data-pan="up">↑ Nord</button><span>Sektor ${mapX}:${mapY} · 64 × 64 Welt</span><button data-pan="down">Süd ↓</button><button data-pan="right">Ost →</button></div><div class="map-layout"><article class="panel map-panel">${terraMinimapMarkup(state,mapX,mapY)}<div class="map">${tiles.join('')}</div><div class="legend"><span>⌂ Deine Kolonie</span><span>⬡ Gegner</span><span>⚑ Besetzt</span><span>♜ Zitadelle</span><span class="route-legend">● Geplanter Weg</span></div>${mapRouteId?`<div id="map-route-status" role="region" aria-label="Routenansicht"><p role="status" aria-live="polite">${route?`Bekannter Weg von deiner aktiven Kolonie zu ${escapeHtml(routeTarget.name)} · ${route.length-1} Sektoren. Die Route nutzt nur bekannte, begehbare Felder.`:`Kein vollständig erkundeter, begehbarer Weg zum gespeicherten Ziel.`}</p>${route?`<details class="route-steps"><summary>Wegpunkt-Koordinaten anzeigen</summary><p>${escapeHtml(routeCoordinates(route))}</p></details>`:''}<button type="button" data-clear-route>Route ausblenden</button></div>`:''}</article><article class="panel"><h3>Sektoraufklärung</h3><p class="eyebrow">${state.world.length} POSTEN / 4.096 SEKTOREN</p><label for="map-search">Außenposten oder Koordinate suchen</label><input id="map-search" type="search" maxlength="80" placeholder="Name oder X:Y (z. B. 12:34)" value="${escapeHtml(mapSearch)}"><div id="map-jump-result" aria-live="polite"></div><label for="map-filter">Ansicht</label><select id="map-filter"><option value="all" ${mapFilter==='all'?'selected':''}>Alle Außenposten</option><option value="bookmarked" ${mapFilter==='bookmarked'?'selected':''}>Nur gemerkte Ziele (${bookmarks.size})</option></select><div id="map-targets">${state.world.map(t=>`<div class="map-target" data-search="${escapeHtml(`${t.name} ${t.x}:${t.y} ${t.tier}`.toLocaleLowerCase('de-DE'))}" data-bookmarked="${bookmarks.has(t.id)}"><div class="map-target-main"><span>${t.owner ? '⚑' : '⬡'}</span><button class="target-row" data-target="${t.id}"><div><b>${escapeHtml(t.name)}</b><small>${t.x}:${t.y} · ${t.owner ? 'Besetzt' : 'Verteidigung '+number(t.defense)+(state.active_world?.terra_combat_ruleset==='FUR-3-TERRA-COMBAT-5'?` · Festungsintegrität ${number(t.fortification_integrity??t.fortification_max_integrity??55*t.tier*t.tier)}/${number(t.fortification_max_integrity??55*t.tier*t.tier)}`:'')} · ${t.terrain} · ${outpostStockSummary(t)} · Reise ${t.travel_seconds??'kein Weg'}s</small></div><strong>${t.tier}</strong></button><button class="compact map-jump" data-jump="${t.x}:${t.y}" aria-label="Karte zu ${t.x}:${t.y} verschieben">↗ Karte</button></div><button class="compact map-bookmark" data-bookmark="${t.id}" data-bookmarked="${bookmarks.has(t.id)}" aria-label="${bookmarks.has(t.id)?'Ziel nicht mehr merken':'Ziel merken'}">${bookmarks.has(t.id)?'★ Gemerkt':'☆ Merken'}</button>${bookmarks.has(t.id)?`<button type="button" class="compact map-route" data-route="${t.id}" aria-pressed="${mapRouteId===t.id}">${mapRouteId===t.id?'✓ Route aktiv':'Route anzeigen'}</button>`:''}${outpostConversionMarkup(t,state)}</div>`).join('')}</div></article></div>${npcFactionMarkup(state.npc_factions)}${npcCampMarkup(state.npc_camps,state.active_world?.npc_camps_ruleset)}${npcAttackPlanMarkup(state.npc_attack_plans,state.active_world?.npc_camps_ruleset)}${regionControlMarkup(state.regions,state.id,state.regional_production_bonus)}<article class="panel queue-panel"><h3 data-i18n="section.commanders">Kommandanten in dieser Welt</h3>${state.players.filter(p=>p.id!==state.id).map(p=>`<button class="target-row" data-player="${p.id}"><span>♙</span><div><b>${escapeHtml(p.name)}</b><small>${p.x}:${p.y} · ${p.protected_until>state.server_time?'Neulingsschutz':p.vacation_until>state.server_time?'Urlaubsmodus':'PvP verfügbar'}</small></div><strong>↗</strong></button>`).join('')||'<p>Noch keine weiteren Kommandanten.</p>'}${window.playerDirectoryMoreMarkup()}</article><article class="panel queue-panel"><h3 data-i18n="section.missions">Missionen</h3>${queue()}</article>`;
  } else if (tab === 'trade') {
    html = `<div class="section-intro"><p class="eyebrow">WIRTSCHAFT / WARENBÖRSE</p><h1 data-i18n="section.trade_heading">Versorgung sichern.</h1><p data-i18n="game.trade_description">Rohstoffe und Materialien zwischen zehn Gütern tauschen.</p></div>` + genericItemInventoryMarkup(state.generic_items) + craftingMarkup(state.crafting) + recyclingMarkup(state.recycling) + neutralMarketMarkup(state.neutral_market);
  } else if (tab === 'alliance') {
    html = allianceViewMarkup();
  } else if (tab === 'reports') {
    html = `<div class="section-intro"><p class="eyebrow">ARCHIV / EINSATZBERICHTE</p><h1 data-i18n="section.reports_heading">Jeder Zug hinterlässt Spuren.</h1></div><div class="reports">${state.reports.length ? state.reports.map(r=>`<article class="panel"><small>${new Date(r.time*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}</small><h3>${escapeHtml(globalThis.FURI18n?.reportText(r,'title') || r.title)}</h3><p>${escapeHtml(globalThis.FURI18n?.reportText(r,'body') || r.body)}</p>${combatReportMarkup(r.combat)}</article>`).join('') : `<article class="panel empty">${assetImage('terra/ui/empty_states/empty_reports','Noch keine Berichte','empty-state-art')}Noch keine Berichte. Baue ein Gebäude oder starte eine Mission.</article>`}</div>`;
  } else if (tab === 'ranking') {
    const militaryRows=(entries)=>`<article class="panel"><ol class="ranking-list">${entries.map((entry,index)=>`<li class="rank"><strong>${String(index+1).padStart(2,'0')}</strong><b>${escapeHtml(entry.name)}${entry.tag?` <small>[${escapeHtml(entry.tag)}]</small>`:''}</b><span>${number(entry.score)} · Angriff ${number(entry.attack)} / Verteidigung ${number(entry.defense)} / Unterstützung ${number(entry.support)}</span></li>`).join('')||'<li>Für diese Welt liegen noch keine FUR-3-Kampfpunkte vor.</li>'}</ol></article>`;
    const category=state.ranking_selected_category||'overall';
    const labels={overall:'Gesamt',economy:'Wirtschaft',research:'Forschung',pve:'PvE',war:'Krieg',alliance:'Allianz',regions:'Regionen'};
    const categories=state.ranking_categories||{};
    const buttons=Object.entries(labels).map(([key,label])=>`<button type="button" class="secondary" data-ranking-category="${key}" aria-pressed="${category===key}">${label}</button>`).join('');
    const selectedRows=category==='overall'?state.ranking:(categories[category]||[]);
    const selectedMarkup=category==='war'?militaryRows(state.military_ranking||[]):category==='alliance'?militaryRows(state.alliance_military_ranking||[]):rankingListMarkup(selectedRows,category==='overall'?(state.ranking_offset||0):0,category==='overall'&&state.ranking_has_more);
    const categoryDescription=category==='overall'?'FUR-2-Gesamtwertung bleibt unverändert.':category==='economy'?'10 Punkte je Gebäudestufe.':category==='research'?'20 Punkte je Technologiestufe.':category==='pve'?'100 Punkte je gehaltenem neutralem Außenposten.':category==='war'?'FUR-3-Punkte aus Kampfverlusten in dieser Welt; vorläufige Wertung.':category==='alliance'?'FUR-3-Militärpunkte der aktuellen Allianzmitglieder in dieser Welt.':'2 Punkte je aktuell kontrollierter Region.';
    html = `<div class="section-intro"><p class="eyebrow">WELTRANGLISTEN · ${escapeHtml(category.toUpperCase())}</p><h1 data-i18n="section.ranking_heading">Die Mächte dieser Welt.</h1><p>FUR-2-Gesamtwertung: 10 Punkte pro Gebäudestufe · 20 pro Technologiestufe · 100 pro neutralem Außenposten. Zusatzkategorien verändern diese Gesamtwertung nicht. FUR-3-Militärwertung: Ein Punkt je verlorener Einheit; bestätigte alliierte Garnisonen geben einmal je 24 Stunden einen Unterstützungspunkt pro stationierter Einheit.</p></div><nav class="button-row" aria-label="Ranglistenart">${buttons}</nav><section class="section-intro"><h2>${labels[category]}</h2><p>${categoryDescription}</p></section>${selectedMarkup}${category==='overall'?`${state.public_profile_preview_error?'<p role="status" aria-live="polite">Dieses Profil ist privat oder in dieser Welt nicht verfügbar.</p>':''}${publicPlayerProfileMarkup(state.public_profile_preview)}`:''}${category==='war'?`<details class="panel"><summary>Eigene Militärpunkte prüfen</summary><ul>${(state.military_score_audit||[]).map(item=>`<li>${new Date(item.created*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')} · ${escapeHtml(item.category)} · ${number(item.points)} · ${escapeHtml(item.rules_version)} · ${escapeHtml(item.mission_id)}</li>`).join('')||'<li>Noch keine FUR-3-Kampfwertung.</li>'}</ul></details>`:''}`;
  } else {
    html = `<div class="section-intro"><p class="eyebrow">HANDBUCH / GENESIS</p><h1 data-i18n="section.help_heading">Dein erster Feldzug.</h1></div><article class="panel manual"><h3 data-i18n="section.first_economy">1. Wirtschaft aufbauen</h3><p data-i18n="help.step_1">Bioforst, Steinbruch und Erzraffinerie produzieren automatisch. Die Produktion läuft auch bei geschlossenem Browser weiter bis zum Depotlimit. Baue alle drei auf Stufe 2 und hole die Direktivenbelohnung im Kommando ab.</p><h3 data-i18n="section.first_army">2. Mobilisieren und forschen</h3><p data-i18n="help.step_2">Baue Kaserne und Labor. Rekrutiere Ranger; Kaserne ab Stufe 2 schaltet Wächter frei, Stufe 3 Sturmmechs. Taktik verbessert die Kampfkraft aller Truppen, Ingenieurswesen die Produktion.</p><h3 data-i18n="section.first_raid">3. Überfallen und erobern</h3><p data-i18n="help.step_3">Wähle auf der Karte einen Außenposten aus. Die Verteidigung neutraler Posten steht in der Aufklärungsliste. Ihre Vorräte erneuern sich automatisch um je 1 Einheit pro Ressource und Minute bis höchstens 400 × Stufe; eroberte Außenposten erneuern ihre Vorräte nicht. Gegenspieler zeigen ihre aktuelle Verteidigungsstärke im Missionsfenster; plane Verluste ein. Überlebende und Beute treffen erst nach dem Rückmarsch ein. Ab Kommandozentrale 3 kannst du freie Posten dauerhaft erobern. Eroberte Posten geben Ranglistenpunkte und je 5 Prozentpunkte zusätzliche Rohstoffproduktion.</p><h3 data-i18n="section.first_core">4. Den Kern übernehmen</h3><p data-i18n="help.step_4">Die Zitadelle hat 3.520 Verteidigung. Sammle eine starke Armee und verbessere Taktik. Erobere sie, um die Kampagne zu gewinnen. Danach kannst du weiterbauen und andere freie Sektoren sichern.</p><h3 data-i18n="section.world_details">Lokale Spielwelt</h3><p data-i18n="help.step_5">Alle Konten teilen eine Welt mit 4.096 Sektoren. Spielerangriffe, Transporte, Allianzen mit diplomatischen Nichtangriffspakten, Welt- und Privatnachrichten sowie ein Handelsmarkt sind verfügbar. Neue Konten sind eine Stunde vor PvP geschützt. Live-Ereignisse und Saisons werden im Weltbetrieb verwaltet; Betreiberangaben und Kontosicherheit findest du im Konto-Bereich. Lokal liegt dein Spielstand in data/empire.sqlite3; im konfigurierten Deployment in PostgreSQL. Der Hintergrundworker verarbeitet die Welt auch ohne geöffneten Browser. Sichere den Serverstand über das Betriebswerkzeug.</p></article>`;
  }
  if (tab==='account' && $('mfa-setup') && !$('mfa-setup').hidden) return;
  if (tab === 'research' && Object.keys(state.faction_research_catalog || {}).length) {
    const labels = {
      adaptive_forestry:['Adaptive Forstwirtschaft','Fünf zusätzliche Prozentpunkte Holzproduktion.'],
      kinetic_shield:['Kinetischer Schild','Fünf Prozent mehr Garnisonsstärke hinter einem Schildwall.'],
      rapid_construction:['Schnellbau','Neue Bauaufträge benötigen zehn Prozent weniger Zeit.'],
      long_range_colony:['Fernkolonisierung','Die Reichweite der Pioniervermessung steigt von zwölf auf sechzehn Sektoren.'],
      bastion_protocol:['Bastionsprotokoll','Wächterwälle liefern 150 Prozent ihrer Grundverteidigung.'],
      mobile_fortress:['Mobile Festung','Wächterbefestigungen halten zwei Stunden.'],
      market_cipher:['Marktchiffre','Geschützte Konvois starten nach vier statt fünf Minuten Abfertigung.'],
      efficient_salvage:['Effiziente Bergung','Expeditionen bergen zehn Prozent mehr Rohstoffe innerhalb ihrer Frachtkapazität.'],
      smuggler_navigation:['Verdeckte Navigation','Eigene Kolonieversorgung benötigt zehn Prozent weniger Reisezeit.']
    };
    html += `<section class="panel queue-panel"><h3 data-i18n="section.faction_research">Fraktionsforschung</h3>
      ${Object.entries(state.faction_research_catalog).map(([key,rule]) => {
        const done = state.faction_research?.includes(key);
        const disabled = done || state.buildings.hq < rule.hq || state.jobs.some(job => job.kind === 'terra_faction_research')
          || rule.cost.some((price,index) => price > state.resources[index]);
        return `<h4>${labels[key][0]}</h4><p>${labels[key][1]} · HQ ${number(rule.hq)} · ${cost(rule)}</p>
          <button type="button" data-action="terra_faction_research" data-key="${key}" ${disabled?'disabled':''}>${done?'Erforscht':'Forschung starten'}</button>`;
      }).join('')}
    </section>`;
  }
  if (tab === 'buildings' && state.terra_energy_catalog) {
    const energy = state.terra_energy;
    const labels = {energy_core:'Energiekern',fusion_plant:'Fusionsanlage',scanner_tower:'Scannerturm',command_uplink:'Kommando-Uplink'};
    html += `<section class="panel queue-panel"><h3 data-i18n="section.terra_buildings">Terra-Spezialgebäude</h3>
      <p>Versorgung ${number(energy.supply)} · Bedarf ${number(energy.demand)} · gedeckt ${number(energy.served)} · Erzbonus ${number(energy.ore_bonus)} Prozentpunkte.</p>
      <p>Bei Unterdeckung sinkt der Bonus der Fusionsanlage. Die Grundproduktion bleibt verfügbar.</p>
      <p>Der Scannerturm erweitert die Kartensicht um bis zu vier Sektoren. Der Kommando-Uplink erhöht das Auftragslimit auf bis zu 40. Aktuelles Limit: ${number(state.terra_mission_limit)}.</p>
      ${state.fusion_supply_cost ? `<p>${state.fusion_supplied_until > state.server_time
        ? `Fusionsbrennstoff reicht bis ${new Date(state.fusion_supplied_until*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}.`
        : 'Fusionsbrennstoff ist aufgebraucht.'}
        <button type="button" data-action="terra_fusion_supply" ${state.resources[2] < state.fusion_supply_cost || state.fusion_supplied_until >= state.server_time + 86400 ? 'disabled' : ''}>24 Stunden nachversorgen · ${number(state.fusion_supply_cost)} Erz</button></p>` : ''}
      ${Object.entries(state.terra_energy_catalog).map(([key,rule]) => {
        const level = state.terra_energy_levels?.[key] || 0;
        const disabled = state.buildings.hq < rule.hq || level >= rule.max_level
          || state.jobs.some(job => job.kind === 'terra_energy_build')
          || rule.cost.some((value,index) => value*(level+1) > state.resources[index]);
        return `<article><h4>${labels[key]} · Stufe ${number(level)}</h4><p>HQ ${number(rule.hq)} · ${cost(rule,level)} · ${number(rule.seconds*(level+1))} Sekunden</p>
          <button type="button" data-action="terra_energy_build" data-key="${key}" ${disabled?'disabled':''}>Ausbauen</button></article>`;
      }).join('')}
    </section>`;
  }
  if (tab === 'buildings' && state.terra_prestige) {
    const prestige = state.terra_prestige;
    html += `<section class="panel queue-panel"><h3>Terra-Prestige · Stufe ${number(prestige.level)}</h3>
      <p>Regelstand ${escapeHtml(prestige.version)}. Je fünf Stufen erhöhen die Obergrenze des Kommando-Uplinks um zwei Plätze.</p>
      ${prestige.enabled ? `<p>HQ ${number(prestige.hq)} · ${cost(prestige)} · ${number(prestige.seconds)} Sekunden</p>
        <button type="button" data-action="terra_prestige" ${state.buildings.hq < prestige.hq || prestige.level >= prestige.max_level || state.jobs.some(job => job.kind === 'terra_prestige') || prestige.cost.some((price,i) => price > state.resources[i]) ? 'disabled' : ''}>Prestigeausbau starten</button>`
        : state.profile.role === 'admin' ? `<button type="button" data-action="admin_enable_terra_prestige" data-world-id="${state.active_world.id}">Prestige-Regelstand für diese Welt freigeben</button>`
        : '<p>Prestige ist in dieser Welt noch nicht freigegeben.</p>'}
    </section>`;
  }
  if (tab === 'colonies') html += worldEventFeedMarkup();
  if (tab === 'colonies' && state.profile.role === 'admin') html += `<section class="panel queue-panel">
    <h3 data-i18n="section.operations">Betriebszustand</h3>
    <button type="button" id="load-operations-status">Betriebsdaten laden</button>
    <p id="operations-status" role="status"></p>
    <h3 data-i18n="section.rules_preview">Regeländerung simulieren</h3><p>Vorschau für die Gebäude und Boni deiner aktiven Kolonie. Es werden keine Regeln veröffentlicht.</p>
    <form id="terra-rule-preview">
      <label>Gelände <select name="terrain">${Object.entries(state.catalog.terrain).map(([key, rule]) => `<option value="${escapeHtml(key)}">${escapeHtml(rule.name)}</option>`).join('')}</select></label>
      <label>Rohstoff <select name="resource"><option value="wood">Holz</option><option value="stone">Stein</option><option value="ore">Erz</option></select></label>
      <label>Neue Geländeproduktion in Prozent <input type="number" name="percent" value="100" min="0" max="300" required></label>
      <label>Einheit <select name="unit">${Object.entries(state.catalog.units).map(([key, unit]) => `<option value="${escapeHtml(key)}">${escapeHtml(unit.name)}</option>`).join('')}</select></label>
      <label>Neue Kampfkraft <input type="number" name="power" value="20" min="1" max="100000" required></label>
      <button>Vorschau berechnen</button>
    </form><p id="terra-rule-result" role="status"></p></section>`;
  if (state.terra_dormant) {
    html = `<section class="panel queue-panel" role="status"><h3>Terra-Kolonien ruhen</h3>
      <p>Deine Kolonien und Bestände sind erhalten. Reaktiviere sie, um Produktion und Spielbefehle wieder freizugeben.</p>
      <button type="button" data-action="terra_reactivate">Terra-Kolonien reaktivieren</button></section>` + html;
  }
  if (tab === 'map' && state.profile.role === 'admin') {
    html += `<section class="panel queue-panel"><h3>Terra-Sektorregeln</h3>
      <p>Geschützte Felder bleiben frei. Reservierte Felder haben Vorrang für neue Heimatkolonien.</p>
      <form id="terra-sector-rule-form">
        <label>X <input name="x" type="number" min="0" max="63" required></label>
        <label>Y <input name="y" type="number" min="0" max="63" required></label>
        <label>Regel <select name="rule"><option value="protected">Geschützt</option><option value="spawn_reserved">Für Neuspawn reserviert</option><option value="clear">Regel entfernen</option></select></label>
        <button>Regel speichern</button>
      </form></section>`;
  }
  const focused = document.activeElement;
  // Preserve form values and focus across server refreshes.
  const formKey = f => f.dataset.formKey || f.dataset.system || f.dataset.train || f.dataset.worldSettings || f.id;
  const forms = new Map(renderedTab===tab ? [...$('content').querySelectorAll('form')].map(f=>[formKey(f),Object.fromEntries([...f.elements].filter(e=>e.name).map(e=>[e.name,e.value]))]) : []);
  const focusId = focused?.id;
  if (focused && $('content').contains(focused) && ['INPUT','SELECT'].includes(focused.tagName)) return;
  $('content').innerHTML = html;
  if (tab === 'map') $('content').insertAdjacentHTML('beforeend', ruinExplorationMarkup(state)+npcInvasionMarkup(state));
  if (tab === 'army') $('content').insertAdjacentHTML('beforeend', terraBossMarkup(state)+npcConvoyMarkup(state));
  if (tab === 'overview') $('content').insertAdjacentHTML('beforeend', commanderMarkup(state.commander,state.commander_doctrines,state.commander_respec,state.resources,state.server_time) + recurringQuestMarkup(state.recurring_quests, state.profile?.role === 'admin'));
  globalThis.FURI18n?.apply();
  renderedTab=tab;
  [...$('content').querySelectorAll('form')].forEach(f=>[...f.elements].forEach(e=>{const value=forms.get(formKey(f))?.[e.name];if(value!==undefined && e.tagName!=='BUTTON') e.value=value;}));
  if (focusId) $(focusId)?.focus();
  $('content').querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>{const action=b.dataset.action,payload=b.dataset.worldId?{world_id:Number(b.dataset.worldId)}:{key:b.dataset.key,...(b.dataset.direction?{direction:b.dataset.direction}:{})};if(action==='terra_defense_build'||action==='terra_defense_repair')Object.assign(payload,{world_id:state.active_world.id,colony_id:state.colony_id});if(b.dataset.count)payload.count=Number(b.dataset.count);return command(action,payload);});
  $('content').querySelectorAll('[data-hero-stat]').forEach(button=>button.onclick=()=>command('hero_allocate',{hero_stat:button.dataset.heroStat}));
  $('content').querySelectorAll('[data-hero-respec]').forEach(button=>button.onclick=()=>command('hero_respec',{}));
  $('content').querySelectorAll('[data-alliance-attack-target]').forEach(button=>button.onclick=()=>openMission(button.dataset.allianceAttackTarget));
  const chartForm = $('content').querySelector('[data-orbit-chart]');
  if ($('load-operations-status')) $('load-operations-status').onclick = async () => {
    const user = state.id;
    try {
      const status = await api('admin/operations');
      if (state?.id !== user || !$('operations-status')) return;
      const labels = {
        api_latency:'API-Latenz',worker_heartbeat:'Worker-Heartbeat',scheduler_lag:'Scheduler-Rückstand',
        backup_age:'Sicherung fehlt oder ist zu alt',orbit_ledger_integrity:'Orbit-Bestandsabweichung'
      };
      const value = (reading, unit) => reading === null || reading === undefined ? 'keine Probe' : `${number(reading)} ${unit}`;
      $('operations-status').textContent = `API p95: ${value(status.api_p95_ms,'ms')} · Worker-Alter: ${value(status.worker_age_seconds,'s')} · Rückstand: ${value(status.scheduler_lag_seconds,'s')} · Sicherungsalter: ${value(status.backup_age_seconds,'s')} · Bestandsabweichungen: ${number(status.orbit_ledger_mismatches)} · ${status.alerts.map(code => labels[code]).join(', ') || 'Keine Warnschwelle überschritten'}`;
    } catch (error) {
      notify(error.message);
    }
  };
  $('content').querySelectorAll('[data-orbit-reports]').forEach(button => {
    button.onclick = async () => {
      const user = state.id, worldId = state.active_world.id;
      const request = {};
      orbitReportRequest = request;
      const query = new URLSearchParams({world_id:String(worldId),colony_id:button.dataset.orbitReports});
      if (button.dataset.before) query.set('before',button.dataset.before);
      try {
        const result = await api('orbit/battle-reports?' + query);
        if (orbitReportRequest !== request || state?.id !== user || state.active_world.id !== result.world_id) return;
        orbitReportPage = {...result,user};
        render();
      } catch (error) {
        if (orbitReportRequest === request && state?.id === user && state.active_world.id === worldId) notify(error.message);
      }
    };
  });
  if ($('terra-rule-preview')) $('terra-rule-preview').onsubmit = async event => {
    event.preventDefault();
    const fields = event.currentTarget.elements;
    const worldId = state.active_world.id, user = state.id;
    try {
      const result = await api('admin/rule-preview', {
        world_id: worldId, terrain: fields.terrain.value, resource: fields.resource.value,
        production_percent: Number(fields.percent.value), unit: fields.unit.value,
        unit_power: Number(fields.power.value)
      });
      if (state?.id !== user || state.active_world.id !== result.world_id || !$('terra-rule-result')) return;
      $('terra-rule-result').textContent = `Produktion ${result.production_before / 10000} → ${result.production_after / 10000}/s · Kampfkraft ${result.unit_power_before} → ${result.unit_power_after} · laufende Terra-Missionen ${result.pending_terra_missions}`;
    } catch (error) {
      notify(error.message);
    }
  };
  if ($('refresh-world-event-feed')) $('refresh-world-event-feed').onclick = () => {
    void loadWorldEventFeed($('world-event-category')?.value || '');
  };
  if ($('world-event-category')) $('world-event-category').onchange = event => {
    const category = event.currentTarget.value;
    void loadWorldEventFeed(category);
  };
  const olderWorldEvents=$('content').querySelector('[data-world-events-more]');
  if($('push-enable'))$('push-enable').onclick=()=>void enableBrowserPush();
  if($('push-disable'))$('push-disable').onclick=()=>void disableBrowserPush();
  if(olderWorldEvents) olderWorldEvents.onclick=async()=>{
    const user=state?.id,worldId=state?.active_world?.id,cursor=olderWorldEvents.dataset.worldEventsMore;
    if(!user||!worldId||!cursor||olderWorldEvents.disabled)return;
    olderWorldEvents.disabled=true;
    const status=$('content').querySelector('[data-world-events-more-status]');
    if(status)status.textContent='Ältere Ereignisse werden geladen …';
    try{
      const category=worldEventFeed?.category||'';
      const result=await api(`game-events?world_id=${worldId}&before=${encodeURIComponent(cursor)}${category?`&category=${encodeURIComponent(category)}`:''}`);
      if(state?.id!==user||state?.active_world?.id!==worldId||result.world_id!==worldId)return;
      const known=new Set(worldEventFeed?.events?.map(item=>item.id)||[]);
      worldEventFeed={...result,user,category,events:[...(result.events||[]).filter(item=>!known.has(item.id)),...(worldEventFeed?.events||[])]};
      render();
    }catch(error){olderWorldEvents.disabled=false;if(status)status.textContent=error.message;}
  };
  document.querySelectorAll('[data-notification-category]').forEach(input => {
    input.onchange = async event => {
      const checkbox=event.currentTarget;
      const category = checkbox.dataset.notificationCategory;
      const user = state.id, worldId = state.active_world.id;
      try {
        await command('notification_preference', {category, muted:checkbox.checked});
        const selectedCategory=worldEventFeed?.category||'';
        const result = await api(`game-events?world_id=${worldId}${selectedCategory?`&category=${encodeURIComponent(selectedCategory)}`:''}`);
        if(state?.id===user&&state.active_world.id===worldId) { worldEventFeed={...result,user,category:selectedCategory}; render(); }
      } catch(error) { checkbox.checked=!checkbox.checked; notify(error.message); }
    };
  });
  if ($('terra-sector-rule-form')) $('terra-sector-rule-form').onsubmit = event => {
    event.preventDefault();
    const fields = event.currentTarget.elements;
    command('admin_terra_sector', {
      world_id: state.active_world.id, x: Number(fields.x.value), y: Number(fields.y.value),
      key: fields.rule.value
    });
  };
  if ($('orbit-event-form')) $('orbit-event-form').onsubmit = event => {
    event.preventDefault();
    command('admin_orbit_event', {world_id: state.active_world.id, key: event.currentTarget.elements.kind.value});
  };
  $('content').querySelectorAll('[data-orbit-ammunition]').forEach(button => {
    button.onclick = () => command('orbit_build_ammunition', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitColony,
      key: button.dataset.orbitAmmunition, count: 1
    });
  });
  $('content').querySelectorAll('[data-orbit-gateway-cargo]').forEach(form => {
    form.onsubmit = event => {
      event.preventDefault();
      command(event.submitter?.dataset.direction === 'export' ? 'orbit_export_ore' : 'orbit_import_ore', {
        world_id: state.active_world.id, colony_id: form.dataset.orbitGatewayCargo,
        orbit_ore: Number(form.elements.ore.value)
      });
    };
  });
  $('content').querySelectorAll('[data-orbit-repair]').forEach(button => {
    button.onclick = () => command('orbit_repair_wrecks', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitColony,
      key: button.dataset.orbitRepair, count: 1
    });
  });
  $('content').querySelectorAll('[data-orbit-supply]').forEach(button => {
    button.onclick = () => command('orbit_fleet_supply', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitSupply
    });
  });
  $('content').querySelectorAll('[data-orbit-template-apply]').forEach(button => {
    button.onclick = () => {
      const form = button.form;
      const template = state.orbit_access.templates.find(item => item.id === form.elements.orbit_template.value);
      if (!template) return notify('Wähle eine Orbit-Vorlage.');
      if (template.kind === 'fleet') {
        const fleet = [...form.elements.fleet.options].find(option => option.dataset.ship === template.ship);
        if (!fleet) return notify('Diese Schiffsklasse ist derzeit in keiner Startkolonie verfügbar.');
        form.elements.fleet.value = fleet.value;
        form.elements.retreat.value = template.retreat_pct ?? '';
      } else {
        form.elements.ship.value = template.ship;
      }
      form.elements.count.value = template.amount;
      notify('Vorlage geladen. Prüfe den Auftrag vor dem Start.');
    };
  });
  $('content').querySelectorAll('[data-orbit-template-save]').forEach(button => {
    button.onclick = () => {
      const form = button.form;
      const fleet = button.dataset.orbitTemplateSave === 'fleet';
      if (!form.reportValidity()) return;
      const name = form.elements.orbit_template_name.value.trim();
      if (name.length < 2) return notify('Gib einen Vorlagennamen ein.');
      command(fleet ? 'orbit_save_fleet_template' : 'orbit_save_shipyard_template', {
        world_id: state.active_world.id, name,
        key: fleet ? form.elements.fleet.selectedOptions[0].dataset.ship : form.elements.ship.value,
        count: Number(form.elements.count.value),
        ...(fleet && form.elements.retreat.value ? {retreat_pct: Number(form.elements.retreat.value)} : {})
      });
    };
  });
  $('content').querySelectorAll('[data-orbit-template-delete]').forEach(button => {
    button.onclick = () => {
      const key = button.form.elements.orbit_template.value;
      if (!key) return notify('Wähle eine Orbit-Vorlage.');
      command('orbit_delete_template', {world_id: state.active_world.id, key});
    };
  });
  $('content').querySelectorAll('[data-orbit-attack-recall]').forEach(button => {
    button.onclick = () => command('orbit_recall_attack', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitColony,
      key: button.dataset.orbitAttackRecall
    });
  });
  if ($('orbit-alliance-form')) $('orbit-alliance-form').onsubmit = event => {
    event.preventDefault();
    const form = event.currentTarget;
    const fleet = form.elements.fleet.selectedOptions[0];
    command('orbit_join_attack', {
      world_id: state.active_world.id, orbit_target: form.elements.attack.value,
      colony_id: fleet.dataset.origin, key: fleet.dataset.ship, count: Number(form.elements.count.value)
    });
  };
  $('content').querySelectorAll('[data-orbit-phalanx]').forEach(form => {
    form.onsubmit = event => {
      event.preventDefault();
      command('orbit_phalanx_scan', {
        world_id: orbitChart.world_id, galaxy: orbitChart.galaxy, system: orbitChart.system,
        slot: Number(form.elements.slot.value), colony_id: form.dataset.orbitPhalanx
      });
    };
  });
  if ($('orbit-expedition-form')) $('orbit-expedition-form').onsubmit = event => {
    event.preventDefault();
    const form = event.currentTarget;
    command('orbit_expedition', {
      world_id: orbitChart.world_id, galaxy: orbitChart.galaxy, system: orbitChart.system,
      slot: Number(form.elements.slot.value), colony_id: form.elements.origin.value,
      count: Number(form.elements.count.value),
      ...(form.elements.special.value ? {orbit_target: form.elements.special.value} : {})
    });
  };
  $('content').querySelectorAll('[data-orbit-gate]').forEach(button => {
    button.onclick = () => command('orbit_build_jumpgate', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitGate
    });
  });
  $('content').querySelectorAll('[data-orbit-jump]').forEach(form => {
    form.onsubmit = event => {
      event.preventDefault();
      command('orbit_jump', {
        world_id: state.active_world.id, colony_id: form.dataset.orbitJump,
        orbit_target: form.elements.target.value, key: form.elements.ship.value,
        count: Number(form.elements.count.value)
      });
    };
  });
  $('content').querySelectorAll('[data-orbit-scanner]').forEach(button => {
    button.onclick = () => command('orbit_build_scanner', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitScanner
    });
  });
  $('content').querySelectorAll('[data-orbit-station]').forEach(button => {
    button.onclick = () => command(button.dataset.orbitStation, {
      world_id: state.active_world.id, colony_id: button.dataset.orbitColony
    });
  });
  $('content').querySelectorAll('[data-orbit-station-transfer]').forEach(form => {
    form.onsubmit = event => {
      event.preventDefault();
      command(form.dataset.orbitStationTransfer, {
        world_id: state.active_world.id, colony_id: form.dataset.orbitColony,
        key: form.elements.ship.value, count: Number(form.elements.count.value)
      });
    };
  });
  $('content').querySelectorAll('[data-orbit-defense]').forEach(button => {
    button.onclick = () => command('orbit_build_defense', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitDefense
    });
  });
  $('content').querySelectorAll('[data-orbit-salvage]').forEach(button => {
    button.onclick = () => command('orbit_salvage', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitColony,
      key: button.dataset.orbitSalvage, count: 1
    });
  });
  if ($('orbit-attack-form')) $('orbit-attack-form').onsubmit = event => {
    event.preventDefault();
    const form = event.currentTarget;
    const fleet = form.elements.fleet.selectedOptions[0];
    const action = event.submitter?.hasAttribute('data-moon-siege') ? 'orbit_destroy_moon'
      : event.submitter?.hasAttribute('data-allied-attack') ? 'orbit_alliance_attack' : 'orbit_attack';
    command(action, {
      world_id: orbitChart.world_id, galaxy: orbitChart.galaxy, system: orbitChart.system,
      slot: Number(form.elements.slot.value), colony_id: fleet.dataset.origin,
      key: fleet.dataset.ship, count: Number(form.elements.count.value),
      lances: Number(form.elements.lances.value),
      ...(form.elements.retreat.value ? {retreat_pct: Number(form.elements.retreat.value)} : {})
    });
  };
  $('content').querySelectorAll('[data-orbit-scout]').forEach(button => {
    button.onclick = () => command('orbit_scout', {
      world_id: orbitChart.world_id, galaxy: orbitChart.galaxy, system: orbitChart.system,
      slot: Number(button.dataset.orbitScout), colony_id: $('orbit-scout-origin').value
    });
  });
  $('content').querySelectorAll('[data-orbit-recall]').forEach(button => {
    button.onclick = () => command('orbit_recall_transport', {
      world_id: state.active_world.id,
      colony_id: button.dataset.orbitColony,
      key: button.dataset.orbitRecall
    });
  });
  $('content').querySelectorAll('[data-orbit-collect]').forEach(button => {
    button.onclick = () => command('orbit_collect_reserve', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitCollect
    });
  });
  $('content').querySelectorAll('[data-orbit-freight]').forEach(form => {
    form.onsubmit = event => {
      event.preventDefault();
      command('orbit_transport', {
        world_id: state.active_world.id, colony_id: form.dataset.orbitFreight,
        key: form.elements.target.value, count: Number(form.elements.count.value),
        orbit_ore: Number(form.elements.ore.value), orbit_ether: Number(form.elements.ether.value)
      });
    };
  });
  $('content').querySelectorAll('[data-orbit-research]').forEach(button => {
    button.onclick = () => command('orbit_research_shipbuilding', {
      world_id: state.active_world.id, colony_id: button.dataset.orbitResearch
    });
  });
  $('content').querySelectorAll('[data-orbit-shipyard]').forEach(form => {
    form.onsubmit = event => {
      event.preventDefault();
      command('orbit_build_ships', {
        world_id: state.active_world.id, colony_id: form.dataset.orbitShipyard,
        key: form.elements.ship.value, count: Number(form.elements.count.value)
      });
    };
  });
  $('content').querySelectorAll('[data-orbit-build]').forEach(button => {
    button.onclick = () => command('orbit_build', {
      world_id: state.active_world.id,
      colony_id: button.dataset.orbitColony,
      key: button.dataset.orbitBuild
    });
  });
  $('content').querySelectorAll('[data-orbit-slot]').forEach(button => {
    button.onclick = () => {
      const origin = $('orbit-colony-origin').value;
      command('orbit_colonize', {
        world_id: orbitChart.world_id,
        galaxy: orbitChart.galaxy,
        system: orbitChart.system,
        slot: Number(button.dataset.orbitSlot),
        ...(origin ? {colony_id: origin} : {})
      });
    };
  });
  if (chartForm) chartForm.onsubmit = async event => {
    event.preventDefault();
    const user = state.id, worldId = state.active_world.id;
    const request = {};
    orbitChartRequest = request;
    const query = new URLSearchParams({
      world_id:String(worldId), galaxy:chartForm.elements.galaxy.value,
      system:chartForm.elements.system.value
    });
    try {
      const result = await api('orbit/system?' + query);
      if (orbitChartRequest !== request || state?.id !== user || state.active_world.id !== result.world_id) return;
      orbitChart = {...result, user};
      if (chartForm.contains(document.activeElement)) chartForm.querySelector('button').focus();
      render();
    } catch (error) {
      if (orbitChartRequest === request && state?.id === user && state.active_world.id === worldId) notify(error.message);
    }
  };
  if ($('alliance-create-form')) $('alliance-create-form').onsubmit=e=>{e.preventDefault();const form=e.currentTarget;command('alliance_create',{tag:form.elements.tag.value,name:form.elements.name.value});};
  if ($('alliance-invite-form')) $('alliance-invite-form').onsubmit=e=>{e.preventDefault();command('alliance_invite',{name:e.currentTarget.elements.player.value});};
  $('content').querySelectorAll('[data-alliance-transfer]').forEach(button=>button.onclick=()=>{const name=button.dataset.memberName;if(window.confirm(`Die Allianzleitung an ${name} übertragen? Du wirst danach Offizier.`))command('alliance_transfer',{key:button.dataset.allianceTransfer});});
  if ($('world-create-form')) $('world-create-form').onsubmit=e=>{e.preventDefault();const form=e.currentTarget;command('world_create',{name:form.elements.name.value,seed:Number(form.elements.seed.value),outposts:Number(form.elements.outposts.value),mode:form.elements.mode.value,joinable:form.elements.joinable.checked,terra_combat_ruleset:form.elements.terra_combat_ruleset.value,terra_retreat_threshold_percent:Number(form.elements.terra_retreat_threshold_percent.value),crafting_ruleset:form.elements.crafting_ruleset.value,hero_ruleset:form.elements.hero_ruleset.value,hero_doctrine_ruleset:form.elements.hero_doctrine_ruleset.value,hero_respec_ruleset:form.elements.hero_respec_ruleset.value,npc_camps_ruleset:form.elements.npc_camps_ruleset.value,terra_ruin_exploration_ruleset:form.elements.terra_ruin_exploration_ruleset.value});};
  if ($('season-create-form')) $('season-create-form').onsubmit=e=>{e.preventDefault();const form=e.currentTarget;command('admin_season',{name:form.elements.name.value,days:Number(form.elements.days.value),goal_score:Number(form.elements.goal_score.value)});};
  $('content').querySelectorAll('[data-world-settings]').forEach(form=>form.onsubmit=e=>{e.preventDefault();command('world_update',{world_id:Number(form.dataset.worldSettings),name:form.elements.name.value,joinable:form.elements.joinable.checked,terra_combat_ruleset:form.elements.terra_combat_ruleset.value,terra_retreat_threshold_percent:Number(form.elements.terra_retreat_threshold_percent.value),crafting_ruleset:form.elements.crafting_ruleset.value,hero_ruleset:form.elements.hero_ruleset.value,hero_doctrine_ruleset:form.elements.hero_doctrine_ruleset.value,hero_respec_ruleset:form.elements.hero_respec_ruleset.value});});
  const rolloutVersions={terra_combat_ruleset:['FUR-2','FUR-3-TERRA-COMBAT-1','FUR-3-TERRA-COMBAT-2','FUR-3-TERRA-COMBAT-3','FUR-3-TERRA-COMBAT-4','FUR-3-TERRA-COMBAT-5'],crafting_ruleset:['FUR-2','FUR-CRAFTING-1'],hero_ruleset:['FUR-2','FUR-3-HERO-1'],hero_doctrine_ruleset:['FUR-2','FUR-3-HERO-2'],hero_respec_ruleset:['FUR-2','FUR-3-HERO-3'],npc_camps_ruleset:['FUR-2','FUR-3-NPC-CAMPS-1','FUR-3-NPC-CAMPS-2','FUR-3-NPC-CAMPS-3'],terra_ruin_exploration_ruleset:['FUR-2','FUR-3-TERRA-RUIN-EXPLORATION-1']};
  $('content').querySelectorAll('[data-rule-rollout]').forEach(form=>{
    const ruleSelect=form.elements.rule_key,targetSelect=form.elements.target_version;
    const refreshTargets=()=>{targetSelect.replaceChildren(...rolloutVersions[ruleSelect.value].map(version=>{const option=document.createElement('option');option.value=version;option.textContent=version;return option;}));};
    ruleSelect.onchange=refreshTargets;
    form.onsubmit=event=>{event.preventDefault();const activeAt=Math.floor(new Date(form.elements.active_at_local.value).getTime()/1000);if(!Number.isSafeInteger(activeAt)){notify('Ungültiger Aktivierungszeitpunkt.');return;}command('admin_rule_rollout_schedule',{world_id:Number(form.dataset.ruleRollout),rule_key:ruleSelect.value,target_version:targetSelect.value,active_at:activeAt});};
  });
  $('content').querySelectorAll('[data-rule-rollout-cancel]').forEach(button=>button.onclick=()=>command('admin_rule_rollout_cancel',{key:button.dataset.ruleRolloutCancel}));
  $('content').querySelectorAll('[data-colony-rename]').forEach(form=>form.onsubmit=e=>{e.preventDefault();command('colony_rename',{colony_id:form.dataset.colonyRename,name:form.elements.name.value});});
  $('content').querySelectorAll('[data-colony-abandon]').forEach(button=>button.onclick=()=>{const colonyName=button.dataset.colonyName;if(window.confirm(`Kolonie „${colonyName}“ mit Rohstoffen, Gebäuden, Forschung und Truppen endgültig aufgeben? Laufende Aufträge, eingehende Versorgungen und offene Handelsangebote müssen vorher geregelt sein.`))command('colony_abandon',{colony_id:button.dataset.colonyAbandon,confirmation:colonyName});});
  $('content').querySelectorAll('[data-convert]').forEach(button=>button.onclick=()=>{const postName=button.dataset.convertName;if(window.confirm(`Außenposten „${postName}“ für 6.000 Holz, 4.500 Stein und 3.000 Erz in eine Kolonie umwandeln? Vorräte und Garnison werden übernommen; der Außenposten und sein Gebietskontrollpunkt verschwinden.`))command('outpost_colonize',{key:button.dataset.convert,confirmation:postName});});
  $('content').querySelectorAll('[data-quest]').forEach(b=>b.onclick=()=>command('quest',{key:b.dataset.quest}));
  $('content').querySelectorAll('[data-recurring-quests-enabled]').forEach(b=>b.onclick=()=>command('admin_recurring_quests',{enabled:b.dataset.recurringQuestsEnabled==='true'}));
  $('content').querySelectorAll('[data-convoy-schedule]').forEach(form=>form.onsubmit=event=>{
    event.preventDefault();
    command('admin_npc_convoy_schedule',{name:event.currentTarget.elements.name.value});
  });
  $('content').querySelectorAll('[data-convoy-join]').forEach(form=>form.onsubmit=event=>{
    event.preventDefault();
    const current=event.currentTarget;
    command(current.elements.role.value==='escort'?'npc_convoy_escort':'npc_convoy_raid',{key:current.dataset.convoyJoin,count:Number(current.elements.count.value)});
  });
  $('content').querySelector('[data-boss-schedule]')?.addEventListener('submit', event=>{
    event.preventDefault();
    command('admin_terra_boss_schedule',{name:event.currentTarget.elements.name.value});
  });
  $('content').querySelector('[data-invasion-schedule]')?.addEventListener('submit', event=>{
    event.preventDefault();
    command('admin_npc_invasion_schedule',{name:event.currentTarget.elements.name.value});
  });
  $('content').querySelector('[data-boss-attack]')?.addEventListener('submit', event=>{
    event.preventDefault();
    const form=event.currentTarget;
    command('terra_boss_attack',{key:form.dataset.bossAttack,count:Number(form.elements.count.value)});
  });
  $('content').querySelectorAll('[data-goto]').forEach(b=>b.onclick=()=>document.querySelector(`nav [data-tab="${b.dataset.goto}"]`).click());
  $('content').querySelectorAll('[data-target]').forEach(b=>b.onclick=()=>openMission(b.dataset.target));
  $('content').querySelectorAll('[data-ruin]').forEach(b=>b.onclick=()=>openMission('ruin:'+b.dataset.ruin));
  $('content').querySelectorAll('[data-train]').forEach(f=>f.onsubmit=e=>{e.preventDefault(); command('train',{key:f.dataset.train,count:Number(f.elements.count.value)});});
  $('content').querySelectorAll('[data-terra-repair]').forEach(f=>f.onsubmit=e=>{e.preventDefault();command('terra_repair_units',{wreck_id:f.dataset.terraRepair,count:Number(f.elements.count.value),world_id:state.active_world.id,colony_id:state.colony_id});});
  const templateForm=$('production-template-form');
  if(templateForm)templateForm.onsubmit=async event=>{
    event.preventDefault();
    const kind=templateForm.dataset.productionKind;
    const payload={name:templateForm.elements.name.value,kind,key:templateForm.elements.key.value,count:kind==='train'?Number(templateForm.elements.count.value):1};
    try{
      const result=await api('production-templates',payload);
      templateForm.elements.name.value='';
      productionTemplates.push(result.template);
      render();
      $('production-template-select').value=result.template.id;
      $('queue-production-template').disabled=false;
      $('delete-production-template').disabled=false;
      notify(`Produktionsvorlage „${result.template.name}“ gespeichert.`);
    }catch(error){$('production-template-status').textContent=error.message;}
  };
  $('production-template-select')?.addEventListener('change',event=>{
    const enabled=Boolean(event.currentTarget.value);
    $('queue-production-template').disabled=!enabled;
    $('delete-production-template').disabled=!enabled;
  });
  $('queue-production-template')?.addEventListener('click',async()=>{
    const templateId=$('production-template-select').value;
    if(!templateId){$('production-template-status').textContent='Wähle zuerst eine Vorlage.';return;}
    if(busy)return;
    busy=true;
    try{
      state=await api(`production-templates/${encodeURIComponent(templateId)}/queue`,{token:crypto.randomUUID(),origin:commandOrigin()});
      render();
      $('production-template-select').value=templateId;
      $('queue-production-template').disabled=false;
      $('delete-production-template').disabled=false;
      notify('Auftrag mit den aktuellen Spielregeln eingereiht.');
    }catch(error){$('production-template-status').textContent=error.message;}
    finally{busy=false;}
  });
  $('delete-production-template')?.addEventListener('click',async()=>{
    const templateId=$('production-template-select').value;
    if(!templateId){$('production-template-status').textContent='Wähle zuerst eine Vorlage.';return;}
    try{
      await api(`production-templates/${encodeURIComponent(templateId)}`,undefined,'DELETE');
      productionTemplates=productionTemplates.filter(item=>item.id!==templateId);
      render();
      notify('Produktionsvorlage gelöscht.');
    }catch(error){$('production-template-status').textContent=error.message;}
  });
  if ($('colony-supply-form')) $('colony-supply-form').onsubmit=e=>{e.preventDefault();const form=e.currentTarget;const army=Object.fromEntries(Object.keys(state.units).map(key=>[key,Number(form.elements[`carrier-${key}`].value)]));const resources=[0,1,2].map(index=>Number(form.elements[`cargo-${index}`].value));const goods=Object.fromEntries((state.neutral_market?.goods||[]).filter(good=>!['wood','stone','ore'].includes(good.id)).map(good=>[good.id,Number(form.elements[`goods-${good.id}`]?.value||0)]).filter(([,amount])=>amount>0));const items=Object.fromEntries((state.generic_items?.items||[]).map(item=>[item.id,Number(form.elements[`item-${item.id}`]?.value||0)]).filter(([,amount])=>amount>0));const key=form.elements.destination.value;
    if(e.submitter?.hasAttribute('data-create-route')) {
      if(Object.keys(goods).length||Object.keys(items).length){notify('Handelsrouten unterstützen derzeit nur Rohstoffe.');return;}
      command('terra_route_create',{key,army,resources,hours:Number(form.elements.route_hours.value),world_id:state.active_world.id,colony_id:state.colony_id});
    } else command('colony_supply',{key,army,resources,goods,items});
  };
  $('content').querySelectorAll('[data-terra-route-action]').forEach(button => {
    button.onclick = () => command(button.dataset.terraRouteAction,{
      key:button.dataset.terraRouteId,world_id:state.active_world.id,colony_id:state.colony_id
    });
  });
  if ($('alliance-supply-form')) $('alliance-supply-form').onsubmit=e=>{e.preventDefault();const form=e.currentTarget;const army=Object.fromEntries(Object.keys(state.units).map(key=>[key,Number(form.elements[`carrier-${key}`].value)]));const resources=[0,1,2].map(index=>Number(form.elements[`cargo-${index}`].value));command('alliance_send_supply',{key:form.elements.destination.value,army,resources});};
  if ($('alliance-garrison-policy-form')) $('alliance-garrison-policy-form').onsubmit=e=>{e.preventDefault();const form=e.currentTarget;command('alliance_garrison_policy',{enabled:form.elements.enabled.checked,capacity:Number(form.elements.capacity.value)});};
  if ($('alliance-garrison-form')) $('alliance-garrison-form').onsubmit=e=>{e.preventDefault();const form=e.currentTarget;const army=Object.fromEntries(Object.keys(state.units).map(unit=>[unit,Number(form.elements[`unit-${unit}`].value)]));command('alliance_garrison_station',{key:form.elements.target.value,army});};
  if ($('warden-fortify-form')) $('warden-fortify-form').onsubmit = event => {
    event.preventDefault();
    command('terra_warden_fortify', {world_id:state.active_world.id,key:event.currentTarget.elements.target.value});
  };
  document.querySelector('[data-alliance-supply-more]')?.addEventListener('click',async event=>{
    const button=event.currentTarget;
    const userId=state?.id, allianceId=state?.membership?.alliance_id, worldId=state?.active_world?.id;
    const cursor=state?.alliance_supply_targets?.at(-1)?.colony_id;
    if(!userId||!allianceId||!worldId||!cursor||button.disabled)return;
    button.disabled=true;
    const status=document.querySelector('[data-alliance-supply-status]');
    if(status)status.textContent='Weitere Allianzmitglieder werden geladen …';
    try{
      const page=await api(`alliance/supply-targets?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId||state?.membership?.alliance_id!==allianceId||state?.active_world?.id!==worldId)return;
      const known=new Set((state.alliance_supply_targets||[]).map(target=>target.colony_id));
      state.alliance_supply_targets.push(...page.targets.filter(target=>!known.has(target.colony_id)));
      state.alliance_supply_targets_has_more=page.has_more;
      render();
    }catch(error){
      button.disabled=false;
      if(status)status.textContent=error.message;
    }
  });
  bindSystems();
  const olderBulletins=$('content').querySelector('[data-bulletin-more]');
  if(olderBulletins) olderBulletins.onclick=async()=>{
    const allianceId=state?.membership?.alliance_id;
    if(!allianceId||olderBulletins.disabled)return;
    olderBulletins.disabled=true;
    const status=$('content').querySelector('[data-bulletin-more-status]');
    if(status)status.textContent='Ältere Beiträge werden geladen …';
    try{
      const cursor=encodeURIComponent(olderBulletins.dataset.bulletinMore);
      const page=await api(`alliance/bulletins?before=${cursor}`);
      if(state?.membership?.alliance_id!==allianceId)return;
      state.alliance_bulletins.push(...page.entries);
      state.alliance_bulletins_has_more=page.has_more;
      render();
    }catch(error){
      olderBulletins.disabled=false;
      if(status)status.textContent=error.message;
    }
  };
  const olderForum=$('content').querySelector('[data-forum-more]');
  if(olderForum) olderForum.onclick=async()=>{
    const allianceId=state?.membership?.alliance_id;
    if(!allianceId||olderForum.disabled)return;
    olderForum.disabled=true;
    const status=$('content').querySelector('[data-forum-more-status]');
    if(status)status.textContent='Ältere Themen werden geladen …';
    try{
      const cursor=encodeURIComponent(olderForum.dataset.forumMore);
      const page=await api(`alliance/forum?before=${cursor}`);
      if(state?.membership?.alliance_id!==allianceId)return;
      state.alliance_forum.push(...page.threads);
      state.alliance_forum_has_more=page.has_more;
      render();
    }catch(error){
      olderForum.disabled=false;
      if(status)status.textContent=error.message;
    }
  };
  const olderRanking=$('content').querySelector('[data-ranking-more]');
  if(olderRanking) olderRanking.onclick=async()=>{
    const worldId=state?.active_world?.id;
    const cursor=state?.ranking?.at(-1)?.id;
    if(!worldId||!cursor||olderRanking.disabled)return;
    olderRanking.disabled=true;
    const status=$('content').querySelector('[data-ranking-status]');
    if(status)status.textContent='Weitere Ranglistenplätze werden geladen …';
    try{
      const page=await api(`ranking?before=${encodeURIComponent(cursor)}`);
      if(state?.active_world?.id!==worldId)return;
      const known=new Set(state.ranking.map(entry=>entry.id));
      state.ranking.push(...page.entries.filter(entry=>!known.has(entry.id)));
      state.ranking_has_more=page.has_more;
      render();
    }catch(error){
      olderRanking.disabled=false;
      if(status)status.textContent=error.message;
    }
  };
  $('content').querySelectorAll('[data-ranking-category]').forEach(button=>button.onclick=()=>{state.ranking_selected_category=button.dataset.rankingCategory;render();});
  const profileClose=$('content').querySelector('[data-player-profile-close]');
  if(profileClose)profileClose.onclick=()=>{state.public_profile_preview=null;state.public_profile_preview_error=false;render();};
  $('content').querySelectorAll('[data-player-profile]').forEach(button=>button.onclick=async()=>{
    const worldId=state?.active_world?.id, profileId=button.dataset.playerProfile;
    if(!worldId||!profileId||button.disabled)return;
    button.disabled=true;state.public_profile_preview_error=false;
    try{
      const result=await api(`profiles/${encodeURIComponent(profileId)}`);
      if(state?.active_world?.id!==worldId)return;
      state.public_profile_preview=result.profile;state.public_profile_preview_error=false;render();
    }catch{
      if(state?.active_world?.id!==worldId)return;
      state.public_profile_preview=null;state.public_profile_preview_error=true;render();
    }
  });
  const olderWorlds=$('content').querySelector('[data-worlds-more]');
  if(olderWorlds) olderWorlds.onclick=async()=>{
    const userId=state?.id, cursor=state?.worlds?.at(-1)?.id;
    if(!userId||!cursor||olderWorlds.disabled)return;
    olderWorlds.disabled=true;
    const status=$('content').querySelector('[data-worlds-status]');
    if(status)status.textContent='Weitere Welten werden geladen …';
    try{
      const page=await api(`worlds?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId)return;
      const known=new Set((state.worlds||[]).map(world=>world.id));
      state.worlds.push(...page.worlds.filter(world=>!known.has(world.id)));
      state.worlds_has_more=page.has_more;
      render();
    }catch(error){
      olderWorlds.disabled=false;
      if(status)status.textContent=error.message;
    }
  };
  const olderColonies=$('content').querySelector('[data-colonies-more]');
  if(olderColonies) olderColonies.onclick=async()=>{
    const userId=state?.id, cursor=state?.empire_colonies?.at(-1)?.colony_id;
    if(!userId||!cursor||olderColonies.disabled)return;
    olderColonies.disabled=true;
    const status=$('content').querySelector('[data-colonies-status]');
    if(status)status.textContent='Weitere Kolonien werden geladen …';
    try{
      const page=await api(`colonies?before=${encodeURIComponent(cursor)}`);
      if(state?.id!==userId)return;
      const known=new Set((state.empire_colonies||[]).map(colony=>colony.colony_id));
      state.empire_colonies.push(...page.colonies.filter(colony=>!known.has(colony.colony_id)));
      for(const colony of page.colonies)colony.selected=colony.colony_id===state.colony_id;
      state.empire_colonies_has_more=page.has_more;
      render();
    }catch(error){
      olderColonies.disabled=false;
      if(status)status.textContent=error.message;
    }
  };
  $('content').querySelectorAll('[data-player]').forEach(b=>b.onclick=()=>openMission('player:'+b.dataset.player));
  $('content').querySelectorAll('[data-pan]').forEach(b=>b.onclick=()=>{const d=b.dataset.pan;mapX=Math.max(0,Math.min(MAP_MAX_START,mapX+(d==='right'?MAP_VIEW_SIZE-1:d==='left'?1-MAP_VIEW_SIZE:0)));mapY=Math.max(0,Math.min(MAP_MAX_START,mapY+(d==='down'?MAP_VIEW_SIZE-1:d==='up'?1-MAP_VIEW_SIZE:0)));render();});
  const minimap = $('terra-minimap');
  if (minimap) {
    minimap.onclick = event => {
      const sector = minimapPointerSector(event.clientX,event.clientY,minimap.getBoundingClientRect());
      if (sector) jumpToSector(...sector);
    };
    minimap.onkeydown = event => {
      const steps = {ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
      const step = steps[event.key];
      if (!step) return;
      event.preventDefault();
      jumpToSector(mapX+Math.floor(MAP_VIEW_SIZE/2)+step[0],mapY+Math.floor(MAP_VIEW_SIZE/2)+step[1]);
      $('terra-minimap')?.focus();
    };
  }
  if ($('map-search')) {
    $('map-search').oninput = event => { mapSearch = event.currentTarget.value; filterMapTargets(); };
    $('map-filter').onchange = event => { mapFilter = event.currentTarget.value; filterMapTargets(); };
    $('content').querySelectorAll('[data-bookmark]').forEach(button => button.onclick = () => { if (button.dataset.bookmarked === 'true' && mapRouteId === button.dataset.bookmark) mapRouteId = ''; command(button.dataset.bookmarked === 'true' ? 'map_bookmark_remove' : 'map_bookmark_add', {key:button.dataset.bookmark}); });
    $('content').querySelectorAll('[data-jump]').forEach(button => button.onclick = () => { const [x,y] = button.dataset.jump.split(':').map(Number); jumpToSector(x,y); });
    $('content').querySelectorAll('[data-route]').forEach(button => button.onclick = () => { mapRouteId = button.dataset.route; jumpToSector(state.x,state.y); });
    $('content').querySelector('[data-clear-route]')?.addEventListener('click',()=>{mapRouteId='';render();});
    filterMapTargets();
  }
  bindNeutralMarket();
  bindCrafting();
}
function filterMapTargets() {
  const query = mapSearch.trim().toLocaleLowerCase('de-DE');
  $('content').querySelectorAll('.map-target').forEach(row => {
    row.hidden = (mapFilter === 'bookmarked' && row.dataset.bookmarked !== 'true') || !row.dataset.search.includes(query);
  });
  const result = $('map-jump-result');
  if (!result) return;
  result.replaceChildren();
  const coordinate = parseMapCoordinate(mapSearch);
  if (coordinate) {
    const [x,y] = coordinate;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'compact map-jump-result';
      button.textContent = `Zu Sektor ${x}:${y} springen`;
      button.onclick = () => jumpToSector(x, y);
      result.append(button);
      if (state.faction_research?.includes('adaptive_forestry')) {
        const survey = document.createElement('button');
        survey.type = 'button';
        survey.textContent = 'Pioniervermessung · 8 % Gründungsrabatt für eine Stunde';
        survey.disabled = (state.pioneer_survey_ready_at || 0) > state.server_time;
        survey.onclick = () => command('terra_pioneer_survey',{world_id:state.active_world.id,x,y});
        result.append(survey);
      }
      const sectorRule = state.terra_sector_rules?.[`${x}:${y}`];
      const ruinUntil = state.terra_ruins?.[`${x}:${y}`];
      if (state.terra_dormant_sectors?.includes(`${x}:${y}`)) {
        const dormant = document.createElement('p');
        dormant.textContent = 'Ruhende Kolonie · Sektor belegt';
        result.append(dormant);
      }
      if (ruinUntil > state.server_time) {
        const ruin = document.createElement('p');
        ruin.textContent = `Kolonieruine · Sektor gesperrt bis ${new Date(ruinUntil*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}`;
        result.append(ruin);
      }
      if (sectorRule) {
        const restriction = document.createElement('p');
        restriction.textContent = sectorRule === 'protected' ? 'Geschützter Sektor' : 'Für Neuspawn reservierter Sektor';
        result.append(restriction);
      }
      const occupied = state.world.some(town=>town.x===x&&town.y===y)
        || (state.colonies||[]).some(colony=>colony.x===x&&colony.y===y)
        || state.players.some(player=>player.id!==state.id&&player.x===x&&player.y===y);
      if (!occupied) {
        const water = state.terrain_map?.[`${x}:${y}`] === 'water';
        const surveyed = state.pioneer_survey?.x === x && state.pioneer_survey?.y === y
          && state.pioneer_survey.expires > state.server_time;
        const settlementCosts = state.colonization_cost.map(cost =>
          surveyed ? Math.floor(cost*(100-state.pioneer_survey_discount)/100) : cost);
        const available = !water && state.buildings.hq >= 3
          && state.colony_count < state.colony_slot_limit
          && settlementCosts.every((cost,index)=>state.resources[index]>=cost);
        const colonize = document.createElement('button');
        colonize.type = 'button';
        colonize.className = 'compact map-colonize';
        colonize.textContent = available
          ? `Freien Sektor ${x}:${y} kolonisieren · ${settlementCosts.map(number).join(' / ')}`
          : water ? `Sektor ${x}:${y} ist Wasser und nicht bebaubar` : 'Kolonisation benötigt Kommandozentrale 3, freien Slot und die Rohstoffkosten';
        colonize.disabled = !available || Boolean(sectorRule) || ruinUntil > state.server_time;
        colonize.onclick = () => command('colonize',{x,y});
        result.append(colonize);
        const relocate = document.createElement('button');
        relocate.type = 'button';
        relocate.className = 'compact';
        const costs = state.relocation_cost || [];
        const coolingDown = (state.relocation_ready_at || 0) > state.server_time;
        relocate.disabled = water || Boolean(sectorRule) || ruinUntil > state.server_time || coolingDown || state.buildings.hq < 3
          || !costs.length || costs.some((cost,index) => state.resources[index] < cost);
        relocate.textContent = coolingDown
          ? `Versetzung wieder ab ${new Date(state.relocation_ready_at*1000).toLocaleString(globalThis.FURI18n?.locale || 'de-DE')}`
          : `Aktive Kolonie nach ${x}:${y} versetzen · ${costs.map(number).join(' / ')}`;
        relocate.onclick = () => {
          if (window.confirm(`Aktive Kolonie nach ${x}:${y} versetzen? Der Umzug kostet Rohstoffe und ist danach sieben Tage gesperrt.`)) {
            command('colony_relocate',{world_id:state.active_world.id,colony_id:state.colony_id,x,y});
          }
        };
        result.append(relocate);
      }
  }
}
function parseMapCoordinate(value) {
  const coordinate = /^(\d{1,2})\s*[:,]\s*(\d{1,2})$/.exec(String(value).trim());
  if (!coordinate) return null;
  const x = Number(coordinate[1]), y = Number(coordinate[2]);
  return x < MAP_SIZE && y < MAP_SIZE ? [x,y] : null;
}
function jumpToSector(x, y) {
  if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || y < 0 || x >= MAP_SIZE || y >= MAP_SIZE) return;
  mapX = Math.max(0, Math.min(MAP_MAX_START, x - Math.floor(MAP_VIEW_SIZE / 2)));
  mapY = Math.max(0, Math.min(MAP_MAX_START, y - Math.floor(MAP_VIEW_SIZE / 2)));
  render();
}
function openMission(id) {
  const ruin=id.startsWith('ruin:'), player=id.startsWith('player:');
  const targetId=ruin?id.slice(5):player?id.slice(7):id;
  const matchingAttack=ruin?undefined:(state.terra_alliance_attacks||[]).find(attack=>attack.target_kind===(player?'player':'outpost')&&attack.target_id===targetId&&!attack.joined);
  const listedTarget=ruin?(state.terra_ruin_targets||[]).find(item=>item.id===targetId):player?state.players.find(p=>p.id===targetId):state.world.find(t=>t.id===targetId);
  target=listedTarget?(ruin?{...listedTarget,name:`Kolonieruine ${listedTarget.x}:${listedTarget.y}`,owner:null,isRuin:true}:player?{...listedTarget,isPlayer:true}:listedTarget):matchingAttack?{id:targetId,name:matchingAttack.target_name,x:matchingAttack.x,y:matchingAttack.y,owner:null,travel_seconds:0,isPlayer:player}:undefined;
  if (!target) return;
  const own = !player && target.owner===state.id;
  const targetKind=player?'player':'outpost';
  const matchingAllianceAttacks=ruin?[]:(state.terra_alliance_attacks||[]).filter(attack=>attack.target_kind===targetKind&&attack.target_id===target.id&&!attack.joined);
  const knownIntel = combatIntelKnown(target,player,own,state.server_time);
  $('target-name').textContent=target.name;
  const intel=target.intel_report;
  const intelStatus=intel ? ` · Aufklärung Stufe ${intel.level}, ${intel.status==='fresh'?'aktuell bis '+new Date(intel.expires_at*1000).toLocaleTimeString(globalThis.FURI18n?.locale || 'de-DE'):'veraltet'}${intel.data?.hq?` · Kommandozentrale ${intel.data.hq}`:''}${intel.data?.buildings?` · Gebäude ${Object.entries(intel.data.buildings).map(([k,v])=>`${k} ${v}`).join(', ')}`:''}${knownIntel?` · Verteidigung ${number(intel.data.defense)}, Garnison ${intel.data.garrison}`:''}` : '';
  $('target-info').textContent=ruin ? `Aktive Kolonieruine im bekannten Sektor ${target.x}:${target.y}. Nur Ranger können sie vor Ablauf erkunden; Ergebnisse und Gefahrenbericht bleiben privat.` : player ? `Spielerkolonie ${target.x}:${target.y}${intelStatus}${knownIntel?'':' · Militärstärke unbekannt'} · ${target.protected_until>state.server_time?'Neulingsschutz aktiv':target.vacation_until>state.server_time?'Urlaubsmodus aktiv':(state.world_pvp_enabled??state.flags.pvp)?'PvP verfügbar':'Spielerangriffe deaktiviert'}.` : !knownIntel ? `Sektor ${target.x}:${target.y} · Besetzter Außenposten · Militärstärke unbekannt, Aufklärung erforderlich.` : `Sektor ${target.x}:${target.y} · Verteidigung ${number(target.defense)} · Garnison ${target.garrison??Object.values(target.units||{}).reduce((a,b)=>a+b,0)}. Deine Taktik: Stufe ${state.tech.tactics}.`;
  $('mission-mode-label').hidden=false;
  const modes=ruin?'<option value="ruin_exploration">Ruinenerkundung</option>':own?'<option value="station">Garnison verstärken</option><option value="recall">Garnison zurückrufen</option>':player?'<option value="scout">Aufklärung</option><option value="attack">Angriff</option><option value="transport">Rohstofftransport</option>':'<option value="attack">Überfall</option><option value="expedition">Expedition</option>';
  const playerEligible=!player||((state.world_pvp_enabled??state.flags.pvp)&&Number(target.protected_until||0)<=state.server_time&&Number(target.vacation_until||0)<=state.server_time);
  const canCreateAllianceAttack=Boolean(!ruin&&state.membership&&!own&&playerEligible&&(player||target.owner===null));
  $('mission-mode').innerHTML=modes+(canCreateAllianceAttack?'<option value="alliance_attack_create">Allianzangriff eröffnen</option>':'')+(matchingAllianceAttacks.length?'<option value="alliance_attack_join">Allianzangriff beitreten</option>':'');
  $('mission-operation').innerHTML=matchingAllianceAttacks.map(attack=>`<option value="${escapeHtml(attack.id)}">${escapeHtml(attack.target_name)} · ${attack.participant_count}/12 · Ende ${new Date(attack.join_until*1000).toLocaleTimeString(globalThis.FURI18n?.locale || 'de-DE')}</option>`).join('');
  $('mission-operation-label').hidden=true;
  $('mission-mode').value=ruin?'ruin_exploration':own?'station':player?'scout':'attack';
  $('mission-template-select').closest('section').hidden=ruin;
  $('cargo-fields').hidden=true;
  $('capture').parentElement.hidden=ruin||player||own;
  $('army-select').innerHTML=Object.entries(state.catalog.units).filter(([key])=>!ruin||key==='ranger').map(([key,u])=>`<label>${u.name} (${state.units[key]} verfügbar)<input type="number" name="${key}" value="${state.units[key]}" min="0" max="${state.units[key]}" required></label>`).join('')+'<p id="power-preview" role="status" aria-live="polite"></p>';
  $('mission-template-select').innerHTML=missionTemplateOptions(missionTemplates);
  $('mission-template-status').textContent='';
  $('mission-mode').onchange();
  const travel=target.travel_seconds;
  const reachable=Number.isInteger(travel);
  $('mission-form').querySelector('[type="submit"]').disabled=!reachable||(ruin&&(!state.units.ranger||state.active_world?.terra_ruin_exploration_ruleset!=='FUR-3-TERRA-RUIN-EXPLORATION-1'));
  $('simulate-battle').hidden=true;
  $('battle-simulation').textContent='';
  const defense=knownIntel?(player?intel.data.defense:target.defense):undefined;
  let movementRequest=0, movementTimer;
  const preview=()=>{
    const fields=$('mission-form').elements;
    const army=ruin?{ranger:Number(fields.ranger.value)}:Object.fromEntries(Object.keys(state.units).map(key=>[key,Number(fields[key].value)]));
    const power=Math.floor(Object.entries(state.catalog.units).reduce((n,[k,u])=>n+(army[k]||0)*u.power,0)*(100+15*state.tech.tactics)/100);
    const base=!reachable?'Kein begehbarer Weg zum Ziel.':ruin?(!state.units.ranger?'Keine Ranger verfügbar.':`Hin- und Rückweg ${2*travel} s`):defense===undefined?`Kampfkraft ${number(power)} · Gegnerische Stärke unbekannt · Hin- und Rückweg ${2*travel}s`:`Kampfkraft ${number(power)} · Verteidigung ${number(defense)} · Hin- und Rückweg ${2*travel}s${power>defense?' · voraussichtlicher Sieg':' · Verluste möglich'}`;
    $('power-preview').textContent=base;
    if(!['FUR-3-TERRA-COMBAT-3','FUR-3-TERRA-COMBAT-4','FUR-3-TERRA-COMBAT-5'].includes(state.active_world?.terra_combat_ruleset)||Object.values(army).every(count=>count===0))return;
    clearTimeout(movementTimer);
    movementTimer=setTimeout(async()=>{
      const request=++movementRequest;
      try{
        const quote=(await api('simulate-movement',{target_id:target.id,army,...(ruin?{target_kind:'ruin'}:{})})).movement;
        if(request!==movementRequest)return;
        $('power-preview').textContent=`${base} · FUR-3-Marsch ${number(quote.travel_seconds)} s je Strecke · Treibstoff ${number(quote.fuel_ore)} Erz für Hin- und Rückweg${quote.affordable?'':' · Erzbestand reicht nicht'}`;
      }catch(error){if(request===movementRequest)$('power-preview').textContent=`${base} · Bewegungsprobe: ${error.message}`;}
    },180);
  };
  $('army-select').oninput=preview; preview(); $('capture').checked=false; $('mission').showModal();
}
$('close-mission').onclick=()=>$('mission').close();
$('load-mission-template').onclick=()=>{
  const template=missionTemplates.find(item=>item.id===$('mission-template-select').value);
  if(!template){$('mission-template-status').textContent='Wähle zuerst eine Vorlage.';return;}
  if(![...$('mission-mode').options].some(option=>option.value===template.mode)){$('mission-template-status').textContent='Diese Vorlage passt nicht zu diesem Ziel.';return;}
  $('mission-mode').value=template.mode;
  $('mission-mode').dispatchEvent(new Event('change'));
  for(const key of Object.keys(state.units)){
    const field=$('mission-form').elements[key];
    field.value=Math.min(template.army[key]||0,Number(field.max));
  }
  $('capture').checked=Boolean(template.capture)&&!target.isPlayer&&target.owner!==state.id;
  $('army-select').dispatchEvent(new Event('input',{bubbles:true}));
  $('mission-template-status').textContent=`Vorlage „${template.name}“ geladen. Verfügbare Truppen wurden berücksichtigt.`;
};
$('save-mission-template').onclick=async()=>{
  const army=Object.fromEntries(Object.keys(state.units).map(key=>[key,Number($('mission-form').elements[key].value)]));
  try{
    const result=await api('mission-templates',{name:$('mission-template-name').value,mode:$('mission-mode').value,army,capture:$('capture').checked});
    missionTemplates.push(result.template);
    $('mission-template-select').innerHTML=missionTemplateOptions(missionTemplates);
    $('mission-template-select').value=result.template.id;
    $('mission-template-name').value='';
    $('mission-template-status').textContent=`Vorlage „${result.template.name}“ gespeichert.`;
  }catch(error){$('mission-template-status').textContent=error.message;}
};
$('delete-mission-template').onclick=async()=>{
  const id=$('mission-template-select').value;
  if(!id){$('mission-template-status').textContent='Wähle zuerst eine Vorlage.';return;}
  try{
    await api(`mission-templates/${encodeURIComponent(id)}`,undefined,'DELETE');
    missionTemplates=missionTemplates.filter(item=>item.id!==id);
    $('mission-template-select').innerHTML=missionTemplateOptions(missionTemplates);
    $('mission-template-status').textContent='Vorlage gelöscht.';
  }catch(error){$('mission-template-status').textContent=error.message;}
};
$('simulate-battle').onclick=async()=>{
  const army=Object.fromEntries(Object.keys(state.units).map(key=>[key,Number($('mission-form').elements[key].value)]));
  try {
    const result=(await api('simulate-battle',{target_id:target.id,army})).simulation;
    if(result.simulation) {
      const estimate=result.simulation;
      const range=values=>`${number(values[0])}–${number(values[1])}`;
      const loot=estimate.loot?` · Beuteband ${estimate.loot.map(range).join(' / ')}`:' · Beute unbekannt (nicht aufgeklärte Ressourcen)';
      const mineChance=Number.isFinite(estimate.terra_defense?.minefield_trigger_percent)?` · geschätzte Minenauslösung ${number(estimate.terra_defense.minefield_trigger_percent)} %`:'';
      $('battle-simulation').textContent=`FUR-3-Schätzung aus ${number(estimate.samples)} reproduzierbaren Szenarien · geschätzte Siegchance ${number(estimate.attacker_victory_percent)} % · eigene Verluste ${range(estimate.attacker_losses_total)} · Überlebende ${range(estimate.attacker_survivors_total)}${mineChance}${loot}`;
      return;
    }
    const survivors=Object.entries(result.attacker_survivors).filter(([,count])=>count>0).map(([key,count])=>`${state.catalog.units[key].name} ${number(count)}`).join(', ')||'keine';
    const losses=Object.entries(army).reduce((sum,[key,count])=>sum+count-(result.attacker_survivors[key]||0),0);
    const loot=result.loot?`Beute ${result.loot.map(number).join(' / ')}`:'Beute unbekannt (nicht aufgeklärte Ressourcen)';
    $('battle-simulation').textContent=`Deterministische FUR-2-Projektion auf Basis des aktuellen ${target.isPlayer?'Stufe-2-Aufklärungsberichts':'Zielzustands'} · ${result.victory?'Sieg':'Niederlage'} · Kampfkraft ${number(result.power)} / Verteidigung ${number(result.defense)} · eigene Verluste ${number(losses)} · Überlebende ${survivors} · ${loot}`;
  } catch(error) { $('battle-simulation').textContent=error.message; }
};
$('mission-mode').onchange=()=>{
  const mode=$('mission-mode').value, expedition=mode==='expedition', ruinExploration=mode==='ruin_exploration';
  const allianceCreate=mode==='alliance_attack_create', allianceJoin=mode==='alliance_attack_join';
  const player=Boolean(target.isPlayer), own=!player&&target.owner===state.id;
  const knownIntel=combatIntelKnown(target,player,own,state.server_time);
  const playerPreview=player&&mode==='attack'&&knownIntel&&(state.world_pvp_enabled??state.flags.pvp)&&Number(target.protected_until||0)<=state.server_time&&Number(target.vacation_until||0)<=state.server_time;
  const neutralPreview=!target.isPlayer&&!expedition&&!ruinExploration&&target.owner!==state.id;
  const combatAvailable=Number.isInteger(target.travel_seconds)&&(playerPreview||neutralPreview);
  const missionCombatAvailable=combatAvailable&&!allianceCreate&&!allianceJoin;
  $('cargo-fields').hidden=mode!=='transport';
  $('mission-operation-label').hidden=!allianceJoin;
  [0,1,2].forEach(i=>{const cargo=$(`cargo-${i}`);cargo.max=state.resources[i];if(mode!=='transport')cargo.value=0;});
  $('save-mission-template').hidden=mode==='recall'||allianceCreate||allianceJoin;
  $('capture').closest('label').hidden=!missionCombatAvailable||player||own;
  if(!combatAvailable)$('capture').checked=false;
  $('simulate-battle').hidden=!missionCombatAvailable;
  $('battle-simulation').hidden=!missionCombatAvailable;
  const dropRules=state.expedition_item_drops;
  const dropSummary=dropRules?.enabled?(dropRules.drops||[]).map(drop=>`${drop.item_name}: ${number(drop.chance_basis_points/100)} % bei Fund, Vorratsfund oder Patrouille (${number(drop.overall_chance_basis_points/100)} % je Expedition), maximal ${number(drop.max_per_mission)} Stück je Expedition.`).join(' '):'Gegenstandsfunde sind aus; sie benötigen die ausdrückliche FUR-3-Gegenstands-Opt-in-Weltregel.';
  $('mission-mode-note').textContent=ruinExploration?`FUR-3-TERRA-RUIN-EXPLORATION-1 · Entwurfsbalance. Nur Ranger können die aktive Ruine untersuchen. Der missionsgebundene Ergebniswurf aktualisiert private Sektordaten und gewährt 24 Stunden private Ruinenbeobachtung.`:expedition?`${expeditionCatalogSummary(state.expedition_rules)} ${dropRules?.version||''}: ${dropSummary} Ergebnis und Rückkehr erfolgen automatisch.`:allianceCreate?'FUR-3-TERRA-ACS-2 · Sammelphase 5 Minuten · 2–12 Allianzmitglieder · gemeinsame Ankunft und FUR-2-Kampfauswertung.':allianceJoin?'FUR-3-TERRA-ACS-2 · Deine Truppen werden bis zum gemeinsamen Angriff reserviert. Du kannst vor Ende der Sammelphase aussteigen.':'';
  $('mission-risk').textContent=ruinExploration?'Die Ranger bleiben bis zur Rückkehr gebunden. Das Ergebnis ist deterministisch pro Auftrag: Fund, Bergung, instabile Ruine, Gefahr oder keine Vorkommnisse. Verluste sind auf den im Ruleset angegebenen Anteil begrenzt; Rohstofffunde bleiben innerhalb der Traglast. Vor der Ankunft kannst du die Mission zurückrufen.':expedition?'Die Truppen bleiben bis zur Rückkehr gebunden. Ergebnis und Itemwurf sind pro Expedition reproduzierbar; Rohstoffbeute hat Vorrang vor Gegenständen bei der Trägerkapazität. Ein Rückruf vor Ankunft bricht die Mission ab.':allianceCreate||allianceJoin?'Truppen und Verluste werden jedem Mitglied einzeln zugeordnet. Überlebende und Beute kehren an die jeweilige Ausgangskolonie zurück.':mode==='station'?'Die Truppen bleiben bis zur Garnisonsankunft gebunden. Ist der Außenposten dann nicht mehr deiner, kehren sie zurück.':mode==='recall'?'Die ausgewählte Garnison kehrt zur Kolonie zurück.':mode==='transport'?'Die Fracht wird vor dem Abflug reserviert und bei Zustellung ins Zieldepot gebucht. Träger kehren danach zurück.':mode==='scout'?scoutMissionRisk(state.active_world):'Bei Niederlage gehen die entsandten Truppen verloren. Plane deine Kampfkraft mit Reserve.';
  if(mode==='recall') {
    Object.keys(state.units).forEach(k=>{const e=$('mission-form').elements[k];e.max=target.units?.[k]||0;e.value=target.units?.[k]||0;});
  } else if(ruinExploration) {
    const input=$('mission-form').elements.ranger;
    input.min=1;
    input.value=Math.min(1,state.units.ranger);
  } else {
    Object.keys(state.units).forEach(k=>{const e=$('mission-form').elements[k];e.max=state.units[k];e.value=mode==='scout'?(k==='ranger'?Math.min(1,state.units[k]):0):state.units[k];});
  }
};
$('mission-form').onsubmit=async e=>{
  e.preventDefault();
  const mode=$('mission-mode').value;
  const fields=e.currentTarget.elements;
  const army=mode==='ruin_exploration'?{ranger:Number(fields.ranger.value)}:Object.fromEntries(Object.keys(state.units).map(k=>[k,Number(fields[k].value)]));
  const action=mode==='ruin_exploration'?'ruin_exploration':mode==='expedition'?'expedition':mode==='alliance_attack_create'?'alliance_attack_create':mode==='alliance_attack_join'?'alliance_attack_join':target.isPlayer||target.owner===state.id?mode:'raid';
  const payload={key:mode==='alliance_attack_join'?$('mission-operation').value:target.id,army,capture:$('capture').checked};
  if(mode==='alliance_attack_create')payload.target_kind=target.isPlayer?'player':'outpost';
  if(action==='transport') payload.resources=[0,1,2].map(i=>Number($('cargo-'+i).value));
  if(await command(action,payload)) $('mission').close();
};
async function refresh() { if (busy || document.hidden || window.furRecoveryCodesPending) return; try { await gameAssetCatalogReady; const next=await api('state'); csrf=next.csrf; state=next; await loadMissionTemplates(next.id); await loadProductionTemplates(next.id); await loadPushState(next.id); if($('game').hidden) await showGame(); else render(); } catch(error) { if(error.status===401 && state) {state=undefined;missionTemplates=[];missionTemplateOwner='';productionTemplates=[];productionTemplateOwner='';pushUiState={user:'',enabled:false,subscribed:false,count:0,status:''};$('game').hidden=true;$('auth').hidden=false;notify('Die Sitzung ist abgelaufen. Bitte erneut anmelden.');}else if(state) $('sync').textContent='Verbindung unterbrochen · erneuter Versuch …'; } }
refresh(); setInterval(refresh,3000);





