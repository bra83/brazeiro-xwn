# BRASEIRO XWN — Without Numbers 3.3.0 · DOMAIN ISOLATION HARDENING

Build de hardening derivada da 3.0.1 MESA VIVA.

## Estado atual — 3.3.0

- quatro perfis integrados: Worlds Without Number, Stars Without Number, Ashes Without Number e Cities Without Number;
- WWN mantém o corpus mecânico local já indexado; SWN/AWN/CWN continuam fail-closed enquanto seus corpora próprios não forem homologados;
- adaptadores de domínio impedem que SWN/AWN/CWN nasçam a partir do mapa de fantasia de WWN;
- SWN usa geometria pointy-top; WWN/AWN/CWN usam flat-top nesta build;
- importação sanitiza NPCs, facções, campos de mapa e proveniência cross-system;
- RAG sem proveniência explícita é descartado em vez de reutilizado em outro sistema.

## Sistemas reconhecidos pelo núcleo

- Worlds Without Number (WWN)
- Stars Without Number (SWN)
- Ashes Without Number (AWN)
- Cities Without Number (CWN)

O estado, a campanha, o atlas, os prompts visuais, o Mestre opcional, a persistência e a UI agora carregam identidade explícita de sistema. Trocar de sistema cria uma campanha nova para impedir contaminação cruzada.

## Integridade de regras nesta build

WWN mantém o índice local e as mecânicas já homologadas da 3.0.1. SWN, AWN e CWN possuem perfis, estado inicial, identidade visual/narrativa, mundo inicial e isolamento de persistência, mas as regras mecânicas específicas permanecem bloqueadas até os respectivos corpora serem indexados e testados. O motor NÃO reutiliza o WWN SRD para preencher lacunas dos outros jogos.

## Correções estruturais 3.1.0

- Registro central `systems.js` com quatro perfis.
- Migração pré-3.1 tratada como WWN; saves antigos não podem se declarar CWN/SWN/AWN e carregar Dorsa por baixo.
- gmBridge recebe sistema e gênero ativos; removido hardcode de Worlds Without Number.
- Manifest e cache PWA tornados multissistema.
- SWN/CWN/AWN usam visual abstrato seguro enquanto atlas próprios não forem integrados; AWN não herda tiles de fantasia.
- Clima, estação, personagem, NPCs, facções, relógios e ponto inicial não-WWN deixam de herdar os defaults de Dorsa.
- Consultas de regra não-WWN são bloqueadas sem avançar a cena e sem pesquisar o índice WWN.
- Viagem/exploração/resolução mecânica não-WWN ficam bloqueadas nesta fundação até o adaptador mecânico correspondente estar validado.

## Testes desta rodada

- `node --check` em systems.js, engine.js, app.js, gmBridge.js e sw.js.
- `node tests/test_engine.js`: 148 assertions aprovadas.
- Fuzz/round-trip: 3.625 verificações em 500 saves gerados entre os quatro sistemas.
- Todos os 12 recursos essenciais do cache PWA responderam HTTP 200 em servidor local.
- Chromium headless foi tentado, mas o processo não encerrou no ambiente atual por limitações do runtime/DBus; portanto teste visual de navegador não é declarado como aprovado.

## Próximas prioridades obrigatórias

1. Indexar e implementar SWN Revised sem misturar WWN.
2. Localizar/indexar CWN e AWN no acervo; se ausentes, registrar fonte canônica antes de codificar mecânicas.
3. Criar adaptadores mecânicos por sistema e retirar os bloqueios de integridade somente após testes.
4. Criar atlas/geradores próprios: setor para SWN, cidade/distritos para CWN, ermos pós-apocalípticos para AWN.
5. Repetir regressão completa WWN a cada integração.
