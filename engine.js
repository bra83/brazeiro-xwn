(function (global) {
  'use strict';

  const VERSION = '1.5.0';
  const STORAGE_KEY = 'braseiro_xwn_wwn_v150';
  const HEX_RADIUS = 3;
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
    return `assets/hex_library/${id}.png`;
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
    '-1,-1': { name: 'Casa do Salgueiro', kind: 'site', icon: '⌂', summary: 'Uma casa isolada continua soltando fumaça apesar da estrada ter sumido.' }
  });

  const ENEMIES = Object.freeze({
    ash_scout: { id: 'ash_scout', name: 'Batedor da Cinza', hp: 6, ac: 13, ab: 1, damage: '1d6', morale: 7, shock: 2, shockAC: 13 },
    grave_robber: { id: 'grave_robber', name: 'Saqueador de Túmulos', hp: 5, ac: 12, ab: 1, damage: '1d6', morale: 6, shock: 1, shockAC: 13 },
    marsh_hound: { id: 'marsh_hound', name: 'Cão do Brejo', hp: 4, ac: 12, ab: 1, damage: '1d4', morale: 7, shock: 1, shockAC: 12 },
    road_bandit: { id: 'road_bandit', name: 'Bandido da Estrada', hp: 5, ac: 13, ab: 1, damage: '1d6', morale: 6, shock: 2, shockAC: 13 }
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
    return explicit[k] || 'plains';
  }

  function roadFor(q, r) {
    const roadKeys = new Set(['-1,1', '0,1', '0,0', '0,-1', '1,-1', '2,-1']);
    return roadKeys.has(key(q, r));
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
          discovered: k === '0,0' || axialDistance({ q, r }, { q: 0, r: 0 }) === 1,
          explored: k === '0,0',
          visited: k === '0,0',
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
      atlas: { id: 'orne-r3', orientation: 'flat', radius: 3, hexMiles: 6, source: 'acervo-compartilhado' },
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
        { id: 'salt', name: 'Companhia do Sal', force: 2, cunning: 1, wealth: 3, power: 2, location: '0,0', goal: 'Controlar a ponte de Dorsa', progress: 0, clock: 6, known: true },
        { id: 'bell', name: 'Irmãos do Sino', force: 1, cunning: 2, wealth: 1, power: 1, location: '-1,1', goal: 'Recuperar uma relíquia perdida', progress: 0, clock: 5, known: true },
        { id: 'ash', name: 'Vigias da Cinza', force: 2, cunning: 2, wealth: 1, power: 2, location: '2,-1', goal: 'Abrir o Passo do Corvo', progress: 0, clock: 7, known: false }
      ],
      npcs: {
        mara: { id:'mara', name: 'Mara Tessel', role: 'estalajadeira', disposition: 1, home:'0,0', location:'0,0', schedule:['0,0'], agenda:'manter a estalagem segura e descobrir por que a Companhia do Sal pressiona os carroceiros', alive:true, lastSeenDay:1, memory:[], visualDescriptor:'mulher humana de meia-idade, cabelo ruivo-escuro preso, sardas, avental de couro sobre roupa vinho, olhar atento e postura prática', knows: ['A Torre de Cinza voltou a mostrar luz à noite.', 'Dois carregadores sumiram no Marco Quebrado.'] },
        del: { id:'del', name: 'Irmão Del', role: 'escriba itinerante', disposition: 0, home:'0,0', location:'0,0', schedule:['0,0','-1,1','-1,1','0,0','1,-1'], agenda:'copiar inscrições antigas e descobrir a origem do sino enterrado', alive:true, lastSeenDay:1, memory:[], visualDescriptor:'homem humano de trinta e poucos anos, magro, cabelo preto ondulado, barba curta, capuz cinza, bolsa de pergaminhos e dedos manchados de tinta', knows: ['O cemitério é mais antigo que Dorsa.', 'Há marcas novas na pedra do Passo do Corvo.'] },
        selka: { id:'selka', name:'Selka Venn', role:'batedora da ponte', disposition:0, home:'0,0', location:'1,0', schedule:['1,0','1,0','0,0','1,0','1,-1'], agenda:'mapear movimentos de estranhos sem revelar quem a paga', alive:true, lastSeenDay:null, memory:[], visualDescriptor:'mulher humana jovem, pele morena, trança preta longa, capa marrom curta, arco simples, cicatriz fina na sobrancelha direita', knows:['A mata ao leste tem marcas de fogueiras recentes.', 'A estrada para o Passo do Corvo está sendo observada.'] }
      },
      visual: { tokens: {}, sceneHistory: [], geminiExports: 0 },
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
      lastMechanics: '',
      lastRuleAnswer: '',
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

  function openingScene() {
    return [
      'A manhã encontra Dorsa coberta por uma bruma baixa. A velha ponte de pedra desaparece pela metade dentro do nevoeiro, e carroças atravessam devagar para não assustar os animais.',
      'Perto do portão oriental, uma carroça de sal permanece parada sem condutor. Ninguém parece tratá-la como emergência, mas os carregadores evitam olhar para ela por tempo demais.',
      'A estrada segue para os campos e, além deles, sobe na direção de uma torre escura recortada contra as colinas. Você ainda tem o dia inteiro pela frente.'
    ];
  }

  function sceneForHex(hex, state, mode) {
    const t = TERRAIN[hex.terrain];
    const base = [];
    const weather = state.campaign.weather.toLowerCase();
    const byTerrain = {
      plains: 'A terra se abre em ondulações baixas, com capim úmido e longas linhas de visão.',
      farmland: 'Valas rasas dividem os campos. Cercas de pedra e árvores antigas marcam propriedades que parecem maiores do que seus donos conseguem manter.',
      forest: 'A estrada se estreita sob copas irregulares. O chão guarda folhas velhas, raízes expostas e marcas que a luz lateral transforma em pistas falsas.',
      dense_forest: 'A mata fecha o horizonte. Galhos cruzados abafam o vento e obrigam cada escolha de direção a ser consciente.',
      hills: 'O terreno sobe em lombadas pedregosas. Cada crista oferece visão melhor e, ao mesmo tempo, deixa qualquer viajante mais exposto.',
      mountains: 'A pedra domina a paisagem. O caminho escolhe por você onde é possível passar, e cada desvio custa tempo.',
      swamp: 'A água invade o caminho em lâminas rasas. O solo firme aparece em ilhas estreitas, separadas por lama escura.',
      water: 'A margem é baixa e enlameada. A superfície quase imóvel devolve um céu mais escuro do que deveria.'
    };
    if (mode === 'arrival') base.push(`Você entra em ${t.label.toLowerCase()}. ${byTerrain[hex.terrain]}`);
    else base.push(byTerrain[hex.terrain]);
    if (hex.road) base.push('Uma estrada antiga atravessa este hex e oferece avanço mais rápido enquanto o piso se mantém transitável.');
    if (weather.includes('bruma')) base.push('A bruma reduz a distância útil de observação, mas também encobre movimentos discretos.');
    if (hex.explored && hex.poi) base.push(`${hex.poi.name}: ${hex.poi.summary}`);
    else if (hex.discovered && hex.poi && hex.poi.public) base.push(`${hex.poi.name} é visível e conhecido daqui.`);
    const present = npcsAt(state, hex.key);
    if (present.length) base.push(`${present.map(n=>n.name).join(present.length>1 ? ' e ' : '')} ${present.length>1 ? 'estão' : 'está'} por aqui, cada qual ocupado com seus próprios assuntos.`);
    const latestNote = Array.isArray(hex.notes) ? hex.notes[hex.notes.length-1] : null;
    if (latestNote && latestNote.day < state.campaign.day) base.push(`Há uma mudança desde a última passagem: ${latestNote.text}.`);
    return base;
  }

  function revealNeighbors(state, center) {
    for (const d of AXIAL_DIRS) {
      const h = state.hexes[key(center.q + d.q, center.r + d.r)];
      if (h) h.discovered = true;
    }
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

  function dailyWorldUpdate(state) {
    state.world ||= {lastProcessedDay:state.campaign.day,publicEvents:[],secretLedger:[],factionTraffic:[],siteMutations:[],rumorConfidence:{},clocks:[]};
    const day = state.campaign.day;
    Object.values(state.npcs || {}).forEach(npc => moveNpcForDay(state,npc,day));
    advanceWorldClocks(state, day);
    mutateWorldSite(state, day);

    // Full faction turns remain slower than ordinary NPC/world motion. The world
    // moves daily, while strategic faction progress is resolved weekly.
    if (day % 7 === 0) {
      state.campaign.worldTurn += 1;
      const faction = state.factions[state.campaign.worldTurn % state.factions.length];
      faction.progress = Math.min(faction.clock || 6, (faction.progress || 0) + 1);
      state.world.factionTraffic.unshift({day,faction:faction.id,location:faction.location,progress:faction.progress});
      state.world.secretLedger.unshift({day,type:'faction_turn',faction:faction.id,goal:faction.goal,progress:faction.progress});
      if (faction.known) addJournal(state, 'mundo', `${faction.name} avançou seu objetivo conhecido: ${faction.goal}.`);
    }
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

  function selectHex(state, q, r) {
    if (!state.hexes[key(q, r)]) return { ok: false, reason: 'Hex inexistente.' };
    state.selected = { q, r };
    return { ok: true };
  }

  function travelTo(state, q, r) {
    if (state.combat) return { ok: false, narrative: ['Você precisa resolver o combate antes de viajar.'], mechanics: '' };
    const dest = state.hexes[key(q, r)];
    if (!dest) return { ok: false, narrative: ['Esse hex não pertence ao atlas atual.'], mechanics: '' };
    if (!isAdjacent(state.current, { q, r })) return { ok: false, narrative: ['O destino não é adjacente. Escolha um dos seis hexes vizinhos.'], mechanics: '' };

    const hours = travelHours(dest, state);
    const journey = advanceTravelTime(state, hours);
    state.current = { q, r };
    state.selected = { q, r };
    dest.discovered = true;
    dest.visited = true;
    revealNeighbors(state, state.current);
    const hoursLabel = `${Math.ceil(journey.marchingHours)}h de marcha${journey.campNights ? ` + ${journey.campNights} acampamento${journey.campNights > 1 ? 's' : ''}` : ''}`;
    const mechanics = `VIAGEM — 6 milhas; ${TERRAIN[dest.terrain].label}; velocidade base ${TERRAIN[dest.terrain].mph} mph${dest.road ? '; estrada aplicada (máx. 3 mph)' : ''}; ${hoursLabel}. Limite aplicado: até 10h de marcha/dia.`;
    addJournal(state, 'viagem', `Chegada ao hex ${dest.key} (${TERRAIN[dest.terrain].label}).`);
    const narrative = sceneForHex(dest, state, 'arrival');
    const encounter = encounterCheck(state, dest, 'travel');
    if (encounter) {
      const start = startCombat(state, encounter, 'viagem');
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
    hex.discovered = true;
    revealNeighbors(state, state.current);
    const mechanics = `EXPLORAÇÃO — hex de 6 milhas; ${days} dia${days > 1 ? 's' : ''} de reconhecimento (${TERRAIN[hex.terrain].label}).`;
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
      const start = startCombat(state, encounter, 'exploração');
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
      narrative.push(`${npc.name} interrompe o que estava fazendo antes de responder. “${info}”`);
      narrative.push('A conversa continua aberta; uma pergunta comum não exige teste social. Só haverá rolagem quando você tentar obter algo que o NPC tenha motivo real para negar.');
      if (!state.rumors.includes(info)) state.rumors.push(info);
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
    addJournal(state, 'ação', text);
    state.narrative = narrative;
    return { ok: true, narrative, mechanics };
  }

  function startCombat(state, enemy, source) {
    const playerInit = rollDie(state, 8) + state.player.mods.dex;
    const enemyInit = rollDie(state, 8);
    state.combat = { enemy, round: 1, playerTurn: playerInit >= enemyInit, source, initiative: { player: playerInit, enemy: enemyInit }, log: [] };
    const narrative = [`A tensão vira combate: ${enemy.name} fecha a distância e a cena deixa de ser apenas exploração.`];
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
    return { ok: true, narrative: ['Em combate, a V1 aceita ações estruturadas de atacar ou fugir. A intenção foi registrada, mas não foi transformada em uma rolagem inventada.'], mechanics: 'COMBATE — use ATACAR ou FUGIR para resolução mecânica determinística nesta versão.' };
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
    'encontro':['wandering encounters'], 'faccao':['faction'], 'facção':['faction'], 'moral':['morale'], 'instinto':['instinct'], 'reacao':['reaction roll'], 'reação':['reaction roll'],
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
    if(/faccao|faction/.test(q)) pages.push(82,83,84);
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
    else if (/ataque|acertar|ac/.test(q)) answer = 'Ataque de personagem: 1d20 + bônus base de ataque + modificador do atributo da arma + perícia de combate relevante. Sem nível-0 na perícia apropriada, a penalidade é -2. Igualar ou superar a AC relevante acerta. [WWN SRD 2.4.5]';
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
    parsed.visual ||= clone(fresh.visual); parsed.visual.tokens ||= {}; parsed.visual.sceneHistory ||= [];
    parsed.world ||= clone(fresh.world);
    parsed.world.publicEvents ||= []; parsed.world.secretLedger ||= []; parsed.world.factionTraffic ||= []; parsed.world.siteMutations ||= []; parsed.world.rumorConfidence ||= {};
    if(!Array.isArray(parsed.world.clocks) || !parsed.world.clocks.length) parsed.world.clocks=clone(fresh.world.clocks);
    parsed.player.visualDescriptor ||= fresh.player.visualDescriptor;
    Object.values(parsed.hexes).forEach(h=>{ h.notes ||= []; h.tile ||= tileVariantFor(h.terrain,h.q,h.r); });
    const oldNpcs=parsed.npcs||{}; parsed.npcs={};
    for(const [id,def] of Object.entries(fresh.npcs)) parsed.npcs[id]={...clone(def),...(oldNpcs[id]||{})};
    for(const [id,n] of Object.entries(oldNpcs)) if(!parsed.npcs[id]) parsed.npcs[id]={id,...n};
    Object.entries(parsed.npcs).forEach(([id,n])=>{ n.id ||= id; n.memory ||= []; n.alive = n.alive !== false; n.home ||= '0,0'; n.location ||= n.home; n.schedule ||= [n.home]; n.visualDescriptor ||= `${n.name}, ${n.role}`; });
    const freshFactions=Object.fromEntries(fresh.factions.map(f=>[f.id,f]));
    parsed.factions=(parsed.factions||fresh.factions).map(f=>({...clone(freshFactions[f.id]||{}),...f}));
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
    key, clone, attrMod, axialDistance, isAdjacent, makeInitialState, selectHex, travelTo, exploreCurrentHex,
    skillCheck, performAction, queryRules, queryRulesIndexed, searchRuleIndex, playerAttack, fleeCombat, exportState, importState, revealNeighbors, travelHours, advanceTravelTime, npcsAt, rememberNpcInteraction, setEntityToken, entitySnapshot, activeVisualEntities, makeGeminiImageBundle, GameBus
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  global.XWNEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);
