from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
checks=0
def ok(v,msg):
    global checks; checks+=1
    if not v: raise AssertionError(msg)
def text(p): return (ROOT/p).read_text('utf-8')
idx=text('index.html'); app=text('app.js'); css=text('styles.css'); sw=text('sw.js'); manifest=json.loads(text('manifest.webmanifest'))
required_scripts=['systems.js','adapters.js','hex-library.js','rules-index.js','swn-rules-index.js','engine.js','xwn4-runtime.js','xwn4-compat.js','xwn4-mechanics-fix.js','xwn4-migration.js','xwn4-combat-bridge.js','barbara-browser.js','audioEngineV2.js','local-audio-library.js','snapshot-store.js','gmBridge.js','app.js','xwn4-ui.js']
pos=[]
for s in required_scripts:
    ok(f'src="{s}"' in idx,f'missing script {s}')
    pos.append(idx.index(f'src="{s}"'))
ok(pos==sorted(pos),'script order is unsafe')
for p in required_scripts:
    ok((ROOT/p).is_file(),f'missing runtime file {p}')
for p in ['assets/domain/space.svg','assets/domain/urban.svg','assets/domain/wasteland.svg','assets/app-icon.svg']:
    ok((ROOT/p).is_file(),f'missing asset {p}')
    if p.endswith('.svg'):
        s=text(p);ok('width="224"' in s and 'height="194"' in s,f'bad domain tile dimensions {p}')
ids=set(re.findall(r'id="([A-Za-z0-9_-]+)"',idx))
for ref in sorted(set(re.findall(r"\$\('([^']+)'\)",app))): ok(ref in ids,f'app references absent DOM id {ref}')
ok('[hidden]{display:none!important}' in css.replace(' ',''),'hidden CSS invariant missing')
ok('BRASEIRO XWN 4.0' in idx,'visible version missing')
ok('Motor Barbara' in manifest['name'],'manifest not Barbara-branded')
ok(manifest.get('share_target',{}).get('method')=='POST','share target lost')
for s in required_scripts+['assets/domain/space.svg','assets/domain/urban.svg','assets/domain/wasteland.svg']:
    ok(("./"+s) in sw,f'service worker missing {s}')
ok("braseiro-xwn-v400-barbara" in sw,'service worker cache not versioned')
hexes=list((ROOT/'assets'/'hex_full').glob('*.png'))
ok(len(hexes)>=44,f'WWN hex library regressed: {len(hexes)}')
lib=text('hex-library.js')
for p in hexes: ok(p.stem in lib or len(hexes)>44,f'hex asset absent from manifest {p.name}')
systems=text('systems.js')
ok("WWN:{" in systems and "corpusReady:true" in systems,'WWN rules not ready')
ok("SWN:{" in systems and systems.count('corpusReady:true')>=2,'SWN rules not ready')
ok("CWN:{" in systems and "corpusReady:false" in systems,'CWN fail-closed profile missing')
ok("AWN:{" in systems and systems.count('corpusReady:false')>=2,'AWN fail-closed profile missing')
runtime=text('xwn4-runtime.js');barbara=text('barbara-browser.js');gm=text('gmBridge.js')
ok("a31fdb9f9e361fc81b6a5f25c7646450311d0ce3" in runtime and "a31fdb9f9e361fc81b6a5f25c7646450311d0ce3" in barbara,'Barbara pin mismatch')
for invariant in ['campaign_opening','first_arrival','changed_return','player_knows_only_experienced_world','dramatize_world_instead_of_reporting_it']:
    ok(invariant in barbara,f'Barbara narrative invariant missing {invariant}')
ok('BarbaraBrowser.validate' in gm and 'BarbaraBrowser.commitExperience' in gm,'Gemini bypasses Barbara validator')
ok('indexedDB' in text('local-audio-library.js'),'local audio persistence missing')
ok('indexedDB' in text('snapshot-store.js'),'snapshot persistence missing')
ui=text('xwn4-ui.js')
for feature in ['Exportar ficha JSON','Importar ficha JSON','Salvar snapshot local','DADOS VIRTUAIS','MÚSICA / AMBIÊNCIA LOCAL','COMBATE TÁTICO SWN']:
    ok(feature in ui,f'parity UI missing {feature}')
for bad in ['\x08moral','\x08ataque','\x08acertar']:
    ok(bad not in text('engine.js'),'control-character regex regression returned')
ok('xwn4-migration.js' in sw,'save migration not cached')
print(f'XWN4 static parity audit OK: {checks} checks, {len(hexes)} WWN hex assets')
