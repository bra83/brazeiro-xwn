(function (global) {
  'use strict';

  const VERSION = '3.0.0';
  const STORAGE_KEY = 'braseiro_xwn_wwn_v300';
  const HEX_RADIUS = 4;
  const AXIAL_DIRS = [
    { q: 1, r: 0 }, { q: 1, r: -1 }, { q: 0, r: -1 },
    { q: -1, r: 0 }, { q: -1, r: 1 }, { q: 0, r: 1 }
  ];

  const DIFFICULTIES = Object.freeze({ routine: 6, competent: 8, hard: 10, master: 12, legendary: 14 });
  const TERRAIN = Object.freeze({
    plains: { label: 'Planície', mph: 3, exploreDays: 1, encounterDie: 8, forage: 8, visibility: 'longa', danger: 1, css: 'plains', tile: 'assets/terrain/plains_lush.png' },
    farmland: { label: 'Campos cultivados', mph: 3, exploreDays: 1, encounterDie: 10, forage: 6, visibility: 'longa', danger: 1, css: 'farmland', tile: 'assets/terrain/farmland.png' },
    forest: { label: 'Floresta leve', mph: 2, exploreDays: 1, encounterDie: 8, forage: 7, visibility: 'média', danger: 2, css: 'forest', tile: 'assets/terrain/forest_lush.png' },
    dense_forest: { label: 'Floresta densa', mph: 1.5, exploreDays: 2, encounterDie: 6, forage: 8, visibility: 'curta', danger: 3, css: 'dense-forest', tile: 'assets/terrain/forest_lush.png' },
    hills: { label: 'Colinas acidentadas', mph: 1.5, exploreDays: 2, encounterDie: 6, forage: 9, visibility: 'longa nas cristas', danger: 2, css: 'hills', tile: 'assets/terrain/hills_lush.png' },
    mountains: { label: 'Montanhas', mph: 0.5, exploreDays: 2, encounterDie: 6, forage: 10, visibility: 'variável', danger: 4, css: 'mountains', tile: 'assets/terrain/mountains_lush.png' },
    swamp: { label: 'Pântano', mph: 1, exploreDays: 2, encounterDie: 6, forage: 10, visibility: 'curta', danger: 4, css: 'swamp', tile: 'assets/terrain/swamp.png' },
    water: { label: 'Águas rasas', mph: 1, exploreDays: 2, encounterDie: 8, forage: 9, visibility: 'aberta', danger: 3, css: 'water', tile: 'assets/terrain/water.png' }
  });

  const HEX_VARIANTS = Object.freeze({
    plains: ['plains_lush','plains_dry','plains_autumn','plains_dusk','plains_pale'],
    farmland: ['farmland_green','farmland_harvested','farmland_fallow','farmland_wet'],
    forest: ['forest_mixed','forest_autumn','forest_mist'],
    dense_forest: ['forest_dark','forest_dead','forest_mixed'],
    hills: ['hills_lush','hills_dry','hills_autumn','hills_stony'],
    mountains: ['mountains_green','mountains_bare','mountains_snow','mountains_storm'],
    swamp: ['swamp_green','swamp_blackwater','swamp_pale','swamp_murky'],
    water: ['water_still','water_deep','water_pale','water_storm']
  });

  function tileVariantFor(terrain,q,r) {
    const variants=HEX_VARIANTS[terrain] || [];
    if(!variants.length) return TERRAIN[terrain]?.tile || '';
    const id=variants[hashString(`${terrain}:${q},${r}`)%variants.length];
    return `assets/hex_full/${id}.png`;
  }

  const POIS = Object.freeze({
    '0,0': { name: 'Dorsa', kind: 'settlement', icon: '⌂', summary: 'Uma aldeia murada em torno de uma velha ponte de pedra.', public: true },
    '1,0': { name: 'Bosque das Lanternas', kind: 'site', icon: '✦', summary: 'Luzes amarelas aparecem entre os troncos depois do crepúsculo.' },
    '1,-1': { name: 'Torre de Cinza', kind: 'ruin', icon: 'tower', image: 'assets/poi/tower.png', summary: 'Uma torre sem telhado vigia o vale como um dente escurecido.', forcedEncounter: 'ash_scout' },
    '0,-1': { name: 'Campos de Rill', kind: 'farm', icon: '♜', summary: 'Terra fértil cortada por valas e pequenas propriedades abandonadas.' },
    '-1,0': { name: 'Brejo do Vidro', kind: 'hazard', icon: '≈', summary: 'Água rasa, limo cinzento e reflexos que não acompanham o céu.' },
    '-1,1': { name: 'Cemitério dos Peregrinos', kind: 'ruin', icon: 'cemetery', image: 'assets/poi/cemetery.png', summary: 'Lápides inclinadas cercam uma capela sem portas.', forcedEncounter: 'grave_robber' },
    '0,1': { name: 'Marco Quebrado', kind: 'landmark', icon: '◆', summary: 'Um marco de estrada partido, coberto por inscrições quase apagadas.' },
    '2,-1': { name: 'Passo do Corvo', kind: 'landmark', icon: '▲', summary: 'A única passagem segura por uma serra de pedra negra.' },
    '2,-2': { name: 'Mosteiro Afundado', kind: 'ruin', icon: '✚', summary: 'Telhados de ardósia emergem de uma depressão tomada pela mata.' },
    '-2,1': { name: 'Poço das Vozes', kind: 'site', icon: '◉', summary: 'Um poço circular de pedra no meio do brejo; ecos respondem antes da pergunta.' },
    '-2,2': { name: 'Lago de Orne', kind: 'water', icon: '≈', summary: 'Água escura e imóvel, cercada por salgueiros baixos.' },
    '1,1': { name: 'Pedreira Velha', kind: 'site', icon: '◇', summary: 'Cortes retos na rocha e guindastes de madeira abandonados.' },
    '2,0': { name: 'Muralha dos Três Reis', kind: 'landmark', icon: '▦', summary: 'Trechos de muralha ciclópica seguem a crista das colinas.' },
    '-1,-1': { name: 'Casa do Salgueiro', kind: 'site', icon: '⌂', summary: 'Uma casa isolada continua soltando fumaça apesar da estrada ter sumido.' },
    '4,-2': { name: 'Monólitos Brancos', kind: 'landmark', icon: '▥', summary: 'Três pedras claras erguem-se acima do mato; nenhuma face aponta para a mesma direção.' },
    '3,1': { name: 'Forte Escavado', kind: 'ruin', icon: '▦', summary: 'Um terrapleno antigo acompanha a encosta, com paliçadas novas misturadas à pedra velha.' },
    '-4,2': { name: 'Poço de Turfa', kind: 'hazard', icon: '◉', summary: 'Uma depressão negra guarda água imóvel e tábuas afundadas de uma passagem esquecida.' },
    '-2,4': { name: 'Ilha do Sino', kind: 'site', icon: '✚', summary: 'Uma ilhota baixa sustenta as ruínas de um campanário que não deveria ter sobrevivido à água.' },
    '1,3': { name: 'Solar de Venn', kind: 'site', icon: '⌂', summary: 'Muros de pedra cercam um solar rural quase escondido por árvores antigas.' },
    '-3,-1': { name: 'Bosque Queimado', kind: 'hazard', icon: '♨', summary: 'Troncos negros permanecem de pé onde o fogo morreu há anos, mas o solo ainda cheira a cinza depois da chuva.' }
  });

  const ENEMIES = Object.freeze({
    ash_scout: { id: 'ash_scout', name: 'Batedor da Cinza', hp: 6, ac: 13, ab: 1, damage: '1d6', morale: 7, instinct: 2, shock: 2, shockAC: 13 },
    grave_robber: { id: 'grave_robber', name: 'Saqueador de Túmulos', hp: 5, ac: 12, ab: 1, damage: '1d6', morale: 6, instinct: 4, shock: 1, shockAC: 13 },
    marsh_hound: { id: 'marsh_hound', name: 'Cão do Brejo', hp: 4, ac: 12, ab: 1, damage: '1d4', morale: 7, instinct: 5, shock: 1, shockAC: 12 },
    road_bandit: { id: 'road_bandit', name: 'Bandido da Estrada', hp: 5, ac: 13, ab: 1, damage: '1d6', morale: 6, instinct: 4, shock: 2, shockAC: 13 }
  });

  function key(q, r) { return `${q},${r}`; }
  function clone(v) { return JSON.parse(JSON.stringify(v)); }
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

  function attrMod(score) {
    if (score <= 3) return -2;
    if (score <= 7) return -1;
    if (score <= 13) return 0;
    if (score <= 17) return 1;
    return 2;
  }

  function hashString(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function nextRandom(state) {
    const x = Math.sin((state.seed + state.rngCursor * 9301) * 0.0174533) * 10000;
    state.rngCursor += 1;
    return x - Math.floor(x);
  }

  function rollDie(state, sides) { return 1 + Math.floor(nextRandom(state) * sides); }
  function rollDice(state, count, sides) {
    const rolls = [];
    for (let i = 0; i < count; i++) rolls.push(rollDie(state, sides));
    return { rolls, total: rolls.reduce((a, b) => a + b, 0) };
  }

  function parseDie(expr, state) {
    const m = String(expr).match(/(\d+)d(\d+)(?:\s*([+-])\s*(\d+))?/i);
    if (!m) return { total: 0, rolls: [] };
    const count = Number(m[1]), sides = Number(m[2]);
    const base = rollDice(state, count, sides);
    const mod = m[3] ? (m[3] === '+' ? 1 : -1) * Number(m[4]) : 0;
    return { total: base.total + mod, rolls: base.rolls, mod };
  }

  function axialDistance(a, b) {
    const aq = a.q, ar = a.r, as = -aq - ar;
    const bq = b.q, br = b.r, bs = -bq - br;
    return (Math.abs(aq - bq) + Math.abs(ar - br) + Math.abs(as - bs)) / 2;
  }

  function isAdjacent(a, b) { return axialDistance(a, b) === 1; }

  function terrainFor(q, r) {
    const k = key(q, r);
    const explicit = {
      '0,0': 'farmland', '1,0': 'forest', '1,-1': 'hills', '0,-1': 'farmland', '-1,0': 'swamp', '-1,1': 'plains', '0,1': 'plains',
      '2,-1': 'mountains', '2,-2': 'dense_forest', '-2,1': 'swamp', '-2,2': 'water', '1,1': 'hills', '2,0': 'hills', '-1,-1': 'forest',
      '3,-1': 'mountains', '3,-2': 'mountains', '3,-3': 'mountains', '2,-3': 'dense_forest', '1,-3': 'dense_forest', '0,-3': 'forest',
      '-1,-2': 'forest', '-2,-1': 'swamp', '-3,0': 'swamp', '-3,1': 'swamp', '-3,2': 'water', '-3,3': 'water', '-2,3': 'water',
      '-1,3': 'plains', '0,3': 'plains', '1,2': 'farmland', '2,1': 'hills', '3,0': 'mountains', '0,2': 'farmland', '-1,2': 'plains',
      '-2,0': 'swamp', '0,-2': 'forest', '1,-2': 'forest', '-2,2': 'water'
    };
    if (explicit[k]) return explicit[k];
    // O anel externo usa biomas determinísticos para evitar uma borda monótona de planície.
    const n = hashString(`biome:${q},${r}`) % 100;
    if (q >= 3) return n < 58 ? 'mountains' : 'hills';
    if (r <= -3) return n < 55 ? 'dense_forest' : 'forest';
    if (q <= -3) return n < 52 ? 'swamp' : (n < 72 ? 'water' : 'plains');
    if (r >= 3) return n < 42 ? 'water' : (n < 72 ? 'plains' : 'farmland');
    return n < 22 ? 'forest' : n < 40 ? 'hills' : n < 54 ? 'farmland' : n < 66 ? 'swamp' : 'plains';
  }

  function roadFor(q, r) {
    // Rotas existem como topologia, não como um risco decorativo solto.
    const roadKeys = new Set([
      '-4,2','-3,1','-2,0','-1,0','0,0','1,0','2,0','3,0','3,1',
      '-1,1','0,1','0,-1','1,-1','2,-1','3,-1','4,-2',
      '1,1','1,2','1,3'
    ]);
    return roadKeys.has(key(q, r));
  }

  function roadConnections(state, hex) {
    if (!hex || !hex.road) return [];
    const out=[];
    AXIAL_DIRS.forEach((d,i)=>{
      const other=state.hexes[key(hex.q+d.q,hex.r+d.r)];
      if (other && other.road) out.push(i);
    });
    return out;
  }

  function generateHexes() {
    const out = {};
    for (let q = -HEX_RADIUS; q <= HEX_RADIUS; q++) {
      const r1 = Math.max(-HEX_RADIUS, -q - HEX_RADIUS);
      const r2 = Math.min(HEX_RADIUS, -q + HEX_RADIUS);
      for (let r = r1; r <= r2; r++) {
        const k = key(q, r);
        out[k] = {
          q, r, key: k,
          terrain: terrainFor(q, r),
          tile: tileVariantFor(terrainFor(q,r),q,r),
          road: roadFor(q, r),
          discovered: k === '0,0',
          explored: k === '0,0',
          visited: k === '0,0',
          visitCount: k === '0,0' ? 1 : 0,
          discoverySource: k === '0,0' ? 'campaign-start' : null,
          poi: POIS[k] ? clone(POIS[k]) : null,
          notes: []
        };
      }
    }
    return out;
  }

  function makeInitialState() {
    const playerAttrs = { str: 10, dex: 14, con: 12, int: 13, wis: 14, cha: 9 };
    const state = {
      schema: 1,
      version: VERSION,
      seed: hashString('DORSA-V010'),
      rngCursor: 1,
      campaign: { name: 'As Marchas de Orne', system: 'WWN', day: 1, hour: 8, weather: 'Bruma fria', season: 'Outono', worldTurn: 0 },
      atlas: { id: 'orne-r4', orientation: 'flat', radius: 4, hexMiles: 6, source: 'acervo-compartilhado', fogPolicy: 'enter-only-v2' },
      current: { q: 0, r: 0 },
      selected: { q: 0, r: 0 },
      hexes: generateHexes(),
      player: {
        name: 'Elian Vargo', level: 1, className: 'Expert', hp: 6, maxHp: 6, ac: 13, attackBonus: 0,
        attrs: playerAttrs,
        mods: Object.fromEntries(Object.entries(playerAttrs).map(([k, v]) => [k, attrMod(v)])),
        skills: { notice: 1, survive: 1, connect: 0, sneak: 0, exert: 0, stab: 0, shoot: -1, heal: 0, know: 0, convince: 0 },
        weapon: { name: 'Espada curta', damage: '1d6', skill: 'stab', attr: 'dex', shock: 2, shockAC: 13 },
        inventory: ['Espada curta', 'Arco curto', 'Mochila', '2 dias de comida', 'Odre', 'Pederneira'],
        systemStrain: 0, condition: 'Apto', frail: false, mortallyWounded: false,
        visualDescriptor: 'homem humano adulto, explorador cuidadoso, rosto anguloso, cabelo castanho escuro curto, manto verde-musgo gasto, espada curta e mochila de viagem'
      },
      factions: [
        { id: 'salt', name: 'Companhia do Sal', force: 2, cunning: 1, wealth: 3, power: 2, location: '0,0', goal: 'Controlar a ponte de Dorsa', progress: 0, clock: 6, known: true, treasure: 4, magic: 'none' },
        { id: 'bell', name: 'Irmãos do Sino', force: 1, cunning: 2, wealth: 1, power: 1, location: '-1,1', goal: 'Recuperar uma relíquia perdida', progress: 0, clock: 5, known: true, treasure: 2, magic: 'low' },
        { id: 'ash', name: 'Vigias da Cinza', force: 2, cunning: 2, wealth: 1, power: 2, location: '2,-1', goal: 'Abrir o Passo do Corvo', progress: 0, clock: 7, known: false, treasure: 3, magic: 'low' },
        { id: 'reed', name: 'Casa dos Juncos', force: 1, cunning: 3, wealth: 2, power: 2, location: '-2,1', goal: 'Controlar as passagens do Brejo do Vidro', progress: 0, clock: 6, known: false, treasure: 3, magic: 'none' },
        { id: 'crown', name: 'Cartógrafos da Coroa', force: 1, cunning: 2, wealth: 3, power: 2, location: '0,0', goal: 'Mapear as Marchas antes da chegada de um novo intendente', progress: 1, clock: 8, known: true, treasure: 5, magic: 'low' }
      ],
      npcs: {
        mara: { id:'mara', name: 'Mara Tessel', role: 'estalajadeira', disposition: 1, home:'0,0', location:'0,0', schedule:['0,0'], agenda:'manter a estalagem segura e descobrir por que a Companhia do Sal pressiona os carroceiros', activity:'secar uma caneca com um pano enquanto escuta a conversa de duas mesas ao mesmo tempo', alive:true, lastSeenDay:1, memory:[], visualDescriptor:'mulher humana de meia-idade, cabelo ruivo-escuro preso, sardas, avental de couro sobre roupa vinho, olhar atento e postura prática', knows: ['A Torre de Cinza voltou a mostrar luz à noite.', 'Dois carregadores sumiram no Marco Quebrado.'] },
        del: { id:'del', name: 'Irmão Del', role: 'escriba itinerante', disposition: 0, home:'0,0', location:'0,0', schedule:['0,0','-1,1','-1,1','0,0','1,-1'], agenda:'copiar inscrições antigas e descobrir a origem do sino enterrado', activity:'comparar duas folhas de pergaminho e riscar diferenças com carvão', alive:true, lastSeenDay:1, memory:[], visualDescriptor:'homem humano de trinta e poucos anos, magro, cabelo preto ondulado, barba curta, capuz cinza, bolsa de pergaminhos e dedos manchados de tinta', knows: ['O cemitério é mais antigo que Dorsa.', 'Há marcas novas na pedra do Passo do Corvo.'] },
        selka: { id:'selka', name:'Selka Venn', role:'batedora da ponte', disposition:0, home:'0,0', location:'1,0', schedule:['1,0','1,0','0,0','1,0','1,-1'], agenda:'mapear movimentos de estranhos sem revelar quem a paga', activity:'afiar uma flecha enquanto observa quem atravessa a ponte', alive:true, lastSeenDay:null, memory:[], visualDescriptor:'mulher humana jovem, pele morena, trança preta longa, capa marrom curta, arco simples, cicatriz fina na sobrancelha direita', knows:['A mata ao leste tem marcas de fogueiras recentes.', 'A estrada para o Passo do Corvo está sendo observada.'] },
        arven: { id:'arven', name:'Arven Lo', role:'carroceiro de sal', disposition:0, home:'0,0', location:'0,0', schedule:['0,0','0,-1','1,-1','0,0'], agenda:'encontrar o irmão desaparecido sem perder o contrato da Companhia', activity:'reapertar uma correia de couro na carroça, olhando mais para a estrada do que para o trabalho', alive:true, lastSeenDay:1, memory:[], visualDescriptor:'homem humano robusto, quarenta anos, barba curta grisalha, casaco azul desbotado, mãos rachadas de sal', knows:['Uma carroça voltou vazia da estrada norte.', 'Os homens da Companhia perguntam demais sobre quem sai de Dorsa.'] },
        nera: { id:'nera', name:'Nera Voss', role:'curandeira', disposition:1, home:'0,0', location:'0,0', schedule:['0,0','0,0','-1,1','0,0'], agenda:'repor ervas e descobrir a origem de uma febre que apareceu nos viajantes do sul', activity:'separar folhas secas sobre um pano, descartando as que escureceram nas bordas', alive:true, lastSeenDay:1, memory:[], visualDescriptor:'mulher humana idosa, cabelo branco curto, pele morena, xale azul acinzentado, bolsa de ervas presa à cintura', knows:['A água do Brejo do Vidro deixou dois viajantes febris.', 'Irmão Del perguntou por inscrições anteriores à ponte.'] },
        torren: { id:'torren', name:'Torren de Rill', role:'lavrador', disposition:0, home:'0,-1', location:'0,-1', schedule:['0,-1','0,-1','0,0','0,-1'], agenda:'impedir que a terra da família seja comprada por atravessadores', activity:'limpar barro de uma enxada com a lâmina de uma faca', alive:true, lastSeenDay:null, memory:[], visualDescriptor:'homem humano jovem, cabelo louro queimado de sol, camisa de linho cru, botas cobertas de barro', knows:['Há pegadas recentes cruzando as valas durante a noite.', 'Alguém tem comprado grãos por preço alto demais para ser normal.'] },
        vey: { id:'vey', name:'Vey Sarto', role:'mercadora itinerante', disposition:0, home:'0,0', location:'-1,1', schedule:['-1,1','0,0','1,0','0,0'], agenda:'vender mapas incompletos sem admitir de onde vieram', activity:'recontar pequenas moedas sobre uma caixa fechada', alive:true, lastSeenDay:null, memory:[], visualDescriptor:'mulher humana de trinta anos, cabelo castanho raspado de um lado, casaco cinza claro, anéis de cobre, sorriso rápido', knows:['O Marco Quebrado tem uma inscrição que não aparece em cópias antigas.', 'Uma trilha de caçadores evita o Bosque das Lanternas.'] }
      },
      visual: { tokens: {}, sceneHistory: [], geminiExports: 0 },
      continuity: {
        actionLedger: [],
        familiarRoutes: {},
        sessionResume: {day:1,hour:8,hex:'0,0',summary:'A campanha começou em Dorsa.'},
        locationRecaps: {},
        immutableFacts: [{id:'campaign-start',day:1,hour:8,fact:'Elian Vargo está em Dorsa no início da campanha.',source:'engine'}]
      },
      world: {
        lastProcessedDay: 1,
        publicEvents: [],
        secretLedger: [],
        factionTraffic: [],
        siteMutations: [],
        rumorConfidence: {},
        clocks: [
          {id:'salt_bridge',label:'Pressão sobre a Ponte',value:1,max:6,public:true},
          {id:'bell_relic',label:'Busca pela relíquia',value:0,max:5,public:false},
          {id:'ash_pass',label:'Abertura do Passo',value:1,max:7,public:false}
        ]
      },
      journal: [],
      rumors: [],
      pendingActions: [],
      combat: null,
      encounter: null,
      lastMechanics: '',
      lastRuleAnswer: '',
      sceneTitle: 'A estrada para fora de Dorsa',
      narrative: []
    };
    addJournal(state, 'campanha', 'A campanha começou em Dorsa, ao amanhecer do primeiro dia.');
    state.narrative = openingScene(state);
    return state;
  }

  function nowLabel(state) {
    return `Dia ${state.campaign.day}, ${String(state.campaign.hour).padStart(2, '0')}:00`;
  }

  function addJournal(state, type, text) {
    state.journal.unshift({ id: `${Date.now()}-${state.journal.length}`, type, when: nowLabel(state), text });
    if (state.journal.length > 200) state.journal.length = 200;
  }

  function periodOfDay(hour) {
    const h=((Number(hour)||0)%24+24)%24;
    if (h < 5) return 'dawn';
    if (h < 12) return 'morning';
    if (h < 18) return 'afternoon';
    return 'night';
  }

  function timePhrase(state) {
    const p=periodOfDay(state.campaign.hour);
    return p==='dawn' ? 'na madrugada, quando até os ruídos pequenos parecem próximos demais'
      : p==='morning' ? 'sob a luz fria da manhã'
      : p==='afternoon' ? 'com a tarde já pesando sobre a estrada'
      : 'depois que a noite engoliu as distâncias';
  }

  const TERRAIN_FICTION = Object.freeze({
    plains:{approach:'O terreno se abre em ondulações de capim e terra baixa, oferecendo distância aos olhos e pouca coisa onde desaparecer.',sound:'O vento corre sem obstáculo e traz sons de muito longe, deformados pela distância.',detail:'Pegadas permanecem legíveis nos trechos de solo úmido, mas o campo aberto cobra de quem prefere não ser visto.'},
    farmland:{approach:'Valas de drenagem, cercas baixas e árvores antigas dividem a terra em propriedades longas e irregulares.',sound:'Há madeira batendo ao longe, um animal preso em algum cercado e o rumor de trabalho que nunca chega a ficar completamente silencioso.',detail:'Alguns campos estão bem cuidados; outros mostram fileiras abandonadas no meio da estação, como se faltassem mãos.'},
    forest:{approach:'As copas se aproximam da estrada e quebram a luz em faixas estreitas sobre folhas velhas e raízes expostas.',sound:'Pássaros se calam por trechos, depois recomeçam todos de uma vez em outro ponto da mata.',detail:'O chão oferece rastros demais: animais, botas antigas, galhos partidos e marcas que só ganham sentido quando comparadas.'},
    dense_forest:{approach:'A mata fecha o horizonte e transforma cada poucos passos numa nova parede de troncos, samambaias e sombra.',sound:'O vento quase não chega ao chão; o que se ouve são folhas roçando, madeira estalando e respirações que parecem altas demais.',detail:'Aqui uma trilha pode existir a cinco metros e continuar invisível até que alguém atravesse exatamente o ângulo certo.'},
    hills:{approach:'O chão sobe em lombadas de pedra e capim curto. Cada crista entrega uma vista e cobra a exposição de quem a alcança.',sound:'Pedrinhas soltas denunciam movimento antes que uma silhueta apareça contra o céu.',detail:'As depressões entre colinas escondem caminhos, fumaça e gente com a mesma facilidade com que escondem água.'},
    mountains:{approach:'A pedra começa a decidir a rota. Paredões, fendas e cascalho empurram o caminho para passagens estreitas.',sound:'O vento assobia em rachaduras e devolve ecos curtos, difíceis de localizar.',detail:'Um erro de direção aqui custa mais do que distância; custa altura, fôlego e horas de retorno.'},
    swamp:{approach:'A água ocupa o caminho em lâminas escuras e o solo firme surge em ilhas pequenas, cobertas por junco e lama.',sound:'Insetos, água mexida e o estalo ocasional de alguma coisa sob a superfície impedem o silêncio completo.',detail:'Nem toda marca na água aponta para quem a fez; corrente fraca e barro mole torcem rastros em poucos minutos.'},
    water:{approach:'A margem baixa cede sob as botas e a água quase imóvel reflete um céu sempre um pouco mais escuro.',sound:'O som viaja pela superfície: um remo distante, uma ave levantando voo, alguma coisa tocando a margem fora de vista.',detail:'A linha d’água guarda restos trazidos de longe e apaga depressa aquilo que aconteceu perto demais dela.'}
  });

  function openingScene(state) {
    const mara=state && state.npcs ? state.npcs.mara : null;
    return [
      `Dorsa desperta ${timePhrase(state || {campaign:{hour:8}})} com a ponte de pedra cortando a bruma como a única coisa sólida num vale ainda indeciso. O cheiro de lenha úmida se mistura ao de sal das carroças, e os primeiros trabalhadores falam baixo para não desperdiçar voz no frio.`,
      `Perto do portão oriental, uma carroça carregada permanece parada fora da fila. O cavalo está preso, a lona continua amarrada e não há condutor por perto. Ninguém grita por ajuda; o estranho é justamente a maneira como os carregadores contornam o veículo e continuam trabalhando, cada um fingindo que não reparou na ausência.`,
      `${mara ? 'Mara Tessel, à porta da estalagem, seca uma caneca sem tirar os olhos da carroça. ' : ''}Além dos campos, uma torre sem telhado aparece e some na névoa sobre as colinas. A manhã ainda não decidiu se aquilo é apenas paisagem ou o começo de um problema.`
    ];
  }

  function npcActivity(npc,state) {
    if (!npc) return '';
    return npc.activity || `${npc.name} está ocupado com algo que não começou quando você chegou`;
  }

  function sceneForHex(hex, state, mode) {
    const t=TERRAIN[hex.terrain];
    const f=TERRAIN_FICTION[hex.terrain] || TERRAIN_FICTION.plains;
    const weather=String(state.campaign.weather||'').toLowerCase();
    const revisit=Boolean(hex.visitCount && hex.visitCount>1);
    const paragraphs=[];

    if (mode==='arrival') {
      if (revisit && !(hex.notes||[]).some(n=>n.day>=state.campaign.day-1)) {
        paragraphs.push(`Você reconhece o terreno antes de reconhecer qualquer detalhe novo. ${f.approach} ${timePhrase(state)}, a rota conhecida permite cortar o que já não exige decisão.`);
      } else {
        paragraphs.push(`A travessia termina ${timePhrase(state)}. ${f.approach} ${weather.includes('bruma') ? 'A bruma encurta as linhas de visão e faz cada marco surgir tarde, já perto demais para ser apenas pano de fundo.' : f.sound}`);
      }
    } else if (mode==='explore') {
      paragraphs.push(`Quando você abandona a passagem mais óbvia e começa a ler o hex como lugar, não como caminho, o terreno muda de escala. ${f.detail}`);
    } else {
      paragraphs.push(`${f.approach} ${f.sound}`);
    }

    const latest=(hex.notes||[])[hex.notes.length-1];
    if (latest && latest.day < state.campaign.day) paragraphs.push(`Há uma diferença que não estava aqui na última passagem: ${latest.text}. Não explica o que aconteceu, mas prova que o lugar continuou existindo enquanto você estava longe.`);

    const present=npcsAt(state,hex.key);
    if (present.length) {
      const activities=present.slice(0,2).map(n=>`${n.name} está ${npcActivity(n,state)}`).join('; ');
      paragraphs.push(`A cena já estava em andamento antes da sua chegada: ${activities}. Nenhum deles interrompe tudo apenas porque você entrou no quadro.`);
    }

    if (hex.explored && hex.poi) {
      paragraphs.push(`${hex.poi.name} deixa de ser um símbolo abstrato no mapa. ${hex.poi.summary} O que importa agora não é que o lugar existe, mas o que você decide fazer com a distância finalmente reduzida a poucos passos.`);
    } else if (hex.poi && hex.poi.public && hex.discovered) {
      paragraphs.push(`${hex.poi.name} é um marco conhecido daqui, mas conhecer o nome não equivale a conhecer o que há dentro.`);
    } else if (mode==='explore') {
      paragraphs.push('A varredura cobre os marcos maiores sem transformar ausência de descoberta em certeza absoluta. O que não se mostrou continua sendo desconhecido, não inexistente.');
    }
    return paragraphs.slice(0,4);
  }

  function revealNeighbors(state, center, reason='survey') {
    // V3: mover ou explorar NÃO abre automaticamente o anel vizinho.
    // Esta função só é usada por observação deliberada, terreno alto ou regra futura de linha de visão.
    if (reason !== 'survey') return [];
    const revealed=[];
    for (const d of AXIAL_DIRS) {
      const h=state.hexes[key(center.q+d.q,center.r+d.r)];
      if (h && !h.discovered) { h.discovered=true; h.discoverySource='survey'; revealed.push(h.key); }
    }
    return revealed;
  }

  function advanceHours(state, hours) {
    state.campaign.hour += Math.max(0, Math.ceil(hours));
    while (state.campaign.hour >= 24) {
      state.campaign.hour -= 24;
      state.campaign.day += 1;
      dailyWorldUpdate(state);
    }
  }

  function advanceDays(state, days) {
    for (let i = 0; i < days; i++) {
      state.campaign.day += 1;
      dailyWorldUpdate(state);
    }
  }

  function moveNpcForDay(state, npc, day) {
    if (!npc.alive || !Array.isArray(npc.schedule) || !npc.schedule.length) return;
    const previous = npc.location;
    npc.location = npc.schedule[(day - 1) % npc.schedule.length] || npc.home || previous;
    if (previous !== npc.location) {
      state.world.secretLedger.unshift({ day, type:'npc_move', entity:npc.id, from:previous, to:npc.location });
      if (state.world.secretLedger.length > 120) state.world.secretLedger.length = 120;
    }
  }

  function mutateWorldSite(state, day) {
    const candidates = Object.values(state.hexes).filter(h => h.poi && h.explored);
    if (!candidates.length || day % 3 !== 0) return;
    const h = candidates[rollDie(state, candidates.length) - 1];
    const messages = [
      'há rastros novos e sinais de passagem recente',
      'uma estrutura foi mexida desde a última visita',
      'marcas de acampamento sugerem presença recente',
      'o lugar está mais silencioso do que antes, como se alguém tivesse partido às pressas'
    ];
    const text = messages[rollDie(state, messages.length)-1];
    h.notes ||= [];
    h.notes.push({day,text});
    state.world.siteMutations.unshift({day,hex:h.key,poi:h.poi.name,text});
    if (state.world.siteMutations.length > 80) state.world.siteMutations.length = 80;
  }

  function advanceWorldClocks(state, day) {
    for (const c of state.world.clocks || []) {
      if ((day + hashString(c.id)) % 4 === 0 && c.value < c.max) c.value += 1;
    }
    const salt = state.world.clocks.find(c=>c.id==='salt_bridge');
    if (salt && salt.value >= 3 && !state.world.publicEvents.some(e=>e.id==='salt_toll')) {
      state.world.publicEvents.unshift({id:'salt_toll',day,text:'Carroceiros comentam que a Companhia do Sal começou a cobrar taxas informais perto da ponte.'});
      addJournal(state,'mundo','A Companhia do Sal começou a cobrar taxas informais perto da ponte.');
    }
  }

  function factionCheck(state, attacker, defender, attribute='cunning') {
    const aRoll=rollDie(state,10),dRoll=rollDie(state,10),a=aRoll+Number(attacker?.[attribute]||0),d=dRoll+Number(defender?.[attribute]||0);
    return {attribute,attackerRoll:aRoll,defenderRoll:dRoll,attackerTotal:a,defenderTotal:d,success:a>d};
  }

  function factionGoalAttribute(f){const g=normalizeSearch(f.goal||'');if(/control|ponte|forte|passo|territ/.test(g))return 'force';if(/map|descobr|recuper|segredo|passagem/.test(g))return 'cunning';return 'wealth'}

  function runFactionTurn(state, day=state.campaign.day) {
    state.campaign.worldTurn += 1;
    const rivals={salt:'crown',crown:'salt',bell:'ash',ash:'bell',reed:'salt'};
    const byId=Object.fromEntries(state.factions.map(f=>[f.id,f]));
    const order=state.factions.map(f=>({f,initiative:rollDie(state,8)})).sort((a,b)=>b.initiative-a.initiative);
    for(const {f,initiative} of order){
      const income=Math.ceil((Number(f.wealth||1)/2)+((Number(f.force||1)+Number(f.cunning||1))/4));
      f.treasure=Math.max(0,Number(f.treasure||0)+income);
      const defender=byId[rivals[f.id]]||null,attribute=factionGoalAttribute(f),check=defender?factionCheck(state,f,defender,attribute):null;
      const advanced=!check||check.success;if(advanced)f.progress=Math.min(f.clock||6,(f.progress||0)+1);
      const action={day,faction:f.id,target:defender?.id||null,attribute,progress:f.progress,initiative,income,check};
      state.world.factionTraffic.unshift(action);
      state.world.secretLedger.unshift({day,type:'faction_turn',faction:f.id,target:defender?.id||null,goal:f.goal,progress:f.progress,initiative,income,check});
      if(f.known){
        const result=advanced?'ganhou terreno':'encontrou resistência';
        state.world.publicEvents.unshift({id:`faction-${state.campaign.worldTurn}-${f.id}`,day,text:`Movimentos de ${f.name} indicam que a organização ${result} em torno de “${f.goal}”.`});
      }
    }
    if(state.world.factionTraffic.length>120) state.world.factionTraffic.length=120;
    if(state.world.publicEvents.length>80) state.world.publicEvents.length=80;
    if(state.world.secretLedger.length>160) state.world.secretLedger.length=160;
    return order.map(x=>({id:x.f.id,initiative:x.initiative}));
  }

  function dailyWorldUpdate(state) {
    state.world ||= {lastProcessedDay:state.campaign.day,publicEvents:[],secretLedger:[],factionTraffic:[],siteMutations:[],rumorConfidence:{},clocks:[]};
    const day = state.campaign.day;
    Object.values(state.npcs || {}).forEach(npc => moveNpcForDay(state,npc,day));
    advanceWorldClocks(state, day);
    mutateWorldSite(state, day);

    // WWN 6.2.0 sugere um turno de facção aproximadamente mensal/entre aventuras.
    // Movimento de NPCs e relógios continua diário; a camada estratégica não gira toda semana.
    if (day % 30 === 0) runFactionTurn(state, day);
    const weatherRoll = rollDie(state, 6);
    if (weatherRoll === 1) state.campaign.weather = 'Chuva pesada';
    else if (weatherRoll === 2) state.campaign.weather = 'Vento frio';
    else if (weatherRoll >= 5) state.campaign.weather = 'Céu aberto';
    else state.campaign.weather = 'Bruma fria';
    state.world.lastProcessedDay = day;
  }

  function npcsAt(state, hexKey) {
    return Object.values(state.npcs || {}).filter(n => n.alive !== false && n.location === hexKey);
  }

  function rememberNpcInteraction(state, npcId, text) {
    const npc = state.npcs && state.npcs[npcId];
    if (!npc) return;
    npc.memory ||= [];
    npc.memory.unshift({day:state.campaign.day,hour:state.campaign.hour,text:String(text||'').slice(0,260)});
    if (npc.memory.length > 24) npc.memory.length = 24;
    npc.lastSeenDay = state.campaign.day;
  }

  function travelHours(hex, state) {
    const t = TERRAIN[hex.terrain];
    let mph = t.mph;
    if (hex.road) mph = Math.min(3, mph * 2);
    if (/chuva pesada|lama|tempestade/i.test(state.campaign.weather)) mph *= 0.5;
    return 6 / mph;
  }

  // WWN assumes at most ten hours of overland travel in a day. Long crossings
  // automatically include a night camp rather than silently treating 12+ hours
  // as one uninterrupted march.
  function advanceTravelTime(state, travelHoursRequired) {
    let remaining = Math.max(0, travelHoursRequired);
    let marchingHours = 0;
    let campNights = 0;
    while (remaining > 0.001) {
      if (state.campaign.hour < 8) advanceHours(state, 8 - state.campaign.hour);
      if (state.campaign.hour >= 18) {
        advanceHours(state, 24 - state.campaign.hour + 8);
        campNights += 1;
        continue;
      }
      const capacity = 18 - state.campaign.hour;
      const leg = Math.min(remaining, capacity, 10);
      advanceHours(state, leg);
      marchingHours += leg;
      remaining -= leg;
      if (remaining > 0.001) {
        advanceHours(state, 24 - state.campaign.hour + 8);
        campNights += 1;
      }
    }
    return { marchingHours, campNights };
  }

  function encounterCheck(state, hex, context) {
    if (context === 'explore' && hex.poi && hex.poi.forcedEncounter && !hex.poi.encounterResolved) {
      return clone(ENEMIES[hex.poi.forcedEncounter]);
    }
    const die = TERRAIN[hex.terrain].encounterDie;
    const r = rollDie(state, die);
    if (r !== 1) return null;
    if (hex.terrain === 'swamp') return clone(ENEMIES.marsh_hound);
    return clone(ENEMIES.road_bandit);
  }

  function reactionRoll(state, enemy, charismaEligible=true) {
    const roll = rollDice(state, 2, 6);
    const cha = charismaEligible ? (state.player.mods.cha || 0) : 0;
    const total = roll.total + cha;
    let band = 'normal', label = 'reação esperada para a situação';
    if (total <= 2) { band = 'aggressive'; label = 'agressivamente hostil'; }
    else if (total <= 5) { band = 'hostile'; label = 'mais hostil e pouco cooperativo que o esperado'; }
    else if (total <= 8) { band = 'normal'; label = 'tão hostil ou amigável quanto a situação normalmente sugere'; }
    else if (total <= 11) { band = 'friendly'; label = 'mais benigno e aberto que o esperado'; }
    else { band = 'helpful'; label = 'tão amigável e prestativo quanto sua natureza permite'; }
    return { roll: roll.rolls, raw: roll.total, cha, total, band, label, enemyId: enemy?.id || '' };
  }

  function reactionClue(enemy, reaction) {
    if (reaction.band === 'aggressive') return `${enemy.name} já vem para cima sem fingir que existe espaço para conversa; peso, olhar e arma apontam todos na mesma direção.`;
    if (reaction.band === 'hostile') return `${enemy.name} não ataca de imediato, mas fecha a postura e guarda a melhor posição. Há ameaça suficiente para que qualquer gesto brusco possa decidir o encontro.`;
    if (reaction.band === 'friendly') return `${enemy.name} mede a distância, mas a tensão diminui um grau: a arma não sobe e a postura deixa uma margem clara para palavras.`;
    if (reaction.band === 'helpful') return `${enemy.name} parece mais interessado em evitar sangue do que em provocar uma luta e oferece a primeira abertura antes que alguém precise sacar uma arma.`;
    return `${enemy.name} para para avaliar você. Ainda não há ataque; primeiro vem aquele instante curto em que os dois lados tentam decidir o que o outro pretende.`;
  }

  function beginEncounter(state, enemy, source) {
    const reaction = reactionRoll(state, enemy, true);
    const mechanics = `REAÇÃO — 2d6 (${reaction.roll.join('+')})${reaction.cha ? ` + CAR ${reaction.cha >= 0 ? '+' : ''}${reaction.cha}` : ''} = ${reaction.total}: ${reaction.label}. [WWN SRD 5.2.1]`;
    const narrative = [reactionClue(enemy, reaction)];
    state.sceneTitle = `Encontro: ${enemy.name}`;
    if (reaction.band === 'aggressive') {
      const combat = startCombat(state, enemy, source);
      narrative.push(...combat.narrative);
      return { narrative, mechanics: `${mechanics}\n${combat.mechanics}`, combat: true, reaction };
    }
    state.encounter = { enemy: clone(enemy), source, reaction, startedDay: state.campaign.day, startedHour: state.campaign.hour };
    state.lastMechanics = mechanics;
    addJournal(state, 'encontro', `${enemy.name}: reação inicial ${reaction.band}.`);
    return { narrative, mechanics, combat: false, reaction };
  }

  function resolveEncounterPeacefully(state, narrative, mechanics='') {
    const name = state.encounter?.enemy?.name || 'O outro lado';
    state.encounter = null;
    state.narrative = narrative;
    state.lastMechanics = mechanics;
    addJournal(state, 'encontro', `Encontro com ${name} encerrado sem combate.`);
    return { ok:true, narrative, mechanics };
  }

  function encounterTextAction(state, text) {
    const enc = state.encounter;
    if (!enc) return null;
    const lower = String(text || '').toLowerCase();
    const enemy = enc.enemy, reaction = enc.reaction;
    if (/atac|golpe|espada|saco a arma|saco minha arma/i.test(lower)) {
      state.encounter = null;
      const start = startCombat(state, enemy, enc.source || 'encontro');
      start.narrative.unshift(`Você transforma a distância tensa em decisão: ${enemy.name} reage ao movimento da arma.`);
      return { ok:true, narrative:start.narrative, mechanics:start.mechanics };
    }
    if (/recu|afasto|vou embora|sigo caminho|evito|contorno|deixo passar/i.test(lower)) {
      if (reaction.total >= 6) return resolveEncounterPeacefully(state,[`${enemy.name} acompanha sua retirada com os olhos, mas não encontra motivo suficiente para transformar distância em perseguição. O encontro fica para trás sem virar batalha.`],'SEM TESTE — a reação atual não oferece oposição significativa à retirada.');
      const c = skillCheck(state,'sneak','dex',8,0);
      if (c.success) return resolveEncounterPeacefully(state,[`Você cede terreno sem oferecer a abertura que ${enemy.name} parecia procurar. Quando a distância finalmente quebra a tensão, ninguém corre atrás.`],skillMechanics(c));
      const narrative=[`Você tenta romper o contato, mas ${enemy.name} acompanha o movimento e corta a saída antes que a distância fique segura. A falha muda a posição; não apaga sua escolha.`];
      state.narrative=narrative; state.lastMechanics=skillMechanics(c); addJournal(state,'ação',text); return {ok:true,narrative,mechanics:state.lastMechanics};
    }
    if (/falo|convers|pergunt|saúdo|saudo|negocio|negócio/i.test(lower)) {
      const tone = reaction.total <= 5 ? `“Fala rápido e mantém as mãos onde eu possa ver.”` : reaction.total >= 9 ? `“Não vim procurar briga. Se você também não veio, podemos conversar.”` : `“Diga o que quer antes que a situação mude.”`;
      const narrative=[`${enemy.name} não se torna amistoso por conveniência narrativa; apenas responde dentro do humor já mostrado. ${tone}`,'Uma conversa básica não exige teste social. Só haverá rolagem se você pedir uma concessão que ele tenha motivo real para negar.'];
      state.narrative=narrative; state.lastMechanics='SEM TESTE SOCIAL — parley básico sob a reação já determinada. [WWN SRD 5.2.0]'; addJournal(state,'ação',text); return {ok:true,narrative,mechanics:state.lastMechanics};
    }
    if (/convenc|persuad|suborn|propina|ameaç|intimid|mentir/i.test(lower)) {
      const diff = reaction.total <= 5 ? 10 : reaction.total >= 9 ? 6 : 8;
      const c=skillCheck(state,'convince','cha',diff,0);
      if(c.success) return resolveEncounterPeacefully(state,[`${enemy.name} não muda de personalidade, mas aceita uma saída que preserva o próprio interesse. A tensão se desfaz o bastante para os dois lados seguirem sem sangue.`],skillMechanics(c));
      const narrative=[`${enemy.name} não compra o argumento. A recusa deixa mais claro o que pesa do outro lado, mas o encontro continua aberto: você pode mudar de oferta, recuar ou assumir o risco de lutar.`];
      state.narrative=narrative; state.lastMechanics=skillMechanics(c); addJournal(state,'ação',text); return {ok:true,narrative,mechanics:state.lastMechanics};
    }
    const narrative=[`${enemy.name} continua diante de você, com a reação inicial ainda valendo. A ação foi registrada sem transformar automaticamente tensão em combate.`];
    state.narrative=narrative; state.lastMechanics='SEM TESTE — a intenção ainda não criou uma incerteza mecânica resolvível.'; addJournal(state,'ação',text); return {ok:true,narrative,mechanics:state.lastMechanics};
  }

  function moraleCheck(state, reason='perdendo a luta') {
    if (!state.combat) return null;
    const enemy=state.combat.enemy, roll=rollDice(state,2,6), failed=roll.total > (enemy.morale ?? 6);
    return {roll:roll.rolls,total:roll.total,morale:enemy.morale??6,failed,reason};
  }

  function instinctCheck(state, reason='caos do combate') {
    if (!state.combat) return null;
    const enemy=state.combat.enemy, instinct=enemy.instinct ?? 0, roll=rollDie(state,10), failed=instinct>0 && roll<=instinct;
    return {roll,instinct,failed,reason};
  }

  function selectHex(state, q, r) {
    if (!state.hexes[key(q, r)]) return { ok: false, reason: 'Hex inexistente.' };
    state.selected = { q, r };
    return { ok: true };
  }

  function recordActionFact(state, type, text, extra={}) {
    state.continuity ||= {actionLedger:[],familiarRoutes:{},sessionResume:{},locationRecaps:{},immutableFacts:[]};
    state.continuity.actionLedger ||= [];
    const entry={id:`a${state.campaign.day}-${state.campaign.hour}-${state.continuity.actionLedger.length+1}`,day:state.campaign.day,hour:state.campaign.hour,hex:key(state.current.q,state.current.r),type,text:String(text||'').slice(0,360),...extra};
    state.continuity.actionLedger.push(entry);if(state.continuity.actionLedger.length>300)state.continuity.actionLedger.shift();
    state.continuity.sessionResume={day:state.campaign.day,hour:state.campaign.hour,hex:entry.hex,summary:entry.text};return entry;
  }

  function routeKey(a,b){const ak=typeof a==='string'?a:key(a.q,a.r),bk=typeof b==='string'?b:key(b.q,b.r);return [ak,bk].sort().join('<>')}
  function rememberRoute(state, from, to) {
    state.continuity ||= {actionLedger:[],familiarRoutes:{},sessionResume:{},locationRecaps:{},immutableFacts:[]};state.continuity.familiarRoutes ||= {};
    const k=routeKey(from,to),r=state.continuity.familiarRoutes[k]||{uses:0,lastDay:0};r.uses++;r.lastDay=state.campaign.day;state.continuity.familiarRoutes[k]=r;return r;
  }

  function travelTo(state, q, r) {
    if (state.combat) return { ok: false, narrative: ['Você precisa resolver o combate antes de viajar.'], mechanics: '' };
    const dest = state.hexes[key(q, r)];
    if (!dest) return { ok: false, narrative: ['Esse hex não pertence ao atlas atual.'], mechanics: '' };
    if (!isAdjacent(state.current, { q, r })) return { ok: false, narrative: ['O destino não é adjacente. Escolha um dos seis hexes vizinhos.'], mechanics: '' };

    const from={...state.current},hours = travelHours(dest, state);
    const journey = advanceTravelTime(state, hours);
    state.current = { q, r };
    state.selected = { q, r };
    dest.discovered = true;
    dest.visited = true;
    dest.visitCount = (dest.visitCount || 0) + 1;
    const hoursLabel = `${Math.ceil(journey.marchingHours)}h de marcha${journey.campNights ? ` + ${journey.campNights} acampamento${journey.campNights > 1 ? 's' : ''}` : ''}`;
    const mechanics = `VIAGEM — 6 milhas; ${TERRAIN[dest.terrain].label}; velocidade base ${TERRAIN[dest.terrain].mph} mph${dest.road ? '; estrada aplicada (máx. 3 mph)' : ''}; ${hoursLabel}. Limite aplicado: até 10h de marcha/dia.`;
    addJournal(state, 'viagem', `Chegada ao hex ${dest.key} (${TERRAIN[dest.terrain].label}).`);
    const route=rememberRoute(state,from,{q,r});recordActionFact(state,'movement',`Viajei de ${key(from.q,from.r)} para ${dest.key}.`,{from:key(from.q,from.r),to:dest.key,routeUses:route.uses});
    state.sceneTitle = dest.poi && dest.explored ? dest.poi.name : `Chegada a ${TERRAIN[dest.terrain].label.toLowerCase()}`;
    const narrative = sceneForHex(dest, state, 'arrival');
    const encounter = encounterCheck(state, dest, 'travel');
    if (encounter) {
      const start = beginEncounter(state, encounter, 'viagem');
      narrative.push(...start.narrative);
      return { ok: true, narrative, mechanics: `${mechanics}\n${start.mechanics}` };
    }
    return { ok: true, narrative, mechanics };
  }

  function exploreCurrentHex(state) {
    if (state.combat) return { ok: false, narrative: ['Você não consegue conduzir uma exploração sistemática enquanto a luta está em curso.'], mechanics: '' };
    const hex = state.hexes[key(state.current.q, state.current.r)];
    const days = TERRAIN[hex.terrain].exploreDays;
    advanceDays(state, days);
    hex.explored = true;
    hex.visitCount = Math.max(1, hex.visitCount || 0);
    recordActionFact(state,'exploration',`Explorei sistematicamente o hex ${hex.key}.`,{hex:hex.key});
    hex.discovered = true;
    const mechanics = `EXPLORAÇÃO — hex de 6 milhas; ${days} dia${days > 1 ? 's' : ''} de reconhecimento (${TERRAIN[hex.terrain].label}).`;
    state.sceneTitle = hex.poi ? `Explorando ${hex.poi.name}` : `Explorando ${TERRAIN[hex.terrain].label.toLowerCase()}`;
    const narrative = sceneForHex(hex, state, 'explore');
    if (hex.poi) {
      narrative.push(`Depois de uma busca deliberada, o lugar deixa de ser apenas um ponto no mapa. ${hex.poi.name} se revela como algo que merece atenção própria.`);
      addJournal(state, 'descoberta', `${hex.poi.name} foi localizado em ${hex.key}.`);
    } else {
      narrative.push('A busca cobre os marcos principais do hex. Nada aqui se impõe como sítio maior, embora pequenos detalhes ainda possam escapar a uma varredura comum.');
      addJournal(state, 'exploração', `O hex ${hex.key} foi explorado.`);
    }
    const encounter = encounterCheck(state, hex, 'explore');
    if (encounter) {
      if (hex.poi) hex.poi.encounterResolved = true;
      const start = beginEncounter(state, encounter, 'exploração');
      narrative.push(...start.narrative);
      return { ok: true, narrative, mechanics: `${mechanics}\n${start.mechanics}` };
    }
    return { ok: true, narrative, mechanics };
  }

  function skillCheck(state, skill, attr, difficulty, situational = 0) {
    const skillLevel = state.player.skills[skill] ?? -1;
    const attrBonus = state.player.mods[attr] ?? 0;
    let penalty = 0;
    if (skillLevel < 0) penalty = -1;
    const roll = rollDice(state, 2, 6);
    const effectiveSkill = Math.max(0, skillLevel);
    const total = roll.total + effectiveSkill + attrBonus + penalty + clamp(situational, -2, 2);
    return { roll: roll.rolls, total, skill, skillLevel, attr, attrBonus, penalty, situational: clamp(situational, -2, 2), difficulty, success: total >= difficulty };
  }

  function skillMechanics(c) {
    const parts = [`2d6 (${c.roll.join('+')})`, `${c.skill} ${c.skillLevel >= 0 ? c.skillLevel : 'sem treino'}`, `${c.attr.toUpperCase()} ${c.attrBonus >= 0 ? '+' : ''}${c.attrBonus}`];
    if (c.penalty) parts.push(`${c.penalty} sem nível-0`);
    if (c.situational) parts.push(`${c.situational >= 0 ? '+' : ''}${c.situational} situação`);
    return `TESTE — ${parts.join(' | ')} = ${c.total} vs ${c.difficulty}: ${c.success ? 'SUCESSO' : 'FALHA'}.`;
  }

  function performAction(state, rawText) {
    const text = String(rawText || '').trim();
    if (!text) return { ok: false, narrative: [], mechanics: '' };
    if (state.combat) return combatTextAction(state, text);
    if (state.encounter) return encounterTextAction(state, text);

    const lower = text.toLowerCase();
    const current = state.hexes[key(state.current.q, state.current.r)];
    let check = null;
    let narrative = [];

    if (/regras?|como funciona|qual regra|teste\?|rolagem/i.test(lower)) {
      return { ok: false, narrative: ['Essa mensagem parece uma consulta de regra. Use a caixa azul para que ela não avance a cena.'], mechanics: 'ENTRADA INTERCEPTADA — nenhuma mudança no estado da campanha.' };
    }

    if (/observo|olho em volta|vejo o que|examino o horizonte/i.test(lower)) {
      narrative = sceneForHex(current, state, 'observe');
      narrative.push('Você dedica alguns instantes a organizar o que já está ao alcance dos sentidos. Nada é decidido por rolagem quando a informação é evidente.');
      return completeAction(state, text, narrative, 'SEM TESTE — observação do que já é perceptível; a cena não exige incerteza mecânica.');
    }

    if (/procuro|investigo|vasculho|examino|rastro|pista/i.test(lower)) {
      const diff = current.terrain === 'dense_forest' || current.terrain === 'swamp' ? 10 : 8;
      check = skillCheck(state, 'notice', 'wis', diff, 0);
      if (check.success) {
        const detail = current.poi ? `Você encontra um indício concreto ligado a ${current.poi.name}: marcas recentes mostram que alguém passou por aqui antes de você.` : 'Você encontra sinais de passagem recente: pegadas, um galho rompido e terra ainda úmida sob uma pedra deslocada.';
        narrative.push(detail);
      } else {
        narrative.push('A busca consome tempo e produz apenas sinais ambíguos. Você não perde a possibilidade de continuar, mas fica mais exposto ao que estiver usando a mesma área.');
        advanceHours(state, 1);
      }
      return completeAction(state, text, narrative, skillMechanics(check));
    }

    if (/forrage|comida|caçar|coletar/i.test(lower)) {
      const diff = current.terrain === 'swamp' || current.terrain === 'mountains' ? 10 : 8;
      check = skillCheck(state, 'survive', 'wis', diff, 0);
      if (check.success) {
        state.player.inventory.push('1 dia de comida forrageada');
        narrative.push('Você encontra alimento suficiente para aliviar as provisões do grupo sem precisar desmontar o acampamento ou abandonar a rota.');
      } else {
        narrative.push('O terreno oferece pouco e você gasta parte do dia procurando. O fracasso custa tempo, não uma parede invisível na aventura.');
        advanceHours(state, 2);
      }
      return completeAction(state, text, narrative, skillMechanics(check));
    }

    if (/esgueir|furtiv|sem ser visto|me escondo/i.test(lower)) {
      check = skillCheck(state, 'sneak', 'dex', 8, /bruma|noite/i.test(state.campaign.weather) ? 1 : 0);
      narrative.push(check.success ? 'Você escolhe cobertura, ritmo e silêncio suficientes para atravessar a área sem oferecer um alvo fácil aos olhos alheios.' : 'Você avança com cuidado, mas deixa sinais demais para ter certeza de que passou despercebido. A posição não é perdida, porém sua presença pode ter sido notada.');
      return completeAction(state, text, narrative, skillMechanics(check));
    }

    if (/escal|saltar|forçar|arrombar|nadar/i.test(lower)) {
      check = skillCheck(state, 'exert', 'str', 8, 0);
      narrative.push(check.success ? 'O esforço funciona. Você supera o obstáculo e chega do outro lado ainda em condições de decidir o próximo passo.' : 'Você não consegue concluir a manobra como pretendia. Em vez de bloquear a cena, o erro cobra posição e tempo: você precisa tentar outro método ou aceitar maior exposição.');
      if (!check.success) advanceHours(state, 1);
      return completeAction(state, text, narrative, skillMechanics(check));
    }

    if (/pergunto|converso|falo com|mara|del|selka|estalajadeira|escriba|batedora/i.test(lower)) {
      const present = npcsAt(state, current.key);
      const named = present.find(n => normalizeSearch(lower).includes(normalizeSearch(n.name.split(' ')[0])) || normalizeSearch(lower).includes(normalizeSearch(n.role)));
      const npc = named || (present.length === 1 ? present[0] : null);
      if (!npc) {
        narrative.push(present.length ? `Há mais de uma pessoa disponível para conversa aqui: ${present.map(n=>n.name).join(', ')}. Diga com quem você fala.` : 'A pessoa que você procura não está neste hex agora. O mundo mantém a localização dos NPCs mesmo quando eles estão fora da cena.');
        return completeAction(state, text, narrative, 'SEM TESTE — presença e localização consultadas no estado canônico do mundo.');
      }
      const info = npc.knows[Math.floor(nextRandom(state) * npc.knows.length)];
      const questions=(text.match(/\?/g)||[]).length;
      narrative.push(`${npc.name} não abandona a própria atividade para virar uma fonte de informação. ${npcActivity(npc,state).replace(/^./,c=>c.toUpperCase())}. Só então olha para você. “${info}”`);
      if(questions>1) narrative.push(`Você fez ${questions} perguntas. ${npc.name} responde ao que pode sem fingir conhecer o que está fora da própria experiência; o restante fica explicitamente sem resposta em vez de ser descartado.`);
      narrative.push('A conversa continua aberta; uma pergunta comum não exige teste social. Só haverá rolagem quando você tentar obter algo que o NPC tenha motivo real para negar.');
      if (!state.rumors.includes(info)) state.rumors.push(info);
      state.world.rumorConfidence ||= {};state.world.rumorConfidence[info]={status:'reported',source:npc.id,sourceName:npc.name,heardDay:state.campaign.day,validated:false};
      rememberNpcInteraction(state,npc.id,text);
      addJournal(state, 'rumor', `${npc.name}: ${info}`);
      return completeAction(state, text, narrative, 'SEM TESTE SOCIAL — conversa básica e informação que o NPC está disposto a compartilhar.');
    }

    if (/persuad|convencer|pression|intimid|mentir/i.test(lower)) {
      check = skillCheck(state, 'convince', 'cha', 8, 0);
      narrative.push(check.success ? 'A outra pessoa cede o bastante para abrir uma possibilidade concreta. A concessão não elimina seus próprios interesses, mas muda o que ela aceita fazer agora.' : 'A resistência permanece. Em vez de encerrar a conversa, a tentativa deixa claro qual é o preço, medo ou interesse que precisa ser contornado.');
      return completeAction(state, text, narrative, skillMechanics(check));
    }

    narrative.push(`Você declara: “${text}”. O Mestre registra a intenção sem presumir uma rolagem.`);
    narrative.push('A ação é possível dentro da cena atual; como não há incerteza relevante identificada pelo motor, ela segue sem teste e o mundo permanece disponível para sua próxima decisão.');
    return completeAction(state, text, narrative, 'SEM TESTE — nenhuma incerteza mecânica relevante foi detectada.');
  }

  function completeAction(state, text, narrative, mechanics) {
    state.lastMechanics = mechanics;
    recordActionFact(state,'player_action',text);
    addJournal(state, 'ação', text);
    state.narrative = narrative;
    return { ok: true, narrative, mechanics };
  }

  function startCombat(state, enemy, source) {
    state.encounter = null;
    const playerInit = rollDie(state, 8) + state.player.mods.dex;
    const enemyInit = rollDie(state, 8);
    state.combat = { enemy, round: 1, playerTurn: playerInit >= enemyInit, source, initiative: { player: playerInit, enemy: enemyInit }, log: [], moraleChecked:false, instinctCheckedRounds:[] };
    const narrative = [`${enemy.name} compromete o corpo com a luta. A distância útil some, os pés procuram terreno firme e cada movimento seguinte passa a ter consequência imediata.`];
    const mechanics = `INICIATIVA — jogador ${playerInit}, inimigo ${enemyInit}. ${state.combat.playerTurn ? 'Você age primeiro.' : `${enemy.name} age primeiro.`}`;
    addJournal(state, 'combate', `Combate iniciado contra ${enemy.name}.`);
    if (!state.combat.playerTurn) {
      const enemyResult = enemyAttack(state);
      narrative.push(...enemyResult.narrative);
      return { narrative, mechanics: `${mechanics}\n${enemyResult.mechanics}` };
    }
    return { narrative, mechanics };
  }

  function playerAttack(state) {
    if (state.player.mortallyWounded) return { ok: false, narrative: ['Você está Ferido Mortalmente e não pode agir até ser estabilizado.'], mechanics: 'FERIMENTO MORTAL — personagem indefeso; janela de estabilização de seis rodadas. [WWN SRD 2.5.1]' };
    if (!state.combat) return { ok: false, narrative: ['Não há combate ativo.'], mechanics: '' };
    const enemy = state.combat.enemy;
    const w = state.player.weapon;
    const d20 = rollDie(state, 20);
    const skill = state.player.skills[w.skill] ?? -1;
    const skillPart = skill < 0 ? -2 : skill;
    const total = d20 + state.player.attackBonus + state.player.mods[w.attr] + skillPart;
    let damage = 0;
    let hit = total >= enemy.ac;
    let shock = false;
    if (hit) damage = parseDie(w.damage, state).total + state.player.mods[w.attr];
    else if (enemy.ac <= w.shockAC) { damage = Math.max(0, w.shock + state.player.mods[w.attr]); shock = damage > 0; }
    enemy.hp = Math.max(0, enemy.hp - damage);
    const mechanics = `ATAQUE — d20 ${d20} + AB ${state.player.attackBonus} + ${w.attr.toUpperCase()} ${state.player.mods[w.attr] >= 0 ? '+' : ''}${state.player.mods[w.attr]} + ${w.skill} ${skillPart >= 0 ? '+' : ''}${skillPart} = ${total} vs AC ${enemy.ac}. ${hit ? `Acerto; ${damage} dano.` : shock ? `Erro; Shock ${damage}.` : 'Erro; sem dano.'}`;
    const narrative = [hit ? `A lâmina encontra abertura e ${enemy.name} recua sob o impacto.` : shock ? `O golpe não entra limpo, mas a pressão do combate ainda força ${enemy.name} a ceder terreno e absorver o choque.` : `${enemy.name} evita o golpe sem oferecer uma abertura imediata.`];
    if (enemy.hp <= 0) {
      narrative.push(`${enemy.name} não consegue continuar lutando. O silêncio volta ao lugar aos poucos, deixando as consequências para serem examinadas.`);
      addJournal(state, 'combate', `${enemy.name} foi derrotado.`);
      state.combat = null;
      state.narrative = narrative;
      state.lastMechanics = mechanics;
      return { ok: true, narrative, mechanics };
    }
    if (!state.combat.moraleChecked && enemy.hp <= Math.ceil((ENEMIES[enemy.id]?.hp || enemy.hp) / 2)) {
      const morale=moraleCheck(state,'ferido e visivelmente perdendo a luta');
      state.combat.moraleChecked=true;
      mechanics += `
MORAL — 2d6 (${morale.roll.join('+')}) = ${morale.total} vs Moral ${morale.morale}: ${morale.failed?'FALHOU':'MANTEVE-SE'}. [WWN SRD 5.3.1]`;
      if (morale.failed) {
        narrative.push(`${enemy.name} percebe antes de você precisar provar de novo que a luta deixou de valer a própria vida. A guarda cede e ele procura saída, rendição ou distância em vez de morrer por inércia.`);
        addJournal(state,'combate',`${enemy.name} perdeu a Moral e abandonou a luta.`);
        state.combat=null; state.narrative=narrative; state.lastMechanics=mechanics;
        return {ok:true,narrative,mechanics};
      }
    }
    const enemyResult = enemyAttack(state);
    narrative.push(...enemyResult.narrative);
    state.combat.round += 1;
    const merged = `${mechanics}\n${enemyResult.mechanics}`;
    state.narrative = narrative;
    state.lastMechanics = merged;
    return { ok: true, narrative, mechanics: merged };
  }

  function enemyAttack(state) {
    const enemy = state.combat.enemy;
    const round=state.combat.round||1;
    state.combat.instinctCheckedRounds ||= [];
    if (round >= 2 && !state.combat.instinctCheckedRounds.includes(round)) {
      state.combat.instinctCheckedRounds.push(round);
      const instinct=instinctCheck(state,'pressão e confusão do combate');
      if(instinct?.failed && enemy.id !== 'marsh_hound') {
        return {narrative:[`${enemy.name} perde por um instante a leitura limpa da luta. Em vez de explorar a melhor abertura, recua para uma posição que parece segura e desperdiça o momento.`],mechanics:`INSTINTO — d10 ${instinct.roll} vs ${instinct.instinct}: FALHA; ação subótima nesta rodada. [WWN SRD 5.4.1]`};
      }
      if(instinct?.failed && enemy.id === 'marsh_hound') {
        const d20=rollDie(state,20), total=d20+enemy.ab-2, hit=total>=state.player.ac, damage=hit?parseDie(enemy.damage,state).total:0;
        state.player.hp=Math.max(0,state.player.hp-damage);
        const narrative=[hit?`${enemy.name} se deixa dominar pelo instinto e salta cedo demais, mas ainda consegue rasgar você na passagem.`:`${enemy.name} se lança num bote precipitado, furioso demais para corrigir a trajetória quando você sai da linha.`];
        const mechanics=`INSTINTO — d10 ${instinct.roll} vs ${instinct.instinct}: FALHA; bote precipitado. ATAQUE -2 — d20 ${d20} + AB ${enemy.ab} -2 = ${total} vs AC ${state.player.ac}. ${hit?`${damage} dano.`:'Erro.'} [WWN SRD 5.4.1]`;
        if(state.player.hp<=0){state.player.mortallyWounded=true;state.player.condition='Ferido Mortalmente';state.player.deathRound=6;narrative.push('Você cai Ferido Mortalmente; a luta deixa de ser uma abstração e vira uma corrida de seis rodadas por estabilização.');}
        return {narrative,mechanics};
      }
    }
    const d20 = rollDie(state, 20);
    const total = d20 + enemy.ab;
    const hit = total >= state.player.ac;
    let damage = 0;
    let shock = false;
    if (hit) damage = parseDie(enemy.damage, state).total;
    else if (state.player.ac <= (enemy.shockAC || 0)) { damage = enemy.shock || 0; shock = damage > 0; }
    state.player.hp = Math.max(0, state.player.hp - damage);
    const mechanics = `INIMIGO — d20 ${d20} + AB ${enemy.ab} = ${total} vs AC ${state.player.ac}. ${hit ? `Acerto; ${damage} dano.` : shock ? `Erro; Shock ${damage}.` : 'Erro.'}`;
    const narrative = [hit ? `${enemy.name} aproveita a abertura e o golpe chega antes que você consiga fechar a guarda.` : shock ? `${enemy.name} não acerta em cheio, mas mantém pressão suficiente para machucar mesmo assim.` : `${enemy.name} ataca, mas você consegue sair da linha do golpe.`];
    if (state.player.hp <= 0) {
      state.player.mortallyWounded = true;
      state.player.condition = 'Ferido Mortalmente';
      state.player.deathRound = 6;
      narrative.push('Você cai Ferido Mortalmente. Pelas regras, um personagem nesse estado fica indefeso e morrerá ao fim da sexta rodada após cair se ninguém o estabilizar.');
      addJournal(state, 'ferimento', 'Elian caiu Ferido Mortalmente; janela de estabilização: seis rodadas.');
    }
    return { narrative, mechanics };
  }

  function fleeCombat(state) {
    if (!state.combat) return { ok: false, narrative: ['Não há combate ativo.'], mechanics: '' };
    const c = skillCheck(state, 'exert', 'dex', 8, 0);
    const enemyName = state.combat.enemy.name;
    const mechanics = `FUGA — ${skillMechanics(c)}`;
    const narrative = [];
    if (c.success) {
      narrative.push(`Você rompe o contato com ${enemyName} e encontra espaço suficiente para transformar a luta em perseguição evitada. A posição fica preservada, mas o inimigo continua existindo no mundo.`);
      addJournal(state, 'combate', `Fuga bem-sucedida de ${enemyName}.`);
      state.combat = null;
    } else {
      narrative.push(`Você tenta abrir distância de ${enemyName}, mas a rota fecha. A falha não encerra sua ação: o inimigo ganha a chance de pressionar antes do próximo movimento.`);
      const e = enemyAttack(state); narrative.push(...e.narrative);
    }
    state.narrative = narrative; state.lastMechanics = mechanics;
    return { ok: true, narrative, mechanics };
  }

  function combatTextAction(state, text) {
    const lower = text.toLowerCase();
    if (/atac|golpe|espada/i.test(lower)) return playerAttack(state);
    if (/fug|recu|escapar/i.test(lower)) return fleeCombat(state);
    return { ok: true, narrative: ['O combate não transforma qualquer frase em uma rolagem automática. A intenção foi registrada, mas precisa corresponder a uma manobra mecanicamente suportada antes que dados sejam lançados.'], mechanics: 'COMBATE — resolução determinística disponível para ATACAR ou FUGIR; outras manobras permanecem sem rolagem inventada.' };
  }

  function entitySnapshot(state, entityId) {
    if (entityId === 'player') return { id:'player', name:state.player.name, role:`${state.player.className} ${state.player.level}`, descriptor:state.player.visualDescriptor || '', token:(state.visual && state.visual.tokens && state.visual.tokens.player) || null };
    const n = state.npcs && state.npcs[entityId];
    if (!n) return null;
    return { id:entityId, name:n.name, role:n.role, descriptor:n.visualDescriptor || '', token:(state.visual && state.visual.tokens && state.visual.tokens[entityId]) || null };
  }

  function setEntityToken(state, entityId, token) {
    state.visual ||= {tokens:{},sceneHistory:[],geminiExports:0};
    state.visual.tokens ||= {};
    if (!token) delete state.visual.tokens[entityId];
    else state.visual.tokens[entityId] = clone(token);
    return entitySnapshot(state, entityId);
  }

  function activeVisualEntities(state) {
    const ids = ['player', ...npcsAt(state, key(state.current.q,state.current.r)).map(n=>n.id)];
    return ids.map(id=>entitySnapshot(state,id)).filter(Boolean);
  }

  function makeGeminiImageBundle(state, sceneHint='') {
    const current = state.hexes[key(state.current.q,state.current.r)];
    const entities = activeVisualEntities(state);
    const refs = entities.filter(e=>e.token && e.token.dataUrl).slice(0,4).map(e=>({entityId:e.id,name:e.name,fileName:e.token.fileName||`${e.id}.png`,mimeType:e.token.mimeType||'image/jpeg',dataUrl:e.token.dataUrl,descriptor:e.descriptor}));
    const identityRules = entities.map((e,i)=>`${i+1}. ${e.name} (${e.role}): ${e.descriptor || 'preservar rigorosamente a identidade visual do token de referência'}`).join('\n');
    const place = current.explored && current.poi ? `${current.poi.name}. ${current.poi.summary}` : `${TERRAIN[current.terrain].label}, hex ${current.key}`;
    const scene = (state.narrative||[]).join(' ');
    const prompt = `Crie uma ilustração cinematográfica horizontal para uma cena de RPG de fantasia sandbox.\n\nCENA CANÔNICA: ${scene}\nLOCAL: ${place}.\nTEMPO: Dia ${state.campaign.day}, ${String(state.campaign.hour).padStart(2,'0')}:00; ${state.campaign.weather}; ${state.campaign.season}.\n${sceneHint ? `INTENÇÃO VISUAL EXTRA: ${sceneHint}\n` : ''}\nPERSONAGENS/NPCS CANÔNICOS:\n${identityRules}\n\nREGRAS DE CONTINUIDADE VISUAL: use os tokens anexados como referências de identidade. Não troque rosto, idade aparente, cabelo, etnia, roupas-chave, cicatrizes, cores dominantes ou equipamento identificador sem uma mudança registrada no estado da campanha. Se um personagem já apareceu em imagens anteriores, trate a identidade anterior como canônica. Não invente personagens adicionais. Sem HUD, sem texto, sem moldura, sem ícones. A imagem deve representar exatamente o momento atual e a posição relativa plausível dos presentes.`;
    state.visual.geminiExports = (state.visual.geminiExports||0)+1;
    state.visual.sceneHistory ||= [];
    state.visual.sceneHistory.unshift({day:state.campaign.day,hour:state.campaign.hour,hex:current.key,entities:entities.map(e=>e.id),prompt:prompt.slice(0,1200)});
    if(state.visual.sceneHistory.length>40) state.visual.sceneHistory.length=40;
    return {schema:'braseiro.visual-prompt.v1',system:'WWN',campaign:state.campaign.name,generatedAt:new Date().toISOString(),prompt,references:refs,entities:entities.map(({token,...rest})=>rest),continuityHistory:state.visual.sceneHistory.slice(0,8)};
  }

  const RULE_QUERY_SYNONYMS = {
    'pericia':['skill','check'], 'perícia':['skill','check'], 'teste':['skill','check'], 'dificuldade':['difficulty'], 'ataque':['attack'], 'acertar':['attack roll'],
    'iniciativa':['initiative'], 'surpresa':['surprise'], 'choque':['shock'], 'ferido':['mortally wounded'], 'mortal':['mortal injury'], 'estabilizar':['stabilizing'],
    'cura':['healing'], 'viagem':['overland travel'], 'viajar':['overland travel'], 'explorar':['exploring a hex'], 'hex':['hex'], 'forragear':['foraging'],
    'encontro':['wandering encounters'], 'faccao':['faction'], 'facção':['faction'], 'faccoes':['faction'], 'facções':['faction'], 'moral':['morale'], 'instinto':['instinct'], 'reacao':['reaction roll'], 'reação':['reaction roll'],
    'encumbrancia':['encumbrance'], 'carga':['encumbrance'], 'perseguicao':['chases pursuit'], 'perseguição':['chases pursuit'], 'magia':['magic spellcasting'], 'magica':['magic spellcasting']
  };

  function normalizeSearch(s) { return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9\s-]/g,' ').replace(/\s+/g,' ').trim(); }
  function expandedRuleTerms(question) {
    const norm=normalizeSearch(question); const terms=new Set(norm.split(' ').filter(w=>w.length>2));
    for(const [pt,eng] of Object.entries(RULE_QUERY_SYNONYMS)) if(norm.includes(normalizeSearch(pt))) eng.forEach(t=>normalizeSearch(t).split(' ').forEach(x=>terms.add(x)));
    return [...terms];
  }
  function searchRuleIndex(question, index, limit=3) {
    const terms=expandedRuleTerms(question); if(!Array.isArray(index)||!index.length||!terms.length) return [];
    return index.map(p=>{
      const t=normalizeSearch(p.text); let score=0;
      for(const term of terms){ const re=new RegExp(`\\b${term.replace(/[.*+?^${}()|[\\]\\]/g,'\\$&')}\\b`,'g'); const m=t.match(re); if(m) score += Math.min(8,m.length)*(term.length>5?2:1); }
      if(/section|regra|como|funciona/.test(normalizeSearch(question))) score*=1.05;
      return {page:p,score};
    }).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,limit);
  }
  function excerptForTerms(text, terms, max=500) {
    const lower=normalizeSearch(text); let best=0; let bestScore=-1;
    const prioritized=[...terms].sort((a,b)=>b.length-a.length);
    for(const term of prioritized){
      let from=0, i=-1;
      while((i=lower.indexOf(term,from))>=0){
        const start=Math.max(0,i-160), window=lower.slice(start,start+max);
        const score=prioritized.reduce((acc,t)=>acc+(window.includes(t)?Math.min(10,t.length):0),0);
        if(score>bestScore){bestScore=score;best=start;}
        from=i+term.length;
      }
    }
    let ex=String(text).slice(best,best+max).trim(); if(best>0) ex='…'+ex; if(best+max<text.length) ex+='…'; return ex;
  }
  function preferredRulePages(question) {
    const q=normalizeSearch(question); const pages=[];
    if(/estabil|ferid.*mortal|mortal.*ferid/.test(q)) pages.push(48);
    if(/explor.*hex|hex.*explor/.test(q)) pages.push(54);
    if(/viagem|viajar|marcha/.test(q)) pages.push(53);
    if(/dificuldade|pericia|teste de/.test(q)) pages.push(44,45);
    if(/iniciativa|surpresa/.test(q)) pages.push(45);
    if(/shock|choque|ataque|acertar/.test(q)) pages.push(47);
    if(/salvamento|saving|save/.test(q)) pages.push(44);
    if(/reacao|reaction/.test(q)) pages.push(79);
    if(/moral|morale/.test(q)) pages.push(80);
    if(/instinto|instinct/.test(q)) pages.push(81);
    if(/faccao|faccoes|faction/.test(q)) pages.push(82,83,84);
    return [...new Set(pages)];
  }
  function queryRulesIndexed(state, question, index) {
    const base=queryRules(state,question);
    const preferred=preferredRulePages(question).map(pg=>({page:(index||[]).find(p=>p.bookPage===pg),score:999})).filter(h=>h.page);
    const searched=searchRuleIndex(question,index,5);
    const seen=new Set(); const hits=[...preferred,...searched].filter(h=>{if(seen.has(h.page.bookPage))return false;seen.add(h.page.bookPage);return true;}).slice(0,3);
    if(!hits.length) return base;
    const terms=expandedRuleTerms(question);
    const source=hits.map(h=>`WWN SRD p. ${h.page.bookPage}: ${excerptForTerms(h.page.text,terms,430)}`).join('\n\n');
    const answer = `${base}\n\nFONTES INDEXADAS LOCAIS\n${source}`;
    state.lastRuleAnswer=answer;
    return answer;
  }

  function queryRules(state, question) {
    const q = String(question || '').trim().toLowerCase();
    if (!q) return '';
    let answer;
    if (/dificuldade|cd|difficulty/.test(q)) answer = 'Dificuldades comuns: 6 tarefa relativamente simples; 8 desafio significativo para um profissional competente; 10 difícil até para alguém habilidoso; 12 confiável apenas para um mestre; 14+ até um mestre provavelmente falha. Modificadores situacionais normalmente ficam entre -2 e +2. [WWN SRD 2.3.1]';
    else if (/teste|skill|perícia|pericia/.test(q)) answer = 'Teste de perícia: role 2d6 e some o nível da perícia e o modificador do atributo relevante; total igual ou maior que a dificuldade é sucesso. Sem sequer nível-0 na perícia pertinente, normalmente há -1 e certas tarefas técnicas podem ser impossíveis. O Mestre só pede teste quando existe incerteza relevante. [WWN SRD 2.3.0]';
    else if (/explor|hex/.test(q)) answer = 'Explorar levemente um hex padrão de 6 milhas leva um dia inteiro e encontra a maioria dos pontos de interesse maiores. Terreno muito acidentado ou ocultante, como montanhas ou pântano sem trilha, pode dobrar ou triplicar esse tempo. [WWN SRD 2.12.1]';
    else if (/viagem|viajar|marcha|milhas/.test(q)) answer = 'Viagem terrestre presume até 10 horas de marcha por dia. Velocidades: planície/savana 3 mph; floresta leve/deserto 2; floresta densa/colinas 1,5; pântano 1; montanhas/ermos 0,5. Estrada dobra a velocidade, mas não acima de 3 mph. Mau tempo reduz pela metade. [WWN SRD 2.11.0]';
    else if (/iniciativa/.test(q)) answer = 'Iniciativa padrão é por lado: cada lado rola 1d8 e soma o melhor modificador de Destreza do grupo; maior resultado age primeiro. A ordem não é rerrolada a cada rodada. [WWN SRD 2.4.2]';
    else if (/shock|choque/.test(q)) answer = 'Algumas armas corpo a corpo causam Shock mesmo quando o ataque erra, desde que a AC corpo a corpo do alvo seja igual ou menor que o valor de AC indicado pelo Shock da arma. O modificador de atributo relevante soma ao Shock. Escudo normalmente nega a primeira fonte de Shock sofrida na rodada. [WWN SRD 2.4.6.4]';
    else if (/facç(?:ão|ões)|facc(?:ao|oes)|faction/.test(q)) answer = 'Turnos de facção são uma camada estratégica do mundo, normalmente resolvida aproximadamente uma vez por mês ou entre aventuras. As facções têm Força, Astúcia, Riqueza, Tesouro e Assets; recebem renda, pagam manutenção e executam uma ação por turno. Conflitos de facção usam 1d10 + atributo contra 1d10 + atributo e o atacante precisa superar, não apenas igualar, o defensor. [WWN SRD 6.0–6.7]';
    else if (/reação|reacao|reaction/.test(q)) answer = 'Encontros que não sejam inevitavelmente violentos normalmente recebem uma rolagem de Reação: 2d6, com o modificador de Carisma do personagem que faz a abordagem quando aplicável. 2- é agressivamente hostil; 3–5 hostil; 6–8 esperado; 9–11 mais amistoso; 12+ tão prestativo quanto a natureza permitir. O Mestre deve mostrar sinais dessa reação antes dos personagens agirem. [WWN SRD 5.2.0–5.2.1]';
    else if (/moral|morale/.test(q)) answer = 'Moral: quando as circunstâncias justificam, role 2d6; se o resultado for maior que o valor de Moral, o NPC falha e tenta fugir, render-se ou interromper a luta conforme a situação. [WWN SRD 5.3.1]';
    else if (/instinto|instinct/.test(q)) answer = 'Instinto: em gatilhos apropriados, role 1d10; se o resultado for igual ou menor que o valor de Instinto, o NPC cede a um comportamento impulsivo ou subótimo. Personagens de jogador nunca fazem testes de Instinto. [WWN SRD 5.4.1]';
    else if (/ataque|acertar|ac/.test(q)) answer = 'Ataque de personagem: 1d20 + bônus base de ataque + modificador do atributo da arma + perícia de combate relevante. Sem nível-0 na perícia apropriada, a penalidade é -2. Igualar ou superar a AC relevante acerta. [WWN SRD 2.4.5]';
    else if (/salvamento|save|saving/.test(q)) answer = 'Salvamentos usam 1d20 e precisam igualar ou superar o alvo. Há salvamentos Físico, Evasão, Mental e Sorte. Para PCs, os três primeiros derivam de 16 - nível - melhor modificador de atributo do par pertinente; Sorte é 16 - nível. [WWN SRD 2.2.0]';
    else if (/ferido mortal|ferimento mortal|estabiliz/.test(q)) answer = 'Ao chegar a 0 PV por dano letal, um PC fica Ferido Mortalmente, indefeso e incapaz de agir. Ele morre ao fim da sexta rodada após cair se não for estabilizado. Estabilizar normalmente é uma Ação Principal com Dex/Heal ou Int/Heal, dificuldade 8 + rodadas completas desde a queda; sem kit de cura, +2. [WWN SRD 2.5.1]';
    else if (/round|rodada|turno|cena/.test(q)) answer = 'Cena é uma unidade narrativa curta; combate ocorre em rodadas de cerca de 6 segundos; turnos de exploração complexa duram cerca de 10 minutos. Esses relógios são separados para que perguntas de regra não consumam tempo ficcional. [WWN SRD 2.1.0]';
    else answer = 'A resposta rápida não tem um verbete específico para essa formulação. O índice local completo do WWN SRD será pesquisado abaixo sem alterar a cena.';
    state.lastRuleAnswer = answer;
    return answer;
  }

  function exportState(state) { return JSON.stringify(state, null, 2); }
  function importState(json) {
    const parsed = typeof json === 'string' ? JSON.parse(json) : clone(json);
    if (!parsed || !parsed.hexes || !parsed.player || !parsed.campaign) throw new Error('Save inválido.');
    const fresh = makeInitialState();
    parsed.visual ||= clone(fresh.visual); parsed.visual.tokens ||= {}; parsed.visual.sceneHistory ||= []; parsed.visual.sceneImages ||= [];
    parsed.world ||= clone(fresh.world);
    const oldVersion=String(parsed.version||'0');
    const mergedHexes=clone(fresh.hexes);
    for(const [k,h] of Object.entries(parsed.hexes||{})) if(mergedHexes[k]) mergedHexes[k]={...mergedHexes[k],...h};
    parsed.hexes=mergedHexes;
    parsed.atlas={...fresh.atlas,...(parsed.atlas||{}),radius:HEX_RADIUS,fogPolicy:'enter-only-v2'};
    if(/^1\./.test(oldVersion)) {
      const currentKey=key(parsed.current?.q||0,parsed.current?.r||0);
      Object.values(parsed.hexes).forEach(h=>{ h.discovered=Boolean(h.visited||h.explored||h.key===currentKey); });
    }
    parsed.world.publicEvents ||= []; parsed.world.secretLedger ||= []; parsed.world.factionTraffic ||= []; parsed.world.siteMutations ||= []; parsed.world.rumorConfidence ||= {};
    if(!Array.isArray(parsed.world.clocks) || !parsed.world.clocks.length) parsed.world.clocks=clone(fresh.world.clocks);
    parsed.player.visualDescriptor ||= fresh.player.visualDescriptor;
    Object.values(parsed.hexes).forEach(h=>{ h.notes ||= []; h.tile = tileVariantFor(h.terrain,h.q,h.r); h.visitCount ||= h.visited ? 1 : 0; });
    const oldNpcs=parsed.npcs||{}; parsed.npcs={};
    for(const [id,def] of Object.entries(fresh.npcs)) parsed.npcs[id]={...clone(def),...(oldNpcs[id]||{})};
    for(const [id,n] of Object.entries(oldNpcs)) if(!parsed.npcs[id]) parsed.npcs[id]={id,...n};
    Object.entries(parsed.npcs).forEach(([id,n])=>{ n.id ||= id; n.memory ||= []; n.alive = n.alive !== false; n.home ||= '0,0'; n.location ||= n.home; n.schedule ||= [n.home]; n.visualDescriptor ||= `${n.name}, ${n.role}`; });
    const freshFactions=Object.fromEntries(fresh.factions.map(f=>[f.id,f]));
    const oldFactionMap=Object.fromEntries((parsed.factions||[]).map(f=>[f.id,f])); parsed.factions=fresh.factions.map(f=>({...clone(f),...(oldFactionMap[f.id]||{})})); for(const [id,f] of Object.entries(oldFactionMap)) if(!freshFactions[id]) parsed.factions.push(f);
    parsed.continuity ||= clone(fresh.continuity);parsed.continuity.actionLedger ||= [];parsed.continuity.familiarRoutes ||= {};parsed.continuity.sessionResume ||= clone(fresh.continuity.sessionResume);parsed.continuity.locationRecaps ||= {};parsed.continuity.immutableFacts ||= [];
    parsed.encounter ||= null;
    parsed.version = VERSION;
    parsed.schema = Math.max(2, parsed.schema||1);
    return parsed;
  }

  const GameBus = (() => {
    const handlers = {};
    return {
      on(event, fn) { (handlers[event] ||= []).push(fn); },
      emit(event, payload) { (handlers[event] || []).forEach(fn => fn(payload)); }
    };
  })();

  const api = {
    VERSION, STORAGE_KEY, HEX_RADIUS, AXIAL_DIRS, DIFFICULTIES, TERRAIN, HEX_VARIANTS, POIS, ENEMIES,
    key, clone, attrMod, axialDistance, isAdjacent, periodOfDay, roadConnections, openingScene, sceneForHex, makeInitialState, selectHex, travelTo, exploreCurrentHex,
    skillCheck, reactionRoll, moraleCheck, instinctCheck, beginEncounter, factionCheck, runFactionTurn, recordActionFact, rememberRoute, performAction, queryRules, queryRulesIndexed, searchRuleIndex, playerAttack, fleeCombat, exportState, importState, revealNeighbors, travelHours, advanceTravelTime, npcsAt, rememberNpcInteraction, setEntityToken, entitySnapshot, activeVisualEntities, makeGeminiImageBundle, GameBus
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  global.XWNEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);
