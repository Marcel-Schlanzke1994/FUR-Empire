const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

test('production graph shows exact server components, capacity forecast and pause accessibly',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(source,/\+ productionGraphMarkup\(state\.production_details\)/);
  const helper=source.match(/function productionGraphMarkup\(details\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'production graph renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,names:['Holz','Stein','Erz'],icons:['♣','▧','◈'],number:String,assetImage:()=>'',resourceIcon:()=>''});
  vm.runInContext(helper,box);
  const markup=box.productionGraphMarkup([
    {per_second_ten_thousandths:27600,base_per_second:4,bonus_percent:20,terrain:'Wald',terrain_percent:115,storage:100,storage_cap:4000,seconds_to_cap:1413043,paused:false},
    {per_second_ten_thousandths:12000,base_per_second:2,bonus_percent:0,terrain:'Ebene',terrain_percent:100,storage:4000,storage_cap:4000,seconds_to_cap:null,paused:false},
    {per_second_ten_thousandths:0,base_per_second:2,bonus_percent:0,terrain:'<Erz>',terrain_percent:100,storage:0,storage_cap:4000,seconds_to_cap:null,paused:true}
  ]);
  assert.match(markup,/<summary>Produktionsgrafik<\/summary>/);
  assert.match(markup,/aria-label="Aktuelle Rohstoffproduktion"/);
  assert.match(markup,/Basis 4\/s · Bonus 20% · Wald 115%/);
  assert.match(markup,/Depot voll in ca\. 23551 min/);
  assert.match(markup,/Depot voll/);
  assert.match(markup,/Produktion pausiert/);
  assert.match(markup,/&lt;Erz&gt;/);
  assert.match(markup,/aria-label="Erz: 0\.00 pro Sekunde"/);
  assert.equal(box.productionGraphMarkup([]),'');
});

test('neutral goods stay usable without images and escape all catalog labels',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function neutralMarketMarkup\(market\) \{[\s\S]*?\n\}/)?.[0];
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  const markup=box.neutralMarketMarkup({goods:[{id:'wood',name:'<Holz>',description:'<unsafe>',value:1,amount:90},{id:'alloy',name:'Legierung',description:'Material',value:3,amount:3995,reserve_amount:12,incoming_amount:0}],material_stacks:{used:2,available_types:7},payout_percent:50,capacity:4000,minimum_amount:10,maximum_amount:100000,version:'<rules>'});
  assert.ok(markup.includes('id="goods-trade-form"'));
  assert.ok(markup.includes('Materialstapel: 2 von 7 Warenarten belegt.'));
  assert.ok(markup.includes('role="status"'));
  assert.ok(markup.includes('&lt;Holz&gt;'));
  assert.ok(markup.includes('&lt;unsafe&gt;'));
  assert.ok(!markup.includes('<unsafe>'));
  assert.ok(markup.includes('/static/assets/goods/wood.svg'));
  assert.ok(markup.includes('data-goods-claim="alloy" data-goods-amount="5"'));
});

test('generic item inventory shows reserved inbound stacks and only claimable reserve amounts',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function genericItemInventoryMarkup\(inventory\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'generic item inventory renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String,assetImage:()=>'',gameAssetKey:()=>''});
  vm.runInContext(helper,box);
  const markup=box.genericItemInventoryMarkup({version:'FUR-ITEM-INVENTORY-1',used_stack_types:1,max_stack_types:6,stack_limit:1000,items:[{id:'repair_kit',name:'<Kit>',description:'Safe',amount:995,incoming_amount:0,reserve_amount:12}]});
  assert.ok(markup.includes('data-item-claim="repair_kit" data-item-amount="5"'));
  assert.ok(markup.includes('&lt;Kit&gt;'));
  assert.ok(markup.includes('Reserve: 12'));
});

test('commander progression exposes earned XP and accessible skill allocation only when enabled',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function commanderMarkup\([^\n]+\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'commander progression renderer must be available');
  assert.match(source,/data-hero-stat/);
  assert.match(source,/hero_ruleset:form\.elements\.hero_ruleset\.value/);
  assert.match(source,/hero_doctrine_ruleset:form\.elements\.hero_doctrine_ruleset\.value/);
  assert.match(source,/hero_respec_ruleset:form\.elements\.hero_respec_ruleset\.value/);
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  assert.match(box.commanderMarkup({enabled:false}),/nicht aktiviert/);
  const markup=box.commanderMarkup({enabled:true,rules_version:'<draft>',level:2,level_cap:20,experience:100,experience_to_next:200,skill_points:1,stat_cap:10,available_stats:['economy','military','recon','command'],stats:{military:1,economy:1,recon:1,command:1}},{enabled:true,rules_version:'FUR-3-HERO-2',bonuses:{production_percent:2,combat_damage_percent:2,intel_lifetime_percent:10,mission_slots:1}});
  assert.match(markup,/&lt;draft&gt;/);
  assert.match(markup,/aria-label="Skillpunkt für Wirtschaft vergeben"/);
  assert.match(markup,/FUR-3-HERO-2/);
  assert.match(markup,/10 % Berichtsdauer/);
  assert.match(markup,/200 XP bis Stufe 3/);
  assert.match(markup,/2 % Rohstoffproduktion je Stufe/);
  assert.doesNotMatch(markup,/data-hero-stat="economy"[^>]*disabled/);
  assert.doesNotMatch(markup,/data-hero-stat="military"[^>]*disabled/);
  const reset=box.commanderMarkup({enabled:true,rules_version:'FUR-3-HERO-1',level:2,level_cap:20,experience:100,experience_to_next:200,skill_points:0,stat_cap:10,available_stats:['economy'],stats:{military:0,economy:1,recon:0,command:0}},{enabled:false,bonuses:{}},{enabled:true,rules_version:'FUR-3-HERO-3',cost:{wood:250,stone:250,ore:250},cooldown_seconds:604800,available_at:0,has_allocated_stats:true},[1000,1000,1000],100);
  assert.match(reset,/250 Holz, 250 Stein und 250 Erz/);
  assert.match(reset,/Abklingzeit: 7 Tage/);
  assert.match(reset,/data-hero-respec(?![^>]*disabled)/);
  const cooldown=box.commanderMarkup({enabled:true,rules_version:'FUR-3-HERO-1',level:2,level_cap:20,experience:100,experience_to_next:200,skill_points:0,stat_cap:10,available_stats:['economy'],stats:{military:0,economy:1,recon:0,command:0}},{enabled:false,bonuses:{}},{enabled:true,rules_version:'FUR-3-HERO-3',cost:{wood:250,stone:250,ore:250},cooldown_seconds:604800,available_at:200,has_allocated_stats:true},[1000,1000,1000],100);
  assert.match(cooldown,/data-hero-respec[^>]*disabled/);
  const legacy=box.commanderMarkup({enabled:true,rules_version:'FUR-3-HERO-1',level:2,level_cap:20,experience:100,experience_to_next:200,skill_points:1,stat_cap:10,available_stats:['economy'],stats:{military:0,economy:0,recon:0,command:0}},{enabled:false,bonuses:{}});
  assert.match(legacy,/data-hero-stat="military"[^>]*disabled/);
});

test('alliance role permissions are shown only to the leader and stay separate from server roles',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceRolePermissionsMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance permission editor renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const commandForm=(action,body,label)=>`<form data-system="${action}">${body}<button>${label}</button></form>`;
  const box=vm.createContext({escapeHtml,commandForm,state:{membership:{role:'leader'},alliance_permission_catalog:[{id:'invitations',label:'Einladungen verwalten'}],alliance_role_permissions:{officer:['invitations'],member:[]}}});
  vm.runInContext(helper,box);
  const markup=box.allianceRolePermissionsMarkup();
  assert.match(markup,/name="role" value="officer"/);
  assert.match(markup,/name="permission" value="invitations" checked/);
  assert.match(markup,/Servermoderation sind hier nicht vergebbar/);
  box.state.membership.role='officer';
  assert.equal(box.allianceRolePermissionsMarkup(),'');
});

test('alliance leadership proposals show consent actions only to their successor',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceTransferMarkup\(transfer,userId\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'leadership transfer renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${id}">${label}</button>`;
  const box=vm.createContext({escapeHtml,actionButton});
  vm.runInContext(helper,box);
  const transfer={id:'request-1',leader_id:'leader',successor_id:'successor',leader_name:'<Alpha>',successor_name:'<Bravo>',created:1};
  const successor=box.allianceTransferMarkup(transfer,'successor');
  assert.match(successor,/&lt;Alpha&gt; hat &lt;Bravo&gt;/);
  assert.match(successor,/Führung bleibt bis zur Annahme unverändert/);
  assert.match(successor,/alliance_transfer_accept/);
  assert.match(successor,/alliance_transfer_decline/);
  assert.doesNotMatch(successor,/alliance_transfer_cancel/);
  const leader=box.allianceTransferMarkup(transfer,'leader');
  assert.match(leader,/alliance_transfer_cancel/);
  assert.doesNotMatch(leader,/alliance_transfer_accept/);
  assert.equal(box.allianceTransferMarkup(null,'leader'),'');
});

test('public alliance wars escape labels and expose peace controls only to a member party',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceWarsMarkup\(own,canDiplomacy\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'public alliance war renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${id}">${label}</button>`;
  const number=String;
  const state={alliance_wars:[{id:'war-1',alliance_a:'a',alliance_b:'b',alliance_a_tag:'<AAA>',alliance_b_tag:'BBB',alliance_a_name:'Alpha',alliance_b_name:'Bravo',status:'peace_offered',peace_offered_by:'a',score_a:12,score_b:7,target_points:1000,rules_version:'FUR-3-ALLIANCE-WAR-1',started:1}],alliance_war_events:[{created:1,event_type:'battle_score',actor_tag:'<AAA>',alliance_a_tag:'AAA',alliance_b_tag:'BBB',details:{attacker_losses:2,defender_losses:3,score_a:12,score_b:7}}]};
  const box=vm.createContext({escapeHtml,actionButton,number,state});
  vm.runInContext(helper,box);
  const own={id:'a'};
  const party=box.allianceWarsMarkup(own,true);
  assert.match(party,/&lt;AAA&gt;/);
  assert.match(party,/alliance_peace_cancel/);
  assert.doesNotMatch(party,/alliance_peace_accept/);
  assert.match(party,/FUR-3-Entwurfswertung/);
  assert.match(party,/12 : 7/);
  const opponent=box.allianceWarsMarkup({id:'b'},true);
  assert.match(opponent,/alliance_peace_accept/);
  assert.match(opponent,/alliance_peace_decline/);
  const outsider=box.allianceWarsMarkup({id:'c'},true);
  assert.doesNotMatch(outsider,/data-system-action="alliance_peace_/);
  assert.match(outsider,/Kriegswertung aktualisiert|Gefechtswertung aktualisiert/);
});

test('home designation is offered only for owned nonhome entries in active world',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function colonyHomeMarkup\(colony\) \{[\s\S]*?\n\}/)?.[0];
  const box=vm.createContext({state:{active_world:{id:1},home_designation:{available:true}},escapeHtml:String});
  vm.runInContext(helper,box);
  assert.equal(box.colonyHomeMarkup({is_home:true,world_id:1}),'');
  assert.equal(box.colonyHomeMarkup({is_home:false,world_id:2}),'');
  assert.ok(box.colonyHomeMarkup({colony_id:'owned',is_home:false,world_id:1}).includes('data-action="colony_home"'));
});

function context(extra={}) {
  const box={...extra};
  vm.createContext(box);
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8'),box);
  return box;
}

test('active world label follows the selected world with a Genesis fallback',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function activeWorldLabel\(world\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'active world label formatter must be available for rendering tests');
  const box=vm.createContext({});
  vm.runInContext(helper,box);
  assert.equal(box.activeWorldLabel({id:2,name:'Browser QA World'}),'Browser QA World · WELT 02');
  assert.equal(box.activeWorldLabel(null),'Genesis · WELT 01');
});

test('progression directives disclose locked order and expose only the next claim',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function directivesMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'directive progression renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({
    escapeHtml,number:String,assetImage:()=>'',
    state:{claimed:['economy'],quests:[
      {id:'economy',name:'<Economy>',reward:400,done:true,unlocked:true},
      {id:'army',name:'Mobilmachung',reward:300,done:true,unlocked:true},
      {id:'science',name:'Neues Wissen',reward:500,done:true,unlocked:false}
    ]}
  });
  vm.runInContext(helper,box);
  const markup=box.directivesMarkup();
  assert.ok(markup.includes('&lt;Economy&gt;'));
  assert.match(markup,/Gesperrt · zuerst die vorherige Direktive abholen/);
  assert.match(markup,/data-quest="army"[^>]*aria-label="Mobilmachung: Abholen"/);
  assert.match(markup,/data-quest="science"[^>]*aria-label="Neues Wissen: Gesperrt"[^>]*disabled/);
});

test('ranking pages announce the absolute position and safely render later pages',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function rankingListMarkup\(entries, offset, hasMore\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'ranking renderer must be available for pagination checks');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:value=>String(value)});
  vm.runInContext(helper,box);
  const markup=box.rankingListMarkup([{name:'<Pilot>',score:70}],50,true);
  assert.ok(markup.includes('<strong>51</strong>'));
  assert.ok(markup.includes('&lt;Pilot&gt;'));
  assert.ok(markup.includes('data-ranking-more'));
  assert.ok(!box.rankingListMarkup([],0,false).includes('data-ranking-more'));
  assert.match(source,/data-ranking-category/);
  assert.match(source,/aria-pressed/);
  assert.match(source,/ranking_categories/);
  for (const label of ['Wirtschaft','Forschung','PvE','Krieg','Allianz','Regionen']) assert.ok(source.includes(label));
});

test('FUR-3 military ranking labels draft scoring and exposes personal audit rows',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(source,/Ein Punkt je verlorener Einheit/);
  assert.match(source,/bestätigte alliierte Garnisonen geben einmal je 24 Stunden einen Unterstützungspunkt pro stationierter Einheit/);
  assert.match(source,/Eigene Militärpunkte prüfen/);
  assert.match(source,/state\.military_score_audit/);
  assert.match(source,/state\.alliance_military_ranking/);
});

test('season view displays archived versioned alliance standings',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  assert.match(source,/FUR-3-Allianzarchiv/);
  assert.match(source,/s\.alliance_standings/);
  assert.match(source,/s\.alliance_rules_digest/);
  const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(app,/season\.category_standings/);
  assert.match(app,/season\.ranking_rules_version/);
  assert.match(app,/Hall of Fame/);
  assert.match(app,/hall\.bosses/);
  assert.match(app,/hall\.wars/);
  assert.match(app,/prestige\.milestones/);
  assert.match(app,/ohne Kampf- oder Ranglistenbonus/);
});

test('hall of fame exposes world scoped season, alliance, boss and war record sections',()=>{
  const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(app,/id="hall-of-fame-title"/);
  assert.match(app,/hall\.seasons/);
  assert.match(app,/hall\.alliances/);
  assert.match(app,/hall\.bosses/);
  assert.match(app,/hall\.wars/);
  const systems=fs.readFileSync(path.join(__dirname,'../fur_empire/systems.py'),'utf8');
  assert.match(systems,/def hall_of_fame/);
  assert.match(systems,/e\.world_id=\?/);
});

