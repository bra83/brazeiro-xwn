(function(global){
  'use strict';

  const listeners = new Set();
  const state = {
    enabled: true,
    speaking: false,
    ambientEnabled: false,
    rate: 1.18,
    pitch: 0.98,
    volume: 1,
    voiceName: '',
    ambientVolume: 0.12,
    currentSoundscape: '',
    recognition: null,
    activeRecognitionTarget: null,
    audioCtx: null,
    ambienceGain: null,
    ambienceSource: null,
    ambienceFilter: null,
    ducked: false,
    queueToken: 0,
  };

  function emit(type, payload={}) { for (const fn of listeners) { try { fn({type, ...payload}); } catch (_) {} } }
  function on(fn){ listeners.add(fn); return () => listeners.delete(fn); }
  function supportsTTS(){ return 'speechSynthesis' in global && 'SpeechSynthesisUtterance' in global; }
  function supportsSTT(){ return !!(global.SpeechRecognition || global.webkitSpeechRecognition); }

  function voices(){
    if (!supportsTTS()) return [];
    return speechSynthesis.getVoices().filter(v => /^pt(-|_)/i.test(v.lang) || /Portugu/i.test(v.name));
  }

  function pickVoice(){
    const vs = voices();
    if (!vs.length) return null;
    if (state.voiceName) {
      const chosen = vs.find(v => v.name === state.voiceName);
      if (chosen) return chosen;
    }
    return vs.find(v => /brasil|brazil|pt-br/i.test(`${v.name} ${v.lang}`)) || vs[0];
  }

  function splitSpeech(text, max=220){
    const clean = String(text||'').replace(/\s+/g,' ').trim();
    if (!clean) return [];
    const sentences = clean.match(/[^.!?…]+[.!?…]?/g) || [clean];
    const chunks=[]; let buf='';
    for (const sentence of sentences){
      const s=sentence.trim();
      if (!s) continue;
      if ((buf+' '+s).trim().length <= max) buf=(buf+' '+s).trim();
      else { if(buf) chunks.push(buf); if(s.length<=max) buf=s; else { for(let i=0;i<s.length;i+=max) chunks.push(s.slice(i,i+max)); buf=''; } }
    }
    if(buf) chunks.push(buf);
    return chunks;
  }

  function ensureAudioContext(){
    if (state.audioCtx) return state.audioCtx;
    const AC = global.AudioContext || global.webkitAudioContext;
    if (!AC) return null;
    const ctx = new AC();
    const gain = ctx.createGain();
    gain.gain.value = state.ambientVolume;
    gain.connect(ctx.destination);
    state.audioCtx = ctx;
    state.ambienceGain = gain;
    return ctx;
  }

  function stopAmbience(){
    if (state.ambienceSource) { try { state.ambienceSource.stop(); } catch (_) {} }
    state.ambienceSource = null;
    state.ambienceFilter = null;
  }

  function makeNoiseBuffer(ctx, seconds=3){
    const buffer=ctx.createBuffer(1,ctx.sampleRate*seconds,ctx.sampleRate);
    const data=buffer.getChannelData(0);
    for(let i=0;i<data.length;i++) data[i]=(Math.random()*2-1)*0.55;
    return buffer;
  }

  function setSoundscape(kind){
    state.currentSoundscape=kind || 'quiet';
    if (!state.ambientEnabled) return;
    const ctx=ensureAudioContext(); if(!ctx) return;
    if (ctx.state==='suspended') ctx.resume().catch(()=>{});
    stopAmbience();
    if(kind==='quiet') return;
    const src=ctx.createBufferSource(); src.buffer=makeNoiseBuffer(ctx); src.loop=true;
    const filter=ctx.createBiquadFilter(); filter.type='lowpass';
    if(/rain|swamp|water/i.test(kind)) filter.frequency.value=1300;
    else if(/mountain|wind/i.test(kind)) filter.frequency.value=650;
    else filter.frequency.value=850;
    src.connect(filter); filter.connect(state.ambienceGain); src.start();
    state.ambienceSource=src; state.ambienceFilter=filter;
  }

  function duck(on){
    const gain=state.ambienceGain; if(!gain || !state.audioCtx) return;
    const now=state.audioCtx.currentTime;
    gain.gain.cancelScheduledValues(now);
    const target=on ? Math.max(0.008,state.ambientVolume*0.16) : state.ambientVolume;
    gain.gain.linearRampToValueAtTime(target, now + (on ? 0.06 : 0.18));
    state.ducked=on;
  }

  function stopSpeech(){
    state.queueToken++;
    if (supportsTTS()) speechSynthesis.cancel();
    state.speaking=false; duck(false); emit('speechend');
  }

  function speak(text, opts={}){
    if(!state.enabled || !supportsTTS()) return false;
    stopSpeech();
    const chunks=splitSpeech(text);
    if(!chunks.length) return false;
    const token=++state.queueToken;
    const voice=pickVoice();
    state.speaking=true; duck(true); emit('speechstart');
    let i=0;
    const next=()=>{
      if(token!==state.queueToken) return;
      if(i>=chunks.length){ state.speaking=false; duck(false); emit('speechend'); return; }
      const u=new SpeechSynthesisUtterance(chunks[i++]);
      u.lang='pt-BR'; u.rate=Number(opts.rate||state.rate); u.pitch=Number(opts.pitch||state.pitch); u.volume=Number(opts.volume||state.volume);
      if(voice) u.voice=voice;
      u.onend=next;
      u.onerror=(e)=>{ emit('error',{error:e.error||'tts'}); next(); };
      speechSynthesis.speak(u);
    };
    next(); return true;
  }

  function createRecognition(){
    const RC=global.SpeechRecognition || global.webkitSpeechRecognition;
    if(!RC) return null;
    const rec=new RC();
    rec.lang='pt-BR'; rec.continuous=false; rec.interimResults=true; rec.maxAlternatives=1;
    return rec;
  }

  function listenTo(target, options={}){
    if(!supportsSTT()) { emit('sttunsupported'); return false; }
    stopSpeech();
    if(state.recognition){ try{state.recognition.abort();}catch(_){ } }
    const rec=createRecognition(); state.recognition=rec; state.activeRecognitionTarget=target;
    const initial=(target.value||'').trim();
    let finalText='';
    rec.onstart=()=>emit('listenstart',{target});
    rec.onresult=(ev)=>{
      let interim='';
      for(let i=ev.resultIndex;i<ev.results.length;i++){
        const t=ev.results[i][0].transcript;
        if(ev.results[i].isFinal) finalText += t+' '; else interim += t;
      }
      target.value=[initial,finalText.trim(),interim.trim()].filter(Boolean).join(initial ? ' ' : '');
      target.dispatchEvent(new Event('input',{bubbles:true}));
    };
    rec.onerror=e=>emit('listenerror',{error:e.error,target});
    rec.onend=()=>{ state.recognition=null; state.activeRecognitionTarget=null; emit('listenend',{target}); };
    try{rec.start(); return true;}catch(e){ emit('listenerror',{error:e.message,target}); return false; }
  }

  function stopListening(){ if(state.recognition){ try{state.recognition.stop();}catch(_){ } } }
  function syncWorldState(world){
    if(!world) return;
    const terrain=String(world.terrain||''); const weather=String(world.weather||'');
    let kind='quiet';
    if(/chuva|tempest/i.test(weather)) kind='rain';
    else if(/pânt|swamp|water|água/i.test(terrain)) kind='water';
    else if(/mont|vento/i.test(terrain+' '+weather)) kind='wind';
    else if(/forest|floresta/i.test(terrain)) kind='forest';
    if(kind!==state.currentSoundscape) setSoundscape(kind);
  }
  function configure(opts={}){
    for(const k of ['rate','pitch','volume','ambientVolume','voiceName']) if(opts[k]!==undefined) state[k]=opts[k];
    if(opts.ambientEnabled!==undefined){ state.ambientEnabled=!!opts.ambientEnabled; if(!state.ambientEnabled) stopAmbience(); else setSoundscape(state.currentSoundscape||'quiet'); }
    if(state.ambienceGain) state.ambienceGain.gain.value=state.ambientVolume;
  }

  global.AudioEngineV2={state,on,supportsTTS,supportsSTT,voices,configure,speak,stopSpeech,listenTo,stopListening,syncWorldState,setSoundscape};
})(window);
