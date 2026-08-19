(function(global){
  'use strict';
  const E=global.XWNEngine;if(!E?.queryRules||!E?.queryRulesIndexed)return;
  const oldQuery=E.queryRules,oldIndexed=E.queryRulesIndexed;
  function isWWN(state){return E.systemId(state?.campaign?.system)==='WWN';}
  function quickWWN(question){
    const q=String(question||'').toLowerCase();
    if(/\bmoral\b|morale/.test(q))return 'Moral: quando as circunstâncias justificam, role 2d6; se o resultado for maior que o valor de Moral, o NPC falha e tenta fugir, render-se ou interromper a luta conforme a situação. [WWN SRD 5.3.1]';
    if(/\bataque\b|\bacertar\b|\bac\b/.test(q))return 'Ataque de personagem: 1d20 + bônus base de ataque + modificador do atributo da arma + perícia de combate relevante. Sem nível-0 na perícia apropriada, a penalidade é -2. Igualar ou superar a AC relevante acerta. [WWN SRD 2.4.5]';
    return null;
  }
  function pageFor(question){const q=String(question||'').toLowerCase();if(/\bmoral\b|morale/.test(q))return 80;if(/\bataque\b|\bacertar\b|\bac\b/.test(q))return 47;return null;}
  E.queryRules=function(state,question){if(!isWWN(state))return oldQuery(state,question);const fast=quickWWN(question);if(!fast)return oldQuery(state,question);state.lastRuleAnswer=fast;return fast;};
  E.queryRulesIndexed=function(state,question,index){if(!isWWN(state))return oldIndexed(state,question,index);const fast=quickWWN(question);if(!fast)return oldIndexed(state,question,index);const pg=pageFor(question),hit=(index||global.XWN_RULE_INDEX||[]).find(x=>x.bookPage===pg);const answer=hit?`${fast}\n\nFONTES INDEXADAS LOCAIS\nWWN SRD p. ${pg}: ${String(hit.text||'').slice(0,430)}`:fast;state.lastRuleAnswer=answer;return answer;};
  if(typeof module!=='undefined'&&module.exports)module.exports=E;
})(typeof window!=='undefined'?window:globalThis);
