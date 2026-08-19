(function(global){
  'use strict';
  const E=global.XWNEngine;if(!E?.storageKeyFor)return;
  const NEW=E.storageKeyFor(E.activeSystem());
  const LEGACY_WWN=['braseiro_xwn_wwn_v370','braseiro_xwn_wwn_v360','braseiro_xwn_wwn_v350','braseiro_xwn_wwn_v340','braseiro_xwn_wwn_v330','braseiro_xwn_wwn_v301','braseiro_xwn_wwn_v300','braseiro_xwn_wwn_v150','braseiro_xwn_wwn_v100'];
  try{
    if(E.activeSystem()==='WWN'&&!localStorage.getItem(NEW)){
      for(const key of LEGACY_WWN){const raw=localStorage.getItem(key);if(!raw)continue;try{const migrated=E.importState(raw);localStorage.setItem(NEW,E.exportState(migrated));localStorage.setItem('braseiro_xwn_last_migration_v4',JSON.stringify({from:key,to:NEW,at:new Date().toISOString()}));break;}catch(e){console.warn('Legacy XWN save rejected',key,e);}}
    }
  }catch(e){console.warn('XWN migration unavailable',e)}
})(typeof window!=='undefined'?window:globalThis);
