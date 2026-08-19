# Auditoria — Braseiro XWN 4.0.0 + Motor Barbara

## Escopo e origem

Esta versão foi reconstruída a partir da árvore XWN preservada em `backup-xwn-pre-barbara` e confrontada com os invariantes conhecidos da linha 3.5/3.6/3.7. O ZIP exato `Braseiro_XWN_3.7.0_FINAL_AUDIT.zip` não estava recuperável no ambiente desta rodada; portanto não se afirma identidade byte a byte com aquele artefato. Os comportamentos documentados da 3.7 foram reimplementados e transformados em gates automatizados.

Referência conhecida do artefato 3.7: SHA-256 `11c6434d83fe7eefef6a30dfe3b5fc1d52570dadf2f9bf3a6ccb6f598be6cdf6`.

## Regras

### Worlds Without Number

Estado: **RULES READY**.

Autoridade: **Worlds Without Number SRD 1.0**.

A implementação preserva e testa: perícias 2d6 + perícia + atributo; penalidade por falta de nível-0; dificuldades e modificadores situacionais; iniciativa; ataque; Shock; reação; moral; instinto; viagem/hexcrawl; exploração; facções; ferimento mortal e estabilização. Consultas de regra não avançam o mundo.

A regressão específica da 3.7 para as consultas rápidas `moral`, `ataque` e `acertar/AC` foi recriada em `xwn4-rules-fix.js` e possui teste independente em `tests/test_xwn4_rule_boundaries.js`.

### Stars Without Number Revised

Estado: **RULES READY**.

Autoridade: **Stars Without Number: Revised Edition**.

Foram homologados no núcleo local: perícias 2d6; salvamentos; iniciativa individual 1d8 + Destreza; ataque 1d20 + AB + perícia + atributo contra AC; penalidade -2 para arma sem nível-0; dano e Shock; cobertura; alcance; arma de uma mão em melee a -4; bloqueio de arma de duas mãos em melee; Total Defense; Fighting Withdrawal. O combate tático usa tabuleiro 11×11, múltiplos atores sem sobreposição, obstáculos e cobertura.

### Cities Without Number e Ashes Without Number

Estado: **FAIL-CLOSED** nesta build.

Os sistemas aparecem como domínios isolados e podem usar save, narrativa, Mundo Vivo, mapas, áudio, tokens, snapshots e demais infraestrutura. A resolução mecânica específica fica bloqueada até existir um corpus RULE principal homologado. A build não reutiliza regra de WWN/SWN como substituto.

## Isolamento entre sistemas

Cada sistema possui save próprio e identidade mecânica própria. SWN usa domínio espacial e hex pointy-top; WWN mantém hexcrawl flat-top. CWN e AWN usam domínios de apresentação próprios. NPCs, facções, POIs, RAG e fichas não podem cruzar silenciosamente entre sistemas.

## Paridade funcional com o Braseiro D&D como referência

A versão mantém ou acrescenta:

- campanha/aventura JSON completa: exportar e importar;
- migração de saves WWN 3.x;
- ficha de personagem JSON: exportar e importar, sanitizada e vinculada ao sistema;
- snapshots locais persistentes via IndexedDB, além de snapshot exportável;
- dados virtuais d4/d6/d8/d10/d12/d20/d100 com cursor independente do RNG do mundo;
- tokens e descritores visuais persistentes;
- compartilhamento de prompt/imagem com Gemini e continuidade visual;
- mapas/atlas, fog of war e biblioteca de terrenos;
- 44 variantes visuais WWN: 30 PNG históricos preservados + 14 variantes 224×194 reconstruídas para recuperar a amplitude funcional conhecida da 3.7;
- áudio/TTS Charon e fallback de voz do navegador/Android;
- ambiência procedural;
- biblioteca de música/ambiência local via IndexedDB, com play/stop/delete;
- diário de campanha e continuidade;
- Mundo Vivo, facções, clocks, rumores e ledgers;
- Rule Gate fail-closed;
- combate determinístico e combate tático SWN;
- sugestões de ação adaptadas ao sistema;
- PWA, service worker, manifesto e share target.

As 14 variantes visuais reconstruídas não são apresentadas como os arquivos PNG originais perdidos da 3.7; são substitutos funcionais novos, com mesma dimensão lógica 224×194 e IDs distintos.

## Motor Barbara

Motor: **1.0.0**, pinado no commit `a31fdb9f9e361fc81b6a5f25c7646450311d0ce3`.

A integração aplica no host XWN:

- jogador conhece apenas o mundo experimentado;
- abertura de campanha é história, não briefing;
- primeira chegada é cena narrativa;
- retorno materialmente alterado é dramatizado novamente;
- clima, economia, guerra, política e cultura aparecem por sinais perceptíveis;
- história vem antes de escolhas;
- proteção de agência;
- NPCs têm conhecimento limitado;
- rumor não vira fato automaticamente;
- regras ficam fora da ficção;
- Gemini não tem autoridade sobre resultado mecânico;
- saída Gemini passa por validação Barbara e uma tentativa de reparo; se continuar inválida, o scaffold determinístico é preservado.

## Gates automatizados

A branch `xwn-4.0.0-barbara` só produz o ZIP de release após:

1. `node --check` em todas as camadas JavaScript;
2. regressão do engine preservado;
3. regressão explícita das quick-rules da 3.7;
4. bateria XWN4 de regras, isolamento, segurança, Barbara, combate e fuzzing;
5. auditoria estática de paridade e assets;
6. smoke real em Chromium/Playwright;
7. criação do ZIP, checksum SHA-256 e `unzip -t`.

A execução de CI é a autoridade final sobre o estado verde/vermelho desta candidata.
