# BRASEIRO XWN — Worlds Without Number 3.0 · MESA VIVA

Versão web jogável do motor universal XWN, com foco nesta build em **Worlds Without Number**. A 3.0 substitui a tela-protótipo da 1.5 por uma mesa ao vivo enxuta e herda contratos já maduros dos projetos Braseiro.

## Mesa ao vivo

A aba **Jogo** contém somente o que precisa permanecer na frente do jogador durante a sessão: faixa persistente de personagens/NPCs presentes, atlas, narração do Mestre, imagem da cena, resolução mecânica recolhível, sugestões, Ação/Fala com microfone e acesso rápido à caixa azul de regras.

Ficha, Diário, Regras, Mundo Vivo/Facções, Som e Configuração ficam em abas separadas.

## Atlas 3.0

- 61 hexes flat-top (raio 4), 6 milhas por hex.
- 30 tiles `224×194` em `assets/hex_full/`, recortados para preencher a célula hexagonal inteira.
- estrada só é desenhada quando há conexão topológica com outro hex de estrada já conhecido; um único segmento só pode terminar em um POI compatível.
- marcador do jogador usa o próprio token persistente, com anel/beacon e ponteiro triangular; o losango amarelo antigo foi removido.
- fog **enter-only**: viajar ou explorar revela apenas o hex efetivamente alcançado. O anel vizinho continua desconhecido.
- POIs, estradas e informações não são revelados através da névoa.

## Interface por período do dia

O tema acompanha o relógio ficcional e recalcula fundo, superfícies, fonte, bordas e acentos:

- manhã: azul claro;
- tarde: azul profundo;
- noite: cinza escuro;
- madrugada: preto/quase preto.

## Mestre / Actual Play

O motor local trabalha em beats de 1–4 parágrafos e o refinador opcional do Gemini recebe somente fatos já decididos pelo engine. A direção foi consolidada a partir dos estudos Actual Play dos projetos Braseiro e dos serviços recuperados do Forbidden Lands 3.2:

- panorama → aproximação → atividade atual → detalhe/limiar;
- mundo já estava em movimento antes da chegada;
- NPC entra fazendo algo e possui conhecimento limitado;
- rumor não vira verdade automaticamente;
- rotina/rota conhecida pode ser comprimida quando nada mudou;
- viagem volta a ganhar detalhe quando clima, recurso, ameaça ou estado criam nova decisão;
- ameaça aparece primeiro por sinais perceptíveis;
- a narração para na primeira incerteza significativa;
- teste somente quando há incerteza, risco e consequência;
- falha cobra tempo, exposição, posição ou complicação em vez de bloquear a aventura;
- regras/números ficam fora da prosa do Mestre;
- o Mestre não controla o personagem do jogador.

O perfil está documentado em `NARRATIVE_ACTUAL_PLAY_PROFILE.json` e `HERANCA_FORBIDDEN_LANDS_3.2.md`.

## Continuidade e mundo vivo

A 3.0 mantém em estado canônico separado da apresentação:

- `actionLedger`: fatos explícitos declarados pelo jogador;
- `familiarRoutes`: cache de rotas efetivamente percorridas;
- `sessionResume`: último fato canônico de retomada;
- `immutableFacts`: fatos que a narração não pode contradizer;
- localização/agendas/memória dos NPCs;
- `secretLedger`: movimento que ocorre fora da percepção do personagem;
- `siteMutations`: locais explorados podem mudar com a passagem do tempo;
- relógios públicos/secretos;
- proveniência/confiança dos rumores;
- `factionTraffic`: turno estratégico separado do movimento diário do mundo.

## Reação, Moral, Instinto e Facções

- Reação: 2d6 + CAR aplicável; a atitude é mostrada antes de o jogador agir.
- conversa básica/parley não exige teste social.
- Moral: 2d6 > Moral causa falha e tentativa de abandonar a luta.
- Instinto: 1d10 ≤ Instinto produz ação impulsiva/subótima; PCs nunca rolam Instinto.
- Facções: iniciativa d8, renda e check oposto d10 + atributo, com sucesso do atacante apenas se superar o defensor.

A fonte textual continua pesquisável no índice offline de 94 páginas mecânicas do WWN SRD.

## Gemini — imagem da cena

O botão **✦ Imagem** monta um prompt restrito ao que é perceptível na cena e inclui as identidades visuais dos presentes.

- tokens personalizados são anexados como imagens de referência quando o Web Share API permite;
- em Android, há tentativa de encaminhar o texto diretamente ao app Gemini, com fallback para compartilhamento/web;
- o prompt também é copiado para a área de transferência;
- quando o Braseiro estiver instalado como PWA, o `share_target` aceita uma imagem compartilhada de volta e a coloca automaticamente no quadro da cena;
- há importação manual de imagem como fallback.

## Tokens persistentes

O token é ligado ao ID canônico (`player`, `mara`, `del`, etc.), não à cena. Se o NPC sair, passar dias fora e reaparecer, continua com a mesma imagem e descrição visual. Export/import preserva essa identidade.

## Áudio — herança Forbidden Lands 3.2

`audioEngineV2.js` porta o desenho web do motor rápido recuperado do projeto anexado:

- voz Charon;
- cadeia TTS `gemini-3.1-flash-tts-preview` → `gemini-2.5-flash-preview-tts`;
- primeiro trecho curto (até 320 caracteres) e seguintes até 680;
- síntese do trecho seguinte durante a reprodução do atual;
- cache local;
- sessões canceláveis;
- WebAudio + fallback de PCM cru 24 kHz;
- ducking da ambiência durante a fala;
- navegador/Android permanece como provedor manual alternativo.

## Regras / caixa azul

Consulta indexada do WWN SRD é um canal protegido: não avança tempo, posição, RNG, narrativa, diário, encontro, combate, NPCs, facções ou mundo vivo. Se a regra não for encontrada, o sistema não deve inventá-la.

## Testes

Execute:

```bash
node tests/test_engine.js
```

A suíte 3.0 audita motor, fog, continuidade, reação/moral/instinto, facções, tokens/Gemini, regras, migração, temas, UI, áudio e share target.
