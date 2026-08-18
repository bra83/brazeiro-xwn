(() => {
  'use strict';
  const E=window.XWNEngine,A=window.AudioEngineV2,RULE_INDEX=window.XWN_RULE_INDEX||[],HEX_LIBRARY=window.XWN_HEX_LIBRARY||[],GM=window.XWNGMBridge;
  let state,mapScale=1,editingTokenEntity=null,lastGeminiBundle=null,actionRevision=0;
  const $=id=>document.getElementById(id);
  const OLD_KEYS=['braseiro_xwn_wwn_v150','braseiro_xwn_wwn_v100'];
  const AUDIO_KEY='braseiro_xwn_audio_v2';
  const SHARED_CACHE='braseiro-shares-v1',SHARED_KEY='./__shared_scene_image__';
  const themeMeta=$('themeColorMeta');

  function escapeHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function initials(name){return String(name||'?').split(/\s+/).slice(0,2).map(x=>x[0]||'').join('').toUpperCase()}
  function currentHex(){return state.hexes[E.key(state.current.q,state.current.r)]}
  function selectedHex(){return state.hexes[E.key(state.selected.q,state.selected.r)]}
  function saveState(){localStorage.setItem(E.STORAGE_KEY,E.exportState(state))}
  function loadState(){
    let raw=localStorage.getItem(E.STORAGE_KEY), migratedFromOld=false;
    if(!raw)for(const k of OLD_KEYS){raw=localStorage.getItem(k);if(raw){migratedFromOld=true;break}}
    try{state=raw?E.importState(raw):E.makeInitialState()}catch(e){console.warn(e);state=E.makeInitialState()}
    state.visual ||= {tokens:{},sceneHistory:[],sceneImages:[]}; state.visual.sceneImages ||= [];
    if(migratedFromOld){
      const cur=currentHex();
      state.sceneTitle=cur?.poi&&cur.explored?cur.poi.name:'A estrada para fora de Dorsa';
      state.narrative=E.sceneForHex(cur,state,cur?.key==='0,0'?'observe':'arrival');
      state.lastMechanics='';
      saveState();
    }
  }

  function periodTheme(){
    const p=E.periodOfDay(state.campaign.hour);document.body.dataset.period=p;
    const colors={morning:'#8fc7e8',afternoon:'#1f5578',night:'#2e3439',dawn:'#05080a'};if(themeMeta)themeMeta.content=colors[p];
  }

  function hexPixel(q,r){const size=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--hexW'))/2;const h=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--hexH'));const x=size*1.5*q;const y=h*(r+q/2);return{x:410+x-size,y:360+y-h/2}}
  function entityTokenContent(id,name){const token=state.visual?.tokens?.[id];return token?.dataUrl?`<img src="${token.dataUrl}" alt="${escapeHtml(name)}">`:`<span>${initials(name)}</span>`}
  function tokenHtml(id,name,cls='entity-token'){return `<button class="${cls}" data-entity="${escapeHtml(id)}" title="${escapeHtml(name)}">${entityTokenContent(id,name)}</button>`}

  function renderEntityStrip(){
    const entities=E.activeVisualEntities(state);$('entityStrip').innerHTML=entities.map(e=>tokenHtml(e.id,e.name)).join('');
    $('entityStrip').querySelectorAll('[data-entity]').forEach(b=>b.addEventListener('click',()=>openTokenDialog(b.dataset.entity)));
  }

  function renderMap(){
    const map=$('hexMap');map.innerHTML='';
    const currentKey=E.key(state.current.q,state.current.r);
    Object.values(state.hexes).forEach(hex=>{
      const p=hexPixel(hex.q,hex.r),t=E.TERRAIN[hex.terrain];
      const b=document.createElement('button');b.className=`hex${hex.discovered?'':' fog'}${hex.key===E.key(state.selected.q,state.selected.r)?' selected':''}${hex.key===currentKey?' current':''}`;b.style.left=`${p.x}px`;b.style.top=`${p.y}px`;b.dataset.q=hex.q;b.dataset.r=hex.r;
      if(hex.discovered){b.style.backgroundImage=`url('${hex.tile||t.tile}')`;
        const visibleRoadDirs=E.roadConnections(state,hex).filter(dir=>{const n=E.AXIAL_DIRS[dir],other=state.hexes[E.key(hex.q+n.q,hex.r+n.r)];return !!other?.discovered});
        const isRoadEndpoint=!!(hex.explored&&hex.poi&&['settlement','farm','site','ruin','fort'].includes(hex.poi.kind));
        if(visibleRoadDirs.length>=2||(visibleRoadDirs.length===1&&isRoadEndpoint)) visibleRoadDirs.forEach(dir=>{const seg=document.createElement('i');seg.className=`road-segment d${dir}`;b.appendChild(seg)});
        if(hex.explored&&hex.poi){const m=document.createElement('span');m.className='poi-marker';if(hex.poi.image){const img=document.createElement('img');img.src=hex.poi.image;m.appendChild(img)}else m.textContent=hex.poi.icon||'•';b.appendChild(m)}
        if(hex.explored&&hex.poi){const label=document.createElement('span');label.className='hex-label';label.textContent=hex.poi.name;b.appendChild(label)}
        if(hex.key===currentKey){const m=document.createElement('span');m.className='map-player-token';m.setAttribute('aria-label',`Posição de ${state.player.name}`);m.title=`Posição de ${state.player.name}`;b.appendChild(m)}
      }
      b.addEventListener('click',()=>{E.selectHex(state,hex.q,hex.r);renderMapMeta();renderMap()});map.appendChild(b);
    });
    document.documentElement.style.setProperty('--mapScale',mapScale);
  }

  function renderMapMeta(){
    const h=selectedHex(),cur=currentHex(),adj=E.isAdjacent(state.current,state.selected);
    $('hexTitle').textContent=cur.explored&&cur.poi?cur.poi.name:`Hex ${cur.key}`;
    $('selectedLabel').textContent=h.discovered?(h.explored&&h.poi?h.poi.name:`Hex ${h.key}`):'Território sob névoa';
    $('terrainLabel').textContent=h.discovered?E.TERRAIN[h.terrain].label:'Terreno desconhecido';
    $('travelBtn').disabled=!adj||!!state.combat;$('travelBtn').textContent=adj?'Viajar':(h.key===cur.key?'Você está aqui':'Não adjacente');$('exploreBtn').disabled=!!state.combat;
  }

  function renderMeta(){periodTheme();$('campaignName').textContent=state.campaign.name;$('dayLabel').textContent=`Dia ${state.campaign.day}`;$('timeLabel').textContent=`${String(state.campaign.hour).padStart(2,'0')}:00`;$('weatherLabel').textContent=state.campaign.weather;$('seasonLabel').textContent=state.campaign.season;renderMapMeta();A.syncWorldState({terrain:E.TERRAIN[currentHex().terrain].label,weather:state.campaign.weather})}

  function renderStory(){
    $('sceneTitle').textContent=state.sceneTitle||'Cena atual';const feed=$('storyFeed');feed.innerHTML='';(state.narrative||[]).forEach(text=>{const p=document.createElement('p');p.textContent=text;if(/^\s*[“\"]/.test(text)||/^[^:]{2,30}:\s*[“\"]/.test(text))p.classList.add('dialogue');feed.appendChild(p)});
    if(state.lastMechanics){$('mechanicsDetails').hidden=false;$('mechanicsText').textContent=state.lastMechanics}else $('mechanicsDetails').hidden=true;renderSuggestions();renderCombat();renderSceneImage();
  }

  function renderSuggestions(){
    const cur=currentHex(),present=E.npcsAt(state,cur.key);let list=[];
    if(state.combat)list=['Ataco com a espada','Tento romper contato','Procuro cobertura para fugir'];
    else if(state.encounter)list=[`Converso com ${state.encounter.enemy.name}`,`Mantenho distância e observo ${state.encounter.enemy.name}`,'Recuo sem provocar'];
    else if(present.length)list=[`Converso com ${present[0].name}`,cur.explored?'Procuro sinais de mudança':'Exploro o lugar','Observo sem tocar em nada'];
    else list=[cur.explored?'Procuro sinais recentes':'Exploro o lugar','Observo a área','Sigo pela rota mais segura'];
    $('suggestions').innerHTML='';list.slice(0,3).forEach(text=>{const b=document.createElement('button');b.textContent=text;b.onclick=()=>{$('actionInput').value=text;$('actionInput').focus()};$('suggestions').appendChild(b)});
  }
  function renderCombat(){const box=$('combatBox');if(!state.combat){box.hidden=true;return}box.hidden=false;const e=state.combat.enemy;$('enemyName').textContent=e.name;$('enemyHpText').textContent=`${e.hp} PV • AC ${e.ac}`;const max=E.ENEMIES[e.id]?.hp||Math.max(1,e.hp);$('enemyHpBar').style.width=`${Math.max(0,Math.min(100,e.hp/max*100))}%`}

  function renderCharacter(){const p=state.player;$('charName').textContent=p.name;$('charClass').textContent=`${p.className} ${p.level}`;$('hpText').textContent=`${p.hp}/${p.maxHp}`;$('acText').textContent=p.ac;$('abText').textContent=p.attackBonus>=0?`+${p.attackBonus}`:p.attackBonus;$('strainText').textContent=p.systemStrain;$('conditionText').textContent=p.condition||'Apto';$('playerHpBar').style.width=`${Math.max(0,p.hp/p.maxHp*100)}%`;$('characterBigToken').innerHTML=entityTokenContent('player',p.name);
    const names={str:'FOR',dex:'DES',con:'CON',int:'INT',wis:'SAB',cha:'CAR'};$('attrGrid').innerHTML=Object.entries(p.attrs).map(([k,v])=>`<div><span>${names[k]}</span><strong>${v} (${p.mods[k]>=0?'+':''}${p.mods[k]})</strong></div>`).join('');$('skillsGrid').innerHTML=Object.entries(p.skills).filter(([,v])=>v>=0).map(([k,v])=>`<span class="skill">${escapeHtml(k)} ${v}</span>`).join('');$('inventoryList').innerHTML=p.inventory.map(x=>`<span class="item">${escapeHtml(x)}</span>`).join('')}

  function renderWorld(){
    const known=state.factions.filter(f=>f.known!==false);$('factionList').innerHTML=known.map(f=>`<div class="faction-card"><b>${escapeHtml(f.name)}</b><small>${escapeHtml(f.goal)}</small><div class="faction-stats"><span>Força ${f.force||0}</span><span>Astúcia ${f.cunning||0}</span><span>Riqueza ${f.wealth||0}</span></div><div class="progress"><i style="width:${Math.min(100,(f.progress||0)/(f.clock||6)*100)}%"></i></div></div>`).join('');
    const cur=currentHex();$('npcWorldList').innerHTML=Object.values(state.npcs).map(n=>{const loc=n.location===cur.key?(cur.poi?.name||`hex ${cur.key}`):(n.lastSeenDay?`última vez visto: dia ${n.lastSeenDay}`:'localização atual desconhecida');return `<div class="npc-world-card"><div class="mini-token">${tokenHtml(n.id,n.name)}</div><div><b>${escapeHtml(n.name)}</b><small>${escapeHtml(n.role)} • ${escapeHtml(loc)}</small></div></div>`}).join('');$('npcWorldList').querySelectorAll('[data-entity]').forEach(b=>b.onclick=()=>openTokenDialog(b.dataset.entity));
    const clocks=(state.world.clocks||[]).filter(c=>c.public);$('worldClockList').innerHTML=clocks.map(c=>`<div class="clock-row"><span>${escapeHtml(c.label)}</span><span class="clock-pips">${Array.from({length:c.max},(_,i)=>`<i class="${i<c.value?'on':''}"></i>`).join('')}</span></div>`).join('')||'<p class="muted-note">Nenhum relógio público.</p>';
    $('worldEventList').innerHTML=(state.world.publicEvents||[]).slice(0,10).map(e=>`<div class="world-event"><b>Dia ${e.day}</b> ${escapeHtml(e.text)}</div>`).join('')||'<p class="muted-note">Nenhuma mudança pública chegou até o personagem.</p>';
  }
  function renderJournal(){$('journalList').innerHTML=(state.journal||[]).map(j=>`<article class="journal-entry"><small>${escapeHtml(j.when)} • ${escapeHtml(j.type)}</small><p>${escapeHtml(j.text)}</p></article>`).join('')}
  function renderHexLibrary(){$('hexLibraryGrid').innerHTML=HEX_LIBRARY.map(x=>`<div class="hex-library-item"><img src="assets/hex_full/${escapeHtml(x.id)}.png" alt=""><span>${escapeHtml(x.terrain)} · ${escapeHtml(x.variant)}</span></div>`).join('')}
  function renderRulesStatus(){$('ruleIndexStatus').textContent=`Índice offline: ${RULE_INDEX.length} páginas mecânicas do WWN SRD.`}

  function renderSceneImage(){const latest=(state.visual.sceneImages||[])[0],frame=$('sceneImageFrame');if(!latest){frame.hidden=true;return}frame.hidden=false;$('sceneImage').src=latest.dataUrl;$('sceneImageCaption').textContent=latest.caption||state.sceneTitle||'Imagem da cena'}
  async function fileToSceneImage(file,caption='Imagem compartilhada do Gemini'){if(!file)return;const dataUrl=await fileToDataUrl(file);state.visual.sceneImages.unshift({id:`img_${Date.now()}`,dataUrl,caption,day:state.campaign.day,hour:state.campaign.hour,hex:currentHex().key});state.visual.sceneImages=state.visual.sceneImages.slice(0,12);saveState();renderSceneImage()}
  async function consumeSharedImage(){try{if(!('caches'in window))return;const c=await caches.open(SHARED_CACHE),r=await c.match(SHARED_KEY);if(!r)return;const blob=await r.blob();if(blob.size){const file=new File([blob],`gemini_${Date.now()}.${(blob.type.split('/')[1]||'png')}`,{type:blob.type||'image/png'});await fileToSceneImage(file,'Imagem compartilhada para a cena atual')}await c.delete(SHARED_KEY);history.replaceState({},'',location.pathname)}catch(e){console.warn('share target',e)}}

  function renderAll(persist=true){renderMeta();renderEntityStrip();renderMap();renderStory();renderCharacter();renderWorld();renderJournal();renderRulesStatus();renderSceneImage();if(persist)saveState()}

  async function maybeRefineNarration(scaffold,playerAction,revision){
    if(!GM?.enabled())return;const cur=currentHex(),present=E.npcsAt(state,cur.key);try{const out=await GM.refineNarrative({location:cur.explored&&cur.poi?cur.poi.name:`hex ${cur.key}`,terrain:E.TERRAIN[cur.terrain].label,day:`Dia ${state.campaign.day}`,time:`${String(state.campaign.hour).padStart(2,'0')}:00`,period:E.periodOfDay(state.campaign.hour),weather:state.campaign.weather,action:playerAction,npcs:present.map(n=>`${n.name} (${n.role}; ${n.activity||'ocupado'})`).join('; '),poi:cur.explored&&cur.poi?`${cur.poi.name}: ${cur.poi.summary}`:'nenhum confirmado',mechanics:state.lastMechanics,scaffold});if(revision!==actionRevision||!out?.paragraphs?.length)return;state.narrative=out.paragraphs;state.gmModel=out.model;saveState();renderStory()}catch(e){console.warn('Gemini narrador indisponível',e)}}

  function handleResult(result,playerAction=''){
    if(!result)return;if(result.narrative)state.narrative=result.narrative;if(typeof result.mechanics==='string')state.lastMechanics=result.mechanics;const rev=++actionRevision;const scaffold=[...(state.narrative||[])];renderAll(true);$('storyFeed').scrollTop=0;void maybeRefineNarration(scaffold,playerAction,rev);
  }

  function queryProtected(inputId,answerId){const q=$(inputId).value.trim();if(!q)return;const before=JSON.stringify({day:state.campaign.day,hour:state.campaign.hour,current:state.current,journal:state.journal.length,world:state.world?.lastProcessedDay,narrative:state.narrative,combat:state.combat});const ans=E.queryRulesIndexed(state,q,RULE_INDEX);const after=JSON.stringify({day:state.campaign.day,hour:state.campaign.hour,current:state.current,journal:state.journal.length,world:state.world?.lastProcessedDay,narrative:state.narrative,combat:state.combat});$(answerId).textContent=ans+(before===after?'\n\n✓ Cena preservada: tempo, posição, narrativa, NPCs e mundo vivo não foram alterados.':'\n\n⚠ Auditoria detectou mutação indevida.');$(inputId).value='';saveState()}

  function fileToDataUrl(file){return new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result);r.onerror=rej;r.readAsDataURL(file)})}
  function loadImage(src){return new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=rej;i.src=src})}
  async function imageFileToToken(file){const dataUrl=await fileToDataUrl(file),img=await loadImage(dataUrl),size=320,c=document.createElement('canvas');c.width=c.height=size;const x=c.getContext('2d'),scale=Math.max(size/img.width,size/img.height),w=img.width*scale,h=img.height*scale;x.drawImage(img,(size-w)/2,(size-h)/2,w,h);return{dataUrl:c.toDataURL('image/jpeg',.88),fileName:file.name,mimeType:'image/jpeg',assignedAt:new Date().toISOString()}}
  function openTokenDialog(id){editingTokenEntity=id;const e=E.entitySnapshot(state,id);if(!e)return;$('tokenDialogTitle').textContent=`${e.name} • ${e.role}`;$('tokenDescriptor').value=e.descriptor||'';$('tokenPreview').innerHTML=tokenHtml(id,e.name);$('tokenDialog').showModal()}

  function makeGeminiBundle(showDialog=true){
    lastGeminiBundle=E.makeGeminiImageBundle(state);const visible=E.activeVisualEntities(state);const continuity=visible.map(e=>`- ${e.name}: ${e.descriptor||e.role}`).join('\n');
    lastGeminiBundle.prompt=`${lastGeminiBundle.prompt}\n\nCONTINUIDADE VISUAL OBRIGATÓRIA — use os tokens anexados como referência direta quando disponíveis. Preserve rosto, idade aparente, cabelo, roupa-chave, cicatrizes, porte, proporções e cores dos personagens:\n${continuity}\n\nA imagem deve representar SOMENTE elementos perceptíveis desta cena. Não mostrar HUD, texto, hexágonos ou interface. Não revelar território sob névoa, segredos do Mestre nem personagens ausentes.`;
    $('geminiPromptText').value=lastGeminiBundle.prompt;$('geminiReferenceList').innerHTML=lastGeminiBundle.references.length?lastGeminiBundle.references.map(r=>`<div class="gemini-ref"><img src="${r.dataUrl}" alt=""><div><b>${escapeHtml(r.name)}</b><small>${escapeHtml(r.fileName)}</small></div></div>`).join(''):'<p class="muted-note">Sem token personalizado; serão usadas as descrições canônicas.</p>';
    if(showDialog)$('geminiDialog').showModal();return lastGeminiBundle;
  }
  function dataUrlToFile(ref){try{const [head,data]=String(ref.dataUrl||'').split(',');const mime=(head.match(/data:([^;]+)/)||[])[1]||ref.mimeType||'image/jpeg';const bin=atob(data||''),u8=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u8[i]=bin.charCodeAt(i);return new File([u8],ref.fileName||`${ref.entityId||'token'}.jpg`,{type:mime})}catch(_){return null}}
  function geminiAndroidIntent(prompt){const fallback=encodeURIComponent('https://gemini.google.com/app');const text=encodeURIComponent(prompt);const subject=encodeURIComponent('Braseiro XWN — imagem da cena');return `intent:#Intent;action=android.intent.action.SEND;category=android.intent.category.DEFAULT;type=text/plain;package=com.google.android.apps.bard;S.android.intent.extra.TEXT=${text};S.android.intent.extra.SUBJECT=${subject};S.browser_fallback_url=${fallback};end`}
  async function launchGeminiForImage(){
    const bundle=makeGeminiBundle(false),prompt=bundle.prompt,files=(bundle.references||[]).map(dataUrlToFile).filter(Boolean).slice(0,4);try{await navigator.clipboard?.writeText(prompt)}catch(_){}
    // Quando há tokens, prioriza o Share Sheet: assim o Gemini recebe também as imagens de referência, não apenas o texto.
    if(files.length&&navigator.share){try{const payload={title:'Braseiro XWN — imagem da cena',text:prompt,files};if(!navigator.canShare||navigator.canShare(payload)){await navigator.share(payload);return}}catch(e){if(e?.name==='AbortError')return}}
    // Android/Chrome: tenta abrir o app Gemini já com o ACTION_SEND textual. O prompt também fica copiado como fallback.
    if(/Android/i.test(navigator.userAgent)){try{location.href=geminiAndroidIntent(prompt);return}catch(_){}}
    if(navigator.share){try{await navigator.share({title:'Braseiro XWN — imagem da cena',text:prompt});return}catch(e){if(e?.name==='AbortError')return}}
    window.open('https://gemini.google.com/app','_blank','noopener');$('geminiDialog').showModal();
  }
  async function sharePrompt(){
    const bundle=lastGeminiBundle||makeGeminiBundle(false),prompt=bundle.prompt,files=(bundle.references||[]).map(dataUrlToFile).filter(Boolean).slice(0,4);try{await navigator.clipboard?.writeText(prompt)}catch(_){}
    if(navigator.share){try{const payload={title:'Braseiro XWN — imagem da cena',text:prompt};if(files.length)payload.files=files;if(!navigator.canShare||navigator.canShare(payload)){await navigator.share(payload);return}}catch(e){if(e?.name==='AbortError')return}}
    if(/Android/i.test(navigator.userAgent)){location.href=geminiAndroidIntent(prompt);return}window.open('https://gemini.google.com/app','_blank','noopener');
  }

  function bindSpeech(id,targetId,statusId){const b=$(id),target=$(targetId),status=$(statusId);if(!A.supportsSTT()){b.title='Fala→texto indisponível neste navegador';b.disabled=true;return}b.onclick=()=>{if(A.state.activeRecognitionTarget===target)A.stopListening();else A.listenTo(target)};A.on(ev=>{if(ev.target!==target)return;if(ev.type==='listenstart'){b.classList.add('listening');status.textContent='Ouvindo…'}if(ev.type==='listenend'){b.classList.remove('listening');status.textContent='Transcrição pronta para revisão.'}if(ev.type==='listenerror'){b.classList.remove('listening');status.textContent=`Microfone: ${ev.error}`}})}
  function loadAudio(){let cfg={};try{cfg=JSON.parse(localStorage.getItem(AUDIO_KEY)||'{}')}catch(_){}const provider=cfg.voiceProvider||(GM?.getKey()?'gemini':'browser');A.configure({rate:cfg.rate??1.08,volume:cfg.volume??1,ambientEnabled:cfg.ambientEnabled??false,ambientVolume:cfg.ambientVolume??.12,voiceProvider:provider});$('voiceProvider').value=A.state.voiceProvider;$('ttsRate').value=A.state.rate;$('ttsRateValue').value=`${Number(A.state.rate).toFixed(2)}×`;$('ttsVolume').value=A.state.volume;$('ttsVolumeValue').value=`${Math.round(A.state.volume*100)}%`;$('ambientToggle').checked=A.state.ambientEnabled;$('ambientVolume').value=A.state.ambientVolume;$('ambientVolumeValue').value=`${Math.round(A.state.ambientVolume*100)}%`}
  function saveAudio(){localStorage.setItem(AUDIO_KEY,JSON.stringify({rate:A.state.rate,volume:A.state.volume,ambientEnabled:A.state.ambientEnabled,ambientVolume:A.state.ambientVolume,voiceProvider:A.state.voiceProvider}))}

  function showPage(name){document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active',p.dataset.page===name));document.querySelectorAll('.bottom-nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===name));window.scrollTo({top:0,behavior:'smooth'})}
  function openRules(){const d=$('rulesDrawer');d.classList.add('open');d.setAttribute('aria-hidden','false');$('drawerScrim').hidden=false;$('drawerRulesInput').focus()}function closeRules(){const d=$('rulesDrawer');d.classList.remove('open');d.setAttribute('aria-hidden','true');$('drawerScrim').hidden=true}

  // Live play actions
  $('travelBtn').onclick=()=>handleResult(E.travelTo(state,state.selected.q,state.selected.r),'Viajar para o hex selecionado');$('exploreBtn').onclick=()=>handleResult(E.exploreCurrentHex(state),'Explorar o hex atual');
  $('sendAction').onclick=()=>{const text=$('actionInput').value.trim();if(!text)return;$('actionInput').value='';handleResult(E.performAction(state,text),text)};$('actionInput').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('sendAction').click()}});
  $('attackBtn').onclick=()=>handleResult(E.playerAttack(state),'Atacar');$('fleeBtn').onclick=()=>handleResult(E.fleeCombat(state),'Fugir');
  $('zoomIn').onclick=()=>{mapScale=Math.min(1.65,mapScale+.1);renderMap()};$('zoomOut').onclick=()=>{mapScale=Math.max(.58,mapScale-.1);renderMap()};$('zoomReset').onclick=()=>{mapScale=1;renderMap();$('mapViewport').scrollTo({left:150,top:100,behavior:'smooth'})};
  $('ttsBtn').onclick=()=>A.speak((state.narrative||[]).join(' '));$('ttsStopBtn').onclick=()=>A.stopSpeech();

  // Rules
  $('sendRule').onclick=()=>queryProtected('rulesInput','rulesAnswer');$('drawerSendRule').onclick=()=>queryProtected('drawerRulesInput','drawerRulesAnswer');['rulesInput','drawerRulesInput'].forEach(id=>$(id).addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();id==='rulesInput'?$('sendRule').click():$('drawerSendRule').click()}}));$('openRulesDrawer').onclick=openRules;$('closeRulesDrawer').onclick=closeRules;$('drawerScrim').onclick=closeRules;

  // Tokens + image flow
  $('tokenFileInput').onchange=async e=>{const f=e.target.files[0];if(!f||!editingTokenEntity)return;E.setEntityToken(state,editingTokenEntity,await imageFileToToken(f));saveState();renderAll(false);const ent=E.entitySnapshot(state,editingTokenEntity);$('tokenPreview').innerHTML=tokenHtml(editingTokenEntity,ent.name);e.target.value=''};
  $('saveDescriptorBtn').onclick=()=>{if(!editingTokenEntity)return;const v=$('tokenDescriptor').value.trim();if(editingTokenEntity==='player')state.player.visualDescriptor=v;else if(state.npcs[editingTokenEntity])state.npcs[editingTokenEntity].visualDescriptor=v;saveState();renderEntityStrip()};$('clearTokenBtn').onclick=()=>{if(!editingTokenEntity)return;E.setEntityToken(state,editingTokenEntity,null);saveState();renderAll(false)};
  $('geminiLaunchBtn').onclick=launchGeminiForImage;$('shareGeminiPrompt').onclick=sharePrompt;$('copyGeminiPrompt').onclick=async()=>{await navigator.clipboard?.writeText($('geminiPromptText').value);$('copyGeminiPrompt').textContent='Copiado ✓';setTimeout(()=>$('copyGeminiPrompt').textContent='Copiar prompt',1200)};$('sceneImageInput').onchange=async e=>{if(e.target.files[0])await fileToSceneImage(e.target.files[0]);e.target.value=''};$('clearSceneImage').onclick=()=>{state.visual.sceneImages.shift();saveState();renderSceneImage()};

  // Settings / audio / persistence
  document.querySelectorAll('.bottom-nav button').forEach(b=>b.onclick=()=>showPage(b.dataset.page));
  $('exportBtn').onclick=()=>{const a=document.createElement('a'),blob=new Blob([E.exportState(state)],{type:'application/json'});a.href=URL.createObjectURL(blob);a.download=`braseiro_xwn_3_${Date.now()}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500)};$('importInput').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{state=E.importState(await f.text());renderAll(true)}catch(err){alert(`JSON inválido: ${err.message}`)}e.target.value=''};$('resetBtn').onclick=()=>{if(confirm('Reiniciar a campanha?')){localStorage.removeItem(E.STORAGE_KEY);OLD_KEYS.forEach(k=>localStorage.removeItem(k));state=E.makeInitialState();renderAll(true);showPage('play')}};
  $('geminiApiKey').value=GM?.getKey()||'';$('gmAiToggle').checked=GM?.enabled()||false;$('geminiApiKey').onchange=e=>{GM?.setKey(e.target.value);$('gmAiToggle').checked=GM?.enabled()||false};$('gmAiToggle').onchange=e=>{GM?.setEnabled(e.target.checked);if(e.target.checked&&!GM?.getKey()){$('geminiApiKey').focus();e.target.checked=false}};
  loadAudio();$('voiceProvider').onchange=e=>{A.configure({voiceProvider:e.target.value});saveAudio();$('audioStatus').textContent=e.target.value==='gemini'?'Charon pronto':'Voz local pronta'};$('ttsRate').oninput=e=>{A.configure({rate:+e.target.value});$('ttsRateValue').value=`${(+e.target.value).toFixed(2)}×`;saveAudio()};$('ttsVolume').oninput=e=>{A.configure({volume:+e.target.value});$('ttsVolumeValue').value=`${Math.round(+e.target.value*100)}%`;saveAudio()};$('ambientToggle').onchange=e=>{A.configure({ambientEnabled:e.target.checked});A.syncWorldState({terrain:E.TERRAIN[currentHex().terrain].label,weather:state.campaign.weather});saveAudio()};$('ambientVolume').oninput=e=>{A.configure({ambientVolume:+e.target.value});$('ambientVolumeValue').value=`${Math.round(+e.target.value*100)}%`;saveAudio()};A.on(ev=>{if(ev.type==='speechstart')$('audioStatus').textContent=ev.backend?`Falando • ${ev.backend}`:'Falando';if(ev.type==='ttsready')$('audioStatus').textContent=`Charon pronto • ${ev.model} • ${ev.latencyMs} ms`;if(ev.type==='ttscache')$('audioStatus').textContent='Charon • cache local';if(ev.type==='error')$('audioStatus').textContent=`Áudio: ${ev.error}`;if(ev.type==='speechend'||ev.type==='listenend')$('audioStatus').textContent='Pronto';if(ev.type==='listenstart')$('audioStatus').textContent='Ouvindo'});
  bindSpeech('actionMic','actionInput','actionSpeechStatus');bindSpeech('rulesMic','rulesInput','rulesSpeechStatus');bindSpeech('drawerRulesMic','drawerRulesInput','drawerSpeechStatus');

  loadState();renderHexLibrary();renderAll(false);requestAnimationFrame(()=>$('mapViewport').scrollTo({left:145,top:105}));
  if('serviceWorker'in navigator&&/^https?:$/.test(location.protocol))navigator.serviceWorker.register('./sw.js').then(()=>consumeSharedImage()).catch(console.warn);else void consumeSharedImage();
})();
