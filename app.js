(() => {
  'use strict';
  const E = window.XWNEngine;
  const A = window.AudioEngineV2;
  const RULE_INDEX = window.XWN_RULE_INDEX || [];
  let state;
  let mapScale = 1;
  let editingTokenEntity = null;
  let lastGeminiBundle = null;
  const $ = id => document.getElementById(id);
  const OLD_STORAGE_KEYS = ['braseiro_xwn_wwn_v100'];
  const AUDIO_SETTINGS_KEY = 'braseiro_xwn_audio_v2';

  function loadState() {
    try {
      let raw = localStorage.getItem(E.STORAGE_KEY);
      if (!raw) {
        for (const oldKey of OLD_STORAGE_KEYS) {
          raw = localStorage.getItem(oldKey);
          if (raw) break;
        }
      }
      state = raw ? E.importState(raw) : E.makeInitialState();
    } catch (err) {
      console.warn('Save inválido; criando campanha nova.', err);
      state = E.makeInitialState();
    }
  }

  function saveState() {
    localStorage.setItem(E.STORAGE_KEY, E.exportState(state));
  }

  function loadAudioSettings() {
    let cfg = {};
    try { cfg = JSON.parse(localStorage.getItem(AUDIO_SETTINGS_KEY) || '{}'); } catch (_) {}
    A.configure({ rate: cfg.rate ?? 1.18, volume: cfg.volume ?? 1, ambientEnabled: cfg.ambientEnabled ?? false, ambientVolume: cfg.ambientVolume ?? .12 });
    $('ttsRate').value = A.state.rate; $('ttsRateValue').value = `${Number(A.state.rate).toFixed(2)}×`;
    $('ttsVolume').value = A.state.volume; $('ttsVolumeValue').value = `${Math.round(A.state.volume*100)}%`;
    $('ambientToggle').checked = A.state.ambientEnabled;
    $('ambientVolume').value = A.state.ambientVolume; $('ambientVolumeValue').value = `${Math.round(A.state.ambientVolume*100)}%`;
  }

  function persistAudioSettings() {
    localStorage.setItem(AUDIO_SETTINGS_KEY, JSON.stringify({rate:A.state.rate,volume:A.state.volume,ambientEnabled:A.state.ambientEnabled,ambientVolume:A.state.ambientVolume}));
  }

  function hexPixel(q, r) {
    const size = 56;
    const x = size * 1.5 * q;
    const y = size * Math.sqrt(3) * (r + q / 2);
    return { x: 325 + x - 56, y: 285 + y - 48.5 };
  }

  function currentHex() { return state.hexes[E.key(state.current.q,state.current.r)]; }

  function renderMap() {
    const map = $('hexMap');
    map.innerHTML = '';
    Object.values(state.hexes).forEach(hex => {
      const t = E.TERRAIN[hex.terrain];
      const p = hexPixel(hex.q, hex.r);
      const btn = document.createElement('button');
      btn.className = `hex terrain-${t.css}${hex.discovered ? '' : ' fog'}${hex.q === state.selected.q && hex.r === state.selected.r ? ' selected' : ''}${hex.q === state.current.q && hex.r === state.current.r ? ' current' : ''}`;
      btn.style.left = `${p.x}px`; btn.style.top = `${p.y}px`;
      btn.dataset.q = hex.q; btn.dataset.r = hex.r;
      const tile = hex.tile || t.tile;
      if (hex.discovered && tile) { btn.style.backgroundImage = `url('${tile}')`; btn.classList.add('has-tile'); }
      if (hex.road && hex.discovered) {
        const road = document.createElement('span'); road.className = 'road-stroke'; btn.appendChild(road);
      }
      if (hex.discovered && hex.explored && hex.poi) {
        const marker = document.createElement('span'); marker.className = 'poi-marker';
        if (hex.poi.image) { const img = document.createElement('img'); img.src = hex.poi.image; img.alt = ''; marker.appendChild(img); }
        else marker.textContent = hex.poi.icon || '•';
        btn.appendChild(marker);
      }
      if (hex.discovered) {
        const label = document.createElement('span'); label.className = 'hex-label';
        label.textContent = hex.explored && hex.poi ? hex.poi.name : `${hex.q},${hex.r}`;
        btn.appendChild(label);
      }
      btn.addEventListener('click', () => { E.selectHex(state, hex.q, hex.r); renderAll(false); });
      map.appendChild(btn);
    });
    document.documentElement.style.setProperty('--mapScale', mapScale);
  }

  function renderMeta() {
    $('campaignName').textContent = state.campaign.name;
    $('dayLabel').textContent = `Dia ${state.campaign.day}`;
    $('timeLabel').textContent = `${String(state.campaign.hour).padStart(2,'0')}:00`;
    $('weatherLabel').textContent = state.campaign.weather;
    $('seasonLabel').textContent = state.campaign.season;
    const h = state.hexes[E.key(state.selected.q, state.selected.r)];
    const current = currentHex();
    $('hexTitle').textContent = current.explored && current.poi ? current.poi.name : `Hex ${current.key}`;
    $('selectedLabel').textContent = h.discovered ? (h.explored && h.poi ? h.poi.name : `Hex ${h.key}`) : 'Não mapeado';
    $('terrainLabel').textContent = h.discovered ? E.TERRAIN[h.terrain].label : 'Desconhecido';
    $('discoveryLabel').textContent = h.explored ? 'Explorado' : h.discovered ? 'Revelado' : 'Névoa';
    const adjacent = E.isAdjacent(state.current, state.selected);
    $('travelBtn').disabled = !adjacent || !!state.combat;
    $('travelBtn').textContent = adjacent ? 'Viajar para o hex' : (h.key === current.key ? 'Você está aqui' : 'Selecione um hex adjacente');
    $('exploreBtn').disabled = !!state.combat;
    A.syncWorldState({terrain:E.TERRAIN[current.terrain].label,weather:state.campaign.weather});
  }

  function renderStory() {
    const feed = $('storyFeed'); feed.innerHTML = '';
    (state.narrative || []).forEach(text => { const p = document.createElement('p'); p.textContent = text; feed.appendChild(p); });
    if (state.lastMechanics) { $('mechanicsBox').hidden = false; $('mechanicsText').textContent = state.lastMechanics; }
    else $('mechanicsBox').hidden = true;
    renderSuggestions();
    renderCombat();
  }

  function renderSuggestions() {
    const s = $('suggestions'); s.innerHTML = '';
    const current = currentHex();
    let list = ['Observo a área', 'Procuro rastros', 'Forrageio por comida'];
    const present = E.npcsAt(state,current.key);
    if (present.length) list = [...present.slice(0,2).map(n=>`Converso com ${n.name}`), 'Observo a área', current.explored ? 'Procuro sinais recentes' : 'Exploro o local'];
    if (state.combat) list = ['Ataco com a espada', 'Tento fugir'];
    list.slice(0,5).forEach(text => {
      const b = document.createElement('button'); b.textContent = text;
      b.addEventListener('click', () => { $('actionInput').value = text; $('actionInput').focus(); }); s.appendChild(b);
    });
  }

  function renderCombat() {
    const box = $('combatBox');
    if (!state.combat) { box.hidden = true; return; }
    box.hidden = false;
    const e = state.combat.enemy;
    $('enemyName').textContent = e.name;
    $('enemyHpText').textContent = `${e.hp} PV restantes • AC ${e.ac}`;
    const max = E.ENEMIES[e.id] ? E.ENEMIES[e.id].hp : Math.max(e.hp, 1);
    $('enemyHpBar').style.width = `${Math.max(0, Math.min(100, e.hp / max * 100))}%`;
  }

  function renderCharacter() {
    const p = state.player;
    $('charName').textContent = p.name;
    $('charClass').textContent = `${p.className} ${p.level}`;
    $('hpText').textContent = `${p.hp}/${p.maxHp}`; $('acText').textContent = p.ac; $('abText').textContent = p.attackBonus >= 0 ? `+${p.attackBonus}` : p.attackBonus; $('strainText').textContent = p.systemStrain; $('conditionText').textContent = p.condition || 'Apto';
    $('playerHpBar').style.width = `${Math.max(0, p.hp / p.maxHp * 100)}%`;
    const attrNames = { str:'FOR', dex:'DES', con:'CON', int:'INT', wis:'SAB', cha:'CAR' };
    $('attrGrid').innerHTML = Object.entries(p.attrs).map(([k,v]) => `<div><span>${attrNames[k]}</span><strong>${v} (${p.mods[k] >= 0 ? '+' : ''}${p.mods[k]})</strong></div>`).join('');
    $('skillsGrid').innerHTML = Object.entries(p.skills).filter(([,v]) => v >= 0).map(([k,v]) => `<span class="skill">${escapeHtml(k)} ${v}</span>`).join('');
    $('inventoryList').innerHTML = p.inventory.map(i => `<span class="item">${escapeHtml(i)}</span>`).join('');
  }

  function renderWorld() {
    const known = state.factions.filter(f => f.known !== false);
    $('factionList').innerHTML = known.map(f => `<div class="faction-card"><b>${escapeHtml(f.name)}</b><small>${escapeHtml(f.goal)}</small><div class="faction-stats"><span>Força ${f.force ?? f.power ?? 0}</span><span>Astúcia ${f.cunning ?? 0}</span><span>Riqueza ${f.wealth ?? 0}</span></div><div class="progress"><i style="width:${Math.min(100,(f.progress||0)/(f.clock||6)*100)}%"></i></div></div>`).join('') || '<p class="muted-note">Nenhuma facção conhecida.</p>';

    const cur = currentHex();
    $('npcWorldList').innerHTML = Object.values(state.npcs).map(n => {
      const visibleLocation = n.location === cur.key ? (cur.poi?.name || `hex ${cur.key}`) : (n.lastSeenDay ? `última vez visto: dia ${n.lastSeenDay}` : 'localização atual desconhecida');
      return `<article class="npc-world-card"><div class="mini-token">${tokenHtml(n.id,n.name)}</div><div><b>${escapeHtml(n.name)}</b><small>${escapeHtml(n.role)} • ${escapeHtml(visibleLocation)}</small><p>${escapeHtml(n.agenda ? 'Objetivo percebido: '+n.agenda.split(' e ')[0] : '')}</p></div></article>`;
    }).join('');

    const publicClocks=(state.world?.clocks||[]).filter(c=>c.public);
    $('worldClockList').innerHTML=publicClocks.map(c=>`<div class="world-clock"><div><b>${escapeHtml(c.label)}</b><span>${c.value}/${c.max}</span></div><div class="progress"><i style="width:${Math.min(100,c.value/c.max*100)}%"></i></div></div>`).join('') || '<p class="muted-note">Nenhum relógio público.</p>';
    const ev=(state.world?.publicEvents||[]).slice(0,8);
    $('worldEventList').innerHTML=ev.length?ev.map(e=>`<p><b>Dia ${e.day}:</b> ${escapeHtml(e.text)}</p>`).join(''):'<p class="muted-note">Nenhuma mudança pública chegou até você ainda.</p>';
  }

  function tokenHtml(entityId,name){
    const tok=state.visual?.tokens?.[entityId];
    if(tok?.dataUrl) return `<img src="${tok.dataUrl}" alt="${escapeHtml(name)}">`;
    return `<span>${escapeHtml(initials(name))}</span>`;
  }
  function initials(name){ return String(name||'?').split(/\s+/).slice(0,2).map(s=>s[0]||'').join('').toUpperCase(); }

  function renderEntityStrip(){
    const strip=$('entityStrip'); strip.innerHTML='';
    E.activeVisualEntities(state).forEach(entity=>{
      const b=document.createElement('button'); b.className='entity-token-card'; b.type='button'; b.dataset.entityId=entity.id;
      b.innerHTML=`<div class="entity-token">${tokenHtml(entity.id,entity.name)}</div><div><b>${escapeHtml(entity.name)}</b><small>${escapeHtml(entity.role)}</small></div><span class="edit-token-mark">✎</span>`;
      b.addEventListener('click',()=>openTokenDialog(entity.id)); strip.appendChild(b);
    });
  }

  function renderJournal() {
    $('journalList').innerHTML = state.journal.map(j => `<article class="journal-item"><small>${escapeHtml(j.when)} • ${escapeHtml(j.type.toUpperCase())}</small><p>${escapeHtml(j.text)}</p></article>`).join('');
  }

  function renderHexLibrary(){
    const lib=window.XWN_HEX_LIBRARY||[]; const host=$('hexLibraryGrid'); if(!host) return;
    host.innerHTML=lib.map(x=>`<article class="hex-library-card"><div class="hex-library-img" style="background-image:url('${x.file}')"></div><b>${escapeHtml(x.terrain)}</b><small>${escapeHtml(x.variant)}</small></article>`).join('');
    $('hexLibraryCount').textContent=`${lib.length} variações flat-top 224×194`;
  }

  function renderRules() {
    $('ruleIndexStatus').textContent = `Índice local ativo: ${RULE_INDEX.length} páginas do WWN SRD • busca offline • fonte exibida`;
    if (state.lastRuleAnswer) $('rulesAnswer').textContent = state.lastRuleAnswer;
  }

  function renderAll(persist = true) {
    renderMap(); renderMeta(); renderEntityStrip(); renderStory(); renderCharacter(); renderWorld(); renderJournal(); renderRules(); renderHexLibrary();
    if (persist) saveState();
  }

  function handleResult(result) {
    if (!result) return;
    if (result.narrative) state.narrative = result.narrative;
    if (typeof result.mechanics === 'string') state.lastMechanics = result.mechanics;
    renderAll(true);
    $('storySection').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function escapeHtml(v) { return String(v ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

  async function imageFileToToken(file){
    const dataUrl=await fileToDataUrl(file);
    const img=await loadImage(dataUrl);
    const size=256; const canvas=document.createElement('canvas'); canvas.width=size; canvas.height=size;
    const ctx=canvas.getContext('2d');
    const scale=Math.max(size/img.width,size/img.height); const w=img.width*scale,h=img.height*scale;
    ctx.drawImage(img,(size-w)/2,(size-h)/2,w,h);
    return {dataUrl:canvas.toDataURL('image/jpeg',.84),fileName:file.name,mimeType:'image/jpeg',assignedAt:new Date().toISOString()};
  }
  function fileToDataUrl(file){ return new Promise((res,rej)=>{ const r=new FileReader(); r.onload=()=>res(r.result); r.onerror=rej; r.readAsDataURL(file); }); }
  function loadImage(src){ return new Promise((res,rej)=>{ const i=new Image(); i.onload=()=>res(i); i.onerror=rej; i.src=src; }); }

  function openTokenDialog(entityId){
    editingTokenEntity=entityId; const e=E.entitySnapshot(state,entityId); if(!e) return;
    $('tokenDialogTitle').textContent=`${e.name} • ${e.role}`;
    $('tokenDescriptor').value=e.descriptor||'';
    $('tokenPreview').innerHTML=tokenHtml(entityId,e.name);
    $('tokenDialog').showModal();
  }

  async function handleTokenFile(file){
    if(!editingTokenEntity||!file) return;
    const token=await imageFileToToken(file);
    E.setEntityToken(state,editingTokenEntity,token);
    saveState();
    const e=E.entitySnapshot(state,editingTokenEntity);
    $('tokenPreview').innerHTML=tokenHtml(editingTokenEntity,e.name);
    renderEntityStrip(); renderWorld();
  }

  function saveDescriptor(){
    if(!editingTokenEntity) return;
    const value=$('tokenDescriptor').value.trim();
    if(editingTokenEntity==='player') state.player.visualDescriptor=value;
    else if(state.npcs[editingTokenEntity]) state.npcs[editingTokenEntity].visualDescriptor=value;
    saveState(); renderEntityStrip();
  }

  function makeGeminiBundle(){
    lastGeminiBundle=E.makeGeminiImageBundle(state);
    $('geminiPromptText').value=lastGeminiBundle.prompt;
    $('geminiReferenceList').innerHTML=lastGeminiBundle.references.length ? lastGeminiBundle.references.map(r=>`<div class="gemini-ref"><img src="${r.dataUrl}" alt=""><div><b>${escapeHtml(r.name)}</b><small>${escapeHtml(r.fileName)}</small></div></div>`).join('') : '<p class="muted-note">Nenhum token personalizado anexado. O prompt ainda usa as descrições visuais persistentes.</p>';
    saveState(); $('geminiDialog').showModal();
  }

  function downloadJson(obj,filename){
    const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=filename; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),700);
  }

  function bindSpeechButton(buttonId,targetId,statusId){
    const btn=$(buttonId), target=$(targetId), status=$(statusId);
    if(!A.supportsSTT()){ btn.classList.add('unsupported'); btn.title='Fala para texto não disponível neste navegador'; status.textContent=''; }
    btn.addEventListener('click',()=>{
      if(A.state.activeRecognitionTarget===target){ A.stopListening(); return; }
      A.listenTo(target);
    });
    A.on(ev=>{
      if(ev.target!==target) return;
      if(ev.type==='listenstart'){ btn.classList.add('listening'); status.textContent='Ouvindo… toque novamente para parar.'; }
      if(ev.type==='listenend'){ btn.classList.remove('listening'); status.textContent='Texto capturado. Revise e envie quando quiser.'; }
      if(ev.type==='listenerror'){ btn.classList.remove('listening'); status.textContent=`Microfone: ${ev.error}.`; }
    });
  }

  function setupAudioUi(){
    loadAudioSettings();
    A.on(ev=>{
      if(ev.type==='speechstart') $('audioStatus').textContent='Falando';
      if(ev.type==='speechend') $('audioStatus').textContent='Pronto';
      if(ev.type==='listenstart') $('audioStatus').textContent='Ouvindo';
      if(ev.type==='listenend') $('audioStatus').textContent='Pronto';
    });
    $('ttsRate').addEventListener('input',e=>{ A.configure({rate:+e.target.value}); $('ttsRateValue').value=`${(+e.target.value).toFixed(2)}×`; persistAudioSettings(); });
    $('ttsVolume').addEventListener('input',e=>{ A.configure({volume:+e.target.value}); $('ttsVolumeValue').value=`${Math.round(+e.target.value*100)}%`; persistAudioSettings(); });
    $('ambientToggle').addEventListener('change',e=>{ A.configure({ambientEnabled:e.target.checked}); A.syncWorldState({terrain:E.TERRAIN[currentHex().terrain].label,weather:state.campaign.weather}); persistAudioSettings(); });
    $('ambientVolume').addEventListener('input',e=>{ A.configure({ambientVolume:+e.target.value}); $('ambientVolumeValue').value=`${Math.round(+e.target.value*100)}%`; persistAudioSettings(); });
  }

  $('travelBtn').addEventListener('click', () => handleResult(E.travelTo(state, state.selected.q, state.selected.r)));
  $('exploreBtn').addEventListener('click', () => handleResult(E.exploreCurrentHex(state)));
  $('sendAction').addEventListener('click', () => { const text = $('actionInput').value.trim(); if (!text) return; $('actionInput').value = ''; handleResult(E.performAction(state, text)); });
  $('actionInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('sendAction').click(); } });
  $('sendRule').addEventListener('click', () => {
    const q = $('rulesInput').value.trim(); if (!q) return;
    const before = JSON.stringify({ day: state.campaign.day, hour: state.campaign.hour, current: state.current, journal: state.journal.length, world:state.world?.lastProcessedDay, narrative:state.narrative });
    const answer = E.queryRulesIndexed(state, q, RULE_INDEX);
    const after = JSON.stringify({ day: state.campaign.day, hour: state.campaign.hour, current: state.current, journal: state.journal.length, world:state.world?.lastProcessedDay, narrative:state.narrative });
    $('rulesAnswer').textContent = answer + (before === after ? '\n\n✓ Cena preservada: nenhuma alteração temporal, espacial, narrativa ou de mundo vivo.' : '\n\n⚠ Auditoria: alteração indevida detectada.');
    $('rulesInput').value = ''; saveState();
  });
  $('rulesInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('sendRule').click(); } });
  $('attackBtn').addEventListener('click', () => handleResult(E.playerAttack(state)));
  $('fleeBtn').addEventListener('click', () => handleResult(E.fleeCombat(state)));
  $('zoomIn').addEventListener('click', () => { mapScale = Math.min(1.6, mapScale + .1); renderMap(); });
  $('zoomOut').addEventListener('click', () => { mapScale = Math.max(.65, mapScale - .1); renderMap(); });
  $('zoomReset').addEventListener('click', () => { mapScale = 1; renderMap(); $('mapViewport').scrollTo({left: 90, top: 55, behavior:'smooth'}); });
  $('ttsBtn').addEventListener('click', () => A.speak((state.narrative || []).join(' ')));
  $('ttsStopBtn').addEventListener('click', () => A.stopSpeech());
  $('exportBtn').addEventListener('click', () => { const blob = new Blob([E.exportState(state)], {type:'application/json'}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `braseiro_xwn_${Date.now()}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 500); });
  $('importInput').addEventListener('change', async e => { const file = e.target.files[0]; if (!file) return; try { state = E.importState(await file.text()); renderAll(true); } catch (err) { alert('JSON inválido: ' + err.message); } e.target.value = ''; });
  $('resetBtn').addEventListener('click', () => { if (confirm('Reiniciar a campanha piloto?')) { localStorage.removeItem(E.STORAGE_KEY); OLD_STORAGE_KEYS.forEach(k=>localStorage.removeItem(k)); state = E.makeInitialState(); renderAll(true); } });
  document.querySelectorAll('.bottom-nav button').forEach(b => b.addEventListener('click', () => $(b.dataset.target).scrollIntoView({ behavior:'smooth', block:'start' })));

  $('tokenFileInput').addEventListener('change',async e=>{ const file=e.target.files[0]; if(file) await handleTokenFile(file); e.target.value=''; });
  $('clearTokenBtn').addEventListener('click',()=>{ if(!editingTokenEntity)return; E.setEntityToken(state,editingTokenEntity,null); saveState(); const e=E.entitySnapshot(state,editingTokenEntity); $('tokenPreview').innerHTML=tokenHtml(editingTokenEntity,e.name); renderEntityStrip(); renderWorld(); });
  $('saveDescriptorBtn').addEventListener('click',saveDescriptor);
  $('geminiPromptBtn').addEventListener('click',makeGeminiBundle);
  $('copyGeminiPrompt').addEventListener('click',async()=>{ if(!lastGeminiBundle)return; try{await navigator.clipboard.writeText(lastGeminiBundle.prompt); $('copyGeminiPrompt').textContent='Copiado ✓'; setTimeout(()=>$('copyGeminiPrompt').textContent='Copiar prompt',1300);}catch(_){ $('geminiPromptText').select(); document.execCommand('copy'); } });
  $('downloadGeminiBundle').addEventListener('click',()=>{ if(lastGeminiBundle) downloadJson(lastGeminiBundle,`braseiro_gemini_scene_${Date.now()}.json`); });

  bindSpeechButton('actionMic','actionInput','actionSpeechStatus');
  bindSpeechButton('rulesMic','rulesInput','rulesSpeechStatus');
  setupAudioUi();
  loadState();
  renderAll(false);
  requestAnimationFrame(() => $('mapViewport').scrollTo({ left: 85, top: 55 }));
  if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) navigator.serviceWorker.register('./sw.js').catch(()=>{});
})();
