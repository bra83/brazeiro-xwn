(function(global){
  'use strict';
  const KEY='braseiro_xwn_gemini_key',ENABLED='braseiro_xwn_gm_ai_enabled';
  const MODELS=['gemini-3.5-flash-lite','gemini-3.6-flash','gemini-3.5-flash','gemini-3.1-flash-lite'];
  function getKey(){try{return localStorage.getItem(KEY)||''}catch(_){return''}}
  function setKey(v){const x=String(v||'').trim();try{if(x)localStorage.setItem(KEY,x);else localStorage.removeItem(KEY)}catch(_){}return x}
  function enabled(){try{return localStorage.getItem(ENABLED)==='1'&&!!getKey()}catch(_){return false}}
  function setEnabled(v){try{localStorage.setItem(ENABLED,v?'1':'0')}catch(_){}}
  function cleanParagraphs(text,max=8){return String(text||'').replace(/^```[a-z]*|```$/gim,'').trim().split(/\n\s*\n/).map(x=>x.replace(/^[-*#]+\s*/,'').trim()).filter(Boolean).slice(0,max)}
  function currentState(){try{const E=global.XWNEngine;if(!E)return null;const raw=localStorage.getItem(E.STORAGE_KEY);return raw?E.importState(raw):null}catch(_){return null}}
  async function callModel(model,key,prompt,maxOutputTokens=1400){const url=`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`;const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),30000);try{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{role:'user',parts:[{text:prompt}]}],generationConfig:{temperature:.55,maxOutputTokens}}),signal:ctl.signal});if(!r.ok)throw new Error(`${model}: HTTP ${r.status}`);const data=await r.json();return data?.candidates?.[0]?.content?.parts?.map(p=>p.text||'').join('\n').trim()||''}finally{clearTimeout(timer)}}
  function promptFor(ctx,state,plan,repair=''){
    const systemLabel=ctx.systemLabel||ctx.system||global.XWN_SYSTEMS?.[state?.campaign?.system]?.label||'Without Numbers',systemGenre=ctx.systemGenre||global.XWN_SYSTEMS?.[state?.campaign?.system]?.genre||'sandbox';
    const obligation=plan?.occasion||'continuation',target=plan?.target_chars||[350,900],storyRule=obligation==='continuation'?'Mantenha densidade proporcional ao momento.':`OBRIGAÇÃO DE HISTÓRIA: ${obligation}. Conte uma cena de chegada/abertura real com pelo menos quatro movimentos narrativos e aproximadamente ${target[0]}–${target[1]} caracteres. Não transforme isso em briefing, ficha de contexto ou lista de opções.`;
    const envelope=global.BarbaraBrowser?.narratorEnvelope?.(state,ctx.action||'',ctx.scaffold)||{};
    return `Você é a VOZ DE MESA do Mestre de ${systemLabel}, um jogo ${systemGenre}. O Motor Barbara é a autoridade narrativa. O motor determinístico já decidiu fatos, regras, posições e consequências; você NÃO pode alterar nenhum deles.\n\nCONTRATO OBRIGATÓRIO BARBARA:\n- O jogador NÃO conhece automaticamente o estado do mundo. Não despeje clima, economia, guerras, política ou cultura como relatório. Mostre-os por coisas perceptíveis: preços, filas, soldados, fumaça, tráfego, conversas, ruínas, trabalho, comportamento e paisagem.\n- História antes de escolhas. Uma primeira chegada ou abertura deve ser vivida em cena.\n- NPCs só sabem o que sabem e entram já fazendo algo. Rumor nunca vira fato sem confirmação.\n- Não controle o personagem do jogador nem transforme “talvez/penso em” em ação executada.\n- Não invente regra, teste, NPC, inimigo, pista, distância, objeto, saída ou consequência.\n- Não explique a própria narrativa. Linguagem concreta, oral, PT-BR, como mestre numa mesa de jogo.\n- Regra/tutorial fica fora da ficção. Se houver incerteza mecânica ainda não resolvida, pare antes do resultado.\n${storyRule}\n\nPLANO BARBARA:\n${JSON.stringify(envelope.barbara||plan)}\n\nFATOS CANÔNICOS PERMITIDOS:\nLocal: ${ctx.location}\nTerreno/domínio: ${ctx.terrain}\nDia/hora: ${ctx.day}, ${ctx.time} (${ctx.period})\nClima percebível: ${ctx.weather}\nAção do jogador: ${ctx.action||'abertura/continuação'}\nNPCs comprovadamente presentes: ${ctx.npcs||'nenhum'}\nPOI conhecido/percebido: ${ctx.poi||'nenhum confirmado'}\nResolução mecânica já decidida (não narrar números): ${ctx.mechanics||'nenhuma'}\nEventos públicos conhecidos: ${JSON.stringify(envelope.world_public?.publicEvents||[])}\n\nRASCUNHO FACTUAL DO MOTOR:\n${(ctx.scaffold||[]).join('\n\n')}\n${repair?`\n\nA RESPOSTA ANTERIOR FOI REJEITADA PELO VALIDADOR BARBARA por: ${repair}. Reescreva corrigindo exatamente isso.`:''}\n\nRetorne APENAS parágrafos narrativos, sem títulos, bullets, JSON, resumo ou bloco de contexto.`;
  }
  async function refineNarrative(ctx){
    if(!enabled())return null;const key=getKey(),state=currentState();const plan=state&&global.BarbaraBrowser?global.BarbaraBrowser.plan(state,ctx.action||''):null;let last='';
    for(const model of MODELS){
      try{
        let text=await callModel(model,key,promptFor(ctx,state,plan),plan&&plan.occasion!=='continuation'?1800:1000),paragraphs=cleanParagraphs(text,plan&&plan.occasion!=='continuation'?8:4),validation=state&&global.BarbaraBrowser?global.BarbaraBrowser.validate(state,ctx.action||'',paragraphs.join('\n\n'),plan):{valid:paragraphs.length>0,errors:[]};
        if(!validation.valid){text=await callModel(model,key,promptFor(ctx,state,plan,validation.errors.join(', ')),1800);paragraphs=cleanParagraphs(text,8);validation=state&&global.BarbaraBrowser?global.BarbaraBrowser.validate(state,ctx.action||'',paragraphs.join('\n\n'),plan):{valid:paragraphs.length>0,errors:[]};}
        if(validation.valid&&paragraphs.length){if(state&&plan&&global.BarbaraBrowser)global.BarbaraBrowser.commitExperience(state,plan);return {paragraphs,model,barbara:plan,validated:true};}
        last=`Barbara rejeitou: ${(validation.errors||[]).join(', ')}`;
      }catch(e){last=String(e?.message||e)}
    }
    console.warn('Narrativa Gemini descartada; mantendo scaffold determinístico.',last);return null;
  }
  global.XWNGMBridge={MODELS,getKey,setKey,enabled,setEnabled,refineNarrative};
  // O host antigo é carregado antes da UI. Ativamos a correção 3.7 como camada separada
  // para não depender dos bytes de regex defeituosos herdados de builds antigas.
  if(typeof document!=='undefined'&&!global.XWN4RulesFixLoading){global.XWN4RulesFixLoading=true;const s=document.createElement('script');s.src='xwn4-rules-fix.js';s.async=false;s.onload=()=>{global.XWN4RulesFixLoaded=true;};s.onerror=()=>console.error('Falha ao carregar xwn4-rules-fix.js');document.head.appendChild(s);}
})(window);
