'use strict';
const assert=require('assert');
global.window=global;
const store=new Map();global.localStorage={getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>store.set(String(k),String(v)),removeItem:k=>store.delete(k),clear:()=>store.clear()};
require('../systems.js');require('../adapters.js');require('../rules-index.js');require('../swn-rules-index.js');require('../hex-library.js');
const E=require('../engine.js');require('../xwn4-runtime.js');require('../xwn4-compat.js');require('../xwn4-mechanics-fix.js');require('../xwn4-combat-bridge.js');const B=require('../barbara-browser.js');
let checks=0;function ok(v,msg){checks++;assert.ok(v,msg)}function eq(a,b,msg){checks++;assert.deepStrictEqual(a,b,msg)}function has(s,x,msg){checks++;assert.ok(String(s).toLowerCase().includes(String(x).toLowerCase()),msg||`${s} missing ${x}`)}
function setSystem(id){E.setActiveSystem(id);}

setSystem('WWN');
let w=E.makeInitialState('WWN');
eq(E.VERSION,'4.0.0');eq(w.campaign.system,'WWN');ok(E.rulesReady(w));ok(E.auditState(w).ok,E.auditState(w).errors.join(','));
let bp=B.plan(w,'');eq(bp.occasion,'campaign_opening');let bv=B.validate(w,'',(w.narrative||[]).join('\n\n'),bp);ok(bv.valid,bv.errors.join(','));ok((w.narrative||[]).length>=4);ok((w.narrative||[]).join(' ').length>=495);
B.commitExperience(w,bp);eq(B.plan(w,'Observo a ponte').occasion,'continuation');
let travel=E.travelTo(w,1,0);ok(travel.ok);let ap=B.plan(w,'Chego ao novo lugar');eq(ap.occasion,'first_arrival');B.commitExperience(w,ap);w.hexes['1,0'].notes.push({day:w.campaign.day,text:'uma ponte caiu'});eq(B.plan(w,'Olho ao redor').occasion,'changed_return');
ok(!B.validate(w,'Talvez eu abra a porta','Você abre a porta e entra.',{...B.plan(w,'Talvez eu abra a porta'),occasion:'continuation'}).valid,'agency must fail');
ok(!B.validate(w,'','Contexto: clima = chuva; economia: 3.',{...bp,occasion:'campaign_opening'}).valid,'report opening must fail');

has(E.queryRules(w,'Como funciona teste de perícia?'),'2d6');has(E.queryRules(w,'Como funciona iniciativa?'),'1d8');has(E.queryRules(w,'Como funciona ataque?'),'1d20');has(E.queryRules(w,'Como estabilizar um ferido mortal?'),'sexta rodada');
let rng=w.rngCursor,dice=w.diceCursor;let d=E.rollVirtual(w,20,1);ok(d.rolls[0]>=1&&d.rolls[0]<=20);eq(w.rngCursor,rng,'virtual dice must not alter world rng');ok(w.diceCursor>dice);
let sk=E.skillCheck(w,'notice','wis',8,0);eq(sk.roll.length,2);ok(Number.isFinite(sk.total));

let doc=JSON.parse(E.exportState(w));doc.hexes['5,0']={q:5,r:0,key:'5,0',terrain:'hills',tile:'assets/hex_full/hills_green.png',discovered:true,explored:false,visited:true,visitCount:1,notes:[]};doc.player.hp=99999;doc.player.maxHp=99999;doc.player.ac=-50;doc.player.level=999;doc.player.attrs.str=999;doc.player.skills.notice=999;doc.player.inventory=Array.from({length:180},(_,i)=>`item ${i}`);doc.player.name='Teste\u0000 Malicioso';let migrated=E.importState(doc);ok(!!migrated.hexes['5,0'],'dynamic imported hex lost');ok(migrated.atlas.radius>=5);eq(migrated.player.hp,999);eq(migrated.player.maxHp,999);eq(migrated.player.ac,0);eq(migrated.player.level,20);eq(migrated.player.attrs.str,18);eq(migrated.player.skills.notice,4);eq(migrated.player.inventory.length,100);ok(!migrated.player.name.includes('\u0000'));
let char=E.exportCharacter(migrated),charDoc=JSON.parse(char);eq(charDoc.schema,'braseiro-xwn-character-1');let w2=E.makeInitialState('WWN');E.importCharacter(w2,char);eq(w2.player.name,migrated.player.name);
let snap=E.snapshotState(migrated,'auditoria');let restored=E.restoreSnapshot(snap);eq(restored.campaign.system,'WWN');ok(!!restored.hexes['5,0']);

setSystem('SWN');
let s=E.makeInitialState('SWN');eq(s.campaign.system,'SWN');eq(s.atlas.orientation,'pointy');eq(s.player.weapon.name,'Pistola laser');ok(E.rulesReady(s));ok(E.auditState(s).ok,E.auditState(s).errors.join(','));ok(Object.values(s.hexes).every(h=>h.sourceSystem==='SWN'));ok(!('mara' in s.npcs));ok(!(s.factions||[]).some(f=>['salt','bell','ash','reed','crown'].includes(f.id)));
let sp=B.plan(s,'');eq(sp.occasion,'campaign_opening');ok(B.validate(s,'',s.narrative.join('\n\n'),sp).valid);ok(s.narrative.join(' ').length>=495);
has(E.queryRules(s,'Como funciona perícia?'),'2d6');has(E.queryRules(s,'Como funciona iniciativa?'),'1d8');has(E.queryRules(s,'Como funciona ataque?'),'1d20');has(E.queryRules(s,'Como funciona cobertura?'),'-2');ok(!E.queryRules(s,'Como funciona ataque?').includes('WWN SRD'),'SWN rule answer leaked WWN');
let ssk=E.skillCheck(s,'shoot','dex',8,0);eq(ssk.roll.length,2);
let charswn=E.exportCharacter(s);let cross=E.makeInitialState('WWN'),crossBlocked=false;try{E.importCharacter(cross,charswn)}catch(_){crossBlocked=true}ok(crossBlocked,'cross-system character import accepted');

