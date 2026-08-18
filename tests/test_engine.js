const assert=require('assert');
const fs=require('fs'); const path=require('path');
global.window=global; require('../rules-index.js'); require('../hex-library.js');
const E=require('../engine.js');
let count=0; const ok=(x,msg)=>{assert.ok(x,msg);count++;};
const eq=(a,b,msg)=>{assert.deepStrictEqual(a,b,msg);count++;};

let s=E.makeInitialState();
ok(E.VERSION==='3.0.0','version 3');
ok(E.HEX_RADIUS===4,'radius 4');
eq(Object.keys(s.hexes).length,61,'61 hexes');
ok(s.atlas.orientation==='flat','flat orientation');
eq(Object.values(s.hexes).filter(h=>h.discovered).map(h=>h.key),['0,0'],'only start revealed');
ok(Object.values(s.hexes).every(h=>String(h.tile).startsWith('assets/hex_full/')),'full bleed tiles');
ok(new Set(Object.values(s.hexes).map(h=>h.tile)).size>=20,'tile diversity');
eq(global.XWN_HEX_LIBRARY.length,30,'30 library variants');
ok(s.continuity&&Array.isArray(s.continuity.actionLedger),'continuity ledger exists');
ok(Array.isArray(s.world.secretLedger)&&Array.isArray(s.world.factionTraffic),'world ledgers exist');

// Theme periods.
eq(E.periodOfDay(2),'dawn','dawn'); eq(E.periodOfDay(8),'morning','morning'); eq(E.periodOfDay(15),'afternoon','afternoon'); eq(E.periodOfDay(22),'night','night');

// Fog: traveling reveals destination only, never the ring.
let fog=E.makeInitialState(); const beforeHidden=Object.values(fog.hexes).filter(h=>!h.discovered).length;
let tr=E.travelTo(fog,1,0); ok(tr.ok,'travel ok'); ok(fog.hexes['1,0'].discovered,'destination revealed');
eq(Object.values(fog.hexes).filter(h=>h.discovered).length,2,'no neighbor ring reveal on travel');
ok(beforeHidden-Object.values(fog.hexes).filter(h=>!h.discovered).length===1,'exactly one new hex revealed');
ok(fog.continuity.actionLedger.some(x=>x.type==='movement'&&x.to==='1,0'),'movement immutable ledger');
ok(Object.keys(fog.continuity.familiarRoutes).length===1,'familiar route cache');
// Avoid pending encounter for exploration assertion.
fog.combat=null; fog.encounter=null; const discoveredBeforeExplore=Object.values(fog.hexes).filter(h=>h.discovered).length; E.exploreCurrentHex(fog);
eq(Object.values(fog.hexes).filter(h=>h.discovered).length,discoveredBeforeExplore,'explore does not reveal neighbors');
ok(fog.continuity.actionLedger.some(x=>x.type==='exploration'),'exploration ledger');

// Reaction/morale/instinct rules are deterministic and bounded.
let rstate=E.makeInitialState(); for(let i=0;i<20;i++){const r=E.reactionRoll(rstate,E.ENEMIES.road_bandit);ok(r.total>=0&&r.total<=14,'reaction bounded')}
let cstate=E.makeInitialState(); cstate.combat={enemy:{...E.ENEMIES.road_bandit},round:2}; let m=E.moraleCheck(cstate);ok(m.total>=2&&m.total<=12&&typeof m.failed==='boolean','morale 2d6'); let inst=E.instinctCheck(cstate);ok(inst.roll>=1&&inst.roll<=10&&typeof inst.failed==='boolean','instinct d10');
let encState=E.makeInitialState(),enc=E.beginEncounter(encState,{...E.ENEMIES.road_bandit},'teste');ok(enc.reaction&&/REAÇÃO/.test(enc.mechanics),'reaction before encounter');ok(encState.encounter||encState.combat,'encounter has parley or combat');

// Faction turn: WWN monthly strategic layer callable and logged.
let fstate=E.makeInitialState(); const wt=fstate.campaign.worldTurn; E.runFactionTurn(fstate,30);eq(fstate.campaign.worldTurn,wt+1,'faction turn advances');ok(fstate.world.factionTraffic.length>=fstate.factions.length,'faction traffic logged');ok(fstate.world.secretLedger.some(x=>x.type==='faction_turn'),'faction secret ledger');

// NPC identity + token + Gemini continuity.
let v=E.makeInitialState(); ok(E.npcsAt(v,'0,0').some(n=>n.id==='mara'),'Mara present'); E.setEntityToken(v,'mara',{dataUrl:'data:image/jpeg;base64,YWJj',fileName:'mara.jpg',mimeType:'image/jpeg'}); let bundle=E.makeGeminiImageBundle(v);ok(bundle.references.some(x=>x.entityId==='mara'),'Gemini token attached');ok(/Não troque rosto|tokens anexados|identidade/i.test(bundle.prompt),'visual identity prompt'); let restored=E.importState(E.exportState(v));eq(restored.visual.tokens.mara.fileName,'mara.jpg','token persists');

