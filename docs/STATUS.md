# Status

Versão: 1.0.0

O núcleo Barbara 1.0 está em fechamento de release sobre a árvore reconstruída que substituiu o conteúdo XWN no `main`. O conteúdo anterior permanece recuperável no branch `backup-xwn-pre-barbara`.

Os itens que este arquivo listava como pendentes no `rc1` foram implementados: provider Gemini real, RAG SQLite persistente/híbrido, adapters com perfis mecânicos explícitos e bateria integrada de campanha longa.

A matriz normativa de aceitação está em `docs/RELEASE_1_0_ACCEPTANCE.md`. O critério de fechamento é: zero requisito obrigatório `PARCIAL/AUSENTE`, suíte `pytest` verde, wheel construída e smoke test em instalação limpa verde. A homologação Gemini live permanece dependente de credencial/cota externa, mas o provider e seu workflow estão implementados.