test('alliance treasury view exposes scoped balances, approvals and owner-approved fee rules',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  assert.match(source,/function allianceTreasuryMarkup\(\)/);
  assert.match(source,/Allianzkasse/);
  assert.match(source,/5\.000 Brutto-Ressourcen/);
  assert.match(source,/1 % je Ressource/);
  assert.match(source,/alliance_treasury_approve/);
  assert.match(source,/alliance_treasury_cancel/);
  assert.match(source,/alliance_treasury_ledger/);
  assert.match(source,/FUR-3-Regeln freigegeben/);
  assert.match(source,/gewünschte Auszahlung/);
  assert.match(source,/zusätzlich 1 % je Ressource als Gebühr/);
  assert.match(source,/data\.resources=\[0,1,2\]/);
});

test('alliance projects view exposes bounded contributions, refunds and non-economic completion records',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  assert.match(source,/function allianceProjectMarkup\(\)/);
  assert.match(source,/alliance_project_create/);
  assert.match(source,/alliance_project_contribute/);
  assert.match(source,/alliance_project_cancel/);
  assert.match(source,/Überschüsse werden abgewiesen/);
  assert.match(source,/keine Ressourcen-, Produktions-, Kampf- oder Ranglistenboni/);
  assert.match(source,/data\.resources=\[0,1,2\]/);
});

test('alliance directory renders escaped public entries and a bounded next-page control',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceDirectoryMarkup\(own,officer\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance directory renderer must be available for pagination checks');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${id}">${label}</button>`;
  const box=context({escapeHtml,state:{membership:null,alliances:[{id:'a1',tag:'<ONE>',name:'<League>',size:4,diplomacy_status:'nap',diplomacy_accepted:1,diplomacy_proposed_by:'own'}],alliances_has_more:true},actionButton});
  vm.runInContext(helper,box);
  const markup=box.allianceDirectoryMarkup(null,false);
  assert.ok(markup.includes('&lt;ONE&gt;'));
  assert.ok(markup.includes('&lt;League&gt;'));
  assert.ok(markup.includes('data-system-action="alliance_apply"'));
  assert.ok(markup.includes('data-alliance-directory-more'));
  assert.ok(markup.includes('nap aktiv'));
  box.state.alliances[0].application_id='my-application';
  assert.ok(box.allianceDirectoryMarkup(null,false).includes('data-system-action="alliance_application_withdraw"'));
  box.state.alliances_has_more=false;
  assert.ok(!box.allianceDirectoryMarkup(null,false).includes('data-alliance-directory-more'));
});

test('alliance roster exposes a bounded load-more control only when another page exists',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceMembersMoreMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance roster pagination renderer must be available');
  const box=context({state:{members_has_more:true}});
  vm.runInContext(helper,box);
  assert.ok(box.allianceMembersMoreMarkup().includes('data-alliance-members-more'));
  assert.ok(box.allianceMembersMoreMarkup().includes('aria-live="polite"'));
  box.state.members_has_more=false;
  assert.equal(box.allianceMembersMoreMarkup(),'');
  assert.match(source,/alliance\/members\?before=/);
});

test('alliance invite candidates expose an accessible bounded load-more control',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const legacy=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function allianceCandidatesMoreMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance candidate pagination renderer must exist');
  const box=context({state:{alliance_candidates:[{id:'candidate-50'}],alliance_candidates_has_more:true}});
  vm.runInContext(helper,box);
  const markup=box.allianceCandidatesMoreMarkup();
  assert.ok(markup.includes('data-alliance-candidates-more'));
  assert.ok(markup.includes('aria-live="polite"'));
  box.state.alliance_candidates_has_more=false;
  assert.equal(box.allianceCandidatesMoreMarkup(),'');
  assert.match(source,/alliance\/candidates\?before=\$\{encodeURIComponent\(cursor\)\}/);
  assert.match(source,/state\.alliance_candidates\.push\(\.\.\.page\.candidates/);
  assert.doesNotMatch(legacy,/alliance_invite_candidates/);
  assert.match(legacy,/const candidates=state\.alliance_candidates\|\|\[\]/);
});

test('incoming attack status renders an exact count without exposing a mission detail list',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(source,/state\.incoming_count \? '⚑ '\+state\.incoming_count\+' feindliche Anmärsche'/);
  assert.doesNotMatch(source,/state\.incoming\?\.length/);
});

test('world player directory exposes its paged load-more control in social and map views',()=>{
  const community=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=community.match(/function playerDirectoryMoreMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'world player directory pagination renderer must exist');
  const box=context({state:{players:[{id:'p1'}],players_has_more:true}});
  vm.runInContext(helper,box);
  assert.ok(box.playerDirectoryMoreMarkup().includes('data-player-directory-more'));
  assert.ok(box.playerDirectoryMoreMarkup().includes('aria-live="polite"'));
  box.state.players_has_more=false;
  assert.equal(box.playerDirectoryMoreMarkup(),'');
  assert.match(community,/players\?before=\$\{encodeURIComponent\(cursor\)\}/);
  assert.match(community,/state\.players\.push\(\.\.\.page\.players/);
  const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(app,/Kommandanten in dieser Welt[\s\S]*?window\.playerDirectoryMoreMarkup\(\)/);
});

test('empire directory exposes accessible world and colony pagination',()=>{
  const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(app,/state.worlds_has_more\?'<button[^']*data-worlds-more/);
  assert.match(app,/state.empire_colonies_has_more\?'<button[^']*data-colonies-more/);
  assert.match(app,/worlds\?before=\$\{encodeURIComponent\(cursor\)\}/);
  assert.match(app,/colonies\?before=\$\{encodeURIComponent\(cursor\)\}/);
  assert.match(app,/state.worlds.push\(\.\.\.page.worlds/);
  assert.match(app,/state.empire_colonies.push\(\.\.\.page.colonies/);
  assert.match(app,/data-worlds-status aria-live="polite"/);
  assert.match(app,/data-colonies-status aria-live="polite"/);
});

test('alliance application pages render escaped owner actions and hide incoming review from members',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceApplicationsMarkup\(direction\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance application renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${id}">${label}</button>`;
  const box=context({escapeHtml,actionButton,state:{membership:{alliance_id:'a1',role:'officer'},alliance_permissions:['applications'],alliance_incoming_applications:[{id:'app1',name:'<Applicant>'}],alliance_incoming_applications_has_more:true}});
  let markup=box.allianceApplicationsMarkup('incoming');
  assert.ok(markup.includes('&lt;Applicant&gt;'));
  assert.ok(markup.includes('data-system-action="alliance_application_accept"'));
  assert.ok(markup.includes('data-alliance-applications-more="incoming"'));
  box.state.membership.role='member';
  box.state.alliance_permissions=[];
  assert.equal(box.allianceApplicationsMarkup('incoming'),'');
  box.state.membership=null;
  box.state.alliance_applications=[{id:'app2',name:'Alliance',tag:'A&B'}];
  box.state.alliance_applications_has_more=false;
  markup=box.allianceApplicationsMarkup('outgoing');
  assert.ok(markup.includes('A&amp;B'));
  assert.ok(markup.includes('data-system-action="alliance_application_withdraw"'));
  assert.match(source,/alliance\/applications\?/);
});

test('alliance invitation pages retain owner/manager controls and hide outgoing controls from members',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceInvitationsMarkup\(direction\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance invitation renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${id}">${label}</button>`;
  const box=context({escapeHtml,actionButton,state:{membership:null,invites:[{id:'incoming',name:'<Guild>',tag:'A&B'}],invites_has_more:true}});
  let markup=box.allianceInvitationsMarkup('incoming');
  assert.ok(markup.includes('&lt;Guild&gt;'));
  assert.ok(markup.includes('data-system-action="alliance_accept"'));
  assert.ok(markup.includes('data-system-action="alliance_invite_decline"'));
  assert.ok(markup.includes('data-alliance-invitations-more="incoming"'));
  box.state.membership={alliance_id:'a1',role:'officer'};
  box.state.alliance_permissions=['invitations'];
  box.state.alliance_outgoing_invites=[{id:'outgoing',name:'Target'}];
  box.state.alliance_outgoing_invites_has_more=true;
  markup=box.allianceInvitationsMarkup('outgoing');
  assert.ok(markup.includes('data-system-action="alliance_invite_cancel"'));
  box.state.membership.role='member';
  box.state.alliance_permissions=[];
  assert.equal(box.allianceInvitationsMarkup('outgoing'),'');
  assert.match(source,/alliance\/invitations\?/);
});

test('API refreshes stale CSRF state once and retries the same command token',async()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/async function api\(path, body, method\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'API helper must be available for CSRF retry regression');
  const calls=[];
  const replies=[
    {ok:false,status:400,json:async()=>({error:'Ungültiger Sitzungsschutz. Bitte Seite neu laden.'})},
    {ok:true,status:200,json:async()=>({csrf:'fresh-token'})},
    {ok:true,status:200,json:async()=>({ok:true})},
  ];
  const box=vm.createContext({csrf:'stale-token',fetch:async(url,options={})=>{calls.push({url,options:{...options,headers:{...options.headers}}});return replies.shift();}});
  vm.runInContext(helper,box);
  const result=await box.api('command',{action:'build',token:'stable-idempotency-token'});
  assert.equal(result.ok,true);
  assert.equal(calls.length,3);
  assert.equal(calls[0].options.headers['X-CSRF-Token'],'stale-token');
  assert.equal(calls[1].url,'/api/v1/state');
  assert.equal(calls[2].options.headers['X-CSRF-Token'],'fresh-token');
  assert.equal(calls[0].options.body,calls[2].options.body);
});

test('mission template delete uses the current CSRF token and template options escape account data',async()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const apiHelper=source.match(/async function api\(path, body, method\) \{[\s\S]*?\n\}/)?.[0];
  const optionsHelper=source.match(/function missionTemplateOptions\(templates\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(apiHelper,'API helper should support safe template deletion');
  assert.ok(optionsHelper,'template option renderer should be isolated');
  const calls=[];
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({csrf:'session-csrf',fetch:async(url,options)=>{calls.push({url,options});return {ok:true,status:200,json:async()=>({ok:true})};},escapeHtml});
  vm.runInContext(apiHelper,box);
  vm.runInContext(optionsHelper,box);
  await box.api('mission-templates/template-id',undefined,'DELETE');
  assert.equal(calls[0].options.method,'DELETE');
  assert.equal(calls[0].options.headers['X-CSRF-Token'],'session-csrf');
  const markup=box.missionTemplateOptions([{id:'id"><img',name:'<script>x</script>',mode:'attack'}]);
  assert.ok(markup.includes('value="id&quot;&gt;&lt;img"'));
  assert.ok(markup.includes('&lt;script&gt;x&lt;/script&gt;'));
  assert.ok(!markup.includes('<script>'));
});

test('mission template loading clamps to available units and rejects an incompatible mode',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const handler=source.match(/\$\('load-mission-template'\)\.onclick=\(\)=>\{[\s\S]*?\n\};/)?.[0];
  assert.ok(handler,'mission template load handler should be present');
  const elements={
    'load-mission-template':{},
    'mission-template-select':{value:'formation-1'},
    'mission-template-status':{textContent:''},
    'mission-mode':{value:'attack',options:[{value:'attack'}],dispatchEvent(){this.changed=true;}},
    'mission-form':{elements:{ranger:{value:'0',max:'2'},sentinel:{value:'0',max:'4'},mech:{value:'0',max:'0'}}},
    'capture':{checked:false},
    'army-select':{dispatchEvent(event){this.lastEvent=event;}}
  };
  const box=vm.createContext({
    $:selector=>elements[selector],
    missionTemplates:[{id:'formation-1',name:'Grenzschutz',mode:'attack',army:{ranger:5,sentinel:1,mech:3},capture:true}],
    state:{id:'owner-1',units:{ranger:2,sentinel:4,mech:0}},
    target:{isPlayer:false,owner:null},
    Event:class Event{constructor(type,options={}){this.type=type;this.bubbles=options.bubbles;}}
  });
  vm.runInContext(handler,box);
  elements['load-mission-template'].onclick();
  assert.equal(elements['mission-form'].elements.ranger.value,2);
  assert.equal(elements['mission-form'].elements.sentinel.value,1);
  assert.equal(elements['mission-form'].elements.mech.value,0);
  assert.equal(elements.capture.checked,true);
  assert.match(elements['mission-template-status'].textContent,/Verfügbare Truppen wurden berücksichtigt/);
  elements['mission-mode'].options=[];
  elements['mission-template-status'].textContent='';
  elements['load-mission-template'].onclick();
  assert.equal(elements['mission-template-status'].textContent,'Diese Vorlage passt nicht zu diesem Ziel.');
});

test('production presets escape labels and are bound to the normal idempotent queue endpoint',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function productionTemplateOptions\(templates, kind\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'production template option renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  const markup=box.productionTemplateOptions([
    {id:'id"><img',name:'<Safe & Ready>',kind:'train',key:'ranger',count:4},
    {id:'other',name:'Research',kind:'research',key:'tactics',count:1},
  ],'train');
  assert.ok(markup.includes('value="id&quot;&gt;&lt;img"'));
  assert.ok(markup.includes('&lt;Safe &amp; Ready&gt; · ranger × 4'));
  assert.ok(!markup.includes('Research'));
  assert.match(source,/production-templates\/\$\{encodeURIComponent\(templateId\)\}\/queue/);
  assert.match(source,/token:crypto\.randomUUID\(\)/);
  assert.match(source,/data-production-kind/);
});

test('production blueprint panel is available for construction, research, and recruitment',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function productionTemplatePanel\(kind\) \{[\s\S]*?\n\}/)?.[0];
  const options=source.match(/function productionTemplateOptions\(templates, kind\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'production blueprint panel builder must exist');
  assert.ok(options,'production template options renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({
    escapeHtml,
    state:{catalog:{buildings:{wood:{name:'Wood'}},tech:{tactics:{name:'Tactics'},engineering:{name:'Engineering'}},units:{ranger:{name:'Ranger'},sentinel:{name:'Sentinel'}}}},
    productionTemplates:[
      {id:'build-1',name:'<Base>',kind:'build',key:'wood',count:1},
      {id:'research-1',name:'Research',kind:'research',key:'tactics',count:1},
      {id:'train-1',name:'<Guard>',kind:'train',key:'sentinel',count:3},
    ],
    canTrainUnit:key=>key==='ranger',
  });
  vm.runInContext(options,box);
  vm.runInContext(helper,box);
  for(const [kind,label,id] of [['build','Bau','build-1'],['research','Forschung','research-1'],['train','Rekrutierung','train-1']]){
    const markup=box.productionTemplatePanel(kind);
    assert.ok(markup.includes(`${label}vorlagen`));
    assert.ok(markup.includes(`value="${id}"`));
    assert.ok(markup.includes('name="count"')=== (kind==='train'));
  }
  assert.ok(box.productionTemplatePanel('train').includes('&lt;Guard&gt;'));
  assert.ok(!box.productionTemplatePanel('train').includes('Sentinel'));
});

