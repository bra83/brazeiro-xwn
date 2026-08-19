# Motor Barbara 1.0

Núcleo desacoplado de Mestre IA para RPG, projetado para substituir o fluxo tradicional dos apps sem perder inteligência de regras, continuidade ou Mundo Vivo.

## Garantias do núcleo
- Mundo Vivo obrigatório e independente da câmera: NPCs, rotinas, facções, clocks, rumores, eventos e consequências persistentes.
- RAG persistente híbrido com SQLite, escopo por campanha/sistema, autoridade, proveniência, checksum, busca lexical + vetorial e proteção de segredos.
- Rule Gate fail-closed e autoridade mecânica separada do Narrador.
- memória estruturada e contextual, save/load canônico e idempotência persistida entre reinícios.
- NPCs com conhecimento limitado, agendas privadas e memória própria.
- separação entre fato, rumor e inferência, com Claim Grounding pós-geração.
- proteção de agência, anti-resumo, perguntas múltiplas, narrativa proporcional à importância e canais separados para regras/ajuda/TTS.
- patches de estado validados e transacionais, retry limitado e rollback integral.
- replay determinístico, telemetria de regressão e homologação integrada de campanha longa.
- 12 adapters: D&D, Mystara, Mausritter, Forbidden Lands, O Um Anel, GURPS, Worlds/Stars/Cities/Ashes Without Number, Tales from the Loop e Traveller 2e.

A matriz de fechamento da versão está em `docs/RELEASE_1_0_ACCEPTANCE.md`. A CI deve manter verdes a suíte completa, a construção da wheel e o smoke test em instalação limpa. A homologação Gemini live usa `gemini-3.5-flash-lite` e depende de credencial/cota externa.

> O branch `backup-xwn-pre-barbara` preserva o conteúdo XWN anterior ao corte.
