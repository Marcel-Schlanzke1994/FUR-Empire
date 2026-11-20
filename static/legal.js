'use strict';
fetch('/api/v1/public-config').then(response=>response.json()).then(config=>{
  document.getElementById('operator').textContent=[config.operator_name||'Lokale Entwicklungswelt',config.operator_contact||'Noch keine öffentlichen Betreiberangaben hinterlegt.'].join(' · ');
  document.getElementById('deployment-note').textContent=config.production?'Diese Informationen müssen vom Betreiber für den konkreten öffentlichen Betrieb geprüft und vervollständigt werden.':'Du verwendest eine lokale Entwicklungswelt. Kontodaten werden auf diesem Rechner gespeichert.';
}).catch(()=>{document.getElementById('operator').textContent='Betreiberinformationen konnten nicht geladen werden. Bitte später erneut versuchen.';});