// Ordinary dialogue doesn't demand social test and rumor gets provenance.
let talk=E.makeInitialState();let talkRes=E.performAction(talk,'Pergunto a Mara o que aconteceu na estrada?');ok(/SEM TESTE SOCIAL/.test(talkRes.mechanics),'basic talk no social roll');ok(Object.keys(talk.world.rumorConfidence).length>0,'rumor provenance');ok(talk.continuity.actionLedger.some(x=>x.type==='player_action'),'player action ledger');

// Rules channel protected and indexed.
let qstate=E.makeInitialState();const snapshot=JSON.stringify({day:qstate.campaign.day,hour:qstate.campaign.hour,current:qstate.current,journal:qstate.journal,world:qstate.world,continuity:qstate.continuity,rng:qstate.rngCursor});
const queries=[['Como estabilizar um ferido mortal?',48],['Como funciona explorar um hex?',54],['Como funciona iniciativa?',45],['Como funciona uma reação?',79],['Como funciona moral?',80],['Como funciona instinto?',81],['Como funcionam facções?',82]];
for(const [q,page] of queries){const ans=E.queryRulesIndexed(qstate,q,global.XWN_RULE_INDEX);ok(ans.includes(`WWN SRD p. ${page}`),`rule page ${page}`)}
const after=JSON.stringify({day:qstate.campaign.day,hour:qstate.campaign.hour,current:qstate.current,journal:qstate.journal,world:qstate.world,continuity:qstate.continuity,rng:qstate.rngCursor});eq(after,snapshot,'rules do not advance fiction/world/rng');

// Old save migration must undo v1 radial fog and add V3 ledgers/world.
let legacy=E.makeInitialState();legacy.version='1.5.0';legacy.atlas.radius=3;delete legacy.continuity;delete legacy.world.rumorConfidence;delete legacy.npcs.selka;Object.values(legacy.hexes).forEach(h=>{delete h.tile; h.discovered=true; h.visited=false; h.explored=false});legacy.hexes['0,0'].visited=true;legacy.hexes['0,0'].explored=true;let mig=E.importState(JSON.stringify(legacy));
eq(Object.keys(mig.hexes).length,61,'migration expands atlas');eq(Object.values(mig.hexes).filter(h=>h.discovered).length,1,'migration removes old radial fog reveal');ok(!!mig.npcs.selka,'migration restores canonical NPCs');ok(mig.continuity&&Array.isArray(mig.continuity.actionLedger),'migration adds continuity');ok(Object.values(mig.hexes).every(h=>h.tile&&h.tile.startsWith('assets/hex_full/')),'migration full bleed tiles');

// Source/UI static invariants.
const root=path.resolve(__dirname,'..'); const html=fs.readFileSync(path.join(root,'index.html'),'utf8'),css=fs.readFileSync(path.join(root,'styles.css'),'utf8'),app=fs.readFileSync(path.join(root,'app.js'),'utf8'),sw=fs.readFileSync(path.join(root,'sw.js'),'utf8'),manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.webmanifest'),'utf8')),audio=fs.readFileSync(path.join(root,'audioEngineV2.js'),'utf8');
for(const p of ['morning','afternoon','night','dawn'])ok(css.includes(`body[data-period="${p}"]`),`theme ${p}`);
ok(!css.includes('.road-stroke'),'old road stroke removed');ok(css.includes('playerBeacon')&&!css.includes('rotate(45deg);border-right:2px solid var(--accent)'), 'player marker upgraded');ok(app.includes('visibleRoadDirs.length>=2'),'roads require topology');ok(app.includes('launchGeminiForImage'),'direct Gemini flow');ok(app.includes('com.google.android.apps.bard'),'Gemini Android package flow');ok(app.includes('navigator.share(payload)'),'share tokens to Gemini');ok(manifest.share_target?.method==='POST','PWA share target POST');ok(sw.includes('__shared_scene_image__')&&sw.includes('share-target'),'share-back image reception');
ok(audio.includes('gemini-3.1-flash-tts-preview')&&audio.includes('gemini-2.5-flash-preview-tts'),'Forbidden Lands TTS chain');ok(audio.includes('Charon'),'Charon voice');ok(audio.includes('320')&&audio.includes('680'),'fast chunk profile');
for(const tab of ['play','character','journal','rules','world','audio','settings'])ok(html.includes(`data-page="${tab}"`),`tab ${tab}`);
const ids=[...app.matchAll(/\$\('([^']+)'\)/g)].map(m=>m[1]);const missing=[...new Set(ids)].filter(id=>!new RegExp(`id=["']${id}["']`).test(html));eq(missing,[],'all app DOM ids exist');
const fullDir=path.join(root,'assets','hex_full');const pngs=fs.readdirSync(fullDir).filter(x=>x.endsWith('.png'));ok(pngs.length>=30,'30+ full bleed png assets');
console.log(`PASS ${count} assertions — BRASEIRO XWN WWN ${E.VERSION}`);