test('social lists escape player names and expose owner-scoped request, block, and unblock actions',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function socialMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  const profileHelper=source.match(/function playerProfileSettingsMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  const pagination=source.match(/function playerDirectoryMoreMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  const socialPagination=source.match(/function socialMoreMarkup\(listName\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'social list renderer must exist');
  assert.ok(profileHelper,'profile privacy settings renderer must exist');
  assert.ok(pagination,'player directory pagination renderer must exist');
  assert.ok(socialPagination,'social list pagination renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${id}">${label}</button>`;
  const box=vm.createContext({escapeHtml,number:String,actionButton,sharedReportsMarkup:()=>'',state:{id:'owner',profile:{public_profile_visibility:'private',public_profile_title:'none',public_profile_badges:[]},profile_rules:{titles:{none:'Kein Titel',architect:'Architekt'},badges:{builder:'Baumeister'},max_badges:3},players:[{id:'candidate',name:'<Potential & Pilot>',x:4,y:8}],social:{friends:[{id:'friend',name:'<Friend>'}],friends_has_more:true,incoming_requests:[{id:'incoming',name:'Sender'}],incoming_requests_has_more:true,outgoing_requests:[],outgoing_requests_has_more:false,blocked:[{id:'blocked',name:'Blocked'}],blocked_has_more:true}}});
  vm.runInContext(pagination,box);
  vm.runInContext(socialPagination,box);
  vm.runInContext(profileHelper,box);
  vm.runInContext(helper,box);
  const markup=box.socialMarkup();
  assert.ok(markup.includes('&lt;Friend&gt;'));
  assert.ok(markup.includes('&lt;Potential &amp; Pilot&gt;'));
  assert.ok(markup.includes('data-system-action="friend_accept"'));
  assert.ok(markup.includes('data-system-action="friend_request"'));
  assert.ok(markup.includes('data-system-action="player_block"'));
  assert.ok(markup.includes('data-system-action="player_unblock"'));
  assert.ok(markup.includes('data-social-more="friends"'));
  assert.ok(markup.includes('data-social-more="incoming_requests"'));
  assert.ok(markup.includes('data-social-more="blocked"'));
  assert.ok(markup.includes('Öffentliches Kommandantenprofil'));
  assert.ok(markup.includes('value="private" selected'));
  assert.match(source,/command\('profile_settings_update'/);
  assert.ok(markup.includes('höchstens'));
  assert.ok(!markup.includes('<Potential'));
});

test('public player cards escape labels and use the authenticated profile endpoint',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const list=source.match(/function rankingListMarkup\(entries, offset, hasMore\) \{[\s\S]*?\n\}/)?.[0];
  const card=source.match(/function publicPlayerProfileMarkup\(profile\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(list,'ranking list must include public profile entry points');
  assert.ok(card,'public profile card renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(list,box);vm.runInContext(card,box);
  const ranking=box.rankingListMarkup([{id:'player-1',name:'<Commander>',score:42}],0,false);
  assert.ok(ranking.includes('data-player-profile="player-1"'));
  assert.ok(ranking.includes('&lt;Commander&gt;'));
  const profile=box.publicPlayerProfileMarkup({name:'<Pilot>',title:'<Title>',badges:['<Badge>'],world:'Genesis',rank:1,score:42,rules_version:'FUR-3-PROFILE-1'});
  assert.ok(profile.includes('&lt;Pilot&gt;'));
  assert.ok(profile.includes('&lt;Badge&gt;'));
  assert.ok(!profile.includes('<Pilot>'));
  assert.match(source,/api\(`profiles\/\$\{encodeURIComponent\(profileId\)\}`\)/);
  assert.match(source,/data-player-profile-close/);
});

test('alliance bulletin renderer escapes member content and limits management controls to officers',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceBulletinMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance bulletin renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key:id}))}">${label}</button>`;
  const commandForm=(action,body,label,extra='')=>`<form data-system="${action}" ${extra}>${body}<button>${label}</button></form>`;
  const input=(name,label,type='text',value='',extra='')=>`<label>${escapeHtml(label)}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${extra}></label>`;
  const hostile='<img src=x onerror=alert(1)>';
  const box=vm.createContext({escapeHtml,actionButton,commandForm,input,state:{membership:{alliance_id:'a',role:'leader'},alliance_permissions:['bulletin'],alliance_bulletins_has_more:true,alliance_bulletins:[{id:'id"><x',title:hostile,body:hostile,author_name:hostile,created:1,updated:1,archived:0}]}});
  vm.runInContext(helper,box);
  const markup=box.allianceBulletinMarkup();
  assert.ok(markup.includes('&lt;img src=x onerror=alert(1)&gt;'));
  assert.ok(!markup.includes('<img'));
  assert.ok(markup.includes('alliance_bulletin_create'));
  assert.ok(markup.includes('alliance_bulletin_update'));
  assert.ok(markup.includes('alliance_bulletin_archive'));
  assert.ok(markup.includes('Ältere Beiträge laden'));
  assert.ok(markup.includes('data-bulletin-more="id&quot;&gt;&lt;x"'));
  box.state.membership={alliance_id:'a',role:'member'};
  box.state.alliance_permissions=[];
  const memberMarkup=box.allianceBulletinMarkup();
  assert.ok(memberMarkup.includes('&lt;img'));
  assert.ok(!memberMarkup.includes('alliance_bulletin_create'));
  assert.ok(!memberMarkup.includes('alliance_bulletin_update'));
  assert.ok(!memberMarkup.includes('alliance_bulletin_archive'));
  assert.ok(memberMarkup.includes('Ältere Beiträge laden'));
  box.state.membership=null;
  assert.equal(box.allianceBulletinMarkup(),'');
  const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(app,/alliance\/bulletins\?before=\$\{cursor\}/);
  assert.match(app,/state\.alliance_bulletins\.push\(\.\.\.page\.entries\)/);
});

test('alliance forum escapes posts and enforces the rendered member/moderator controls',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function allianceForumMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance forum renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key:id}))}">${label}</button>`;
  const commandForm=(action,body,label,extra='')=>`<form data-system="${action}" ${extra}>${body}<button>${label}</button></form>`;
  const input=(name,label,type='text',value='',extra='')=>`<label>${escapeHtml(label)}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${extra}></label>`;
  const hostile='<svg onload=alert(1)>';
  const box=vm.createContext({escapeHtml,actionButton,commandForm,input,state:{id:'leader',membership:{alliance_id:'a',role:'leader'},alliance_permissions:['forum_moderation'],alliance_forum_has_more:true,alliance_forum_reports_has_more:true,alliance_forum:[{id:'thread-1',author_id:'member',author_name:hostile,title:hostile,created:1,updated:1,archived:0,posts:[{id:'post-1',thread_id:'thread-1',author_id:'member',author_name:hostile,body:hostile,created:1,updated:1}]}],alliance_forum_reports:[{id:'report-1',post_id:'post-1',reporter_id:'member',reporter_name:hostile,reason:hostile,status:'pending',thread_title:hostile,post_body:hostile,post_author_name:hostile}]}});
  vm.runInContext(helper,box);
  const markup=box.allianceForumMarkup();
  assert.ok(markup.includes('&lt;svg onload=alert(1)&gt;'));
  assert.ok(!markup.includes('<svg'));
  for(const action of ['alliance_forum_thread_create','alliance_forum_thread_edit','alliance_forum_post_edit','alliance_forum_reply','alliance_forum_report','alliance_forum_archive','alliance_forum_report_resolve']) assert.ok(markup.includes(action));
  assert.ok(markup.includes('Ältere Themen laden'));
  assert.ok(markup.includes('Weitere Meldungen laden'));
  box.state.membership={alliance_id:'a',role:'member'};
  box.state.alliance_permissions=[];
  const memberMarkup=box.allianceForumMarkup();
  assert.ok(memberMarkup.includes('alliance_forum_thread_create'));
  assert.ok(memberMarkup.includes('alliance_forum_reply'));
  assert.ok(!memberMarkup.includes('alliance_forum_archive'));
  assert.ok(!memberMarkup.includes('alliance_forum_report_resolve'));
  box.state.membership=null;
  assert.equal(box.allianceForumMarkup(),'');
  const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(app,/alliance\/forum\?before=\$\{cursor\}/);
  assert.match(app,/state\.alliance_forum\.push\(\.\.\.page\.threads\)/);
  assert.match(source,/alliance\/forum-reports\?before=\$\{encodeURIComponent\(cursor\)\}/);
  assert.match(source,/state\.alliance_forum_reports\.push\(\.\.\.page\.reports/);
});

test('public diplomacy chronicle escapes alliance tags and renders state changes semantically',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({escapeHtml,number:String,tab:'alliance',state:{
    membership:null,alliances:[],diplomacy:[],invites:[],alliance_candidates:[],
    diplomacy_events_has_more:true,
    diplomacy_events:[{id:'event-1',event_type:'war_declared',created:100000,actor_alliance_tag:'<img src=x onerror=1>',alliance_a_tag:'<A>',alliance_b_tag:'B'}],
  }});
  const markup=vm.runInContext('systemsView()',box);
  assert.ok(markup.includes('Öffentliches Diplomatieprotokoll'));
  assert.ok(markup.includes('Krieg erklärt'));
  assert.ok(markup.includes('&lt;img src=x onerror=1&gt;'));
  assert.ok(markup.includes('[&lt;A&gt;] ↔ [B]'));
  assert.ok(!markup.includes('<img src=x'));
  assert.ok(markup.includes('<ol role="list">'));
  assert.ok(markup.includes('data-diplomacy-events-more'));
  assert.ok(markup.includes('aria-live="polite"'));
  assert.match(fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8'),/diplomacy\/events\?before=/);
});

test('live events expose accessible older-page control without deriving bonuses from the visible page',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function liveEventsMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'live event renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({escapeHtml,number:String,state:{events:[{id:'e1',name:'<Event>',active_bonus:40,world_active_bonus:100,phase:'end',goal_progress:90,goal_score:100,goal_reached:false,rules_version:'FUR-2-LIVE-2',rules_digest:'abcdef0123456789',ends:1000}],events_has_more:true}});
  vm.runInContext(helper,box);
  const markup=box.liveEventsMarkup();
  assert.ok(markup.includes('&lt;Event&gt;'));
  assert.ok(markup.includes('Endphase'));
  assert.ok(markup.includes('Gesamtbonus: 100%'));
  assert.ok(markup.includes('Obergrenze 100%'));
  assert.ok(markup.includes('90 / 100 Punkte'));
  assert.ok(markup.includes('FUR-2-LIVE-2'));
  assert.ok(markup.includes('data-live-events-more'));
  assert.ok(markup.includes('aria-live="polite"'));
  assert.match(source,/events\?before=/);
  const formHelper=source.match(/function adminLiveEventFormMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(formHelper,'versioned event editor form must be available');
  const input=(name,label,type,value,attrs)=>`<label>${label}<input name="${name}" type="${type}" value="${value}" ${attrs}></label>`;
  const commandForm=(action,fields,label)=>`<form data-system="${action}">${fields}<button>${label}</button></form>`;
  const formBox=context({escapeHtml,input,commandForm});
  vm.runInContext(formHelper,formBox);
  const editor=formBox.adminLiveEventFormMarkup();
  for (const field of ['hours','warning_hours','bonus','goal_score','end_hours','end_bonus']) assert.ok(editor.includes(`name="${field}"`));
  assert.ok(editor.includes('FUR-2-Regelsatz'));
  assert.ok(editor.includes('100 Prozentpunkte'));
});

test('private map and report notes escape text and use bounded owner actions',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function notesMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'private notes renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const input=(name,label,type='text',value='',extra='')=>`<label>${escapeHtml(label)}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${extra}></label>`;
  const select=(name,label,options)=>`<label>${escapeHtml(label)}<select name="${name}">${options.map(([value,text])=>`<option value="${escapeHtml(value)}">${escapeHtml(text)}</option>`).join('')}</select></label>`;
  const commandForm=(action,body,label,extra='')=>`<form data-system="${action}" ${extra}>${body}<button>${label}</button></form>`;
  const actionButton=(action,key,label)=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key}))}">${label}</button>`;
  const box=vm.createContext({escapeHtml,input,select,commandForm,actionButton,state:{active_world:{name:'<Genesis>'},reports:[{id:'report-1',title:'<Sichtungsbericht>'}],notes_has_more:true,notes:[{id:'note-1',target_kind:'sector',x:2,y:5,body:'<script>alert(1)</script>'},{id:'note-2',target_kind:'report',report_id:'report-1',report_title:'<Sichtungsbericht>',body:'Route & Versorgung'}]}});
  vm.runInContext(helper,box);
  const markup=box.notesMarkup();
  assert.ok(markup.includes('&lt;Genesis&gt;'));
  assert.ok(markup.includes('&lt;Sichtungsbericht&gt;'));
  assert.ok(markup.includes('&lt;script&gt;alert(1)&lt;/script&gt;'));
  assert.ok(markup.includes('maxlength="500"'));
  assert.ok(markup.includes('data-system="note_save"'));
  assert.ok(markup.includes('data-system-action="note_delete"'));
  assert.ok(markup.includes('data-notes-more'));
  assert.ok(!markup.includes('<script>'));
});

test('alliance report sharing renders only redacted summaries and owner revoke actions',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function sharedReportsMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance report sharing renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,key,label,fields={})=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key,...fields}))}">${label}</button>`;
  const number=String;
  const box=vm.createContext({escapeHtml,actionButton,number,state:{
    membership:{alliance_id:'alliance-1'},
    reports:[{id:'private-report-id',title:'<Own target 9:9>',share_owner:{allowed:true},combat:{rounds:[]}},{id:'unshared-report-id',title:'No share yet',share_owner:{allowed:true},combat:{rounds:[]}},{id:'blocked-report-id',title:'Blocked report',share_owner:{allowed:false},combat:{rounds:[]}}],
    shared_combat_report_keys:{'private-report-id':'share-owner-id'},
    alliance_shared_reports:[
      {id:'share-owner-id',owner_name:'<Owner>',summary:{outcome:'victory',rounds:[{number:1,outcome:'victory',own_losses:2,own_survivors:4}]},can_revoke:true,report_id:'private-report-id'},
      {id:'share-other-id',owner_name:'Ally',summary:{outcome:'defeat',rounds:[{number:2,outcome:'defeat',own_losses:5,own_survivors:1}]},can_revoke:false}
    ],
    alliance_shared_reports_has_more:false
  }});
  vm.runInContext(helper,box);
  const markup=box.sharedReportsMarkup();
  assert.ok(markup.includes('report_unshare'));
  assert.ok(markup.includes('report_share'));
  assert.ok(!markup.includes('blocked-report-id'));
  assert.ok(markup.includes('&lt;Owner&gt;'));
  assert.ok(markup.includes('eigene Verluste'));
  assert.ok(markup.includes('Koordinaten'));
  assert.ok(!markup.includes('<Owner>'));
  assert.ok(!markup.includes('Hidden Target'));
});

test('invasion history shows the public budget and hides scheduling from players',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function npcInvasionMarkup\(current\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper);
  const escapeHtml=value=>String(value).replaceAll('<','&lt;').replaceAll('>','&gt;');
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  const event={name:'<Welle>',status:'warning',starts:2400,ends:7200,budget:6,planned:2,resolved:1,cancelled:0};
  const view={npc_invasions:{enabled:true,items:[event]}};
  const history=box.npcInvasionMarkup(view);
  assert.match(history,/&lt;Welle&gt;<\/b> · Warnphase/);
  assert.match(history,/2\/6 Angriffe angesetzt · 1 abgeschlossen/);
  assert.doesNotMatch(history,/data-invasion-schedule/);
  assert.match(box.npcInvasionMarkup({profile:{role:'admin'},npc_invasions:{enabled:true,items:[]}}),/data-invasion-schedule/);
  assert.doesNotMatch(box.npcInvasionMarkup({...view,profile:{role:'admin'}}),/data-invasion-schedule/);
  assert.match(source,/command\('admin_npc_invasion_schedule'/);
});

