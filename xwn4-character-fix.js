(function(global){
  'use strict';
  const E=global.XWNEngine;if(!E?.sanitizeCharacter)return;
  function clone(v){return JSON.parse(JSON.stringify(v));}
  function bounded(v,min=0,max=999){const n=Number(v);return Number.isFinite(n)?Math.max(min,Math.min(max,Math.round(n))):undefined;}
  function portableWeapon(player,system){const w=clone(player?.weapon||{});w.twoHanded=w.twoHanded===true;if(system==='SWN'){
    const ammo=bounded(player?.weapon?.ammo);const maxAmmo=bounded(player?.weapon?.maxAmmo);if(ammo!==undefined)w.ammo=ammo;if(maxAmmo!==undefined)w.maxAmmo=maxAmmo;
  }else{delete w.ammo;delete w.maxAmmo;}return w;}
  E.exportCharacter=function(state){const system=E.systemId(state?.campaign?.system),character=E.sanitizeCharacter(state?.player,system);character.weapon=portableWeapon(state?.player,system);character.sourceSystem=system;return JSON.stringify({schema:'braseiro-xwn-character-1',system,exportedAt:new Date().toISOString(),character},null,2);};
  E.importCharacter=function(state,raw){const doc=typeof raw==='string'?JSON.parse(raw):clone(raw);if(!doc||doc.schema!=='braseiro-xwn-character-1'||!doc.character)throw new Error('Ficha JSON inválida.');const system=E.systemId(state?.campaign?.system),incoming=String(doc.system||'').toUpperCase();if(incoming!==system)throw new Error('Ficha pertence a outro sistema.');const clean=E.sanitizeCharacter(doc.character,system),src=doc.character.weapon||{};clean.weapon.twoHanded=src.twoHanded===true;if(system==='SWN'){const ammo=bounded(src.ammo),maxAmmo=bounded(src.maxAmmo);if(ammo!==undefined)clean.weapon.ammo=ammo;if(maxAmmo!==undefined)clean.weapon.maxAmmo=maxAmmo;}clean.sourceSystem=system;state.player=clean;return clean;};
  if(typeof module!=='undefined'&&module.exports)module.exports=E;
})(typeof window!=='undefined'?window:globalThis);
