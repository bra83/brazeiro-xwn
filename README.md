# Braseiro XWN — WWN 1.5.0 WORLD LIVE

Versão web jogável baseada na vertical slice 1.0.0, ampliada com mundo vivo, identidade visual persistente, consulta de regras indexada, fala→texto e Audio V2.

## O que funciona nesta build

- Atlas regional flat-top de 37 hexes, 6 milhas por hex.
- Biblioteca visual com 30 variações PNG flat-top 224×194 derivadas dos tiles do acervo.
- Movimento adjacente, fog, exploração, viagem, clima, encontros e combate determinístico.
- Mundo vivo: NPCs com localização, agenda, memória, deslocamento offscreen; mutações de locais; relógios públicos/secretos; turnos de facções.
- Tokens persistentes: jogador e NPCs presentes aparecem no topo; clicar permite escolher imagem do dispositivo; o token é ligado ao ID da entidade e volta quando ela reaparece.
- Continuidade visual: descrição canônica por entidade e exportador de pacote Gemini com prompt + tokens anexados + histórico visual recente.
- Regras indexadas: 94 páginas mecânicas do WWN SRD embutidas para busca offline com número de página e trecho-fonte.
- Canal azul protegido: consulta de regra audita e preserva hora, posição, narrativa, diário e estado do mundo.
- Fala→texto em ambos os campos, quando o navegador oferece SpeechRecognition/webkitSpeechRecognition.
- AudioEngineV2: TTS PT-BR segmentado, velocidade/volume, parar fala e ducking de ambiência procedural durante a narração.
- Save/import/export JSON preservando mundo, NPCs, tokens e histórico visual.

## Abrir

Abra `index.html` no Chrome/Edge. Em Android, Chrome oferece a melhor chance de suporte a fala→texto. O navegador pedirá permissão de microfone na primeira utilização quando suportado.

## Regras

O índice local desta build deriva do `WorldsWithoutNumber_SRD_1.0.pdf`, 94 páginas de conteúdo mecânico indexável. A resposta rápida em PT-BR é complementada por fontes locais do texto original e não deve alterar o estado ficcional.

## Identidade visual / Gemini

`Imagem Gemini` cria um JSON `braseiro.visual-prompt.v1` contendo o prompt da cena, entidades presentes, descrições canônicas, histórico visual e até quatro tokens personalizados em data URL. A integração posterior pode enviar esses tokens como imagens de referência em vez de depender somente do texto.

## PWA / celular

A pasta já inclui `manifest.webmanifest` e `sw.js`. Quando hospedada em HTTPS (por exemplo, GitHub Pages), pode ser instalada pela opção **Adicionar à tela inicial / Instalar app** do navegador e continua disponível offline após o primeiro carregamento. O microfone/fala→texto tende a funcionar de forma mais confiável em origem HTTPS do que abrindo `file://` diretamente.