test('cooperative boss panel shows health, signup and private rewards without raw names',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function terraBossMarkup\(current\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper);
  const escapeHtml=value=>String(value).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;');
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  const base={units:{ranger:15},server_time:300,terra_boss:{raid:null,rewards:[],max_rangers:40,attack_slots:12,reward_ore_pool:6000}};
  assert.equal(box.terraBossMarkup(base),'');
  assert.match(box.terraBossMarkup({...base,profile:{role:'admin'}}),/data-boss-schedule/);
  const raid={id:'boss',name:'<Wächter>',health:1000,remaining_health:450,phase:2,can_join:true,booked:2,starts:1,ends:800};
  const attack=box.terraBossMarkup({...base,terra_boss:{...base.terra_boss,raid}});
  assert.match(attack,/&lt;Wächter&gt;/);
  assert.match(attack,/Phase 2/);
  assert.match(attack,/<meter min="0" max="1000" value="450">/);
  assert.match(attack,/data-boss-attack="boss"/);
  assert.match(attack,/max="15"/);
  const rewards=[{id:'boss',name:'<Wächter>',ore:600}];
  const claim=box.terraBossMarkup({...base,terra_boss:{...base.terra_boss,rewards}});
  assert.match(claim,/600 Erz/);
  assert.match(claim,/data-action="terra_boss_claim"/);
  assert.doesNotMatch(claim,/data-boss-schedule/);
  assert.match(source,/command\('terra_boss_attack'/);
});

test('ruin exploration offers known targets and private observations independently',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function ruinExplorationMarkup\(current\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper);
  const escapeHtml=value=>String(value).replaceAll('"','&quot;').replaceAll('<','&lt;');
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  assert.equal(box.ruinExplorationMarkup({}), '');
  const current={
    active_world:{terra_ruin_exploration_ruleset:'FUR-3-TERRA-RUIN-EXPLORATION-1'},
    terra_ruin_targets:[{id:'"<ruin>',x:11,y:12,expires:5000,travel_seconds:8}],
    terra_ruin_intel:{old:{x:4,y:9,expires_at:6000,outcome:'salvage'}},
  };
  const markup=box.ruinExplorationMarkup(current);
  assert.match(markup,/aria-labelledby="ruin-exploration-title"/);
  assert.match(markup,/data-ruin="&quot;&lt;ruin>"[^>]*><span>Kolonieruine 11:12 · 8 s Hinweg/);
  assert.match(markup,/Private Ruinenbeobachtungen[\s\S]*4:9 · Fracht geborgen/);
  assert.doesNotMatch(box.ruinExplorationMarkup({...current,active_world:{}}), /data-ruin=/);
  assert.match(source,/mode==='ruin_exploration'\?\{ranger:Number\(fields.ranger.value\)\}/);
});

test('expedition mode is offered for neutral sectors and submits its own action',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
  assert.match(source,/option value="expedition">Expedition/);
  assert.match(source,/mode==='expedition'\?'expedition'/);
  assert.match(source,/expedition:'Expedition'/);
  assert.match(source,/mission-mode-note/);
  assert.match(source,/state\.expedition_item_drops/);
  assert.match(source,/expeditionCatalogSummary\(state\.expedition_rules\)/);
  const helper=source.match(/function expeditionCatalogSummary\(catalog\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper);
  const box=vm.createContext({number:String});
  vm.runInContext(helper,box);
  assert.equal(box.expeditionCatalogSummary({
    version:'test-rule',outcome_rolls:200,
    outcomes:[{id:'skirmish',weight:75,resource_min:6,resource_max:9,loss_min_percent:3,loss_max_percent:4}],
  }), 'test-rule · Patrouille 37.5 %, 6–9 einer Rohstoffart vor Traglastprüfung, 3–4 % Verlustrate.');
  assert.match(source,/overall_chance_basis_points/);
  assert.match(source,/Gegenstandsfunde sind aus/);
  assert.match(source,/Rohstoffbeute hat Vorrang vor Gegenständen bei der Trägerkapazität/);
  assert.match(html,/id="mission-mode-label"[^>]*for="mission-mode"/);
  assert.match(html,/id="cargo-fields"[^>]*>/);
  for(const id of ['cargo-0','cargo-1','cargo-2']) assert.match(html,new RegExp(`id="${id}"`));
});

test('world manual explains neutral outpost stock regeneration and its cap',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.ok(source.includes('1 Einheit pro Ressource und Minute'));
  assert.ok(source.includes('400 × Stufe'));
  assert.ok(source.includes('eroberte Außenposten erneuern ihre Vorräte nicht'));
});

test('map stock summary shows neutral resources without exposing owned stock',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function outpostStockSummary\(outpost\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'outpost stock summary formatter must exist');
  const box=vm.createContext({number:value=>String(value),resourceIcon:index=>['[Holz]','[Stein]','[Erz]'][index]});
  vm.runInContext(helper,box);
  assert.equal(box.outpostStockSummary({owner:null,stock:[100,200,300]}),'Vorräte [Holz] 100 · [Stein] 200 · [Erz] 300');
  assert.equal(box.outpostStockSummary({owner:'player',stock:[100,200,300]}),'');
  assert.equal(box.outpostStockSummary({owner:null,stock:[100]}),'');
});

test('NPC frontier panel escapes faction names and explains predictable threat pressure',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function npcFactionMarkup\(factions\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'NPC frontier panel renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:value=>String(value)});
  vm.runInContext(helper,box);
  const markup=box.npcFactionMarkup([{id:'ash',name:'<Ash & Iron>',outposts:4,threat_level:3,pressure:312}]);
  assert.ok(markup.includes('&lt;Ash &amp; Iron&gt;'));
  assert.ok(markup.includes('Bedrohungsstufe 3'));
  assert.ok(markup.includes('Fünf-Minuten-Takt'));
  assert.ok(markup.includes('automatische Angriffe auf Spielerbasen finden nicht statt'));
  assert.ok(box.npcFactionMarkup([]).includes('keine neutralen Fraktionsposten'));
});

test('NPC attack plan panel is private-plan language and escapes player-controlled target names',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function npcAttackPlanMarkup\(plans, ruleset\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'NPC attack plan panel renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:value=>String(value),Date});
  vm.runInContext(helper,box);
  const markup=box.npcAttackPlanMarkup([{target_name:'<Home & Hope>',target_x:4,target_y:5,created:1800000000}],'FUR-3-NPC-CAMPS-2');
  assert.ok(markup.includes('&lt;Home &amp; Hope&gt;'));
  assert.ok(markup.includes('kein Angriff wurde gestartet'));
  assert.ok(markup.includes('höchstens ein Ziel je Welt und Fünf-Minuten-Takt'));
  const incoming=box.npcAttackPlanMarkup([{target_name:'Home',target_x:4,target_y:5,created:1800000000,attack_arrival:1800000300,attack_status:'warning'}],'FUR-3-NPC-CAMPS-3');
  assert.ok(incoming.includes('NPC-Angriffsberichte'));
  assert.ok(incoming.includes('Angriff angekündigt'));
  assert.ok(incoming.includes('höchstens einen Angriff innerhalb von 24 Stunden'));
  const resolved=box.npcAttackPlanMarkup([{target_name:'Home',target_x:4,target_y:5,created:1800000000,attack_arrival:1800000300,attack_status:'resolved',attack_outcome:'defender_win'}],'FUR-3-NPC-CAMPS-3');
  assert.ok(resolved.includes('Kampf beendet: defender_win'));
  assert.equal(box.npcAttackPlanMarkup([], 'FUR-3-NPC-CAMPS-2'),'');
  assert.equal(box.npcAttackPlanMarkup([{target_name:'Private'}], 'FUR-2'),'');
});

test('FUR-3 NPC camp panel is opt-in, escapes profiles, and exposes only allowed actions',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function npcCampMarkup\(camps, ruleset\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'NPC camp renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:value=>String(value)});
  vm.runInContext(helper,box);
  const camp={name:'<Ash & Iron>',doctrine:'logistics',actions:['resupply','scout'],resources:[1,2,3],units:{ranger:4},movement_quota:4,deployment_quota:8,x:5,y:7,scouted_outposts:3};
  assert.equal(box.npcCampMarkup([camp],'FUR-2'),'');
  const markup=box.npcCampMarkup([camp],'FUR-3-NPC-CAMPS-1');
  assert.ok(markup.includes('&lt;Ash &amp; Iron&gt;'));
  assert.ok(markup.includes('Versorgung, Aufklärung'));
  assert.ok(markup.includes('Entwurfsbalance'));
  assert.ok(markup.includes('höchstens eine bezahlbare Profilaktion automatisch'));
  assert.ok(!markup.includes('autonomous_attack'));
  const movement=box.npcCampMarkup([camp],'FUR-3-NPC-CAMPS-2');
  assert.ok(movement.includes('Standort 5:7'));
  assert.ok(movement.includes('bekannte Außenposten 3'));
  assert.ok(movement.includes('kürzesten begehbaren Vier-Wege-Pfad'));
  assert.ok(movement.includes('Sechs-Sektoren-Abstands'));
  assert.ok(movement.includes('Veränderungen an Spielerbesitz'));
  const attack=box.npcCampMarkup([camp],'FUR-3-NPC-CAMPS-3');
  assert.ok(attack.includes('warnen fünf Minuten vorher'));
  assert.ok(attack.includes('Außenposten werden nicht erobert'));
});

test('owned non-citadel outposts expose a disabled-aware conversion action with escaped confirmation data',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function outpostConversionMarkup\(outpost, state\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'outpost conversion renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml});
  vm.runInContext(helper,box);
  const state={id:'pilot',buildings:{hq:3},colony_count:1,colony_slot_limit:2,resources:[6000,4500,3000],colonies:[{x:0,y:0}]};
  const markup=box.outpostConversionMarkup({id:'post',name:'<Foundry>',owner:'pilot',tier:2,x:8,y:0},state);
  assert.ok(markup.includes('data-convert="post"'));
  assert.ok(markup.includes('data-convert-name="&lt;Foundry&gt;"'));
  assert.ok(!markup.includes(' disabled'));
  assert.equal(box.outpostConversionMarkup({owner:'enemy',tier:2},state),'');
  assert.equal(box.outpostConversionMarkup({owner:'pilot',tier:8},state),'');
});

test('regional map summary escapes owners and shows surveyed alliance boundaries',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function regionControlMarkup\(regions, playerId, productionBonus\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'region control summary formatter must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml});
  vm.runInContext(helper,box);
  const markup=box.regionControlMarkup([
    {id:'A1',x_min:0,x_max:15,y_min:0,y_max:15,outpost_count:3,leader_id:'pilot',leader_name:'Pilot',leader_outposts:2,required_posts:2,owner_id:'pilot',owner_name:'Pilot',alliance_owner_id:'alliance-a',alliance_owner_name:'<FOX>',alliance_leader_tied:false,production_bonus_percent:2,leader_tied:false},
    {id:'B1',x_min:16,x_max:31,y_min:0,y_max:15,outpost_count:3,leader_id:'opponent',leader_name:'Opponent',leader_outposts:2,required_posts:2,owner_id:'opponent',owner_name:'<Pilot>',production_bonus_percent:2,leader_tied:false},
    {id:'D4',x_min:48,x_max:63,y_min:48,y_max:63,outpost_count:0,leader_id:null,leader_name:null,leader_outposts:0,required_posts:2,owner_id:null,owner_name:null,production_bonus_percent:0,leader_tied:false},
  ],'pilot',2);
  assert.ok(markup.includes('Deine Kontrolle'));
  assert.ok(markup.includes('&lt;Pilot&gt;'));
  assert.ok(markup.includes('Keine Außenposten in diesem Gebiet'));
  assert.ok(markup.includes('Allianzgebiet: &lt;FOX&gt;'));
  assert.ok(markup.includes('DEIN REGIONSBONUS · +2%'));
  assert.ok(markup.includes('mehr als die Hälfte'));
});

test('unexplored regions do not disclose global outpost or control counts',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(source,/region\.surveyed===false/);
  assert.match(source,/Gebiet noch nicht vollständig erkundet/);
});

test('admin world settings markup carries the world id and checked join policy',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function worldSettingsMarkup\(world\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'world settings form builder must be available for rendering tests');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  const markup=box.worldSettingsMarkup({id:2,name:'<World & Beyond>',joinable:false,terra_combat_ruleset:'FUR-3-TERRA-COMBAT-1',terra_retreat_threshold_percent:37,crafting_ruleset:'FUR-2'});
  assert.ok(markup.includes('id="world-settings-form-2" data-world-settings="2"'));
  assert.ok(markup.includes('&lt;World &amp; Beyond&gt;'));
  assert.ok(markup.includes('name="joinable" type="checkbox" >'));
  assert.ok(markup.includes('name="terra_combat_ruleset"'));
  assert.ok(markup.includes('value="FUR-3-TERRA-COMBAT-1" selected'));
  assert.ok(markup.includes('value="FUR-3-TERRA-COMBAT-2"'));
  assert.ok(markup.includes('Außenpostenbefestigung (Entwurf)'));
  assert.ok(markup.includes('value="FUR-3-TERRA-COMBAT-3"'));
  assert.ok(markup.includes('Rollen + Truppenbewegung (Entwurf)'));
  assert.ok(markup.includes('value="FUR-3-TERRA-COMBAT-5"'));
  assert.ok(markup.includes('Festungsregeneration (Entwurf)'));
  assert.ok(markup.includes('name="terra_retreat_threshold_percent" type="number" min="1" max="100" step="1" required value="37"'));
  assert.ok(markup.includes('name="crafting_ruleset"'));
  assert.ok(markup.includes('name="hero_respec_ruleset"'));
  assert.ok(markup.includes('name="active_at_local" type="datetime-local" required'));
  assert.ok(markup.includes('name="rule_key"'));
  assert.ok(markup.includes('data-rule-rollout="2"'));
  assert.ok(markup.includes('Die angegebenen FUR-3-Balancewerte bleiben Entwürfe.'));
  assert.ok(markup.includes('Regelupdate einplanen'));
  assert.ok(markup.includes('value="FUR-2" selected') && markup.includes('FUR-2 · aus'));
  assert.ok(markup.includes('value="FUR-CRAFTING-1"'));
  assert.ok(!markup.includes('type="checkbox" checked'));
  assert.match(source,/terra_retreat_threshold_percent:Number\(form\.elements\.terra_retreat_threshold_percent\.value\)/);
  assert.match(source,/crafting_ruleset:form\.elements\.crafting_ruleset\.value/);
  assert.match(source,/hero_respec_ruleset:form\.elements\.hero_respec_ruleset\.value/);
});

test('world directory explains world rules and offers the active-world ranking accessibly',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function worldRulesSummaryMarkup\(world\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'world rules summary must be available for rendering tests');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml});
  vm.runInContext(helper,box);
  const markup=box.worldRulesSummaryMarkup({terra_combat_ruleset:'<unsafe>',crafting_ruleset:'FUR-2',hero_ruleset:'FUR-2'});
  assert.ok(markup.includes('Grundregeln: FUR-2'));
  assert.ok(markup.includes('&lt;unsafe&gt;'));
  assert.ok(markup.includes('Commander-Doktrinen: FUR-2'));
  assert.ok(markup.includes('Rangliste folgt den Regeln der ausgewählten Welt'));
  assert.match(source,/<button type="button" data-goto="ranking">Rangliste dieser Welt öffnen/);
});

