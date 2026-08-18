# CHANGELOG 3.1.0 — MULTISYSTEM CORE

## Falhas novas encontradas e corrigidas

1. **Universalidade falsa:** 3.0.1 declarava motor XWN, porém regras, estado, manifest, UI e testes eram WWN-hardcoded.
2. **Vazamento do Mestre:** gmBridge instruía o narrador explicitamente como Worlds Without Number mesmo em futuro estado não-WWN.
3. **Migração contaminável:** um save pré-multissistema poderia receber outro identificador e preservar NPCs/POIs/facções de Dorsa.
4. **Vazamento visual AWN:** Ashes estava configurado para usar tiles de terreno WWN antes de possuir atlas próprio.
5. **Erros introduzidos pela expansão da suíte:** colisões de identificadores `ids` e `legacy` no teste; corrigidas e regressão repetida.

## Implementado

- `systems.js` para WWN/SWN/AWN/CWN.
- Identidade de sistema no estado, regras, atlas, UI, exportação, prompts e narração IA.
- Seleção de sistema com campanha nova isolada.
- Perfis iniciais não-WWN sem personagens/NPCs/facções/clima de WWN.
- Bloqueios mecânicos e de RAG para impedir regra inventada ou corpus errado.
- Migração defensiva pré-3.1 => WWN.
- Manifest/service worker multissistema.
- Visual abstrato temporário para SWN/AWN/CWN.

## Validação

- 148 assertions unitárias/estáticas: PASS.
- 3.625 checks adversariais em 500 round-trips de saves: PASS.
- 12/12 recursos PWA essenciais via HTTP local: PASS.
- Chromium headless: inconclusivo por limitação do ambiente (processo/DBus), não contado como PASS.
