(function(global){
  'use strict';
  const KEY='braseiro_xwn_gemini_key';
  const ENABLED='braseiro_xwn_gm_ai_enabled';
  // Cadeia recuperada do Forbidden Lands 3.2.0 anexado pelo usuário.
  const MODELS=['gemini-3.5-flash-lite','gemini-3.6-flash','gemini-3.5-flash','gemini-3.1-flash-lite'];
  function getKey(){return localStorage.getItem(KEY)||''} function setKey(v){const x=String(v||'').trim();if(x)localStorage.setItem(KEY,x);else localStorage.removeItem(KEY);return x}
  function enabled(){return localStorage.getItem(ENABLED)==='1'&&!!getKey()} function setEnabled(v){localStorage.setItem(ENABLED,v?'1':'0')}
  function cleanParagraphs(text){return String(text||'').replace(/^```[a-z]*|```$/gim,'').trim().split(/\n\s*\n/).map(x=>x.replace(/^[-*#]+\s*/,'').trim()).filter(Boolean).slice(0,4)}
  async function callModel(model,key,prompt){
    const url=`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`;
    const ctl=new AbortController();const timer=setTimeout(()=>ctl.abort(),16000);
    try{
      const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{role:'user',parts:[{text:prompt}]}],generationConfig:{temperature:.72,maxOutputTokens:700}}),signal:ctl.signal});
      if(!r.ok) throw new Error(`${model}: HTTP ${r.status}`);
      const data=await r.json();return data?.candidates?.[0]?.content?.parts?.map(p=>p.text||'').join('\n').trim()||'';
    }finally{clearTimeout(timer)}
  }
  async function refineNarrative(ctx){
    if(!enabled())return null;const key=getKey();
    const systemLabel=ctx.systemLabel||ctx.system||'Without Numbers';
    const systemGenre=ctx.systemGenre||'sandbox';
    const prompt=`Você é a VOZ DE MESA do Mestre de ${systemLabel}, um jogo ${systemGenre}. O motor determinístico já decidiu todos os fatos, regras, posições e consequências abaixo. NÃO acrescente regra, teste, NPC, inimigo, pista, distância, objeto, saída, segredo ou consequência não contida nos fatos. NÃO controle o personagem jogador.\n\nDIREÇÃO ACTUAL PLAY recuperada dos projetos Braseiro: procedimento gera ficção; mundo já estava em movimento; chegada = luz/horário + entrada + atividade atual + reação; NPC entra fazendo algo e só sabe o que sabe; rumor não vira fato; rotina conhecida comprime; ameaça cresce por sinais antes do contato; narração para na primeira incerteza significativa; falha cobra custo/exposição/tempo/posição/complicação em vez de bloquear; Use o padrão Braseiro de actual play: CONTEXTO → ESPAÇO → MOVIMENTO/ATIVIDADE → FOCO → IMPLICAÇÃO → abertura para ação. Normalmente 1 a 3 parágrafos e 350 a 900 caracteres; só amplie quando a cena realmente ganhou peso. Linguagem concreta, oral e jogável. Evite prosa ornamental, metáforas em série, frases que comentem a própria narrativa e explicações do que “importa”. Não explique mecânica e não termine com pergunta artificial.\n\nFATOS CANÔNICOS:\nLocal: ${ctx.location}\nTerreno: ${ctx.terrain}\nDia/hora: ${ctx.day}, ${ctx.time} (${ctx.period})\nClima: ${ctx.weather}\nAção do jogador: ${ctx.action||'abertura/continuação'}\nNPCs comprovadamente presentes: ${ctx.npcs||'nenhum'}\nPOI conhecido/percebido: ${ctx.poi||'nenhum confirmado'}\nResolução mecânica já decidida (NÃO narrar números): ${ctx.mechanics||'nenhuma'}\n\nRASCUNHO FACTUAL DO MOTOR:\n${(ctx.scaffold||[]).join('\n\n')}\n\nReescreva APENAS a narração em português do Brasil, como um mestre falando na mesa: o suficiente para situar, tornar o espaço perceptível, mostrar o que está acontecendo agora e parar antes de decidir pelo jogador. Preserve todos os fatos acima. Retorne só os parágrafos narrativos.`;
    let last='';
    for(const m of MODELS){try{const text=await callModel(m,key,prompt);if(text){const p=cleanParagraphs(text);if(p.length)return {paragraphs:p,model:m}}}catch(e){last=String(e?.message||e)}}
    throw new Error(last||'Nenhum modelo respondeu');
  }
  global.XWNGMBridge={MODELS,getKey,setKey,enabled,setEnabled,refineNarrative};
})(window);
