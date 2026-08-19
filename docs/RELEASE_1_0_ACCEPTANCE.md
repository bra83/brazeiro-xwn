# Motor Barbara 1.0 — matriz de aceitação

A 1.0 só é considerada fechada quando todos os requisitos obrigatórios abaixo estão implementados e cobertos por testes automatizados. Nenhum item obrigatório pode permanecer `PARCIAL` ou `AUSENTE`.

| Requisito obrigatório | Estado | Evidência no núcleo |
|---|---|---|
| Arquitetura desacoplada | COMPLETO | `BarbaraEngine` recebe provider, RAG, embedder, recovery, adapters, telemetria e políticas por injeção. |
| Mundo Vivo fora da câmera | COMPLETO | NPCs, rotinas, facções, clocks, eventos, causalidade, sites e rumores avançam sem depender do Narrador. |
| Causalidade e consequências persistentes | COMPLETO | eventos encadeados, `site_changes`, ledgers público/secreto e limites de profundidade/fanout. |
| Memória e continuidade | COMPLETO | memória persistente, busca por relevância/localidade/recência, save/load canônico e idempotência durável. |
| NPCs com conhecimento limitado | COMPLETO | apenas NPCs presentes e conhecimento público alcançam o Narrador; agendas e segredos ficam no Diretor. |
| Rumor separado de verdade | COMPLETO | confiança por localização, propagação por rotas e `truth_status` privado. |
| Rule Gate fail-closed | COMPLETO | ação mecânica e consulta de regra com provider exigem evidência `RULE` aplicável. |
| Autoridade mecânica | COMPLETO | Narrador não decide resultado pendente; resolução confiável vem de host/adapter/dados e é vinculada ao sistema. |
| Agência do jogador | COMPLETO | ações deliberativas não podem ser convertidas pelo Narrador em ações executadas. |
| Anti-resumo e densidade proporcional | COMPLETO | bandas de importância, mínimo para cenas relevantes e abertura obrigatória para decisão. |
| Perguntas múltiplas | COMPLETO | respostas estruturadas não podem colapsar várias perguntas relevantes em uma só. |
| Validação pós-geração | COMPLETO | schema, claims grounded, patches, agência, mecânica, densidade e completude são validados antes do commit. |
| Recuperação/fallback transacional | COMPLETO | retry limitado para timeout/429/5xx e rollback integral em falha. |
| RAG persistente híbrido e seguro | COMPLETO | SQLite, lexical + vetor, autoridade, checksum, isolamento campanha/sistema, quarentena e ACL de segredo. |
| Adapters obrigatórios | COMPLETO | D&D, Mystara, Mausritter, Forbidden Lands, O Um Anel, GURPS, WWN, SWN, CWN, AWN, Tales from the Loop e Traveller 2e. |
| Replay e regressão | COMPLETO | replay semântico determinístico, checkpoints, telemetria de assinaturas e campanhas longas integradas. |
| Persistência de app móvel | COMPLETO | estado JSON canônico e idempotência persistida impedem duplo turno após reinício/retry. |
| Empacotamento instalável | COMPLETO | CI constrói wheel e realiza smoke test em ambiente virtual limpo. |

## Homologação externa Gemini

O provider HTTP real e o workflow de homologação live existem e usam `gemini-3.5-flash-lite`. A execução live depende de `GEMINI_API_KEY` e de cota disponível no momento. Falha por ausência de credencial ou quota é condição externa de homologação, não ausência de implementação do motor.

## Regra de release

A branch `main` só representa Barbara 1.0 quando `pytest -q`, build da wheel e smoke de instalação limpa estiverem verdes. O workflow live é uma homologação adicional contra serviço externo e não pode mascarar regressões do núcleo.
