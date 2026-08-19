# Braseiro XWN 4.0.0 — Motor Barbara

## Base

Reconstrução auditada da linha XWN 3.x preservada, elevando a candidata para 4.0.0 após integração do Motor Barbara e endurecimento multissistema.

## Principais mudanças

- Motor Barbara 1.0 integrado e pinado no commit `a31fdb9f9e361fc81b6a5f25c7646450311d0ce3`.
- Abertura de campanha, primeira chegada e retorno materialmente alterado passam a exigir história em cena.
- WWN continua mecanicamente baseado no WWN SRD 1.0.
- SWN Revised ganhou índice de regras local e combate tático próprio.
- CWN e AWN permanecem fail-closed para mecânica específica até corpus canônico homologado.
- Saves separados por sistema e migração de saves WWN 3.x.
- Ficha de personagem JSON com import/export e sanitização.
- Snapshots persistentes locais e exportáveis.
- Dados virtuais independentes do RNG do Mundo Vivo.
- Biblioteca de áudio local em IndexedDB, preservando TTS Charon, fallback Android/browser e ambiência.
- 44 variantes visuais WWN disponíveis: 30 PNG preservados e 14 variantes 224×194 reconstruídas.
- SWN usa domínio pointy-top; WWN mantém flat-top.
- Proteções contra vazamento de entidades, facções, regras e fichas entre sistemas.
- Rule Gate explícito e sem fallback de regra entre jogos.
- Correção funcional da regressão 3.7 em consultas rápidas de moral, ataque e AC.
- PWA/service worker/manifesto/share target atualizados para os novos módulos.

## Compatibilidade

Nenhuma função histórica é intencionalmente removida. O objetivo da 4.0 é manter a infraestrutura já existente e acrescentar paridade de app com a referência D&D onde havia lacunas: snapshots, ficha JSON, dados virtuais, áudio local e orquestração Barbara.

Consulte `AUDITORIA_XWN_4.0.0_MOTOR_BARBARA.md` e `VALIDACAO_XWN_4.0.0.txt` no pacote final.
