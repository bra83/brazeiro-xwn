(function(global){
  'use strict';
  const E=global.XWNEngine;if(!E?.systemId||!E.swAttack)return;
  const oldSanitize=E.sanitizeCharacter,oldMake=E.makeInitialState,oldImport=E.importState;
  function ensureWeapon(w,raw){if(!w)return w;w.twoHanded=raw?.weapon?.twoHanded===true||w.twoHanded===true;return w;}
  E.sanitizeCharacter=function(raw,sys){const out=oldSanitize(raw,sys);ensureWeapon(out.weapon,raw);return out;};
  E.makeInitialState=function(sys=E.activeSystem()){const s=oldMake(sys);if(E.systemId(s.campaign.system)==='SWN')ensureWeapon(s.player.weapon,{weapon:{twoHanded:false}});return s;};
  E.importState=function(raw){const source=typeof raw==='string'?JSON.parse(raw):JSON.parse(JSON.stringify(raw)),s=oldImport(source);ensureWeapon(s.player.weapon,source?.player);return s;};
  function distance(a,b){return Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));}
  function coverPenalty(combat,target){const c=(combat.board.cover||[]).find(x=>Number(x.x)===target.x&&Number(x.y)===target.y);return c?.grade==='full'?-4:c?-2:0;}
  function actor(combat,id){return combat?.actors?.find(a=>a.id===id);}
  function attrMod(score){return E.attrMod(Number(score)||10);}
  E.swAttack=function(state,attackerId='player',targetId){
    const c=state?.combat?.system==='SWN'?state.combat:null;if(!c)throw new Error('swn_combat_not_active');const a=actor(c,attackerId),t=actor(c,targetId||c.actors.find(x=>x.side!==a?.side)?.id);if(!a||!t||a.hp<=0||t.hp<=0)throw new Error('invalid_combat_actor');
    const w=a.weapon||{},range=distance(a,t)*2,kind=w.kind||'ranged';let penalty=coverPenalty(c,t);
    if(kind==='melee'&&distance(a,t)>1)return {ok:false,reason:'fora_de_alcance_corpo_a_corpo'};
    if(kind!=='melee'){
      if(range>Number(w.maxRange||100))return {ok:false,reason:'fora_de_alcance'};
      if(range>Number(w.normalRange||30))penalty-=2;
      const adjacent=c.actors.some(x=>x.side!==a.side&&x.hp>0&&distance(a,x)<=1&&String(x.weapon?.kind||'ranged')==='melee');
      if(adjacent){if(w.twoHanded===true)return {ok:false,reason:'arma_duas_maos_em_melee'};penalty-=4;}
    }
    const d20=E.rollVirtual(state,20,1).total,skill=Number(a.skills?.[w.skill]??-1),skillPart=skill<0?-2:skill,mod=attrMod(a.attrs?.[w.attr]??10),total=d20+Number(a.ab||0)+skillPart+mod+penalty,hit=total>=Number(t.ac||10);let damage=0,shock=false;
    if(hit){const m=String(w.damage||'1d6').match(/(\d+)d(\d+)(?:\s*([+-])\s*(\d+))?/i);if(m){const rr=E.rollVirtual(state,+m[2],+m[1]);damage=rr.total+(m[3]?(m[3]==='+'?1:-1)*+m[4]:0)+mod;}damage=Math.max(damage,(Number(w.shock||0)>0&&Number(t.ac)<=Number(w.shockAC||0))?Number(w.shock||0)+mod:0);}else if(Number(w.shock||0)>0&&Number(t.ac)<=Number(w.shockAC||0)&&kind==='melee'&&!t.totalDefense){damage=Math.max(0,Number(w.shock)+mod);shock=damage>0;}
    t.hp=Math.max(0,t.hp-damage);if(t.id==='player')state.player.hp=t.hp;if(c.enemy?.id===t.id)c.enemy=t;c.log.push({round:c.round,type:'attack',attacker:a.id,target:t.id,d20,total,penalty,rangeMeters:range,hit,shock,damage});return {ok:true,d20,total,penalty,rangeMeters:range,hit,shock,damage,targetHp:t.hp,mechanics:`SWN Revised p. 49–50 — 1d20 + AB + perícia + atributo${penalty?` ${penalty}`:''} vs AC ${t.ac}.`};
  };
  if(typeof module!=='undefined'&&module.exports)module.exports=E;
})(typeof window!=='undefined'?window:globalThis);