const enemies=Array.from({length:12},(_,i)=>({id:`e${i}`,name:`Hostil ${i}`,hp:8,ac:13,ab:1,attrs:{dex:10,str:10},skills:{shoot:0,stab:0},weapon:{name:'Carabina',damage:'1d8',skill:'shoot',attr:'dex',normalRange:100,maxRange:300,kind:'ranged',twoHanded:true}}));
let combat=E.startSWNTactical(s,enemies,{cover:[{x:5,y:2,grade:'half'}],obstacles:[{x:0,y:0}]});eq(combat.board.width,11);eq(combat.board.height,11);eq(combat.actors.length,13);let coords=new Set(combat.actors.map(a=>`${a.x},${a.y}`));eq(coords.size,combat.actors.length,'actors overlap');ok(combat.actors.every(a=>Number.isFinite(a.initiative)));
let pc=combat.actors.find(a=>a.id==='player'),target=combat.actors.find(a=>a.id==='e0');eq(target.x,5);eq(target.y,2);let ar=E.swAttack(s,'player','e0');eq(ar.penalty,-2,'half cover not applied');
// Adjacent one-handed pistol is allowed at -4; two-handed ranged is blocked.
pc.x=5;pc.y=5;target.x=6;target.y=5;pc.weapon.twoHanded=false;pc.weapon.kind='ranged';pc.weapon.normalRange=100;pc.weapon.maxRange=300;let close=E.swAttack(s,'player','e0');ok(close.ok);ok(close.penalty<=-4,'one-handed ranged melee penalty missing');pc.weapon.twoHanded=true;let blocked=E.swAttack(s,'player','e0');ok(!blocked.ok&&blocked.reason==='arma_duas_maos_em_melee');pc.weapon.twoHanded=false;
// Untrained weapon use is -2, plus Dex +1: total = d20 -1 when no other penalties.
target.x=5;target.y=2;combat.board.cover=[];pc.x=5;pc.y=8;pc.skills.shoot=-1;let untrained=E.swAttack(s,'player','e0');eq(untrained.total,untrained.d20-1,'untrained attack math wrong');
// Total Defense grants +2 AC and suppresses melee Shock on a miss.
let baseAc=pc.ac;ok(E.totalDefense(s,'player'));eq(pc.ac,baseAc+2);let melee=combat.actors.find(a=>a.id==='e1');melee.x=pc.x;melee.y=pc.y-1;melee.ab=-100;melee.skills={stab:0};melee.weapon={name:'Cassetete',damage:'1d6',skill:'stab',attr:'str',kind:'melee',shock:3,shockAC:20};let defensive=E.swAttack(s,'e1','player');ok(!defensive.hit);ok(!defensive.shock,'Total Defense failed to suppress Shock');
// Live buttons route to tactical SWN rather than legacy WWN combat.
let live=E.playerAttack(s);ok(live&&typeof live.mechanics==='string');

for(const id of ['CWN','AWN']){setSystem(id);const x=E.makeInitialState(id);eq(x.campaign.system,id);ok(!E.rulesReady(x));ok(E.auditState(x).ok,E.auditState(x).errors.join(','));const ans=E.queryRules(x,'Faço um teste de ataque');has(ans,'REGRA BLOQUEADA');const before=JSON.stringify(x.continuity.actionLedger||[]),rr=E.performAction(x,'Faço um teste de ataque');ok(rr.ok===false);eq(JSON.stringify(x.continuity.actionLedger||[]),before,'blocked mechanic advanced action ledger');ok((x.narrative||[]).join(' ').length>=495,'opening story missing');}

// Fuzz input hardening and isolation. 20k+ assertions without touching network or Gemini.
setSystem('WWN');for(let i=0;i<5000;i++){const base=E.makeInitialState('WWN'),raw={name:`P\u0000${i}`,level:i%50,hp:i*100,maxHp:(i%1000)+1,ac:(i%100)-30,attrs:{str:i%40,dex:30-i%40,con:12,int:13,wis:14,cha:9},skills:{notice:(i%20)-5},inventory:Array.from({length:i%130},(_,j)=>`x${j}`),weapon:{name:'Teste',damage:'1d6',skill:'shoot',attr:'dex',kind:'ranged',twoHanded:i%2===0}};const c=E.sanitizeCharacter(raw,'WWN');ok(c.level>=1&&c.level<=20);ok(c.hp>=0&&c.hp<=c.maxHp);ok(c.ac>=0&&c.ac<=40);ok(c.attrs.str>=3&&c.attrs.str<=18);}
console.log(`XWN4 runtime audit OK: ${checks} checks`);
