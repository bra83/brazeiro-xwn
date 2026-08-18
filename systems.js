(function(global){
  'use strict';
  const systems={
    WWN:{
      id:'WWN',label:'Worlds Without Number',short:'Worlds',genre:'fantasia sandbox',theme:'Latter Earth / fantasia de espada e feitiçaria',
      corpusId:'wwn-srd-1.0',corpusReady:true,mechanicsReady:true,atlasKind:'wilderness',atlasLabel:'Ermos / hexcrawl',mapUnit:'6 milhas por hex',visualMode:'terrain',mapOrientation:'flat',
      modules:['exploração de ermos','facções','magia','projetos','mundo vivo'],
      imageGenre:'fantasia sandbox de espada e feitiçaria',
      defaultCampaign:'As Marchas de Orne'
    },
    SWN:{
      id:'SWN',label:'Stars Without Number',short:'Stars',genre:'ficção científica sandbox',theme:'setores estelares e exploração sci-fi',
      corpusId:'swn-revised',corpusReady:false,mechanicsReady:false,atlasKind:'sector',atlasLabel:'Setor estelar',mapUnit:'hex de setor / sistema',visualMode:'abstract',mapOrientation:'pointy',
      modules:['setor estelar','naves','psionismo','facções','exploração planetária'],
      imageGenre:'ficção científica sandbox, tecnologia espacial usada e funcional',
      defaultCampaign:'Fronteira do Setor Orne'
    },
    CWN:{
      id:'CWN',label:'Cities Without Number',short:'Cities',genre:'cyberpunk sandbox',theme:'megacorporações, operações urbanas e rua',
      corpusId:'cwn-core',corpusReady:false,mechanicsReady:false,atlasKind:'city',atlasLabel:'Cidade / distritos',mapUnit:'distrito / zona urbana',visualMode:'abstract',mapOrientation:'flat',
      modules:['distritos','corporações e gangues','cyberware','hacking','operações urbanas'],
      imageGenre:'cyberpunk urbano, neon gasto, concreto, fios, chuva e tecnologia invasiva',
      defaultCampaign:'Cidade Orne'
    },
    AWN:{
      id:'AWN',label:'Ashes Without Number',short:'Ashes',genre:'pós-apocalipse sandbox',theme:'ermos pós-apocalípticos, sobrevivência e ruínas',
      corpusId:'awn-core',corpusReady:false,mechanicsReady:false,atlasKind:'wasteland',atlasLabel:'Ermos pós-apocalípticos',mapUnit:'hex de ermo',visualMode:'abstract',mapOrientation:'flat',
      modules:['hexcrawl de ermos','sobrevivência','sucata e recursos','assentamentos','facções'],
      imageGenre:'pós-apocalipse sandbox, ruínas, poeira, sucata, sobreviventes e tecnologia remendada',
      defaultCampaign:'Ermos de Orne'
    }
  };
  Object.values(systems).forEach(Object.freeze);Object.freeze(systems);
  global.XWN_SYSTEMS=systems;
  if(typeof module!=='undefined'&&module.exports)module.exports=systems;
})(typeof window!=='undefined'?window:globalThis);
