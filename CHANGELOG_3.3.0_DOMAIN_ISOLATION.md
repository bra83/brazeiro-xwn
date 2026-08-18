# CHANGELOG 3.3.0 — DOMAIN ISOLATION HARDENING

## Correções estruturais

- `adapters.js` passa a ser a camada explícita de domínio para WWN, SWN, AWN e CWN.
- SWN/AWN/CWN não são mais derivados do `generateHexes()` de WWN: nascem com estado de domínio próprio e sem `terrain`, `tile` ou `road` de fantasia.
- SWN usa orientação `pointy`; WWN, AWN e CWN usam `flat` nesta build.
- importação de saves 3.1+ reconhece corretamente toda a linha multissistema, inclusive 3.2 e 3.3.
- saves são sanitizados contra contaminação cross-system de hexes, NPCs e facções.
- entidades canônicas conhecidas têm ownership de sistema; ids de outro sistema são descartados na importação.
- chunks RAG sem proveniência explícita ou com proveniência de outro sistema são descartados em modo fail-closed.
- renderização e prompts de cena usam `systemLabel/domainTerrain` com fallback seguro e não presumem `TERRAIN` de WWN.
- cache offline inclui `adapters.js` e foi versionado para `v330-domain-isolation`.

## Compatibilidade

WWN mantém o corpus/index mecânico existente. SWN, AWN e CWN permanecem bloqueados para regras específicas enquanto seus corpora próprios não forem homologados, evitando invenção ou vazamento de regras WWN.
