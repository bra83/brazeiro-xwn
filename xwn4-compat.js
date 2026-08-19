(function(global){
  'use strict';
  const E=global.XWNEngine,A=global.XWN_ADAPTERS||{};
  if(!E||!E.systemId)throw new Error('xwn4-runtime must load before xwn4-compat');
  const DOMAIN={SWN:{terrain:'space',tile:'assets/domain/space.svg',label:'Setor / espaço local',mph:1,exploreDays:1,encounterDie:8,forage:99,visibility:'sensores',danger:2},CWN:{terrain:'urban',tile:'assets/domain/urban.svg',label:'Distrito urbano',mph:2,exploreDays:1,encounterDie:8,forage:99,visibility:'urbana',danger:2},AWN:{terrain:'wasteland',tile:'assets/domain/wasteland.svg',label:'Ermo pós-apocalíptico',mph:2,exploreDays:1,encounterDie:8,forage:12,visibility:'aberta',danger:3}};
  const oldMake=E.makeInitialState,oldImport=E.importState;
  const merged={...E.TERRAIN};for(const [sys,d] of Object.entries(DOMAIN))merged[d.terrain]={label:d.label,mph:d.mph,exploreDays:d.exploreDays,encounterDie:d.encounterDie,forage:d.forage,visibility:d.visibility,danger:d.danger,css:d.terrain,tile:d.tile,sourceSystem:sys,presentationOnly:true};E.TERRAIN=Object.freeze(merged);

  function storageKey(sys=E.activeSystem()){return `braseiro_xwn_v400_${E.systemId(sys).toLowerCase()}`;}
  try{Object.defineProperty(E,'STORAGE_KEY',{configurable:true,enumerable:true,get(){return storageKey();}});}catch(_){E.STORAGE_KEY=storageKey();}
  E.storageKeyFor=storageKey;

  function addPresentation(state){const sys=E.systemId(state?.campaign?.system);if(sys==='WWN')return state;const d=DOMAIN[sys];if(!d)return state;for(const h of Object.values(state.hexes||{})){h.terrain=d.terrain;h.tile=d.tile;h.road=false;h.presentationTerrain=true;}state.atlas.presentationTile=d.tile;return state;}
  function removePresentation(doc){const sys=E.systemId(doc?.campaign?.system);if(sys==='WWN')return doc;for(const h of Object.values(doc?.hexes||{})){if(h?.presentationTerrain||DOMAIN[sys]?.terrain===h?.terrain){delete h.terrain;delete h.tile;delete h.road;delete h.presentationTerrain;}}return doc;}
  function openingFor(state){
    const sys=E.systemId(state?.campaign?.system),hour=String(state?.campaign?.hour||8).padStart(2,'0'),weather=state?.campaign?.weather||'',h=state?.hexes?.['0,0'];
    if(sys==='WWN')return [
      `Dorsa já está acordada quando você percebe que o dia não vai começar esperando por você. Às ${hour}:00, ${weather.toLowerCase()}, a velha ponte de pedra aperta carroças, carregadores e animais num gargalo de vozes baixas, rodas molhadas e madeira batendo nos portões. O cheiro de palha úmida se mistura ao sal que escapa de sacos mal fechados.`,
      `No portão leste, uma carroça carregada está parada fora da fila. O cavalo continua preso, a lona está amarrada e ninguém descarrega nada. Os trabalhadores passam perto o bastante para notar, mas abrem espaço demais ao contorná-la; um deles começa a dizer alguma coisa ao companheiro e desiste quando vê quem está olhando.`,
      `Mara Tessel ocupa a porta da estalagem com uma caneca numa mão e um pano na outra. Ela continua secando a borda enquanto acompanha a ponte, duas mesas lá dentro e a carroça abandonada como se cada uma fosse parte do mesmo problema. Do outro lado da estrada, homens da Companhia do Sal contam volumes sem pressa, mas contam duas vezes.`,
      `Quando a bruma abre por alguns segundos, as colinas a leste aparecem inteiras. A Torre de Cinza, sem telhado, recorta-se acima da mata e some de novo antes que a visão se acostume. Ninguém toca um sino, ninguém anuncia perigo e ninguém lhe entrega um relatório do que está acontecendo; Dorsa simplesmente continua trabalhando em torno de alguma coisa que ainda não se explicou.`,
      `Você está dentro dessa manhã agora. A ponte leva gente para fora, a estalagem reúne quem sabe falar e quem prefere ouvir, e a carroça imóvel continua ocupando espaço num lugar onde tudo o mais tem destino. O mundo já estava em movimento antes de sua chegada, e o que ele significa terá de ser descoberto vivendo nele.`
    ];
    if(sys==='SWN')return [
      `O primeiro sinal de que o sistema não está esperando por você chega antes de qualquer apresentação: luzes de aproximação piscam no casco das naves e rebocadores cortam o vazio em trajetórias tão ensaiadas que ninguém no cais olha para eles. Às ${hour}:00 do ciclo local, o painel da doca repete autorizações enquanto uma fila de cargueiros pequenos avança devagar demais para um porto que deveria estar em rotina.`,
      `Perto do corredor de manutenção, Sen Kade está com metade do corpo dentro de um painel chamuscado de rebocador. Ele puxa um feixe de cabos, olha de relance para o controle de tráfego e volta ao trabalho sem levantar a voz. Duas equipes que esperavam carga mudam de corredor quando agentes de inspeção aparecem na passarela superior.`,
      `Ira Sen recalibra um sensor portátil junto ao cais. O visor devolve linhas verdes sobre o rosto dela e, de tempos em tempos, ela interrompe o ajuste para acompanhar uma nave recém-chegada. Mais adiante, contêineres permanecem lacrados em posições de descarga, como se alguém tivesse decidido que chegar ao porto não significa necessariamente ter permissão para sair dele.`,
      `Nada disso vem acompanhado de uma explicação sobre quem manda, quanto vale o combustível ou que conflito existe além da órbita. Você vê apenas as consequências: inspeções demoradas, pilotos discutindo em voz baixa, contratos abertos em telas e gente que conhece as rotas escolhendo palavras com cuidado. O estado do setor está ali, mas ainda não pertence ao seu conhecimento.`,
      `É nesse movimento que sua viagem começa. Há trabalho, passagem e informação para quem souber onde olhar; há também coisas que ninguém parece disposto a dizer primeiro. O mapa mostra coordenadas. O resto do mundo terá de ser descoberto em cena.`
    ];
    if(sys==='CWN')return [
      `A cidade chega primeiro pelos ruídos, não por um mapa. Às ${hour}:00, ${weather.toLowerCase()}, anúncios luminosos competem com sirenes distantes e o fluxo de pedestres se divide ao redor de uma barreira corporativa montada no meio da avenida. Ninguém para para admirar o neon; quem mora aqui está ocupado demais chegando atrasado a algum lugar.`,
      `No Distrito Zero, entregadores empilham caixas sob uma marquise enquanto drones de trânsito corrigem rotas sobre suas cabeças. Uma loja fecha a grade antes do horário indicado na própria fachada. Do outro lado da rua, um grupo espera junto a um terminal fora de serviço e confere o corredor sempre que um veículo preto reduz a velocidade.`,
      `Você ainda não sabe quais corporações estão em guerra, que gangue controla a próxima quadra ou por que certos preços mudaram esta semana. A cidade não oferece essas respostas como legenda. Ela mostra salários discutidos no balcão, seguranças extras nas portas e pessoas acostumadas a medir distância até uma saída.`,
      `O que existe aqui será confirmado quando você ouvir, observar, negociar ou se arriscar. Até lá, boato permanece boato e infraestrutura permanece apenas aquilo que seus olhos conseguem alcançar. A rua já tinha problemas antes de você entrar nela.`,
      `A sua história começa no meio desse trânsito, sem uma voz de fora explicando o cenário. Há caminhos, pessoas e tensões reais ao redor; decidir quais merecem sua atenção vem depois de sentir a cidade funcionando.`
    ];
    return [
      `O ermo não começa quando você sai do abrigo; ele já estava trabalhando contra tudo ao redor durante a noite. Às ${hour}:00, ${weather.toLowerCase()}, poeira se acumula nas frestas e uma chapa solta bate em algum telhado com intervalos irregulares. Gente acordada cedo separa água, sucata útil e coisas que talvez ainda possam ser consertadas.`,
      `No limite do assentamento, marcas de pneus desaparecem onde a estrada se desfaz. Um carregador improvisado ronca por alguns segundos, falha e volta ao silêncio. Duas pessoas discutem o peso de uma caixa sem abrir a tampa; nenhuma delas parece disposta a desperdiçar energia numa discussão longa.`,
      `Você não recebe uma lista do que aconteceu com as rotas, de quem controla os poços ou de quanto vale comida esta semana. Essas respostas estão nas latas contadas uma a uma, nas armas mantidas perto da mão e no modo como quem chega do horizonte é observado antes de ser cumprimentado.`,
      `Além das últimas estruturas, o terreno muda de cor e engole detalhes rapidamente. Ruínas, fumaça ou movimento podem significar oportunidade, ameaça ou apenas vestígios. O que não foi visto continua desconhecido; o ermo não preenche lacunas para facilitar sua decisão.`,
      `É daqui que a campanha começa: não de um resumo do mundo, mas de um lugar tentando sobreviver enquanto você está nele. O que existe além da borda segura será aprendido passo a passo, com consequências que continuarão acontecendo mesmo quando você não estiver olhando.`
    ];
  }
  E.storyOpening=openingFor;
  E.makeInitialState=function(sys=E.activeSystem()){const state=addPresentation(oldMake(sys));state.narrative=openingFor(state);state.sceneTitle=state.hexes?.['0,0']?.poi?.name||state.hexes?.['0,0']?.systemLabel||'Abertura da campanha';if(state.barbara){state.barbara.started=false;state.barbara.lastOccasion='campaign_opening';state.barbara.discovery={};}return state;};
  E.importState=function(raw){let doc=typeof raw==='string'?JSON.parse(raw):JSON.parse(JSON.stringify(raw));doc=removePresentation(doc);return addPresentation(oldImport(doc));};
  E.exportState=function(state){const copy=JSON.parse(JSON.stringify(state));removePresentation(copy);copy.version=E.VERSION;return JSON.stringify(copy,null,2);};
  E.addPresentationFields=addPresentation;E.removePresentationFields=removePresentation;
  E.auditState=function(state){const sys=E.systemId(state?.campaign?.system),errors=[];if(state?.version!==E.VERSION)errors.push('version');if(state?.system?.id!==sys)errors.push('system.id');if(state?.rules?.systemId!==sys)errors.push('rules.systemId');if(sys!=='WWN'){const d=DOMAIN[sys];for(const h of Object.values(state?.hexes||{})){if(h.sourceSystem!==sys)errors.push(`hex owner mismatch ${h.key}`);if(h.road)errors.push(`road leak ${h.key}`);if(h.terrain!==d.terrain||h.tile!==d.tile)errors.push(`presentation domain mismatch ${h.key}`);if(h.poi&&h.key!=='0,0'&&['settlement','farm','site','ruin','fort','hazard','landmark','water'].includes(h.poi.kind))errors.push(`fantasy poi leak ${h.key}`);}}if(!state?.player||!state?.hexes||!state?.campaign||!state?.continuity||!state?.world)errors.push('missing_core_state');return {ok:!errors.length,system:sys,rulesReady:E.rulesReady(state),errors};};
  E.DOMAIN_PRESENTATION=Object.freeze(DOMAIN);
  if(typeof module!=='undefined'&&module.exports)module.exports=E;
})(typeof window!=='undefined'?window:globalThis);