test('new world form exposes FUR-2 defaults and opt-in ruleset controls',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function worldCreationRulesMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'new world rules builder must be available');
  const box=vm.createContext({});
  vm.runInContext(helper,box);
  const markup=box.worldCreationRulesMarkup();
  assert.match(markup,/value="FUR-2">FUR-2 · Legacy/);
  for(const field of ['terra_combat_ruleset','terra_retreat_threshold_percent','crafting_ruleset','hero_ruleset','hero_doctrine_ruleset','hero_respec_ruleset']) assert.ok(markup.includes(`name="${field}"`));
  assert.ok(markup.includes('bleiben aus, bis du sie hier ausdrücklich auswählst'));
  assert.match(source,/hero_doctrine_ruleset:form\.elements\.hero_doctrine_ruleset\.value/);
});

test('season creation is admin-only in season worlds and archives target completion accessibly',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function seasonSummaryMarkup\(current\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'season summary builder must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=String,box=vm.createContext({escapeHtml,number});
  vm.runInContext(helper,box);
  assert.equal(box.seasonSummaryMarkup({profile:{role:'admin'},active_world:{mode:'permanent'}}),'');
  assert.equal(box.seasonSummaryMarkup({profile:{role:'player'},active_world:{mode:'season'},seasons:[]}),'<p role="status">Für diese Saisonwelt wurde noch kein Wettbewerb gestartet.</p>');
  const form=box.seasonSummaryMarkup({profile:{role:'admin'},active_world:{mode:'season'},seasons:[]});
  assert.match(form,/name="days" type="number" min="1" max="365"/);
  assert.match(form,/name="goal_score" type="number" min="1" max="1000000000"/);
  const archive=box.seasonSummaryMarkup({profile:{role:'player'},active_world:{mode:'season'},seasons:[{name:'<Season>',archived:1,goal_score:80,ends:1,standings:'[{"name":"<Pilot>","score":90,"goal_reached":true,"awards":["season_champion"]}]',alliance_standings:[{alliance_name:'<Alliance>',alliance_tag:'<Tag>',score:12}],awards:[{name:'<Pilot>',award:'season_champion',score:90}]}]});
  assert.ok(archive.includes('&lt;Season&gt;')&&archive.includes('&lt;Pilot&gt;'));
  assert.ok(archive.includes('&lt;Alliance&gt;')&&archive.includes('&lt;Tag&gt;'));
  assert.ok(archive.includes('Ziel erreicht'));
  assert.ok(archive.includes('Saisonmeister'));
});

test('crafting UI escapes recipe and job text and keeps disabled recipes unavailable',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function craftingMarkup\(crafting\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'crafting panel builder must be available for rendering tests');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String,state:{jobs:[{kind:'craft',label:'<Kit>',due:1050,id:'job"><x'}],server_time:1000}});
  vm.runInContext(helper,box);
  const markup=box.craftingMarkup({version:'FUR-CRAFTING-1',active_jobs:1,max_active_jobs:5,recipes:[{id:'component_press',name:'<Press>',description:'safe & sound',resources:{ore:100},goods:{},items:{},output:{crafting_component:4},duration_seconds:300,min_hq:1,available:false}]});
  assert.ok(markup.includes('&lt;Press&gt;'));
  assert.ok(markup.includes('safe &amp; sound'));
  assert.ok(markup.includes('disabled>Fertigung starten'));
  assert.ok(markup.includes('&lt;Kit&gt;'));
  assert.ok(markup.includes('data-key="job&quot;&gt;&lt;x"'));
});

test('recycling UI escapes recipe text and disables unavailable rules',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function recyclingMarkup\(recycling\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'recycling panel builder must be available for rendering tests');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:String});
  vm.runInContext(helper,box);
  const markup=box.recyclingMarkup({version:'FUR-ITEM-RECYCLING-1',max_units_per_command:100,recipes:[{item_id:'repair_kit',name:'<Kit>',description:'Safe & limited',output_items:{crafting_component:2},output_goods:{textiles:3},available:false}]});
  assert.match(markup,/&lt;Kit&gt;/);
  assert.match(markup,/Safe &amp; limited/);
  assert.match(markup,/disabled>Gegenstände zerlegen/);
  assert.match(markup,/Rückgabe: 2 crafting_component · 3 textiles/);
  assert.match(source,/item_amount:Number\(form\.elements\.amount\.value\)/);
});

test('FUR-3 movement preview announces its server quote accessibly',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(source,/<p id="power-preview" role="status" aria-live="polite"><\/p>/);
  assert.match(source,/api\('simulate-movement'/);
  assert.match(source,/FUR-3-Marsch/);
  assert.match(source,/Treibstoff/);
});

test('colony rename form escapes its identity and existing name',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function colonyRenameMarkup\(colony\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'colony rename form builder must be available for rendering tests');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml});
  vm.runInContext(helper,box);
  const markup=box.colonyRenameMarkup({colony_id:'id"><x',name:'<North & South>'});
  assert.ok(markup.includes('data-colony-rename="id&quot;&gt;&lt;x"'));
  assert.ok(markup.includes('value="&lt;North &amp; South&gt;"'));
  assert.ok(markup.includes('maxlength="32"'));
  assert.ok(markup.includes('aria-describedby="rename-help-id&quot;&gt;&lt;x"'));
  assert.ok(markup.includes('weltweit eindeutig'));
});

test('colony abandonment requires explicit confirmation and protects the home colony',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function colonyAbandonMarkup\(colony\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'colony abandonment control builder must be available for rendering tests');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml});
  vm.runInContext(helper,box);
  const secondary=box.colonyAbandonMarkup({colony_id:'id"><x',name:'<North & South>',is_home:false});
  assert.ok(secondary.includes('data-colony-abandon="id&quot;&gt;&lt;x"'));
  assert.ok(secondary.includes('data-colony-name="&lt;North &amp; South&gt;"'));
  assert.ok(secondary.includes('Rücknahme offener Handelsangebote'));
  const home=box.colonyAbandonMarkup({colony_id:'home',name:'Home',is_home:true});
  assert.ok(home.includes('role="status"'));
  assert.ok(!home.includes('data-colony-abandon'));
});

test('untrusted alliance and message content is escaped before HTML insertion',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({escapeHtml,number:String,tab:'messages',state:{messages:[{channel:'world',name:'<img src=x onerror=1>',body:'<script>attack()</script>',created:0}],message_has_more:{world:true},administration:null}});
  const markup=vm.runInContext('systemsView()',box);
  assert.ok(markup.includes('&lt;script&gt;'));
  assert.ok(!markup.includes('<script>attack'));
  assert.ok(!markup.includes('<img src=x'));
  assert.ok(markup.includes('data-message-more'));
  assert.ok(markup.includes('Ältere Nachrichten laden'));
});

test('chat reports exclude own messages and private moderation cases render only to their owner',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const commandForm=(action,body,label)=>`<form data-system="${action}">${body}<button>${label}</button></form>`;
  const actionButton=(action,key,label,fields={})=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key,...fields}))}">${label}</button>`;
  const box=context({escapeHtml,number:String,commandForm,actionButton,tab:'messages',messageChannel:'world',state:{
    id:'reader',server_time:100,profile:{muted_until:0},administration:null,alliances:[],players:[],social:{friends:[],incoming_requests:[],outgoing_requests:[],blocked:[]},
    messages:[
      {id:'own-message',sender:'reader',channel:'world',name:'Reader',body:'Eigener Beitrag',created:1},
      {id:'reported-message',sender:'author',channel:'world',name:'<Author>',body:'<script>bad()</script>',created:2},
    ],message_has_more:{},moderation_cases:[],
  }});
  const markup=vm.runInContext('systemsView()',box);
  assert.equal((markup.match(/data-system="message_report"/g)||[]).length,1);
  assert.ok(markup.includes('name="key" value="reported-message"'));
  assert.ok(!markup.includes('name="key" value="own-message"'));
  assert.ok(markup.includes('&lt;script&gt;bad()&lt;/script&gt;'));
  assert.ok(markup.includes('Deine Moderationsfälle'));
});

test('moderation case queue escapes player text and offers case-specific decisions',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,key,label,fields={})=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key,...fields}))}">${label}</button>`;
  const box=context({escapeHtml,actionButton});
  const markup=vm.runInContext(`adminModerationCasesMarkup({cases:[
    {id:'report-1',case_type:'message_report',reporter_name:'<Reporter>',target_name:'Target',body:'<script>x</script>',reason:'<reason>',created:1},
    {id:'appeal-1',case_type:'mute_appeal',reporter_name:'Player',target_name:'Player',body:null,reason:'Please review',created:2},
  ],cases_has_more:true})`,box);
  assert.ok(markup.includes('&lt;Reporter&gt;'));
  assert.ok(!markup.includes('<script>x</script>'));
  assert.ok(markup.includes('&lt;script&gt;x&lt;/script&gt;'));
  assert.ok(markup.includes('value&quot;:&quot;hide_message'));
  assert.ok(markup.includes('value&quot;:&quot;lift_mute'));
  assert.ok(markup.includes('data-admin-cases-more'));
});

test('ban appeal queue offers restore and denial actions without exposing unsafe text',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,key,label,fields={})=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key,...fields}))}">${label}</button>`;
  const box=context({escapeHtml,actionButton});
  const markup=vm.runInContext(`adminModerationCasesMarkup({cases:[
    {id:'ban-appeal-1',case_type:'account_ban_appeal',reporter_name:'<Pilot>',target_name:'<Pilot>',reason:'<review>',body:null,created:1}
  ],cases_has_more:false})`,box);
  assert.ok(markup.includes('Einspruch gegen Kontosperrung'));
  assert.ok(markup.includes('&lt;Pilot&gt;'));
  assert.ok(markup.includes('&lt;review&gt;'));
  assert.ok(markup.includes('value&quot;:&quot;grant_ban_appeal'));
  assert.ok(markup.includes('value&quot;:&quot;deny_ban_appeal'));
});

test('banned-account appeal form is present and revealed only by the banned-login signal',()=>{
  const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
  const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const community=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  assert.match(html,/<section id="ban-appeal"[^>]*hidden/);
  assert.match(html,/id="ban-appeal-reason"[^>]*maxlength="1000"/);
  assert.match(app,/error\.message==='Dieses Konto ist gesperrt\.'/);
  assert.match(community,/api\('auth\/ban-appeal'/);
  assert.match(community,/recovery_code:recovery\?document\.getElementById\('auth-recovery-code'\)\.value:''/);
});

test('system announcements and private mailbox render separate, escaped views',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,key,label,fields={})=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key,...fields}))}">${label}</button>`;
  const commandForm=(action,body,label)=>`<form data-system="${action}">${body}<button>${label}</button></form>`;
  const input=(name,label,type='text',value='',extra='')=>`<label>${escapeHtml(label)}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${extra}></label>`;
  const box=context({escapeHtml,actionButton,commandForm,input,number:String,state:{
    profile:{role:'admin'},active_world:{id:4},world_id:4,server_time:10,
    announcements:[{id:'public-1',world_id:4,title:'<Wartung>',body:'<script>alert(1)</script>',author_name:'<Mod>',created:1,publish_at:1,emergency:true}],
    system_mail:[{id:'private-1',title:'<Kontohinweis>',body:'Nur für mich',author_name:'Admin',created:2,read_at:null}],
    administration:{users:[{id:'other',name:'<Pilot>'}],users_has_more:false},
  }});
  const markup=vm.runInContext('systemCommunicationMarkup(state)',box);
  assert.ok(markup.includes('&lt;Wartung&gt;'));
  assert.ok(markup.includes('&lt;script&gt;alert(1)&lt;/script&gt;'));
  assert.ok(!markup.includes('<script>alert(1)</script>'));
  assert.ok(markup.includes('Systempostfach'));
  assert.ok(markup.includes('mail_read'));
  assert.ok(markup.includes('admin_mail_send'));
  assert.ok(markup.includes('&lt;Pilot&gt;'));
  assert.ok(markup.includes('NOTFALL'));
  assert.ok(markup.includes('name="publish_at_local"'));
  assert.ok(markup.includes('Notfallankündigung deutlich markieren'));
});

test('moderator announcement controls stay bound to the active world',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,key,label,fields={})=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key,...fields}))}">${label}</button>`;
  const commandForm=(action,body,label)=>`<form data-system="${action}">${body}<button>${label}</button></form>`;
  const input=(name,label,type='text',value='',extra='')=>`<label>${escapeHtml(label)}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${extra}></label>`;
  const box=context({escapeHtml,actionButton,commandForm,input,number:String,state:{
    profile:{role:'moderator'},active_world:{id:4},world_id:4,
    announcements:[{id:'local',world_id:4,title:'Local',body:'World text',author_name:'Mod',created:1},{id:'global',world_id:null,title:'Global',body:'Public text',author_name:'Admin',created:2}],
    system_mail:[],administration:{users:[]},
  }});
  const markup=vm.runInContext('systemCommunicationMarkup(state)',box);
  assert.equal((markup.match(/data-system-action="admin_announcement_archive"/g)||[]).length,1);
  assert.ok(markup.includes('data-payload="{&quot;key&quot;:&quot;local&quot;}"'));
  assert.ok(!markup.includes('admin_mail_send'));
});

test('game event center shows category mute controls and private delivery failures',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(source,/onchange = event => \{\s*const category = event\.currentTarget\.value;\s*void loadWorldEventFeed\(category\);/);
  const helper=source.match(/function worldEventFeedMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'game event center renderer must be available');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({escapeHtml,number:String,pushUiState:{user:'owner',enabled:false,subscribed:false,count:0,status:''},state:{id:'owner',active_world:{id:2}},worldEventFeed:{user:'owner',world_id:2,category:'military',cursor:8,has_more:true,preferences:{economy:true,research:false,military:false,social:false,system:false},delivery_failures:[{id:'safe',kind:'research',category:'research',attempts:5,failed_at:1}],events:[{sequence:8,id:'event-8',category:'military',kind:'attack',created:1}]}});
  const markup=vm.runInContext(`${helper}; worldEventFeedMarkup()`,box);
  assert.match(markup,/data-notification-category="economy" checked/);
  assert.match(markup,/data-notification-category="military"/);
  assert.match(markup,/id="world-event-category"/);
  assert.match(markup,/<fieldset class="world-event-preferences">/);
  assert.match(markup,/option value="military" selected/);
  assert.match(markup,/data-world-events-more="8"/);
  assert.match(markup,/Nicht zugestellte Ereignisse/);
  assert.match(markup,/5 Versuche/);
  assert.match(markup,/Militär/);
});

test('browser push asks explicitly, shows no sensitive preview and supports unsubscribe',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const renderer=source.match(/function worldEventFeedMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  const keys=source.match(/function encodeVapidKey\(value\) \{[\s\S]*?\n\}/)?.[0];
  const box=vm.createContext({escapeHtml:String,number:String,pushUiState:{user:'owner',enabled:true,subscribed:false,count:0,status:''},state:{id:'owner',active_world:{id:1}},worldEventCategory:'',worldEventFeed:null});
  vm.runInContext(`${renderer}; ${keys}`,box);
  const markup=box.worldEventFeedMarkup();
  assert.match(markup,/id="push-enable"/);
  assert.match(markup,/Vorschauen enthalten keine Spiel-, Nachrichten- oder Kontodetails/);
  assert.match(source,/Notification\.requestPermission\(\)/);
  assert.match(source,/id="push-disable"/);
  assert.match(source,/push\/subscriptions\?endpoint=/);
  assert.match(source,/subscription\.unsubscribe\(\)/);
  assert.match(fs.readFileSync(path.join(__dirname,'../static/service-worker.js'),'utf8'),/Es gibt neue Informationen in deinem Imperium/);
});

