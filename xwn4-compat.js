(function(global){
  'use strict';
  const E=global.XWNEngine,A=global.XWN_ADAPTERS||{};
  if(!E||!E.systemId)throw new Error('xwn4-runtime must load before xwn4-compat');
  const DOMAIN={SWN:{terrain:'space',tile:'assets/domain/space.svg',label:'Setor / espaço local',mph:1,exploreDays:1,encounterDie:8,forage:99,visibility:'sensores',danger:2},CWN:{terrain:'urban',tile:'assets/domain/urban.svg',label:'Distrito urbano',mph:2,exploreDays:1,encounterDie:8,forage:99,visibility:'urbana',danger:2},AWN:{terrain:'wasteland',tile:'assets/domain/wasteland.svg',label:'Ermo pós-apocalíptico',mph:2,exploreDays:1,encounterDie:8,forage:12,visibility:'aberta',danger:3}};
  const oldMake=E.makeInitialState,oldImport=E.importState,oldExport=E.exportState,oldAudit=E.auditState;
  const merged={...E.TERRAIN};for(const [sys,d] of Object.entries(DOMAIN))merged[d.terrain]={label:d.label,mph:d.mph,exploreDays:d.exploreDays,encounterDie:d.encounterDie,forage:d.forage,visibility:d.visibility,danger:d.danger,css:d.terrain,tile:d.tile,sourceSystem:sys,presentationOnly:true};E.TERRAIN=Object.freeze(merged);

  function storageKey(sys=E.activeSystem()){return `braseiro_xwn_v400_${E.systemId(sys).toLowerCase()}`;}
  try{Object.defineProperty(E,'STORAGE_KEY',{configurable:true,enumerable:true,get(){return storageKey();}});}catch(_){E.STORAGE_KEY=storageKey();}
  E.storageKeyFor=storageKey;

  function addPresentation(state){const sys=E.systemId(state?.campaign?.system);if(sys==='WWN')return state;const d=DOMAIN[sys];if(!d)return state;for(const h of Object.values(state.hexes||{})){h.terrain=d.terrain;h.tile=d.tile;h.road=false;h.presentationTerrain=true;}state.atlas.presentationTile=d.tile;return state;}
  function removePresentation(doc){const sys=E.systemId(doc?.campaign?.system);if(sys==='WWN')return doc;for(const h of Object.values(doc?.hexes||{})){if(h?.presentationTerrain||DOMAIN[sys]?.terrain===h?.terrain){delete h.terrain;delete h.tile;delete h.road;delete h.presentationTerrain;}}return doc;}
  E.makeInitialState=function(sys=E.activeSystem()){return addPresentation(oldMake(sys));};
  E.importState=function(raw){let doc=typeof raw==='string'?JSON.parse(raw):JSON.parse(JSON.stringify(raw));doc=removePresentation(doc);return addPresentation(oldImport(doc));};
  E.exportState=function(state){const copy=JSON.parse(JSON.stringify(state));removePresentation(copy);copy.version=E.VERSION;return JSON.stringify(copy,null,2);};
  E.addPresentationFields=addPresentation;E.removePresentationFields=removePresentation;
  E.auditState=function(state){const sys=E.systemId(state?.campaign?.system),errors=[];if(state?.version!==E.VERSION)errors.push('version');if(state?.system?.id!==sys)errors.push('system.id');if(state?.rules?.systemId!==sys)errors.push('rules.systemId');if(sys!=='WWN'){const d=DOMAIN[sys];for(const h of Object.values(state?.hexes||{})){if(h.sourceSystem!==sys)errors.push(`hex owner mismatch ${h.key}`);if(h.road)errors.push(`road leak ${h.key}`);if(h.terrain!==d.terrain||h.tile!==d.tile)errors.push(`presentation domain mismatch ${h.key}`);if(h.poi&&h.key!=='0,0'&&['settlement','farm','site','ruin','fort','hazard','landmark','water'].includes(h.poi.kind))errors.push(`fantasy poi leak ${h.key}`);}}if(!state?.player||!state?.hexes||!state?.campaign||!state?.continuity||!state?.world)errors.push('missing_core_state');return {ok:!errors.length,system:sys,rulesReady:E.rulesReady(state),errors};};
  E.DOMAIN_PRESENTATION=Object.freeze(DOMAIN);
  if(typeof module!=='undefined'&&module.exports)module.exports=E;
})(typeof window!=='undefined'?window:globalThis);
