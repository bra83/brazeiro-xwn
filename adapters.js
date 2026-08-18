(function(global){
  'use strict';
  const SYSTEMS=global.XWN_SYSTEMS||{};
  const LABELS=Object.freeze({
    SWN:['sistema estelar','espaço profundo','cinturão de detritos','mundo habitado','posto orbital','anomalia de navegação'],
    AWN:['ermo aberto','ruínas habitáveis','estrada quebrada','zona de sucata','assentamento disperso','área de risco'],
    CWN:['distrito corporativo','zona residencial','corredor industrial','mercado de rua','periferia densa','infraestrutura crítica']
  });
  const STARTS=Object.freeze({
    SWN:{name:'Ponto de Chegada',kind:'system',icon:'✦',summary:'Um sistema de fronteira cuja situação precisa ser confirmada em jogo.'},
    AWN:{name:'Abrigo de Partida',kind:'settlement',icon:'⌂',summary:'Um ponto seguro relativo na borda de um ermo ainda pouco conhecido.'},
    CWN:{name:'Distrito Zero',kind:'district',icon:'▦',summary:'Um distrito urbano conhecido apenas pelo que a campanha já confirmou.'}
  });
  const OWNERS=Object.freeze({
    WWN:new Set(['mara','del','selka','arven','nera','torren','vey','salt','bell','ash','reed','crown']),
    SWN:new Set(['ira','sen','vex','consorcio','livres','arquivo']),
    AWN:new Set(['ena','bar','kes','agua','trilho','cinza']),
    CWN:new Set(['lia','tor','nox','helix','nove','grid'])
  });
  function key(q,r){return `${q},${r}`}
  function hashString(str){let h=2166136261>>>0;for(let i=0;i<str.length;i++){h^=str.charCodeAt(i);h=Math.imul(h,16777619)}return h>>>0}
  function normalize(id){const k=String(id||'WWN').toUpperCase();return SYSTEMS[k]?k:'WWN'}
  function sourceOwner(id){for(const [sys,set] of Object.entries(OWNERS))if(set.has(String(id)))return sys;return null}
  function generateDomainHexes(systemId,radius=4){
    const sys=normalize(systemId); if(sys==='WWN')return null;
    const labels=LABELS[sys]||['zona desconhecida'], out={};
    for(let q=-radius;q<=radius;q++){
      const r1=Math.max(-radius,-q-radius),r2=Math.min(radius,-q+radius);
      for(let r=r1;r<=r2;r++){
        const k=key(q,r),start=k==='0,0';
        out[k]={q,r,key:k,domainTerrain:labels[hashString(`${sys}:${k}`)%labels.length],systemLabel:labels[hashString(`${sys}:label:${k}`)%labels.length],sourceSystem:sys,discovered:start,explored:start,visited:start,visitCount:start?1:0,discoverySource:start?'campaign-start':null,poi:start?JSON.parse(JSON.stringify(STARTS[sys])):null,notes:[]};
      }
    }
    out['0,0'].systemLabel=STARTS[sys].name;
    return out;
  }
  function sanitizeHexes(systemId,hexes){
    const sys=normalize(systemId), out=hexes||{};
    for(const h of Object.values(out)){
      h.notes ||= []; h.sourceSystem=sys;
      if(sys==='WWN'){ delete h.domainTerrain; delete h.systemLabel; continue; }
      delete h.terrain; delete h.tile; delete h.road;
      h.domainTerrain ||= (LABELS[sys]||['zona desconhecida'])[hashString(`${sys}:${h.key}`)%(LABELS[sys]||['zona desconhecida']).length];
      h.systemLabel ||= h.domainTerrain;
      if(h.key!=='0,0' && h.poi && ['settlement','farm','site','ruin','fort','hazard','landmark','water'].includes(h.poi.kind))h.poi=null;
    }
    if(sys!=='WWN'&&out['0,0']){out['0,0'].poi=JSON.parse(JSON.stringify(STARTS[sys]));out['0,0'].systemLabel=STARTS[sys].name;}
    return out;
  }
  function sanitizeEntityMap(systemId,map){
    const sys=normalize(systemId),clean={};
    for(const [id,raw] of Object.entries(map||{})){
      const owner=sourceOwner(id),declared=raw&&String(raw.sourceSystem||'').toUpperCase();
      if(owner&&owner!==sys)continue;
      if(declared&&declared!==sys)continue;
      clean[id]={id,...raw,sourceSystem:sys};
    }
    return clean;
  }
  function sanitizeFactionList(systemId,list){
    const sys=normalize(systemId),clean=[];
    for(const raw of list||[]){const id=raw?.id;if(!id)continue;const owner=sourceOwner(id),declared=String(raw.sourceSystem||'').toUpperCase();if(owner&&owner!==sys)continue;if(declared&&declared!==sys)continue;clean.push({...raw,sourceSystem:sys});}
    return clean;
  }
  function sanitizeRagChunks(systemId,chunks){
    const sys=normalize(systemId);return (chunks||[]).filter(c=>String(c?.systemId||c?.sourceSystem||c?.corpusSystem||'').toUpperCase()===sys);
  }
  function validateState(state){
    const sys=normalize(state?.campaign?.system),errors=[];
    if(state?.rules?.systemId!==sys)errors.push('rules.systemId mismatch');
    if(state?.system?.id!==sys)errors.push('system.id mismatch');
    if(sys!=='WWN')for(const h of Object.values(state?.hexes||{})){if('terrain'in h||'tile'in h||'road'in h)errors.push(`fantasy field leak ${h.key}`);if(h.sourceSystem!==sys)errors.push(`hex owner mismatch ${h.key}`)}
    for(const [id,n] of Object.entries(state?.npcs||{})){const owner=sourceOwner(id);if(owner&&owner!==sys)errors.push(`npc owner leak ${id}`);if(n?.sourceSystem&&n.sourceSystem!==sys)errors.push(`npc source mismatch ${id}`)}
    for(const f of state?.factions||[]){const owner=sourceOwner(f?.id);if(owner&&owner!==sys)errors.push(`faction owner leak ${f.id}`);if(f?.sourceSystem&&f.sourceSystem!==sys)errors.push(`faction source mismatch ${f.id}`)}
    return {ok:errors.length===0,errors};
  }
  const api={LABELS,STARTS,OWNERS,normalize,sourceOwner,generateDomainHexes,sanitizeHexes,sanitizeEntityMap,sanitizeFactionList,sanitizeRagChunks,validateState};
  global.XWN_ADAPTERS=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