test('game event category switching loads a fresh category-bound cursor page',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/async function loadWorldEventFeed\(category = worldEventCategory\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'game event loader must be available');
  assert.match(helper,/game-events\?world_id=\$\{worldId\}\$\{selectedCategory\?/);
  assert.match(helper,/worldEventFeed = \{\.\.\.result,user,category:selectedCategory\}/);
  assert.match(source,/worldEventFeed=\{\.\.\.result,user,category,events:\[\.\.\.\(result\.events\|\|\[\]\)\.filter/);
});

test('game event loader requests the selected filter and replaces cursor state',async()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/async function loadWorldEventFeed\(category = worldEventCategory\) \{[\s\S]*?\n\}/)?.[0];
  const calls=[];
  const state={id:'reader',active_world:{id:3}};
  const box=vm.createContext({state,worldEventFeed:{user:'reader',world_id:3,events:[{id:'old'}],cursor:9,has_more:true},worldEventCategory:'',render(){},notify(){},api:async path=>{calls.push(path);return {world_id:3,events:[{id:'economy'}],cursor:4,has_more:false,preferences:{},delivery_failures:[]};}});
  await vm.runInContext(`${helper}; loadWorldEventFeed('economy')`,box);
  assert.deepEqual(calls,['game-events?world_id=3&category=economy']);
  assert.equal(box.worldEventFeed.category,'economy');
  assert.equal(box.worldEventFeed.cursor,4);
  assert.deepEqual(JSON.parse(JSON.stringify(box.worldEventFeed.events)),[{id:'economy'}]);
  assert.equal(box.worldEventFeed.has_more,false);
});

test('market controls bind escaped payloads rather than inline JavaScript',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({escapeHtml});
  const markup=vm.runInContext('actionButton("market_accept", "offer-id", "Tauschen")',box);
  assert.ok(markup.includes('data-system-action="market_accept"'));
  assert.ok(markup.includes('&quot;key&quot;'));
  assert.ok(!markup.includes('onclick='));
});

test('non-admin state renders no moderation controls',()=>{
  const box=context({tab:'admin',state:{administration:null}});
  const markup=vm.runInContext('systemsView()',box);
  assert.ok(markup.includes('Kein Administrationszugriff'));
  assert.ok(!markup.includes('admin_ban'));
});

test('private recipient is selected from known players, not typed as an arbitrary name',()=>{
  const box=context({
    escapeHtml:value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),number:String,
    tab:'messages',messageChannel:'private',
    state:{
      messages:[],players:[{id:'own',name:'Own',x:1,y:2},{id:'other',name:'Other',x:3,y:4}],
      id:'own',alliances:[],alliance_candidates:[],invites:[],diplomacy:[],administration:null,
    },
  });
  vm.runInContext("messageChannel='private'",box);
  const markup=vm.runInContext('systemsView()',box);
  assert.ok(markup.includes('<select name="name" required>'));
  assert.ok(markup.includes('<option value="Other">Other · 3:4</option>'));
  assert.ok(!markup.includes('input name="name" type="text"'));
});

test('alliance supply form lists only supplied alliance targets and escapes names',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function colonySupplyMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'colony and alliance supply forms must be isolated for rendering tests');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({
    escapeHtml,names:['Holz','Stein','Erz'],
    state:{
      colonies:[{colony_id:'home',world_id:1,selected:true}],
      membership:{alliance_id:'alliance'},
      alliance_supply_targets_has_more:true,
      alliance_supply_targets:[{colony_id:'ally-home',world_id:1,x:4,y:7,name:'<script>bad</script>'},{colony_id:'other-world',world_id:2,x:1,y:1,name:'Hidden'}],
      catalog:{units:{ranger:{name:'Träger'}}},units:{ranger:5},resources:[100,100,100],colony_name:'Start',name:'Start',
    },
  });
  vm.runInContext(`${helper}`,box);
  const markup=vm.runInContext('colonySupplyMarkup()',box);
  assert.ok(markup.includes('id="alliance-supply-form"'));
  assert.ok(markup.includes('data-alliance-supply-more'));
  assert.ok(markup.includes('aria-live="polite"'));
  assert.ok(markup.includes('data-action')===false);
  assert.ok(markup.includes('&lt;script&gt;bad&lt;/script&gt;'));
  assert.ok(!markup.includes('<script>bad'));
  assert.ok(!markup.includes('other-world'));
});

test('admin user and failed-job panels expose accessible bounded pages',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const usersHelper=source.match(/function adminUsersMarkup\(admin\) \{[\s\S]*?\n\}/)?.[0];
  const failuresHelper=source.match(/function adminFailuresMarkup\(admin\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(usersHelper,'admin user list renderer must exist');
  assert.ok(failuresHelper,'admin failure list renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,id,label)=>`<button data-system-action="${action}" data-payload="${id}">${label}</button>`;
  const box=context({escapeHtml,actionButton});
  vm.runInContext(usersHelper,box);
  vm.runInContext(failuresHelper,box);
  const users=box.adminUsersMarkup({users:[{id:'u1',name:'<Pilot>',role:'player',banned:false}],users_has_more:true});
  assert.ok(users.includes('&lt;Pilot&gt;'));
  assert.ok(users.includes('data-admin-list-more="users"'));
  assert.ok(users.includes('aria-live="polite"'));
  const failures=box.adminFailuresMarkup({failures:[{id:'f1',job_id:'j1',attempts:2,error:'<Failure>'}],failures_has_more:true});
  assert.ok(failures.includes('&lt;Failure&gt;'));
  assert.ok(failures.includes('data-admin-list-more="failures"'));
  assert.ok(failures.includes('data-system-action="admin_retry"'));
  assert.match(source,/admin\/users/);
  assert.match(source,/admin\/job-failures/);
});

test('admin audit log exposes an accessible older-page control and scoped endpoint',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function adminAuditMarkup\(admin\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'admin audit renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({escapeHtml});
  vm.runInContext(helper,box);
  const markup=box.adminAuditMarkup({audit:[{id:'a1',created:1,action:'<moderation>',target:'<pilot>'}],audit_has_more:true});
  assert.ok(markup.includes('&lt;moderation&gt;'));
  assert.ok(markup.includes('data-admin-audit-more'));
  assert.ok(markup.includes('aria-live="polite"'));
  assert.match(source,/admin\/audit\?before=/);
});

test('faction benefit descriptions match the implemented economy and defense bonuses',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({escapeHtml,tab:'worldops',state:{
    faction_chosen:false,profile:{faction:'pioneers'},events:[],seasons:[],vacation_until:0,server_time:0,
  }});
  const markup=vm.runInContext('systemsView()',box);
  assert.ok(markup.includes('60 statt 50 Prozent'));
  assert.ok(markup.includes('Der Schildwall deiner Kolonie ist im PvP 40 % stärker.'));
});

test('authenticated POST requests automatically include CSRF while auth and recovery remain public',async()=>{
  const requests=[];
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const apiSource=source.match(/async function api\(path, body, method\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(apiSource,'api helper must be available for this regression test');
  const box=vm.createContext({fetch:async(url,options)=>{
    requests.push({url,options});
    return {ok:true,json:async()=>({ok:true})};
  }});
  await vm.runInContext(`let csrf='session-csrf';${apiSource};(async()=>{
    await api('command',{});
    await api('logout',{});
    await api('account/private',{});
    await api('auth/login',{});
    await api('account/public',{});
  })()`,box);
  for(const request of requests.slice(0,3))
    assert.equal(request.options.headers['X-CSRF-Token'],'session-csrf');
  for(const request of requests.slice(3))
    assert.ok(!('X-CSRF-Token' in request.options.headers));
});

test('world map always renders a bounded 20-by-20 window within all 4096 sectors',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const constants=source.match(/const MAP_SIZE = 64, MAP_VIEW_SIZE = 20, MAP_MAX_START = MAP_SIZE - MAP_VIEW_SIZE;/)?.[0];
  const helper=source.match(/function mapCoordinates\(x, y\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(constants&&helper,'map window geometry must be implemented as a testable helper');
  const box=vm.createContext({});
  vm.runInContext(`${constants}\n${helper}`,box);
  const sectors=(x,y)=>JSON.parse(JSON.stringify(vm.runInContext(`mapCoordinates(${x},${y})`,box)));
  for(const [x,y] of [[0,0],[44,0],[0,44],[44,44],[100,-5]]) {
    const view=sectors(x,y);
    assert.equal(view.length,400);
    assert.equal(new Set(view.map(([cx,cy])=>`${cx}:${cy}`)).size,400);
    assert.ok(view.every(([cx,cy])=>cx>=0&&cx<64&&cy>=0&&cy<64));
  }
  const all=new Set();
  for(const y of [0,20,40,44]) for(const x of [0,20,40,44])
    for(const [cx,cy] of sectors(x,y)) all.add(`${cx}:${cy}`);
  assert.equal(all.size,4096);
});

test('map coordinate search accepts valid sectors and rejects malformed or out-of-world values',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const constants=source.match(/const MAP_SIZE = 64, MAP_VIEW_SIZE = 20, MAP_MAX_START = MAP_SIZE - MAP_VIEW_SIZE;/)?.[0];
  const helper=source.match(/function parseMapCoordinate\(value\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(constants&&helper,'coordinate parser must be an isolated, testable helper');
  const box=vm.createContext({});
  vm.runInContext(`${constants}\n${helper}`,box);
  const parse=value=>JSON.parse(JSON.stringify(vm.runInContext(`parseMapCoordinate(${JSON.stringify(value)})`,box)));
  assert.deepEqual(parse('12:34'),[12,34]);
  assert.deepEqual(parse('63, 0'),[63,0]);
  assert.deepEqual(parse('0:63'),[0,63]);
  assert.equal(parse('64:2'),null);
  assert.equal(parse('2:-1'),null);
  assert.equal(parse('north'),null);
});

test('saved map targets receive an on-map favorite marker',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function isMapBookmarked\(bookmarks, targetId\) \{[\s\S]*?\n\}/)?.[0];
  const styles=fs.readFileSync(path.join(__dirname,'../static/multiplayer.css'),'utf8');
  assert.ok(helper,'bookmark membership must be testable');
  assert.match(source,/Merke bis zu 20 Außenposten je Welt/);
  assert.match(source,/bookmarked \? 'bookmarked' : ''/);
  assert.match(styles,/\.tile\.bookmarked::after\{content:'★'/);
  const box=vm.createContext({});
  vm.runInContext(helper,box);
  assert.equal(vm.runInContext('isMapBookmarked(new Set(["target"]),"target")',box),true);
  assert.equal(vm.runInContext('isMapBookmarked(new Set(),"target")',box),false);
  assert.equal(vm.runInContext('isMapBookmarked(new Set(["target"]),null)',box),false);
});

test('saved favorite routes use only known walkable terrain and avoid water',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helpers=source.match(/const MAP_SIZE = 64, MAP_VIEW_SIZE = 20, MAP_MAX_START = MAP_SIZE - MAP_VIEW_SIZE;[\s\S]*?function isMapBookmarked/);
  assert.ok(helpers,'map route calculation must be isolated and testable');
  const box=vm.createContext({});
  vm.runInContext(helpers[0].replace(/function isMapBookmarked[\s\S]*$/, ''),box);
  const terrain={'0:0':'plain','1:0':'water','2:0':'plain','0:1':'plain','1:1':'plain','2:1':'plain','2:2':'plain'};
  const rules={plain:{movement_cost:10},water:{movement_cost:null}};
  const route=JSON.parse(JSON.stringify(vm.runInContext(
    `knownTerrainRoute(${JSON.stringify(terrain)},${JSON.stringify(rules)},[0,0],[2,0])`,box)));
  assert.deepEqual(route,[[0,0],[0,1],[1,1],[2,1],[2,0]]);
  assert.equal(vm.runInContext(`routeCoordinates(${JSON.stringify(route)})`,box),'0:0 → 0:1 → 1:1 → 2:1 → 2:0');
  const unknownGap={...terrain}; delete unknownGap['1:1'];
  assert.equal(vm.runInContext(
    `knownTerrainRoute(${JSON.stringify(unknownGap)},${JSON.stringify(rules)},[0,0],[2,0])`,box),null);
  assert.equal(vm.runInContext(
    `knownTerrainRoute(${JSON.stringify(terrain)},${JSON.stringify(rules)},[0,0],[3,2])`,box),null);
  assert.match(source,/data-route=/);
  assert.match(source,/class="route-steps"/);
  assert.match(source,/aria-live="polite"/);
  assert.match(fs.readFileSync(path.join(__dirname,'../static/multiplayer.css'),'utf8'),/\.tile\.route/);
});

test('map renders server terrain and communicates blocked water and movement modifiers',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(source,/state\.terrain_map\?\.\[`\$\{x\}:\$\{y\}`\]\s*\|\| 'unknown'/);
  assert.match(source,/Wasser ist unpassierbar/);
  assert.match(source,/Gebirge \+20 % Stein\/Erz\/\+25 % Verteidigung/);
  assert.match(source,/Pässe −20 % Wegkosten/);
  assert.doesNotMatch(source,/\(x\*17\+y\*31\)%19/);
});

test('queue cancellation is exposed for upgrades and repair with accessible labels',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const queueSource=source.match(/function queue\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(queueSource,'queue renderer must be available for regression testing');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({state:{server_time:10,jobs:[
    {id:'build-id',kind:'build',label:'<Bau>',due:20,target_level:1,queue_order:0,queued:false},
    {id:'barracks-id',kind:'build',label:'Kaserne',due:30,target_level:1,queue_order:1,queued:true},
    {id:'lab-id',kind:'build',label:'Labor',due:40,target_level:1,queue_order:2,queued:true},
    {id:'repair-id',kind:'terra_repair',label:'Feldspäher',due:25},
    {id:'raid-id',kind:'raid',label:'Raid',due:30},
  ]},escapeHtml});
  const markup=vm.runInContext(`${queueSource};queue()`,box);
  assert.ok(markup.includes('data-action="cancel_job" data-key="build-id"'));
  assert.ok(markup.includes('aria-label="Bauauftrag &lt;Bau&gt; abbrechen"'));
  assert.equal((markup.match(/data-action="cancel_job"/g)||[]).length,4);
  assert.ok(markup.includes('data-action="cancel_job" data-key="repair-id"'));
  assert.ok(markup.includes('aria-label="Feldspäher abbrechen und erstatten"'));
  assert.ok(markup.includes('data-action="queue_move" data-direction="up" data-key="lab-id"'));
  assert.ok(markup.includes('data-action="queue_move" data-direction="down" data-key="barracks-id"'));
  assert.ok(!markup.includes('data-action="cancel_job" data-key="raid-id"'));
});

test('Terra recovery shows escaped expiring wrecks and binds repair to the active colony',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function terraRecoveryMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'Terra wreck renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const state={
    active_world:{terra_combat_ruleset:'FUR-3-TERRA-COMBAT-4',id:7},colony_id:'colony-1',
    terra_recovery_rules:{version:'FUR-3-TERRA-RECOVERY-1',loss_recovery_percent:25,repair_cost_percent:50},
    terra_unit_wrecks:[{id:'wreck-<1>',unit:'scout',amount:3,expires:2000}],jobs:[],
    catalog:{units:{scout:{name:'<Feldspäher>',cost:[80,65,105],time:24}}}
  };
  const box=vm.createContext({escapeHtml,number:value=>String(value),state});
  vm.runInContext(helper,box);
  const markup=box.terraRecoveryMarkup();
  assert.match(markup,/FUR-3-TERRA-RECOVERY-1/);
  assert.match(markup,/data-terra-repair="wreck-&lt;1&gt;"/);
  assert.match(markup,/&lt;Feldspäher&gt;/);
  assert.match(markup,/40 \/ 33 \/ 53 Holz, Stein, Erz/);
  assert.match(markup,/name="count" type="number" min="1" max="3"/);
  assert.match(source,/command\('terra_repair_units',\{wreck_id:f\.dataset\.terraRepair,count:Number\(f\.elements\.count\.value\),world_id:state\.active_world\.id,colony_id:state\.colony_id\}\)/);
  state.jobs=[{kind:'terra_repair'}];
  assert.match(box.terraRecoveryMarkup(),/disabled/);
  state.active_world.terra_combat_ruleset='FUR-2';
  assert.equal(box.terraRecoveryMarkup(),'');
});

