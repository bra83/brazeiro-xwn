(function(global){
  'use strict';
  const systems={
    WWN:{
      id:'WWN',barbaraSystemId:'worlds_without_number',label:'Worlds Without Number',short:'Worlds',genre:'fantasia sandbox',theme:'Latter Earth / fantasia de espada e feitiçaria',
      corpusId:'wwn-srd-1.0',corpusReady:true,mechanicsReady:true,rulesAuthority:'WWN SRD 1.0',atlasKind:'wilderness',atlasLabel:'Ermos / hexcrawl',mapUnit:'6 milhas por hex',visualMode:'terrain',mapOrientation:'flat',
      mechanics:{skill:'2d6 + perícia + atributo',attack:'1d20 + AB + perícia + atributo vs AC',initiative:'1d8 por lado + melhor DEX',shock:true},
      modules:['exploração de ermos','facções','magia','projetos','mundo vivo'],imageGenre:'fantasia sandbox de espada e feitiçaria',defaultCampaign:'As Marchas de Orne'
    },
    SWN:{
      id:'SWN',barbaraSystemId:'stars_without_number',label:'Stars Without Number',short:'Stars',genre:'ficção científica sandbox',theme:'setores estelares e exploração sci-fi',
      corpusId:'swn-revised',corpusReady:true,mechanicsReady:true,rulesAuthority:'Stars Without Number Revised',atlasKind:'sector',atlasLabel:'Setor estelar',mapUnit:'hex de setor / sistema',visualMode:'abstract',mapOrientation:'pointy',
      mechanics:{skill:'2d6 + perícia + atributo',attack:'1d20 + AB + perícia + atributo vs AC',initiative:'1d8 + DEX individual (grupo opcional)',shock:true},
      modules:['setor estelar','combate pessoal','cobertura','naves','psionismo','facções','exploração planetária'],imageGenre:'ficção científica sandbox, tecnologia espacial usada e funcional',defaultCampaign:'Fronteira do Setor Orne'
    },
    CWN:{
      id:'CWN',barbaraSystemId:'cities_without_number',label:'Cities Without Number',short:'Cities',genre:'cyberpunk sandbox',theme:'megacorporações, operações urbanas e rua',
      corpusId:'cwn-core',corpusReady:false,mechanicsReady:false,rulesAuthority:null,atlasKind:'city',atlasLabel:'Cidade / distritos',mapUnit:'distrito / zona urbana',visualMode:'abstract',mapOrientation:'flat',
      mechanics:{skill:'bloqueado sem corpus local homologado',attack:'bloqueado sem corpus local homologado',initiative:'bloqueado sem corpus local homologado',shock:null},
      modules:['distritos','corporações e gangues','cyberware','hacking','operações urbanas'],imageGenre:'cyberpunk urbano, neon gasto, concreto, fios, chuva e tecnologia invasiva',defaultCampaign:'Cidade Orne'
    },
    AWN:{
      id:'AWN',barbaraSystemId:'ashes_without_number',label:'Ashes Without Number',short:'Ashes',genre:'pós-apocalipse sandbox',theme:'ermos pós-apocalípticos, sobrevivência e ruínas',
      corpusId:'awn-core',corpusReady:false,mechanicsReady:false,rulesAuthority:null,atlasKind:'wasteland',atlasLabel:'Ermos pós-apocalípticos',mapUnit:'hex de ermo',visualMode:'abstract',mapOrientation:'flat',
      mechanics:{skill:'bloqueado sem corpus local homologado',attack:'bloqueado sem corpus local homologado',initiative:'bloqueado sem corpus local homologado',shock:null},
      modules:['hexcrawl de ermos','sobrevivência','sucata e recursos','assentamentos','facções'],imageGenre:'pós-apocalipse sandbox, ruínas, poeira, sucata, sobreviventes e tecnologia remendada',defaultCampaign:'Ermos de Orne'
    }
  };
  Object.values(systems).forEach(Object.freeze);Object.freeze(systems);
  global.XWN_SYSTEMS=systems;
  if(typeof module!=='undefined'&&module.exports)module.exports=systems;
})(typeof window!=='undefined'?window:globalThis);
