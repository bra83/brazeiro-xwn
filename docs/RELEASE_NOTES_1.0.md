# Motor Barbara 1.0.0

Motor Barbara 1.0.0 é o primeiro fechamento estável do núcleo desacoplado de Mestre IA para os projetos de RPG.

## Capacidades incluídas

- Mundo Vivo transacional com NPCs, rotinas, facções, clocks, eventos causais, sites persistentes, rumores e consequências fora da câmera.
- Memória de campanha persistente com recuperação por relevância, localidade, saliência e recência.
- NPCs com conhecimento limitado, memória própria, rumores ouvidos e agendas privadas protegidas.
- RAG híbrido persistente em SQLite com escopo por campanha/sistema, autoridade, ACL de segredo, checksum, quarentena e recuperação lexical/vetorial.
- Rule Gate fail-closed e autoridade mecânica separada do Narrador.
- Resolução mecânica vinculada ao adapter/sistema ativo e protegida contra resultados inventados pelo LLM.
- Adapters para D&D, Mystara, Mausritter, Forbidden Lands, O Um Anel, GURPS, Worlds Without Number, Stars Without Number, Cities Without Number, Ashes Without Number, Tales from the Loop e Traveller 2e.
- Orquestração de turno para ficção, diálogo, investigação, viagem, combate, planejamento e consultas meta.
- Agência do jogador, anti-resumo, densidade proporcional, cobertura de perguntas múltiplas e encerramento de cenas importantes em decisão significativa.
- Validação pós-geração de schema, claims, patches, grounding, agência, mecânica e completude.
- Retry limitado para timeout/429/5xx com rollback integral do turno.
- Persistência JSON canônica, idempotência durável entre reinícios, replay semântico determinístico e telemetria de regressão.
- Provider Gemini estruturado com `gemini-3.5-flash-lite` como padrão operacional.

## Critério de release

A release é aceita quando a branch `main` passa a suíte automatizada, constrói a wheel, instala a wheel em ambiente virtual limpo e conclui o smoke test fora do checkout. O artefato `motor-barbara-1.0.0` é publicado pelo GitHub Actions apenas depois dessas etapas.

A homologação Gemini live é adicional e depende de `GEMINI_API_KEY` e cota externa disponível; ausência de quota não invalida a implementação local do provider.

## Compatibilidade

Python 3.11 ou superior. O núcleo não depende de framework de UI e foi projetado para ser integrado aos hosts Android/VTT existentes.