test('Terra defense panel escapes catalogs, enforces build gates and binds active colony',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function terraDefenseMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'Terra defense renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const state={
    terra_defense:{version:'FUR-3-TERRA-DEFENSE-1',slot_usage:0,slot_limit:1,power:0,stacks:{kinetic_turret:[]},catalog:{kinetic_turret:{name:'<Geschütz>',kind:'cannon',cost:[500,350,100],repair_cost_percent:50,maximum_count:4,slot_cost:1,defense_power:180,prerequisites:{buildings:{barracks:2},tech:{weapons:1}}}}},
    catalog:{buildings:{barracks:{name:'Kaserne'}},tech:{weapons:{name:'Waffen'}}},
    buildings:{barracks:1},tech:{weapons:0},resources:[10000,10000,10000]
  };
  const box=vm.createContext({state,escapeHtml,number:String,icons:['♣','▧','◈'],cost:item=>item.cost.map(String).join(' / ')});
  vm.runInContext(helper,box);
  let markup=box.terraDefenseMarkup();
  assert.match(markup,/FUR-3-TERRA-DEFENSE-1/);
  assert.match(markup,/&lt;Geschütz&gt;/);
  assert.match(markup,/Voraussetzungen:[^<]*✕ Kaserne 2 · ✕ Waffen 1/);
  assert.match(markup,/data-action="terra_defense_build"[^>]*disabled/);
  state.buildings.barracks=2;state.tech.weapons=1;
  markup=box.terraDefenseMarkup();
  assert.doesNotMatch(markup,/data-action="terra_defense_build"[^>]*disabled/);
  state.terra_defense.stacks.kinetic_turret=[50];
  markup=box.terraDefenseMarkup();
  assert.match(markup,/data-action="terra_defense_repair"[^>]*data-count="1"/);
  assert.match(markup,/Reparaturkosten: ♣ 125 ▧ 88 ◈ 25/);
  assert.match(source,/Object\.assign\(payload,\{world_id:state\.active_world\.id,colony_id:state\.colony_id\}\)/);
  assert.match(source,/build\?terraDefenseMarkup\(\):''/);
});

test('building and technology prerequisite helpers gate actions and escape catalog names',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=['itemPrerequisites','itemPrerequisitesMet','itemPrerequisitesLabel'].map(name=>
    source.match(new RegExp('function '+name+'\\(item\\) \\{[\\s\\S]*?\\n\\}'))?.[0]||'').join('');
  assert.match(helper,/function itemPrerequisites\(item\)/);
  const escapeHtml=value=>String(value).replace(/[<>]/g,c=>c==='<'?'&lt;':'&gt;');
  const box=vm.createContext({
    state:{
      buildings:{lab:0,barracks:1},tech:{tactics:0},
      catalog:{buildings:{lab:{name:'<Labor>'},barracks:{name:'Kaserne'}},tech:{tactics:{name:'Taktik'}}}
    },escapeHtml
  });
  const value=vm.runInContext(helper+'; JSON.stringify({met:itemPrerequisitesMet({requirements:{buildings:{lab:1},tech:{}}}),label:itemPrerequisitesLabel({requirements:{buildings:{lab:1},tech:{}}}),advanced:itemPrerequisitesMet({requirements:{buildings:{},tech:{tactics:1}}})})',box);
  const result=JSON.parse(value);
  assert.equal(result.met,false);
  assert.equal(result.advanced,false);
  assert.equal(result.label,' &lt;Labor&gt; Stufe 1');
});

test('outbound missions expose accessible recall controls but return journeys do not',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function queue\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'mission queue renderer must exist');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({
    state:{server_time:100,jobs:[
      {id:'raid"><x',kind:'raid',label:'Angriff',due:120},
      {id:'return-job',kind:'return',label:'Rückmarsch',due:130},
      {id:'alliance-job',kind:'alliance_supply',label:'Allianzversorgung',due:140},
    ]},
    escapeHtml,
  });
  vm.runInContext(helper,box);
  const markup=box.queue();
  assert.equal((markup.match(/data-action="mission_recall"/g)||[]).length,1);
  assert.ok(markup.includes('data-key="raid&quot;&gt;&lt;x"'));
  assert.ok(markup.includes('aria-label="Angriff zurückrufen"'));
  assert.ok(markup.includes('data-action="alliance_supply_cancel"'));
  assert.equal(markup.includes('data-key="return-job"'),false);
});

test('colony supply form offers only another owned colony and escapes its name and id',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function colonySupplyMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'colony supply screen must be testable');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,names:['Holz','Stein','Erz'],state:{
    id:'owner',name:'Alpha',colony_name:'Alpha',colony_id:'home',
    colonies:[
      {colony_id:'home',world_id:1,name:'Alpha',selected:true},
      {colony_id:'<target&>',world_id:1,name:'<Außenposten>',x:10,y:20,selected:false},
      {colony_id:'another-world',world_id:2,name:'Remote',selected:false},
    ],
    catalog:{units:{ranger:{name:'Ranger'},sentinel:{name:'Wächter'},mech:{name:'Sturmmech'}}},
    units:{ranger:4,sentinel:0,mech:1},resources:[1200,1000,800],
    neutral_market:{goods:[{id:'wood',name:'Holz',amount:1200},{id:'alloy',name:'Legierung',amount:12}]},
    generic_items:{items:[{id:'repair_kit',name:'Feldkit',amount:3}]},
  }});
  const markup=vm.runInContext(`${helper}\ncolonySupplyMarkup()`,box);
  assert.ok(markup.includes('value="&lt;target&amp;&gt;"'));
  assert.ok(markup.includes('&lt;Außenposten&gt;'));
  assert.ok(!markup.includes('another-world'));
  assert.ok(!markup.includes('value="home"'));
  assert.ok(markup.includes('max="4"'));
  assert.ok(markup.includes('name="cargo-2"'));
  assert.ok(markup.includes('name="goods-alloy"'));
  assert.ok(markup.includes('name="item-repair_kit"'));
  assert.ok(markup.includes('max="12"'));
  assert.ok(markup.includes('Versorgung entsenden'));
});

test('market history shows only anonymous aggregates with weighted prices',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  assert.match(source,/Preisverlauf der Welt \(30 Tage\)/);
  assert.match(source,/market-history-title/);
  assert.match(source,/role="list" aria-label="Preisverlauf der Welt"/);
  assert.match(source,/class="audit-row" role="listitem"/);
  assert.match(source,/Noch keine abgeschlossenen Trades im Zeitraum/);
  assert.match(source,/Stundenwerte abgeschlossener Trades; ohne Kontodaten/);
  assert.match(source,/row\.weighted_price_milli\/1000/);
  assert.match(source,/row\.trade_count/);
  assert.doesNotMatch(source,/row\.buyer|row\.seller|row\.user_id/);
  assert.match(source,/data-market-offers-more/);
  assert.match(source,/market\/offers\?before=\$\{encodeURIComponent\(cursor\)\}/);
});

test('market offers render a bounded accessible load-more control',()=>{
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=context({tab:'market',escapeHtml,names:['Holz','Stein','Erz'],icons:['H','S','E'],number:value=>String(value),intro:()=>'',select:()=>'',input:()=>'',commandForm:()=>'',actionButton:()=>'',state:{id:'owner',offers:[{id:'offer-50',owner:'owner',name:'<Pilot>',give_resource:0,give_amount:10,want_resource:1,want_amount:20}],offers_has_more:true,reserve:[0,0,0],market_history:[]}});
  const markup=vm.runInContext('systemsView()',box);
  assert.ok(markup.includes('&lt;Pilot&gt;'));
  assert.ok(markup.includes('Weitere Angebote laden'));
  box.state.offers_has_more=false;
  assert.ok(!vm.runInContext('systemsView()',box).includes('Weitere Angebote laden'));
});

test('combat details remain hidden for players and occupied enemy outposts without reconnaissance',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function combatIntelKnown\(target, player, own, now\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'combat intel policy must be isolated and testable');
  const box=vm.createContext({});
  vm.runInContext(helper,box);
  assert.equal(vm.runInContext('combatIntelKnown({intel_level:"unknown",defense:999,garrison:99},true,false,100)',box),false);
  assert.equal(vm.runInContext('combatIntelKnown({intel_report:{level:1,status:"fresh",expires_at:200,data:{defense:1}}},true,false,100)',box),false);
  assert.equal(vm.runInContext('combatIntelKnown({intel_report:{level:2,status:"stale",expires_at:90,data:{defense:1}}},true,false,100)',box),false);
  assert.equal(vm.runInContext('combatIntelKnown({intel_report:{level:2,status:"fresh",expires_at:200,data:{defense:10}}},true,false,100)',box),true);
  assert.equal(vm.runInContext('combatIntelKnown({owner:"enemy",intel_level:"unknown",defense:999,garrison:99},false,false,100)',box),false);
  assert.equal(vm.runInContext('combatIntelKnown({owner:"self",units:{ranger:2}},false,true,100)',box),true);
  assert.equal(vm.runInContext('combatIntelKnown({owner:null,tier:2},false,false,100)',box),true);
  assert.match(source,/Aufklärung Stufe/);
  assert.match(source,/value="scout">Aufklärung/);
  assert.match(source,/Militärstärke unbekannt, Aufklärung erforderlich/);
  assert.match(source,/Gegnerische Stärke unbekannt/);
  const scoutRisk=source.match(/function scoutMissionRisk\(activeWorld\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(scoutRisk,'scout risk explanation should be isolated and testable');
  const riskBox=vm.createContext({});
  vm.runInContext(scoutRisk,riskBox);
  assert.match(riskBox.scoutMissionRisk({terra_combat_ruleset:'FUR-3-TERRA-COMBAT-1'}),/Gegenaufklärung.*einen Ranger/);
  assert.match(riskBox.scoutMissionRisk({terra_combat_ruleset:'FUR-2'}),/Bericht bleibt privat/);
});

test('combat reports render escaped per-round and per-unit losses and survivors',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function combatReportMarkup\(combat\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'combat report renderer should be independently testable');
  const box=vm.createContext({
    state:{catalog:{units:{ranger:{name:'<Ranger>'}}}},
    escapeHtml:value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
    number:value=>String(value),
    icons:['♣','▧','◈'],
  });
  vm.runInContext(helper,box);
  const html=box.combatReportMarkup({
    rules_version:'FUR-2',participants:{attacker:'<Commander>',defender:'Neutralpost'},
    rounds:[{round:1,attack_power:60,defense_power:55,victory:true,
      attacker:{sent:{ranger:5},losses:{ranger:1},survivors:{ranger:4}},
      defender:{sent:{ranger:2},losses:{ranger:2},survivors:{ranger:0}},loot:[10,0,0]}],
  });
  assert.match(html,/Runde 1/);
  assert.match(html.replace(/<[^>]*>/g,''),/1 verloren/);
  assert.match(html.replace(/<[^>]*>/g,''),/4 überlebt/);
  assert.match(html,/&lt;Commander&gt;/);
  assert.match(html,/&lt;Ranger&gt;/);
  assert.doesNotMatch(html,/<Commander>|<Ranger>/);
  const defense=box.combatReportMarkup({rules_version:'FUR-3-TERRA-COMBAT-4',rounds:[
    {round:1,attack_power:12,defense_power:20,attacker:{sent:{mech:2},losses:{},survivors:{mech:2}},
      defender:{sent:{furdef_kinetic_turret_0:1},losses:{},survivors:{furdef_kinetic_turret_0:1}},loot:[]},
  ],terra_defense:{initial_stacks:{proximity_mines:[100]},minefield:{triggered:true},structure_remaining:{furdef_kinetic_turret_0:62}}});
  assert.match(defense,/Kinetikgeschütz/);
  assert.match(defense,/Annäherungsminen ausgelöst/);
  assert.match(defense,/62 % Integrität/);
  assert.doesNotMatch(defense,/furdef_/);
  const multi=box.combatReportMarkup({rules_version:'FUR-3-TERRA-COMBAT-2',outcome:'attacker_retreat',
    rounds:[{round:1,attack_power:20,defense_power:8,attacker_wings:[{commander:'Alpha',sent:{ranger:3},losses:{ranger:1},survivors:{ranger:2}}],
      defender:{sent:{outpost_fortification:4},losses:{outpost_fortification:1},survivors:{outpost_fortification:3}},loot:[]}],
  });
  assert.match(multi,/Rückzug/);
  assert.match(multi,/Gefechtsphase/);
  assert.match(multi,/Außenpostenbefestigung/);
});

test('neutral outpost battle probe is server authoritative and announced accessibly',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const page=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
  assert.match(page,/<button type="button" id="simulate-battle"[^>]*>Gefechtsprobe<\/button>/);
  assert.match(page,/<p id="battle-simulation" role="status" aria-live="polite"><\/p>/);
  assert.match(source,/api\('simulate-battle',\{target_id:target\.id,army\}\)/);
  assert.match(source,/Deterministische FUR-2-Projektion/);
  assert.match(source,/FUR-3-Schätzung aus \$\{number\(estimate\.samples\)\} reproduzierbaren Szenarien/);
  assert.match(source,/estimate\.attacker_victory_percent/);
  assert.match(source,/geschätzte Minenauslösung/);
  assert.match(source,/estimate\.attacker_losses_total/);
  assert.match(source,/playerPreview=player&&mode==='attack'&&knownIntel/);
  assert.match(source,/Beute unbekannt \(nicht aufgeklärte Ressourcen\)/);
});

test('alliance view exposes private invitation acceptance, decline, and owner cancellation controls',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const page=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
  assert.match(page,/<button data-tab="alliance"[^>]*>[\s\S]*?<span[^>]*>Allianz<\/span><\/button>/);
  assert.match(source,/function allianceViewMarkup\(\)/);
  assert.match(source,/data-action="alliance_accept"/);
  assert.match(source,/data-action="alliance_invite_decline"/);
  assert.match(source,/data-action="alliance_invite_cancel"/);
  assert.match(source,/data-action="alliance_apply"/);
  assert.match(source,/data-action="alliance_application_withdraw"/);
  assert.match(source,/data-action="alliance_application_accept"/);
  assert.match(source,/data-action="alliance_application_reject"/);
  assert.match(source,/data-action="alliance_apply"/);
  assert.match(source,/data-action="alliance_application_withdraw"/);
  assert.match(source,/data-action="alliance_application_accept"/);
  assert.match(source,/data-action="alliance_application_reject"/);
  assert.match(source,/data-action="alliance_apply"/);
  assert.match(source,/data-action="alliance_application_withdraw"/);
  assert.match(source,/data-action="alliance_application_accept"/);
  assert.match(source,/data-action="alliance_application_reject"/);
  assert.match(source,/command\('alliance_invite'/);
});

test('account security view exposes scoped session listing and explicit revocation controls',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  assert.match(source,/account\/sessions/);
  assert.match(source,/data-account-sessions-more/);
  assert.match(source,/account\/sessions\?before=/);
  assert.match(source,/user_agent/);
  assert.match(source,/data-revoke-session/);
  assert.match(source,/account\/sessions\/revoke-others/);
  assert.match(source,/account\/sessions\/revoke-all/);
  assert.match(source,/Sitzungstoken und Netzwerkadressen werden nicht angezeigt/);
  assert.match(source,/commandForm\('account_password'/);
  assert.match(source,/auf allen Geräten abgemeldet/);
});

test('account security exposes one-time recovery code issue and login fallback',()=>{
  const account=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const auth=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  assert.match(account,/recovery_codes_regenerate/);
  assert.match(account,/result\.recovery_codes\.join\('\\n'\)/);
  assert.match(account,/Diese Codes werden nicht erneut angezeigt/);
  assert.match(auth,/recovery_code:recovery\?/);
  assert.match(auth,/window\.furRecoveryCodesPending\) return/);
  assert.match(account,/window\.furRecoveryCodesPending=true/);
});

test('account security offers a reauthenticated personal-data export',()=>{
  const account=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  assert.match(account,/commandForm\('account_export'/);
  assert.match(account,/aktuelles Passwort und bei aktivem Authenticator ein frischer Code verlangt/);
  assert.match(account,/result\.format==='fur-empire-account-export'/);
});


test('Terra alliance operations are exposed only to members and can be joined through the mission panel',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
  assert.match(source,/state\.terra_alliance_attacks/);
  assert.match(source,/alliance_attack_create/);
  assert.match(source,/alliance_attack_join/);
  assert.match(source,/data-alliance-attack-target/);
  assert.match(source,/mission-operation-label/);
  assert.match(source,/FUR-3-TERRA-ACS-2/);
  assert.match(html,/id="mission-operation"/);
});

test('Terra alliance attack panel renders role actions and escapes untrusted labels',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function terraAllianceAttackMarkup\(attacks,userId\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'live alliance view must use an independently testable attack renderer');
  assert.match(source,/terraAllianceAttackMarkup\(state\.terra_alliance_attacks,state\.id\)/);
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const actionButton=(action,key,label)=>`<button data-system-action="${action}" data-payload="${escapeHtml(JSON.stringify({key}))}">${label}</button>`;
  const box=vm.createContext({escapeHtml,actionButton,Date});
  vm.runInContext(helper,box);
  const render=vm.runInContext('terraAllianceAttackMarkup',box);
  const attacks=[
    {id:'leader-op',target_name:'<Home>',target_kind:'player',target_id:'defender',participant_count:2,join_until:1800000000,leader_name:'<Leader>',leader_id:'leader',joined:true},
    {id:'member-op',target_name:'Neutral',target_kind:'outpost',target_id:'post-1',participant_count:1,join_until:1800000000,leader_name:'Leader',leader_id:'leader',joined:true},
    {id:'open-op',target_name:'Neutral 2',target_kind:'outpost',target_id:'post-2',participant_count:1,join_until:1800000000,leader_name:'Leader',leader_id:'leader',joined:false}
  ];
  const leaderMarkup=render(attacks,'leader');
  const memberMarkup=render(attacks,'member');
  assert.match(leaderMarkup,/data-system-action="alliance_attack_cancel"/);
  assert.match(leaderMarkup,/&quot;key&quot;:&quot;leader-op&quot;/);
  assert.match(memberMarkup,/data-system-action="alliance_attack_withdraw"/);
  assert.match(memberMarkup,/&quot;key&quot;:&quot;member-op&quot;/);
  assert.match(memberMarkup,/data-alliance-attack-target="post-2">Truppen beitreten/);
  assert.match(leaderMarkup,/&lt;Home&gt;/);
  assert.match(leaderMarkup,/&lt;Leader&gt;/);
  assert.doesNotMatch(leaderMarkup,/<Home>|<Leader>/);
  assert.match(render([],'member'),/Keine offenen Allianzangriffe/);
});

test('allied garrison controls expose consent, capacity, contribution and recall actions',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/community.js'),'utf8');
  const helper=source.match(/function alliedGarrisonMarkup\(\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'alliance view must render its working garrison controls');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const input=(name,label,type,value,extra='')=>`<label>${escapeHtml(label)}<input name="${name}" type="${type}" value="${value}" ${extra}></label>`;
  const select=(name,label,options)=>`<label>${label}<select name="${name}">${options.map(([value,text])=>`<option value="${escapeHtml(value)}">${escapeHtml(text)}</option>`).join('')}</select></label>`;
  const actionButton=(action,key,label)=>`<button data-system-action="${action}" data-payload="${JSON.stringify({key})}">${label}</button>`;
  const box=vm.createContext({state:{membership:{alliance_id:'a'},alliance_garrison_home_colony_id:'home',colony_id:'home',alliance_garrison_policy:{enabled:false,capacity:80},alliance_garrison_targets:[{colony_id:'host',host_name:'<Host>',name:'Base',capacity:80}],units:{ranger:12},catalog:{units:{ranger:{name:'Ranger'}}},alliance_garrisons:[{id:'g1',contributor_name:'Guest',host_name:'Host',status:'active',army:{ranger:4},can_recall:true}]},escapeHtml,input,select,actionButton,number:String});
  vm.runInContext(helper,box);
  const markup=box.alliedGarrisonMarkup();
  assert.match(markup,/data-system="alliance_garrison_policy"/);
  assert.match(markup,/name="enabled" type="checkbox"/);
  assert.match(markup,/max="300"/);
  assert.match(markup,/data-system="alliance_garrison_station"|id="alliance-garrison-form"/);
  assert.match(markup,/&lt;Host&gt;/);
  assert.match(markup,/alliance_garrison_recall/);
  box.state.membership=null;
  assert.equal(box.alliedGarrisonMarkup(),'');
});

test('orbit station defense renders capacity, upkeep, deployment and withdrawal controls accessibly',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function orbitStationMarkup\(colony\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'orbital station renderer must be independently testable');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml,number:value=>String(value),state:{server_time:1000}});
  vm.runInContext(helper,box);
  const colony={mission_id:'orb-<1>',station:{level:2,active:true,ships:{probe:2}},ships:{probe:5,courier:0},shipbuilding_ready_at:900,ore:5000,ether:1000};
  const markup=box.orbitStationMarkup(colony);
  assert.match(markup,/Raumstation/);
  assert.match(markup,/Garnison 2\/200/);
  assert.match(markup,/Station ausbauen · 1800 Erz \/ 360 Äther/);
  assert.match(markup,/24 Stunden Wartung · 48 Äther/);
  assert.match(markup,/data-orbit-station-transfer="orbit_station_deploy"/);
  assert.match(markup,/data-orbit-station-transfer="orbit_station_withdraw"/);
  assert.match(markup,/type="number" value="1" min="1" max="100" required/);
  assert.match(markup,/orb-&#39;|orb-&lt;1&gt;/);
  const inactive=box.orbitStationMarkup({...colony,station:{...colony.station,active:false}});
  assert.doesNotMatch(inactive,/data-orbit-station-transfer="orbit_station_deploy"/);
  assert.match(inactive,/data-orbit-station-transfer="orbit_station_withdraw"/);
  for (const [override,reason] of [
    [{shipbuilding_ready_at:null},/Schiffbauforschung erforderlich/],
    [{shipbuilding_ready_at:1100},/Schiffbauforschung läuft/],
    [{ore:1199},/Nicht genügend Orbit-Erz oder Äther/],
    [{ether:239},/Nicht genügend Orbit-Erz oder Äther/],
  ]) {
    const blocked=box.orbitStationMarkup({...colony,...override});
    assert.match(blocked,/data-orbit-station="orbit_station_build"[^>]*disabled/);
    assert.match(blocked,reason);
  }
  const inProgress=box.orbitStationMarkup({...colony,station:{...colony.station,ready_at:1200}});
  assert.match(inProgress,/Stationsbau läuft/);
  assert.doesNotMatch(inProgress,/data-orbit-station="orbit_station_build"/);
  assert.match(source,/data-orbit-station-transfer/);
  assert.match(source,/command\(form\.dataset\.orbitStationTransfer/);
  assert.match(source,/data-orbit-defense/);
  assert.match(source,/command\('orbit_build_defense'/);
});
test('orbit mission templates are filtered by action type and escape saved names and IDs',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function orbitTemplateMarkup\(kind, access\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper,'orbital template renderer must be independently testable');
  const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const box=vm.createContext({escapeHtml});
  vm.runInContext(helper,box);
  const access={templates:[
    {id:'fleet-<1>',kind:'fleet',name:'<Vorhut & Eskorte>'},
    {id:'yard-2',kind:'shipyard',name:'Werft'}
  ]};
  const markup=box.orbitTemplateMarkup('fleet',access);
  assert.match(markup,/name="orbit_template"/);
  assert.match(markup,/value="fleet-&lt;1&gt;">&lt;Vorhut &amp; Eskorte&gt;/);
  assert.doesNotMatch(markup,/Werft/);
  assert.match(markup,/data-orbit-template-apply="fleet"/);
  assert.match(markup,/data-orbit-template-save="fleet"/);
  assert.match(markup,/data-orbit-template-delete/);
  assert.match(markup,/name="orbit_template_name" minlength="2" maxlength="32"/);
  assert.match(source,/command\(fleet \? 'orbit_save_fleet_template' : 'orbit_save_shipyard_template'/);
  assert.match(source,/command\('orbit_delete_template'/);
  assert.match(source,/Vorlage geladen\. Prüfe den Auftrag vor dem Start/);
});



test('NPC convoy renders PvE risk, UTC itinerary, private recall and reward actions',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function npcConvoyMarkup\(current\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper);
  const box=vm.createContext({number:String,escapeHtml:value=>String(value).replaceAll('<','&lt;').replaceAll('>','&gt;')});
  vm.runInContext(helper,box);
  const program={convoy:null,rewards:[],slots:12,maximum_rangers:40,power_per_ranger:12,
    npc_power:{escort:120,raid:180},victory_loss_percent:10,defeat_loss_percent:50,reward_ore:300};
  const current={npc_convoy:program,units:{ranger:20},profile:{role:'player'},jobs:[],server_time:100};
  assert.equal(box.npcConvoyMarkup(current),'');
  const admin=box.npcConvoyMarkup({...current,profile:{role:'admin'}});
  assert.match(admin,/data-convoy-schedule/);
  assert.match(admin,/Reines PvE/);
  assert.match(admin,/höchstens 3600 Erz/);
  const point={x:3,y:7,stage:0,starts:100,ends:14500,due:120};
  program.convoy={id:'<event>',name:'<Konvoi>',checkpoints:[point],rendezvous:point,
    can_join:true,booked:0,starts:100};
  const active=box.npcConvoyMarkup(current);
  assert.match(active,/&lt;Konvoi&gt;/);
  assert.match(active,/data-convoy-join="&lt;event&gt;"/);
  assert.match(active,/value="escort"/);
  assert.match(active,/value="raid"/);
  assert.match(active,/<time datetime="[^"]+Z">[^<]+ UTC<\/time>/);
  assert.doesNotMatch(active,/data-convoy-schedule/);
  program.convoy.can_join=false;
  program.convoy.own={status:'marching',mission_id:'<mission>'};
  assert.doesNotMatch(box.npcConvoyMarkup(current),/data-action="npc_convoy_recall"/);
  current.jobs=[{id:'<mission>'}];
  assert.match(box.npcConvoyMarkup(current),/data-action="npc_convoy_recall" data-key="&lt;mission&gt;"/);
  program.convoy=null;
  program.rewards=[{id:'<event>',name:'<Konvoi>',reward_ore:300}];
  assert.match(box.npcConvoyMarkup(current),/data-action="npc_convoy_claim" data-key="&lt;event&gt;"/);
});

test('recurring quests render UTC deadlines and only offer available claims',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
  const helper=source.match(/function recurringQuestMarkup\(program, isAdmin\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(helper);
  const box=vm.createContext({
    number:String,
    names:['Holz','Stein','Erz'],
    escapeHtml:value=>String(value).replaceAll('<','&lt;').replaceAll('>','&gt;')
  });
  vm.runInContext(helper,box);
  const render=box.recurringQuestMarkup;
  assert.equal(render({enabled:false,quests:[]},false),'');
  assert.match(render({enabled:false,quests:[]},true),/data-recurring-quests-enabled="true"/);
  const quest={ends:1794950400,title:'<Aufgabe>',reward:[1,2,3],progress:1,target:1,claimed:false};
  const markup=render({enabled:true,quests:[
    {...quest,period:'daily', key:'day-claim'},
    {...quest,period:'weekly', key:'not-ready', progress:0},
    {...quest,period:'weekly', key:'already-claimed', claimed:true},
  ]},false);
  assert.match(markup,/Tagesaufgaben/);
  assert.match(markup,/Wochenaufgaben/);
  assert.match(markup,/<time datetime="[^"]+\.000Z">[^<]+ UTC<\/time>/);
  assert.match(markup,/&lt;Aufgabe&gt;/);
  assert.match(markup,/1 Holz · 2 Stein · 3 Erz/);
  assert.match(markup,/data-action="recurring_quest_claim" data-key="day-claim"/);
  assert.doesNotMatch(markup,/data-key="(?:not-ready|already-claimed)"/);
  assert.doesNotMatch(markup,/data-recurring-quests-enabled/);
});

test('approved Terra and Orbit artwork catalog is complete and every runtime file exists',()=>{
  const root=path.join(__dirname,'..');
  const catalog=JSON.parse(fs.readFileSync(path.join(root,'static/assets/game/asset-catalog.json'),'utf8'));
  assert.equal(catalog.packages.terra.asset_count,169);
  assert.equal(catalog.packages.orbit.asset_count,133);
  assert.equal(Object.keys(catalog.assets).length,302);
  const urls=Object.values(catalog.assets).flatMap(asset=>asset.files);
  assert.equal(urls.length,512);
  for(const url of urls) {
    assert.match(url,/^\/static\/assets\/game\/(terra|orbit)\//);
    assert.ok(fs.existsSync(path.join(root,'static',url.replace(/^\/static\//,''))),`missing runtime artwork: ${url}`);
  }
  const app=fs.readFileSync(path.join(root,'static/app.js'),'utf8');
  const page=fs.readFileSync(path.join(root,'static/index.html'),'utf8');
  assert.match(app,/function assetUrl\(key\)/);
  assert.match(app,/function assetImage\(key, alt/);
  assert.match(app,/orbit\/ships\/\$\{ship\}/);
  assert.match(app,/terra\/markers\/colony_own/);
  assert.match(page,/fur_wordmark\.svg/);
  assert.match(page,/fur_favicon\.svg/);
});
